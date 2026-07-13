"""Bundled toolbar/menu icon paths for FoliaSeal."""

from __future__ import annotations

from pathlib import Path


def icon_path(name: str) -> str:
    """Return the absolute path to a bundled SVG icon."""

    return str(Path(__file__).resolve().parent / "icons" / name)
