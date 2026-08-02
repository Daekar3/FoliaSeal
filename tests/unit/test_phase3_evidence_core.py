from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, get_type_hints

from foliaseal.application.phase3_evidence_core import (
    Phase3MatrixKind,
    normalize_matrix_result,
    validate_signed_acceptance_matrix_summary,
)
from foliaseal.application.phase3_evidence_orchestrator import (
    Phase3EvidenceOrchestrator,
)


def test_normalize_matrix_result_preserves_authoritative_summary_path() -> None:
    result = normalize_matrix_result(
        kind=Phase3MatrixKind.PREVIEW,
        summary={
            "artifacts_dir": "artifacts/preview",
            "summary_json_path": "authoritative/summary.json",
            "scenario_count": 4,
            "successful_scenario_count": 4,
            "error_scenario_count": 0,
        },
    )

    assert result.passed is True
    assert result.summary_json_path == "authoritative/summary.json"
    assert result.scenario_count == 4


def test_signed_summary_validation_rejects_nonzero_critical_counter() -> None:
    errors = validate_signed_acceptance_matrix_summary(
        name="signed",
        summary={
            "acceptance_expectations_passed": True,
            "expected_outcome_mismatch_count": 0,
            "cryptographic_validation_failure_count": 1,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
        },
    )

    assert errors == ["signed: expected cryptographic_validation_failure_count=0, observed 1."]


def test_evidence_application_boundary_does_not_import_heavy_render_dependencies() -> None:
    project_root = Path(__file__).parents[2]
    code = (
        "import sys; "
        "import foliaseal.application.phase3_evidence_core; "
        "import foliaseal.application.phase3_evidence_orchestrator; "
        "heavy = ('PIL', 'pyhanko', 'cryptography', 'PySide6'); "
        "assert not any("
        "any(name == root or name.startswith(root + '.') for name in sys.modules) "
        "for root in heavy)"
    )
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=project_root,
        env={"PYTHONPATH": str(project_root / "src")},
        check=True,
    )


def test_orchestrator_public_results_are_typed() -> None:
    for method in (
        Phase3EvidenceOrchestrator.capture,
        Phase3EvidenceOrchestrator.preview_matrix,
        Phase3EvidenceOrchestrator.signed_acceptance_matrix,
        Phase3EvidenceOrchestrator.signed_acceptance_evidence,
        Phase3EvidenceOrchestrator.validate,
    ):
        assert get_type_hints(method)["return"] is not Any
