"""Typed presentation results for safe external-link confirmation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ExternalLinkOutcome(StrEnum):
    """Observable result of one external-link request."""

    OPENED = "opened"
    CANCELED = "canceled"
    DEFERRED = "deferred"
    REPLACED = "replaced"
    FAILED = "failed"
    IGNORED = "ignored"


@dataclass(frozen=True)
class ExternalLinkRequestResult:
    """Non-executable result returned by the presentation confirmation seam."""

    outcome: ExternalLinkOutcome
    destination: str
    launch_destination: str | None = None
    launched: bool = False


__all__ = ["ExternalLinkOutcome", "ExternalLinkRequestResult"]
