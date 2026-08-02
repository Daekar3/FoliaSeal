"""Lazy typed matrix-operation composition for evidence."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from foliaseal.application.phase3_evidence_service import Phase3MatrixRequest

MatrixOperation = Callable[[Phase3MatrixRequest], Mapping[str, Any]]
MatrixOperationFactory = Callable[[], MatrixOperation]


class _LazyMatrixOperation:
    def __init__(self, factory: MatrixOperationFactory) -> None:
        self._factory = factory
        self._operation: MatrixOperation | None = None

    def __call__(self, request: Phase3MatrixRequest) -> Mapping[str, Any]:
        if self._operation is None:
            self._operation = self._factory()
        return self._operation(request)


@dataclass(frozen=True)
class EvidenceMatrixOperations:
    """The two matrix operations injected into the application evidence service."""

    preview: MatrixOperation
    signed_acceptance: MatrixOperation


def build_evidence_matrix_operations(
    *,
    preview_factory: MatrixOperationFactory,
    signed_acceptance_factory: MatrixOperationFactory,
) -> EvidenceMatrixOperations:
    """Build lazy matrix callables without importing or constructing Qt state."""

    return EvidenceMatrixOperations(
        preview=_LazyMatrixOperation(preview_factory),
        signed_acceptance=_LazyMatrixOperation(signed_acceptance_factory),
    )
