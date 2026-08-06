"""Shared, environment-neutral preview evidence analysis and projection policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PreviewEvidenceFrame:
    """Normalized capture values supplied by a Qt or headless adapter."""

    preview: Any
    artifacts_dir: str | None
    artifact_basename: str
    preview_image_path: str | None
    analysis_image_path: str | None
    analysis_request_image_path: str | None
    image_error: str | None
    card_bounds: dict[str, int] | None
    body_bounds: dict[str, int] | None
    detail_bounds: dict[str, int] | None
    stamp_bounds: dict[str, int] | None
    text_widget_bounds: dict[str, int] | None
    analysis_detection_bounds: dict[str, int] | None
    stamp_band_bounds: dict[str, int] | None
    stamp_pixmap_bounds: dict[str, int] | None
    stamp_pixmap_size: dict[str, int] | None
    stamp_content_bounds_override: dict[str, int] | None
    structural_text_content_bounds: dict[str, int] | None
    structural_line_bounds: tuple[dict[str, int], ...]
    reference_text_content_bounds: dict[str, int] | None
    reference_text_detection_error: str | None
    text_color_rgba: tuple[int, int, int, int] | None
    active_label: Any | None
    preview_padding_px: int
    layout_spacing_px: int | None
    stamp_alignment: str | None
    single_body_bounds: dict[str, int] | None
    multi_body_bounds: dict[str, int] | None
    detail_label_bounds: dict[str, int] | None
    stamp_label_bounds: dict[str, int] | None
    multi_detail_bounds: dict[str, int] | None
    multi_stamp_bounds: dict[str, int] | None
    detail_text_size_hint: dict[str, int] | None
    canonical_snapshot: Any | None
    analysis_snapshot: Any | None
    prefer_analysis_snapshot: bool
    fallback_snapshot_image_path_to_base: bool


def build_preview_analysis_request(*, frame: PreviewEvidenceFrame, dependencies: Any) -> Any:
    """Build the existing analysis request from normalized adapter observations."""

    return dependencies.preview_analysis_request_type(
        preview=frame.preview,
        preview_image_path=frame.preview_image_path,
        analysis_image_path=frame.analysis_request_image_path,
        image_error=frame.image_error,
        card_bounds=frame.card_bounds,
        body_bounds=frame.body_bounds,
        detail_bounds=frame.detail_bounds,
        stamp_bounds=frame.stamp_bounds,
        text_widget_bounds=frame.text_widget_bounds,
        analysis_detection_bounds=frame.analysis_detection_bounds,
        stamp_band_bounds=frame.stamp_band_bounds,
        stamp_pixmap_bounds=frame.stamp_pixmap_bounds,
        stamp_content_bounds_override=frame.stamp_content_bounds_override,
        structural_text_content_bounds=frame.structural_text_content_bounds,
        structural_line_bounds=frame.structural_line_bounds,
        reference_text_content_bounds=frame.reference_text_content_bounds,
        reference_text_detection_error=frame.reference_text_detection_error,
        text_color_rgba=frame.text_color_rgba,
        active_label=frame.active_label,
        preview_padding_px=frame.preview_padding_px,
        layout_spacing_px=frame.layout_spacing_px,
    )


def assemble_preview_evidence(
    *,
    frame: PreviewEvidenceFrame,
    analysis_values: Mapping[str, Any],
    dependencies: Any,
) -> dict[str, Any]:
    """Apply shared diagnostic, artifact, snapshot, and mapping policy."""

    stamp_source_analysis = {
        key: analysis_values[key]
        for key in (
            "stamp_source_image_size_px",
            "stamp_source_content_bounds_px",
            "stamp_source_content_error",
        )
    }
    stamp_content_bounds = analysis_values["stamp_rendered_content_bounds_px"]
    stamp_diagnostics = {
        key: value
        for key, value in analysis_values.items()
        if key.startswith("stamp_")
        and key
        not in {
            "stamp_source_image_size_px",
            "stamp_source_content_bounds_px",
            "stamp_source_content_error",
            "stamp_rendered_content_bounds_px",
            "stamp_band_bounds_px",
            "stamp_rendered_pixmap_bounds_px",
            "stamp_debug_image_path",
            "stamp_debug_image_error",
        }
    }
    text_rendered_content_bounds = analysis_values["text_rendered_content_bounds_px"]
    text_rendered_line_bounds = analysis_values["text_rendered_line_bounds_px"]
    text_diagnostics = {
        key: value for key, value in analysis_values.items() if key.startswith("text_content_")
    }
    font_diagnostics = {
        key: value
        for key, value in analysis_values.items()
        if key.startswith(("requested_text_font_", "effective_text_font_", "font_family_"))
    }

    stamp_debug_image_path = None
    stamp_debug_image_error = None
    text_debug_image_path = None
    text_debug_image_error = None
    target_dir = None if frame.artifacts_dir is None else Path(frame.artifacts_dir)
    if (
        frame.preview_image_path is not None
        and frame.image_error is None
        and frame.stamp_band_bounds is not None
        and frame.stamp_pixmap_bounds is not None
    ):
        stamp_debug_image_path = str(target_dir / f"{frame.artifact_basename}_stamp_debug.png")
        stamp_debug_image_error = dependencies.write_stamp_debug_overlay(
            preview_image_path=frame.preview_image_path,
            output_path=stamp_debug_image_path,
            stamp_band_bounds=frame.stamp_band_bounds,
            stamp_pixmap_bounds=frame.stamp_pixmap_bounds,
            stamp_content_bounds=stamp_content_bounds,
            crop_padding=max(6, frame.preview_padding_px),
        )
    text_debug_image_source = frame.analysis_request_image_path or frame.preview_image_path
    if (
        text_debug_image_source is not None
        and frame.image_error is None
        and frame.analysis_detection_bounds is not None
    ):
        text_debug_image_path = str(target_dir / f"{frame.artifact_basename}_text_debug.png")
        text_debug_image_error = dependencies.write_text_debug_overlay(
            preview_image_path=text_debug_image_source,
            output_path=text_debug_image_path,
            text_widget_bounds=frame.analysis_detection_bounds,
            text_content_bounds=text_rendered_content_bounds,
            stamp_band_bounds=frame.stamp_band_bounds,
            crop_padding=max(6, frame.preview_padding_px),
        )

    analysis_appearance_snapshot = None
    if frame.canonical_snapshot is not None:
        base_snapshot = None
        if frame.prefer_analysis_snapshot and frame.analysis_snapshot is not None:
            base_snapshot = getattr(frame.analysis_snapshot, "appearance_snapshot", None)
        if base_snapshot is None:
            base_snapshot = getattr(frame.canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is None:
            box_style = getattr(frame.preview, "box_style", None)
            base_snapshot = dependencies.appearance_snapshot_type(
                image_path=frame.analysis_image_path,
                image_size_px=(
                    None
                    if frame.card_bounds is None
                    else {
                        "width": frame.card_bounds["width"],
                        "height": frame.card_bounds["height"],
                    }
                ),
                container_bounds_px=frame.card_bounds,
                border_bounds_px=frame.card_bounds,
                border_style=(
                    None
                    if box_style is None or not box_style.show_border
                    else {
                        "show_border": True,
                        "shape": "rounded",
                        "border_color_hex": box_style.border_color_hex,
                        "border_width_pt": box_style.border_width_pt,
                        "background_color_hex": box_style.background_color_hex,
                    }
                ),
                text_bounds_px=text_rendered_content_bounds,
                stamp_bounds_px=stamp_content_bounds,
                text_fragments=(),
                line_bounds_px=(),
            )
        snapshot_image_path = frame.analysis_image_path
        if frame.fallback_snapshot_image_path_to_base and snapshot_image_path is None:
            snapshot_image_path = base_snapshot.image_path
        analysis_appearance_snapshot = replace(
            base_snapshot,
            image_path=snapshot_image_path,
            line_bounds_px=base_snapshot.line_bounds_px or text_rendered_line_bounds,
        )

    return {
        "preview_image_path": frame.preview_image_path,
        "analysis_preview_image_path": frame.analysis_image_path,
        "analysis_appearance_snapshot": (
            None
            if analysis_appearance_snapshot is None
            else dependencies.jsonable_capture(analysis_appearance_snapshot)
        ),
        "preview_image_error": frame.image_error,
        "card_bounds_px": frame.card_bounds,
        "text_widget_bounds_px": frame.text_widget_bounds,
        "single_body_bounds_px": frame.single_body_bounds,
        "multi_body_bounds_px": frame.multi_body_bounds,
        "detail_label_bounds_px": frame.detail_label_bounds,
        "stamp_label_bounds_px": frame.stamp_label_bounds,
        "multi_detail_bounds_px": frame.multi_detail_bounds,
        "multi_stamp_bounds_px": frame.multi_stamp_bounds,
        "detail_text_size_hint_px": frame.detail_text_size_hint,
        "stamp_pixmap_size_px": frame.stamp_pixmap_size,
        "layout_spacing_px": frame.layout_spacing_px,
        "preview_padding_px": frame.preview_padding_px,
        "edge_distances_px": analysis_values["edge_distances_px"],
        "text_debug_image_path": text_debug_image_path,
        "text_debug_image_error": text_debug_image_error,
        "text_widget_image_sha256": analysis_values["text_widget_image_sha256"],
        "text_rendered_content_bounds_px": text_rendered_content_bounds,
        "text_structural_content_bounds_px": frame.structural_text_content_bounds,
        "text_content_detection_error": analysis_values["text_content_detection_error"],
        "text_rendered_line_bounds_px": text_rendered_line_bounds,
        "text_structural_line_bounds_px": frame.structural_line_bounds,
        "text_line_detection_error": analysis_values["text_line_detection_error"],
        "text_reference_content_bounds_px": frame.reference_text_content_bounds,
        "text_reference_detection_error": frame.reference_text_detection_error,
        **font_diagnostics,
        "stamp_debug_image_path": stamp_debug_image_path,
        "stamp_debug_image_error": stamp_debug_image_error,
        "stamp_band_bounds_px": frame.stamp_band_bounds,
        "stamp_alignment": frame.stamp_alignment,
        "stamp_rendered_pixmap_bounds_px": frame.stamp_pixmap_bounds,
        "stamp_rendered_content_bounds_px": stamp_content_bounds,
        **stamp_source_analysis,
        **text_diagnostics,
        **stamp_diagnostics,
    }


__all__ = [
    "PreviewEvidenceFrame",
    "assemble_preview_evidence",
    "build_preview_analysis_request",
]
