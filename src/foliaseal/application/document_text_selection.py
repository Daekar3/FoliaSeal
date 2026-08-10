"""Application-layer document text selection state and protocols."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from foliaseal.application.coordinate_transform import PdfRect


@dataclass(frozen=True)
class DocumentTextSelection:
    """One arbitrary text selection plus its highlight rectangles."""

    page_index: int
    text: str
    highlight_rects: tuple[PdfRect, ...]


@dataclass(frozen=True)
class DocumentTextSelectionState:
    """Immutable shell-facing state for arbitrary text selection."""

    status_text: str
    detail_text: str
    selection: DocumentTextSelection | None
    can_copy: bool
    can_clear: bool


class DocumentTextSelectionEngine(Protocol):
    """Low-level selection adapter for one PDF path."""

    def select(
        self,
        input_pdf_path: str,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentTextSelection | None:
        """Return a document text selection for one page/drag rectangle."""

    def select_all(
        self,
        input_pdf_path: str,
        *,
        page_index: int,
    ) -> DocumentTextSelection | None:
        """Return all extractable text on one page, if any."""


class DocumentTextSelectionSession:
    """Track the current arbitrary text selection for one PDF."""

    def __init__(
        self,
        *,
        input_pdf_path: str,
        selection_engine: DocumentTextSelectionEngine,
    ) -> None:
        self._input_pdf_path = input_pdf_path
        self._selection_engine = selection_engine
        self._selection: DocumentTextSelection | None = None
        self._error_detail: str | None = None

    def select(
        self,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentTextSelectionState:
        self._error_detail = None
        try:
            self._selection = self._selection_engine.select(
                self._input_pdf_path,
                page_index=page_index,
                selection_rect=selection_rect,
            )
        except Exception as exc:
            self._selection = None
            self._error_detail = str(exc)
        return self._build_state()

    def select_all(self, *, page_index: int) -> DocumentTextSelectionState:
        """Select all extractable text on one page without changing the page."""

        self._error_detail = None
        try:
            self._selection = self._selection_engine.select_all(
                self._input_pdf_path,
                page_index=page_index,
            )
        except Exception as exc:
            self._selection = None
            self._error_detail = str(exc)
        return self._build_state()

    def clear(self) -> DocumentTextSelectionState:
        self._selection = None
        self._error_detail = None
        return self._build_state()

    def current_copy_text(self) -> str | None:
        if self._selection is None:
            return None
        return self._selection.text or None

    def current_selection(self) -> DocumentTextSelection | None:
        return self._selection

    def _build_state(self) -> DocumentTextSelectionState:
        if self._error_detail is not None:
            return DocumentTextSelectionState(
                status_text="Text selection unavailable.",
                detail_text=f"Selected PDF text could not be read: {self._error_detail}",
                selection=None,
                can_copy=False,
                can_clear=False,
            )
        if self._selection is None:
            return DocumentTextSelectionState(
                status_text="No document text selected.",
                detail_text="Enable Select text, then drag across visible PDF text.",
                selection=None,
                can_copy=False,
                can_clear=False,
            )
        text = " ".join(self._selection.text.split())
        preview = text[:80]
        if len(text) > 80:
            preview = f"{preview}..."
        return DocumentTextSelectionState(
            status_text=f"Selected text on page {self._selection.page_index + 1}.",
            detail_text=preview,
            selection=self._selection,
            can_copy=bool(self._selection.text),
            can_clear=True,
        )
