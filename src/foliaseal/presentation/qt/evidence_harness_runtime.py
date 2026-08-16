"""Typed, lazy evidence-harness operation composition.

The application owns the explicit evidence verbs. This module owns only the
presentation-side wiring that turns those verbs into lazy operations, keeping
Qt and rendering dependencies out of import-time construction.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from foliaseal.application.evidence_service import (
        EvidenceCaptureRequest,
        EvidenceMatrixRequest,
    )
    from foliaseal.presentation.qt.evidence_interactive_capture import (
        InteractiveHarnessCapture,
    )

class CaptureOperation(Protocol):
    """Callable contract for one lazy interactive capture operation."""

    def __call__(self, request: EvidenceCaptureRequest) -> InteractiveHarnessCapture:
        ...


class MatrixOperation(Protocol):
    """Callable contract for one lazy evidence-matrix operation."""

    def __call__(self, request: EvidenceMatrixRequest) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class EvidenceHarnessRuntime:
    """Explicit lazy operations used by the application evidence service."""

    capture_operation: CaptureOperation
    preview_matrix_operation: MatrixOperation
    signed_acceptance_matrix_operation: MatrixOperation

    def capture(self, request: EvidenceCaptureRequest) -> InteractiveHarnessCapture:
        return self.capture_operation(request)

    def preview_matrix(self, request: EvidenceMatrixRequest) -> Mapping[str, Any]:
        return self.preview_matrix_operation(request)

    def signed_acceptance_matrix(
        self,
        request: EvidenceMatrixRequest,
    ) -> Mapping[str, Any]:
        return self.signed_acceptance_matrix_operation(request)
