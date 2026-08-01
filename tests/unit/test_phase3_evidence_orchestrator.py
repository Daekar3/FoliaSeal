from __future__ import annotations

from dataclasses import dataclass

import pytest

from foliaseal.application.phase3_evidence_orchestrator import (
    Phase3EvidenceOrchestrator,
    Phase3OperationKind,
    Phase3OperationRequest,
    Phase3ValidationRequest,
)
from foliaseal.application.phase3_evidence_service import (
    Phase3HarnessCaptureRequest,
    Phase3HarnessValidationRequest,
    Phase3MatrixRequest,
    Phase3SignedAcceptanceEvidenceRequest,
)


@dataclass
class _FakeService:
    calls: list[tuple[str, object]]

    def capture_harness(self, request):
        self.calls.append(("capture", request))
        return "capture-result"

    def preview_matrix_result(self, request):
        self.calls.append(("preview", request))
        return "preview-result"

    def signed_acceptance_matrix_result(self, request):
        self.calls.append(("signed", request))
        return "signed-result"

    def run_signed_acceptance_evidence(self, request):
        self.calls.append(("evidence", request))
        return "evidence-result"

    def validate_harness_capture(self, request):
        self.calls.append(("validate", request))
        return "validation-result"


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


def test_orchestrator_dispatches_all_effectful_operation_kinds() -> None:
    service = _FakeService([])
    orchestrator = Phase3EvidenceOrchestrator(service)

    assert orchestrator.run(Phase3OperationRequest.capture(_capture_request())) == (
        "capture-result"
    )
    assert orchestrator.run(Phase3OperationRequest.preview_matrix(_matrix_request())) == (
        "preview-result"
    )
    assert (
        orchestrator.run(Phase3OperationRequest.signed_acceptance_matrix(_matrix_request()))
        == "signed-result"
    )
    assert (
        orchestrator.run(
            Phase3OperationRequest.signed_acceptance_evidence(
                Phase3SignedAcceptanceEvidenceRequest(passphrase="secret")
            )
        )
        == "evidence-result"
    )

    assert [name for name, _request in service.calls] == [
        "capture",
        "preview",
        "signed",
        "evidence",
    ]


def test_orchestrator_validates_through_the_service_boundary() -> None:
    service = _FakeService([])

    result = Phase3EvidenceOrchestrator(service).validate(Phase3ValidationRequest("capture.json"))

    assert result == "validation-result"
    assert service.calls == [
        (
            "validate",
            Phase3HarnessValidationRequest(summary_json_path="capture.json"),
        )
    ]


def test_orchestrator_rejects_mismatched_payload_before_calling_service() -> None:
    service = _FakeService([])
    request = Phase3OperationRequest(
        kind=Phase3OperationKind.PREVIEW_MATRIX,
        payload=_capture_request(),
    )

    with pytest.raises(TypeError, match="PREVIEW_MATRIX requires"):
        Phase3EvidenceOrchestrator(service).run(request)

    assert service.calls == []
