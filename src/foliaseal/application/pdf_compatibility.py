"""Phase 1 PDF compatibility policy checks and standards reporting."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class PdfCompatibilityError(ValueError):
    """Raised when an input/output policy rule is violated."""


@dataclass(frozen=True)
class PdfCompatibilityProfile:
    """Policy rules for opening/signing PDFs in the v1 signing flow."""

    min_open_version: Decimal = Decimal("1.4")
    max_open_version: Decimal = Decimal("2.0")
    preserve_input_version: bool = True

    def ensure_open_version_supported(self, input_pdf_version: str) -> None:
        """Enforce the accepted open range from the feasibility requirements."""
        parsed = self._parse_pdf_version(input_pdf_version)
        if parsed < self.min_open_version or parsed > self.max_open_version:
            raise PdfCompatibilityError(
                f"Unsupported PDF version '{input_pdf_version}'. "
                f"Supported range is {self.min_open_version} to {self.max_open_version}."
            )

    def ensure_output_version_policy(self, input_pdf_version: str, output_pdf_version: str) -> None:
        """Ensure version preservation rules in signing flow."""
        self.ensure_open_version_supported(input_pdf_version)
        self.ensure_open_version_supported(output_pdf_version)
        if self.preserve_input_version and input_pdf_version != output_pdf_version:
            raise PdfCompatibilityError(
                "Signing flow must preserve input PDF version in incremental output. "
                f"Input={input_pdf_version}, Output={output_pdf_version}."
            )

    def build_standards_summary(
        self,
        *,
        input_pdf_version: str,
        output_pdf_version: str,
        signature_subfilter: str,
        timestamp_present: bool,
    ) -> str:
        """Generate a user-visible standards summary string."""
        self.ensure_output_version_policy(input_pdf_version, output_pdf_version)
        timestamp_label = "timestamped" if timestamp_present else "without timestamp"
        return (
            f"Opened as PDF {input_pdf_version}, saved incrementally as PDF {output_pdf_version}, "
            f"subfilter={signature_subfilter}, {timestamp_label}."
        )

    @staticmethod
    def _parse_pdf_version(version: str) -> Decimal:
        try:
            parsed = Decimal(version)
        except InvalidOperation as exc:
            raise PdfCompatibilityError(f"Invalid PDF version string '{version}'.") from exc

        if not parsed.is_finite():
            raise PdfCompatibilityError(f"Invalid PDF version string '{version}'.")
        return parsed
