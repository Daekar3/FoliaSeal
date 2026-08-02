from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.evidence_program import (
    EvidenceProgram,
    EvidenceValidationRequest,
)
from foliaseal.application.evidence_service import (
    EvidenceCaptureRequest,
    EvidenceMatrixRequest,
    EvidenceServiceValidationRequest,
    SignedAcceptanceEvidenceRequest,
)


@dataclass
class _FakeService:
    calls: list[tuple[str, object]]

    def capture(self, request):
        self.calls.append(("capture", request))
        return "capture-result"

    def preview_matrix(self, request):
        self.calls.append(("preview", request))
        return "preview-result"

    def signed_acceptance_matrix(self, request):
        self.calls.append(("signed", request))
        return "signed-result"

    def signed_acceptance_evidence(self, request):
        self.calls.append(("evidence", request))
        return "evidence-result"

    def validate(self, request):
        self.calls.append(("validate", request))
        return "validation-result"


def _capture_request() -> EvidenceCaptureRequest:
    return EvidenceCaptureRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        summary_json_path="capture.json",
        checklist_results_path="results.md",
        checklist_template_path="template.md",
        artifacts_dir="artifacts/capture",
    )


def _matrix_request() -> EvidenceMatrixRequest:
    return EvidenceMatrixRequest(
        pdf_path="input.pdf",
        certificate_path="cert.p12",
        passphrase="secret",
        scenario_manifest_path="manifest.json",
        artifacts_dir="artifacts/matrix",
    )


def test_orchestrator_exposes_explicit_effectful_verbs() -> None:
    service = _FakeService([])
    orchestrator = EvidenceProgram(service)

    assert orchestrator.capture(_capture_request()) == "capture-result"
    assert orchestrator.preview_matrix(_matrix_request()) == "preview-result"
    assert orchestrator.signed_acceptance_matrix(_matrix_request()) == "signed-result"
    assert orchestrator.signed_acceptance_evidence(
        SignedAcceptanceEvidenceRequest(passphrase="secret")
    ) == "evidence-result"

    assert [name for name, _request in service.calls] == [
        "capture",
        "preview",
        "signed",
        "evidence",
    ]

def test_orchestrator_validates_through_the_service_boundary() -> None:
    service = _FakeService([])

    result = EvidenceProgram(service).validate(EvidenceValidationRequest("capture.json"))

    assert result == "validation-result"
    assert service.calls == [
        (
            "validate",
            EvidenceServiceValidationRequest(summary_json_path="capture.json"),
        )
    ]
