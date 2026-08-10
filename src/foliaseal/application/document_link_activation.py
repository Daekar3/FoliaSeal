"""Pure link hit-testing, policy projection, and lightweight page history."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_links import DocumentLink
from foliaseal.application.document_safety import (
    LinkDecision,
    LinkInteractionMode,
    classify_link_destination,
)


@dataclass(frozen=True)
class DocumentLinkActivation:
    """The policy result for one PDF-space pointer location."""

    link: DocumentLink | None = None
    rectangle: PdfRect | None = None
    decision: LinkDecision | None = None

    @property
    def is_hit(self) -> bool:
        return self.link is not None and self.rectangle is not None


class DocumentLinkActivationService:
    """Resolve one pointer location without I/O, launching, or viewer mutation."""

    def resolve(
        self,
        *,
        page_index: int,
        pdf_x: float,
        pdf_y: float,
        links: tuple[DocumentLink, ...],
        interaction_mode: LinkInteractionMode,
    ) -> DocumentLinkActivation:
        for link in links:
            if link.page_index != page_index:
                continue
            for rectangle in link.rectangles:
                normalized = rectangle.normalized()
                if not _contains(normalized, pdf_x, pdf_y):
                    continue
                decision = classify_link_destination(
                    link.raw_destination,
                    internal_page_index=link.internal_page_index,
                    interaction_mode=interaction_mode,
                )
                return DocumentLinkActivation(
                    link=link,
                    rectangle=normalized,
                    decision=decision,
                )
        return DocumentLinkActivation()


class ViewerLinkHistory:
    """Page-index Back/Forward history for internal document links."""

    def __init__(self, *, current_page_index: int = 0) -> None:
        self.reset(current_page_index)

    @property
    def can_go_back(self) -> bool:
        return bool(self._back_pages)

    @property
    def can_go_forward(self) -> bool:
        return bool(self._forward_pages)

    @property
    def current_page_index(self) -> int:
        return self._current_page_index

    def record_internal_navigation(self, *, from_page_index: int, to_page_index: int) -> None:
        if from_page_index == to_page_index:
            self._current_page_index = to_page_index
            return
        self._back_pages.append(from_page_index)
        self._forward_pages.clear()
        self._current_page_index = to_page_index

    def back(self) -> int | None:
        if not self._back_pages:
            return None
        target = self._back_pages.pop()
        self._forward_pages.append(self._current_page_index)
        self._current_page_index = target
        return target

    def forward(self) -> int | None:
        if not self._forward_pages:
            return None
        target = self._forward_pages.pop()
        self._back_pages.append(self._current_page_index)
        self._current_page_index = target
        return target

    def reset(self, current_page_index: int) -> None:
        if current_page_index < 0:
            raise ValueError("current_page_index must not be negative.")
        self._current_page_index = current_page_index
        self._back_pages: list[int] = []
        self._forward_pages: list[int] = []


def _contains(rectangle: PdfRect, pdf_x: float, pdf_y: float) -> bool:
    return (
        rectangle.x1 <= pdf_x <= rectangle.x2
        and rectangle.y1 <= pdf_y <= rectangle.y2
    )


__all__ = [
    "DocumentLinkActivation",
    "DocumentLinkActivationService",
    "ViewerLinkHistory",
]
