"""Pure evidence-matrix result and acceptance projection.

This module deliberately has no Qt, Pillow, pyHanko, or filesystem imports.
It owns the stable mapping policy shared by the preview and signed matrix
adapters while the concrete harness remains responsible for capture.
"""

from __future__ import annotations

from typing import Any


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def preview_matrix_error_result(*, scenario: dict[str, Any], error: Exception) -> dict[str, Any]:
    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "error": str(error),
        "error_type": error.__class__.__name__,
    }


def preview_matrix_diagnostic_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    text_clip_count = 0
    text_overlap_count = 0
    stamp_warning_count = 0
    stamp_edge_touch_count = 0
    signable_text_clip_count = 0
    rejected_text_clip_count = 0
    signable_text_overlap_count = 0
    rejected_text_overlap_count = 0
    signable_stamp_warning_count = 0
    rejected_stamp_warning_count = 0
    signable_stamp_edge_touch_count = 0
    rejected_stamp_edge_touch_count = 0
    for result in results:
        preview_snapshot = result.get("preview_snapshot")
        if not isinstance(preview_snapshot, dict):
            continue
        render_capture = preview_snapshot.get("render_capture")
        if not isinstance(render_capture, dict):
            continue
        can_submit = preview_snapshot.get("can_submit") is True
        if render_capture.get("text_content_clipped_in_preview") is True:
            text_clip_count += 1
            if can_submit:
                signable_text_clip_count += 1
            else:
                rejected_text_clip_count += 1
        if (
            render_capture.get("text_content_overlaps_stamp_band") is True
            or render_capture.get("text_content_overlaps_stamp_content") is True
        ):
            text_overlap_count += 1
            if can_submit:
                signable_text_overlap_count += 1
            else:
                rejected_text_overlap_count += 1
        if render_capture.get("stamp_content_within_warning_distance") is True:
            stamp_warning_count += 1
            if can_submit:
                signable_stamp_warning_count += 1
            else:
                rejected_stamp_warning_count += 1
        if render_capture.get("stamp_content_touches_band_edge") is True:
            stamp_edge_touch_count += 1
            if can_submit:
                signable_stamp_edge_touch_count += 1
            else:
                rejected_stamp_edge_touch_count += 1
    return {
        "text_clipping_risk_scenario_count": text_clip_count,
        "signable_text_clipping_risk_scenario_count": signable_text_clip_count,
        "rejected_text_clipping_risk_scenario_count": rejected_text_clip_count,
        "text_stamp_overlap_risk_scenario_count": text_overlap_count,
        "signable_text_stamp_overlap_risk_scenario_count": signable_text_overlap_count,
        "rejected_text_stamp_overlap_risk_scenario_count": rejected_text_overlap_count,
        "stamp_warning_scenario_count": stamp_warning_count,
        "signable_stamp_warning_scenario_count": signable_stamp_warning_count,
        "rejected_stamp_warning_scenario_count": rejected_stamp_warning_count,
        "stamp_edge_touch_scenario_count": stamp_edge_touch_count,
        "signable_stamp_edge_touch_scenario_count": signable_stamp_edge_touch_count,
        "rejected_stamp_edge_touch_scenario_count": rejected_stamp_edge_touch_count,
    }


def signed_scenario_matches_expectation(
    result: dict[str, Any],
) -> tuple[bool | None, str | None]:
    expected_outcome = result.get("expected_outcome")
    if expected_outcome is None:
        return None, None
    signing_result = _mapping(result.get("signing_result"))
    actual_success = signing_result.get("success") is True
    if expected_outcome == "success":
        if actual_success:
            return True, None
        message = signing_result.get("message")
        return False, (
            "Expected signing success but scenario failed"
            + (f": {message}" if isinstance(message, str) and message else ".")
        )
    if expected_outcome == "validation_rejection":
        if actual_success:
            return False, "Expected an intentional validation rejection but signing succeeded."
        fragment = result.get("expected_failure_message_contains")
        if isinstance(fragment, str) and fragment:
            message = signing_result.get("message")
            if not isinstance(message, str) or fragment not in message:
                return (
                    False,
                    f"Expected rejection message to contain {fragment!r}, got {message!r}.",
                )
        return True, None
    return False, f"Unsupported expected_outcome: {expected_outcome!r}"


def signed_matrix_diagnostic_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    cryptographic_failures = 0
    preview_output_failures = 0
    annotation_rect_mismatches = 0
    sign_success_count = 0
    expected_success_count = 0
    expected_rejection_count = 0
    matched_expected_success_count = 0
    matched_expected_rejection_count = 0
    expected_outcome_mismatch_count = 0
    expectation_errors: list[str] = []
    for result in results:
        signing_result = _mapping(result.get("signing_result"))
        if signing_result.get("success") is True:
            sign_success_count += 1
        verification = _mapping(result.get("output_verification_snapshot"))
        if verification.get("cryptographic_validation_passed") is False:
            cryptographic_failures += 1
        comparison = _mapping(result.get("signed_output_preview_comparison"))
        if comparison.get("preview_vs_signed_output_passed") is False:
            preview_output_failures += 1
        if comparison.get("annotation_rect_matches_request") is False:
            annotation_rect_mismatches += 1
        expected_outcome = result.get("expected_outcome")
        if expected_outcome == "success":
            expected_success_count += 1
        elif expected_outcome == "validation_rejection":
            expected_rejection_count += 1
        matched, error = signed_scenario_matches_expectation(result)
        if matched is True:
            if expected_outcome == "success":
                matched_expected_success_count += 1
            elif expected_outcome == "validation_rejection":
                matched_expected_rejection_count += 1
        elif matched is False:
            expected_outcome_mismatch_count += 1
            expectation_errors.append(f"{result.get('name')}: {error}")
    return {
        "successful_signing_run_count": sign_success_count,
        "cryptographic_validation_failure_count": cryptographic_failures,
        "preview_output_comparison_failure_count": preview_output_failures,
        "annotation_rect_mismatch_count": annotation_rect_mismatches,
        "expected_success_scenario_count": expected_success_count,
        "expected_intentional_rejection_count": expected_rejection_count,
        "matched_expected_success_count": matched_expected_success_count,
        "matched_expected_intentional_rejection_count": matched_expected_rejection_count,
        "expected_outcome_mismatch_count": expected_outcome_mismatch_count,
        "acceptance_expectation_errors": expectation_errors,
    }


def evaluate_signed_matrix_acceptance_expectations(
    *,
    summary: dict[str, Any],
    manifest_expectations: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    if not manifest_expectations:
        return True, []
    errors: list[str] = []
    scenario_count = int(summary.get("scenario_count", 0))
    success_count = int(summary.get("successful_signing_run_count", 0))
    rejection_count = int(summary.get("matched_expected_intentional_rejection_count", 0))
    mismatch_count = int(summary.get("expected_outcome_mismatch_count", 0))
    crypto_failures = int(summary.get("cryptographic_validation_failure_count", 0))
    comparison_failures = int(summary.get("preview_output_comparison_failure_count", 0))
    annotation_mismatches = int(summary.get("annotation_rect_mismatch_count", 0))

    if "scenario_count" in manifest_expectations:
        expected = int(manifest_expectations["scenario_count"])
        if scenario_count != expected:
            errors.append(f"Expected {expected} scenarios, observed {scenario_count}.")
    if "minimum_successful_signing_run_count" in manifest_expectations:
        expected = int(manifest_expectations["minimum_successful_signing_run_count"])
        if success_count < expected:
            errors.append(
                f"Expected at least {expected} successful signings, observed {success_count}."
            )
    if "expected_intentional_rejection_count" in manifest_expectations:
        expected = int(manifest_expectations["expected_intentional_rejection_count"])
        if rejection_count != expected:
            errors.append(
                f"Expected {expected} intentional rejections, observed {rejection_count}."
            )
    if manifest_expectations.get("require_zero_cryptographic_validation_failures") is True:
        if crypto_failures != 0:
            errors.append(
                f"Expected zero cryptographic validation failures, observed {crypto_failures}."
            )
    if manifest_expectations.get("require_zero_preview_output_comparison_failures") is True:
        if comparison_failures != 0:
            errors.append(
                f"Expected zero preview/output comparison failures, observed {comparison_failures}."
            )
    if manifest_expectations.get("require_zero_annotation_rect_mismatches") is True:
        if annotation_mismatches != 0:
            errors.append(
                f"Expected zero annotation rect mismatches, observed {annotation_mismatches}."
            )
    if mismatch_count != 0:
        errors.append(
            f"Expected zero per-scenario expectation mismatches, observed {mismatch_count}."
        )
    return not errors, errors
