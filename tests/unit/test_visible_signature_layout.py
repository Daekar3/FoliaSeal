from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.visible_signature_layout import (
    HorizontalInkMeasurement,
    HorizontalInkMeasurementRequest,
    ImageMetrics,
    LayoutRequest,
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
