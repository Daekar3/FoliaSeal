from pathlib import Path

import pytest

from foliaseal.application.qa_signed_acceptance_generation import (
    GeneratedSignedAcceptanceAssets,
)
from foliaseal.presentation.qt.phase3_signed_acceptance_evidence import (
    run_signed_acceptance_evidence,
    validate_signed_acceptance_matrix_summary,
)


def _assets(root: Path) -> GeneratedSignedAcceptanceAssets:
    return GeneratedSignedAcceptanceAssets(
        fixture_pdf=root / "artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf",
        identity_p12=root / "artifacts/generated_acceptance_assets/signed_acceptance_identity.p12",
        stamp_image=root / "artifacts/generated_acceptance_assets/signed_acceptance_stamp.png",
        signed_acceptance_manifest=(
            root / "artifacts/preview_sweep_assets/signed_acceptance_matrix.json"
        ),
        signed_preview_parity_manifest=(
            root / "artifacts/preview_sweep_assets/signed_preview_parity_matrix.json"
        ),
        signed_fit_rejection_manifest=(
            root / "artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json"
        ),
    )


def _passing_summary(*, artifacts_dir: str, scenario_count: int = 3) -> dict[str, object]:
    return {
        "acceptance_expectations_passed": True,
        "scenario_count": scenario_count,
        "successful_signing_run_count": scenario_count,
        "matched_expected_intentional_rejection_count": 0,
        "expected_outcome_mismatch_count": 0,
        "cryptographic_validation_failure_count": 0,
        "preview_output_comparison_failure_count": 0,
        "annotation_rect_mismatch_count": 0,
        "artifacts_dir": artifacts_dir,
    }


def test_run_signed_acceptance_evidence_generates_assets_runs_three_matrices_and_writes_summary(
    tmp_path: Path,
) -> None:
    generated_roots: list[Path] = []
    matrix_calls: list[dict[str, str]] = []

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        generated_roots.append(root)
        return _assets(root)

    def fake_matrix_runner(**kwargs: str) -> dict[str, object]:
        matrix_calls.append(kwargs)
        return _passing_summary(artifacts_dir=kwargs["artifacts_dir"])

    evidence = run_signed_acceptance_evidence(
        artifacts_root=tmp_path,
        asset_generator=fake_asset_generator,
        matrix_runner=fake_matrix_runner,
    )

    assert generated_roots == [tmp_path]
    assert [Path(call["scenario_manifest_path"]).name for call in matrix_calls] == [
        "signed_acceptance_matrix.json",
        "signed_preview_parity_matrix.json",
        "signed_fit_rejection_matrix.json",
    ]
    assert evidence["passed"] is True
    summary_path = Path(evidence["summary_markdown_path"])
    assert summary_path == tmp_path / "artifacts/phase3_signed_acceptance_evidence_summary.md"
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Overall result: PASS" in summary_text
    assert "signed_acceptance_matrix" in summary_text
    assert "signed_preview_parity_matrix" in summary_text
    assert "signed_fit_rejection_matrix" in summary_text


def test_run_signed_acceptance_evidence_writes_failure_summary_and_raises(
    tmp_path: Path,
) -> None:
    call_count = 0

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(**kwargs: str) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        summary = _passing_summary(artifacts_dir=kwargs["artifacts_dir"])
        if call_count == 2:
            summary["preview_output_comparison_failure_count"] = 1
            summary["acceptance_expectations_passed"] = False
            summary["acceptance_expectation_errors"] = [
                "Expected zero preview/output comparison failures, observed 1."
            ]
        return summary

    with pytest.raises(RuntimeError, match="signed_preview_parity_matrix"):
        run_signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    summary_path = tmp_path / "artifacts/phase3_signed_acceptance_evidence_summary.md"
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Overall result: FAIL" in summary_text
    assert "expected preview_output_comparison_failure_count=0, observed 1" in summary_text
    assert "Expected zero preview/output comparison failures, observed 1." in summary_text
    assert "Preview/output comparison failures: 1" in summary_text


def test_run_signed_acceptance_evidence_writes_failure_summary_when_matrix_raises(
    tmp_path: Path,
) -> None:
    call_count = 0

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(**kwargs: str) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Qt renderer unavailable")
        return _passing_summary(artifacts_dir=kwargs["artifacts_dir"])

    with pytest.raises(RuntimeError, match="Qt renderer unavailable"):
        run_signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    summary_path = tmp_path / "artifacts/phase3_signed_acceptance_evidence_summary.md"
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Overall result: FAIL" in summary_text
    assert (
        "matrix runner failed before returning a summary: Qt renderer unavailable"
        in summary_text
    )


def test_validate_signed_acceptance_matrix_summary_rejects_missing_counter() -> None:
    summary = _passing_summary(artifacts_dir="artifacts/run")
    del summary["annotation_rect_mismatch_count"]

    errors = validate_signed_acceptance_matrix_summary(
        name="signed_acceptance_matrix",
        summary=summary,
    )

    assert errors == [
        "signed_acceptance_matrix: Matrix summary missing integer counter "
        "'annotation_rect_mismatch_count'."
    ]
