"""Neutral, deterministic analysis for one captured signing preview."""

from __future__ import annotations

import importlib
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from PIL import Image

from foliaseal.application.signature_font_registry import preview_font_family_supported
from foliaseal.application.text_raster_analysis import (
    detect_text_content_bounds_in_image,
    detect_text_line_bounds_in_image,
)
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition

from .preview_image_comparison import PreviewImageComparisonAnalyzer
from .preview_text_geometry import PreviewTextGeometryAnalyzer

Bounds = dict[str, int] | None


@dataclass(frozen=True)
class PreviewAnalysisRequest:
    """All non-lifecycle inputs required to analyze one preview capture."""

    preview: Any
    preview_image_path: str | None
    analysis_image_path: str | None
    image_error: str | None
    card_bounds: Bounds
    body_bounds: Bounds
    detail_bounds: Bounds
    stamp_bounds: Bounds
    text_widget_bounds: Bounds
    analysis_detection_bounds: Bounds
    stamp_band_bounds: Bounds
    stamp_pixmap_bounds: Bounds
    stamp_content_bounds_override: Bounds
    structural_text_content_bounds: Bounds
    structural_line_bounds: tuple[dict[str, int], ...]
    reference_text_content_bounds: Bounds
    reference_text_detection_error: str | None
    text_color_rgba: tuple[int, int, int, int] | None
    active_label: Any | None
    preview_padding_px: int
    layout_spacing_px: int | None


@dataclass(frozen=True)
class PreviewAnalysisResult:
    """Stable analysis values merged into the existing capture payload."""

    values: Mapping[str, Any]

    def as_mapping(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(frozen=True)
class PreviewAnalysisEngine:
    """Deep preview-analysis boundary shared by live and headless capture."""

    text_geometry: PreviewTextGeometryAnalyzer
    image_comparison: PreviewImageComparisonAnalyzer

    def analyze(self, request: PreviewAnalysisRequest) -> PreviewAnalysisResult:
        stamp_source_analysis = analyze_stamp_source_image(
            getattr(request.preview, "image_stamp_path", None)
        )
        stamp_content_bounds = request.stamp_content_bounds_override
        if stamp_content_bounds is None:
            stamp_content_bounds = project_content_bounds_to_preview(
                source_image_size=stamp_source_analysis.get("stamp_source_image_size_px"),
                source_content_bounds=stamp_source_analysis.get(
                    "stamp_source_content_bounds_px"
                ),
                pixmap_bounds=request.stamp_pixmap_bounds,
            )

        stamp_diagnostics = stamp_edge_diagnostics(
            preview=request.preview,
            stamp_band_bounds=request.stamp_band_bounds,
            stamp_pixmap_bounds=request.stamp_pixmap_bounds,
            stamp_content_bounds=stamp_content_bounds,
        )

        analysis_image_path = request.analysis_image_path or request.preview_image_path
        text_rendered_content_bounds: Bounds = None
        text_rendered_line_bounds: tuple[dict[str, int], ...] = ()
        text_content_error = None
        text_line_detection_error = None
        if (
            analysis_image_path is not None
            and request.image_error is None
            and request.analysis_detection_bounds is not None
        ):
            text_rendered_content_bounds, text_content_error = (
                self.text_geometry.detect_text_content_bounds_in_preview(
                    preview_image_path=analysis_image_path,
                    text_widget_bounds=request.analysis_detection_bounds,
                    text_color_rgba=request.text_color_rgba,
                    reference_text_content_bounds=request.reference_text_content_bounds,
                )
            )
            if (
                text_rendered_content_bounds is None
                and request.structural_text_content_bounds is not None
            ):
                text_rendered_content_bounds = request.structural_text_content_bounds
            text_rendered_line_bounds, text_line_detection_error = (
                self.text_geometry.detect_text_line_bounds_in_preview(
                    preview_image_path=analysis_image_path,
                    text_widget_bounds=request.analysis_detection_bounds,
                    text_color_rgba=request.text_color_rgba,
                    reference_text_content_bounds=request.reference_text_content_bounds,
                )
            )
            if not text_rendered_line_bounds and request.structural_line_bounds:
                text_rendered_line_bounds = request.structural_line_bounds

        text_diagnostics = text_edge_diagnostics(
            preview=request.preview,
            card_bounds=request.card_bounds,
            text_widget_bounds=request.text_widget_bounds,
            text_content_bounds=text_rendered_content_bounds,
            reference_text_content_bounds=request.reference_text_content_bounds,
            stamp_band_bounds=request.stamp_band_bounds,
            stamp_content_bounds=stamp_content_bounds,
        )
        edge_distances = preview_edge_distances(
            card_bounds=request.card_bounds,
            body_bounds=request.body_bounds,
            detail_bounds=request.detail_bounds,
            stamp_bounds=request.stamp_bounds,
            preview_padding_px=request.preview_padding_px,
        )
        font_values = font_diagnostics(
            preview=request.preview,
            active_label=request.active_label,
        )
        values: dict[str, Any] = {
            "card_bounds_px": request.card_bounds,
            "text_widget_bounds_px": request.text_widget_bounds,
            "stamp_pixmap_size_px": (
                None
                if request.stamp_pixmap_bounds is None
                else {
                    "width": request.stamp_pixmap_bounds["width"],
                    "height": request.stamp_pixmap_bounds["height"],
                }
            ),
            "layout_spacing_px": request.layout_spacing_px,
            "preview_padding_px": request.preview_padding_px,
            "edge_distances_px": edge_distances,
            "text_widget_image_sha256": self.image_comparison.image_crop_sha256(
                preview_image_path=request.preview_image_path,
                crop_bounds=request.text_widget_bounds,
            ),
            "text_rendered_content_bounds_px": text_rendered_content_bounds,
            "text_structural_content_bounds_px": request.structural_text_content_bounds,
            "text_content_detection_error": text_content_error,
            "text_rendered_line_bounds_px": text_rendered_line_bounds,
            "text_structural_line_bounds_px": request.structural_line_bounds,
            "text_line_detection_error": text_line_detection_error,
            "text_reference_content_bounds_px": request.reference_text_content_bounds,
            "text_reference_detection_error": request.reference_text_detection_error,
            "stamp_band_bounds_px": request.stamp_band_bounds,
            "stamp_rendered_pixmap_bounds_px": request.stamp_pixmap_bounds,
            "stamp_rendered_content_bounds_px": stamp_content_bounds,
            "stamp_debug_image_path": None,
            "stamp_debug_image_error": None,
            "text_debug_image_path": None,
            "text_debug_image_error": None,
            **font_values,
            **stamp_source_analysis,
            **text_diagnostics,
            **stamp_diagnostics,
        }
        return PreviewAnalysisResult(values)

    def analyze_capture_transitions(
        self, states: Sequence[Mapping[str, Any]]
    ) -> tuple[Mapping[str, Any], ...]:
        diagnostics: list[Mapping[str, Any]] = []
        for index in range(1, len(states)):
            previous = states[index - 1]
            current = states[index]
            if not isinstance(previous, Mapping) or not isinstance(current, Mapping):
                continue
            previous_preview = previous.get("preview_snapshot")
            current_preview = current.get("preview_snapshot")
            if not isinstance(previous_preview, dict) or not isinstance(current_preview, dict):
                continue
            previous_style = previous_preview.get("text_style") or {}
            current_style = current_preview.get("text_style") or {}
            previous_render = previous_preview.get("render_capture") or {}
            current_render = current_preview.get("render_capture") or {}
            if normalize_preview_text(previous.get("preview_text")) != normalize_preview_text(
                current.get("preview_text")
            ):
                continue
            if any(
                previous_preview.get(key) != current_preview.get(key)
                for key in ("layout_template", "stamp_position", "signature_rect")
            ):
                continue
            change_ratio = self.image_comparison.image_crop_change_ratio(
                previous_image_path=previous_render.get("preview_image_path"),
                previous_bounds=previous_render.get("text_widget_bounds_px"),
                current_image_path=current_render.get("preview_image_path"),
                current_bounds=current_render.get("text_widget_bounds_px"),
            )
            same_bounds = (
                previous_render.get("text_rendered_content_bounds_px")
                == current_render.get("text_rendered_content_bounds_px")
                and previous_render.get("text_rendered_content_bounds_px") is not None
            )
            if (
                previous_style.get("font_size_pt") != current_style.get("font_size_pt")
                and same_bounds
                and change_ratio is not None
                and change_ratio < 0.005
            ):
                diagnostics.append(
                    {
                        "from_capture_label": previous.get("capture_label"),
                        "to_capture_label": current.get("capture_label"),
                        "issue_code": "font_size_change_had_negligible_visual_effect",
                        "previous_font_size_pt": previous_style.get("font_size_pt"),
                        "current_font_size_pt": current_style.get("font_size_pt"),
                        "changed_pixel_ratio": round(change_ratio, 6),
                    }
                )
            if (
                previous_style.get("font_family") != current_style.get("font_family")
                and previous_render.get("effective_text_font_category")
                == current_render.get("effective_text_font_category")
                and change_ratio is not None
                and change_ratio < 0.01
            ):
                diagnostics.append(
                    {
                        "from_capture_label": previous.get("capture_label"),
                        "to_capture_label": current.get("capture_label"),
                        "issue_code": "font_family_change_had_negligible_visual_effect",
                        "previous_font_family": previous_style.get("font_family"),
                        "current_font_family": current_style.get("font_family"),
                        "effective_text_font_category": current_render.get(
                            "effective_text_font_category"
                        ),
                        "changed_pixel_ratio": round(change_ratio, 6),
                    }
                )
        return tuple(diagnostics)


def build_preview_analysis_engine(
    *,
    write_widget_capture_png: Callable[..., str | None] | None = None,
) -> PreviewAnalysisEngine:
    """Build the neutral engine without importing Qt bindings."""

    return PreviewAnalysisEngine(
        text_geometry=PreviewTextGeometryAnalyzer(
            detect_text_content_bounds_in_image=detect_text_content_bounds_in_image,
            detect_text_line_bounds_in_image=detect_text_line_bounds_in_image,
            import_module=importlib.import_module,
            write_widget_capture_png=write_widget_capture_png
            or (lambda _widget, _path: "Qt reference capture is unavailable."),
        ),
        image_comparison=PreviewImageComparisonAnalyzer(),
    )


def analyze_capture_state_transitions(
    states: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Analyze transition diagnostics without importing the Qt harness."""

    return build_preview_analysis_engine().analyze_capture_transitions(states)


def analyze_stamp_source_image(image_path: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "stamp_source_image_size_px": None,
        "stamp_source_content_bounds_px": None,
        "stamp_source_content_error": None,
    }
    if not image_path:
        return result
    try:
        with Image.open(image_path) as image:
            width, height = image.size
            result["stamp_source_image_size_px"] = {"width": width, "height": height}
            alpha_bounds = image.convert("RGBA").getchannel("A").getbbox()
            if alpha_bounds is None:
                result["stamp_source_content_error"] = (
                    "Stamp source image contains no non-transparent pixels."
                )
                return result
            left, top, right, bottom = alpha_bounds
            result["stamp_source_content_bounds_px"] = {
                "x": int(left),
                "y": int(top),
                "width": int(right - left),
                "height": int(bottom - top),
            }
    except OSError as exc:
        result["stamp_source_content_error"] = f"Failed to open stamp source image: {exc}"
    return result


def project_content_bounds_to_preview(
    *,
    source_image_size: dict[str, int] | None,
    source_content_bounds: dict[str, int] | None,
    pixmap_bounds: dict[str, int] | None,
) -> dict[str, int] | None:
    if source_image_size is None or source_content_bounds is None or pixmap_bounds is None:
        return None
    source_width = max(1, source_image_size["width"])
    source_height = max(1, source_image_size["height"])
    content_left = int(round(source_content_bounds["x"] * pixmap_bounds["width"] / source_width))
    content_top = int(round(source_content_bounds["y"] * pixmap_bounds["height"] / source_height))
    content_width = max(
        1, int(round(source_content_bounds["width"] * pixmap_bounds["width"] / source_width))
    )
    content_height = max(
        1, int(round(source_content_bounds["height"] * pixmap_bounds["height"] / source_height))
    )
    content_width = min(content_width, pixmap_bounds["width"] - content_left)
    content_height = min(content_height, pixmap_bounds["height"] - content_top)
    return {
        "x": pixmap_bounds["x"] + content_left,
        "y": pixmap_bounds["y"] + content_top,
        "width": max(1, content_width),
        "height": max(1, content_height),
    }


def _rect_edge_distances(*, outer_bounds: Bounds, inner_bounds: Bounds) -> dict[str, int] | None:
    if outer_bounds is None or inner_bounds is None:
        return None
    outer_right = outer_bounds["x"] + outer_bounds["width"]
    outer_bottom = outer_bounds["y"] + outer_bounds["height"]
    inner_right = inner_bounds["x"] + inner_bounds["width"]
    inner_bottom = inner_bounds["y"] + inner_bounds["height"]
    return {
        "left": inner_bounds["x"] - outer_bounds["x"],
        "top": inner_bounds["y"] - outer_bounds["y"],
        "right": outer_right - inner_right,
        "bottom": outer_bottom - inner_bottom,
    }


def stamp_edge_diagnostics(
    *,
    preview: Any,
    stamp_band_bounds: Bounds,
    stamp_pixmap_bounds: Bounds,
    stamp_content_bounds: Bounds,
) -> dict[str, Any]:
    pixmap_distances = _rect_edge_distances(
        outer_bounds=stamp_band_bounds, inner_bounds=stamp_pixmap_bounds
    )
    content_distances = _rect_edge_distances(
        outer_bounds=stamp_band_bounds, inner_bounds=stamp_content_bounds
    )
    relevant = _relevant_stamp_edge_distances(
        layout_template=getattr(preview, "layout_template", None),
        stamp_position=getattr(preview, "stamp_position", None),
        edge_distances=content_distances,
    )

    def minimum(distances: dict[str, int] | None) -> int | None:
        return None if distances is None else min(distances.values())

    pixmap_min = minimum(pixmap_distances)
    content_min = minimum(relevant)
    warning_threshold = 0
    return {
        "stamp_pixmap_edge_distances_px": pixmap_distances,
        "stamp_content_edge_distances_px": content_distances,
        "stamp_pixmap_touches_band_edge": None if pixmap_min is None else pixmap_min <= 0,
        "stamp_content_touches_band_edge": None if content_min is None else content_min <= 0,
        "stamp_content_warning_threshold_px": warning_threshold,
        "stamp_pixmap_min_edge_distance_px": pixmap_min,
        "stamp_content_min_edge_distance_px": content_min,
        "stamp_content_within_warning_distance": (
            None if content_min is None else content_min <= warning_threshold
        ),
    }


def text_edge_diagnostics(
    *,
    preview: Any,
    card_bounds: Bounds,
    text_widget_bounds: Bounds,
    text_content_bounds: Bounds,
    reference_text_content_bounds: Bounds,
    stamp_band_bounds: Bounds,
    stamp_content_bounds: Bounds,
) -> dict[str, Any]:
    widget_distances = _rect_edge_distances(
        outer_bounds=text_widget_bounds, inner_bounds=text_content_bounds
    )
    border_distances = _rect_edge_distances(
        outer_bounds=card_bounds, inner_bounds=text_content_bounds
    )
    border_edge, stamp_edge = _text_widget_edge_roles(
        stamp_position=getattr(preview, "stamp_position", None)
    )
    border_facing_distance = None if widget_distances is None else widget_distances.get(border_edge)
    stamp_facing_distance = None if widget_distances is None else widget_distances.get(stamp_edge)
    stamp_band_overlap = _rectangles_overlap_exceeds_tolerance(
        text_content_bounds, stamp_band_bounds, tolerance_px=3
    )
    stamp_content_overlap = _rectangles_overlap_exceeds_tolerance(
        text_content_bounds, stamp_content_bounds, tolerance_px=3
    )
    widget_min = None if widget_distances is None else min(widget_distances.values())
    border_min = None if border_distances is None else min(border_distances.values())
    reference_width_loss = None
    reference_height_loss = None
    if text_content_bounds is not None and reference_text_content_bounds is not None:
        reference_width_loss = max(
            0,
            reference_text_content_bounds["width"] - text_content_bounds["width"],
        )
        reference_height_loss = max(
            0,
            reference_text_content_bounds["height"] - text_content_bounds["height"],
        )
    clipped_from_reference = None
    if reference_width_loss is not None and reference_height_loss is not None:
        clipped_from_reference = reference_width_loss > 3 or reference_height_loss > 1
    clipped_with_edge_contact = None
    if clipped_from_reference is not None:
        clipped_with_edge_contact = clipped_from_reference and (
            widget_min is not None
            and widget_min <= 0
            or border_min is not None
            and border_min <= 0
        )
    return {
        "text_content_edge_distances_px": widget_distances,
        "text_content_border_edge_distances_px": border_distances,
        "text_content_min_edge_distance_px": widget_min,
        "text_content_min_border_distance_px": border_min,
        "text_content_reference_width_loss_px": reference_width_loss,
        "text_content_reference_height_loss_px": reference_height_loss,
        "text_content_reference_width_tolerance_px": 3,
        "text_content_reference_height_tolerance_px": 1,
        "text_content_border_facing_distance_px": border_facing_distance,
        "text_content_stamp_facing_distance_px": stamp_facing_distance,
        "text_content_touches_widget_edge": None if widget_min is None else widget_min <= 0,
        "text_content_touches_border_facing_edge": (
            None if border_facing_distance is None else border_facing_distance <= 0
        ),
        "text_content_touches_stamp_facing_edge": (
            None if stamp_facing_distance is None else stamp_facing_distance <= 0
        ),
        "text_content_overlaps_stamp_band": stamp_band_overlap,
        "text_content_overlaps_stamp_content": stamp_content_overlap,
        "text_content_clipped_in_preview": (
            None
            if clipped_from_reference is None
            and widget_min is None
            and stamp_band_overlap is None
            and stamp_content_overlap is None
            else clipped_with_edge_contact is True
            or stamp_band_overlap is True
            or stamp_content_overlap is True
        ),
    }


def preview_edge_distances(
    *,
    preview: Any | None = None,
    card_bounds: Bounds,
    body_bounds: Bounds,
    detail_bounds: Bounds,
    stamp_bounds: Bounds,
    preview_padding_px: int | None = None,
) -> dict[str, Any]:
    if preview_padding_px is None:
        preview_padding_px = 6
    result = {
        "preview_padding_px": preview_padding_px,
        "text_top_to_border_px": None,
        "text_bottom_to_border_px": None,
        "stamp_top_to_border_px": None,
        "stamp_bottom_to_border_px": None,
        "content_top_to_border_px": None,
        "content_bottom_to_border_px": None,
    }
    if card_bounds is None or body_bounds is None:
        return result
    body_top = body_bounds["y"]
    card_height = card_bounds["height"]
    if detail_bounds is not None:
        detail_top = body_top + detail_bounds["y"]
        detail_bottom = detail_top + detail_bounds["height"]
        result["text_top_to_border_px"] = detail_top
        result["text_bottom_to_border_px"] = max(0, card_height - detail_bottom)
    if stamp_bounds is not None:
        stamp_top = body_top + stamp_bounds["y"]
        stamp_bottom = stamp_top + stamp_bounds["height"]
        result["stamp_top_to_border_px"] = stamp_top
        result["stamp_bottom_to_border_px"] = max(0, card_height - stamp_bottom)
    tops = [
        result[key]
        for key in ("text_top_to_border_px", "stamp_top_to_border_px")
        if result[key] is not None
    ]
    bottoms = [
        result[key]
        for key in ("text_bottom_to_border_px", "stamp_bottom_to_border_px")
        if result[key] is not None
    ]
    if tops:
        result["content_top_to_border_px"] = min(tops)
    if bottoms:
        result["content_bottom_to_border_px"] = min(bottoms)
    return result


def font_diagnostics(*, preview: Any, active_label: Any | None) -> dict[str, Any]:
    text_style = getattr(preview, "text_style", None)
    requested_family = getattr(text_style, "font_family", None) if text_style else None
    requested_size = getattr(text_style, "font_size_pt", None) if text_style else None
    effective_family = requested_family
    effective_size = requested_size
    if active_label is not None:
        font_getter = getattr(active_label, "font", None)
        if callable(font_getter):
            font = font_getter()
            family_getter = getattr(font, "family", None)
            size_getter = getattr(font, "pointSizeF", None)
            if callable(family_getter):
                effective_family = family_getter() or effective_family
            if callable(size_getter):
                effective_size = size_getter()
        info_getter = getattr(active_label, "fontInfo", None)
        if callable(info_getter):
            info = info_getter()
            family_getter = getattr(info, "family", None)
            size_getter = getattr(info, "pointSizeF", None)
            if callable(family_getter):
                effective_family = family_getter() or effective_family
            if callable(size_getter) and size_getter() > 0:
                effective_size = size_getter()
    requested_category = _font_family_category(str(requested_family or ""))
    effective_category = _font_family_category(str(effective_family or ""))
    return {
        "requested_text_font_family": requested_family,
        "requested_text_font_size_pt": requested_size,
        "effective_text_font_family": effective_family,
        "effective_text_font_point_size_pt": effective_size,
        "requested_text_font_category": requested_category,
        "effective_text_font_category": effective_category,
        "font_family_direct_preview_mapping_supported": preview_font_family_supported(
            str(requested_family or "")
        ),
        "font_family_category_mismatch": (
            None
            if not requested_category or not effective_category
            else requested_category != effective_category
        ),
    }


def _font_family_category(font_family: str) -> str | None:
    normalized = re.sub(r"\s*\[[^\]]+\]\s*$", "", font_family.strip().lower())
    if not normalized:
        return None
    if any(
        token in normalized
        for token in (
            "sans serif",
            "sans-serif",
            "sans",
            "helvetica",
            "arial",
            "nimbus sans",
            "liberation sans",
            "dejavu sans",
            "noto sans",
            "source sans",
            "verdana",
        )
    ):
        return "sans_serif"
    if any(token in normalized for token in ("courier", "mono", "code", "consola", "menlo")):
        return "monospace"
    if any(
        token in normalized
        for token in (
            "fantasy",
            "decor",
            "display",
            "papyrus",
            "noto serif display",
        )
    ):
        return "fantasy"
    if any(
        token in normalized
        for token in (
            "times",
            "serif",
            "georgia",
            "garamond",
            "cambria",
            "baskerville",
            "liberation serif",
            "noto serif",
        )
    ):
        return "serif"
    if any(
        token in normalized
        for token in ("cursive", "script", "hand", "brush", "callig", "comic", "zapfino")
    ):
        return "cursive"
    if "fantasy" in normalized:
        return "fantasy"
    return "unknown"


def _text_widget_edge_roles(*, stamp_position: SignatureStampPosition | None) -> tuple[str, str]:
    if stamp_position == SignatureStampPosition.TOP:
        return ("bottom", "top")
    if stamp_position == SignatureStampPosition.BOTTOM:
        return ("top", "bottom")
    if stamp_position == SignatureStampPosition.LEFT:
        return ("right", "left")
    return ("left", "right")


def _relevant_stamp_edge_distances(
    *,
    layout_template: SignatureLayoutTemplate | None,
    stamp_position: SignatureStampPosition | None,
    edge_distances: dict[str, int] | None,
) -> dict[str, int] | None:
    _ = layout_template
    if edge_distances is None:
        return None
    if stamp_position == SignatureStampPosition.TOP:
        return {"top": edge_distances["top"]}
    if stamp_position == SignatureStampPosition.BOTTOM:
        return {"bottom": edge_distances["bottom"]}
    if stamp_position == SignatureStampPosition.LEFT:
        return {"left": edge_distances["left"]}
    if stamp_position == SignatureStampPosition.RIGHT:
        return {"right": edge_distances["right"]}
    return dict(edge_distances)


def _rectangles_overlap_exceeds_tolerance(
    first: Bounds, second: Bounds, *, tolerance_px: int
) -> bool | None:
    if first is None or second is None:
        return None
    overlap_width = min(first["x"] + first["width"], second["x"] + second["width"]) - max(
        first["x"], second["x"]
    )
    overlap_height = min(first["y"] + first["height"], second["y"] + second["height"]) - max(
        first["y"], second["y"]
    )
    return overlap_width > tolerance_px and overlap_height > tolerance_px


def normalize_preview_text(value: Any) -> str:
    return re.sub(
        r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?(?:\s+[A-Z]{2,5})?\b",
        "<signing_time>",
        str(value or ""),
    )


def normalize_visible_text_for_comparison(value: Any) -> str:
    """Normalize rendered text for stable preview/output comparison."""

    return re.sub(r"\s+", " ", normalize_preview_text(value)).strip()
