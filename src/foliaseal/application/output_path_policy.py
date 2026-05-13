"""Path policy helpers for signing output files."""

from __future__ import annotations

from pathlib import Path


def suggest_signed_output_path(
    *,
    input_pdf_path: str | Path,
    default_output_directory: str | Path,
    current_output_path: str | Path | None = None,
) -> Path:
    """Return the suggested destination for a signed PDF."""
    filename = ""
    if current_output_path is not None:
        filename = Path(current_output_path).name
    if not filename:
        input_stem = Path(input_pdf_path).stem or "signed"
        filename = f"{input_stem}-signed.pdf"
    return Path(default_output_directory) / filename
