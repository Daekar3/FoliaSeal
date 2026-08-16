from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import pytest

from foliaseal.application.evidence_core import (
    EvidenceMatrixKind,
    validate_signed_acceptance_matrix_summary,
)
from foliaseal.application.evidence_service import (
    EvidenceCaptureRequest,
    EvidenceMatrixRequest,
    EvidenceService,
    EvidenceServiceValidationRequest,
    SignedAcceptanceEvidenceRequest,
)
from foliaseal.application.qa_signed_acceptance_generation import (
    GeneratedSignedAcceptanceAssets,
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
        "error_scenario_count": 0,
        "artifacts_dir": artifacts_dir,
    }


def _service(
    *,
    harness_runner=None,
    preview_matrix_runner=None,
    signed_acceptance_matrix_runner=None,
    asset_generator=None,
    capture_contract_evaluator=None,
    text_writer=None,
    matrix_runtime_context_factory=None,
    capture_loader=None,
) -> EvidenceService:
    return EvidenceService(
        harness_runner=harness_runner or (lambda request: request),
        preview_matrix_runner=preview_matrix_runner or (lambda request: request),
        signed_acceptance_matrix_runner=signed_acceptance_matrix_runner
        or (lambda request: request),
        asset_generator=asset_generator or (lambda *, root: _assets(root)),
        capture_contract_evaluator=capture_contract_evaluator or (lambda payload: payload),
        text_writer=text_writer
        or (
            lambda path, text: (
                path.parent.mkdir(parents=True, exist_ok=True),
                path.write_text(text, encoding="utf-8"),
            )
        ),
        matrix_runtime_context_factory=matrix_runtime_context_factory
        or (lambda _name: nullcontext()),
        capture_loader=capture_loader or (lambda path: {}),
    )


def test_evidence_service_forwards_capture_and_matrix_requests() -> None:
    captured: dict[str, object] = {}

    service = _service(
        harness_runner=lambda request: captured.setdefault("harness", request),
        preview_matrix_runner=lambda request: (
            captured.setdefault("preview", request)
            and {"artifacts_dir": request.artifacts_dir, "error_scenario_count": 0}
        ),
        signed_acceptance_matrix_runner=lambda request: (
            captured.setdefault("acceptance", request)
            and {
                "artifacts_dir": request.artifacts_dir,
                "acceptance_expectations_passed": True,
                "acceptance_expectation_errors": [],
                "expected_outcome_mismatch_count": 0,
                "cryptographic_validation_failure_count": 0,
                "preview_output_comparison_failure_count": 0,
                "annotation_rect_mismatch_count": 0,
            }
        ),
    )

    service.capture(
        EvidenceCaptureRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            summary_json_path="summary.json",
            checklist_results_path="results.md",
            checklist_template_path="template.md",
            artifacts_dir="artifacts",
        )
    )
    service.preview_matrix(
        EvidenceMatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="preview.json",
            artifacts_dir="artifacts/preview",
        )
    )
    service.signed_acceptance_matrix(
        EvidenceMatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="acceptance.json",
            artifacts_dir="artifacts/acceptance",
        )
    )

    assert captured == {
        "harness": EvidenceCaptureRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            summary_json_path="summary.json",
            checklist_results_path="results.md",
            checklist_template_path="template.md",
            artifacts_dir="artifacts",
        ),
        "preview": EvidenceMatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="preview.json",
            artifacts_dir="artifacts/preview",
        ),
        "acceptance": EvidenceMatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="acceptance.json",
            artifacts_dir="artifacts/acceptance",
        ),
    }


def test_evidence_service_normalizes_typed_matrix_results() -> None:
    service = _service(
        preview_matrix_runner=lambda _request: {
            "scenario_count": 2,
            "successful_scenario_count": 2,
            "error_scenario_count": 0,
            "artifacts_dir": "artifacts/preview",
        },
        signed_acceptance_matrix_runner=lambda _request: {
            "scenario_count": 2,
            "successful_signing_run_count": 2,
            "acceptance_expectations_passed": True,
            "acceptance_expectation_errors": [],
            "expected_outcome_mismatch_count": 0,
            "cryptographic_validation_failure_count": 0,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
            "artifacts_dir": "artifacts/signed",
        },
    )
    request = EvidenceMatrixRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        scenario_manifest_path="manifest.json",
        artifacts_dir="artifacts",
    )

    preview = service.preview_matrix(request)
    signed = service.signed_acceptance_matrix(request)

    assert preview.kind is EvidenceMatrixKind.PREVIEW
    assert preview.passed is True
    assert preview.summary_json_path == "artifacts/preview/summary.json"
    assert preview.successful_run_count == 2
    assert signed.kind is EvidenceMatrixKind.SIGNED_ACCEPTANCE
    assert signed.passed is True
    assert signed.summary_json_path == "artifacts/signed/summary.json"
    assert signed.successful_run_count == 2


def test_evidence_service_typed_signed_result_surfaces_counter_failures() -> None:
    service = _service(
        signed_acceptance_matrix_runner=lambda _request: {
            "scenario_count": 2,
            "successful_signing_run_count": 1,
            "acceptance_expectations_passed": False,
            "acceptance_expectation_errors": ["one mismatch"],
            "expected_outcome_mismatch_count": 1,
            "cryptographic_validation_failure_count": 0,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
            "artifacts_dir": "artifacts/signed",
        }
    )

    result = service.signed_acceptance_matrix(
        EvidenceMatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="manifest.json",
            artifacts_dir="artifacts",
        )
    )

    assert result.passed is False
    assert result.errors == ("one mismatch", "expected_outcome_mismatch_count=1")


def test_evidence_service_typed_signed_result_surfaces_scenario_errors() -> None:
    service = _service(
        signed_acceptance_matrix_runner=lambda _request: {
            **_passing_summary(artifacts_dir="artifacts/signed"),
            "error_scenario_count": 1,
        }
    )

    result = service.signed_acceptance_matrix(
        EvidenceMatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="manifest.json",
            artifacts_dir="artifacts",
        )
    )

    assert result.passed is False
    assert result.errors == ("error_scenario_count=1",)


def test_evidence_service_signed_acceptance_evidence_writes_summary(
    tmp_path: Path,
) -> None:
    matrix_calls: list[EvidenceMatrixRequest] = []
    context_names: list[str] = []

    service = _service(
        signed_acceptance_matrix_runner=lambda request: (
            matrix_calls.append(request) or _passing_summary(artifacts_dir=request.artifacts_dir)
        ),
        matrix_runtime_context_factory=lambda name: context_names.append(name) or nullcontext(),
    )

    result = service.signed_acceptance_evidence(
        SignedAcceptanceEvidenceRequest(
            artifacts_root=tmp_path,
            summary_markdown_path=tmp_path / "artifacts/summary.md",
            passphrase="secret",
            required_manifests=("parity.json", "rejection.json"),
        )
    )

    assert [Path(call.scenario_manifest_path).name for call in matrix_calls] == [
        "signed_preview_parity_matrix.json",
        "signed_fit_rejection_matrix.json",
    ]
    assert context_names == [
        "signed_preview_parity_matrix",
        "signed_fit_rejection_matrix",
    ]
    assert result.passed is True
    assert result.required_manifests == ("parity.json", "rejection.json")
    summary_text = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    assert "Overall result: PASS" in summary_text
    assert "signed_acceptance_matrix" not in summary_text
    assert "signed_fit_rejection_matrix" in summary_text


def test_evidence_service_strict_gate_never_runs_mixed_diagnostic_manifest(
    tmp_path: Path,
) -> None:
    matrix_calls: list[EvidenceMatrixRequest] = []

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        matrix_calls.append(request)
        if Path(request.scenario_manifest_path).name == "signed_acceptance_matrix.json":
            raise AssertionError("mixed diagnostic manifest must not run in strict evidence")
        return _passing_summary(artifacts_dir=request.artifacts_dir)

    result = _service(
        signed_acceptance_matrix_runner=fake_matrix_runner
    ).signed_acceptance_evidence(
        SignedAcceptanceEvidenceRequest(
            artifacts_root=tmp_path,
            summary_markdown_path=tmp_path / "artifacts/summary.md",
            passphrase="secret",
        )
    )

    assert result.passed is True
    assert [Path(call.scenario_manifest_path).name for call in matrix_calls] == [
        "signed_preview_parity_matrix.json",
        "signed_fit_rejection_matrix.json",
    ]


def test_evidence_service_aggregate_preserves_runner_summary_path(
    tmp_path: Path,
) -> None:
    custom_summary_path = str(tmp_path / "custom" / "authoritative-summary.json")

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        return {
            **_passing_summary(artifacts_dir=request.artifacts_dir),
            "summary_json_path": custom_summary_path,
        }

    service = _service(signed_acceptance_matrix_runner=fake_matrix_runner)

    result = service.signed_acceptance_evidence(
        SignedAcceptanceEvidenceRequest(
            artifacts_root=tmp_path,
            summary_markdown_path=tmp_path / "artifacts/summary.md",
            passphrase="secret",
        )
    )

    assert all(row.summary_json_path == custom_summary_path for row in result.matrix_results)


def test_evidence_service_writes_failure_summary_before_raising(
    tmp_path: Path,
) -> None:
    call_count = 0

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        summary = _passing_summary(artifacts_dir=request.artifacts_dir)
        if call_count == 1:
            summary["preview_output_comparison_failure_count"] = 1
            summary["acceptance_expectations_passed"] = False
            summary["acceptance_expectation_errors"] = [
                "Expected zero preview/output comparison failures, observed 1."
            ]
        return summary

    service = _service(signed_acceptance_matrix_runner=fake_matrix_runner)

    with pytest.raises(RuntimeError, match="signed_preview_parity_matrix"):
        service.signed_acceptance_evidence(
            SignedAcceptanceEvidenceRequest(
                artifacts_root=tmp_path,
                summary_markdown_path=tmp_path / "artifacts/summary.md",
                passphrase="secret",
            )
        )

    summary_text = (tmp_path / "artifacts/summary.md").read_text(encoding="utf-8")
    assert "Overall result: FAIL" in summary_text
    assert "expected preview_output_comparison_failure_count=0, observed 1" in summary_text


def test_evidence_service_validate_loads_payload(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text('{"contract_version": "evidence.v1"}', encoding="utf-8")
    captured: dict[str, object] = {}

    service = _service(
        capture_loader=lambda path: {"loaded_from": str(path)},
        capture_contract_evaluator=lambda payload: captured.setdefault("payload", payload) or None,
    )

    result = service.validate(
        EvidenceServiceValidationRequest(summary_json_path=summary_path)
    )

    assert captured == {"payload": {"loaded_from": str(summary_path)}}
    assert result == {"loaded_from": str(summary_path)}


def test_validate_signed_acceptance_matrix_summary_rejects_missing_counter() -> None:
    summary = _passing_summary(artifacts_dir="artifacts/run")
    del summary["annotation_rect_mismatch_count"]

    errors = validate_signed_acceptance_matrix_summary(
        name="signed_acceptance_matrix",
        summary=summary,
    )

    assert "signed_acceptance_matrix: Matrix summary missing integer counter" in errors[0]
