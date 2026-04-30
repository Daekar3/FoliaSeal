from __future__ import annotations

from dataclasses import dataclass

import pytest
from PIL import Image

from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.visible_signature_layout import (
    HorizontalInkMeasurement,
    HorizontalInkMeasurementRequest,
    ImageMetrics,
    LayoutRequest,
    PyHankoSignatureAppearanceAdapter,
    RectBounds,
    SignatureLayoutPlan,
    TextMetrics,
    VisibleSignatureLayoutEngine,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
)
from tests.support.phase3_builders import build_signature_appearance


@dataclass(frozen=True)
class FakeTextMeasurer:
    width_pt: int = 120
    height_pt: int = 16
    line_count: int = 1

    def measure(self, text: str, text_style: SignatureTextStyle) -> TextMetrics:
        del text, text_style
        return TextMetrics(
            width_pt=self.width_pt,
            height_pt=self.height_pt,
            line_count=self.line_count,
        )


@dataclass(frozen=True)
class FakeStampImageProbe:
    metrics: ImageMetrics | None = ImageMetrics(width_px=400, height_px=100, aspect_ratio=4.0)

    def inspect(self, image_stamp_path: str | None) -> ImageMetrics | None:
        del image_stamp_path
        return self.metrics


@dataclass
class FakeHorizontalInkMeasurer:
    measurement: HorizontalInkMeasurement | None
    requests: list[HorizontalInkMeasurementRequest]

    def measure(
        self,
        request: HorizontalInkMeasurementRequest,
    ) -> HorizontalInkMeasurement | None:
        self.requests.append(request)
        return self.measurement


def _box_style(*, show_border: bool = True) -> SignatureBoxStyle:
    return SignatureBoxStyle(
        show_border=show_border,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )


def _request(
    *,
    rect: SignatureRect | None = None,
    layout_template: SignatureLayoutTemplate = SignatureLayoutTemplate.SINGLE_LINE,
    stamp_position: SignatureStampPosition = SignatureStampPosition.LEFT,
    image_stamp_path: str | None = "stamp.png",
    show_border: bool = True,
) -> LayoutRequest:
    return LayoutRequest(
        signature_rect=rect
        or SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=40.0,
            width_pt=260.0,
            height_pt=40.0,
        ),
        layout_template=layout_template,
        stamp_position=stamp_position,
        text_style=SignatureTextStyle(font_family="Serif", font_size_pt=8.5),
        box_style=_box_style(show_border=show_border),
        stamp_text="Digitally signed by\nMorgan Ellery",
        image_stamp_path=image_stamp_path,
    )


def _engine(
    *,
    text_width: int = 120,
    text_height: int = 16,
    image: ImageMetrics | None = ImageMetrics(width_px=400, height_px=100, aspect_ratio=4.0),
    ink: FakeHorizontalInkMeasurer | None = None,
) -> VisibleSignatureLayoutEngine:
    return VisibleSignatureLayoutEngine(
        text_measurer=FakeTextMeasurer(width_pt=text_width, height_pt=text_height),
        image_probe=FakeStampImageProbe(image),
        ink_measurer=ink,
    )


def test_plan_reserves_text_and_stamp_areas_for_horizontal_image_stamp() -> None:
    plan = _engine().plan(_request())

    assert isinstance(plan, SignatureLayoutPlan)
    assert plan.container_width_pt == 260
    assert plan.container_height_pt == 40
    assert plan.has_visible_stamp_image is True
    assert plan.text_box == TextMetrics(width_pt=120, height_pt=16, line_count=1)
    assert plan.text_area_width_pt == 120
    assert plan.text_area_height_pt == 32
    assert plan.stamp_area_width_pt == 126
    assert plan.stamp_area_height_pt == 32
    assert plan.background_text_box_width_pt == 120
    assert plan.fit_issues == ()
    assert plan.text_layout.x_align == "ALIGN_MAX"
    assert plan.stamp_layout.x_align == "ALIGN_MIN"


def test_single_line_no_stamp_gives_usable_area_to_text_and_zero_stamp_area() -> None:
    plan = _engine(image=None).plan(
        _request(
            stamp_position=SignatureStampPosition.TOP,
            image_stamp_path=None,
        )
    )

    assert plan.has_visible_stamp_image is False
    assert plan.stamp_area_width_pt == 0
    assert plan.stamp_area_height_pt == 0
    assert plan.text_area_width_pt == 254
    assert plan.text_area_height_pt == 34
    assert plan.fit_issues == ()


def test_horizontal_ink_measurement_can_reduce_text_lane() -> None:
    ink = FakeHorizontalInkMeasurer(
        measurement=HorizontalInkMeasurement(
            structural_text_bounds_px=RectBounds(x=40, y=8, width=120, height=16),
            rendered_ink_bounds_px=RectBounds(x=52, y=10, width=80, height=12),
            px_to_pt=1.0,
        ),
        requests=[],
    )

    plan = _engine(ink=ink).plan(_request())

    assert len(ink.requests) == 1
    assert ink.requests[0].structural_text_box_width_pt == 120
    assert plan.ink_reservation is not None
    assert plan.ink_reservation.lane_width_pt == 88
    assert plan.text_area_width_pt == 88
    assert plan.stamp_area_width_pt == 158
    assert plan.background_text_box_width_pt == 78
    assert plan.fit_issues == ()


def test_horizontal_single_line_plan_gives_overwide_text_the_full_lane() -> None:
    plan = _engine(
        text_width=475,
        text_height=10,
        image=ImageMetrics(width_px=400, height_px=100, aspect_ratio=4.0),
    ).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=34.3,
                bottom_pt=428.99,
                width_pt=260.61,
                height_pt=23.04,
            ),
            stamp_position=SignatureStampPosition.RIGHT,
        )
    )

    assert plan.text_area_width_pt == plan.container_width_pt - 8
    assert plan.stamp_area_width_pt == 0


def test_horizontal_single_line_plan_prioritizes_text_before_stamp() -> None:
    plan = _engine(
        text_width=254,
        text_height=18,
        image=ImageMetrics(width_px=410, height_px=100, aspect_ratio=4.1),
    ).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=34.82,
                bottom_pt=428.48,
                width_pt=373.25,
                height_pt=36.86,
            ),
            stamp_position=SignatureStampPosition.RIGHT,
        )
    )

    assert plan.text_area_width_pt == 254
    assert plan.stamp_area_width_pt == 105
    assert plan.stamp_area_height_pt == 29


@pytest.mark.parametrize(
    (
        "layout_template",
        "stamp_position",
        "rect",
        "expected_text_width",
        "expected_text_height",
        "expected_stamp_width",
        "expected_stamp_height",
        "expected_stamp_x_align",
        "expected_text_x_align",
    ),
    [
        (
            SignatureLayoutTemplate.SINGLE_LINE,
            SignatureStampPosition.TOP,
            SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=240.0,
                height_pt=72.0,
            ),
            232,
            18,
            232,
            40,
            "ALIGN_MID",
            "ALIGN_MIN",
        ),
        (
            SignatureLayoutTemplate.MULTI_LINE,
            SignatureStampPosition.RIGHT,
            SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=240.0,
                height_pt=72.0,
            ),
            110,
            64,
            116,
            64,
            "ALIGN_MAX",
            "ALIGN_MIN",
        ),
        (
            SignatureLayoutTemplate.WRAPPED_BLOCK,
            SignatureStampPosition.BOTTOM,
            SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=240.0,
                height_pt=72.0,
            ),
            232,
            18,
            232,
            40,
            "ALIGN_MID",
            "ALIGN_MID",
        ),
    ],
)
def test_plan_allocates_template_specific_text_and_stamp_areas(
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    rect: SignatureRect,
    expected_text_width: int,
    expected_text_height: int,
    expected_stamp_width: int,
    expected_stamp_height: int,
    expected_stamp_x_align: str,
    expected_text_x_align: str,
) -> None:
    plan = _engine(text_width=110, text_height=18).plan(
        _request(
            rect=rect,
            layout_template=layout_template,
            stamp_position=stamp_position,
        )
    )

    assert plan.reserved_primary_extent_pt > 0
    assert plan.text_area_width_pt == expected_text_width
    assert plan.text_area_height_pt == expected_text_height
    assert plan.stamp_area_width_pt == expected_stamp_width
    assert plan.stamp_area_height_pt == expected_stamp_height
    assert plan.stamp_layout.x_align == expected_stamp_x_align
    assert plan.text_layout.x_align == expected_text_x_align
    assert plan.stamp_layout.scaling == "STRETCH_TO_FIT"
    assert plan.text_layout.scaling == "NO_SCALING"


def test_unsafe_horizontal_ink_measurement_falls_back_to_structural_layout() -> None:
    ink = FakeHorizontalInkMeasurer(
        measurement=HorizontalInkMeasurement(
            structural_text_bounds_px=RectBounds(x=40, y=8, width=120, height=16),
            rendered_ink_bounds_px=RectBounds(x=35, y=10, width=140, height=12),
            px_to_pt=1.0,
        ),
        requests=[],
    )

    plan = _engine(ink=ink).plan(_request())

    assert len(ink.requests) == 1
    assert plan.ink_reservation is None
    assert plan.text_area_width_pt == 120
    assert plan.stamp_area_width_pt == 126
    assert plan.fit_issues == ()


def test_fit_issue_is_returned_for_text_that_cannot_fit() -> None:
    plan = _engine(text_width=240, text_height=30).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=120.0,
                height_pt=24.0,
            ),
        )
    )

    assert len(plan.fit_issues) == 1
    issue = plan.fit_issues[0]
    assert issue.code == "visible_signature_layout_unavailable"
    assert issue.field_name == "signature_appearance"
    assert "Visible signature content does not fit" in issue.message


@pytest.mark.parametrize(
    ("layout_template", "stamp_position", "with_image", "show_border"),
    [
        (
            SignatureLayoutTemplate.SINGLE_LINE,
            SignatureStampPosition.TOP,
            True,
            True,
        ),
        (
            SignatureLayoutTemplate.SINGLE_LINE,
            SignatureStampPosition.BOTTOM,
            False,
            True,
        ),
        (
            SignatureLayoutTemplate.MULTI_LINE,
            SignatureStampPosition.LEFT,
            True,
            True,
        ),
        (
            SignatureLayoutTemplate.WRAPPED_BLOCK,
            SignatureStampPosition.RIGHT,
            True,
            False,
        ),
        (
            SignatureLayoutTemplate.MULTI_LINE,
            SignatureStampPosition.BOTTOM,
            False,
            False,
        ),
    ],
)
def test_pyhanko_adapter_matches_existing_stamp_style_for_representative_cases(
    tmp_path,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    with_image: bool,
    show_border: bool,
) -> None:
    stamp_path = _write_stamp(tmp_path) if with_image else None
    appearance = _backend_appearance(
        layout_template=layout_template,
        stamp_position=stamp_position,
        image_stamp_path=stamp_path,
        show_border=show_border,
    )
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=320.0,
        height_pt=120.0,
    )
    stamp_text = "Digitally signed by\nMorgan Ellery\nFoliaSeal"

    expected_style = _existing_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        signature_rect=signature_rect,
    )
    layout_plan = VisibleSignatureLayoutEngine().plan(
        _layout_request(
            signature_rect=signature_rect,
            appearance=appearance,
            stamp_text=stamp_text,
        )
    )
    actual_style = PyHankoSignatureAppearanceAdapter().build_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        layout_plan=layout_plan,
    )

    assert _style_snapshot(actual_style) == _style_snapshot(expected_style)


def test_pyhanko_adapter_matches_existing_stamp_style_with_injected_horizontal_ink(
    monkeypatch,
    tmp_path,
) -> None:
    from foliaseal.application import phase3_signing_backend as backend
    from foliaseal.application.horizontal_signature_reservation import (
        HorizontalSingleLineRenderedReference,
    )

    stamp_path = _write_stamp(tmp_path)
    appearance = _backend_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path=stamp_path,
        show_border=True,
    )
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=320.0,
        height_pt=42.0,
    )
    stamp_text = "Digitally signed by\nMorgan Ellery"

    def fake_reference(*_args: object, **_kwargs: object) -> HorizontalSingleLineRenderedReference:
        return HorizontalSingleLineRenderedReference(
            preview_size_px={"width": 704, "height": 106},
            structural_text_bounds_px={"x": 40, "y": 8, "width": 200, "height": 18},
            rendered_ink_bounds_px={"x": 52, "y": 10, "width": 20, "height": 12},
            structural_text_bounds_pt={"x": 40, "y": 8, "width": 200, "height": 18},
            rendered_ink_bounds_pt={"x": 52, "y": 10, "width": 20, "height": 12},
            px_to_pt=1.0,
        )

    monkeypatch.setattr(
        backend,
        "measure_horizontal_single_line_rendered_reference",
        fake_reference,
    )

    expected_style = _existing_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        signature_rect=signature_rect,
    )
    ink_measurer = FakeHorizontalInkMeasurer(
        measurement=HorizontalInkMeasurement(
            structural_text_bounds_px=RectBounds(x=40, y=8, width=200, height=18),
            rendered_ink_bounds_px=RectBounds(x=52, y=10, width=20, height=12),
            px_to_pt=1.0,
        ),
        requests=[],
    )
    layout_plan = VisibleSignatureLayoutEngine(ink_measurer=ink_measurer).plan(
        _layout_request(
            signature_rect=signature_rect,
            appearance=appearance,
            stamp_text=stamp_text,
        )
    )
    actual_style = PyHankoSignatureAppearanceAdapter().build_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        layout_plan=layout_plan,
    )

    assert layout_plan.ink_reservation is not None
    assert _style_snapshot(actual_style) == _style_snapshot(expected_style)


def _backend_appearance(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    image_stamp_path: str | None,
    show_border: bool,
) -> SigningBackendAppearance:
    appearance = build_signature_appearance(
        layout_template=layout_template,
        stamp_position=stamp_position,
        image_stamp_path=image_stamp_path,
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#123456",
        ),
        box_style=SignatureBoxStyle(
            show_border=show_border,
            border_color_hex="#333333",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )
    return SigningBackendAppearance.from_signature_appearance(appearance)


def _layout_request(
    *,
    signature_rect: SignatureRect,
    appearance: SigningBackendAppearance,
    stamp_text: str,
) -> LayoutRequest:
    return LayoutRequest(
        signature_rect=signature_rect,
        layout_template=appearance.layout_template,
        stamp_position=appearance.stamp_position,
        text_style=appearance.text_style,
        box_style=appearance.box_style,
        stamp_text=stamp_text,
        image_stamp_path=appearance.image_stamp_path,
    )


def _write_stamp(tmp_path) -> str:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (400, 100), color=(0, 0, 0, 160)).save(stamp_path)
    return str(stamp_path)


def _existing_stamp_style(
    *,
    appearance: SigningBackendAppearance,
    stamp_text: str,
    signature_rect: SignatureRect,
):
    from foliaseal.application.phase3_signing_backend import _build_stamp_style

    return _build_stamp_style(
        appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
    )


def _stamp_background(image_stamp_path: str | None):
    from foliaseal.application.phase3_signing_backend import _stamp_background_for_path

    return _stamp_background_for_path(image_stamp_path)


def _style_snapshot(style) -> dict[str, object]:
    return {
        "border_width": style.border_width,
        "border_color": style.border_color,
        "background_present": style.background is not None,
        "background_layout": _layout_snapshot(style.background_layout),
        "inner_content_layout": _layout_snapshot(style.inner_content_layout),
        "font_size": str(style.text_box_style.font_size),
        "text_color": style.text_box_style.text_color,
        "stamp_text": style.stamp_text,
        "timestamp_format": style.timestamp_format,
    }


def _layout_snapshot(layout) -> dict[str, object]:
    margins = layout.margins
    return {
        "x_align": layout.x_align,
        "y_align": layout.y_align,
        "scaling": layout.inner_content_scaling,
        "margins": (
            margins.left,
            margins.right,
            margins.top,
            margins.bottom,
        ),
    }
