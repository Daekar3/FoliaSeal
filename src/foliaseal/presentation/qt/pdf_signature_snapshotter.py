"""Pure signed-PDF evidence snapshots for the Acceptance harness."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext

from foliaseal.domain.models import TimestampTrustPolicy
from foliaseal.infra.certification import inspect_pdf_certification_reader
from foliaseal.infra.tsa import build_timestamp_validation_context


@dataclass(frozen=True)
class AcceptancePdfSignatureSnapshotter:
    """Own JSON-ready signature, verification, and appearance evidence."""

    def count_embedded_signatures(self, output_file: Path) -> int | None:
        try:
            with output_file.open("rb") as handle:
                reader = PdfFileReader(handle)
                return len(list(reader.embedded_signatures))
        except Exception:
            return None

    def snapshot_output_signature(self, output_file: Path) -> dict[str, Any] | None:
        try:
            with output_file.open("rb") as handle:
                reader = PdfFileReader(handle)
                embedded_signatures = list(reader.embedded_signatures)
                if not embedded_signatures:
                    return None
                signature = embedded_signatures[-1]
                sig_object = signature.sig_object
                return {
                    "field_name": signature.field_name,
                    "name": sig_object.get("/Name"),
                    "location": sig_object.get("/Location"),
                    "contact_info": sig_object.get("/ContactInfo"),
                    "byte_range": list(sig_object.get("/ByteRange", [])),
                    "subfilter": sig_object.get("/SubFilter"),
                    "md_algorithm": signature.md_algorithm,
                    "coverage": _serialize_signature_metadata(signature.coverage),
                    "docmdp_level": _serialize_signature_metadata(signature.docmdp_level),
                }
        except Exception:
            return None

    def snapshot_output_verification(
        self,
        output_file: Path,
        trust_policy: TimestampTrustPolicy | None = None,
    ) -> dict[str, Any] | None:
        try:
            with output_file.open("rb") as handle:
                reader = PdfFileReader(handle)
                embedded_signatures = list(reader.embedded_signatures)
                if not embedded_signatures:
                    return {
                        "cryptographic_validation_passed": False,
                        "signature_count": 0,
                        "docmdp_permission": None,
                        "certification_restricted": False,
                        "restriction_reason": None,
                        "error": "No embedded signature fields were found in the output PDF.",
                    }

                signature = embedded_signatures[-1]
                validation_context = ValidationContext(trust_roots=[signature.signer_cert])
                ts_validation_context = build_timestamp_validation_context(trust_policy)
                status = validation.validate_pdf_signature(
                    signature,
                    signer_validation_context=validation_context,
                    ts_validation_context=ts_validation_context,
                )
                certification = inspect_pdf_certification_reader(reader)
                signer_subject = None
                if getattr(signature, "signer_cert", None) is not None:
                    subject = getattr(signature.signer_cert, "subject", None)
                    if subject is not None:
                        human_friendly = getattr(subject, "human_friendly", None)
                        signer_subject = (
                            human_friendly if isinstance(human_friendly, str) else str(subject)
                        )
                return {
                    "cryptographic_validation_passed": bool(status.intact and status.valid),
                    "intact": bool(status.intact),
                    "valid": bool(status.valid),
                    "trusted": bool(getattr(status, "trust_problem_indicative", False) is False),
                    "signature_count": len(embedded_signatures),
                    "timestamp_present": _status_has_timestamp(status),
                    "timestamp_cryptographically_valid": (
                        _status_timestamp_cryptographically_valid(status)
                        if trust_policy is not None
                        else None
                    ),
                    "tsa_chain_trusted": (
                        _status_timestamp_trusted(status)
                        if trust_policy is not None
                        else None
                    ),
                    "timestamp_validation_error": (
                        _describe_timestamp_trust(status)
                        if trust_policy is not None and not _status_timestamp_trusted(status)
                        else None
                    ),
                    "docmdp_permission": certification.docmdp_permission,
                    "certification_restricted": certification.certification_restricted,
                    "restriction_reason": certification.restriction_reason,
                    "field_name": signature.field_name,
                    "subfilter": signature.sig_object.get("/SubFilter"),
                    "byte_range_present": bool(signature.sig_object.get("/ByteRange")),
                    "md_algorithm": signature.md_algorithm,
                    "signer_subject": signer_subject,
                    "error": None,
                }
        except Exception as exc:
            return {
                "cryptographic_validation_passed": False,
                "signature_count": None,
                "docmdp_permission": None,
                "certification_restricted": False,
                "restriction_reason": None,
                "error": str(exc),
            }

    def snapshot_visible_signature_appearance(
        self,
        output_file: Path,
    ) -> dict[str, Any] | None:
        try:
            with output_file.open("rb") as handle:
                reader = PdfFileReader(handle)
                embedded_signatures = list(reader.embedded_signatures)
                if not embedded_signatures:
                    return None

                signature = embedded_signatures[-1]
                sig_field = signature.sig_field
                rect = snapshot_pdf_rect(sig_field.get("/Rect"))
                appearance_dict = sig_field.get("/AP")
                if appearance_dict is None:
                    return {
                        "field_name": signature.field_name,
                        "annotation_rect": rect,
                        "error": "Missing /AP entry on the signature field.",
                    }

                normal_appearance = appearance_dict.get("/N")
                if normal_appearance is None:
                    return {
                        "field_name": signature.field_name,
                        "annotation_rect": rect,
                        "error": "Missing normal appearance stream for the signature field.",
                    }

                appearance_stream = normal_appearance.get_object()
                appearance_data = appearance_stream.data
                appearance_text = appearance_data.decode("latin1", errors="replace")
                xobject_summaries = _snapshot_appearance_xobjects(
                    appearance_stream.get("/Resources")
                )
                text_fragments = _extract_pdf_text_fragments(appearance_text)
                visible_text_present = bool(text_fragments)
                image_xobject_count = sum(
                    1 for item in xobject_summaries if item.get("subtype") == "/Image"
                )
                appearance_bbox = snapshot_pdf_rect(appearance_stream.get("/BBox"))
                rounded_border = _appearance_text_uses_rounded_border(appearance_text)
                return {
                    "field_name": signature.field_name,
                    "annotation_rect": rect,
                    "appearance_bbox": appearance_bbox,
                    "appearance_stream_length": len(appearance_data),
                    "appearance_text_fragments": text_fragments,
                    "appearance_text_snippet": appearance_text[:240],
                    "appearance_text_operator_count": _count_pdf_text_operators(appearance_text),
                    "appearance_xobjects": xobject_summaries,
                    "appearance_image_xobject_count": image_xobject_count,
                    "appearance_has_visible_text": visible_text_present,
                    "visible_text_present": visible_text_present,
                    "text_fragments": text_fragments,
                    "image_xobjects": xobject_summaries,
                    "annotation_rect_size": _snapshot_rect_size(rect),
                    "appearance_bbox_size": _snapshot_rect_size(appearance_bbox),
                    "text_fragment_count": len(text_fragments),
                    "image_xobject_count": image_xobject_count,
                    "appearance_uses_rounded_border": rounded_border,
                }
        except Exception as exc:
            return {"error": str(exc)}


def snapshot_pdf_rect(value: Any) -> list[float] | None:
    if value is None:
        return None
    try:
        return [float(component) for component in value]
    except Exception:
        return None


def _snapshot_appearance_xobjects(resources: Any) -> list[dict[str, Any]]:
    if resources is None:
        return []
    xobjects = resources.get("/XObject")
    if xobjects is None:
        return []
    summaries: list[dict[str, Any]] = []
    for name, reference in xobjects.items():
        try:
            obj = reference.get_object()
        except Exception:
            obj = reference
        summaries.append(
            {
                "name": str(name),
                "subtype": _snapshot_pdf_name(obj.get("/Subtype")),
                "width": _snapshot_pdf_numeric(obj.get("/Width")),
                "height": _snapshot_pdf_numeric(obj.get("/Height")),
                "bbox": snapshot_pdf_rect(obj.get("/BBox")),
            }
        )
    return summaries


def _count_pdf_text_operators(appearance_text: str) -> int:
    return len(re.findall(r"\)\s*T[Jj]\b", appearance_text))


def _extract_pdf_text_fragments(appearance_text: str) -> list[str]:
    fragments: list[str] = []
    for match in re.finditer(r"\((?:\\.|[^()])*\)", appearance_text):
        fragment = _decode_pdf_literal_string(match.group(0))
        if fragment:
            fragments.append(fragment)
    return fragments


def _decode_pdf_literal_string(literal: str) -> str:
    if not literal.startswith("(") or not literal.endswith(")"):
        return literal

    body = literal[1:-1]
    out: list[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue

        index += 1
        if index >= len(body):
            break
        escape = body[index]
        if escape in "nrtbf()\\":
            out.append(
                {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "b": "\b",
                    "f": "\f",
                    "(": "(",
                    ")": ")",
                    "\\": "\\",
                }[escape]
            )
            index += 1
            continue
        if escape in "\r\n":
            if escape == "\r" and index + 1 < len(body) and body[index + 1] == "\n":
                index += 2
            else:
                index += 1
            continue
        if escape in "01234567":
            digits = [escape]
            index += 1
            while index < len(body) and len(digits) < 3 and body[index] in "01234567":
                digits.append(body[index])
                index += 1
            out.append(chr(int("".join(digits), 8)))
            continue
        out.append(escape)
        index += 1
    return "".join(out)


def _snapshot_pdf_name(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _snapshot_pdf_numeric(value: Any) -> float | int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except Exception:
        return None
    return int(numeric) if numeric.is_integer() else numeric


def _snapshot_rect_size(rect: list[float] | None) -> dict[str, float] | None:
    if rect is None or len(rect) != 4:
        return None
    left, bottom, right, top = rect
    return {
        "width": float(right - left),
        "height": float(top - bottom),
    }


def _serialize_signature_metadata(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _serialize_signature_metadata(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_signature_metadata(item) for item in value]
    return str(value)


def _appearance_text_uses_rounded_border(appearance_text: str) -> bool | None:
    if not appearance_text.strip():
        return None
    if " c " in appearance_text or appearance_text.strip().startswith("c "):
        return True
    if " re S" in appearance_text or "\nre\nS" in appearance_text:
        return False
    return None


def _status_has_timestamp(status: Any) -> bool:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return False
    return bool(
        getattr(timestamp_validity, "intact", True)
        and getattr(timestamp_validity, "valid", True)
    )


def _status_timestamp_cryptographically_valid(status: Any) -> bool | None:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return None
    return bool(
        getattr(timestamp_validity, "intact", True)
        and getattr(timestamp_validity, "valid", True)
    )


def _status_timestamp_trusted(status: Any) -> bool | None:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return None
    return bool(getattr(timestamp_validity, "trusted", False))


def _describe_timestamp_trust(status: Any) -> str | None:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return None
    describe_timestamp_trust = getattr(timestamp_validity, "describe_timestamp_trust", None)
    if not callable(describe_timestamp_trust):
        return None
    try:
        return describe_timestamp_trust()
    except Exception:
        return None
