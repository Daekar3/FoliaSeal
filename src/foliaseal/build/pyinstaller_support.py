"""PyInstaller support helpers for FoliaSeal bundles."""

from pathlib import Path

_FONT_DESTINATION = "foliaseal/resources/fonts"


def collect_runtime_assets(project_root: Path | None = None) -> list[tuple[str, str]]:
    """Return PyInstaller data tuples for non-Python runtime assets."""

    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[3]
    font_root = root / "src" / "foliaseal" / "resources" / "fonts"
    return [(str(font_path), _FONT_DESTINATION) for font_path in sorted(font_root.glob("*.ttf"))]
