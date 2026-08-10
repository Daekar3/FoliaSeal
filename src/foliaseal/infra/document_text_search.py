"""Concrete Qt PDF text search adapter."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtPdf import QPdfDocument

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_text_search import (
    DocumentTextMatch,
    DocumentTextSearchUnavailable,
)


class QtPdfDocumentTextSearchEngine:
    """Search text in a PDF using the installed Qt PDF bindings."""

    def search(self, input_pdf_path: str, query: str) -> tuple[DocumentTextMatch, ...]:
        normalized_query = query.strip()
        if not normalized_query:
            return ()
        source_path = Path(input_pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Document text search file not found: {source_path}")

        document = QPdfDocument()
        try:
            load_error = document.load(str(source_path))
            if load_error != QPdfDocument.Error.None_:
                raise DocumentTextSearchUnavailable(self._describe_load_error(load_error))

            matches: list[DocumentTextMatch] = []
            lowered_query = normalized_query.lower()
            query_length = len(normalized_query)
            pages_with_text = 0
            for page_index in range(document.pageCount()):
                page_text = document.getAllText(page_index).text()
                if not page_text:
                    continue
                pages_with_text += 1
                lowered_page_text = page_text.lower()
                start_index = 0
                while True:
                    hit_index = lowered_page_text.find(lowered_query, start_index)
                    if hit_index < 0:
                        break
                    selection = document.getSelectionAtIndex(page_index, hit_index, query_length)
                    match_text = selection.text() or page_text[hit_index : hit_index + query_length]
                    end_index = hit_index + len(match_text)
                    page_height = self._page_height(document, page_index)
                    highlight_rects = tuple(
                        self._polygon_to_pdf_rect(polygon, page_height=page_height)
                        for polygon in selection.bounds()
                    )
                    matches.append(
                        DocumentTextMatch(
                            page_index=page_index,
                            start_index=hit_index,
                            end_index=end_index,
                            text=match_text,
                            context=self._context_for_match(page_text, hit_index, end_index),
                            highlight_rects=highlight_rects,
                        )
                    )
                    start_index = hit_index + max(1, len(match_text))
            if document.pageCount() > 0 and pages_with_text == 0:
                if self._contains_image_objects(source_path):
                    raise DocumentTextSearchUnavailable(
                        "This PDF contains only image content; OCR is not provided."
                    )
                raise DocumentTextSearchUnavailable(
                    "This PDF has no extractable text; OCR is not provided."
                )
            return tuple(matches)
        finally:
            document.close()

    def _context_for_match(self, page_text: str, start_index: int, end_index: int) -> str:
        context_start = max(0, start_index - 24)
        context_end = min(len(page_text), end_index + 24)
        context = " ".join(page_text[context_start:context_end].split())
        return context

    def _describe_load_error(self, error: QPdfDocument.Error) -> str:
        try:
            error_name = error.name
        except Exception:  # pragma: no cover - defensive enum compatibility
            error_name = str(error)
        normalized_name = error_name.replace("_", " ").lower()
        compact_name = "".join(character for character in normalized_name if character.isalnum())
        if compact_name == "incorrectpassword":
            return "This PDF is password protected; enter its password before searching text."
        if compact_name == "unsupportedsecurityscheme":
            return "This PDF uses a protection scheme that does not permit text search."
        if compact_name == "invalidfileformat":
            return "The PDF parser rejected this document as an invalid PDF."
        if compact_name == "filenotfound":
            return "The PDF file could not be found while preparing text search."
        return f"The PDF parser could not load this document ({normalized_name})."

    def _contains_image_objects(self, source_path: Path) -> bool:
        """Use the PDF object marker to distinguish image-only pages without OCR."""

        try:
            return b"/Subtype /Image" in source_path.read_bytes()
        except OSError:
            return False

    def _page_height(self, document: QPdfDocument, page_index: int) -> float:
        page_size = document.pagePointSize(page_index)
        to_tuple = getattr(page_size, "toTuple", None)
        if callable(to_tuple):
            _width, height = to_tuple()
            return float(height)
        height = getattr(page_size, "height", None)
        if callable(height):
            return float(height())
        raise DocumentTextSearchUnavailable("PDF page geometry is unavailable for text search.")

    def _polygon_to_pdf_rect(self, polygon: object, *, page_height: float) -> PdfRect:
        points = tuple(polygon)
        if not points:
            raise DocumentTextSearchUnavailable("PDF text match geometry is unavailable.")
        xs = [float(point.x()) for point in points]
        ys = [page_height - float(point.y()) for point in points]
        return PdfRect(
            x1=min(xs),
            y1=min(ys),
            x2=max(xs),
            y2=max(ys),
        )
