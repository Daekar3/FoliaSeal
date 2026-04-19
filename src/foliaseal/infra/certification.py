"""Certification and DocMDP inspection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.validation import read_certification_data
from pyhanko.sign.validation.pdf_embedded import MDPPerm


class CertificationInspectionError(ValueError):
    """Raised when certification metadata cannot be inspected safely."""


@dataclass(frozen=True)
class CertificationPolicyResult:
    """Structured classification of input PDF certification state."""

    docmdp_permission: str | None
    certification_restricted: bool
    restriction_reason: str | None = None


class PyHankoCertificationInspector:
    """Inspect certification state using pyHanko's PDF reader helpers."""

    def inspect(self, input_pdf_path: str) -> CertificationPolicyResult:
        return inspect_pdf_certification(input_pdf_path)


def inspect_pdf_certification(input_pdf_path: str) -> CertificationPolicyResult:
    """Inspect certification metadata from a PDF path."""
    path = Path(input_pdf_path)
    try:
        with path.open("rb") as handle:
            reader = PdfFileReader(handle)
            return inspect_pdf_certification_reader(reader)
    except CertificationInspectionError:
        raise
    except Exception as exc:  # pragma: no cover - defensive mapping for stable contracts.
        raise CertificationInspectionError(str(exc)) from exc


def inspect_pdf_certification_reader(reader: PdfFileReader) -> CertificationPolicyResult:
    """Inspect certification metadata from an open PDF reader."""
    try:
        certification = read_certification_data(reader)
    except Exception as exc:  # pragma: no cover - defensive mapping for stable contracts.
        raise CertificationInspectionError(str(exc)) from exc

    if certification is None:
        return CertificationPolicyResult(
            docmdp_permission=None,
            certification_restricted=False,
            restriction_reason=None,
        )

    permission = getattr(certification, "permission", None)
    permission_name = None
    if permission is not None:
        permission_name = getattr(permission, "name", None)
        if isinstance(permission_name, str):
            permission_name = permission_name.lower()
        else:
            permission_name = str(permission)

    if permission == MDPPerm.NO_CHANGES:
        return CertificationPolicyResult(
            docmdp_permission=permission_name,
            certification_restricted=True,
            restriction_reason=(
                "Certification-restricted PDF: DocMDP NO_CHANGES forbids signing."
            ),
        )

    if permission in {MDPPerm.FILL_FORMS, MDPPerm.ANNOTATE}:
        return CertificationPolicyResult(
            docmdp_permission=permission_name,
            certification_restricted=False,
            restriction_reason=None,
        )

    return CertificationPolicyResult(
        docmdp_permission=permission_name,
        certification_restricted=True,
        restriction_reason=(
            f"Unsupported certification permission {permission_name or permission!r}."
        ),
    )
