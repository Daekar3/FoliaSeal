"""Neutral document-link inspection contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from foliaseal.application.coordinate_transform import PdfRect


@dataclass(frozen=True)
class DocumentLink:
    """One page-local link with normalized PDF-space rectangles."""

    page_index: int
    rectangles: tuple[PdfRect, ...]
    raw_destination: str | None = None
    internal_page_index: int | None = None


class DocumentLinkInspector(Protocol):
    """Read-only link inspection capability supplied by a concrete PDF adapter."""

    def inspect_links(self, document_path: str, page_index: int) -> tuple[DocumentLink, ...]:
        """Return links on one page without activating or opening destinations."""


__all__ = ["DocumentLink", "DocumentLinkInspector"]
