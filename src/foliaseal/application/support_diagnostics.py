"""Privacy-safe, bounded product support locations and diagnostics.

This module intentionally has no Qt or document/signing dependencies.  It is a
small boundary for support UI and must not be confused with evidence harness
diagnostics.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class SupportLocations:
    """Per-user FoliaSeal directories used by support surfaces."""

    config_dir: Path
    data_dir: Path
    logs_dir: Path

    @classmethod
    def for_environment(cls) -> SupportLocations:
        home = Path.home()
        config = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "FoliaSeal"
        data = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / "FoliaSeal"
        state = Path(os.environ.get("XDG_STATE_HOME", home / ".local/state")) / "FoliaSeal"
        return cls(config_dir=config, data_dir=data, logs_dir=state / "logs")

    def ensure_logs_dir(self) -> Path:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        return self.logs_dir


def _privacy_filter(detail: str, sensitive: Mapping[str, str]) -> str:
    filtered = str(detail)
    for key, value in sensitive.items():
        if value:
            filtered = filtered.replace(str(value), "[redacted]")
        filtered = filtered.replace(f"{key}=", f"{key}=[redacted]")
        filtered = filtered.replace(f"{key}: ", f"{key}: [redacted]")
    # These labels are never useful in a product support log, even when a
    # caller accidentally includes them in a free-form detail string.
    for key in (
        "password",
        "private_key",
        "private-key",
        "pdf_content",
        "selected_text",
        "reason",
        "location",
    ):
        filtered = re.sub(
            rf"({re.escape(key)}\s*[:=]\s*)([^,;\n]+)", r"\1[redacted]", filtered, flags=re.I
        )
    return filtered


class DiagnosticLogWriter:
    """Write privacy-filtered UTF-8 logs with deterministic bounded rotation."""

    def __init__(
        self,
        locations: SupportLocations | None = None,
        *,
        max_bytes: int = 256_000,
        backup_count: int = 2,
    ) -> None:
        if max_bytes <= 0 or backup_count < 0:
            raise ValueError("max_bytes must be positive and backup_count non-negative")
        self.locations = locations or SupportLocations.for_environment()
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    @property
    def active_path(self) -> Path:
        return self.locations.logs_dir / "foliaseal.log"

    def write(
        self,
        *,
        level: str,
        error_code: str,
        stage: str,
        detail: str,
        sensitive: Mapping[str, str] | None = None,
    ) -> Path:
        self.locations.ensure_logs_dir()
        message = _privacy_filter(detail, sensitive or {})
        line = f"{datetime.now(UTC).isoformat()} {level.upper()} {error_code} {stage}: {message}\n"
        encoded = line.encode("utf-8")
        if (
            self.active_path.exists()
            and self.active_path.stat().st_size + len(encoded) > self.max_bytes
        ):
            self._rotate()
        with self.active_path.open("ab") as stream:
            stream.write(encoded)
        return self.active_path

    def _rotate(self) -> None:
        if self.backup_count == 0:
            # Truncate the active file when retention is disabled.  Leaving it
            # in place would allow the next record to grow past max_bytes.
            self.active_path.write_bytes(b"")
            return
        for index in range(self.backup_count, 0, -1):
            source = self.locations.logs_dir / (
                "foliaseal.log" if index == 1 else f"foliaseal.log.{index - 1}"
            )
            target = self.locations.logs_dir / f"foliaseal.log.{index}"
            if source.exists():
                if target.exists():
                    target.unlink()
                source.replace(target)
