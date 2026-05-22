"""Application-layer document text search state and protocols."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DocumentTextMatch:
    """One matched text span in a PDF document."""

    page_index: int
    start_index: int
    end_index: int
    text: str
    context: str


@dataclass(frozen=True)
class DocumentTextSearchState:
    """Immutable shell-facing state for document text search."""

    query: str
    match_count: int
    current_index: int | None
    status_text: str
    detail_text: str
    current_match: DocumentTextMatch | None
    can_go_previous: bool
    can_go_next: bool
    can_copy: bool


class DocumentTextSearchEngine(Protocol):
    """Low-level search adapter for one PDF path."""

    def search(self, input_pdf_path: str, query: str) -> tuple[DocumentTextMatch, ...]:
        """Return all matches for a query in the given PDF."""


class DocumentTextSearchSession:
    """Manage query state and current-hit navigation for one PDF."""

    def __init__(
        self,
        *,
        input_pdf_path: str,
        search_engine: DocumentTextSearchEngine,
    ) -> None:
        self._input_pdf_path = input_pdf_path
        self._search_engine = search_engine
        self._query = ""
        self._matches: tuple[DocumentTextMatch, ...] = ()
        self._current_index: int | None = None
        self._error_detail: str | None = None

    def search(self, query: str) -> DocumentTextSearchState:
        normalized_query = query.strip()
        self._query = normalized_query
        self._error_detail = None
        if not normalized_query:
            self._matches = ()
            self._current_index = None
            return self._build_state()
        try:
            self._matches = self._search_engine.search(self._input_pdf_path, normalized_query)
        except Exception as exc:
            self._matches = ()
            self._current_index = None
            self._error_detail = str(exc)
            return self._build_state()
        self._current_index = 0 if self._matches else None
        return self._build_state()

    def next_match(self) -> DocumentTextSearchState:
        if self._current_index is None or not self._matches:
            return self._build_state()
        self._current_index = min(self._current_index + 1, len(self._matches) - 1)
        return self._build_state()

    def previous_match(self) -> DocumentTextSearchState:
        if self._current_index is None or not self._matches:
            return self._build_state()
        self._current_index = max(self._current_index - 1, 0)
        return self._build_state()

    def current_copy_text(self) -> str | None:
        if self._current_index is None or not self._matches:
            return None
        return self._matches[self._current_index].text or None

    def current_page_index(self) -> int | None:
        if self._current_index is None or not self._matches:
            return None
        return self._matches[self._current_index].page_index

    def _build_state(self) -> DocumentTextSearchState:
        if self._error_detail is not None:
            return DocumentTextSearchState(
                query=self._query,
                match_count=0,
                current_index=None,
                status_text="Text search unavailable.",
                detail_text=f"Current PDF text could not be searched: {self._error_detail}",
                current_match=None,
                can_go_previous=False,
                can_go_next=False,
                can_copy=False,
            )
        if not self._query:
            return DocumentTextSearchState(
                query="",
                match_count=0,
                current_index=None,
                status_text="Enter text to search this PDF.",
                detail_text="",
                current_match=None,
                can_go_previous=False,
                can_go_next=False,
                can_copy=False,
            )
        if not self._matches or self._current_index is None:
            return DocumentTextSearchState(
                query=self._query,
                match_count=0,
                current_index=None,
                status_text=f"No matches for '{self._query}'.",
                detail_text="Try a different phrase or check spelling.",
                current_match=None,
                can_go_previous=False,
                can_go_next=False,
                can_copy=False,
            )

        current_match = self._matches[self._current_index]
        return DocumentTextSearchState(
            query=self._query,
            match_count=len(self._matches),
            current_index=self._current_index,
            status_text=f"Found {len(self._matches)} matches for '{self._query}'.",
            detail_text=(
                f"Showing {self._current_index + 1} of {len(self._matches)} "
                f"on page {current_match.page_index + 1}: {current_match.context}"
            ),
            current_match=current_match,
            can_go_previous=self._current_index > 0,
            can_go_next=self._current_index < len(self._matches) - 1,
            can_copy=bool(current_match.text),
        )
