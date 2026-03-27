"""Qt-based render backend adapter with graceful fallback diagnostics."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pdf_signer.infra.render.base import (
    PdfPageGeometry,
    RenderBackendDiagnostic,
    RenderPageRequest,
    RenderPageResult,
)


@dataclass(frozen=True)
class _QtBindings:
    qpdf_document: type[Any]
    qimage: type[Any]


class QtPdfRenderBackend:
    """Render backend using QtPdf + QImage conversion APIs.

    This adapter performs late imports so the project can run in environments
    where Qt bindings are not installed yet.
    """

    def __init__(self) -> None:
        self._bindings_error: str | None = None
        self._bindings: _QtBindings | None = self._load_bindings()

    def diagnostics(self) -> RenderBackendDiagnostic:
        if self._bindings is None:
            return RenderBackendDiagnostic(
                backend_name="qtpdf-render-backend",
                available=False,
                message=(
                    "Qt render backend is unavailable. Install PySide6 with QtPdf support. "
                    f"Details: {self._bindings_error}"
                ),
            )
        return RenderBackendDiagnostic(
            backend_name="qtpdf-render-backend",
            available=True,
            message="QtPdf render backend is available.",
        )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        document = self._open_document(document_path)
        page = self._get_page(document, page_index)

        media = tuple(float(v) for v in page.pageSizePoints())
        width, height = media
        media_box = (0.0, 0.0, width, height)

        # QtPdf exposes page size and rotation, but not explicit crop boxes.
        # For now, use media box as effective crop box.
        return PdfPageGeometry(
            media_box=media_box,
            crop_box=media_box,
            rotation=int(page.rotation()),
        )

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        if request.zoom <= 0:
            raise ValueError("zoom must be greater than zero.")

        document = self._open_document(request.document_path)
        page = self._get_page(document, request.page_index)

        width_pts, height_pts = (float(v) for v in page.pageSizePoints())
        target_width = max(1, int(round(width_pts * request.zoom)))
        target_height = max(1, int(round(height_pts * request.zoom)))

        image = self._bindings.qimage(  # type: ignore[union-attr]
            target_width,
            target_height,
            self._bindings.qimage.Format_RGBA8888,  # type: ignore[union-attr]
        )
        image.fill(0)

        painter = self._import_type("PySide6.QtGui", "QPainter")(image)
        try:
            render_opts = self._import_type("PySide6.QtPdf", "QPdfDocumentRenderOptions")()
            page.render(painter, render_opts)
        finally:
            painter.end()

        raw = image.bits().tobytes(target_width * target_height * 4)
        return RenderPageResult(width_px=target_width, height_px=target_height, rgba_bytes=raw)

    def _open_document(self, document_path: str) -> Any:
        if not Path(document_path).exists():
            raise FileNotFoundError(f"Document does not exist: {document_path}")
        self._require_available()
        document = self._bindings.qpdf_document()  # type: ignore[union-attr]
        status = document.load(document_path)
        error_none = self._import_type("PySide6.QtPdf", "QPdfDocument").Error.None_
        if status != error_none:
            raise RuntimeError(f"Failed to load PDF document: {document_path}")
        return document

    def _get_page(self, document: Any, page_index: int) -> Any:
        page_count = int(document.pageCount())
        if page_index < 0 or page_index >= page_count:
            raise ValueError(f"page_index out of range for document: {page_index}")
        return document.page(page_index)

    def _require_available(self) -> None:
        if self._bindings is None:
            raise RuntimeError(self.diagnostics().message)

    def _load_bindings(self) -> _QtBindings | None:
        try:
            qpdf_document = self._import_type("PySide6.QtPdf", "QPdfDocument")
            qimage = self._import_type("PySide6.QtGui", "QImage")
        except Exception as exc:  # pragma: no cover - driven by environment
            self._bindings_error = str(exc)
            return None
        return _QtBindings(qpdf_document=qpdf_document, qimage=qimage)

    @staticmethod
    def _import_type(module: str, symbol: str) -> Any:
        imported = importlib.import_module(module)
        return getattr(imported, symbol)
