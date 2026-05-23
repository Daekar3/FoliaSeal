"""Read-only document signature review helpers for the GUI shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext

from foliaseal.infra.certification import inspect_pdf_certification_reader


@dataclass(frozen=True)
class DocumentReviewSummary:
    """Plain-language review state for the currently opened PDF."""

    headline: str
    detail: str
    signature_count: int | None
    signature_items: tuple[DocumentSignatureReviewItem, ...] = ()
    signer_subject: str | None = None
    docmdp_permission: str | None = None
    certification_restricted: bool = False
    restriction_reason: str | None = None
    cryptographic_validation_passed: bool | None = None
    inspection_error: str | None = None


@dataclass(frozen=True)
class DocumentSignatureReviewItem:
    """Plain-language review state for one embedded signature."""

    label: str
    signer_subject: str | None
    cryptographic_validation_passed: bool | None
    detail: str
    drill_in_detail: str = ""


class DocumentReviewInspector(Protocol):
    """Read-only inspector used by the signing shell."""

    def inspect(self, input_pdf_path: str) -> DocumentReviewSummary:
        """Return a plain-language review summary for the PDF path."""


def summarize_document_review(
    *,
    signature_count: int | None,
    signature_items: tuple[DocumentSignatureReviewItem, ...] = (),
    signer_subject: str | None = None,
    docmdp_permission: str | None = None,
    certification_restricted: bool = False,
    restriction_reason: str | None = None,
    cryptographic_validation_passed: bool | None = None,
    inspection_error: str | None = None,
) -> DocumentReviewSummary:
    """Build a plain-language summary from read-only signature facts."""

    if inspection_error:
        return DocumentReviewSummary(
            headline="Review unavailable",
            detail=f"Current PDF could not be inspected: {inspection_error}",
            signature_count=signature_count,
            signature_items=signature_items,
            signer_subject=signer_subject,
            docmdp_permission=docmdp_permission,
            certification_restricted=certification_restricted,
            restriction_reason=restriction_reason,
            cryptographic_validation_passed=cryptographic_validation_passed,
            inspection_error=inspection_error,
        )

    if signature_count is None:
        return DocumentReviewSummary(
            headline="Review unavailable",
            detail="Current PDF could not be inspected.",
            signature_count=None,
            signature_items=signature_items,
            signer_subject=signer_subject,
            docmdp_permission=docmdp_permission,
            certification_restricted=certification_restricted,
            restriction_reason=restriction_reason,
            cryptographic_validation_passed=cryptographic_validation_passed,
            inspection_error="Current PDF could not be inspected.",
        )

    if signature_count == 0:
        lines = ["This PDF does not currently contain embedded signatures."]
        if certification_restricted or restriction_reason:
            lines.append(
                "Adding a signature may be blocked: "
                f"{restriction_reason or 'document certification restricts changes.'}"
            )
        else:
            lines.append("You can place and sign a new visible approval signature.")
        return DocumentReviewSummary(
            headline="No signatures found",
            detail=" ".join(lines),
            signature_count=0,
            signature_items=signature_items,
            docmdp_permission=docmdp_permission,
            certification_restricted=certification_restricted,
            restriction_reason=restriction_reason,
            cryptographic_validation_passed=cryptographic_validation_passed,
        )

    lines = [f"Found {signature_count} embedded signature{'s' if signature_count != 1 else ''}."]
    if signer_subject:
        lines.append(f"Latest signer: {signer_subject}.")
    if cryptographic_validation_passed is True:
        lines.append("Latest signature verified locally.")
    elif cryptographic_validation_passed is False:
        lines.append("Latest signature needs attention: local verification failed.")
    else:
        lines.append("Latest signature validity was not evaluated locally.")
    lines.append(
        _certification_guidance(
            docmdp_permission=docmdp_permission,
            certification_restricted=certification_restricted,
            restriction_reason=restriction_reason,
        )
    )
    headline = "Signature review"
    if certification_restricted or restriction_reason:
        headline = "Signature review: restricted"
    return DocumentReviewSummary(
        headline=headline,
        detail=" ".join(lines),
        signature_count=signature_count,
        signature_items=signature_items,
        signer_subject=signer_subject,
        docmdp_permission=docmdp_permission,
        certification_restricted=certification_restricted,
        restriction_reason=restriction_reason,
        cryptographic_validation_passed=cryptographic_validation_passed,
    )


class PyHankoDocumentReviewInspector:
    """Inspect the current PDF for embedded signatures and certification state."""

    def inspect(self, input_pdf_path: str) -> DocumentReviewSummary:
        path = Path(input_pdf_path)
        if not path.exists():
            return summarize_document_review(
                signature_count=None,
                inspection_error="file not found.",
            )

        try:
            with path.open("rb") as handle:
                reader = PdfFileReader(handle)
                embedded_signatures = list(reader.embedded_signatures)
                certification = inspect_pdf_certification_reader(reader)
                if not embedded_signatures:
                    return summarize_document_review(
                        signature_count=0,
                        signature_items=(),
                        docmdp_permission=certification.docmdp_permission,
                        certification_restricted=certification.certification_restricted,
                        restriction_reason=certification.restriction_reason,
                    )

                signature_items = tuple(
                    _signature_review_item(
                        signature,
                        index=index,
                        latest_index=len(embedded_signatures) - 1,
                        docmdp_permission=certification.docmdp_permission,
                        certification_restricted=certification.certification_restricted,
                        restriction_reason=certification.restriction_reason,
                    )
                    for index, signature in enumerate(embedded_signatures)
                )
                signature = embedded_signatures[-1]
                signer_subject = _signer_subject(signature)
                cryptographic_validation_passed = _verify_signature_locally(signature)
                return summarize_document_review(
                    signature_count=len(embedded_signatures),
                    signature_items=signature_items,
                    signer_subject=signer_subject,
                    docmdp_permission=certification.docmdp_permission,
                    certification_restricted=certification.certification_restricted,
                    restriction_reason=certification.restriction_reason,
                    cryptographic_validation_passed=cryptographic_validation_passed,
                )
        except Exception as exc:  # pragma: no cover - defensive stable contract
            return summarize_document_review(
                signature_count=None,
                inspection_error=str(exc),
            )


def _signer_subject(signature: object) -> str | None:
    signer_cert = getattr(signature, "signer_cert", None)
    if signer_cert is None:
        return None
    subject = getattr(signer_cert, "subject", None)
    if subject is None:
        return None
    human_friendly = getattr(subject, "human_friendly", None)
    return human_friendly if isinstance(human_friendly, str) else str(subject)


def _verify_signature_locally(signature: object) -> bool | None:
    signer_cert = getattr(signature, "signer_cert", None)
    if signer_cert is None:
        return None
    try:
        status = validation.validate_pdf_signature(
            signature,
            signer_validation_context=ValidationContext(trust_roots=[signer_cert]),
        )
    except Exception:
        return False
    return bool(status.intact and status.valid)


def _signature_review_item(
    signature: object,
    *,
    index: int,
    latest_index: int,
    docmdp_permission: str | None,
    certification_restricted: bool,
    restriction_reason: str | None,
) -> DocumentSignatureReviewItem:
    signer_subject = _signer_subject(signature)
    cryptographic_validation_passed = _verify_signature_locally(signature)
    label = f"Signature {index + 1}"
    if index == latest_index:
        label = f"{label} (latest)"
    if signer_subject is None:
        subject_text = "Signer not available"
    else:
        subject_text = signer_subject
    if cryptographic_validation_passed is True:
        status_text = "verified locally"
    elif cryptographic_validation_passed is False:
        status_text = "needs local verification attention"
    else:
        status_text = "local verification not evaluated"
    return DocumentSignatureReviewItem(
        label=label,
        signer_subject=signer_subject,
        cryptographic_validation_passed=cryptographic_validation_passed,
        detail=f"{subject_text}: {status_text}.",
        drill_in_detail=_signature_drill_in_detail(
            signer_subject=signer_subject,
            cryptographic_validation_passed=cryptographic_validation_passed,
            docmdp_permission=docmdp_permission,
            certification_restricted=certification_restricted,
            restriction_reason=restriction_reason,
        ),
    )


def _signature_drill_in_detail(
    *,
    signer_subject: str | None,
    cryptographic_validation_passed: bool | None,
    docmdp_permission: str | None,
    certification_restricted: bool,
    restriction_reason: str | None,
) -> str:
    signer_text = signer_subject or "Signer not available"
    if cryptographic_validation_passed is True:
        verification_text = "verified locally"
    elif cryptographic_validation_passed is False:
        verification_text = "needs local verification attention"
    else:
        verification_text = "local verification not evaluated"
    if certification_restricted or restriction_reason:
        guidance_line = (
            "Document restrictions: "
            f"{restriction_reason or 'document certification restricts changes.'}"
        )
    else:
        guidance_line = (
            "Document permissions: "
            + _certification_guidance(
                docmdp_permission=docmdp_permission,
                certification_restricted=False,
                restriction_reason=None,
            )
        )
    return "\n".join(
        (
            f"Signer: {signer_text}.",
            f"Local verification: {verification_text}.",
            guidance_line,
        )
    )


def _certification_guidance(
    *,
    docmdp_permission: str | None,
    certification_restricted: bool,
    restriction_reason: str | None,
) -> str:
    if certification_restricted or restriction_reason:
        return (
            "Further changes may be blocked: "
            f"{restriction_reason or 'document certification restricts changes.'}"
        )
    if docmdp_permission == "fill_forms":
        return "Certification permits form filling and additional signing changes."
    if docmdp_permission == "annotate":
        return "Certification permits annotations and additional signing changes."
    if docmdp_permission is None:
        return "No certification restriction was detected."
    return f"Certification permission: {docmdp_permission.replace('_', ' ')}."
