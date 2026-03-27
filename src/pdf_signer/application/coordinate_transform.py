"""Phase 2 coordinate transform utilities for viewer <-> PDF mapping."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfRect:
    """Rectangle in PDF user-space coordinates (bottom-left origin)."""

    x1: float
    y1: float
    x2: float
    y2: float

    def normalized(self) -> PdfRect:
        """Return a rectangle with ascending coordinate bounds."""
        min_x, max_x = sorted((self.x1, self.x2))
        min_y, max_y = sorted((self.y1, self.y2))
        return PdfRect(x1=min_x, y1=min_y, x2=max_x, y2=max_y)


@dataclass(frozen=True)
class ViewRect:
    """Rectangle in viewer coordinates (top-left origin, pixels)."""

    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class ViewTransform:
    """View state needed for deterministic coordinate conversions."""

    zoom: float
    pan_x: float
    pan_y: float


@dataclass(frozen=True)
class PageBox:
    """Effective page box used for placement bounds (typically CropBox)."""

    left: float
    bottom: float
    right: float
    top: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def height(self) -> float:
        return self.top - self.bottom

    def validate(self) -> None:
        """Ensure page dimensions are strictly positive."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Page box must have positive width and height.")


def _normalize_rotation(rotation: int) -> int:
    if rotation % 90 != 0:
        raise ValueError("Rotation must be a multiple of 90 degrees.")
    return rotation % 360


def _display_dimensions(page_box: PageBox, rotation: int) -> tuple[float, float]:
    normalized_rotation = _normalize_rotation(rotation)
    if normalized_rotation in (0, 180):
        return page_box.width, page_box.height
    return page_box.height, page_box.width


def _pdf_local_to_display(
    page_box: PageBox,
    rotation: int,
    u: float,
    v: float,
) -> tuple[float, float]:
    normalized_rotation = _normalize_rotation(rotation)
    if normalized_rotation == 0:
        return u, v
    if normalized_rotation == 90:
        return v, page_box.width - u
    if normalized_rotation == 180:
        return page_box.width - u, page_box.height - v
    return page_box.height - v, u


def _display_to_pdf_local(
    page_box: PageBox,
    rotation: int,
    dx: float,
    dy: float,
) -> tuple[float, float]:
    normalized_rotation = _normalize_rotation(rotation)
    if normalized_rotation == 0:
        return dx, dy
    if normalized_rotation == 90:
        return page_box.width - dy, dx
    if normalized_rotation == 180:
        return page_box.width - dx, page_box.height - dy
    return dy, page_box.height - dx


def _validate_inputs(*, transform: ViewTransform, page_box: PageBox) -> None:
    if transform.zoom <= 0:
        raise ValueError("Zoom must be greater than zero.")
    page_box.validate()


def view_point_to_pdf(
    *,
    view_x: float,
    view_y: float,
    transform: ViewTransform,
    page_box: PageBox,
    rotation: int,
) -> tuple[float, float]:
    """Convert one viewer-space point to PDF user-space coordinates."""
    _validate_inputs(transform=transform, page_box=page_box)

    _, display_height = _display_dimensions(page_box, rotation)
    dx = (view_x - transform.pan_x) / transform.zoom
    dy = display_height - ((view_y - transform.pan_y) / transform.zoom)
    u, v = _display_to_pdf_local(page_box, rotation, dx, dy)
    return page_box.left + u, page_box.bottom + v


def pdf_point_to_view(
    *,
    pdf_x: float,
    pdf_y: float,
    transform: ViewTransform,
    page_box: PageBox,
    rotation: int,
) -> tuple[float, float]:
    """Convert one PDF user-space point to viewer-space coordinates."""
    _validate_inputs(transform=transform, page_box=page_box)

    _, display_height = _display_dimensions(page_box, rotation)
    u = pdf_x - page_box.left
    v = pdf_y - page_box.bottom
    dx, dy = _pdf_local_to_display(page_box, rotation, u, v)
    view_x = transform.pan_x + (dx * transform.zoom)
    view_y = transform.pan_y + ((display_height - dy) * transform.zoom)
    return view_x, view_y


def view_rect_to_pdf_rect(
    *,
    view_rect: ViewRect,
    transform: ViewTransform,
    page_box: PageBox,
    rotation: int,
) -> PdfRect:
    """Convert a dragged viewer rectangle into a normalized PDF rectangle."""
    p1 = view_point_to_pdf(
        view_x=view_rect.x1,
        view_y=view_rect.y1,
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )
    p2 = view_point_to_pdf(
        view_x=view_rect.x2,
        view_y=view_rect.y2,
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )
    return PdfRect(x1=p1[0], y1=p1[1], x2=p2[0], y2=p2[1]).normalized()


def pdf_rect_to_view_rect(
    *,
    pdf_rect: PdfRect,
    transform: ViewTransform,
    page_box: PageBox,
    rotation: int,
) -> ViewRect:
    """Project a PDF-space rectangle into viewer-space coordinates."""
    normalized_rect = pdf_rect.normalized()
    p1 = pdf_point_to_view(
        pdf_x=normalized_rect.x1,
        pdf_y=normalized_rect.y1,
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )
    p2 = pdf_point_to_view(
        pdf_x=normalized_rect.x2,
        pdf_y=normalized_rect.y2,
        transform=transform,
        page_box=page_box,
        rotation=rotation,
    )
    return ViewRect(x1=p1[0], y1=p1[1], x2=p2[0], y2=p2[1])


def validate_pdf_rect_within_page(pdf_rect: PdfRect, *, page_box: PageBox) -> bool:
    """Validate that a rectangle stays fully within the target page box."""
    page_box.validate()
    normalized_rect = pdf_rect.normalized()
    return (
        normalized_rect.x1 >= page_box.left
        and normalized_rect.x2 <= page_box.right
        and normalized_rect.y1 >= page_box.bottom
        and normalized_rect.y2 <= page_box.top
    )
