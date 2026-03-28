"""Render adapter interfaces and fallbacks."""

from foliaseal.infra.render.base import (
    NullPdfRenderBackend,
    PdfPageGeometry,
    PdfRenderBackend,
    RenderBackendDiagnostic,
    RenderPageRequest,
    RenderPageResult,
)
from foliaseal.infra.render.cache import RenderCacheKey, RenderCachePolicy
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend

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
