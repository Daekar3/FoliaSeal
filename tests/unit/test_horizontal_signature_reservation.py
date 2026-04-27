from dataclasses import replace

from PIL import Image

from foliaseal.application.horizontal_signature_reservation import (
    HorizontalSingleLineInkReservation,
    build_horizontal_single_line_ink_reservation,
    measure_horizontal_single_line_rendered_reference,
)
from foliaseal.application.signing_draft_workflow import SigningDraftPreview
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
)
from tests.support.phase3_builders import build_signature_rect


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


def test_measure_horizontal_single_line_rendered_reference_returns_roomy_ink_geometry(
    tmp_path,
) -> None:
    stamp_path = tmp_path / "stamp.png"

    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=0,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=280.0,
            height_pt=24.0,
        ),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:34",
        issues=(),
        can_submit=True,
    )

    reference = measure_horizontal_single_line_rendered_reference(preview, zoom=1.0)

    assert reference is not None
    assert reference.preview_size_px["width"] > int(preview.signature_rect.width_pt)
    assert reference.structural_text_bounds_px is not None
    assert reference.rendered_ink_bounds_px is not None
    assert reference.rendered_ink_bounds_px["width"] <= reference.structural_text_bounds_px["width"]
    assert reference.rendered_ink_bounds_pt["width"] > 0
    assert reference.px_to_pt > 0


def test_measure_horizontal_single_line_rendered_reference_is_limited_to_target_layouts(
    tmp_path,
) -> None:
    stamp_path = tmp_path / "stamp.png"

    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=0,
        signature_rect=build_signature_rect(page_index=0),
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:34",
        issues=(),
        can_submit=True,
    )

    assert (
        measure_horizontal_single_line_rendered_reference(
            replace(preview, layout_template=SignatureLayoutTemplate.MULTI_LINE)
        )
        is None
    )
    assert (
        measure_horizontal_single_line_rendered_reference(
            replace(preview, stamp_position=SignatureStampPosition.TOP)
        )
        is None
    )
    assert (
        measure_horizontal_single_line_rendered_reference(
            replace(preview, image_stamp_path=None)
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
