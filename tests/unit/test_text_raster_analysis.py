from pathlib import Path

from PIL import Image, ImageDraw

from foliaseal.application.text_raster_analysis import detect_text_content_bounds_in_image


def test_detect_text_bounds_applies_absolute_reference_bounds_to_crop(
    tmp_path: Path,
) -> None:
    image_path = tmp_path / "text.png"
    image = Image.new("RGBA", (140, 40), color=(255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((60, 10, 79, 19), fill=(0, 0, 0, 255))
    image.save(image_path)

    bounds, error = detect_text_content_bounds_in_image(
        preview_image_path=str(image_path),
        text_widget_bounds={"x": 50, "y": 5, "width": 80, "height": 30},
        text_color_rgba=(0, 0, 0, 255),
        reference_text_content_bounds={"x": 60, "y": 10, "width": 20, "height": 10},
    )

    assert error is None
    assert bounds == {"x": 60, "y": 10, "width": 20, "height": 10}
