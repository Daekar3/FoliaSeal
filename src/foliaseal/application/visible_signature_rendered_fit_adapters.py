"""Concrete rendered-preview fit probe for visible signatures.

This module is intentionally the infrastructure-facing edge of the rendered-fit policy. It owns
canonical preview rendering, raster analysis, bounded cache reuse, and temporary-directory cleanup;
the neutral policy and layout modules do not import these dependencies.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field, replace
from pathlib import Path

from foliaseal.application import signing_preview_renderer as _signing_preview_renderer
from foliaseal.application.preview_render_boundary import (
    PreviewRasterRenderer,
    RenderedInkMeasurementPort,
    RenderedInkMeasurementRequest,
)
from foliaseal.application.stamp_preview_builder import signing_draft_preview_for_stamp_text
from foliaseal.application.text_raster_analysis import DefaultRenderedInkMeasurementPort
from foliaseal.application.visible_signature_color import text_style_color_rgba
from foliaseal.application.visible_signature_fit_policy import (
    VisibleSignatureRenderedFitProbe,
    VisibleSignatureRenderedFitRequest,
)
from foliaseal.application.visible_signature_layout import (
    VisibleSignatureLayoutPolicy,
)
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition


@dataclass
class PyHankoRenderedFitProbe(VisibleSignatureRenderedFitProbe):
    """Evaluate rendered fit using the canonical PyHanko/Pillow preview pipeline."""

    render_port: PreviewRasterRenderer | None = None
    ink_measurement_port: RenderedInkMeasurementPort | None = None
    _cache: dict[tuple[object, ...], bool] = field(default_factory=dict, init=False, repr=False)

    def clear_cache(self) -> None:
        """Clear only this probe's bounded rendered-fit cache for test isolation."""
        self._cache.clear()

    def single_line_fits(self, request: VisibleSignatureRenderedFitRequest) -> bool:
        if request.appearance.layout_template != SignatureLayoutTemplate.SINGLE_LINE:
            return False
        effective_request = replace(
            request,
            render_port=(
                request.render_port if request.render_port is not None else self.render_port
            ),
        )
        cache_key = _single_line_rendered_ink_fit_cache_key(effective_request)
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        result = self._single_line_fits_uncached(effective_request)
        if len(self._cache) >= 256:
            self._cache.clear()
        self._cache[cache_key] = result
        return result

    def horizontal_multi_line_fits(self, request: VisibleSignatureRenderedFitRequest) -> bool:
        return _horizontal_multi_line_fits(
            replace(
                request,
                render_port=(
                    request.render_port
                    if request.render_port is not None
                    else self.render_port
                ),
            ),
            ink_measurement_port=self.ink_measurement_port or DefaultRenderedInkMeasurementPort(),
        )

    def _single_line_fits_uncached(self, request: VisibleSignatureRenderedFitRequest) -> bool:
        snapshot = None
        reference_snapshot = None
        try:
            preview = signing_draft_preview_for_stamp_text(
                signature_rect=request.signature_rect,
                signature_appearance=request.appearance,
                stamp_text=request.stamp_text,
            )
            render_port = (
                request.render_port if request.render_port is not None else self.render_port
            )
            snapshot = _signing_preview_renderer.render_canonical_signature_preview(
                preview,
                zoom=1.0,
                include_border=True,
                flatten_to_white=True,
                render_port=render_port,
            )
            if snapshot is None or snapshot.text_area_bounds_px is None:
                return False
            if (
                request.appearance.image_stamp_path is not None
                and request.appearance.stamp_position
                in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
                and (snapshot.stamp_area_bounds_px is None or snapshot.stamp_bounds_px is None)
            ):
                return False
            nominal_width_overflow = (
                (snapshot.text_bounds_px["width"] - snapshot.text_area_bounds_px["width"])
                if snapshot.text_bounds_px is not None
                else 0
            )
            if nominal_width_overflow > 16:
                return False
            text_bounds = _single_line_text_only_ink_bounds(
                preview=preview,
                snapshot=snapshot,
                render_port=render_port,
            )
            if text_bounds is None:
                return False
            if not _horizontal_single_line_text_ink_inside_border(
                text_bounds=text_bounds,
                preview_width_px=snapshot.width_px,
                preview_height_px=snapshot.height_px,
                signature_appearance=request.appearance,
            ):
                return False
            enforce_reference_ink_preservation = (
                request.appearance.image_stamp_path is not None
                and request.appearance.stamp_position
                in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
            )
            if enforce_reference_ink_preservation:
                reference_rect = replace(
                    request.signature_rect,
                    width_pt=max(
                        request.signature_rect.width_pt,
                        request.signature_rect.width_pt
                        + float((snapshot.text_bounds_px or {}).get("width", 0))
                        + 64.0,
                    ),
                    height_pt=max(
                        request.signature_rect.height_pt,
                        float((snapshot.text_bounds_px or {}).get("height", 0)) + 64.0,
                    ),
                )
                reference_preview = signing_draft_preview_for_stamp_text(
                    signature_rect=reference_rect,
                    signature_appearance=request.appearance,
                    stamp_text=request.stamp_text,
                )
                reference_snapshot = _signing_preview_renderer.render_canonical_signature_preview(
                    reference_preview,
                    zoom=1.0,
                    include_border=True,
                    flatten_to_white=True,
                    render_port=render_port,
                )
                if reference_snapshot is None or reference_snapshot.text_area_bounds_px is None:
                    return False
                reference_text_bounds = _single_line_text_only_ink_bounds(
                    preview=reference_preview,
                    snapshot=reference_snapshot,
                    render_port=render_port,
                )
                if reference_text_bounds is None:
                    return False
                if (
                    max(0, reference_text_bounds["width"] - text_bounds["width"]) > 3
                    or max(0, reference_text_bounds["height"] - text_bounds["height"]) > 3
                ):
                    return False
            return (
                text_bounds["width"] <= snapshot.text_area_bounds_px["width"]
                and text_bounds["height"] <= snapshot.text_area_bounds_px["height"] + 1
            )
        except Exception:
            return False
        finally:
            _cleanup_canonical_preview_snapshot(snapshot)
            _cleanup_canonical_preview_snapshot(reference_snapshot)


def _single_line_text_only_ink_bounds(
    *,
    preview: object,
    snapshot: object,
    render_port: PreviewRasterRenderer | None,
) -> dict[str, int] | None:
    layout = _signing_preview_renderer._canonical_preview_layout(
        preview,
        include_text=True,
        include_stamp=True,
        include_border=True,
        render_port=render_port,
    )
    return _signing_preview_renderer._render_optional_preview_bounds(
        preview=preview,
        layout=layout,
        zoom=1.0,
        output_path=Path(snapshot.image_path).parent / "fit-text-only.png",
        include_text=True,
        include_stamp=False,
        render_port=render_port,
        flatten_to_white=True,
    )


def _horizontal_multi_line_fits(
    request: VisibleSignatureRenderedFitRequest,
    *,
    ink_measurement_port: RenderedInkMeasurementPort,
) -> bool:
    if (
        request.appearance.layout_template != SignatureLayoutTemplate.MULTI_LINE
        or request.appearance.image_stamp_path is None
        or request.appearance.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return False

    layout_plan = request.layout_plan
    width_overflow = layout_plan.text_box.width_pt - (layout_plan.text_area_width_pt + 1)
    height_overflow = layout_plan.text_box.height_pt - layout_plan.text_area_height_pt
    if width_overflow > 0 or height_overflow <= 0 or height_overflow > 6:
        return False

    snapshot = None
    try:
        preview = signing_draft_preview_for_stamp_text(
            signature_rect=request.signature_rect,
            signature_appearance=request.appearance,
            stamp_text=request.stamp_text,
        )
        snapshot = _signing_preview_renderer.render_canonical_signature_preview(
            preview,
            zoom=1.0,
            include_border=True,
            flatten_to_white=True,
            render_port=request.render_port,
        )
        if snapshot is None or snapshot.text_area_bounds_px is None:
            return False
        measurement = ink_measurement_port.measure(
            RenderedInkMeasurementRequest(
                preview_image_path=snapshot.image_path,
                text_widget_bounds=snapshot.text_area_bounds_px,
                text_color_rgba=text_style_color_rgba(request.appearance.text_style),
                reference_text_content_bounds=snapshot.text_bounds_px,
            )
        )
        text_bounds = measurement.bounds_px
        stamp_bounds = getattr(snapshot, "stamp_bounds_px", None)
        if text_bounds is None or stamp_bounds is None:
            return False
        if stamp_bounds["width"] <= 0 or stamp_bounds["height"] <= 0:
            return False
        container = {"x": 0, "y": 0, "width": snapshot.width_px, "height": snapshot.height_px}
        return (
            _rect_inside_container(text_bounds, container)
            and _rect_inside_container(stamp_bounds, container)
            and not _rectangles_overlap(text_bounds, stamp_bounds)
        )
    except Exception:
        return False
    finally:
        _cleanup_canonical_preview_snapshot(snapshot)


def _horizontal_single_line_text_ink_inside_border(
    *,
    text_bounds: dict[str, int],
    preview_width_px: int,
    preview_height_px: int,
    signature_appearance: object,
) -> bool:
    if (
        signature_appearance.layout_template != SignatureLayoutTemplate.SINGLE_LINE
        or signature_appearance.image_stamp_path is None
        or signature_appearance.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return True
    guard_px = VisibleSignatureLayoutPolicy.border_safe_inset(
        box_style=signature_appearance.box_style
    )
    if guard_px <= 0:
        return True
    return _rect_inside_container(
        text_bounds,
        {
            "x": guard_px,
            "y": guard_px,
            "width": max(0, preview_width_px - guard_px * 2),
            "height": max(0, preview_height_px - guard_px * 2),
        },
    )


def _single_line_rendered_ink_fit_cache_key(
    request: VisibleSignatureRenderedFitRequest,
) -> tuple[object, ...]:
    appearance = request.appearance
    box_style = appearance.box_style
    text_style = appearance.text_style
    image_identity: tuple[object, ...] = (appearance.image_stamp_path,)
    if appearance.image_stamp_path:
        try:
            image_stat = Path(appearance.image_stamp_path).stat()
        except OSError:
            image_stat = None
        if image_stat is not None:
            image_identity = (
                appearance.image_stamp_path,
                image_stat.st_size,
                image_stat.st_mtime_ns,
            )
    return (
        request.signature_rect.page_index,
        round(request.signature_rect.left_pt, 3),
        round(request.signature_rect.bottom_pt, 3),
        round(request.signature_rect.width_pt, 3),
        round(request.signature_rect.height_pt, 3),
        request.stamp_text,
        appearance.layout_template,
        appearance.stamp_position,
        image_identity,
        appearance.signer_label_prefix,
        appearance.datetime_format,
        appearance.show_field_names,
        text_style.font_family,
        round(text_style.font_size_pt, 3),
        text_style.bold,
        text_style.italic,
        text_style.text_color_hex,
        box_style.show_border,
        box_style.border_color_hex,
        round(box_style.border_width_pt, 3),
        box_style.background_color_hex,
        id(request.render_port) if request.render_port is not None else None,
    )


def _rect_inside_container(rect: dict[str, int], container: dict[str, int]) -> bool:
    return (
        rect["x"] >= container["x"]
        and rect["y"] >= container["y"]
        and rect["x"] + rect["width"] <= container["x"] + container["width"]
        and rect["y"] + rect["height"] <= container["y"] + container["height"]
    )


def _rectangles_overlap(first: dict[str, int], second: dict[str, int]) -> bool:
    return (
        first["x"] < second["x"] + second["width"]
        and second["x"] < first["x"] + first["width"]
        and first["y"] < second["y"] + second["height"]
        and second["y"] < first["y"] + first["height"]
    )


def _cleanup_canonical_preview_snapshot(snapshot: object | None) -> None:
    if snapshot is None:
        return
    image_path = getattr(snapshot, "image_path", None)
    if not isinstance(image_path, str):
        return
    temp_dir = Path(image_path).parent
    if temp_dir.name.startswith("foliaseal-canonical-preview-"):
        shutil.rmtree(temp_dir, ignore_errors=True)
