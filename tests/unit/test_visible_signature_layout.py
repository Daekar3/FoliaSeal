from __future__ import annotations

from dataclasses import dataclass, replace
from math import ceil

import pytest
from PIL import Image

from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.visible_signature_layout import (
    CanonicalPreviewLayout,
    HorizontalInkMeasurement,
    HorizontalInkMeasurementRequest,
    ImageMetrics,
    RectBounds,
    SignatureLayoutPlan,
    SignatureLayoutReservation,
    SigningVisibleSignatureStyle,
    TextMetrics,
    VisibleSignatureLayoutEngine,
    VisibleSignatureLayoutInput,
    VisibleSignatureLayoutOptions,
    VisibleSignatureLayoutPolicy,
    VisibleSignatureLayoutRequest,
    VisibleSignatureLayoutService,
)
from foliaseal.application.visible_signature_layout_adapters import (
    PyHankoSignatureAppearanceAdapter,
    materialize_background_layout,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureImageProminence,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
)
from tests.support.signing_builders import build_signature_appearance


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
        if image_stamp_path is None:
            return None
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


def _materialized_layout(
    *,
    appearance: SigningBackendAppearance,
    stamp_text: str,
    stamp_background: object | None,
    signature_rect: SignatureRect,
    options: VisibleSignatureLayoutOptions | None = None,
    service: VisibleSignatureLayoutService | None = None,
    preview: bool = False,
):
    preparation = (service or VisibleSignatureLayoutService()).prepare(
        VisibleSignatureLayoutRequest(
            appearance=appearance,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            signature_rect=signature_rect,
            options=options or VisibleSignatureLayoutOptions(),
        )
    )
    return preparation.preview() if preview else preparation.signing()


def _box_style(
    *,
    show_border: bool = True,
    border_width_pt: float = 1.0,
) -> SignatureBoxStyle:
    return SignatureBoxStyle(
        show_border=show_border,
        border_color_hex="#000000",
        border_width_pt=border_width_pt,
        background_color_hex="#FFFFFF",
    )


@pytest.mark.parametrize(
    ("stamp_position", "height", "expected"),
    [
        (SignatureStampPosition.TOP, 72, (4, 6)),
        (SignatureStampPosition.BOTTOM, 25, (2, 2)),
        (SignatureStampPosition.LEFT, 72, (4, 6)),
        (SignatureStampPosition.RIGHT, 72, (4, 6)),
    ],
)
def test_visible_layout_policy_exposes_canonical_spacing(
    stamp_position: SignatureStampPosition,
    height: int,
    expected: tuple[int, int],
) -> None:
    spacing = VisibleSignatureLayoutPolicy.spacing(
        stamp_position=stamp_position,
        box_height_pt=height,
    )

    assert (spacing.edge_margin_pt, spacing.separator_width_pt) == expected


def test_visible_layout_policy_margins_include_border_safe_inset() -> None:
    margins = VisibleSignatureLayoutPolicy.margins(
        stamp_position=SignatureStampPosition.TOP,
        box_height_pt=72,
        box_style=_box_style(border_width_pt=8.0),
    )

    assert (margins.left, margins.right, margins.top, margins.bottom) == (5, 5, 5, 5)


def test_visible_layout_policy_reservation_is_public_and_fit_checked() -> None:
    reservation = VisibleSignatureLayoutPolicy.reservation(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        signature_rect=SignatureRect(
            page_index=0,
            left_pt=20,
            bottom_pt=40,
            width_pt=260,
            height_pt=72,
        ),
        text_box_width_pt=120,
        text_box_height_pt=16,
        box_style=_box_style(),
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.0,
    )

    assert isinstance(reservation, SignatureLayoutReservation)
    VisibleSignatureLayoutPolicy.ensure_fit(reservation, has_visible_stamp_image=True)
    assert reservation.text_area_width_pt > 0


def _request(
    *,
    rect: SignatureRect | None = None,
    layout_template: SignatureLayoutTemplate = SignatureLayoutTemplate.SINGLE_LINE,
    stamp_position: SignatureStampPosition = SignatureStampPosition.LEFT,
    image_stamp_path: str | None = "stamp.png",
    show_border: bool = True,
    border_width_pt: float = 1.0,
) -> VisibleSignatureLayoutInput:
    return VisibleSignatureLayoutInput(
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
        box_style=_box_style(
            show_border=show_border,
            border_width_pt=border_width_pt,
        ),
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


@pytest.mark.parametrize(
    ("prominence", "expected_fraction"),
    [
        (SignatureImageProminence.SUPPORTING, 0.35),
        (SignatureImageProminence.BALANCED, 0.55),
        (SignatureImageProminence.PRIMARY, 0.75),
    ],
)
def test_layout_request_allocates_explicit_image_prominence(
    prominence: SignatureImageProminence,
    expected_fraction: float,
) -> None:
    plan = _engine(text_width=40, text_height=12).plan(
        VisibleSignatureLayoutInput(
            signature_rect=SignatureRect(
                page_index=0,
                left_pt=0,
                bottom_pt=0,
                width_pt=300,
                height_pt=100,
            ),
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            text_style=SignatureTextStyle(font_family="Serif", font_size_pt=8.5),
            box_style=_box_style(),
            stamp_text="Signed by Ada",
            image_stamp_path="stamp.png",
            image_prominence=prominence,
        )
    )

    available = plan.text_area_width_pt + plan.stamp_area_width_pt
    actual_fraction = plan.stamp_area_width_pt / available
    assert actual_fraction == pytest.approx(expected_fraction, abs=0.03)


def test_layout_request_image_only_uses_the_available_content_area() -> None:
    plan = _engine().plan(
        VisibleSignatureLayoutInput(
            signature_rect=SignatureRect(
                page_index=0,
                left_pt=0,
                bottom_pt=0,
                width_pt=300,
                height_pt=100,
            ),
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            text_style=SignatureTextStyle(font_family="Serif", font_size_pt=8.5),
            box_style=_box_style(),
            stamp_text=" ",
            image_stamp_path="stamp.png",
            image_prominence=SignatureImageProminence.PRIMARY,
        )
    )

    assert plan.text_box == TextMetrics(width_pt=0, height_pt=0, line_count=0)
    assert plan.text_area_width_pt == 292
    assert plan.text_area_height_pt == 0
    assert plan.stamp_area_height_pt == 92
    assert plan.fit_issues == ()


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


def test_bottom_no_stamp_plan_uses_optical_text_alignment() -> None:
    plan = _engine(text_width=180, text_height=16, image=None).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=260.0,
                height_pt=25.0,
            ),
            stamp_position=SignatureStampPosition.BOTTOM,
            image_stamp_path=None,
            border_width_pt=3.5,
        )
    )

    assert plan.stamp_layout.y_align == "ALIGN_MID"
    assert plan.text_layout.y_align == "ALIGN_MAX"
    assert plan.text_layout.margins.top < plan.text_layout.margins.bottom


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM],
)
def test_compact_vertical_single_line_plan_uses_symmetric_outer_clearance(
    stamp_position: SignatureStampPosition,
) -> None:
    plan = _engine(text_width=180, text_height=16).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=262.0,
                height_pt=25.0,
            ),
            stamp_position=stamp_position,
        )
    )

    if stamp_position == SignatureStampPosition.TOP:
        assert plan.stamp_layout.margins.top == plan.text_layout.margins.bottom
    else:
        assert plan.text_layout.margins.top == plan.stamp_layout.margins.bottom


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM],
)
def test_compact_vertical_single_line_plan_increases_outer_clearance_with_border(
    stamp_position: SignatureStampPosition,
) -> None:
    rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=262.0,
        height_pt=25.0,
    )
    thin_plan = _engine(text_width=180, text_height=16).plan(
        _request(
            rect=rect,
            stamp_position=stamp_position,
            border_width_pt=1.0,
        )
    )
    thick_plan = _engine(text_width=180, text_height=16).plan(
        _request(
            rect=rect,
            stamp_position=stamp_position,
            border_width_pt=3.5,
        )
    )

    if stamp_position == SignatureStampPosition.TOP:
        assert thick_plan.stamp_layout.margins.top > thin_plan.stamp_layout.margins.top
        assert thick_plan.text_layout.margins.bottom > thin_plan.text_layout.margins.bottom
    else:
        assert thick_plan.text_layout.margins.top > thin_plan.text_layout.margins.top
        assert thick_plan.stamp_layout.margins.bottom > thin_plan.stamp_layout.margins.bottom


@pytest.mark.parametrize(
    "stamp_position, width_pt, height_pt",
    [
        (SignatureStampPosition.TOP, 260.0, 22.0),
        (SignatureStampPosition.BOTTOM, 260.0, 22.0),
        (SignatureStampPosition.LEFT, 260.0, 40.0),
        (SignatureStampPosition.RIGHT, 260.0, 40.0),
    ],
)
def test_plan_uses_border_aware_outer_insets(
    stamp_position: SignatureStampPosition,
    width_pt: float,
    height_pt: float,
) -> None:
    plan = _engine(text_width=120, text_height=18).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=width_pt,
                height_pt=height_pt,
            ),
            stamp_position=stamp_position,
            border_width_pt=7.0,
        )
    )

    expected_edge_margin = 5
    for layout in (plan.stamp_layout, plan.text_layout):
        assert layout.margins.top >= expected_edge_margin
        assert layout.margins.bottom >= expected_edge_margin
        assert layout.margins.left >= expected_edge_margin
        assert layout.margins.right >= expected_edge_margin


@pytest.mark.parametrize(
    (
        "stamp_position",
        "expected_text_left_margin",
        "expected_text_right_margin",
    ),
    [
        (SignatureStampPosition.LEFT, 39, 4),
        (SignatureStampPosition.RIGHT, 4, 39),
    ],
)
def test_horizontal_single_line_plan_preserves_border_facing_text_margin(
    stamp_position: SignatureStampPosition,
    expected_text_left_margin: int,
    expected_text_right_margin: int,
) -> None:
    plan = _engine(
        text_width=254,
        text_height=18,
        image=ImageMetrics(width_px=410, height_px=100, aspect_ratio=4.1),
    ).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=35.84,
                bottom_pt=428.99,
                width_pt=296.96,
                height_pt=22.53,
            ),
            stamp_position=stamp_position,
        )
    )

    assert plan.stamp_area_width_pt == 29
    assert plan.text_layout.margins.left == expected_text_left_margin
    assert plan.text_layout.margins.right == expected_text_right_margin


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
@pytest.mark.parametrize("border_width_pt", [1.0, 8.0])
def test_horizontal_single_line_image_plan_preserves_both_edge_invariants(
    stamp_position: SignatureStampPosition,
    border_width_pt: float,
) -> None:
    rect = SignatureRect(
        page_index=0,
        left_pt=35.84,
        bottom_pt=428.99,
        width_pt=430.0,
        height_pt=44.0,
    )
    plan = _engine(
        text_width=254,
        text_height=18,
        image=ImageMetrics(width_px=410, height_px=100, aspect_ratio=4.1),
    ).plan(
        _request(
            rect=rect,
            stamp_position=stamp_position,
            border_width_pt=border_width_pt,
        )
    )

    edge_margin = max(4, int(ceil(border_width_pt / 2.0)) + 1)
    separator_width = min(
        6,
        max(int(round(rect.width_pt)) - edge_margin * 2 - plan.text_area_width_pt, 0),
    )
    stamp_facing_margin = plan.stamp_area_width_pt + separator_width + edge_margin

    assert plan.text_layout.margins.top == edge_margin
    assert plan.text_layout.margins.bottom == edge_margin
    if stamp_position == SignatureStampPosition.LEFT:
        assert plan.text_layout.margins.right == edge_margin
        assert plan.text_layout.margins.left == stamp_facing_margin
    else:
        assert plan.text_layout.margins.left == edge_margin
        assert plan.text_layout.margins.right == stamp_facing_margin


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
    from foliaseal.application import signing_backend as backend
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

    ink_measurer = FakeHorizontalInkMeasurer(
        measurement=HorizontalInkMeasurement(
            structural_text_bounds_px=RectBounds(x=40, y=8, width=200, height=18),
            rendered_ink_bounds_px=RectBounds(x=52, y=10, width=20, height=12),
            px_to_pt=1.0,
        ),
        requests=[],
    )
    expected_style = _existing_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        signature_rect=signature_rect,
        ink_measurer=ink_measurer,
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


def test_layout_service_builds_backend_signing_style_from_public_facade(tmp_path) -> None:
    stamp_path = _write_stamp(tmp_path)
    appearance = _backend_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        image_stamp_path=stamp_path,
        show_border=True,
    )
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=320.0,
        height_pt=120.0,
    )
    stamp_text = "Digitally signed by\nMorgan Ellery\nFoliaSeal"

    expected_plan = VisibleSignatureLayoutEngine().plan(
        _layout_request(
            signature_rect=signature_rect,
            appearance=appearance,
            stamp_text=stamp_text,
        )
    )
    expected_style = PyHankoSignatureAppearanceAdapter().build_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        layout_plan=expected_plan,
    )

    service_result = _materialized_layout(
        appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(),
    )

    assert isinstance(service_result, SigningVisibleSignatureStyle)
    assert service_result.layout_plan == expected_plan
    assert service_result.fit_issues == ()
    assert service_result.content_layout is service_result.stamp_style.inner_content_layout
    assert service_result.background_layout is service_result.stamp_style.background_layout
    assert _style_snapshot(service_result.stamp_style) == _style_snapshot(expected_style)


@pytest.mark.parametrize(
    ("layout_template", "stamp_position", "expected_x_align", "expected_y_align"),
    [
        (
            SignatureLayoutTemplate.SINGLE_LINE,
            SignatureStampPosition.TOP,
            "ALIGN_MID",
            "ALIGN_MAX",
        ),
        (
            SignatureLayoutTemplate.MULTI_LINE,
            SignatureStampPosition.LEFT,
            "ALIGN_MIN",
            "ALIGN_MID",
        ),
        (
            SignatureLayoutTemplate.WRAPPED_BLOCK,
            SignatureStampPosition.BOTTOM,
            "ALIGN_MID",
            "ALIGN_MIN",
        ),
    ],
)
def test_layout_service_exposes_background_layout_policy_through_public_facade(
    tmp_path,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    expected_x_align: str,
    expected_y_align: str,
) -> None:
    stamp_path = _write_stamp(tmp_path)
    appearance = _backend_appearance(
        layout_template=layout_template,
        stamp_position=stamp_position,
        image_stamp_path=stamp_path,
        show_border=True,
    )
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=320.0,
        height_pt=120.0,
    )

    service_result = _materialized_layout(
        appearance=appearance,
        stamp_text="Digitally signed by\nMorgan Ellery\nFoliaSeal",
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(),
    )

    assert service_result.background_layout.x_align.name == expected_x_align
    assert service_result.background_layout.y_align.name == expected_y_align
    assert service_result.background_layout.inner_content_scaling.name == "SHRINK_TO_FIT"


def test_layout_service_keeps_distinct_top_and_bottom_single_line_stamp_layouts(
    tmp_path,
) -> None:
    stamp_path = _write_stamp(tmp_path)
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=260.0,
        height_pt=40.0,
    )

    top_result = _materialized_layout(
        appearance=_backend_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            image_stamp_path=stamp_path,
            show_border=True,
        ),
        stamp_text="Digitally signed by\nMorgan Ellery",
        stamp_background=_stamp_background(stamp_path),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(),
    )
    bottom_result = _materialized_layout(
        appearance=_backend_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.BOTTOM,
            image_stamp_path=stamp_path,
            show_border=True,
        ),
        stamp_text="Digitally signed by\nMorgan Ellery",
        stamp_background=_stamp_background(stamp_path),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(),
    )

    assert top_result.background_layout.y_align != bottom_result.background_layout.y_align
    assert top_result.background_layout.margins.top < top_result.background_layout.margins.bottom
    assert (
        bottom_result.background_layout.margins.bottom < bottom_result.background_layout.margins.top
    )


def test_layout_service_keeps_horizontal_single_line_stamp_inside_reserved_lane(
    tmp_path,
) -> None:
    stamp_path = _write_stamp(tmp_path)
    appearance = _backend_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path=stamp_path,
        show_border=True,
    )
    signature_rect = SignatureRect(
        page_index=3,
        left_pt=36.86,
        bottom_pt=429.5,
        width_pt=384.506,
        height_pt=28.678,
    )

    service_result = _materialized_layout(
        appearance=appearance,
        stamp_text="Digitally signed by\nMorgan Ellery | FoliaSeal",
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(),
    )

    fitted_height = (
        service_result.layout_plan.container_height_pt
        - service_result.background_layout.margins.top
        - service_result.background_layout.margins.bottom
    )

    assert fitted_height <= service_result.layout_plan.stamp_area_height_pt - 4


def test_layout_service_builds_canonical_preview_style_from_public_facade(tmp_path) -> None:
    stamp_path = _write_stamp(tmp_path)
    appearance = _backend_appearance(
        layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.BOTTOM,
        image_stamp_path=stamp_path,
        show_border=True,
    )
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=320.0,
        height_pt=120.0,
    )
    stamp_text = "Digitally signed by\nMorgan Ellery\nFoliaSeal"
    expected_plan = VisibleSignatureLayoutEngine().plan(
        _layout_request(
            signature_rect=signature_rect,
            appearance=appearance,
            stamp_text=stamp_text,
        )
    )
    expected_style = PyHankoSignatureAppearanceAdapter().build_stamp_style(
        appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        layout_plan=expected_plan,
        allow_fit_issues=True,
    )

    service_result = _materialized_layout(
        appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background(appearance.image_stamp_path),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        preview=True,
    )

    assert isinstance(service_result, CanonicalPreviewLayout)
    assert service_result.layout_plan == expected_plan
    assert service_result.stamp_suppressed is False
    assert service_result.content_layout is service_result.style.inner_content_layout
    assert _style_snapshot(service_result.style) == _style_snapshot(expected_style)


def test_layout_service_suppresses_collapsed_horizontal_preview_stamp() -> None:
    appearance = _backend_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        image_stamp_path="stamp.png",
        show_border=True,
    )
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=100.0,
        height_pt=32.0,
    )

    service = VisibleSignatureLayoutService(
        text_measurer=FakeTextMeasurer(width_pt=200, height_pt=16),
        image_probe=FakeStampImageProbe(
            ImageMetrics(width_px=400, height_px=100, aspect_ratio=4.0)
        ),
    )
    service_result = _materialized_layout(
        service=service,
        appearance=appearance,
        stamp_text="Digitally signed by Morgan Ellery",
        stamp_background=object(),
        signature_rect=signature_rect,
        options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        preview=True,
    )

    assert service_result.stamp_suppressed is True
    assert service_result.style.background is None
    assert service_result.layout_plan.has_visible_stamp_image is False
    assert service_result.layout_plan.stamp_area_width_pt == 0


def test_background_layout_helper_adds_border_facing_inset_for_top_multi_line_stamp(
    tmp_path,
) -> None:
    stamp_path = _write_stamp(tmp_path)
    signature_rect = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=40.0,
        width_pt=260.0,
        height_pt=46.0,
    )
    appearance = _backend_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.TOP,
        image_stamp_path=stamp_path,
        show_border=True,
    )

    plan = VisibleSignatureLayoutEngine().plan(
        _layout_request(
            signature_rect=signature_rect,
            appearance=appearance,
            stamp_text="Digitally signed by\nMorgan Ellery",
        )
    )

    background_layout = materialize_background_layout(
        appearance.layout_template,
        stamp_position=appearance.stamp_position,
        stamp_background=_stamp_background(stamp_path),
        signature_rect=signature_rect,
        text_box_width=plan.background_text_box_width_pt,
        text_box_height=plan.text_box.height_pt,
        box_style=appearance.box_style,
        stamp_aspect_ratio=plan.stamp_image.aspect_ratio if plan.stamp_image else None,
    )

    assert background_layout.margins.top > plan.stamp_layout.margins.top


def test_layout_boundary_rejects_text_that_exceeds_reserved_height() -> None:
    plan = _engine(text_width=120, text_height=40).plan(
        _request(
            rect=SignatureRect(
                page_index=0,
                left_pt=20.0,
                bottom_pt=40.0,
                width_pt=260.0,
                height_pt=25.0,
            ),
            image_stamp_path=None,
            stamp_position=SignatureStampPosition.TOP,
        )
    )

    assert plan.fit_issues
    assert plan.fit_issues[0].code == "visible_signature_layout_unavailable"
    assert "Visible signature content does not fit" in plan.fit_issues[0].message


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
    # These adapter fixtures intentionally exercise the legacy low-level reservation path;
    # production Appearance requests now carry explicit Primary/Supporting/Balanced semantics.
    return replace(
        SigningBackendAppearance.from_signature_appearance(appearance),
        image_prominence=None,
    )


def _layout_request(
    *,
    signature_rect: SignatureRect,
    appearance: SigningBackendAppearance,
    stamp_text: str,
) -> VisibleSignatureLayoutInput:
    return VisibleSignatureLayoutInput(
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
    ink_measurer: FakeHorizontalInkMeasurer | None = None,
):
    return (
        VisibleSignatureLayoutService.production()
        .prepare(
            VisibleSignatureLayoutRequest(
                appearance=appearance,
                stamp_text=stamp_text,
                stamp_background=_stamp_background(appearance.image_stamp_path),
                signature_rect=signature_rect,
                ink_measurer=ink_measurer,
            )
        )
        .signing()
        .stamp_style
    )


def _stamp_background(image_stamp_path: str | None):
    from foliaseal.application.stamp_background import stamp_background_for_path

    return stamp_background_for_path(image_stamp_path)


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
