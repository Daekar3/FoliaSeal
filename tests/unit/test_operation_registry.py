from dataclasses import dataclass

from pdf_signer.application.operation_registry import OperationRegistry
from pdf_signer.domain.models import (
    DocumentOperationRequest,
    DocumentOperationResult,
    DocumentOperationType,
    RevisionStrategy,
)


@dataclass
class StubSignOperation:
    operation_type: DocumentOperationType = DocumentOperationType.SIGN
    revision_strategy: RevisionStrategy = RevisionStrategy.INCREMENTAL

    def execute(self, request: DocumentOperationRequest) -> DocumentOperationResult:
        return DocumentOperationResult(
            success=True,
            operation_type=request.operation_type,
            revision_strategy=self.revision_strategy,
            message="ok",
        )


@dataclass
class StubMoveOperation:
    operation_type: DocumentOperationType = DocumentOperationType.MOVE_PAGE
    revision_strategy: RevisionStrategy = RevisionStrategy.FULL_REWRITE

    def execute(self, request: DocumentOperationRequest) -> DocumentOperationResult:
        return DocumentOperationResult(
            success=True,
            operation_type=request.operation_type,
            revision_strategy=self.revision_strategy,
            message="ok",
        )


def test_registry_tracks_enablement_flags() -> None:
    registry = OperationRegistry()
    registry.register(StubSignOperation(), enabled=True)
    registry.register(StubMoveOperation(), enabled=False)

    assert registry.is_enabled(DocumentOperationType.SIGN) is True
    assert registry.is_enabled(DocumentOperationType.MOVE_PAGE) is False


def test_registry_returns_registered_handler() -> None:
    registry = OperationRegistry()
    handler = StubSignOperation()
    registry.register(handler, enabled=True)

    entry = registry.get(DocumentOperationType.SIGN)

    assert entry.handler is handler
    assert entry.enabled is True
