"""Plain-language completion messages for GUI signing results."""

from __future__ import annotations

from pathlib import Path

from foliaseal.domain.models import SigningResult


def format_signing_completion_message(
    result: SigningResult,
    output_pdf_path: str | Path,
) -> str:
    """Return a compact post-sign completion message for users."""
    lines = [
        result.message,
        f"Saved to: {Path(output_pdf_path)}",
    ]

    if result.standards_summary:
        lines.append(f"Verified locally: {result.standards_summary}")
    else:
        lines.append("Verified locally: signed output was created and checked.")

    if result.timestamp_present is True:
        lines.append("Timestamp token is present.")
        if (
            result.timestamp_cryptographically_valid is False
            or result.tsa_chain_trusted is False
        ):
            detail = result.timestamp_validation_error or "timestamp trust failed."
            lines.append(f"Timestamp trust needs attention: {detail}")
        elif (
            result.timestamp_cryptographically_valid is None
            and result.tsa_chain_trusted is None
        ):
            lines.append("Timestamp trust was not evaluated locally.")
    elif result.timestamp_present is False:
        lines.append("No timestamp token was found.")

    if result.certification_restricted or result.restriction_reason:
        detail = result.restriction_reason or "document certification restricts changes."
        lines.append(f"Adding another signature may be blocked: {detail}")

    return "\n".join(line for line in lines if line.strip())
