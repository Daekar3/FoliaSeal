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


class LibrarySortOrder(StrEnum):
    """Persistent Signature Library ordering choices."""

    NAME_ASCENDING = "name_ascending"
    NAME_DESCENDING = "name_descending"
    EXPIRATION_SOONEST = "expiration_soonest"

    @classmethod
    def from_value(cls, value: object) -> LibrarySortOrder:
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return cls.NAME_ASCENDING


@dataclass(frozen=True)
class MainWindowGeometry:
    """Validated JSON-safe geometry for the main application window."""

    MIN_WIDTH = 1100
    MIN_HEIGHT = 700

    x: int
    y: int
    width: int
    height: int
    maximized: bool = False

    def __post_init__(self) -> None:
        if any(type(value) is not int for value in (self.x, self.y, self.width, self.height)):
            raise ValueError("main-window geometry coordinates and dimensions must be integers")
        if self.width < self.MIN_WIDTH or self.height < self.MIN_HEIGHT:
            raise ValueError("main-window geometry is smaller than the application minimum")
        if type(self.maximized) is not bool:
            raise ValueError("main-window maximized state must be a boolean")

    @classmethod
    def from_mapping(cls, payload: object) -> MainWindowGeometry | None:
        """Project a valid persisted geometry, or return ``None`` for legacy/bad data."""

        if not isinstance(payload, dict):
            return None
        try:
            return cls(
                x=payload["x"],
                y=payload["y"],
                width=payload["width"],
                height=payload["height"],
                maximized=payload.get("maximized", False),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def to_mapping(self) -> dict[str, int | bool]:
        """Return the stable persisted representation."""

        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "maximized": self.maximized,
        }


@dataclass(frozen=True)
class AppUiSettings:
    """Typed UI preferences owned by :class:`AppSettings`."""

    appearance_mode: AppearanceMode = AppearanceMode.SYSTEM
    main_window_geometry: MainWindowGeometry | None = None
    library_last_catalog: str = "presets"
    library_sort: LibrarySortOrder = LibrarySortOrder.NAME_ASCENDING

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> AppUiSettings:
        """Project the known UI preferences without dropping future keys."""

        return cls(
            appearance_mode=AppearanceMode.from_value(payload.get("appearance_mode")),
            main_window_geometry=MainWindowGeometry.from_mapping(
                payload.get("main_window_geometry")
            ),
            library_last_catalog=(
                str(payload.get("library_last_catalog", "presets")).strip().lower()
                or "presets"
            ),
            library_sort=LibrarySortOrder.from_value(payload.get("library_sort")),
        )

    def to_mapping(self, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        """Merge known typed preferences into an existing UI mapping."""

        mapping = dict(existing or {})
        mapping["appearance_mode"] = self.appearance_mode.value
        if self.main_window_geometry is not None:
            mapping["main_window_geometry"] = self.main_window_geometry.to_mapping()
        if "library_last_catalog" in mapping or self.library_last_catalog != "presets":
            mapping["library_last_catalog"] = self.library_last_catalog
        if "library_sort" in mapping or self.library_sort is not LibrarySortOrder.NAME_ASCENDING:
            mapping["library_sort"] = self.library_sort.value
        return mapping
