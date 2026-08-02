"""Application-owned orchestration boundary for Phase 3 evidence operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from foliaseal.application.phase3_evidence_ports import CaptureResultPort
from foliaseal.application.phase3_evidence_service import (
    Phase3HarnessCaptureRequest,
    Phase3HarnessValidationRequest,
    Phase3MatrixRequest,
    Phase3MatrixResult,
    Phase3SignedAcceptanceEvidenceRequest,
    Phase3SignedAcceptanceEvidenceResult,
)
from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation


class Phase3EvidenceServicePort(Protocol):
    """Service behaviors required by the application orchestrator."""

    def capture_harness(self, request: Phase3HarnessCaptureRequest) -> CaptureResultPort:
        """Capture one interactive harness run."""

    def preview_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult:
        """Run and normalize one preview matrix."""

    def signed_acceptance_matrix_result(
        self,
        request: Phase3MatrixRequest,
    ) -> Phase3MatrixResult:
        """Run and normalize one signed-acceptance matrix."""

    def run_signed_acceptance_evidence(
        self,
        request: Phase3SignedAcceptanceEvidenceRequest,
    ) -> Phase3SignedAcceptanceEvidenceResult:
        """Run aggregate signed-acceptance evidence."""

    def validate_harness_capture(
        self,
        request: Phase3HarnessValidationRequest,
    ) -> EvidenceContractEvaluation:
        """Validate one existing capture JSON file."""


@dataclass(frozen=True)
class Phase3ValidationRequest:
    """Read-only validation request kept separate from effectful operations."""

    summary_json_path: str | Path


@dataclass(frozen=True)
class Phase3EvidenceOrchestrator:
    """Deep application boundary over runner-specific Phase 3 adapters."""

    service: Phase3EvidenceServicePort

    def capture(self, request: Phase3HarnessCaptureRequest) -> CaptureResultPort:
        return self.service.capture_harness(request)

    def preview_matrix(self, request: Phase3MatrixRequest) -> Phase3MatrixResult:
        return self.service.preview_matrix_result(request)

    def signed_acceptance_matrix(self, request: Phase3MatrixRequest) -> Phase3MatrixResult:
        return self.service.signed_acceptance_matrix_result(request)

    def signed_acceptance_evidence(
        self, request: Phase3SignedAcceptanceEvidenceRequest
    ) -> Phase3SignedAcceptanceEvidenceResult:
        return self.service.run_signed_acceptance_evidence(request)

    def for_pdf(
        self,
        pdf_path: str | Path,
        *,
        certificate_path: str,
        passphrase: str,
        artifacts_dir: str = "artifacts/phase3",
    ) -> Phase3EvidenceSession:
        return Phase3EvidenceSession(
            orchestrator=self,
            pdf_path=str(pdf_path),
            certificate_path=certificate_path,
            passphrase=passphrase,
            artifacts_dir=artifacts_dir,
        )

    def validate(self, request: Phase3ValidationRequest) -> EvidenceContractEvaluation:
        """Validate a previously written capture through the service boundary."""

        return self.service.validate_harness_capture(
            Phase3HarnessValidationRequest(summary_json_path=request.summary_json_path)
        )

def orchestrator_for_service(
    service: Phase3EvidenceServicePort,
) -> Phase3EvidenceOrchestrator:
    """Build the application orchestrator for the default service composition."""

    return Phase3EvidenceOrchestrator(service)


@dataclass(frozen=True)
class Phase3EvidenceSession:
    """Document-bound convenience object without a compatibility gateway."""

    orchestrator: Phase3EvidenceOrchestrator
    pdf_path: str
    certificate_path: str
    passphrase: str
    artifacts_dir: str = "artifacts/phase3"

    def preview(
        self, manifest_path: str | Path, *, artifacts_dir: str | None = None
    ) -> Phase3MatrixResult:
        return self.orchestrator.preview_matrix(
            Phase3MatrixRequest(
                pdf_path=self.pdf_path,
                certificate_path=self.certificate_path,
                passphrase=self.passphrase,
                scenario_manifest_path=str(manifest_path),
                artifacts_dir=artifacts_dir or self.artifacts_dir,
            )
        )

    def signed_acceptance(
        self, manifest_path: str | Path, *, artifacts_dir: str | None = None
    ) -> Phase3MatrixResult:
        return self.orchestrator.signed_acceptance_matrix(
            Phase3MatrixRequest(
                pdf_path=self.pdf_path,
                certificate_path=self.certificate_path,
                passphrase=self.passphrase,
                scenario_manifest_path=str(manifest_path),
                artifacts_dir=artifacts_dir or self.artifacts_dir,
            )
        )

    def capture(
        self,
        *,
        summary_json_path: str | Path | None = None,
        checklist_results_path: str = "artifacts/phase3_fr3b_acceptance_results.md",
        checklist_template_path: str = "artifacts/phase3_fr3b_acceptance_checklist.md",
        artifacts_dir: str | None = None,
    ) -> CaptureResultPort:
        return self.orchestrator.capture(
            Phase3HarnessCaptureRequest(
                pdf_path=self.pdf_path,
                certificate_path=self.certificate_path,
                passphrase=self.passphrase,
                summary_json_path=None if summary_json_path is None else str(summary_json_path),
                checklist_results_path=str(checklist_results_path),
                checklist_template_path=str(checklist_template_path),
                artifacts_dir=artifacts_dir or self.artifacts_dir,
            )
        )

    def validate(self, summary_json_path: str | Path) -> EvidenceContractEvaluation:
        return self.orchestrator.validate(Phase3ValidationRequest(summary_json_path))
