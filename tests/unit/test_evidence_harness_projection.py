import json
import subprocess
import sys

from foliaseal.presentation.qt.evidence_harness_projection import (
    evaluate_signed_matrix_acceptance_expectations,
    preview_matrix_diagnostic_summary,
)


def test_projection_module_is_free_of_optional_gui_dependencies() -> None:
    script = """
import json
import sys
import foliaseal.presentation.qt.evidence_harness_projection
heavy = ("PySide6", "PIL", "pyhanko")
print(json.dumps(sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)))
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == []


def test_projection_preserves_preview_counter_keys() -> None:
    summary = preview_matrix_diagnostic_summary(
        [
            {
                "preview_snapshot": {
                    "can_submit": True,
                    "render_capture": {
                        "text_content_clipped_in_preview": True,
                        "text_content_overlaps_stamp_band": False,
                        "text_content_overlaps_stamp_content": False,
                        "stamp_content_within_warning_distance": False,
                        "stamp_content_touches_band_edge": False,
                    },
                }
            }
        ]
    )
    assert summary["text_clipping_risk_scenario_count"] == 1
    assert summary["signable_text_clipping_risk_scenario_count"] == 1

    passed, errors = evaluate_signed_matrix_acceptance_expectations(
        summary={
            "scenario_count": 1,
            "successful_signing_run_count": 1,
            "matched_expected_intentional_rejection_count": 0,
            "expected_outcome_mismatch_count": 0,
            "cryptographic_validation_failure_count": 0,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
        },
        manifest_expectations={
            "scenario_count": 1,
            "minimum_successful_signing_run_count": 1,
            "expected_intentional_rejection_count": 0,
            "require_zero_cryptographic_validation_failures": True,
        },
    )
    assert passed is True
    assert errors == []
