"""Shared raster text-bounds analysis for preview and fit diagnostics."""

from __future__ import annotations

from PIL import Image

from foliaseal.application.preview_render_boundary import (
    RenderedInkMeasurementRequest,
    RenderedInkMeasurementResult,
)


class DefaultRenderedInkMeasurementPort:
    """Application adapter exposing the existing raster analysis as a port."""

    def measure(
        self,
        request: RenderedInkMeasurementRequest,
    ) -> RenderedInkMeasurementResult:
        bounds, error = detect_text_content_bounds_in_image(
            preview_image_path=str(request.preview_image_path),
            text_widget_bounds=dict(request.text_widget_bounds),
            text_color_rgba=request.text_color_rgba,
            reference_text_content_bounds=(
                None
                if request.reference_text_content_bounds is None
                else dict(request.reference_text_content_bounds)
            ),
        )
        return RenderedInkMeasurementResult(bounds_px=bounds, error=error)


def detect_text_content_bounds_in_image(
    *,
    preview_image_path: str,
    text_widget_bounds: dict[str, int],
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None = None,
) -> tuple[dict[str, int] | None, str | None]:
    text_bounds, _line_bounds, error = detect_text_geometry_in_image(
        preview_image_path=preview_image_path,
        text_widget_bounds=text_widget_bounds,
        text_color_rgba=text_color_rgba,
        reference_text_content_bounds=reference_text_content_bounds,
    )
    return text_bounds, error


def detect_text_line_bounds_in_image(
    *,
    preview_image_path: str,
    text_widget_bounds: dict[str, int],
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None = None,
) -> tuple[tuple[dict[str, int], ...], str | None]:
    _text_bounds, line_bounds, error = detect_text_geometry_in_image(
        preview_image_path=preview_image_path,
        text_widget_bounds=text_widget_bounds,
        text_color_rgba=text_color_rgba,
        reference_text_content_bounds=reference_text_content_bounds,
    )
    return line_bounds, error


def detect_text_geometry_in_image(
    *,
    preview_image_path: str,
    text_widget_bounds: dict[str, int],
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None = None,
) -> tuple[dict[str, int] | None, tuple[dict[str, int], ...], str | None]:
    try:
        with Image.open(preview_image_path) as image:
            preview_image = image.convert("RGBA")
    except OSError as exc:
        return None, (), f"Failed to open preview image for text analysis: {exc}"

    image_width, image_height = preview_image.size
    crop_left = max(0, text_widget_bounds["x"])
    crop_top = max(0, text_widget_bounds["y"])
    crop_right = min(image_width, crop_left + max(0, text_widget_bounds["width"]))
    crop_bottom = min(image_height, crop_top + max(0, text_widget_bounds["height"]))
    if crop_right <= crop_left or crop_bottom <= crop_top:
        return None, (), "Text widget bounds do not intersect the captured preview image."

    cropped = preview_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    crop_width, crop_height = cropped.size
    candidate_pixels = _text_candidate_pixels_in_crop(
        cropped=cropped,
        crop_left=crop_left,
        crop_top=crop_top,
        crop_width=crop_width,
        crop_height=crop_height,
        text_color_rgba=text_color_rgba,
        reference_text_content_bounds=reference_text_content_bounds,
    )
    if not candidate_pixels:
        return None, (), "No rendered text pixels detected in the preview text widget."
    line_bounds = _line_bounds_from_candidate_pixels(
        candidate_pixels,
        crop_left=crop_left,
        crop_top=crop_top,
    )
    if not line_bounds:
        return None, (), "No rendered text pixels detected in the preview text widget."
    text_bounds = union_rectangles(line_bounds)
    return text_bounds, line_bounds, None


def union_rectangles(rectangles: tuple[dict[str, int], ...]) -> dict[str, int] | None:
    if not rectangles:
        return None
    min_x = min(rect["x"] for rect in rectangles)
    min_y = min(rect["y"] for rect in rectangles)
    max_x = max(rect["x"] + rect["width"] - 1 for rect in rectangles)
    max_y = max(rect["y"] + rect["height"] - 1 for rect in rectangles)
    return {
        "x": min_x,
        "y": min_y,
        "width": (max_x - min_x) + 1,
        "height": (max_y - min_y) + 1,
    }


def _text_candidate_pixels_in_crop(
    *,
    cropped: Image.Image,
    crop_left: int,
    crop_top: int,
    crop_width: int,
    crop_height: int,
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None,
) -> set[tuple[int, int]]:
    background = _estimate_crop_background_rgba(cropped)
    candidate_pixels: set[tuple[int, int]] = set()
    for y in range(crop_height):
        for x in range(crop_width):
            pixel = cropped.getpixel((x, y))
            if not _is_text_candidate_pixel(
                pixel,
                text_color_rgba=text_color_rgba,
                background_rgba=background,
            ):
                continue
            candidate_pixels.add((x, y))
    candidate_pixels = _filter_border_like_candidate_components(
        candidate_pixels,
        crop_width=crop_width,
        crop_height=crop_height,
    )
    return _restrict_candidates_to_reference_envelope(
        candidate_pixels,
        reference_text_content_bounds=reference_text_content_bounds,
        crop_left=crop_left,
        crop_top=crop_top,
        crop_width=crop_width,
        crop_height=crop_height,
    )


def _line_bounds_from_candidate_pixels(
    candidate_pixels: set[tuple[int, int]],
    *,
    crop_left: int,
    crop_top: int,
) -> tuple[dict[str, int], ...]:
    if not candidate_pixels:
        return ()
    row_values = sorted({y for _x, y in candidate_pixels})
    groups: list[list[int]] = [[row_values[0]]]
    for row in row_values[1:]:
        if row <= groups[-1][-1] + 2:
            groups[-1].append(row)
        else:
            groups.append([row])
    line_bounds: list[dict[str, int]] = []
    for group in groups:
        group_pixels = [(x, y) for x, y in candidate_pixels if group[0] <= y <= group[-1]]
        if not group_pixels:
            continue
        min_x = min(x for x, _y in group_pixels)
        max_x = max(x for x, _y in group_pixels)
        min_y = min(y for _x, y in group_pixels)
        max_y = max(y for _x, y in group_pixels)
        line_bounds.append(
            {
                "x": crop_left + min_x,
                "y": crop_top + min_y,
                "width": (max_x - min_x) + 1,
                "height": (max_y - min_y) + 1,
            }
        )
    return tuple(line_bounds)


def _restrict_candidates_to_reference_envelope(
    candidate_pixels: set[tuple[int, int]],
    *,
    reference_text_content_bounds: dict[str, int] | None,
    crop_left: int,
    crop_top: int,
    crop_width: int,
    crop_height: int,
) -> set[tuple[int, int]]:
    if not candidate_pixels or reference_text_content_bounds is None:
        return candidate_pixels
    pad = 4
    reference_left = reference_text_content_bounds["x"] - crop_left
    reference_top = reference_text_content_bounds["y"] - crop_top
    left = max(0, reference_left - pad)
    top = max(0, reference_top - pad)
    right = min(
        crop_width,
        reference_left + reference_text_content_bounds["width"] + pad,
    )
    bottom = min(
        crop_height,
        reference_top + reference_text_content_bounds["height"] + pad,
    )
    restricted = {
        (x, y)
        for x, y in candidate_pixels
        if left <= x < right and top <= y < bottom
    }
    return restricted or candidate_pixels


def _filter_border_like_candidate_components(
    candidate_pixels: set[tuple[int, int]],
    *,
    crop_width: int,
    crop_height: int,
) -> set[tuple[int, int]]:
    if not candidate_pixels:
        return candidate_pixels

    remaining = set(candidate_pixels)
    filtered: set[tuple[int, int]] = set()
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}
        while stack:
            x, y = stack.pop()
            for neighbor in (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ):
                if neighbor not in remaining:
                    continue
                remaining.remove(neighbor)
                component.add(neighbor)
                stack.append(neighbor)
        if _component_looks_like_border_stroke(
            component,
            crop_width=crop_width,
            crop_height=crop_height,
        ):
            continue
        filtered.update(component)
    return filtered


def _component_looks_like_border_stroke(
    component: set[tuple[int, int]],
    *,
    crop_width: int,
    crop_height: int,
) -> bool:
    min_x = min(x for x, _y in component)
    max_x = max(x for x, _y in component)
    min_y = min(y for _x, y in component)
    max_y = max(y for _x, y in component)
    width = (max_x - min_x) + 1
    height = (max_y - min_y) + 1
    touches_left = min_x <= 0
    touches_right = max_x >= crop_width - 1
    touches_top = min_y <= 0
    touches_bottom = max_y >= crop_height - 1

    spans_full_width = width >= max(1, crop_width - 2)
    spans_full_height = height >= max(1, crop_height - 2)
    thin_horizontal = height <= 2 and spans_full_width and (touches_top or touches_bottom)
    thin_vertical = width <= 2 and spans_full_height and (touches_left or touches_right)
    return thin_horizontal or thin_vertical


def _estimate_crop_background_rgba(image: Image.Image) -> tuple[int, int, int, int]:
    width, height = image.size
    if width <= 0 or height <= 0:
        return (255, 255, 255, 255)
    sample_points = {
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, 0),
        (width // 2, height - 1),
        (0, height // 2),
        (width - 1, height // 2),
    }
    samples = [image.getpixel(point) for point in sample_points]
    return tuple(
        int(round(sum(component[index] for component in samples) / len(samples)))
        for index in range(4)
    )


def _is_text_candidate_pixel(
    pixel: tuple[int, int, int, int],
    *,
    text_color_rgba: tuple[int, int, int, int] | None,
    background_rgba: tuple[int, int, int, int],
) -> bool:
    if pixel[3] <= 0:
        return False
    pixel_luma = _rgba_luma(pixel)
    background_luma = _rgba_luma(background_rgba)
    if text_color_rgba is not None:
        text_distance = sum(abs(pixel[index] - text_color_rgba[index]) for index in range(3))
        if text_distance <= 150:
            return True
        return (background_luma - pixel_luma) >= 28
    color_distance = sum(abs(pixel[index] - background_rgba[index]) for index in range(3))
    return color_distance > 80 or (background_luma - pixel_luma) >= 28


def _rgba_luma(pixel: tuple[int, int, int, int]) -> int:
    return int(round((pixel[0] * 299 + pixel[1] * 587 + pixel[2] * 114) / 1000))
