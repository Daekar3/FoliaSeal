from foliaseal.application.horizontal_signature_reservation import (
    HorizontalSingleLineInkReservation,
    build_horizontal_single_line_ink_reservation,
)
from foliaseal.domain.models import SignatureLayoutTemplate, SignatureStampPosition


def test_horizontal_single_line_ink_reservation_uses_measured_ink_inside_structural_box() -> None:
    reservation = build_horizontal_single_line_ink_reservation(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        has_visible_stamp_image=True,
        structural_text_box_width_pt=254,
        structural_text_box_height_pt=18,
        structural_text_bounds_px={"x": 40, "y": 10, "width": 254, "height": 18},
        rendered_ink_bounds_px={"x": 52, "y": 12, "width": 210, "height": 12},
        px_to_pt=1.0,
        border_facing_padding_pt=4,
        stamp_facing_padding_pt=4,
    )

    assert reservation == HorizontalSingleLineInkReservation(
        lane_width_pt=218,
        ink_width_pt=210,
        ink_height_pt=12,
        ink_left_offset_pt=12,
        ink_right_slack_pt=32,
        border_facing_padding_pt=4,
        stamp_facing_padding_pt=4,
    )


def test_horizontal_single_line_ink_reservation_is_limited_to_visible_horizontal_image_stamps(
) -> None:
    common_kwargs = {
        "has_visible_stamp_image": True,
        "structural_text_box_width_pt": 254,
        "structural_text_box_height_pt": 18,
        "structural_text_bounds_px": {"x": 40, "y": 10, "width": 254, "height": 18},
        "rendered_ink_bounds_px": {"x": 52, "y": 12, "width": 210, "height": 12},
        "px_to_pt": 1.0,
        "border_facing_padding_pt": 4,
        "stamp_facing_padding_pt": 4,
    }

    assert (
        build_horizontal_single_line_ink_reservation(
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            **common_kwargs,
        )
        is None
    )
    assert (
        build_horizontal_single_line_ink_reservation(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            **common_kwargs,
        )
        is None
    )
    assert (
        build_horizontal_single_line_ink_reservation(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            **{**common_kwargs, "has_visible_stamp_image": False},
        )
        is None
    )


def test_horizontal_single_line_ink_reservation_falls_back_when_reference_is_not_safe() -> None:
    assert (
        build_horizontal_single_line_ink_reservation(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.RIGHT,
            has_visible_stamp_image=True,
            structural_text_box_width_pt=254,
            structural_text_box_height_pt=18,
            structural_text_bounds_px={"x": 40, "y": 10, "width": 254, "height": 18},
            rendered_ink_bounds_px={"x": 35, "y": 12, "width": 260, "height": 12},
            px_to_pt=1.0,
            border_facing_padding_pt=4,
            stamp_facing_padding_pt=4,
        )
        is None
    )
    assert (
        build_horizontal_single_line_ink_reservation(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.RIGHT,
            has_visible_stamp_image=True,
            structural_text_box_width_pt=214,
            structural_text_box_height_pt=18,
            structural_text_bounds_px={"x": 40, "y": 10, "width": 254, "height": 18},
            rendered_ink_bounds_px={"x": 52, "y": 12, "width": 210, "height": 12},
            px_to_pt=1.0,
            border_facing_padding_pt=4,
            stamp_facing_padding_pt=4,
        )
        is None
    )
