"""Domain models and contracts for document operations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class RevisionStrategy(str, Enum):  # noqa: UP042
    """How an operation writes output revisions."""

    INCREMENTAL = "incremental"
    FULL_REWRITE = "full_rewrite"


class DocumentOperationType(str, Enum):  # noqa: UP042
    """Supported operation categories."""

    SIGN = "sign"
    ADD_PAGE = "add_page"
    REMOVE_PAGE = "remove_page"
    MOVE_PAGE = "move_page"
    CROP_PAGE = "crop_page"


@dataclass(frozen=True)
class DocumentOperationRequest:
    """Generic request envelope used by operation handlers."""

    operation_type: DocumentOperationType
    input_pdf_path: str
    output_pdf_path: str


@dataclass(frozen=True)
class DocumentOperationResult:
    """Generic operation result envelope."""

    success: bool
    operation_type: DocumentOperationType
    revision_strategy: RevisionStrategy
    message: str


class DocumentOperation(Protocol):
    """Contract implemented by each operation capability."""

    operation_type: DocumentOperationType
    revision_strategy: RevisionStrategy

    def execute(self, request: DocumentOperationRequest) -> DocumentOperationResult:
        """Execute a document operation."""
