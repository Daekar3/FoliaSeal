"""Application-owned evidence program with explicit operation verbs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from foliaseal.application.evidence_ports import CaptureResultPort
from foliaseal.application.evidence_service import (
    EvidenceCaptureRequest,
    EvidenceMatrixRequest,
    EvidenceMatrixResult,
    EvidenceServiceValidationRequest,
    SignedAcceptanceEvidenceRequest,
    SignedAcceptanceEvidenceResult,
)
from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation


class EvidenceProgramServicePort(Protocol):
    """Service behaviors required by the evidence program."""

    def capture(self, request: EvidenceCaptureRequest) -> CaptureResultPort:
        """Capture one interactive harness run."""

    def preview_matrix(self, request: EvidenceMatrixRequest) -> EvidenceMatrixResult:
        """Run and normalize one preview matrix."""

    def signed_acceptance_matrix(
        self,
        request: EvidenceMatrixRequest,
    ) -> EvidenceMatrixResult:
        """Run and normalize one signed-acceptance matrix."""

    def signed_acceptance_evidence(
        self,
        request: SignedAcceptanceEvidenceRequest,
    ) -> SignedAcceptanceEvidenceResult:
        """Run aggregate signed-acceptance evidence."""

    def validate(
        self,
        request: EvidenceServiceValidationRequest,
    ) -> EvidenceContractEvaluation:
        """Validate one existing capture JSON file."""


@dataclass(frozen=True)
class EvidenceValidationRequest:
    """Read-only validation request kept separate from effectful operations."""

    summary_json_path: str | Path


@dataclass(frozen=True)
class EvidenceProgram:
    """Deep application boundary over runner-specific Acceptance adapters."""

    service: EvidenceProgramServicePort

    def capture(self, request: EvidenceCaptureRequest) -> CaptureResultPort:
        return self.service.capture(request)

    def preview_matrix(self, request: EvidenceMatrixRequest) -> EvidenceMatrixResult:
        return self.service.preview_matrix(request)

    def signed_acceptance_matrix(self, request: EvidenceMatrixRequest) -> EvidenceMatrixResult:
        return self.service.signed_acceptance_matrix(request)

    def signed_acceptance_evidence(
        self, request: SignedAcceptanceEvidenceRequest
    ) -> SignedAcceptanceEvidenceResult:
        return self.service.signed_acceptance_evidence(request)

    def for_pdf(
        self,
        pdf_path: str | Path,
        *,
        certificate_path: str,
        passphrase: str,
        artifacts_dir: str = "artifacts/acceptance",
    ) -> EvidenceSession:
        return EvidenceSession(
            program=self,
            pdf_path=str(pdf_path),
            certificate_path=certificate_path,
            passphrase=passphrase,
            artifacts_dir=artifacts_dir,
        )

    def validate(self, request: EvidenceValidationRequest) -> EvidenceContractEvaluation:
        """Validate a previously written capture through the service boundary."""

        return self.service.validate(
            EvidenceServiceValidationRequest(summary_json_path=request.summary_json_path)
        )

def program_for_service(
    service: EvidenceProgramServicePort,
) -> EvidenceProgram:
    """Build the evidence program for the default service composition."""

    return EvidenceProgram(service)


@dataclass(frozen=True)
class EvidenceSession:
    """Document-bound convenience object without a compatibility gateway."""

    program: EvidenceProgram
    pdf_path: str
    certificate_path: str
    passphrase: str
    artifacts_dir: str = "artifacts/acceptance"

    def preview(
        self, manifest_path: str | Path, *, artifacts_dir: str | None = None
    ) -> EvidenceMatrixResult:
        return self.program.preview_matrix(
            EvidenceMatrixRequest(
                pdf_path=self.pdf_path,
                certificate_path=self.certificate_path,
                passphrase=self.passphrase,
                scenario_manifest_path=str(manifest_path),
                artifacts_dir=artifacts_dir or self.artifacts_dir,
            )
        )

    def signed_acceptance(
        self, manifest_path: str | Path, *, artifacts_dir: str | None = None
    ) -> EvidenceMatrixResult:
        return self.program.signed_acceptance_matrix(
            EvidenceMatrixRequest(
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
        checklist_results_path: str = "artifacts/acceptance_fr3b_acceptance_results.md",
        checklist_template_path: str = "artifacts/acceptance_fr3b_acceptance_checklist.md",
        artifacts_dir: str | None = None,
    ) -> CaptureResultPort:
        return self.program.capture(
            EvidenceCaptureRequest(
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
        return self.program.validate(EvidenceValidationRequest(summary_json_path))
