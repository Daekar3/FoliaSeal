from __future__ import annotations

from pathlib import Path

from PIL import Image

import foliaseal.presentation.qt.phase3_harness as phase3_harness_module


def _helper():
    return phase3_harness_module._build_phase3_text_geometry_helper()


def test_project_content_bounds_to_preview_scales_source_bounds() -> None:
    projected = _helper().project_content_bounds_to_preview(
        source_image_size={"width": 20, "height": 10},
        source_content_bounds={"x": 4, "y": 2, "width": 12, "height": 6},
        pixmap_bounds={"x": 10, "y": 5, "width": 100, "height": 50},
    )

    assert projected == {"x": 30, "y": 15, "width": 60, "height": 30}


def test_detect_text_content_bounds_in_preview_finds_rendered_pixels(tmp_path: Path) -> None:
    preview_path = tmp_path / "preview.png"
    image = Image.new("RGBA", (80, 40), color=(255, 255, 255, 255))
    for x in range(18, 46):
        for y in range(12, 21):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _helper().detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 8, "width": 50, "height": 20},
        text_color_rgba=(0, 0, 0, 255),
    )

    assert error is None
    assert bounds == {"x": 18, "y": 12, "width": 28, "height": 9}


def test_detect_text_content_bounds_in_preview_captures_antialiased_text_edges(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview_antialias.png"
    image = Image.new("RGBA", (80, 40), color=(255, 255, 255, 255))
    for x in range(22, 40):
        for y in range(12, 18):
            image.putpixel((x, y), (0, 0, 0, 255))
    for x in range(20, 42):
        image.putpixel((x, 11), (120, 120, 120, 255))
        image.putpixel((x, 18), (120, 120, 120, 255))
    image.putpixel((21, 12), (120, 120, 120, 255))
    image.putpixel((40, 17), (120, 120, 120, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _helper().detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 8, "width": 40, "height": 20},
        text_color_rgba=(0, 0, 0, 255),
    )

    assert error is None
    assert bounds == {"x": 20, "y": 11, "width": 22, "height": 8}


def test_detect_text_content_bounds_in_preview_ignores_border_strokes(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview_border.png"
    image = Image.new("RGBA", (80, 40), color=(255, 255, 255, 255))
    for x in range(10, 60):
        image.putpixel((x, 27), (0, 0, 0, 255))
    for x in range(22, 38):
        for y in range(14, 19):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _helper().detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 8, "width": 50, "height": 20},
        text_color_rgba=(0, 0, 0, 255),
    )

    assert error is None
    assert bounds == {"x": 22, "y": 14, "width": 16, "height": 5}


def test_detect_text_content_bounds_in_preview_uses_reference_envelope_to_reject_wide_noise(
    tmp_path: Path,
) -> None:
    preview_path = tmp_path / "preview_reference_guided.png"
    image = Image.new("RGBA", (120, 50), color=(255, 255, 255, 255))
    for x in range(10, 110):
        image.putpixel((x, 30), (0, 0, 0, 255))
    for x in range(28, 52):
        for y in range(16, 22):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(preview_path, format="PNG")

    bounds, error = _helper().detect_text_content_bounds_in_preview(
        preview_image_path=str(preview_path),
        text_widget_bounds={"x": 10, "y": 10, "width": 100, "height": 24},
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds={"x": 28, "y": 16, "width": 28, "height": 10},
    )

    assert error is None
    assert bounds == {"x": 28, "y": 16, "width": 24, "height": 6}

