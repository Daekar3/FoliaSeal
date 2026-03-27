import pytest

from pdf_signer.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewRect,
    ViewTransform,
    pdf_point_to_view,
    pdf_rect_to_view_rect,
    validate_pdf_rect_within_page,
    view_point_to_pdf,
    view_rect_to_pdf_rect,
)


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_view_to_pdf_round_trip_for_point(rotation: int) -> None:
    page_box = PageBox(left=20, bottom=40, right=620, top=840)
    transform = ViewTransform(zoom=1.5, pan_x=15, pan_y=30)

    original_pdf_point = (145.0, 233.0)
    view_point = pdf_point_to_view(
        pdf_x=original_pdf_point[0],
        pdf_y=original_pdf_point[1],
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )
    recovered_pdf_point = view_point_to_pdf(
        view_x=view_point[0],
        view_y=view_point[1],
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )

    assert recovered_pdf_point == pytest.approx(original_pdf_point)


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_view_rect_to_pdf_rect_returns_normalized_bounds(rotation: int) -> None:
    page_box = PageBox(left=0, bottom=0, right=400, top=300)
    transform = ViewTransform(zoom=2.0, pan_x=10, pan_y=20)
    view_rect = ViewRect(x1=350, y1=310, x2=140, y2=90)

    pdf_rect = view_rect_to_pdf_rect(
        view_rect=view_rect,
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )

    assert pdf_rect.x1 <= pdf_rect.x2
    assert pdf_rect.y1 <= pdf_rect.y2


@pytest.mark.parametrize(
    ("pdf_rect", "expected"),
    [
        (PdfRect(10, 10, 100, 120), True),
        (PdfRect(-1, 10, 100, 120), False),
        (PdfRect(10, 10, 401, 120), False),
        (PdfRect(10, -5, 100, 120), False),
        (PdfRect(10, 10, 100, 305), False),
    ],
)
def test_validate_pdf_rect_within_page(pdf_rect: PdfRect, expected: bool) -> None:
    page_box = PageBox(left=0, bottom=0, right=400, top=300)

    assert validate_pdf_rect_within_page(pdf_rect, page_box=page_box) is expected


def test_rejects_non_multiple_of_90_rotation() -> None:
    with pytest.raises(ValueError):
        view_point_to_pdf(
            view_x=0,
            view_y=0,
            transform=ViewTransform(zoom=1.0, pan_x=0, pan_y=0),
            page_box=PageBox(left=0, bottom=0, right=100, top=100),
            rotation=45,
        )


def test_rejects_non_positive_zoom() -> None:
    with pytest.raises(ValueError):
        view_point_to_pdf(
            view_x=0,
            view_y=0,
            transform=ViewTransform(zoom=0.0, pan_x=0, pan_y=0),
            page_box=PageBox(left=0, bottom=0, right=100, top=100),
            rotation=0,
        )


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_pdf_rect_round_trip_via_view_rect(rotation: int) -> None:
    page_box = PageBox(left=20, bottom=40, right=620, top=840)
    transform = ViewTransform(zoom=1.25, pan_x=18, pan_y=22)
    original = PdfRect(x1=100, y1=120, x2=180, y2=210)

    view_rect = pdf_rect_to_view_rect(
        pdf_rect=original, transform=transform, page_box=page_box, rotation=rotation
    )
    recovered = view_rect_to_pdf_rect(
        view_rect=view_rect, transform=transform, page_box=page_box, rotation=rotation
    )

    assert recovered == pytest.approx(original.normalized())


def test_rejects_non_positive_page_box_dimensions() -> None:
    with pytest.raises(ValueError, match="Page box must have positive width and height"):
        view_point_to_pdf(
            view_x=0,
            view_y=0,
            transform=ViewTransform(zoom=1.0, pan_x=0, pan_y=0),
            page_box=PageBox(left=10, bottom=0, right=10, top=100),
            rotation=0,
        )


def test_validate_pdf_rect_within_page_rejects_invalid_page_box() -> None:
    with pytest.raises(ValueError, match="Page box must have positive width and height"):
        validate_pdf_rect_within_page(
            PdfRect(0, 0, 10, 10),
            page_box=PageBox(left=0, bottom=5, right=10, top=5),
        )
