"""Shared reservation model for horizontal single-line signature layouts."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from foliaseal.application.preview_render_boundary import (
    PreviewRasterRenderer,
    RenderedInkMeasurementPort,
    RenderedInkMeasurementRequest,
)
from foliaseal.application.signing_draft_workflow import SigningDraftPreview
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureRect, SignatureStampPosition


@dataclass(frozen=True)
class HorizontalSingleLineRenderedReference:
    """Roomy canonical render measurement for horizontal single-line text ink."""

    preview_size_px: dict[str, int]
    structural_text_bounds_px: dict[str, int]
    rendered_ink_bounds_px: dict[str, int]
    structural_text_bounds_pt: dict[str, int]
    rendered_ink_bounds_pt: dict[str, int]
    px_to_pt: float


@dataclass(frozen=True)
class HorizontalSingleLineInkReservation:
    """Ink-informed text lane metadata for horizontal single-line image stamps."""

    lane_width_pt: int
    ink_width_pt: int
    ink_height_pt: int
    ink_left_offset_pt: int
    ink_right_slack_pt: int
    border_facing_padding_pt: int
    stamp_facing_padding_pt: int


def measure_horizontal_single_line_rendered_reference(
    preview: SigningDraftPreview,
    *,
    zoom: float = 1.0,
    roomy_width_padding_pt: float = 384.0,
    roomy_height_padding_pt: float = 64.0,
    render_port: PreviewRasterRenderer | None = None,
    ink_measurement_port: RenderedInkMeasurementPort | None = None,
) -> HorizontalSingleLineRenderedReference | None:
    """Measure structural and glyph-ink text bounds in a roomy canonical render."""

    if not _applies_to_horizontal_single_line_image_stamp(
        layout_template=preview.layout_template,
        stamp_position=preview.stamp_position,
        has_visible_stamp_image=preview.image_stamp_path is not None,
    ):
        return None
    if preview.signature_rect is None or preview.text_style is None:
        return None

    reference_rect = _roomy_reference_rect(
        preview.signature_rect,
        width_padding_pt=roomy_width_padding_pt,
        height_padding_pt=roomy_height_padding_pt,
    )
    snapshot = None
    try:
        from foliaseal.application.signing_preview_renderer import (
            render_canonical_signature_preview,
        )
        from foliaseal.application.text_raster_analysis import (
            DefaultRenderedInkMeasurementPort,
        )
        from foliaseal.application.visible_signature_color import text_style_color_rgba

        snapshot = render_canonical_signature_preview(
            replace(preview, signature_rect=reference_rect),
            zoom=zoom,
            include_border=True,
            flatten_to_white=True,
            use_horizontal_ink_reservation=False,
            render_port=render_port,
        )
        if (
            snapshot is None
            or snapshot.text_area_bounds_px is None
            or snapshot.text_bounds_px is None
        ):
            return None
        measurement_port = ink_measurement_port or DefaultRenderedInkMeasurementPort()
        measurement = measurement_port.measure(
            RenderedInkMeasurementRequest(
                preview_image_path=snapshot.image_path,
                text_widget_bounds=snapshot.text_area_bounds_px,
                text_color_rgba=text_style_color_rgba(preview.text_style),
                reference_text_content_bounds=snapshot.text_bounds_px,
            )
        )
        rendered_ink_bounds_px = measurement.bounds_px
        if rendered_ink_bounds_px is None:
            return None
        px_to_pt = reference_rect.width_pt / max(1, snapshot.width_px)
        return HorizontalSingleLineRenderedReference(
            preview_size_px={"width": snapshot.width_px, "height": snapshot.height_px},
            structural_text_bounds_px=dict(snapshot.text_bounds_px),
            rendered_ink_bounds_px=dict(rendered_ink_bounds_px),
            structural_text_bounds_pt=_rect_px_to_pt(snapshot.text_bounds_px, px_to_pt),
            rendered_ink_bounds_pt=_rect_px_to_pt(rendered_ink_bounds_px, px_to_pt),
            px_to_pt=px_to_pt,
        )
    except Exception:
        return None
    finally:
        if snapshot is not None:
            snapshot_parent = Path(snapshot.image_path).parent
            if snapshot_parent.name.startswith("foliaseal-canonical-preview-"):
                shutil.rmtree(snapshot_parent, ignore_errors=True)


def build_horizontal_single_line_ink_reservation(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    has_visible_stamp_image: bool,
    structural_text_box_width_pt: int,
    structural_text_box_height_pt: int,
    structural_text_bounds_px: Mapping[str, int] | None,
    rendered_ink_bounds_px: Mapping[str, int] | None,
    px_to_pt: float,
    border_facing_padding_pt: int,
    stamp_facing_padding_pt: int,
) -> HorizontalSingleLineInkReservation | None:
    """Build a conservative ink reservation or return ``None`` to use structural layout.

    The helper only accepts rendered ink that is fully inside the structural
    text box. Missing or contradictory reference data deliberately falls back
    to the existing structural reservation path rather than inventing tighter
    geometry.
    """

    if not _applies_to_horizontal_single_line_image_stamp(
        layout_template=layout_template,
        stamp_position=stamp_position,
        has_visible_stamp_image=has_visible_stamp_image,
    ):
        return None
    if (
        structural_text_bounds_px is None
        or rendered_ink_bounds_px is None
        or px_to_pt <= 0
        or structural_text_box_width_pt <= 0
        or structural_text_box_height_pt <= 0
        or border_facing_padding_pt < 0
        or stamp_facing_padding_pt < 0
    ):
        return None

    ink_left_px = rendered_ink_bounds_px["x"] - structural_text_bounds_px["x"]
    ink_right_slack_px = (
        structural_text_bounds_px["x"]
        + structural_text_bounds_px["width"]
        - rendered_ink_bounds_px["x"]
        - rendered_ink_bounds_px["width"]
    )
    if min(ink_left_px, ink_right_slack_px) < 0:
        return None

    ink_width_pt = _px_to_int_pt(rendered_ink_bounds_px["width"], px_to_pt)
    ink_height_pt = _px_to_int_pt(rendered_ink_bounds_px["height"], px_to_pt)
    ink_left_offset_pt = _px_to_int_pt(ink_left_px, px_to_pt)
    ink_right_slack_pt = _px_to_int_pt(ink_right_slack_px, px_to_pt)
    lane_width_pt = ink_width_pt + border_facing_padding_pt + stamp_facing_padding_pt
    if lane_width_pt > structural_text_box_width_pt:
        return None
    if ink_height_pt > structural_text_box_height_pt:
        return None

    return HorizontalSingleLineInkReservation(
        lane_width_pt=lane_width_pt,
        ink_width_pt=ink_width_pt,
        ink_height_pt=ink_height_pt,
        ink_left_offset_pt=ink_left_offset_pt,
        ink_right_slack_pt=ink_right_slack_pt,
        border_facing_padding_pt=border_facing_padding_pt,
        stamp_facing_padding_pt=stamp_facing_padding_pt,
    )


def _applies_to_horizontal_single_line_image_stamp(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    has_visible_stamp_image: bool,
) -> bool:
    return (
        layout_template == SignatureLayoutTemplate.SINGLE_LINE
        and stamp_position in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
        and has_visible_stamp_image
    )


def _px_to_int_pt(value_px: int, px_to_pt: float) -> int:
    return max(0, int(round(value_px * px_to_pt)))


def _rect_px_to_pt(bounds_px: Mapping[str, int], px_to_pt: float) -> dict[str, int]:
    return {
        "x": _px_to_int_pt(bounds_px["x"], px_to_pt),
        "y": _px_to_int_pt(bounds_px["y"], px_to_pt),
        "width": _px_to_int_pt(bounds_px["width"], px_to_pt),
        "height": _px_to_int_pt(bounds_px["height"], px_to_pt),
    }


def _roomy_reference_rect(
    signature_rect: SignatureRect,
    *,
    width_padding_pt: float,
    height_padding_pt: float,
) -> SignatureRect:
    return replace(
        signature_rect,
        width_pt=max(signature_rect.width_pt, signature_rect.width_pt + width_padding_pt),
        height_pt=max(signature_rect.height_pt, signature_rect.height_pt + height_padding_pt),
    )
