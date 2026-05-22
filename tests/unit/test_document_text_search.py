from pathlib import Path

from foliaseal.application.document_text_search import (
    DocumentTextMatch,
    DocumentTextSearchSession,
)
from foliaseal.infra.document_text_search import QtPdfDocumentTextSearchEngine


class _FakeSearchEngine:
    def __init__(self, matches=(), *, error: Exception | None = None) -> None:
        self.matches = tuple(matches)
        self.error = error
        self.calls = []

    def search(self, input_pdf_path: str, query: str) -> tuple[DocumentTextMatch, ...]:
        self.calls.append((input_pdf_path, query))
        if self.error is not None:
            raise self.error
        return self.matches


def test_document_text_search_session_reports_blank_query_without_engine_call(
    tmp_path: Path,
) -> None:
    engine = _FakeSearchEngine(
        matches=(
            DocumentTextMatch(
                page_index=0,
                start_index=0,
                end_index=6,
                text="alpha",
                context="alpha beta gamma",
            ),
        )
    )
    session = DocumentTextSearchSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        search_engine=engine,
    )

    state = session.search("   ")

    assert state.query == ""
    assert state.match_count == 0
    assert state.current_match is None
    assert state.status_text == "Enter text to search this PDF."
    assert state.detail_text == ""
    assert state.can_copy is False
    assert engine.calls == []


def test_document_text_search_session_tracks_hits_and_navigation(tmp_path: Path) -> None:
    matches = (
        DocumentTextMatch(
            page_index=1,
            start_index=10,
            end_index=15,
            text="Alice",
            context="Signed by Alice Example on page two",
        ),
        DocumentTextMatch(
            page_index=2,
            start_index=3,
            end_index=8,
            text="Alice",
            context="Second Alice hit on page three",
        ),
    )
    session = DocumentTextSearchSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        search_engine=_FakeSearchEngine(matches=matches),
    )

    initial = session.search("Alice")
    second = session.next_match()
    back = session.previous_match()

    assert initial.match_count == 2
    assert initial.current_match == matches[0]
    assert initial.can_go_previous is False
    assert initial.can_go_next is True
    assert initial.status_text == "Found 2 matches for 'Alice'."
    assert "Showing 1 of 2 on page 2" in initial.detail_text
    assert session.current_copy_text() == "Alice"

    assert second.current_match == matches[1]
    assert second.can_go_previous is True
    assert second.can_go_next is False
    assert "Showing 2 of 2 on page 3" in second.detail_text

    assert back.current_match == matches[0]
    assert back.can_go_previous is False
    assert back.can_go_next is True


def test_document_text_search_session_reports_no_matches(tmp_path: Path) -> None:
    session = DocumentTextSearchSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        search_engine=_FakeSearchEngine(matches=()),
    )

    state = session.search("invoice")

    assert state.query == "invoice"
    assert state.match_count == 0
    assert state.current_match is None
    assert state.status_text == "No matches for 'invoice'."
    assert "Try a different phrase" in state.detail_text
    assert state.can_copy is False


def test_document_text_search_session_reports_search_errors(tmp_path: Path) -> None:
    session = DocumentTextSearchSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        search_engine=_FakeSearchEngine(error=RuntimeError("bad pdf")),
    )

    state = session.search("Alice")

    assert state.match_count == 0
    assert state.current_match is None
    assert state.status_text == "Text search unavailable."
    assert "bad pdf" in state.detail_text
    assert session.current_copy_text() is None


def test_qt_pdf_document_text_search_engine_finds_matches(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n")

    class _FakeSelection:
        def __init__(self, text: str) -> None:
            self._text = text

        def text(self) -> str:
            return self._text

    class _FakeQPdfDocument:
        class Error:
            None_ = 0

        def __init__(self) -> None:
            self.loaded_path = None
            self.pages = (
                "Alpha beta ALPHA",
                "No match here",
            )

        def load(self, file_name: str):
            self.loaded_path = file_name
            return self.Error.None_

        def pageCount(self) -> int:  # noqa: N802
            return len(self.pages)

        def getAllText(self, page: int):  # noqa: N802
            return _FakeSelection(self.pages[page])

        def getSelectionAtIndex(self, page: int, start_index: int, max_length: int):  # noqa: N802
            return _FakeSelection(self.pages[page][start_index : start_index + max_length])

        def close(self) -> None:
            return None

    monkeypatch.setattr(
        "foliaseal.infra.document_text_search.QPdfDocument",
        _FakeQPdfDocument,
    )

    matches = QtPdfDocumentTextSearchEngine().search(str(pdf_path), "alpha")

    assert len(matches) == 2
    assert matches[0].page_index == 0
    assert matches[0].text == "Alpha"
    assert "Alpha beta ALPHA" in matches[0].context
    assert matches[1].text == "ALPHA"


def test_qt_pdf_document_text_search_engine_reports_missing_file(tmp_path: Path) -> None:
    engine = QtPdfDocumentTextSearchEngine()

    try:
        engine.search(str(tmp_path / "missing.pdf"), "alpha")
    except FileNotFoundError as exc:
        assert "missing.pdf" in str(exc)
    else:  # pragma: no cover - defensive assertion
        raise AssertionError("expected missing file error")
