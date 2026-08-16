"""Machine-validated evidence contract for Acceptance harness artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

EVIDENCE_CONTRACT_VERSION = "evidence_v1"
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
    """Structured contract verdict for a Acceptance harness capture."""

    contract_version: str
    acceptance_tier: str
    gate_verdict: str
    passed: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def evaluate_acceptance_evidence_contract(
    capture: dict[str, Any],
) -> EvidenceContractEvaluation:
    """Validate a Acceptance harness capture and derive a gate-ready classification."""

    errors: list[str] = []
    warnings: list[str] = []

    preview_snapshot = _mapping(capture.get("preview_snapshot"))
    sign_request_snapshot = _mapping(capture.get("sign_request_snapshot"))
    signature_appearance = _mapping(sign_request_snapshot.get("signature_appearance"))
    backend_reservation_snapshot = _mapping(capture.get("backend_reservation_snapshot"))
    visible_appearance_snapshot = _mapping(capture.get("output_visible_appearance_snapshot"))
    output_verification_snapshot = _mapping(capture.get("output_verification_snapshot"))
    signed_output_render_snapshot = _mapping(capture.get("signed_output_render_snapshot"))
    signed_output_preview_comparison = _mapping(capture.get("signed_output_preview_comparison"))
    signed_output_render_snapshot = _mapping(capture.get("signed_output_render_snapshot"))
    signed_output_preview_comparison = _mapping(
        capture.get("signed_output_preview_comparison")
    )
    captured_states = capture.get("captured_states")
    transition_diagnostics = capture.get("captured_state_transition_diagnostics")

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

    if signing_succeeded and not output_verification_snapshot:
        errors.append(
            "Signing succeeded but output_verification_snapshot is missing."
        )

    if signing_succeeded and output_verification_snapshot:
        if output_verification_snapshot.get("cryptographic_validation_passed") is not True:
            errors.append(
                "Signing succeeded but output_verification_snapshot reports failed "
                "cryptographic validation."
            )

    if signing_succeeded and visible_signature_requested and not signed_output_render_snapshot:
        errors.append(
            "Signing succeeded with a visible signature request but "
            "signed_output_render_snapshot is missing."
        )

    if signing_succeeded and visible_signature_requested and not signed_output_preview_comparison:
        errors.append(
            "Signing succeeded with a visible signature request but "
            "signed_output_preview_comparison is missing."
        )

    if signing_succeeded and visible_signature_requested and signed_output_preview_comparison:
        if signed_output_preview_comparison.get("preview_vs_signed_output_passed") is not True:
            errors.append(
                "Signing succeeded but signed_output_preview_comparison reports "
                "preview/output mismatch."
            )
    if signing_succeeded:
        if not signed_output_render_snapshot:
            errors.append(
                "Signing succeeded but signed_output_render_snapshot is missing; "
                "successful runs must preserve signed-output render evidence."
            )
        if not signed_output_preview_comparison:
            errors.append(
                "Signing succeeded but signed_output_preview_comparison is missing; "
                "successful runs must compare the signed appearance to the preview."
            )
        if signed_output_preview_comparison:
            if signed_output_preview_comparison.get("preview_vs_signed_output_passed") is not True:
                errors.append(
                    "Signing succeeded but the signed-output comparison did not pass."
                )
            if signed_output_preview_comparison.get("signature_crop_path") is None:
                errors.append(
                    "Signing succeeded but signed_output_preview_comparison is missing "
                    "signature_crop_path."
                )
            if signed_output_preview_comparison.get("comparison_path") is None:
                errors.append(
                    "Signing succeeded but signed_output_preview_comparison is missing "
                    "comparison_path."
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

    if capture.get("summary_json_path"):
        _validate_preview_render_artifacts(
            errors=errors,
            render_capture=_mapping(preview_snapshot.get("render_capture")),
            context="current preview snapshot",
        )
        _validate_signable_render_consistency(
            errors=errors,
            preview_snapshot=preview_snapshot,
            context="current preview snapshot",
        )
        if isinstance(captured_states, (list, tuple)):
            for index, state in enumerate(captured_states, start=1):
                state_mapping = _mapping(state)
                state_preview = _mapping(state_mapping.get("preview_snapshot"))
                _validate_preview_render_artifacts(
                    errors=errors,
                    render_capture=_mapping(state_preview.get("render_capture")),
                    context=f"captured_states[{index}]",
                )
                _validate_signable_render_consistency(
                    errors=errors,
                    preview_snapshot=state_preview,
                    context=f"captured_states[{index}]",
                )
        if isinstance(transition_diagnostics, (list, tuple)):
            for index, diagnostic in enumerate(transition_diagnostics, start=1):
                issue_code = str(_mapping(diagnostic).get("issue_code") or "")
                if issue_code:
                    warnings.append(
                        "Captured-state transition diagnostic "
                        f"{index} reported `{issue_code}`; preview control changes may "
                        "not be producing a meaningful visual response."
                    )

    if signing_succeeded and visible_signature_requested:
        _validate_signed_output_artifacts(
            errors=errors,
            render_snapshot=signed_output_render_snapshot,
            comparison_snapshot=signed_output_preview_comparison,
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
        and (not signing_succeeded or bool(output_verification_snapshot))
        and (
            not (signing_succeeded and visible_signature_requested)
            or bool(visible_appearance_snapshot)
        )
        and (
            not (signing_succeeded and visible_signature_requested)
            or bool(signed_output_render_snapshot)
        )
        and (
            not (signing_succeeded and visible_signature_requested)
            or bool(signed_output_preview_comparison)
        )
    )

    acceptance_tier = GATE_CANDIDATE if gate_candidate_ready else ENGINEERING_RUN
    gate_verdict = GATE_CANDIDATE if gate_candidate_ready else NON_GATING

    return EvidenceContractEvaluation(
        contract_version=EVIDENCE_CONTRACT_VERSION,
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


def _validate_preview_render_artifacts(
    *,
    errors: list[str],
    render_capture: dict[str, Any],
    context: str,
) -> None:
    if not render_capture:
        errors.append(f"{context} is missing render_capture diagnostics.")
        return
    if render_capture.get("preview_image_error") is not None:
        errors.append(f"{context} reported preview_image_error in a saved harness capture.")
    if not render_capture.get("preview_image_path"):
        errors.append(f"{context} is missing preview_image_path.")
    for key in (
        "text_rendered_content_bounds_px",
        "text_debug_image_path",
        "stamp_debug_image_path",
        "text_content_clipped_in_preview",
        "stamp_content_within_warning_distance",
    ):
        if key not in render_capture:
            errors.append(f"{context} is missing `{key}` render diagnostics.")


def _validate_signable_render_consistency(
    *,
    errors: list[str],
    preview_snapshot: dict[str, Any],
    context: str,
) -> None:
    if preview_snapshot.get("can_submit") is not True:
        return
    render_capture = _mapping(preview_snapshot.get("render_capture"))
    if not render_capture:
        return
    if (
        render_capture.get("text_content_clipped_in_preview") is True
        or render_capture.get("text_content_overlaps_stamp_band") is True
        or render_capture.get("text_content_overlaps_stamp_content") is True
        or render_capture.get("stamp_content_touches_band_edge") is True
    ):
        errors.append(
            f"{context} is signable even though render diagnostics report "
            "a user-visible fit failure."
        )


def _validate_signed_output_artifacts(
    *,
    errors: list[str],
    render_snapshot: dict[str, Any],
    comparison_snapshot: dict[str, Any],
) -> None:
    if not render_snapshot:
        errors.append("Signed-output render snapshot is missing.")
        return
    if render_snapshot.get("page_render_error") is not None:
        errors.append("Signed-output render reported page_render_error.")
    if render_snapshot.get("signature_crop_error") is not None:
        errors.append("Signed-output render reported signature_crop_error.")
    if not render_snapshot.get("page_render_path"):
        errors.append("Signed-output render is missing page_render_path.")
    if not render_snapshot.get("signature_crop_path"):
        errors.append("Signed-output render is missing signature_crop_path.")
    if comparison_snapshot:
        if comparison_snapshot.get("preview_vs_signed_output_error") is not None:
            errors.append("Signed-output comparison reported an explicit comparison error.")
        if not comparison_snapshot.get("comparison_path"):
            errors.append("Signed-output comparison is missing comparison_path.")
