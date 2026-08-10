"""Pure safety decisions for PDF destinations and source changes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LinkDecisionKind(StrEnum):
    """The safe action a later viewer surface may offer for a destination."""

    ALLOW_INTERNAL = "allow_internal"
    CONFIRM_EXTERNAL = "confirm_external"
    BLOCK = "block"


class SourceChangeStatus(StrEnum):
    """The observed relationship between the open source and its current path."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    MISSING = "missing"


class SourceChangeAction(StrEnum):
    """The condition-only action a future banner may present."""

    NONE = "none"
    RELOAD_OR_IGNORE = "reload_or_ignore"
    LOCATE_OR_CLOSE = "locate_or_close"


@dataclass(frozen=True)
class LinkDecision:
    """A non-executable destination decision."""

    kind: LinkDecisionKind
    destination: str
    page_index: int | None = None
    reason: str | None = None
    launcher: None = None


@dataclass(frozen=True)
class SourceChangeDecision:
    """A pure source-change projection; it never reloads or mutates a workspace."""

    status: SourceChangeStatus
    action: SourceChangeAction


def classify_link_destination(
    raw_destination: str | None,
    *,
    internal_page_index: int | None = None,
) -> LinkDecision:
    """Classify a PDF destination without opening it or performing I/O."""
    destination = (raw_destination or "").strip()
    if (
        internal_page_index is not None
        and internal_page_index >= 0
        and not _has_scheme(destination)
    ):
        return LinkDecision(
            kind=LinkDecisionKind.ALLOW_INTERNAL,
            destination=destination,
            page_index=internal_page_index,
        )
    scheme = _scheme(destination)
    if scheme in {"http", "https", "mailto"}:
        return LinkDecision(
            kind=LinkDecisionKind.CONFIRM_EXTERNAL,
            destination=destination,
            reason="External destinations require confirmation before opening.",
        )
    return LinkDecision(
        kind=LinkDecisionKind.BLOCK,
        destination=destination,
        reason="This destination type is blocked by the document safety policy.",
    )


def source_change_decision(
    *,
    exists: bool,
    observed_fingerprint: tuple[object, ...] | None,
    current_fingerprint: tuple[object, ...] | None,
) -> SourceChangeDecision:
    """Project source presence and identity into a future banner decision."""
    if not exists:
        return SourceChangeDecision(
            status=SourceChangeStatus.MISSING,
            action=SourceChangeAction.LOCATE_OR_CLOSE,
        )
    if observed_fingerprint == current_fingerprint:
        return SourceChangeDecision(
            status=SourceChangeStatus.UNCHANGED,
            action=SourceChangeAction.NONE,
        )
    return SourceChangeDecision(
        status=SourceChangeStatus.CHANGED,
        action=SourceChangeAction.RELOAD_OR_IGNORE,
    )


def _has_scheme(destination: str) -> bool:
    return bool(_scheme(destination))


def _scheme(destination: str) -> str:
    separator = destination.find(":")
    if separator <= 0:
        return ""
    candidate = destination[:separator].lower()
    normalized = candidate.replace("+", "").replace("-", "").replace(".", "")
    return candidate if normalized.isalnum() else ""


__all__ = [
    "LinkDecision",
    "LinkDecisionKind",
    "SourceChangeAction",
    "SourceChangeDecision",
    "SourceChangeStatus",
    "classify_link_destination",
    "source_change_decision",
]
