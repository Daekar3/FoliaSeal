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
from pdf_signer.infra.render.qt_backend import QtPdfRenderBackend

__all__ = [
    "RenderCacheKey",
    "RenderCachePolicy",
    "NullPdfRenderBackend",
    "PdfPageGeometry",
    "PdfRenderBackend",
    "RenderBackendDiagnostic",
    "RenderPageRequest",
    "RenderPageResult",
    "QtPdfRenderBackend",
]
