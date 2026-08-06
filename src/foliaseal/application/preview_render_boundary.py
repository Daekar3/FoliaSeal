"""Neutral ports for canonical preview rasterization and rendered-ink analysis."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class PreviewRasterRequest:
    """One PDF page raster request independent of Qt or another renderer."""

    document_path: str | Path
    page_index: int
    zoom: float


@dataclass(frozen=True)
class PreviewRasterResult:
    """RGBA raster bytes and dimensions returned by a preview renderer."""

    width_px: int
    height_px: int
    rgba_bytes: bytes

    def __post_init__(self) -> None:
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("Preview raster dimensions must be positive.")
        expected_size = self.width_px * self.height_px * 4
        if len(self.rgba_bytes) != expected_size:
            raise ValueError(
                "Preview raster RGBA byte length must equal width_px * height_px * 4."
            )


class PreviewRasterRenderer(Protocol):
    """Render one temporary PDF page into an RGBA raster."""

    def render_page(self, request: PreviewRasterRequest) -> PreviewRasterResult: ...


@dataclass(frozen=True)
class RenderedInkMeasurementRequest:
    """Inputs needed to find glyph ink inside a rendered preview image."""

    preview_image_path: str | Path
    text_widget_bounds: Mapping[str, int]
    text_color_rgba: tuple[int, int, int, int]
    reference_text_content_bounds: Mapping[str, int] | None = None


@dataclass(frozen=True)
class RenderedInkMeasurementResult:
    """Rendered glyph bounds plus a non-fatal diagnostic, if one occurred."""

    bounds_px: dict[str, int] | None
    error: str | None = None


class RenderedInkMeasurementPort(Protocol):
    """Find rendered glyph bounds without exposing image-library objects."""

    def measure(self, request: RenderedInkMeasurementRequest) -> RenderedInkMeasurementResult: ...
