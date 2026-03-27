"""Rendering adapter contracts for Phase 2 viewer infrastructure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RenderPageRequest:
    """Request data for rendering one page to a raster buffer."""

    document_path: str
    page_index: int
    zoom: float


@dataclass(frozen=True)
class RenderPageResult:
    """Rendered page payload and geometry metadata."""

    width_px: int
    height_px: int
    rgba_bytes: bytes


@dataclass(frozen=True)
class PdfPageGeometry:
    """PDF page geometry needed for coordinate transforms."""

    media_box: tuple[float, float, float, float]
    crop_box: tuple[float, float, float, float]
    rotation: int


@dataclass(frozen=True)
class RenderBackendDiagnostic:
    """Health check details when a render backend is unavailable."""

    backend_name: str
    available: bool
    message: str


class PdfRenderBackend(Protocol):
    """Render backend contract for Phase 2 viewer work."""

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        """Return page boxes and effective rotation for one page."""

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        """Render one page for the viewer surface."""

    def diagnostics(self) -> RenderBackendDiagnostic:
        """Return backend availability and fallback guidance."""


class NullPdfRenderBackend:
    """Fallback backend used before a concrete renderer is wired in."""

    _DIAGNOSTIC = RenderBackendDiagnostic(
        backend_name="null-render-backend",
        available=False,
        message=(
            "No render backend configured. Install and wire a concrete backend "
            "(QtPdf/pdfium adapter) for viewer features."
        ),
    )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        raise RuntimeError(self._DIAGNOSTIC.message)

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        raise RuntimeError(self._DIAGNOSTIC.message)

    def diagnostics(self) -> RenderBackendDiagnostic:
        return self._DIAGNOSTIC
