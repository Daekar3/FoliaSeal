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


@dataclass(frozen=True)
class PdfRectSnap:
    """A pointer-placement snap result and the guides that caused it."""

    rect: PdfRect
    guides: tuple[str, ...] = ()


def snap_pdf_rect_to_page_guides(
    pdf_rect: PdfRect,
    *,
    page_box: PageBox,
    threshold_pt: float = 8.0,
) -> PdfRectSnap:
    """Snap a pointer rectangle to nearby page edges or centers.

    Keyboard and numeric callers intentionally do not use this helper. The page box is the
    only authority for guides; no document or neighboring-object snapping is introduced.
    """
    page_box.validate()
    if threshold_pt < 0:
        raise ValueError("Snap threshold must not be negative.")
    normalized = pdf_rect.normalized()
    width = normalized.x2 - normalized.x1
    height = normalized.y2 - normalized.y1

    x_candidates = (
        (abs(normalized.x1 - page_box.left), page_box.left, "left-edge"),
        (abs(normalized.x2 - page_box.right), page_box.right - width, "right-edge"),
        (
            abs((normalized.x1 + normalized.x2) / 2.0 - (page_box.left + page_box.right) / 2.0),
            (page_box.left + page_box.right - width) / 2.0,
            "vertical-center",
        ),
    )
    y_candidates = (
        (abs(normalized.y1 - page_box.bottom), page_box.bottom, "bottom-edge"),
        (abs(normalized.y2 - page_box.top), page_box.top - height, "top-edge"),
        (
            abs((normalized.y1 + normalized.y2) / 2.0 - (page_box.bottom + page_box.top) / 2.0),
            (page_box.bottom + page_box.top - height) / 2.0,
            "horizontal-center",
        ),
    )
    x_snap = min(x_candidates, key=lambda candidate: candidate[0])
    y_snap = min(y_candidates, key=lambda candidate: candidate[0])
    left = x_snap[1] if x_snap[0] <= threshold_pt else normalized.x1
    bottom = y_snap[1] if y_snap[0] <= threshold_pt else normalized.y1
    guides = tuple(
        guide
        for distance, _coordinate, guide in (x_snap, y_snap)
        if distance <= threshold_pt
    )
    return PdfRectSnap(
        rect=PdfRect(
            x1=left,
            y1=bottom,
            x2=left + width,
            y2=bottom + height,
        ),
        guides=guides,
    )


def _normalize_rotation(rotation: int) -> int:
    if rotation % 90 != 0:
        raise ValueError("Rotation must be a multiple of 90 degrees.")
    return rotation % 360


def _display_dimensions(page_box: PageBox, rotation: int) -> tuple[float, float]:
    normalized_rotation = _normalize_rotation(rotation)
    if normalized_rotation in (0, 180):
        return page_box.width, page_box.height
    return page_box.height, page_box.width


def visible_page_dimensions(page_box: PageBox, rotation: int) -> tuple[float, float]:
    """Return the already-rotated visible page width and height in points."""
    page_box.validate()
    return _display_dimensions(page_box, rotation)


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


def pdf_rect_to_visible_page_rect(
    *,
    pdf_rect: PdfRect,
    page_box: PageBox,
    rotation: int,
) -> tuple[float, float, float, float]:
    """Convert a PDF-space rectangle to visible top-left page coordinates."""
    page_box.validate()
    normalized = pdf_rect.normalized()
    corners = (
        (normalized.x1, normalized.y1),
        (normalized.x1, normalized.y2),
        (normalized.x2, normalized.y1),
        (normalized.x2, normalized.y2),
    )
    display_points = tuple(
        _pdf_local_to_display(page_box, rotation, x - page_box.left, y - page_box.bottom)
        for x, y in corners
    )
    display_width, display_height = _display_dimensions(page_box, rotation)
    del display_width
    left = min(point[0] for point in display_points)
    right = max(point[0] for point in display_points)
    bottom = min(point[1] for point in display_points)
    top = max(point[1] for point in display_points)
    return left, display_height - top, right - left, top - bottom


def visible_page_rect_to_pdf_rect(
    *,
    left_pt: float,
    top_pt: float,
    width_pt: float,
    height_pt: float,
    page_box: PageBox,
    rotation: int,
) -> PdfRect:
    """Convert a visible top-left page rectangle into PDF-space coordinates."""
    page_box.validate()
    _, display_height = _display_dimensions(page_box, rotation)
    display_corners = (
        (left_pt, display_height - top_pt),
        (left_pt, display_height - top_pt - height_pt),
        (left_pt + width_pt, display_height - top_pt),
        (left_pt + width_pt, display_height - top_pt - height_pt),
    )
    pdf_points = tuple(_display_to_pdf_local(page_box, rotation, x, y) for x, y in display_corners)
    xs = tuple(page_box.left + point[0] for point in pdf_points)
    ys = tuple(page_box.bottom + point[1] for point in pdf_points)
    return PdfRect(x1=min(xs), y1=min(ys), x2=max(xs), y2=max(ys))


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
