"""Neutral visible-signature color conversion helpers."""

from __future__ import annotations

from foliaseal.domain.models import SignatureTextStyle


def text_style_color_rgba(text_style: SignatureTextStyle) -> tuple[int, int, int, int] | None:
    """Convert a six-digit signature text color into an opaque RGBA tuple."""

    normalized = text_style.text_color_hex.strip().lstrip("#")
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
