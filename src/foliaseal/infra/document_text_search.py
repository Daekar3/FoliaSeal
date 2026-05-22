"""Concrete Qt PDF text search adapter."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtPdf import QPdfDocument

from foliaseal.application.document_text_search import DocumentTextMatch


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
        load_error = document.load(str(source_path))
        if load_error != QPdfDocument.Error.None_:
            raise RuntimeError(
                "Unable to load PDF text for search: "
                f"{self._describe_load_error(load_error)}"
            )

        matches: list[DocumentTextMatch] = []
        lowered_query = normalized_query.lower()
        query_length = len(normalized_query)
        for page_index in range(document.pageCount()):
            page_text = document.getAllText(page_index).text()
            if not page_text:
                continue
            lowered_page_text = page_text.lower()
            start_index = 0
            while True:
                hit_index = lowered_page_text.find(lowered_query, start_index)
                if hit_index < 0:
                    break
                selection = document.getSelectionAtIndex(page_index, hit_index, query_length)
                match_text = selection.text() or page_text[hit_index : hit_index + query_length]
                end_index = hit_index + len(match_text)
                matches.append(
                    DocumentTextMatch(
                        page_index=page_index,
                        start_index=hit_index,
                        end_index=end_index,
                        text=match_text,
                        context=self._context_for_match(page_text, hit_index, end_index),
                    )
                )
                start_index = hit_index + max(1, len(match_text))
        document.close()
        return tuple(matches)

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
        return error_name.replace("_", " ").lower()
