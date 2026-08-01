"""Effect boundaries used by the Phase 3 evidence application service."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import AbstractContextManager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation

if TYPE_CHECKING:
    from foliaseal.application.phase3_evidence_service import (
        Phase3HarnessCaptureRequest,
        Phase3MatrixRequest,
    )
    from foliaseal.application.qa_signed_acceptance_generation import (
        GeneratedSignedAcceptanceAssets,
    )


class CaptureRunnerPort(Protocol):
    def __call__(self, request: Phase3HarnessCaptureRequest) -> CaptureResultPort: ...


class CaptureResultPort(Protocol):
    """Qt-free minimum contract for the structured capture payload."""

    def to_json(self) -> str: ...


class MatrixRunnerPort(Protocol):
    def __call__(self, request: Phase3MatrixRequest) -> Mapping[str, Any]: ...


class AssetGeneratorPort(Protocol):
    def __call__(self, *, root: Path) -> GeneratedSignedAcceptanceAssets: ...


class CaptureContractEvaluatorPort(Protocol):
    def __call__(self, payload: Mapping[str, Any]) -> EvidenceContractEvaluation: ...


class CaptureLoaderPort(Protocol):
    def __call__(self, path: Path) -> Mapping[str, Any]: ...


class TextWriterPort(Protocol):
    def __call__(self, path: Path, text: str) -> None: ...


class MatrixRuntimeContextPort(Protocol):
    def __call__(self, name: str) -> AbstractContextManager[None]: ...
