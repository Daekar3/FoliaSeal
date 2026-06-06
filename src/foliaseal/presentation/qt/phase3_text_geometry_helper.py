"""Shared preview text-geometry helpers for Phase 3 QA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from PIL import Image

DetectTextContentBoundsInImage = Callable[..., tuple[dict[str, int] | None, str | None]]
DetectTextLineBoundsInImage = Callable[..., tuple[tuple[dict[str, int], ...], str | None]]
ImportModule = Callable[[str], Any]
WriteWidgetCapturePng = Callable[[Any, str], str | None]


@dataclass(frozen=True)
class Phase3TextGeometryHelper:
    """Own the shared preview text-geometry primitives."""

    detect_text_content_bounds_in_image: DetectTextContentBoundsInImage
    detect_text_line_bounds_in_image: DetectTextLineBoundsInImage
    import_module: ImportModule
    write_widget_capture_png: WriteWidgetCapturePng

    def project_content_bounds_to_preview(
        self,
        *,
        source_image_size: dict[str, int] | None,
        source_content_bounds: dict[str, int] | None,
        pixmap_bounds: dict[str, int] | None,
    ) -> dict[str, int] | None:
        if source_image_size is None or source_content_bounds is None or pixmap_bounds is None:
            return None
        source_width = max(1, source_image_size["width"])
        source_height = max(1, source_image_size["height"])
        content_left = int(
            round(source_content_bounds["x"] * pixmap_bounds["width"] / source_width)
        )
        content_top = int(
            round(source_content_bounds["y"] * pixmap_bounds["height"] / source_height)
        )
        content_width = max(
            1,
            int(round(source_content_bounds["width"] * pixmap_bounds["width"] / source_width)),
        )
        content_height = max(
            1,
            int(round(source_content_bounds["height"] * pixmap_bounds["height"] / source_height)),
        )
        content_width = min(content_width, pixmap_bounds["width"] - content_left)
        content_height = min(content_height, pixmap_bounds["height"] - content_top)
        return {
            "x": pixmap_bounds["x"] + content_left,
            "y": pixmap_bounds["y"] + content_top,
            "width": max(1, content_width),
            "height": max(1, content_height),
        }

    def detect_text_content_bounds_in_preview(
        self,
        *,
        preview_image_path: str,
        text_widget_bounds: dict[str, int],
        text_color_rgba: tuple[int, int, int, int] | None,
        reference_text_content_bounds: dict[str, int] | None = None,
    ) -> tuple[dict[str, int] | None, str | None]:
        return self.detect_text_content_bounds_in_image(
            preview_image_path=preview_image_path,
            text_widget_bounds=text_widget_bounds,
            text_color_rgba=text_color_rgba,
            reference_text_content_bounds=reference_text_content_bounds,
        )

    def detect_text_line_bounds_in_preview(
        self,
        *,
        preview_image_path: str,
        text_widget_bounds: dict[str, int],
        text_color_rgba: tuple[int, int, int, int] | None,
        reference_text_content_bounds: dict[str, int] | None = None,
    ) -> tuple[tuple[dict[str, int], ...], str | None]:
        return self.detect_text_line_bounds_in_image(
            preview_image_path=preview_image_path,
            text_widget_bounds=text_widget_bounds,
            text_color_rgba=text_color_rgba,
            reference_text_content_bounds=reference_text_content_bounds,
        )

    def detect_text_geometry_in_preview(
        self,
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
        candidate_pixels = self._text_candidate_pixels_in_crop(
            cropped=cropped,
            crop_width=crop_width,
            crop_height=crop_height,
            text_color_rgba=text_color_rgba,
            reference_text_content_bounds=reference_text_content_bounds,
        )
        if not candidate_pixels:
            return None, (), "No rendered text pixels detected in the preview text widget."
        line_bounds = self._line_bounds_from_candidate_pixels(
            candidate_pixels,
            crop_left=crop_left,
            crop_top=crop_top,
        )
        if not line_bounds:
            return None, (), "No rendered text pixels detected in the preview text widget."
        text_bounds = self.union_rectangles(line_bounds)
        return text_bounds, line_bounds, None

    def reference_text_content_bounds(
        self,
        *,
        source_label: Any,
        text_color_rgba: tuple[int, int, int, int] | None,
    ) -> tuple[dict[str, int] | None, str | None]:
        widgets = self.import_module("PySide6.QtWidgets")
        qt_core = self.import_module("PySide6.QtCore")
        reference_label = getattr(widgets, "QLabel")()
        try:
            reference_label.setAttribute(
                getattr(qt_core.Qt.WidgetAttribute, "WA_DontShowOnScreen"),
                True,
            )
            reference_label.setText(source_label.text())
            reference_label.setFont(source_label.font())
            reference_label.setAlignment(source_label.alignment())
            reference_label.setWordWrap(source_label.wordWrap())
            reference_label.setTextFormat(source_label.textFormat())
            reference_label.setIndent(source_label.indent())
            reference_label.setMargin(source_label.margin())
            reference_label.setContentsMargins(source_label.contentsMargins())
            reference_label.setStyleSheet(source_label.styleSheet())
            reference_label.ensurePolished()

            if source_label.wordWrap():
                reference_width = max(1, source_label.width())
                reference_label.setFixedWidth(reference_width)
                reference_height = max(
                    source_label.height(),
                    reference_label.sizeHint().height(),
                    source_label.sizeHint().height(),
                )
                reference_label.resize(reference_width, max(1, reference_height))
            else:
                reference_label.adjustSize()
                hint = reference_label.sizeHint()
                reference_width = max(source_label.width(), hint.width())
                reference_height = max(source_label.height(), hint.height())
                reference_label.resize(max(1, reference_width), max(1, reference_height))

            with NamedTemporaryFile(suffix=".png", delete=False) as handle:
                capture_path = handle.name
            try:
                capture_error = self.write_widget_capture_png(reference_label, capture_path)
                if capture_error is not None:
                    return None, capture_error
                return self.detect_text_content_bounds_in_preview(
                    preview_image_path=capture_path,
                    text_widget_bounds={
                        "x": 0,
                        "y": 0,
                        "width": reference_label.width(),
                        "height": reference_label.height(),
                    },
                    text_color_rgba=text_color_rgba,
                )
            finally:
                Path(capture_path).unlink(missing_ok=True)
        finally:
            reference_label.deleteLater()

    def union_rectangles(
        self, rectangles: tuple[dict[str, int], ...]
    ) -> dict[str, int] | None:
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
        self,
        *,
        cropped: Image.Image,
        crop_width: int,
        crop_height: int,
        text_color_rgba: tuple[int, int, int, int] | None,
        reference_text_content_bounds: dict[str, int] | None,
    ) -> set[tuple[int, int]]:
        background = self._estimate_crop_background_rgba(cropped)
        candidate_pixels: set[tuple[int, int]] = set()
        for y in range(crop_height):
            for x in range(crop_width):
                pixel = cropped.getpixel((x, y))
                if not self._is_text_candidate_pixel(
                    pixel,
                    text_color_rgba=text_color_rgba,
                    background_rgba=background,
                ):
                    continue
                candidate_pixels.add((x, y))
        candidate_pixels = self._filter_border_like_candidate_components(
            candidate_pixels,
            crop_width=crop_width,
            crop_height=crop_height,
        )
        return self._restrict_candidates_to_reference_envelope(
            candidate_pixels,
            reference_text_content_bounds=reference_text_content_bounds,
            crop_width=crop_width,
            crop_height=crop_height,
        )

    def _line_bounds_from_candidate_pixels(
        self,
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
        self,
        candidate_pixels: set[tuple[int, int]],
        *,
        reference_text_content_bounds: dict[str, int] | None,
        crop_width: int,
        crop_height: int,
    ) -> set[tuple[int, int]]:
        if not candidate_pixels or reference_text_content_bounds is None:
            return candidate_pixels
        pad = 4
        left = max(0, reference_text_content_bounds["x"] - pad)
        top = max(0, reference_text_content_bounds["y"] - pad)
        right = min(
            crop_width,
            reference_text_content_bounds["x"] + reference_text_content_bounds["width"] + pad,
        )
        bottom = min(
            crop_height,
            reference_text_content_bounds["y"] + reference_text_content_bounds["height"] + pad,
        )
        restricted = {
            (x, y) for x, y in candidate_pixels if left <= x < right and top <= y < bottom
        }
        return restricted or candidate_pixels

    def _filter_border_like_candidate_components(
        self,
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
                for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if neighbor not in remaining:
                        continue
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
            if self._component_looks_like_border_stroke(
                component,
                crop_width=crop_width,
                crop_height=crop_height,
            ):
                continue
            filtered.update(component)
        return filtered

    def _component_looks_like_border_stroke(
        self,
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

    def _estimate_crop_background_rgba(
        self, image: Image.Image
    ) -> tuple[int, int, int, int]:
        width, height = image.size
        if width <= 0 or height <= 0:
            return (255, 255, 255, 255)
        corners = (
            image.getpixel((0, 0)),
            image.getpixel((width - 1, 0)),
            image.getpixel((0, height - 1)),
            image.getpixel((width - 1, height - 1)),
        )
        channel_medians = []
        for channel_index in range(4):
            values = sorted(pixel[channel_index] for pixel in corners)
            channel_medians.append(int(round((values[1] + values[2]) / 2)))
        return tuple(channel_medians)  # type: ignore[return-value]

    def _is_text_candidate_pixel(
        self,
        pixel: tuple[int, int, int, int],
        *,
        text_color_rgba: tuple[int, int, int, int] | None,
        background_rgba: tuple[int, int, int, int],
    ) -> bool:
        if pixel[3] <= 0:
            return False
        alpha = pixel[3] / 255.0
        if alpha < 0.25:
            return False
        background_luma = self._rgba_luma(background_rgba)
        pixel_luma = self._rgba_luma(pixel)
        if text_color_rgba is not None:
            expected_luma = self._rgba_luma(text_color_rgba)
            if abs(pixel_luma - expected_luma) <= 96:
                return True
        return abs(pixel_luma - background_luma) >= 28

    def _rgba_luma(self, pixel: tuple[int, int, int, int]) -> int:
        return int(round((0.2126 * pixel[0]) + (0.7152 * pixel[1]) + (0.0722 * pixel[2])))

