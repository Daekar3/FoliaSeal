from __future__ import annotations

from contextlib import nullcontext
from pathlib import Path

import pytest

from foliaseal.application.phase3_evidence_service import (
    Phase3EvidenceService,
    Phase3HarnessCaptureRequest,
    Phase3HarnessValidationRequest,
    Phase3MatrixRequest,
    Phase3SignedAcceptanceEvidenceRequest,
    validate_signed_acceptance_matrix_summary,
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
) -> Phase3EvidenceService:
    return Phase3EvidenceService(
        harness_runner=harness_runner or (lambda **kwargs: kwargs),
        preview_matrix_runner=preview_matrix_runner or (lambda **kwargs: kwargs),
        signed_acceptance_matrix_runner=signed_acceptance_matrix_runner
        or (lambda **kwargs: kwargs),
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


def test_phase3_evidence_service_forwards_capture_and_matrix_requests() -> None:
    captured: dict[str, object] = {}

    service = _service(
        harness_runner=lambda **kwargs: captured.setdefault("harness", kwargs),
        preview_matrix_runner=lambda **kwargs: captured.setdefault("preview", kwargs),
        signed_acceptance_matrix_runner=lambda **kwargs: captured.setdefault(
            "acceptance",
            kwargs,
        ),
    )

    service.capture_harness(
        Phase3HarnessCaptureRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            summary_json_path="summary.json",
            checklist_results_path="results.md",
            checklist_template_path="template.md",
            artifacts_dir="artifacts",
        )
    )
    service.run_preview_matrix(
        Phase3MatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="preview.json",
            artifacts_dir="artifacts/preview",
        )
    )
    service.run_signed_acceptance_matrix(
        Phase3MatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="acceptance.json",
            artifacts_dir="artifacts/acceptance",
        )
    )

    assert captured == {
        "harness": {
            "pdf_path": "input.pdf",
            "certificate_path": "cert.p12",
            "passphrase": "secret",
            "summary_json_path": "summary.json",
            "checklist_results_path": "results.md",
            "checklist_template_path": "template.md",
            "artifacts_dir": "artifacts",
        },
        "preview": {
            "pdf_path": "input.pdf",
            "certificate_path": "cert.p12",
            "passphrase": "secret",
            "scenario_manifest_path": "preview.json",
            "artifacts_dir": "artifacts/preview",
        },
        "acceptance": {
            "pdf_path": "input.pdf",
            "certificate_path": "cert.p12",
            "passphrase": "secret",
            "scenario_manifest_path": "acceptance.json",
            "artifacts_dir": "artifacts/acceptance",
        },
    }


def test_phase3_evidence_service_run_signed_acceptance_evidence_writes_summary(
    tmp_path: Path,
) -> None:
    matrix_calls: list[dict[str, str]] = []
    context_names: list[str] = []

    service = _service(
        signed_acceptance_matrix_runner=lambda **kwargs: (
            matrix_calls.append(kwargs) or _passing_summary(artifacts_dir=kwargs["artifacts_dir"])
        ),
        matrix_runtime_context_factory=lambda name: (
            context_names.append(name) or nullcontext()
        ),
    )

    result = service.run_signed_acceptance_evidence(
        Phase3SignedAcceptanceEvidenceRequest(
            artifacts_root=tmp_path,
            summary_markdown_path=tmp_path / "artifacts/summary.md",
            passphrase="secret",
            required_manifests=("a.json", "b.json", "c.json"),
        )
    )

    assert [Path(call["scenario_manifest_path"]).name for call in matrix_calls] == [
        "signed_acceptance_matrix.json",
        "signed_preview_parity_matrix.json",
        "signed_fit_rejection_matrix.json",
    ]
    assert context_names == [
        "signed_acceptance_matrix",
        "signed_preview_parity_matrix",
        "signed_fit_rejection_matrix",
    ]
    assert result.passed is True
    assert result.required_manifests == ("a.json", "b.json", "c.json")
    summary_text = Path(result.summary_markdown_path).read_text(encoding="utf-8")
    assert "Overall result: PASS" in summary_text
    assert "signed_fit_rejection_matrix" in summary_text


def test_phase3_evidence_service_writes_failure_summary_before_raising(
    tmp_path: Path,
) -> None:
    call_count = 0

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

    service = _service(signed_acceptance_matrix_runner=fake_matrix_runner)

    with pytest.raises(RuntimeError, match="signed_preview_parity_matrix"):
        service.run_signed_acceptance_evidence(
            Phase3SignedAcceptanceEvidenceRequest(
                artifacts_root=tmp_path,
                summary_markdown_path=tmp_path / "artifacts/summary.md",
                passphrase="secret",
            )
        )

    summary_text = (tmp_path / "artifacts/summary.md").read_text(encoding="utf-8")
    assert "Overall result: FAIL" in summary_text
    assert "expected preview_output_comparison_failure_count=0, observed 1" in summary_text


def test_phase3_evidence_service_validate_harness_capture_loads_payload(
    tmp_path: Path,
) -> None:
    summary_path = tmp_path / "summary.json"
    summary_path.write_text('{"contract_version": "phase3.v1"}', encoding="utf-8")
    captured: dict[str, object] = {}

    service = _service(
        capture_loader=lambda path: {"loaded_from": str(path)},
        capture_contract_evaluator=lambda payload: captured.setdefault("payload", payload)
        or None,
    )

    result = service.validate_harness_capture(
        Phase3HarnessValidationRequest(summary_json_path=summary_path)
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
