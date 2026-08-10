"""Qt-free final signing confirmation summary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from foliaseal.application.signing_draft_contracts import (
    SigningDraftPreview,
    SigningDraftValidationSeverity,
)


@dataclass(frozen=True)
class SigningConfirmationSummary:
    """Immutable, secret-free facts shown before a signing transaction."""

    preset_name: str
    certificate_name: str
    output_path: str
    page_label: str
    field_label: str
    signing_time: datetime | None
    caveats: tuple[str, ...] = ()

    @classmethod
    def from_preview(
        cls,
        *,
        preview: SigningDraftPreview,
        preset_name: str,
        certificate_name: str,
        output_path: str,
        signing_time: datetime | None,
    ) -> SigningConfirmationSummary:
        page_label = (
            f"Page {preview.page_index + 1}" if preview.page_index is not None else "Not applicable"
        )
        field_label = (
            "New visible signature field"
            if preview.signature_rect is not None
            else "Invisible signature field"
        )
        caveats = tuple(
            issue.message
            for issue in preview.issues
            if issue.severity is SigningDraftValidationSeverity.WARNING
        )
        return cls(
            preset_name=preset_name,
            certificate_name=certificate_name,
            output_path=output_path,
            page_label=page_label,
            field_label=field_label,
            signing_time=signing_time,
            caveats=caveats,
        )

    def as_message(self) -> str:
        """Render a concise review message without secrets or private material."""
        signing_time = (
            self.signing_time.isoformat(timespec="seconds")
            if self.signing_time is not None
            else "Resolved when signing starts"
        )
        caveat_lines = "\n".join(f"- {caveat}" for caveat in self.caveats) or "- None"
        return (
            "Review the final signing summary.\n\n"
            f"Preset: {self.preset_name}\n"
            f"Certificate: {self.certificate_name}\n"
            f"Output: {self.output_path}\n"
            f"Page: {self.page_label.removeprefix('Page ')}\n"
            f"Field: {self.field_label}\n"
            f"Signing time: {signing_time}\n\n"
            f"Caveats:\n{caveat_lines}\n\n"
            "Sign and save creates the signed PDF after verification. Cancel leaves the signing "
            "request unsubmitted and preserves the selected draft and output path."
        )


__all__ = ["SigningConfirmationSummary"]
