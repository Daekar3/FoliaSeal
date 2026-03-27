"""Render adapter interfaces and fallbacks."""

from pdf_signer.infra.render.base import (
    NullPdfRenderBackend,
    PdfPageGeometry,
    PdfRenderBackend,
    RenderBackendDiagnostic,
    RenderPageRequest,
    RenderPageResult,
)
from pdf_signer.infra.render.cache import RenderCacheKey, RenderCachePolicy

__all__ = [
    "RenderCacheKey",
    "RenderCachePolicy",
    "NullPdfRenderBackend",
    "PdfPageGeometry",
    "PdfRenderBackend",
    "RenderBackendDiagnostic",
    "RenderPageRequest",
    "RenderPageResult",
]
