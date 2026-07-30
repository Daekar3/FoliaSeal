"""Artifact boundary for Phase 3 matrix directories and summaries."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


class Phase3MatrixArtifactPort(Protocol):
    """Prepare one matrix directory and publish its stable summary JSON."""

    def prepare(self, artifacts_dir: str) -> Path:
        """Create or reuse the matrix artifact directory."""

    def write_summary(self, artifacts_dir: Path, summary: Mapping[str, Any]) -> str:
        """Write and return the summary JSON path."""


class FilesystemPhase3MatrixArtifactPort:
    """Filesystem adapter preserving the existing summary serialization."""

    def prepare(self, artifacts_dir: str) -> Path:
        root = Path(artifacts_dir)
        root.mkdir(parents=True, exist_ok=True)
        return root

    def write_summary(self, artifacts_dir: Path, summary: Mapping[str, Any]) -> str:
        summary_path = artifacts_dir / "summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return str(summary_path)


class MemoryPhase3MatrixArtifactPort:
    """In-memory artifact substitute for deterministic orchestration tests."""

    def __init__(self) -> None:
        self.prepared: list[str] = []
        self.summaries: dict[str, dict[str, Any]] = {}

    def prepare(self, artifacts_dir: str) -> Path:
        self.prepared.append(artifacts_dir)
        return Path(artifacts_dir)

    def write_summary(self, artifacts_dir: Path, summary: Mapping[str, Any]) -> str:
        path = str(artifacts_dir / "summary.json")
        self.summaries[path] = dict(summary)
        return path
