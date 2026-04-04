"""Machine-validated evidence contract for Phase 3 harness artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PHASE3_EVIDENCE_CONTRACT_VERSION = "phase3_evidence_v1"
ENGINEERING_RUN = "engineering_run"
GATE_CANDIDATE = "gate_candidate"
RELEASE_GATE_PASSED = "release_gate_passed"
NON_GATING = "non_gating"

_SYNCED_APPEARANCE_FIELDS = (
    "layout_template",
    "stamp_position",
    "show_field_names",
    "datetime_format",
    "signer_label_prefix",
    "timezone_display_mode",
    "image_stamp_path",
)


@dataclass(frozen=True)
class EvidenceContractEvaluation:
    """Structured contract verdict for a Phase 3 harness capture."""

    contract_version: str
    acceptance_tier: str
    gate_verdict: str
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def evaluate_phase3_evidence_contract(
    capture: dict[str, Any],
) -> EvidenceContractEvaluation:
    """Validate a Phase 3 harness capture and derive a gate-ready classification."""

    errors: list[str] = []
    warnings: list[str] = []

    preview_snapshot = _mapping(capture.get("preview_snapshot"))
    sign_request_snapshot = _mapping(capture.get("sign_request_snapshot"))
    signature_appearance = _mapping(sign_request_snapshot.get("signature_appearance"))
    backend_reservation_snapshot = _mapping(capture.get("backend_reservation_snapshot"))
    visible_appearance_snapshot = _mapping(capture.get("output_visible_appearance_snapshot"))

    sign_request_count = _int(capture.get("sign_request_count"))
    sign_attempted = sign_request_count > 0
    signing_succeeded = capture.get("last_signing_result_success") is True
    output_file_exists = capture.get("output_file_exists") is True
    checklist_results_written = capture.get("checklist_results_written") is True
    preview_available = capture.get("preview_available") is True
    preview_can_submit = preview_snapshot.get("can_submit") is True
    validation_text = str(capture.get("validation_text") or "")
    visible_signature_requested = capture.get("last_signature_has_visible_appearance") is True

    if signing_succeeded and not output_file_exists:
        errors.append(
            "Signing succeeded but output_file_exists is false; successful runs "
            "must produce an output file."
        )

    if signing_succeeded and capture.get("output_signature_count") is None:
        errors.append(
            "Signing succeeded but output_signature_count is missing; successful "
            "runs must record embedded signature count."
        )

    if signing_succeeded and _int(capture.get("output_signature_count")) < 1:
        errors.append(
            "Signing succeeded but output_signature_count is less than 1; "
            "successful runs must embed at least one signature."
        )

    if signing_succeeded and visible_signature_requested and not visible_appearance_snapshot:
        errors.append(
            "Signing succeeded with a visible signature request but "
            "output_visible_appearance_snapshot is missing."
        )

    if preview_can_submit and not sign_attempted:
        warnings.append(
            "Preview was ready to sign but no submitted sign request was captured; "
            "treat this run as non-gating unless a manual abort is documented."
        )

    if sign_request_snapshot and not backend_reservation_snapshot and not capture.get(
        "backend_reservation_error"
    ):
        errors.append(
            "A sign-request snapshot was captured but backend reservation diagnostics were omitted."
        )

    snapshot_error = backend_reservation_snapshot.get("error")
    reservation_error = capture.get("backend_reservation_error")
    if reservation_error is None and snapshot_error is not None:
        errors.append(
            "backend_reservation_snapshot carries an error while backend_reservation_error is null."
        )
    if (
        reservation_error is not None
        and backend_reservation_snapshot
        and snapshot_error != reservation_error
    ):
        errors.append(
            "backend_reservation_error does not match backend_reservation_snapshot.error."
        )

    if preview_snapshot and sign_request_snapshot:
        for key in _SYNCED_APPEARANCE_FIELDS:
            preview_value = preview_snapshot.get(key)
            request_value = signature_appearance.get(key)
            if preview_value != request_value:
                errors.append(
                    "Preview snapshot and request snapshot disagree on "
                    f"`{key}` ({preview_value!r} != {request_value!r})."
                )

    if sign_attempted and not preview_snapshot:
        errors.append(
            "A sign request was captured without any preview snapshot; gating "
            "runs must preserve preview state."
        )

    if sign_attempted and not sign_request_snapshot:
        errors.append(
            "A sign request count was recorded without a sign_request_snapshot."
        )

    if not checklist_results_written:
        warnings.append(
            "The acceptance results markdown was not written; this run cannot "
            "be treated as a gate candidate."
        )

    if not preview_available and preview_snapshot:
        warnings.append(
            "The harness captured a preview snapshot but preview_available is "
            "false; inspect the preview text/visibility state before treating "
            "this as evidence."
        )

    if sign_attempted and not validation_text:
        warnings.append(
            "A signing attempt was captured without validation_text; the run is "
            "usable for debugging but not ideal gate evidence."
        )

    gate_candidate_ready = (
        not errors
        and checklist_results_written
        and bool(preview_snapshot)
        and bool(sign_request_snapshot)
        and bool(validation_text)
        and (not signing_succeeded or output_file_exists)
        and (not signing_succeeded or capture.get("output_signature_count") is not None)
        and (
            not (signing_succeeded and visible_signature_requested)
            or bool(visible_appearance_snapshot)
        )
    )

    acceptance_tier = GATE_CANDIDATE if gate_candidate_ready else ENGINEERING_RUN
    gate_verdict = GATE_CANDIDATE if gate_candidate_ready else NON_GATING

    return EvidenceContractEvaluation(
        contract_version=PHASE3_EVIDENCE_CONTRACT_VERSION,
        acceptance_tier=acceptance_tier,
        gate_verdict=gate_verdict,
        passed=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0
