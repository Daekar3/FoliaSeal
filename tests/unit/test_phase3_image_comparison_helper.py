from __future__ import annotations

from pathlib import Path

from PIL import Image

import foliaseal.presentation.qt.phase3_harness as phase3_harness_module


def _helper():
    return phase3_harness_module._build_phase3_image_comparison_helper()


def test_image_comparison_helper_reports_changed_pixel_ratio(tmp_path: Path) -> None:
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    base = Image.new("RGBA", (60, 20), color=(255, 255, 255, 255))
    variant = Image.new("RGBA", (60, 20), color=(255, 255, 255, 255))
    for x in range(5, 25):
        for y in range(5, 12):
            base.putpixel((x, y), (0, 0, 0, 255))
            variant.putpixel((x, y), (0, 0, 0, 255))
    variant.putpixel((26, 12), (0, 0, 0, 255))
    base.save(image_a, format="PNG")
    variant.save(image_b, format="PNG")

    change_ratio = _helper().image_crop_change_ratio(
        previous_image_path=str(image_a),
        previous_bounds={"x": 0, "y": 0, "width": 60, "height": 20},
        current_image_path=str(image_b),
        current_bounds={"x": 0, "y": 0, "width": 60, "height": 20},
    )

    assert change_ratio == 1 / 1200


def test_image_comparison_helper_writes_side_by_side_overlay(tmp_path: Path) -> None:
    preview = tmp_path / "preview.png"
    signed = tmp_path / "signed.png"
    output = tmp_path / "compare.png"
    Image.new("RGBA", (20, 10), color=(255, 255, 255, 255)).save(preview)
    Image.new("RGBA", (15, 12), color=(255, 255, 255, 255)).save(signed)

    error = _helper().write_side_by_side_comparison(
        preview_image_path=str(preview),
        preview_bounds={"x": 0, "y": 0, "width": 20, "height": 10},
        signed_image_path=str(signed),
        signed_bounds={"x": 0, "y": 0, "width": 15, "height": 12},
        output_path=str(output),
    )

    assert error is None
    assert output.exists()
    with Image.open(output) as image:
        assert image.size == (47, 12)
