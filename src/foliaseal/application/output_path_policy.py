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
    if current_output_path is not None and Path(current_output_path).name:
        return Path(default_output_directory) / Path(current_output_path).name

    input_stem = Path(input_pdf_path).stem or "signed"
    directory = Path(default_output_directory)
    candidate = directory / f"{input_stem}-signed.pdf"
    suffix = 2
    while candidate.exists():
        candidate = directory / f"{input_stem}-signed-{suffix}.pdf"
        suffix += 1
    return candidate


def paths_refer_to_same_file(
    input_pdf_path: str | Path,
    output_pdf_path: str | Path,
) -> bool:
    """Return whether two user-provided paths resolve to the same intended file."""

    return Path(input_pdf_path).expanduser().resolve(strict=False) == Path(
        output_pdf_path
    ).expanduser().resolve(strict=False)
