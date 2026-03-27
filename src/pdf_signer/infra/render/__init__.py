"""Render adapter interfaces and fallbacks."""

from pdf_signer.infra.render.base import (
    NullPdfRenderBackend,
    PdfPageGeometry,
    PdfRenderBackend,
    RenderBackendDiagnostic,
    RenderPageRequest,
    RenderPageResult,
)

__all__ = [
    "NullPdfRenderBackend",
    "PdfPageGeometry",
    "PdfRenderBackend",
    "RenderBackendDiagnostic",
    "RenderPageRequest",
    "RenderPageResult",
]
