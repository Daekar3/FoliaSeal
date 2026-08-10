from pathlib import Path

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_text_selection import (
    DocumentTextSelection,
    DocumentTextSelectionSession,
)
from foliaseal.infra.document_text_selection import QtPdfDocumentTextSelectionEngine


class _FakeSelectionEngine:
    def __init__(
        self,
        *,
        selection: DocumentTextSelection | None = None,
        error: Exception | None = None,
        select_all_selection: DocumentTextSelection | None = None,
        select_all_error: Exception | None = None,
    ) -> None:
        self.selection = selection
        self.error = error
        self.select_all_selection = select_all_selection
        self.select_all_error = select_all_error
        self.calls = []
        self.select_all_calls = []

    def select(
        self,
        input_pdf_path: str,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentTextSelection | None:
        self.calls.append((input_pdf_path, page_index, selection_rect))
        if self.error is not None:
            raise self.error
        return self.selection

    def select_all(
        self,
        input_pdf_path: str,
        *,
        page_index: int,
    ) -> DocumentTextSelection | None:
        self.select_all_calls.append((input_pdf_path, page_index))
        if self.select_all_error is not None:
            raise self.select_all_error
        return self.select_all_selection


def test_document_text_selection_session_reports_empty_selection(tmp_path: Path) -> None:
    session = DocumentTextSelectionSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        selection_engine=_FakeSelectionEngine(selection=None),
    )

    state = session.select(
        page_index=0,
        selection_rect=PdfRect(x1=1.0, y1=2.0, x2=3.0, y2=4.0),
    )

    assert state.selection is None
    assert state.status_text == "No document text selected."
    assert state.detail_text == "Enable Select text, then drag across visible PDF text."
    assert state.can_copy is False
    assert state.can_clear is False


def test_document_text_selection_session_tracks_selected_text_and_clear(tmp_path: Path) -> None:
    selection = DocumentTextSelection(
        page_index=1,
        text="Alice Example signed here",
        highlight_rects=(PdfRect(x1=10.0, y1=11.0, x2=20.0, y2=13.0),),
    )
    session = DocumentTextSelectionSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        selection_engine=_FakeSelectionEngine(selection=selection),
    )

    selected = session.select(
        page_index=1,
        selection_rect=PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=15.0),
    )
    cleared = session.clear()

    assert selected.selection == selection
    assert selected.status_text == "Selected text on page 2."
    assert selected.detail_text == "Alice Example signed here"
    assert selected.can_copy is True
    assert selected.can_clear is True
    assert session.current_copy_text() is None
    assert cleared.selection is None
    assert cleared.can_copy is False
    assert cleared.can_clear is False


def test_document_text_selection_session_reports_selection_errors(tmp_path: Path) -> None:
    session = DocumentTextSelectionSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        selection_engine=_FakeSelectionEngine(error=RuntimeError("backend offline")),
    )

    state = session.select(
        page_index=0,
        selection_rect=PdfRect(x1=0.0, y1=0.0, x2=5.0, y2=5.0),
    )

    assert state.selection is None
    assert state.status_text == "Text selection unavailable."
    assert "backend offline" in state.detail_text


def test_document_text_selection_session_select_all_tracks_current_page(tmp_path: Path) -> None:
    selection = DocumentTextSelection(
        page_index=2,
        text="Alice Example on page three",
        highlight_rects=(PdfRect(x1=10.0, y1=20.0, x2=40.0, y2=30.0),),
    )
    engine = _FakeSelectionEngine(select_all_selection=selection)
    session = DocumentTextSelectionSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        selection_engine=engine,
    )

    state = session.select_all(page_index=2)

    assert engine.select_all_calls == [(str(tmp_path / "sample.pdf"), 2)]
    assert state.selection == selection
    assert state.status_text == "Selected text on page 3."
    assert state.can_copy is True


def test_document_text_selection_session_select_all_reports_backend_failure(
    tmp_path: Path,
) -> None:
    session = DocumentTextSelectionSession(
        input_pdf_path=str(tmp_path / "sample.pdf"),
        selection_engine=_FakeSelectionEngine(select_all_error=RuntimeError("parser offline")),
    )

    state = session.select_all(page_index=0)

    assert state.selection is None
    assert state.status_text == "Text selection unavailable."
    assert "parser offline" in state.detail_text


class _FakePoint:
    def __init__(self, x_value: float, y_value: float) -> None:
        self._x = x_value
        self._y = y_value

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y


class _FakeSelection:
    def __init__(self, *, text: str, polygons: tuple[tuple[_FakePoint, ...], ...]) -> None:
        self._text = text
        self._polygons = polygons

    def text(self) -> str:
        return self._text

    def bounds(self):
        return self._polygons


class _FakeQPointF:
    def __init__(self, x_value: float, y_value: float) -> None:
        self.x_value = x_value
        self.y_value = y_value


class _FakeQPdfDocument:
    class Error:
        None_ = "none"

    last_selection_call = None

    class _FakePageSize:
        def __init__(self, width: float, height: float) -> None:
            self._width = width
            self._height = height

        def toTuple(self):
            return (self._width, self._height)

    def load(self, file_name: str):
        self.loaded = file_name
        return self.Error.None_

    def pagePointSize(self, page_index: int):  # noqa: N802
        return self._FakePageSize(72.0, 100.0)

    def getSelection(self, page_index: int, start: _FakeQPointF, end: _FakeQPointF):
        type(self).last_selection_call = (page_index, start, end)
        return _FakeSelection(
            text="Alice Example",
            polygons=(
                (
                    _FakePoint(10.0, 12.0),
                    _FakePoint(22.0, 12.0),
                    _FakePoint(22.0, 16.0),
                    _FakePoint(10.0, 16.0),
                ),
            ),
        )

    def close(self) -> None:
        return None


class _FakeLoadError:
    name = "DataNotYetAvailable"


class _FakeLoadFailureQPdfDocument(_FakeQPdfDocument):
    class Error:
        None_ = "none"

    def load(self, file_name: str):
        self.loaded = file_name
        return _FakeLoadError()


class _FakeEmptySelectionQPdfDocument(_FakeQPdfDocument):
    def getSelection(self, page_index: int, start: _FakeQPointF, end: _FakeQPointF):
        type(self).last_selection_call = (page_index, start, end)
        return _FakeSelection(text="   ", polygons=())


class _FakeNoBoundsQPdfDocument(_FakeQPdfDocument):
    def getSelection(self, page_index: int, start: _FakeQPointF, end: _FakeQPointF):
        type(self).last_selection_call = (page_index, start, end)
        return _FakeSelection(text="Alice Example", polygons=())


class _FakeAllTextQPdfDocument(_FakeQPdfDocument):
    last_select_all_call = None

    def getAllText(self, page_index: int):  # noqa: N802
        type(self).last_select_all_call = ("all_text", page_index)
        return _FakeSelection(text="Alice Example on page", polygons=())

    def getSelectionAtIndex(self, page_index: int, start_index: int, max_length: int):  # noqa: N802
        type(self).last_select_all_call = (page_index, start_index, max_length)
        return _FakeSelection(
            text="Alice Example on page",
            polygons=(
                (
                    _FakePoint(10.0, 12.0),
                    _FakePoint(40.0, 12.0),
                    _FakePoint(40.0, 16.0),
                    _FakePoint(10.0, 16.0),
                ),
            ),
        )


class _FakeEmptyAllTextQPdfDocument(_FakeAllTextQPdfDocument):
    def getAllText(self, page_index: int):  # noqa: N802
        del page_index
        return _FakeSelection(text="   ", polygons=())


def test_qt_pdf_document_text_selection_engine_returns_text_and_highlights(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPdfDocument",
        _FakeQPdfDocument,
    )
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPointF",
        _FakeQPointF,
    )
    engine = QtPdfDocumentTextSelectionEngine()

    selection = engine.select(
        str(source_path),
        page_index=2,
        selection_rect=PdfRect(x1=40.0, y1=30.0, x2=10.0, y2=12.0),
    )

    assert selection is not None
    assert selection.page_index == 2
    assert selection.text == "Alice Example"
    assert len(selection.highlight_rects) == 1
    assert selection.highlight_rects[0] == PdfRect(x1=10.0, y1=84.0, x2=22.0, y2=88.0)
    assert _FakeQPdfDocument.last_selection_call[0] == 2
    assert _FakeQPdfDocument.last_selection_call[1].x_value == 10.0
    assert _FakeQPdfDocument.last_selection_call[1].y_value == 70.0
    assert _FakeQPdfDocument.last_selection_call[2].x_value == 40.0
    assert _FakeQPdfDocument.last_selection_call[2].y_value == 88.0


def test_qt_pdf_document_text_selection_engine_reports_missing_file(tmp_path: Path) -> None:
    engine = QtPdfDocumentTextSelectionEngine()

    try:
        engine.select(
            str(tmp_path / "missing.pdf"),
            page_index=0,
            selection_rect=PdfRect(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
        )
    except FileNotFoundError as exc:
        assert "missing.pdf" in str(exc)
    else:  # pragma: no cover - defensive failure path
        raise AssertionError("Expected FileNotFoundError")


def test_qt_pdf_document_text_selection_engine_reports_load_failures(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPdfDocument",
        _FakeLoadFailureQPdfDocument,
    )
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPointF",
        _FakeQPointF,
    )
    engine = QtPdfDocumentTextSelectionEngine()

    try:
        engine.select(
            str(source_path),
            page_index=0,
            selection_rect=PdfRect(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
        )
    except RuntimeError as exc:
        assert "data not yet available" in str(exc)
    else:  # pragma: no cover - defensive failure path
        raise AssertionError("Expected RuntimeError")


def test_qt_pdf_document_text_selection_engine_returns_none_for_empty_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPdfDocument",
        _FakeEmptySelectionQPdfDocument,
    )
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPointF",
        _FakeQPointF,
    )
    engine = QtPdfDocumentTextSelectionEngine()

    selection = engine.select(
        str(source_path),
        page_index=0,
        selection_rect=PdfRect(x1=1.0, y1=1.0, x2=2.0, y2=2.0),
    )

    assert selection is None


def test_qt_pdf_document_text_selection_engine_falls_back_when_bounds_are_empty(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPdfDocument",
        _FakeNoBoundsQPdfDocument,
    )
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPointF",
        _FakeQPointF,
    )
    engine = QtPdfDocumentTextSelectionEngine()

    selection = engine.select(
        str(source_path),
        page_index=1,
        selection_rect=PdfRect(x1=4.0, y1=8.0, x2=12.0, y2=20.0),
    )

    assert selection is not None
    assert selection.highlight_rects == (PdfRect(x1=4.0, y1=8.0, x2=12.0, y2=20.0),)


def test_qt_pdf_document_text_selection_engine_selects_all_page_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPdfDocument",
        _FakeAllTextQPdfDocument,
    )
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPointF",
        _FakeQPointF,
    )

    selection = QtPdfDocumentTextSelectionEngine().select_all(
        str(source_path),
        page_index=1,
    )

    assert selection is not None
    assert selection.page_index == 1
    assert selection.text == "Alice Example on page"
    assert selection.highlight_rects == (PdfRect(x1=10.0, y1=84.0, x2=40.0, y2=88.0),)
    assert _FakeAllTextQPdfDocument.last_select_all_call == (1, 0, len(selection.text))


def test_qt_pdf_document_text_selection_engine_select_all_returns_none_for_empty_page(
    monkeypatch,
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "sample.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr(
        "foliaseal.infra.document_text_selection.QPdfDocument",
        _FakeEmptyAllTextQPdfDocument,
    )

    assert QtPdfDocumentTextSelectionEngine().select_all(str(source_path), page_index=0) is None
