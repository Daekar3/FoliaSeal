"""Neutral boundary for visible-signature text measurement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from foliaseal.domain.models import SignatureTextStyle

if TYPE_CHECKING:
    from foliaseal.application.visible_signature_layout import TextMetrics


@dataclass(frozen=True)
class PreparedTextBox:
    """One atomic text measurement plus an adapter-owned style token."""

    metrics: TextMetrics
    render_style: object


class SignatureTextBoxEngine(Protocol):
    """Port for measuring text and preparing one matching render style."""

    def prepare(self, text: str, text_style: SignatureTextStyle) -> PreparedTextBox:
        """Return neutral metrics and the matching adapter style token."""
