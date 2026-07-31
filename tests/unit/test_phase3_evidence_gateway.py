from __future__ import annotations

from contextlib import nullcontext

import pytest

from foliaseal.application.phase3_evidence_gateway import (
    DEFAULT_PHASE3_ARTIFACTS_DIR,
    DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
    DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
    Phase3EvidenceGateway,
    Phase3OperationKind,
    Phase3OperationRequest,
    Phase3ValidationRequest,
)
from foliaseal.application.phase3_evidence_service import (
    Phase3EvidenceService,
    Phase3HarnessCaptureRequest,
    Phase3HarnessValidationRequest,
    Phase3MatrixKind,
    Phase3MatrixRequest,
    Phase3MatrixResult,
    Phase3SignedAcceptanceEvidenceRequest,
)


class _FakeService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        self.capture_result = object()
        self.preview_result = object()
        self.signed_result = object()
        self.evidence_result = object()
        self.validation_result = object()

    def capture_harness(self, request):
        self.calls.append(("capture", request))
        return self.capture_result

    def preview_matrix_result(self, request):
        self.calls.append(("preview", request))
        return self.preview_result

    def signed_acceptance_matrix_result(self, request):
        self.calls.append(("signed", request))
        return self.signed_result

    def run_signed_acceptance_evidence(self, request):
        self.calls.append(("evidence", request))
        return self.evidence_result

    def validate_harness_capture(self, request):
        self.calls.append(("validate", request))
        return self.validation_result


def _capture_request() -> Phase3HarnessCaptureRequest:
    return Phase3HarnessCaptureRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        summary_json_path="capture.json",
        checklist_results_path="results.md",
        checklist_template_path="template.md",
        artifacts_dir="artifacts/capture",
    )


def _matrix_request() -> Phase3MatrixRequest:
    return Phase3MatrixRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        scenario_manifest_path="manifest.json",
        artifacts_dir="artifacts/matrix",
    )


def test_gateway_dispatches_each_operation_to_the_existing_service() -> None:
    service = _FakeService()
    gateway = Phase3EvidenceGateway(service)

    assert (
        gateway.run(Phase3OperationRequest.capture(_capture_request()))
        is service.capture_result
    )
    assert (
        gateway.run(Phase3OperationRequest.preview_matrix(_matrix_request()))
        is service.preview_result
    )
    assert (
        gateway.run(Phase3OperationRequest.signed_acceptance_matrix(_matrix_request()))
        is service.signed_result
    )
    assert gateway.run(
        Phase3OperationRequest.signed_acceptance_evidence(
            Phase3SignedAcceptanceEvidenceRequest(passphrase="secret")
        )
    ) is service.evidence_result
    assert gateway.validate(Phase3ValidationRequest("capture.json")) is service.validation_result

    assert [name for name, _request in service.calls] == [
        "capture",
        "preview",
        "signed",
        "evidence",
        "validate",
    ]
    assert isinstance(service.calls[-1][1], Phase3HarnessValidationRequest)
    assert service.calls[-1][1].summary_json_path == "capture.json"


def test_gateway_rejects_an_operation_and_payload_with_different_kinds() -> None:
    gateway = Phase3EvidenceGateway(_FakeService())
    request = Phase3OperationRequest(
        kind=Phase3OperationKind.PREVIEW_MATRIX,
        payload=_capture_request(),
    )

    with pytest.raises(TypeError, match="PREVIEW_MATRIX requires"):
        gateway.run(request)


def test_session_reuses_document_inputs_and_resolves_artifact_defaults() -> None:
    service = _FakeService()
    service.preview_result = Phase3MatrixResult(
        kind=Phase3MatrixKind.PREVIEW,
        summary={},
        passed=True,
        artifacts_dir=DEFAULT_PHASE3_ARTIFACTS_DIR,
        summary_json_path="artifacts/phase3/summary.json",
        scenario_count=0,
        successful_run_count=0,
        errors=(),
        warnings=(),
    )
    service.signed_result = Phase3MatrixResult(
        kind=Phase3MatrixKind.SIGNED_ACCEPTANCE,
        summary={},
        passed=True,
        artifacts_dir="artifacts/signed",
        summary_json_path="artifacts/signed/summary.json",
        scenario_count=0,
        successful_run_count=0,
        errors=(),
        warnings=(),
    )
    session = Phase3EvidenceGateway(service).for_pdf(
        "input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
    )

    assert session.preview("preview.json") is service.preview_result
    assert (
        session.signed_acceptance(
            "signed.json",
            artifacts_dir="artifacts/signed",
        )
        is service.signed_result
    )
    assert session.capture() is service.capture_result
    assert session.validate("capture.json") is service.validation_result

    preview_request = service.calls[0][1]
    signed_request = service.calls[1][1]
    capture_request = service.calls[2][1]
    assert preview_request == Phase3MatrixRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        scenario_manifest_path="preview.json",
        artifacts_dir=DEFAULT_PHASE3_ARTIFACTS_DIR,
    )
    assert signed_request.artifacts_dir == "artifacts/signed"
    assert capture_request == Phase3HarnessCaptureRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        summary_json_path=None,
        checklist_results_path=DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
        checklist_template_path=DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
        artifacts_dir=DEFAULT_PHASE3_ARTIFACTS_DIR,
    )


def test_service_for_pdf_returns_gateway_session_without_changing_legacy_methods() -> None:
    service = Phase3EvidenceService(
        harness_runner=lambda request: request,
        preview_matrix_runner=lambda request: {
            "artifacts_dir": request.artifacts_dir,
            "scenario_count": 1,
            "successful_scenario_count": 1,
            "error_scenario_count": 0,
        },
        signed_acceptance_matrix_runner=lambda request: {
            "artifacts_dir": request.artifacts_dir,
            "scenario_count": 1,
            "successful_signing_run_count": 1,
            "acceptance_expectations_passed": True,
            "acceptance_expectation_errors": [],
            "expected_outcome_mismatch_count": 0,
            "cryptographic_validation_failure_count": 0,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
        },
        asset_generator=lambda **_kwargs: None,
        capture_contract_evaluator=lambda _payload: None,
        text_writer=lambda _path, _text: None,
        matrix_runtime_context_factory=lambda _name: nullcontext(),
    )

    session = service.for_pdf(
        "input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
    )
    result = session.preview("preview.json")

    assert result.kind is Phase3MatrixKind.PREVIEW
    assert result.artifacts_dir == DEFAULT_PHASE3_ARTIFACTS_DIR
    assert service.run_preview_matrix(
        Phase3MatrixRequest(
            pdf_path="input.pdf",
            certificate_path="cert.p12",
            passphrase="secret",
            scenario_manifest_path="legacy.json",
            artifacts_dir="legacy-artifacts",
        )
    )["artifacts_dir"] == "legacy-artifacts"
