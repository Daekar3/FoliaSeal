"""Shared, Qt-edge preview geometry and evidence normalization helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def draw_overlay_rect(draw: Any, bounds: dict[str, int], color: tuple[int, ...]) -> None:
    left = bounds["x"]
    top = bounds["y"]
    right = left + max(0, bounds["width"] - 1)
    bottom = top + max(0, bounds["height"] - 1)
    draw.rectangle((left, top, right, bottom), outline=color, width=2)


def offset_rect(bounds: dict[str, int], *, dx: int, dy: int) -> dict[str, int]:
    return {
        "x": bounds["x"] + dx,
        "y": bounds["y"] + dy,
        "width": bounds["width"],
        "height": bounds["height"],
    }


def widget_width(widget: Any) -> int | None:
    width = getattr(widget, "width", None)
    if callable(width):
        value = width()
        if isinstance(value, int):
            return value
    fixed_width = getattr(widget, "fixed_width", None)
    return fixed_width if isinstance(fixed_width, int) else None


def widget_rect_snapshot(widget: Any) -> dict[str, int] | None:
    geometry = getattr(widget, "geometry", None)
    if callable(geometry):
        rect = geometry()
        getters = tuple(getattr(rect, name, None) for name in ("x", "y", "width", "height"))
        if all(callable(item) for item in getters):
            return {
                name: int(getter())
                for name, getter in zip(("x", "y", "width", "height"), getters)
            }
    size = getattr(widget, "fixed_size", None)
    if isinstance(size, tuple) and len(size) == 2:
        return {"x": 0, "y": 0, "width": int(size[0]), "height": int(size[1])}
    width = widget_width(widget)
    height = None
    size_hint = getattr(widget, "sizeHint", None)
    if callable(size_hint):
        hint_height = getattr(size_hint(), "height", None)
        if callable(hint_height):
            height = int(hint_height())
    if width is not None and height is not None:
        return {"x": 0, "y": 0, "width": width, "height": height}
    return None


def size_hint_snapshot(widget: Any) -> dict[str, int] | None:
    size_hint = getattr(widget, "sizeHint", None)
    if not callable(size_hint):
        return None
    hint = size_hint()
    width = getattr(hint, "width", None)
    height = getattr(hint, "height", None)
    if callable(width) and callable(height):
        return {"width": int(width()), "height": int(height())}
    return None


def label_pixmap_size_snapshot(label: Any) -> dict[str, int] | None:
    pixmap = getattr(label, "pixmap", None)
    pixmap = pixmap() if callable(pixmap) else None
    if pixmap is None:
        return None
    width = getattr(pixmap, "width", None)
    height = getattr(pixmap, "height", None)
    if callable(width) and callable(height):
        return {"width": int(width()), "height": int(height())}
    return None


def label_alignment_snapshot(label: Any) -> int | None:
    alignment = getattr(label, "alignment", None)
    value = alignment() if callable(alignment) else alignment
    return value if isinstance(value, int) else None


def project_pixmap_bounds_within_label(
    *,
    label_bounds: dict[str, int] | None,
    pixmap_size: dict[str, int] | None,
    alignment: int | None,
    alignment_flag: Callable[[str], int],
) -> dict[str, int] | None:
    if label_bounds is None or pixmap_size is None:
        return None
    width = min(label_bounds["width"], pixmap_size["width"])
    height = min(label_bounds["height"], pixmap_size["height"])
    horizontal_space = max(0, label_bounds["width"] - width)
    vertical_space = max(0, label_bounds["height"] - height)
    x_offset = horizontal_space // 2
    y_offset = vertical_space // 2
    if alignment is not None:
        if alignment & alignment_flag("AlignLeft"):
            x_offset = 0
        elif alignment & alignment_flag("AlignRight"):
            x_offset = horizontal_space
        if alignment & alignment_flag("AlignTop"):
            y_offset = 0
        elif alignment & alignment_flag("AlignBottom"):
            y_offset = vertical_space
    return {
        "x": label_bounds["x"] + x_offset,
        "y": label_bounds["y"] + y_offset,
        "width": width,
        "height": height,
    }


def preview_text_color_rgba(preview: Any) -> tuple[int, int, int, int] | None:
    text_style = getattr(preview, "text_style", None)
    color_hex = getattr(text_style, "text_color_hex", None) if text_style is not None else None
    if not isinstance(color_hex, str):
        return None
    normalized = color_hex.strip().lstrip("#")
    if len(normalized) != 6:
        return None
    try:
        return (
            int(normalized[0:2], 16),
            int(normalized[2:4], 16),
            int(normalized[4:6], 16),
            255,
        )
    except ValueError:
        return None


__all__ = [
    "draw_overlay_rect",
    "label_alignment_snapshot",
    "label_pixmap_size_snapshot",
    "offset_rect",
    "preview_text_color_rgba",
    "project_pixmap_bounds_within_label",
    "size_hint_snapshot",
    "widget_rect_snapshot",
    "widget_width",
]
