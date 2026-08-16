"""PyInstaller support helpers for FoliaSeal bundles."""

from pathlib import Path

_FONT_DESTINATION = "foliaseal/resources/fonts"
_HELP_DESTINATION = "foliaseal/resources/help"
_ICON_DESTINATION = "foliaseal/resources/icons"


def collect_runtime_assets(project_root: Path | None = None) -> list[tuple[str, str]]:
    """Return PyInstaller data tuples for non-Python runtime assets."""

    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[3]
    font_root = root / "src" / "foliaseal" / "resources" / "fonts"
    help_root = root / "src" / "foliaseal" / "resources" / "help"
    icon_root = root / "src" / "foliaseal" / "resources" / "icons"
    assets = [
        (str(font_path), _FONT_DESTINATION) for font_path in sorted(font_root.glob("*.ttf"))
    ]
    assets.extend(
        (str(help_path), _HELP_DESTINATION)
        for help_path in sorted(help_root.glob("*.md"))
    )
    index_path = help_root / "index.json"
    if index_path.is_file():
        assets.append((str(index_path), _HELP_DESTINATION))
    assets.extend(
        (str(icon_path), _ICON_DESTINATION)
        for icon_path in sorted(icon_root.glob("*.svg"))
    )
    return assets
