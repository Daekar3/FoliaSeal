"""Application-owned orchestration boundary for Phase 3 evidence operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, TypeAlias

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
        """Run aggregate signed-acceptance evidence."""

    def validate_harness_capture(
        self,
        request: Phase3HarnessValidationRequest,
    ) -> EvidenceContractEvaluation:
        """Validate one existing capture JSON file."""


class Phase3OperationKind(StrEnum):
    """Effectful operations accepted by :class:`Phase3EvidenceOrchestrator`."""

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
    """Tagged request for one effectful Phase 3 evidence operation."""

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
class Phase3EvidenceOrchestrator:
    """Deep application boundary over runner-specific Phase 3 adapters."""

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


def orchestrator_for_service(
    service: Phase3EvidenceServicePort,
) -> Phase3EvidenceOrchestrator:
    """Build the application orchestrator for the default service composition."""

    return Phase3EvidenceOrchestrator(service)
