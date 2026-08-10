"""Application-owned source identity monitoring for readiness decisions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from foliaseal.application.document_safety import (
    SourceChangeDecision,
    source_change_decision,
)

SourceFingerprint = tuple[int, int, int, int]


def fingerprint_source(path: str | Path) -> SourceFingerprint | None:
    """Return a stable local identity/size/time fingerprint without reading PDF bytes."""
    try:
        stat_result = os.stat(path)
    except OSError:
        return None
    return (
        int(stat_result.st_dev),
        int(stat_result.st_ino),
        int(stat_result.st_size),
        int(stat_result.st_mtime_ns),
    )


@dataclass
class DocumentSourceMonitor:
    """Compare a mounted document source with the identity observed at open time."""

    source_path: Path
    observed_fingerprint: SourceFingerprint | None

    @classmethod
    def for_path(cls, source_path: str | Path) -> DocumentSourceMonitor:
        path = Path(source_path)
        return cls(path, fingerprint_source(path))

    def decision(self) -> SourceChangeDecision:
        """Return the current source-change decision without reloading or mutating a workspace."""
        current = fingerprint_source(self.source_path)
        return source_change_decision(
            exists=current is not None,
            observed_fingerprint=self.observed_fingerprint,
            current_fingerprint=current,
        )

    def acknowledge_current_source(self) -> SourceChangeDecision:
        """Record the current source identity after an owning reload/ignore operation."""
        self.observed_fingerprint = fingerprint_source(self.source_path)
        return self.decision()


__all__ = ["DocumentSourceMonitor", "SourceFingerprint", "fingerprint_source"]
