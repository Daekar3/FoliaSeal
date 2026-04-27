"""Shared reservation model for horizontal single-line signature layouts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition


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
    ink_top_px = rendered_ink_bounds_px["y"] - structural_text_bounds_px["y"]
    ink_right_slack_px = (
        structural_text_bounds_px["x"]
        + structural_text_bounds_px["width"]
        - rendered_ink_bounds_px["x"]
        - rendered_ink_bounds_px["width"]
    )
    ink_bottom_slack_px = (
        structural_text_bounds_px["y"]
        + structural_text_bounds_px["height"]
        - rendered_ink_bounds_px["y"]
        - rendered_ink_bounds_px["height"]
    )
    if min(ink_left_px, ink_top_px, ink_right_slack_px, ink_bottom_slack_px) < 0:
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
