"""Read-only document signature review helpers for the GUI shell."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal, Protocol

from pyhanko.pdf_utils.form_tools import get_single_field_annot
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko.sign.fields import enumerate_sig_fields
from pyhanko_certvalidator import ValidationContext

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.infra.certification import inspect_pdf_certification_reader

DocumentSignatureKind = Literal["signed_visible", "signed_invisible", "unsigned_field"]
DocumentSignatureIntegrityStatus = Literal[
    "valid",
    "changed_after_signature",
    "invalid",
    "could_not_verify",
    "unsigned",
]


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
    signature_id: str = ""
    kind: DocumentSignatureKind = "signed_visible"
    field_name: str | None = None
    page_index: int | None = None
    highlight_rect: PdfRect | None = None
    claimed_signing_time: str | None = None
    trusted_timestamp: str | None = None
    integrity_status: DocumentSignatureIntegrityStatus = "could_not_verify"


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
                signature_items = _build_signature_review_items(
                    reader,
                    embedded_signatures,
                    docmdp_permission=certification.docmdp_permission,
                    certification_restricted=certification.certification_restricted,
                    restriction_reason=certification.restriction_reason,
                )
                if not embedded_signatures:
                    return summarize_document_review(
                        signature_count=0,
                        signature_items=signature_items,
                        docmdp_permission=certification.docmdp_permission,
                        certification_restricted=certification.certification_restricted,
                        restriction_reason=certification.restriction_reason,
                    )

                signature = embedded_signatures[-1]
                signer_subject = _signer_subject(signature)
                latest_name = str(getattr(signature, "fq_name", ""))
                latest_item = next(
                    (
                        item
                        for item in signature_items
                        if item.field_name == latest_name
                    ),
                    None,
                )
                if latest_item is None:
                    signed_items = tuple(
                        item
                        for item in signature_items
                        if item.kind in {"signed_visible", "signed_invisible"}
                    )
                    latest_item = signed_items[-1] if signed_items else None
                cryptographic_validation_passed = (
                    latest_item.cryptographic_validation_passed
                    if latest_item is not None
                    else _verify_signature_locally(signature)
                )
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


def _build_signature_review_items(
    reader: PdfFileReader,
    embedded_signatures: list[object],
    *,
    docmdp_permission: str | None,
    certification_restricted: bool,
    restriction_reason: str | None,
) -> tuple[DocumentSignatureReviewItem, ...]:
    """Project filled and empty PDF signature fields into document-order items."""

    by_field_name = {
        str(getattr(signature, "fq_name", "")): signature
        for signature in embedded_signatures
        if str(getattr(signature, "fq_name", ""))
    }
    items: list[DocumentSignatureReviewItem] = []
    seen_signed_names: set[str] = set()
    try:
        field_records = tuple(
            enumerate_sig_fields(reader, filled_status=None)
        )
    except Exception:
        field_records = ()

    for field_name, field_value, field_ref in field_records:
        name = str(field_name)
        page_index, highlight_rect = _field_annotation_geometry(reader, field_ref)
        signature = by_field_name.get(name)
        if signature is not None:
            seen_signed_names.add(name)
            index = embedded_signatures.index(signature)
            items.append(
                _signature_review_item(
                    signature,
                    index=index,
                    latest_index=len(embedded_signatures) - 1,
                    docmdp_permission=docmdp_permission,
                    certification_restricted=certification_restricted,
                    restriction_reason=restriction_reason,
                    signature_id=f"{name}:signed",
                    field_name=name,
                    page_index=page_index,
                    highlight_rect=highlight_rect,
                )
            )
        elif field_value is None:
            items.append(
                DocumentSignatureReviewItem(
                    label=f"Unsigned field: {name}",
                    signer_subject=None,
                    cryptographic_validation_passed=None,
                    detail="This signature field is available for an explicit new signature.",
                    drill_in_detail=(
                        f"Field: {name}.\n"
                        "Status: unsigned signature field.\n"
                        "Choose it explicitly when you are ready to place a new signature."
                    ),
                    signature_id=f"{name}:unsigned",
                    kind="unsigned_field",
                    field_name=name,
                    page_index=page_index,
                    highlight_rect=highlight_rect,
                    integrity_status="unsigned",
                )
            )

    for index, signature in enumerate(embedded_signatures):
        field_name = str(getattr(signature, "fq_name", "")) or f"Signature {index + 1}"
        if field_name in seen_signed_names:
            continue
        page_index, highlight_rect = _field_annotation_geometry(
            reader,
            getattr(signature, "sig_field", None),
        )
        items.append(
            _signature_review_item(
                signature,
                index=index,
                latest_index=len(embedded_signatures) - 1,
                docmdp_permission=docmdp_permission,
                certification_restricted=certification_restricted,
                restriction_reason=restriction_reason,
                signature_id=f"{field_name}:signed",
                field_name=field_name,
                page_index=page_index,
                highlight_rect=highlight_rect,
            )
        )
    return tuple(items)


def _field_annotation_geometry(
    reader: PdfFileReader,
    field_ref: object,
) -> tuple[int | None, PdfRect | None]:
    """Read one signature annotation's page and PDF-space rectangle safely."""

    if field_ref is None:
        return None, None
    field = getattr(field_ref, "get_object", lambda: field_ref)()
    try:
        annotation = get_single_field_annot(field)
    except Exception:
        annotation = field
    rect = None
    for key in ("/Rect",):
        getter = getattr(annotation, "get", None)
        if callable(getter):
            rect = getter(key)
        if rect is not None:
            break
    try:
        values = tuple(float(value) for value in rect) if rect is not None else ()
        if len(values) != 4:
            return _annotation_page_index(reader, annotation), None
        highlight_rect = PdfRect(
            x1=values[0],
            y1=values[1],
            x2=values[2],
            y2=values[3],
        ).normalized()
    except (TypeError, ValueError):
        highlight_rect = None
    return _annotation_page_index(reader, annotation), highlight_rect


def _annotation_page_index(reader: PdfFileReader, annotation: object) -> int | None:
    getter = getattr(annotation, "raw_get", None)
    page_ref = getter("/P") if callable(getter) else getattr(annotation, "P", None)
    if page_ref is None:
        return None
    try:
        page_count = int(reader.root["/Pages"]["/Count"])
        for page_index in range(page_count):
            candidate_ref, _resources = reader.find_page_for_modification(page_index)
            if getattr(candidate_ref, "reference", None) == getattr(page_ref, "reference", None):
                return page_index
    except Exception:
        return None
    return None


def _signer_subject(signature: object) -> str | None:
    signer_cert = getattr(signature, "signer_cert", None)
    if signer_cert is None:
        return None
    subject = getattr(signer_cert, "subject", None)
    if subject is None:
        return None
    human_friendly = getattr(subject, "human_friendly", None)
    return human_friendly if isinstance(human_friendly, str) else str(subject)


def _signature_validation_status(signature: object) -> object | None:
    """Return PyHanko's status object without leaking it across the application boundary."""

    signer_cert = getattr(signature, "signer_cert", None)
    if signer_cert is None:
        return None
    try:
        return validation.validate_pdf_signature(
            signature,
            signer_validation_context=ValidationContext(trust_roots=[signer_cert]),
        )
    except Exception:
        return None


def _signature_status_passed(status: object | None) -> bool | None:
    if status is None:
        return None
    intact = getattr(status, "intact", None)
    valid = getattr(status, "valid", None)
    if intact is None or valid is None:
        return None
    return bool(intact and valid)


def _signature_integrity_status(
    status: object | None,
    cryptographic_validation_passed: bool | None,
) -> DocumentSignatureIntegrityStatus:
    """Classify integrity separately from certificate trust and signer identity."""

    if status is None or cryptographic_validation_passed is None:
        return "could_not_verify"
    if not cryptographic_validation_passed:
        return "invalid"
    try:
        modification_level = getattr(status, "modification_level", None)
    except Exception:
        modification_level = None
    if modification_level is not None:
        level_name = getattr(modification_level, "name", str(modification_level))
        if level_name != "NONE":
            return "changed_after_signature"
    return "valid"


def _verify_signature_locally(signature: object) -> bool | None:
    return _signature_status_passed(_signature_validation_status(signature))


def _format_review_time(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    text = str(value).strip()
    return text or None


def _trusted_timestamp_from_status(status: object | None) -> str | None:
    timestamp_status = getattr(status, "timestamp_validity", None)
    if timestamp_status is None:
        return None
    if not all(
        bool(getattr(timestamp_status, attribute, False))
        for attribute in ("valid", "intact", "trusted")
    ):
        return None
    return _format_review_time(getattr(timestamp_status, "timestamp", None))


def _signature_review_item(
    signature: object,
    *,
    index: int,
    latest_index: int,
    docmdp_permission: str | None,
    certification_restricted: bool,
    restriction_reason: str | None,
    signature_id: str | None = None,
    field_name: str | None = None,
    page_index: int | None = None,
    highlight_rect: PdfRect | None = None,
) -> DocumentSignatureReviewItem:
    signer_subject = _signer_subject(signature)
    validation_status = _signature_validation_status(signature)
    cryptographic_validation_passed = _signature_status_passed(validation_status)
    integrity_status = _signature_integrity_status(
        validation_status,
        cryptographic_validation_passed,
    )
    claimed_signing_time = _format_review_time(
        getattr(signature, "self_reported_timestamp", None)
    )
    trusted_timestamp = _trusted_timestamp_from_status(validation_status)
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
    time_lines = []
    if claimed_signing_time is not None:
        time_lines.append(f"Claimed signing time: {claimed_signing_time}.")
    else:
        time_lines.append("Claimed signing time: not available.")
    if trusted_timestamp is not None:
        time_lines.append(f"Trusted timestamp: {trusted_timestamp}.")
    else:
        time_lines.append("Trusted timestamp: not available.")
    drill_in_detail = _signature_drill_in_detail(
        signer_subject=signer_subject,
        cryptographic_validation_passed=cryptographic_validation_passed,
        docmdp_permission=docmdp_permission,
        certification_restricted=certification_restricted,
        restriction_reason=restriction_reason,
    )
    integrity_lines = [f"Integrity status: {_integrity_status_label(integrity_status)}."]
    if integrity_status == "changed_after_signature":
        docmdp_text = "permitted by the document policy" if getattr(
            validation_status, "docmdp_ok", None
        ) else "not permitted by the document policy"
        integrity_lines.append(f"Changes after signature: {docmdp_text}.")
    drill_in_detail = "\n".join(
        (*drill_in_detail.splitlines(), *integrity_lines, *time_lines)
    )
    return DocumentSignatureReviewItem(
        label=label,
        signer_subject=signer_subject,
        cryptographic_validation_passed=cryptographic_validation_passed,
        detail=f"{subject_text}: {status_text}.",
        drill_in_detail=drill_in_detail,
        signature_id=signature_id or label,
        kind="signed_visible" if highlight_rect is not None else "signed_invisible",
        field_name=field_name,
        page_index=page_index,
        highlight_rect=highlight_rect,
        claimed_signing_time=claimed_signing_time,
        trusted_timestamp=trusted_timestamp,
        integrity_status=integrity_status,
    )


def _integrity_status_label(status: DocumentSignatureIntegrityStatus) -> str:
    return {
        "valid": "valid",
        "changed_after_signature": "changed after signature",
        "invalid": "invalid",
        "could_not_verify": "could not be verified locally",
        "unsigned": "unsigned",
    }[status]


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
    lines = [
        f"Signer: {signer_text}.",
        f"Local verification: {verification_text}.",
        guidance_line,
    ]
    next_step = _signature_next_action_guidance(
        cryptographic_validation_passed=cryptographic_validation_passed,
        certification_restricted=certification_restricted,
        restriction_reason=restriction_reason,
    )
    if next_step is not None:
        lines.append(f"Recommended next step: {next_step}")
    return "\n".join(lines)


def _signature_next_action_guidance(
    *,
    cryptographic_validation_passed: bool | None,
    certification_restricted: bool,
    restriction_reason: str | None,
) -> str | None:
    if cryptographic_validation_passed is True:
        return None
    restricted = certification_restricted or restriction_reason is not None
    if cryptographic_validation_passed is False:
        if restricted:
            return (
                "reopen the signed PDF, review the selected signature details "
                "carefully, and expect that further changes may be blocked."
            )
        return (
            "reopen the signed PDF and review the selected signature details "
            "carefully before relying on it."
        )
    if restricted:
        return (
            "reopen the signed PDF, review the embedded signer details, "
            "and expect that further changes may be blocked."
        )
    return (
        "reopen the signed PDF and review the embedded signer details before "
        "relying on this signature."
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
