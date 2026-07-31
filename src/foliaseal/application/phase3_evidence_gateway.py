"""Reusable caller-facing gateway and session for Phase 3 evidence runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, TypeAlias

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

DEFAULT_PHASE3_ARTIFACTS_DIR = "artifacts/phase3"
DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH = "artifacts/phase3_fr3b_acceptance_results.md"
DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH = "artifacts/phase3_fr3b_acceptance_checklist.md"


class Phase3EvidenceServicePort(Protocol):
    """Existing service behaviors required by the gateway."""

    def capture_harness(self, request: Phase3HarnessCaptureRequest) -> object:
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
        """Run the aggregate signed-acceptance evidence workflow."""

    def validate_harness_capture(
        self,
        request: Phase3HarnessValidationRequest,
    ) -> EvidenceContractEvaluation:
        """Validate one existing capture JSON file."""


class Phase3OperationKind(StrEnum):
    """Effectful operation kinds accepted by ``Phase3EvidenceGateway.run``."""

    CAPTURE = "capture"
    PREVIEW_MATRIX = "preview_matrix"
    SIGNED_ACCEPTANCE_MATRIX = "signed_acceptance_matrix"
    SIGNED_ACCEPTANCE_EVIDENCE = "signed_acceptance_evidence"


Phase3OperationPayload: TypeAlias = (
    Phase3HarnessCaptureRequest
    | Phase3MatrixRequest
    | Phase3SignedAcceptanceEvidenceRequest
)


@dataclass(frozen=True)
class Phase3OperationRequest:
    """Tagged request used by the gateway's effectful ``run`` entry point."""

    kind: Phase3OperationKind
    payload: Phase3OperationPayload

    @classmethod
    def capture(cls, request: Phase3HarnessCaptureRequest) -> Phase3OperationRequest:
        return cls(Phase3OperationKind.CAPTURE, request)

    @classmethod
    def preview_matrix(cls, request: Phase3MatrixRequest) -> Phase3OperationRequest:
        return cls(Phase3OperationKind.PREVIEW_MATRIX, request)

    @classmethod
    def signed_acceptance_matrix(
        cls,
        request: Phase3MatrixRequest,
    ) -> Phase3OperationRequest:
        return cls(Phase3OperationKind.SIGNED_ACCEPTANCE_MATRIX, request)

    @classmethod
    def signed_acceptance_evidence(
        cls,
        request: Phase3SignedAcceptanceEvidenceRequest,
    ) -> Phase3OperationRequest:
        return cls(Phase3OperationKind.SIGNED_ACCEPTANCE_EVIDENCE, request)


@dataclass(frozen=True)
class Phase3ValidationRequest:
    """Read-only validation request kept separate from effectful operations."""

    summary_json_path: str | Path


@dataclass(frozen=True)
class Phase3EvidenceGateway:
    """Small gateway over the existing Phase 3 evidence service."""

    service: Phase3EvidenceServicePort

    def run(self, request: Phase3OperationRequest) -> object:
        """Dispatch one tagged operation without exposing runner internals."""

        if request.kind is Phase3OperationKind.CAPTURE:
            self._require_payload(request, Phase3HarnessCaptureRequest)
            return self.service.capture_harness(request.payload)
        if request.kind is Phase3OperationKind.PREVIEW_MATRIX:
            self._require_payload(request, Phase3MatrixRequest)
            return self.service.preview_matrix_result(request.payload)
        if request.kind is Phase3OperationKind.SIGNED_ACCEPTANCE_MATRIX:
            self._require_payload(request, Phase3MatrixRequest)
            return self.service.signed_acceptance_matrix_result(request.payload)
        if request.kind is Phase3OperationKind.SIGNED_ACCEPTANCE_EVIDENCE:
            self._require_payload(request, Phase3SignedAcceptanceEvidenceRequest)
            return self.service.run_signed_acceptance_evidence(request.payload)
        raise ValueError(f"Unsupported Phase 3 operation kind: {request.kind}")

    def validate(self, request: Phase3ValidationRequest) -> EvidenceContractEvaluation:
        """Validate a previously written capture through the service boundary."""

        return self.service.validate_harness_capture(
            Phase3HarnessValidationRequest(summary_json_path=request.summary_json_path)
        )

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

    @staticmethod
    def _require_payload(
        request: Phase3OperationRequest,
        expected_type: type[Any],
    ) -> None:
        if not isinstance(request.payload, expected_type):
            raise TypeError(
                f"{request.kind.name} requires {expected_type.__name__}, "
                f"got {type(request.payload).__name__}"
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
