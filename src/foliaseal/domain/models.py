"""Domain models and contracts for document operations and signing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from foliaseal.domain.errors import FailureCode


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


@dataclass(frozen=True)
class SigningRequest:
    """Headless signing request payload used by the phase 1 pipeline."""

    input_pdf_path: str
    output_pdf_path: str
    certificate_path: str
    passphrase: str
    tsa_url: str
    timestamp_required: bool = True


@dataclass(frozen=True)
class SigningOutput:
    """Produced PDF bytes and related standards metadata."""

    output_bytes: bytes
    output_pdf_version: str
    signature_subfilter: str
    timestamp_present: bool


@dataclass(frozen=True)
class VerificationSummary:
    """Post-sign verification summary for reporting."""

    signature_count: int
    timestamp_present: bool


@dataclass(frozen=True)
class SigningResult:
    """Stable success/failure result for UI and logging layers."""

    success: bool
    failure_code: FailureCode | None
    message: str
    output_pdf_version: str | None = None
    signature_subfilter: str | None = None
    timestamp_present: bool | None = None
    standards_summary: str | None = None


class DocumentOperation(Protocol):
    """Contract implemented by each operation capability."""

    operation_type: DocumentOperationType
    revision_strategy: RevisionStrategy

    def execute(self, request: DocumentOperationRequest) -> DocumentOperationResult:
        """Execute a document operation."""
