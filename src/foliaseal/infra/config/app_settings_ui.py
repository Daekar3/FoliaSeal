"""Typed, UI-only preferences projected from the AppSettings ``ui`` mapping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AppearanceMode(StrEnum):
    """Supported application-chrome appearance modes."""

    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"

    @classmethod
    def from_value(cls, value: object) -> AppearanceMode:
        """Return a supported mode, falling back safely for old/invalid values."""

        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return cls.SYSTEM


@dataclass(frozen=True)
class AppUiSettings:
    """Typed UI preferences owned by :class:`AppSettings`."""

    appearance_mode: AppearanceMode = AppearanceMode.SYSTEM

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> AppUiSettings:
        """Project the known UI preferences without dropping future keys."""

        return cls(appearance_mode=AppearanceMode.from_value(payload.get("appearance_mode")))

    def to_mapping(self, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        """Merge known typed preferences into an existing UI mapping."""

        mapping = dict(existing or {})
        mapping["appearance_mode"] = self.appearance_mode.value
        return mapping
