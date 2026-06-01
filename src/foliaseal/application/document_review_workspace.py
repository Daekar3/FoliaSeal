"""Application-layer session for document review and text interactions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewInspector,
    DocumentReviewSummary,
    DocumentSignatureReviewItem,
)
from foliaseal.application.document_text_search import (
    DocumentTextSearchSession,
    DocumentTextSearchState,
)
from foliaseal.application.document_text_selection import (
    DocumentTextSelectionSession,
    DocumentTextSelectionState,
)

DocumentTextDisplaySource = Literal["search", "selection"]
ViewerInteractionMode = Literal["signature", "text"]


@dataclass(frozen=True)
class DocumentReviewWorkspaceViewerEffects:
    """Viewer-facing effects returned by the review/text workspace session."""

    interaction_mode: ViewerInteractionMode | None = None
    jump_to_page_index: int | None = None
    highlight_page_index: int | None = None
    highlight_rects: tuple[PdfRect, ...] = ()
    clear_highlights: bool = False


@dataclass(frozen=True)
class DocumentReviewCardState:
    """Immutable state for the document-review card only."""

    review_summary: DocumentReviewSummary
    signature_labels: tuple[str, ...]
    selected_signature_index: int | None
    selected_signature_label: str | None
    selected_signature_detail: str
    selector_enabled: bool


@dataclass(frozen=True)
class DocumentTextWorkspaceState:
    """Immutable state for the document-text card only."""

    search_state: DocumentTextSearchState
    selection_state: DocumentTextSelectionState
    selection_mode_enabled: bool
    display_source: DocumentTextDisplaySource
    status_text: str
    detail_text: str


@dataclass(frozen=True)
class DocumentReviewWorkspaceState:
    """Combined immutable state composed from smaller review/text states."""

    review: DocumentReviewCardState
    document_text: DocumentTextWorkspaceState


@dataclass(frozen=True)
class DocumentReviewWorkspaceTransition:
    """Transition result for one review/text interaction."""

    state: DocumentReviewWorkspaceState
    effects: DocumentReviewWorkspaceViewerEffects = field(
        default_factory=DocumentReviewWorkspaceViewerEffects
    )
    viewer_selection_consumed: bool = False


class DocumentReviewWorkspaceSession:
    """Own review/text state transitions while leaving rendering outside."""

    def __init__(
        self,
        *,
        document_review_inspector: DocumentReviewInspector,
        document_text_search_session: DocumentTextSearchSession,
        document_text_selection_session: DocumentTextSelectionSession,
        input_pdf_path: str,
    ) -> None:
        self._document_review_inspector = document_review_inspector
        self._document_text_search_session = document_text_search_session
        self._document_text_selection_session = document_text_selection_session
        self._input_pdf_path = input_pdf_path
        self._review_summary = DocumentReviewSummary(
            headline="Review unavailable",
            detail="Current PDF could not be inspected.",
            signature_count=None,
        )
        self._selected_review_signature_label: str | None = None
        self._text_search_state = self._document_text_search_session.current_state()
        self._text_selection_state = self._document_text_selection_session.clear()
        self._text_selection_mode_enabled = False
        self._document_text_display_source: DocumentTextDisplaySource = "selection"

    def load(self) -> DocumentReviewWorkspaceState:
        self._review_summary = self._document_review_inspector.inspect(self._input_pdf_path)
        return self._build_state()

    def refresh_review(self) -> DocumentReviewWorkspaceState:
        self._review_summary = self._document_review_inspector.inspect(self._input_pdf_path)
        return self._build_state()

    def select_review_signature(self, index: int) -> DocumentReviewWorkspaceState:
        signature_items = self._review_summary.signature_items
        if index < 0 or index >= len(signature_items):
            self._selected_review_signature_label = None
            return self._build_state()
        self._selected_review_signature_label = signature_items[index].label
        return self._build_state()

    def search_text(self, query: str) -> DocumentReviewWorkspaceTransition:
        self._text_search_state = self._document_text_search_session.search(query)
        self._document_text_display_source = "search"
        return DocumentReviewWorkspaceTransition(
            state=self._build_state(),
            effects=self._current_match_effects(),
        )

    def next_text_match(self) -> DocumentReviewWorkspaceTransition:
        self._text_search_state = self._document_text_search_session.next_match()
        self._document_text_display_source = "search"
        return DocumentReviewWorkspaceTransition(
            state=self._build_state(),
            effects=self._current_match_effects(),
        )

    def previous_text_match(self) -> DocumentReviewWorkspaceTransition:
        self._text_search_state = self._document_text_search_session.previous_match()
        self._document_text_display_source = "search"
        return DocumentReviewWorkspaceTransition(
            state=self._build_state(),
            effects=self._current_match_effects(),
        )

    def set_text_selection_mode(self, enabled: bool) -> DocumentReviewWorkspaceTransition:
        self._text_selection_mode_enabled = bool(enabled)
        effects = DocumentReviewWorkspaceViewerEffects(
            interaction_mode="text" if self._text_selection_mode_enabled else "signature",
        )
        if not self._text_selection_mode_enabled:
            self._text_selection_state = self._document_text_selection_session.clear()
            self._document_text_display_source = "search"
            effects = DocumentReviewWorkspaceViewerEffects(
                interaction_mode="signature",
                clear_highlights=True,
            )
        return DocumentReviewWorkspaceTransition(
            state=self._build_state(),
            effects=effects,
        )

    def handle_viewer_selection(
        self,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentReviewWorkspaceTransition:
        if not self._text_selection_mode_enabled:
            return DocumentReviewWorkspaceTransition(
                state=self._build_state(),
                viewer_selection_consumed=False,
            )
        self._text_selection_state = self._document_text_selection_session.select(
            page_index=page_index,
            selection_rect=selection_rect,
        )
        self._document_text_display_source = "selection"
        selection = self._text_selection_state.selection
        effects = DocumentReviewWorkspaceViewerEffects(clear_highlights=selection is None)
        if selection is not None:
            effects = DocumentReviewWorkspaceViewerEffects(
                highlight_page_index=selection.page_index,
                highlight_rects=selection.highlight_rects,
            )
        return DocumentReviewWorkspaceTransition(
            state=self._build_state(),
            effects=effects,
            viewer_selection_consumed=True,
        )

    def clear_selected_text(self) -> DocumentReviewWorkspaceTransition:
        self._text_selection_state = self._document_text_selection_session.clear()
        self._document_text_display_source = "selection"
        return DocumentReviewWorkspaceTransition(
            state=self._build_state(),
            effects=DocumentReviewWorkspaceViewerEffects(clear_highlights=True),
        )

    def copy_current_text_match(self) -> str | None:
        return self._document_text_search_session.current_copy_text()

    def copy_selected_text(self) -> str | None:
        return self._document_text_selection_session.current_copy_text()

    def _current_match_effects(self) -> DocumentReviewWorkspaceViewerEffects:
        current_match = self._text_search_state.current_match
        if current_match is None:
            return DocumentReviewWorkspaceViewerEffects()
        return DocumentReviewWorkspaceViewerEffects(
            jump_to_page_index=current_match.page_index
        )

    def _build_state(self) -> DocumentReviewWorkspaceState:
        (
            selected_index,
            selected_label,
            selected_detail,
            review_selector_enabled,
            review_signature_labels,
        ) = self._selected_review_signature_state(self._review_summary.signature_items)
        if self._document_text_display_source == "search":
            document_text_status_text = self._text_search_state.status_text
            document_text_detail_text = self._text_search_state.detail_text
        else:
            document_text_status_text = self._text_selection_state.status_text
            document_text_detail_text = self._text_selection_state.detail_text
        return DocumentReviewWorkspaceState(
            review=DocumentReviewCardState(
                review_summary=self._review_summary,
                signature_labels=review_signature_labels,
                selected_signature_index=selected_index,
                selected_signature_label=selected_label,
                selected_signature_detail=selected_detail,
                selector_enabled=review_selector_enabled,
            ),
            document_text=DocumentTextWorkspaceState(
                search_state=self._text_search_state,
                selection_state=self._text_selection_state,
                selection_mode_enabled=self._text_selection_mode_enabled,
                display_source=self._document_text_display_source,
                status_text=document_text_status_text,
                detail_text=document_text_detail_text,
            ),
        )

    def _selected_review_signature_state(
        self,
        signature_items: tuple[DocumentSignatureReviewItem, ...],
    ) -> tuple[int | None, str | None, str, bool, tuple[str, ...]]:
        if not signature_items:
            self._selected_review_signature_label = None
            return None, None, "", False, ()
        review_signature_labels = tuple(item.label for item in signature_items)
        selected_label = self._selected_review_signature_label
        selected_index = next(
            (
                index
                for index, item in enumerate(signature_items)
                if item.label == selected_label
            ),
            len(signature_items) - 1,
        )
        selected_item = signature_items[selected_index]
        self._selected_review_signature_label = selected_item.label
        return (
            selected_index,
            selected_item.label,
            selected_item.drill_in_detail,
            len(signature_items) > 1,
            review_signature_labels,
        )
