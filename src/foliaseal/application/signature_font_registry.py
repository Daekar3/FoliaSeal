"""Canonical bundled font mapping for visible-signature rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SignatureFontFace:
    """Exact bundled face used for a visible-signature text request."""

    requested_family: str
    canonical_family: str
    preview_family_name: str
    font_file: Path
    bold: bool
    italic: bool


_FONT_ROOT = Path(__file__).resolve().parent.parent / "resources" / "fonts"


def bundled_font_root() -> Path:
    """Return the packaged font asset directory."""

    return _FONT_ROOT


def preview_font_family_supported(font_family: str) -> bool:
    """Return whether the requested preview family maps directly to bundled assets."""

    return _canonical_family(font_family) in {
        "Sans Serif",
        "Serif",
        "Monospace",
    }


def resolve_signature_font_face(
    font_family: str,
    *,
    bold: bool = False,
    italic: bool = False,
) -> SignatureFontFace:
    """Resolve the requested UI family/style to an exact bundled font asset."""

    canonical_family = _canonical_family(font_family)
    face_name, preview_family_name = _face_name_for_request(
        canonical_family,
        bold=bold,
        italic=italic,
    )
    font_path = bundled_font_root() / face_name
    if not font_path.exists():
        raise ValueError(
            f"Bundled font asset '{face_name}' for '{canonical_family}' is missing."
        )
    return SignatureFontFace(
        requested_family=font_family,
        canonical_family=canonical_family,
        preview_family_name=preview_family_name,
        font_file=font_path,
        bold=bold,
        italic=italic,
    )


def validate_signature_font_request(
    font_family: str,
    *,
    bold: bool = False,
    italic: bool = False,
) -> str | None:
    """Return a blocking validation message when the font/style request is unsupported."""

    try:
        resolve_signature_font_face(font_family, bold=bold, italic=italic)
    except ValueError as exc:
        return str(exc)
    return None


def _canonical_family(font_family: str) -> str:
    normalized = font_family.strip().lower()
    if not normalized:
        return "Sans Serif"
    if any(
        token in normalized
        for token in (
            "sans serif",
            "sans-serif",
            "source sans",
            "source sans 3",
            "helvetica",
            "arial",
            "noto sans",
        )
    ):
        return "Sans Serif"
    if any(token in normalized for token in ("courier", "mono", "code", "dejavu sans mono")):
        return "Monospace"
    if any(
        token in normalized
        for token in ("cursive", "script", "dancing script", "segoe script")
    ):
        return "Cursive"
    if any(
        token in normalized
        for token in ("fantasy", "display", "decor", "noto serif display")
    ):
        return "Fantasy"
    if any(
        token in normalized
        for token in ("times", "serif", "georgia", "noto serif")
    ):
        return "Serif"
    return "Sans Serif"


def _face_name_for_request(
    canonical_family: str,
    *,
    bold: bool,
    italic: bool,
) -> tuple[str, str]:
    if canonical_family == "Sans Serif":
        if bold and italic:
            return ("NotoSans-BoldItalic.ttf", "Noto Sans")
        if bold:
            return ("NotoSans-Bold.ttf", "Noto Sans")
        if italic:
            return ("NotoSans-Italic.ttf", "Noto Sans")
        return ("NotoSans-Regular.ttf", "Noto Sans")
    if canonical_family == "Serif":
        if bold and italic:
            return ("NotoSerif-BoldItalic.ttf", "Noto Serif")
        if bold:
            return ("NotoSerif-Bold.ttf", "Noto Serif")
        if italic:
            return ("NotoSerif-Italic.ttf", "Noto Serif")
        return ("NotoSerif-Regular.ttf", "Noto Serif")
    if canonical_family == "Monospace":
        if bold and italic:
            return ("DejaVuSansMono-BoldOblique.ttf", "DejaVu Sans Mono")
        if bold:
            return ("DejaVuSansMono-Bold.ttf", "DejaVu Sans Mono")
        if italic:
            return ("DejaVuSansMono-Oblique.ttf", "DejaVu Sans Mono")
        return ("DejaVuSansMono.ttf", "DejaVu Sans Mono")
    raise ValueError(f"Unsupported signature font family '{canonical_family}'.")
