"""Reusable caller-facing gateway and session for Phase 3 evidence runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from foliaseal.application.phase3_evidence_orchestrator import (
    Phase3EvidenceOrchestrator,
    Phase3EvidenceServicePort,
    Phase3OperationKind,
    Phase3OperationPayload,
    Phase3OperationRequest,
    Phase3ValidationRequest,
    orchestrator_for_service,
)
from foliaseal.application.phase3_evidence_service import (
    Phase3EvidenceService,
    Phase3HarnessCaptureRequest,
    Phase3HarnessValidationRequest,
    Phase3MatrixRequest,
    Phase3MatrixResult,
    Phase3SignedAcceptanceEvidenceRequest,
    Phase3SignedAcceptanceEvidenceResult,
)
from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation

__all__ = [
    "DEFAULT_PHASE3_ARTIFACTS_DIR",
    "DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH",
    "DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH",
    "Phase3EvidenceGateway",
    "Phase3EvidenceOrchestrator",
    "Phase3EvidenceSession",
    "Phase3EvidenceServicePort",
    "Phase3HarnessValidationRequest",
    "Phase3OperationKind",
    "Phase3OperationPayload",
    "Phase3OperationRequest",
    "Phase3SignedAcceptanceEvidenceRequest",
    "Phase3SignedAcceptanceEvidenceResult",
    "Phase3ValidationRequest",
    "gateway_for_service",
]

DEFAULT_PHASE3_ARTIFACTS_DIR = "artifacts/phase3"
DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH = "artifacts/phase3_fr3b_acceptance_results.md"
DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH = "artifacts/phase3_fr3b_acceptance_checklist.md"


@dataclass(frozen=True)
class Phase3EvidenceGateway:
    """Compatibility gateway over the application evidence orchestrator."""

    service: Phase3EvidenceServicePort

    def run(self, request: Phase3OperationRequest) -> object:
        """Dispatch through the application-owned orchestration boundary."""

        return orchestrator_for_service(self.service).run(request)

    def validate(self, request: Phase3ValidationRequest) -> EvidenceContractEvaluation:
        """Validate a previously written capture through the service boundary."""

        return orchestrator_for_service(self.service).validate(request)

    def for_pdf(
        self,
        pdf_path: str | Path,
        *,
        certificate_path: str,
        passphrase: str,
        artifacts_dir: str = DEFAULT_PHASE3_ARTIFACTS_DIR,
    ) -> Phase3EvidenceSession:
        """Bind document credentials once for repeated evidence operations."""

        return Phase3EvidenceSession(
            gateway=self,
            pdf_path=str(pdf_path),
            certificate_path=certificate_path,
            passphrase=passphrase,
            artifacts_dir=artifacts_dir,
        )


@dataclass(frozen=True)
class Phase3EvidenceSession:
    """Document-bound convenience facade for common Phase 3 callers."""

    gateway: Phase3EvidenceGateway
    pdf_path: str
    certificate_path: str
    passphrase: str
    artifacts_dir: str = DEFAULT_PHASE3_ARTIFACTS_DIR

    def preview(
        self,
        manifest_path: str | Path,
        *,
        artifacts_dir: str | None = None,
    ) -> Phase3MatrixResult:
        request = Phase3MatrixRequest(
            pdf_path=self.pdf_path,
            certificate_path=self.certificate_path,
            passphrase=self.passphrase,
            scenario_manifest_path=str(manifest_path),
            artifacts_dir=artifacts_dir or self.artifacts_dir,
        )
        result = self.gateway.run(Phase3OperationRequest.preview_matrix(request))
        if not isinstance(result, Phase3MatrixResult):
            raise TypeError("Preview matrix gateway returned an unexpected result type")
        return result

    def signed_acceptance(
        self,
        manifest_path: str | Path,
        *,
        artifacts_dir: str | None = None,
    ) -> Phase3MatrixResult:
        request = Phase3MatrixRequest(
            pdf_path=self.pdf_path,
            certificate_path=self.certificate_path,
            passphrase=self.passphrase,
            scenario_manifest_path=str(manifest_path),
            artifacts_dir=artifacts_dir or self.artifacts_dir,
        )
        result = self.gateway.run(
            Phase3OperationRequest.signed_acceptance_matrix(request)
        )
        if not isinstance(result, Phase3MatrixResult):
            raise TypeError("Signed acceptance gateway returned an unexpected result type")
        return result

    def capture(
        self,
        *,
        summary_json_path: str | Path | None = None,
        checklist_results_path: str | Path = DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
        checklist_template_path: str | Path = DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
        artifacts_dir: str | None = None,
    ) -> object:
        request = Phase3HarnessCaptureRequest(
            pdf_path=self.pdf_path,
            certificate_path=self.certificate_path,
            passphrase=self.passphrase,
            summary_json_path=(
                None if summary_json_path is None else str(summary_json_path)
            ),
            checklist_results_path=str(checklist_results_path),
            checklist_template_path=str(checklist_template_path),
            artifacts_dir=artifacts_dir or self.artifacts_dir,
        )
        return self.gateway.run(Phase3OperationRequest.capture(request))

    def validate(self, summary_json_path: str | Path) -> EvidenceContractEvaluation:
        """Validate a capture produced for this session."""

        return self.gateway.validate(Phase3ValidationRequest(summary_json_path))


def gateway_for_service(service: Phase3EvidenceService) -> Phase3EvidenceGateway:
    """Adapt the concrete service without exposing its runner dependencies."""

    return Phase3EvidenceGateway(service)
