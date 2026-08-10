"""Typed, UI-only preferences projected from the AppSettings ``ui`` mapping."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

DEFAULT_RAIL_WIDTH = 320
MIN_RAIL_WIDTH = 280
MAX_RAIL_WIDTH = 640
MIN_LIBRARY_WIDTH = 1000
MIN_LIBRARY_HEIGHT = 650
MIN_LIBRARY_COLUMN_WIDTH = 120
MAX_LIBRARY_COLUMN_WIDTH = 1600
DEFAULT_LIBRARY_SPLITTER_SIZES = (180, 320, 560)


def normalize_rail_width(value: object) -> int:
    """Return a safe remembered signing-rail width in logical pixels."""

    if type(value) is not int:
        return DEFAULT_RAIL_WIDTH
    return max(MIN_RAIL_WIDTH, min(MAX_RAIL_WIDTH, value))


def normalize_library_splitter_sizes(value: object) -> tuple[int, int, int]:
    """Return three safe remembered Signature Library column widths."""

    if not isinstance(value, (list, tuple)) or len(value) != 3:
        return DEFAULT_LIBRARY_SPLITTER_SIZES
    if any(type(item) is not int for item in value):
        return DEFAULT_LIBRARY_SPLITTER_SIZES
    normalized = [
        max(MIN_LIBRARY_COLUMN_WIDTH, min(MAX_LIBRARY_COLUMN_WIDTH, item)) for item in value
    ]
    return normalized[0], normalized[1], normalized[2]


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
class LibraryGeometry:
    """Validated JSON-safe geometry for the modeless Signature Library."""

    MIN_WIDTH = MIN_LIBRARY_WIDTH
    MIN_HEIGHT = MIN_LIBRARY_HEIGHT

    x: int
    y: int
    width: int
    height: int
    maximized: bool = False

    def __post_init__(self) -> None:
        if any(type(value) is not int for value in (self.x, self.y, self.width, self.height)):
            raise ValueError("Library geometry coordinates and dimensions must be integers")
        if self.width < MIN_LIBRARY_WIDTH or self.height < MIN_LIBRARY_HEIGHT:
            raise ValueError("Library geometry is smaller than the minimum")
        if type(self.maximized) is not bool:
            raise ValueError("Library maximized state must be a boolean")

    @classmethod
    def from_mapping(cls, payload: object) -> LibraryGeometry | None:
        """Project valid persisted Library geometry, or return ``None`` for bad data."""

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
    library_geometry: LibraryGeometry | None = None
    library_splitter_sizes: tuple[int, int, int] = DEFAULT_LIBRARY_SPLITTER_SIZES
    library_last_catalog: str = "presets"
    library_sort: LibrarySortOrder = LibrarySortOrder.NAME_ASCENDING
    rail_width: int = DEFAULT_RAIL_WIDTH

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> AppUiSettings:
        """Project the known UI preferences without dropping future keys."""

        return cls(
            appearance_mode=AppearanceMode.from_value(payload.get("appearance_mode")),
            main_window_geometry=MainWindowGeometry.from_mapping(
                payload.get("main_window_geometry")
            ),
            library_geometry=LibraryGeometry.from_mapping(payload.get("library_geometry")),
            library_splitter_sizes=normalize_library_splitter_sizes(
                payload.get("library_splitter_sizes", DEFAULT_LIBRARY_SPLITTER_SIZES)
            ),
            library_last_catalog=(
                str(payload.get("library_last_catalog", "presets")).strip().lower()
                or "presets"
            ),
            library_sort=LibrarySortOrder.from_value(payload.get("library_sort")),
            rail_width=normalize_rail_width(payload.get("rail_width", DEFAULT_RAIL_WIDTH)),
        )

    def to_mapping(self, existing: dict[str, Any] | None = None) -> dict[str, Any]:
        """Merge known typed preferences into an existing UI mapping."""

        mapping = dict(existing or {})
        mapping["appearance_mode"] = self.appearance_mode.value
        if self.main_window_geometry is not None:
            mapping["main_window_geometry"] = self.main_window_geometry.to_mapping()
        if self.library_geometry is not None:
            mapping["library_geometry"] = self.library_geometry.to_mapping()
        else:
            mapping.pop("library_geometry", None)
        if (
            "library_splitter_sizes" in mapping
            or self.library_splitter_sizes != DEFAULT_LIBRARY_SPLITTER_SIZES
        ):
            mapping["library_splitter_sizes"] = list(
                normalize_library_splitter_sizes(self.library_splitter_sizes)
            )
        if "library_last_catalog" in mapping or self.library_last_catalog != "presets":
            mapping["library_last_catalog"] = self.library_last_catalog
        if "library_sort" in mapping or self.library_sort is not LibrarySortOrder.NAME_ASCENDING:
            mapping["library_sort"] = self.library_sort.value
        if "rail_width" in mapping or self.rail_width != DEFAULT_RAIL_WIDTH:
            mapping["rail_width"] = normalize_rail_width(self.rail_width)
        return mapping
