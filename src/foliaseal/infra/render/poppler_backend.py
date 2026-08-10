"""Poppler-backed page rasterisation for the interactive PDF viewer.

QtPdf remains the authoritative geometry source: its page boxes and rotation are
already used by the placement-coordinate transform.  Poppler is deliberately
used for pixels, since it renders some signed PDFs that QtPdf opens but paints
as an empty canvas.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from foliaseal.application.document_links import DocumentLink
from foliaseal.infra.render.base import (
    PdfPageGeometry,
    PdfRenderBackend,
    RenderBackendDiagnostic,
    RenderPageRequest,
    RenderPageResult,
)
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend


class PopplerPdfRenderBackend:
    """Render page pixels with ``pdftoppm`` while retaining Qt geometry.

    The command is late-resolved so non-desktop callers can still import the
    application.  ``pdftoppm`` renders at 72 dpi per zoom unit, matching the
    point-based scale used by :class:`QtPdfRenderBackend`.
    """

    def __init__(
        self,
        *,
        geometry_backend: PdfRenderBackend | None = None,
        executable: str = "pdftoppm",
    ) -> None:
        self._geometry_backend = geometry_backend or QtPdfRenderBackend()
        self._executable = executable

    def diagnostics(self) -> RenderBackendDiagnostic:
        executable = shutil.which(self._executable)
        if executable is None:
            return RenderBackendDiagnostic(
                backend_name="poppler-render-backend",
                available=False,
                message=(
                    "Poppler render backend is unavailable. Install pdftoppm to render "
                    "PDF pages in the interactive viewer."
                ),
            )
        geometry = self._geometry_backend.diagnostics()
        if not geometry.available:
            return RenderBackendDiagnostic(
                backend_name="poppler-render-backend",
                available=False,
                message=(
                    "Poppler can rasterise pages, but PDF placement geometry is unavailable. "
                    f"Details: {geometry.message}"
                ),
            )
        return RenderBackendDiagnostic(
            backend_name="poppler-render-backend",
            available=True,
            message="Poppler raster rendering and QtPdf placement geometry are available.",
        )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        return self._geometry_backend.get_page_geometry(document_path, page_index)

    def inspect_links(self, document_path: str, page_index: int) -> tuple[DocumentLink, ...]:
        """Delegate optional link inspection to the QtPdf geometry adapter."""
        inspector = getattr(self._geometry_backend, "inspect_links", None)
        if not callable(inspector):
            raise RuntimeError("PDF link inspection is unavailable for this render backend.")
        return tuple(inspector(document_path, page_index))

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        if request.zoom <= 0:
            raise ValueError("zoom must be greater than zero.")
        document_path = Path(request.document_path)
        if not document_path.exists():
            raise FileNotFoundError(f"Document does not exist: {document_path}")
        executable = shutil.which(self._executable)
        if executable is None:
            raise RuntimeError(self.diagnostics().message)

        with tempfile.TemporaryDirectory(prefix="foliaseal-poppler-") as temporary_dir:
            output_prefix = Path(temporary_dir) / "page"
            command = [
                executable,
                "-f",
                str(request.page_index + 1),
                "-l",
                str(request.page_index + 1),
                "-r",
                str(72.0 * request.zoom),
                "-png",
                "-singlefile",
                str(document_path),
                str(output_prefix),
            ]
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip()
                raise RuntimeError(f"Poppler failed to render PDF page: {detail}")
            png_path = output_prefix.with_suffix(".png")
            if not png_path.exists():
                raise RuntimeError("Poppler completed without producing a page image.")
            with Image.open(png_path) as image:
                rgba = image.convert("RGBA")
                return RenderPageResult(
                    width_px=rgba.width,
                    height_px=rgba.height,
                    rgba_bytes=rgba.tobytes(),
                )
