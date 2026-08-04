"""Shared preview image-comparison primitives for evidence capture."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class PreviewImageComparisonAnalyzer:
    """Own deterministic preview/output image-comparison primitives."""

    def image_crop_sha256(
        self,
        *,
        preview_image_path: str | None,
        crop_bounds: dict[str, int] | None,
    ) -> str | None:
        if preview_image_path is None or crop_bounds is None:
            return None
        try:
            with Image.open(preview_image_path) as image:
                preview_image = image.convert("RGBA")
        except OSError:
            return None
        crop_left = max(0, crop_bounds["x"])
        crop_top = max(0, crop_bounds["y"])
        crop_right = min(preview_image.width, crop_left + max(0, crop_bounds["width"]))
        crop_bottom = min(preview_image.height, crop_top + max(0, crop_bounds["height"]))
        if crop_right <= crop_left or crop_bottom <= crop_top:
            return None
        cropped = preview_image.crop((crop_left, crop_top, crop_right, crop_bottom))
        return hashlib.sha256(cropped.tobytes()).hexdigest()

    def flatten_preview_image_to_white(self, *, source_path: str, output_path: str) -> None:
        with Image.open(source_path) as image:
            rgba_image = image.convert("RGBA")
        flattened = Image.new("RGBA", rgba_image.size, (255, 255, 255, 255))
        flattened.alpha_composite(rgba_image)
        flattened.save(output_path)

    def image_crop_change_ratio(
        self,
        *,
        previous_image_path: str | None,
        previous_bounds: dict[str, int] | None,
        current_image_path: str | None,
        current_bounds: dict[str, int] | None,
    ) -> float | None:
        if (
            previous_image_path is None
            or previous_bounds is None
            or current_image_path is None
            or current_bounds is None
        ):
            return None
        if (
            previous_bounds["width"] != current_bounds["width"]
            or previous_bounds["height"] != current_bounds["height"]
        ):
            return None
        try:
            with Image.open(previous_image_path) as image:
                previous_image = image.convert("RGBA")
            with Image.open(current_image_path) as image:
                current_image = image.convert("RGBA")
        except OSError:
            return None
        previous_crop = previous_image.crop(
            (
                previous_bounds["x"],
                previous_bounds["y"],
                previous_bounds["x"] + previous_bounds["width"],
                previous_bounds["y"] + previous_bounds["height"],
            )
        )
        current_crop = current_image.crop(
            (
                current_bounds["x"],
                current_bounds["y"],
                current_bounds["x"] + current_bounds["width"],
                current_bounds["y"] + current_bounds["height"],
            )
        )
        total_pixels = previous_crop.width * previous_crop.height
        if total_pixels <= 0 or previous_crop.size != current_crop.size:
            return None
        changed_pixels = 0
        for y in range(previous_crop.height):
            for x in range(previous_crop.width):
                if previous_crop.getpixel((x, y)) != current_crop.getpixel((x, y)):
                    changed_pixels += 1
        return changed_pixels / total_pixels

    def normalized_image_crop_change_ratio(
        self,
        *,
        previous_image_path: str | None,
        previous_bounds: dict[str, int] | None,
        current_image_path: str | None,
        current_bounds: dict[str, int] | None,
    ) -> float | None:
        if (
            previous_image_path is None
            or previous_bounds is None
            or current_image_path is None
            or current_bounds is None
        ):
            return None
        try:
            with Image.open(previous_image_path) as image:
                previous_image = image.convert("RGBA")
            with Image.open(current_image_path) as image:
                current_image = image.convert("RGBA")
        except OSError:
            return None

        previous_crop = previous_image.crop(
            (
                max(0, previous_bounds["x"]),
                max(0, previous_bounds["y"]),
                max(0, previous_bounds["x"]) + max(0, previous_bounds["width"]),
                max(0, previous_bounds["y"]) + max(0, previous_bounds["height"]),
            )
        )
        current_crop = current_image.crop(
            (
                max(0, current_bounds["x"]),
                max(0, current_bounds["y"]),
                max(0, current_bounds["x"]) + max(0, current_bounds["width"]),
                max(0, current_bounds["y"]) + max(0, current_bounds["height"]),
            )
        )
        if previous_crop.width <= 0 or previous_crop.height <= 0:
            return None
        if current_crop.width <= 0 or current_crop.height <= 0:
            return None
        target_width = max(previous_crop.width, current_crop.width)
        target_height = max(previous_crop.height, current_crop.height)
        if target_width <= 0 or target_height <= 0:
            return None
        previous_normalized = previous_crop.resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )
        current_normalized = current_crop.resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )
        total_pixels = target_width * target_height
        changed_pixels = 0
        for y in range(target_height):
            for x in range(target_width):
                if previous_normalized.getpixel((x, y)) != current_normalized.getpixel((x, y)):
                    changed_pixels += 1
        return changed_pixels / total_pixels

    def aspect_ratio_delta(
        self,
        previous_width: int,
        previous_height: int,
        current_width: int,
        current_height: int,
    ) -> float | None:
        if previous_width <= 0 or previous_height <= 0:
            return None
        if current_width <= 0 or current_height <= 0:
            return None
        previous_ratio = previous_width / previous_height
        current_ratio = current_width / current_height
        return abs(previous_ratio - current_ratio) / max(previous_ratio, current_ratio)

    def write_side_by_side_comparison(
        self,
        *,
        preview_image_path: str | None,
        preview_bounds: dict[str, int] | None,
        signed_image_path: str | None,
        signed_bounds: dict[str, int] | None,
        output_path: str,
    ) -> str | None:
        if (
            preview_image_path is None
            or preview_bounds is None
            or signed_image_path is None
            or signed_bounds is None
        ):
            return (
                "Signed-output comparison is unavailable because preview or signed crop "
                "evidence is missing."
            )
        try:
            with Image.open(preview_image_path) as image:
                preview_image = image.convert("RGBA")
            with Image.open(signed_image_path) as image:
                signed_image = image.convert("RGBA")
        except OSError as exc:
            return f"Failed to open images for comparison overlay: {exc}"

        preview_crop = preview_image.crop(
            (
                max(0, preview_bounds["x"]),
                max(0, preview_bounds["y"]),
                max(0, preview_bounds["x"]) + max(0, preview_bounds["width"]),
                max(0, preview_bounds["y"]) + max(0, preview_bounds["height"]),
            )
        )
        signed_crop = signed_image.crop(
            (
                max(0, signed_bounds["x"]),
                max(0, signed_bounds["y"]),
                max(0, signed_bounds["x"]) + max(0, signed_bounds["width"]),
                max(0, signed_bounds["y"]) + max(0, signed_bounds["height"]),
            )
        )
        spacer = 12
        width = preview_crop.width + signed_crop.width + spacer
        height = max(preview_crop.height, signed_crop.height)
        canvas = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))
        canvas.paste(preview_crop, (0, 0))
        canvas.paste(signed_crop, (preview_crop.width + spacer, 0))
        canvas.save(output_path)
        return None
