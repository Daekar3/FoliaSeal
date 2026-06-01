"""Boundary tests for the document review/text workspace session."""

from __future__ import annotations

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewSummary,
    DocumentSignatureReviewItem,
)
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
)
from foliaseal.application.document_text_search import (
    DocumentTextMatch,
    DocumentTextSearchSession,
)
from foliaseal.application.document_text_selection import (
    DocumentTextSelection,
    DocumentTextSelectionSession,
)


class _FakeDocumentReviewInspector:
    def __init__(self, summary: DocumentReviewSummary) -> None:
        self.summary = summary
        self.calls: list[str] = []

    def inspect(self, input_pdf_path: str) -> DocumentReviewSummary:
        self.calls.append(input_pdf_path)
        return self.summary


class _FakeDocumentTextSearchEngine:
    def __init__(self, matches_by_query: dict[str, tuple[DocumentTextMatch, ...]]) -> None:
        self._matches_by_query = matches_by_query

    def search(self, input_pdf_path: str, query: str) -> tuple[DocumentTextMatch, ...]:
        del input_pdf_path
        return self._matches_by_query.get(query, ())


class _FakeDocumentTextSelectionEngine:
    def __init__(self, selection: DocumentTextSelection | None) -> None:
        self._selection = selection
        self.calls: list[tuple[str, int, PdfRect]] = []

    def select(
        self,
        input_pdf_path: str,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentTextSelection | None:
        self.calls.append((input_pdf_path, page_index, selection_rect))
        return self._selection


def _session(
    *,
    summary: DocumentReviewSummary,
    matches_by_query: dict[str, tuple[DocumentTextMatch, ...]] | None = None,
    selection: DocumentTextSelection | None = None,
) -> DocumentReviewWorkspaceSession:
    return DocumentReviewWorkspaceSession(
        document_review_inspector=_FakeDocumentReviewInspector(summary),
        document_text_search_session=DocumentTextSearchSession(
            input_pdf_path="/tmp/sample.pdf",
            search_engine=_FakeDocumentTextSearchEngine(matches_by_query or {}),
        ),
        document_text_selection_session=DocumentTextSelectionSession(
            input_pdf_path="/tmp/sample.pdf",
            selection_engine=_FakeDocumentTextSelectionEngine(selection),
        ),
        input_pdf_path="/tmp/sample.pdf",
    )


def test_workspace_refresh_preserves_selected_signature_label_when_it_still_exists() -> None:
    session = _session(
        summary=DocumentReviewSummary(
            headline="Signature review",
            detail="Found 2 embedded signatures.",
            signature_count=2,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1",
                    signer_subject="CN=Bob Example",
                    cryptographic_validation_passed=True,
                    detail="CN=Bob Example: verified locally.",
                    drill_in_detail="Signer: CN=Bob Example.",
                ),
                DocumentSignatureReviewItem(
                    label="Signature 2 (latest)",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=False,
                    detail="CN=Alice Example: needs local verification attention.",
                    drill_in_detail="Signer: CN=Alice Example.",
                ),
            ),
        )
    )

    session.load()
    state = session.select_review_signature(0)

    assert state.review.selected_signature_label == "Signature 1"

    session._document_review_inspector.summary = DocumentReviewSummary(  # type: ignore[attr-defined]
        headline="Signature review",
        detail="Found 2 embedded signatures.",
        signature_count=2,
        signature_items=(
            DocumentSignatureReviewItem(
                label="Signature 1",
                signer_subject="CN=Bob Example",
                cryptographic_validation_passed=True,
                detail="CN=Bob Example: verified locally.",
                drill_in_detail="Signer: CN=Bob Example.\nUpdated detail.",
            ),
            DocumentSignatureReviewItem(
                label="Signature 2 (latest)",
                signer_subject="CN=Alice Example",
                cryptographic_validation_passed=False,
                detail="CN=Alice Example: needs local verification attention.",
                drill_in_detail="Signer: CN=Alice Example.",
            ),
        ),
    )

    refreshed = session.refresh_review()

    assert refreshed.review.selected_signature_label == "Signature 1"
    assert refreshed.review.selected_signature_index == 0
    assert "Updated detail." in refreshed.review.selected_signature_detail


def test_workspace_search_emits_page_jump_for_current_match() -> None:
    session = _session(
        summary=DocumentReviewSummary(
            headline="No signatures found",
            detail="This PDF does not currently contain embedded signatures.",
            signature_count=0,
        ),
        matches_by_query={
            "Alice": (
                DocumentTextMatch(
                    page_index=1,
                    start_index=0,
                    end_index=5,
                    text="Alice",
                    context="Alice Example on page two",
                ),
            )
        },
    )

    session.load()
    transition = session.search_text("Alice")

    assert transition.state.document_text.search_state.status_text == "Found 1 matches for 'Alice'."
    assert transition.state.document_text.display_source == "search"
    assert transition.effects.jump_to_page_index == 1


def test_workspace_load_exposes_review_and_document_text_substates() -> None:
    session = _session(
        summary=DocumentReviewSummary(
            headline="Signature review",
            detail="Found 1 embedded signature.",
            signature_count=1,
            signature_items=(
                DocumentSignatureReviewItem(
                    label="Signature 1",
                    signer_subject="CN=Alice Example",
                    cryptographic_validation_passed=True,
                    detail="CN=Alice Example: verified locally.",
                    drill_in_detail="Signer: CN=Alice Example.",
                ),
            ),
        )
    )

    state = session.load()

    assert state.review.review_summary.headline == "Signature review"
    assert state.review.signature_labels == ("Signature 1",)
    assert state.review.selected_signature_label == "Signature 1"
    assert state.review.selected_signature_detail == "Signer: CN=Alice Example."
    assert state.document_text.search_state.status_text == "Enter text to search this PDF."
    assert state.document_text.selection_mode_enabled is False
    assert state.document_text.status_text == "No document text selected."


def test_workspace_restores_search_state_when_selection_mode_is_disabled() -> None:
    session = _session(
        summary=DocumentReviewSummary(
            headline="No signatures found",
            detail="This PDF does not currently contain embedded signatures.",
            signature_count=0,
        ),
        matches_by_query={
            "Alice": (
                DocumentTextMatch(
                    page_index=1,
                    start_index=0,
                    end_index=5,
                    text="Alice",
                    context="Alice Example on page two",
                ),
            )
        },
        selection=DocumentTextSelection(
            page_index=1,
            text="Alice Example",
            highlight_rects=(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),),
        ),
    )

    session.load()
    session.search_text("Alice")
    session.set_text_selection_mode(True)
    transition = session.handle_viewer_selection(
        page_index=1,
        selection_rect=PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),
    )

    assert transition.state.document_text.status_text == "Selected text on page 2."

    disabled = session.set_text_selection_mode(False)

    assert disabled.state.document_text.display_source == "search"
    assert disabled.state.document_text.status_text == "Found 1 matches for 'Alice'."
    assert "Showing 1 of 1 on page 2" in disabled.state.document_text.detail_text
    assert disabled.effects.interaction_mode == "signature"
    assert disabled.effects.clear_highlights is True


def test_workspace_consumes_viewer_selection_in_text_mode_and_emits_highlights() -> None:
    selection = DocumentTextSelection(
        page_index=0,
        text="Alice Example",
        highlight_rects=(PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),),
    )
    session = _session(
        summary=DocumentReviewSummary(
            headline="No signatures found",
            detail="This PDF does not currently contain embedded signatures.",
            signature_count=0,
        ),
        selection=selection,
    )

    session.load()
    session.set_text_selection_mode(True)
    transition = session.handle_viewer_selection(
        page_index=0,
        selection_rect=PdfRect(x1=10.0, y1=10.0, x2=30.0, y2=16.0),
    )

    assert transition.viewer_selection_consumed is True
    assert transition.state.document_text.display_source == "selection"
    assert transition.state.document_text.status_text == "Selected text on page 1."
    assert transition.effects.highlight_page_index == 0
    assert transition.effects.highlight_rects == selection.highlight_rects
