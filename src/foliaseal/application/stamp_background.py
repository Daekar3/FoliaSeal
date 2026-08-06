"""Concrete image-stamp loading shared by canonical preview and signing adapters."""

from __future__ import annotations

from PIL import Image
from pyhanko.pdf_utils.images import PdfImage


def stamp_background_for_path(image_stamp_path: str | None) -> PdfImage | None:
    """Load one optional image stamp for a PyHanko materialization edge."""

    if image_stamp_path is None:
        return None
    try:
        with Image.open(image_stamp_path) as image:
            normalized = image.copy()
            if normalized.mode not in {"RGB", "RGBA"}:
                normalized = normalized.convert("RGBA")
            return PdfImage(normalized, writer=None)
    except FileNotFoundError as exc:
        raise ValueError(f"Image stamp path not found: {image_stamp_path}") from exc
    except OSError as exc:
        raise ValueError(f"Image stamp path is not a readable image: {image_stamp_path}") from exc
