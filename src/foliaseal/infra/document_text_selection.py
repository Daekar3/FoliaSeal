"""Concrete Qt PDF text selection adapter."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF
from PySide6.QtPdf import QPdfDocument

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_text_selection import DocumentTextSelection


class QtPdfDocumentTextSelectionEngine:
    """Select arbitrary text from a PDF using Qt PDF bindings."""

    def select(
        self,
        input_pdf_path: str,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentTextSelection | None:
        source_path = Path(input_pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Document text selection file not found: {source_path}")

        document = QPdfDocument()
        try:
            load_error = document.load(str(source_path))
            if load_error != QPdfDocument.Error.None_:
                raise RuntimeError(
                    "Unable to load PDF text for selection: "
                    f"{self._describe_load_error(load_error)}"
                )
            normalized_rect = selection_rect.normalized()
            selection = document.getSelection(
                page_index,
                QPointF(normalized_rect.x1, normalized_rect.y1),
                QPointF(normalized_rect.x2, normalized_rect.y2),
            )
            selected_text = selection.text()
            if not selected_text.strip():
                return None
            highlight_rects = tuple(
                self._polygon_to_pdf_rect(polygon) for polygon in selection.bounds()
            )
            if not highlight_rects:
                highlight_rects = (selection_rect.normalized(),)
            return DocumentTextSelection(
                page_index=page_index,
                text=selected_text,
                highlight_rects=highlight_rects,
            )
        finally:
            document.close()

    def _polygon_to_pdf_rect(self, polygon: object) -> PdfRect:
        points = tuple(polygon)
        if not points:
            raise ValueError("QtPdf returned an empty selection polygon.")
        xs = [float(point.x()) for point in points]
        ys = [float(point.y()) for point in points]
        return PdfRect(
            x1=min(xs),
            y1=min(ys),
            x2=max(xs),
            y2=max(ys),
        )

    def _describe_load_error(self, error: QPdfDocument.Error) -> str:
        try:
            error_name = error.name
        except Exception:  # pragma: no cover - defensive enum compatibility
            error_name = str(error)
        characters: list[str] = []
        for index, char in enumerate(error_name):
            if index > 0 and char.isupper() and error_name[index - 1].islower():
                characters.append(" ")
            characters.append(char)
        return "".join(characters).replace("_", " ").lower()
