"""Pure safety decisions for PDF destinations and source changes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class LinkDecisionKind(StrEnum):
    """The safe action a later viewer surface may offer for a destination."""

    ALLOW_INTERNAL = "allow_internal"
    CONFIRM_EXTERNAL = "confirm_external"
    BLOCK = "block"


class LinkInteractionMode(StrEnum):
    """Viewer mode allowed to activate document links."""

    PAN = "pan"
    SELECT_TEXT = "select_text"
    PLACE_SIGNATURE = "place_signature"


class SourceChangeStatus(StrEnum):
    """The observed relationship between the open source and its current path."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    MISSING = "missing"
    UNKNOWN = "unknown"


class SourceChangeAction(StrEnum):
    """The condition-only action a future banner may present."""

    NONE = "none"
    RELOAD_OR_IGNORE = "reload_or_ignore"
    LOCATE_OR_CLOSE = "locate_or_close"
    REVIEW_REQUIRED = "review_required"


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
    interaction_mode: LinkInteractionMode = LinkInteractionMode.PAN,
) -> LinkDecision:
    """Classify a PDF destination without opening it or performing I/O."""
    destination = _display_destination(raw_destination)
    has_control = raw_destination is not None and any(
        _is_control_character(character) for character in raw_destination
    )
    if interaction_mode is not LinkInteractionMode.PAN:
        return LinkDecision(
            kind=LinkDecisionKind.BLOCK,
            destination=destination,
            reason="Links activate only in Pan mode.",
        )
    if (
        internal_page_index is not None
        and internal_page_index >= 0
    ):
        if raw_destination is not None and (
            not destination
            or destination.startswith("//")
            or ("://" in destination and not _has_scheme(destination))
            or has_control
        ):
            return LinkDecision(
                kind=LinkDecisionKind.BLOCK,
                destination=destination,
                reason="The internal destination is malformed or unsafe.",
            )
        if raw_destination is None or not _has_scheme(destination):
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
    if observed_fingerprint is None or current_fingerprint is None:
        return SourceChangeDecision(
            status=SourceChangeStatus.UNKNOWN,
            action=SourceChangeAction.REVIEW_REQUIRED,
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
    match = re.match(r"^([A-Za-z][A-Za-z0-9+.-]*):", destination)
    if match is None:
        return ""
    return match.group(1).lower()


def _display_destination(raw_destination: str | None) -> str:
    if raw_destination is None:
        return ""
    normalized = "".join(
        character if not _is_control_character(character) else " "
        for character in raw_destination.strip()
    )
    normalized = " ".join(normalized.split())
    return normalized[:512]


def _is_control_character(character: str) -> bool:
    codepoint = ord(character)
    return codepoint < 32 or 0x7F <= codepoint <= 0x9F


__all__ = [
    "LinkDecision",
    "LinkDecisionKind",
    "LinkInteractionMode",
    "SourceChangeAction",
    "SourceChangeDecision",
    "SourceChangeStatus",
    "classify_link_destination",
    "source_change_decision",
]
