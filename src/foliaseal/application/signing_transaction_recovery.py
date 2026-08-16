"""Qt-free contracts for durable signing-transaction recovery."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal, Protocol

TransactionState = Literal["started", "staged", "preserved", "committing"]
RecoveryAction = Literal["open", "copy", "replace", "discard"]
_JOURNAL_FIELDS = frozenset(
    {
        "version",
        "transaction_id",
        "input_pdf_path",
        "output_pdf_path",
        "staged_pdf_path",
        "staged_sha256",
        "state",
        "created_at",
    }
)
_SECRET_KEY = re.compile(
    r"passphrase|password|private[_-]?key|secret|credential|certificate_bytes", re.I
)


class SigningTransactionJournalError(ValueError):
    """Raised when a journal record cannot be safely written or decoded."""


@dataclass(frozen=True)
class SigningTransactionRecord:
    """The only durable facts needed to identify one owned signing transaction."""

    transaction_id: str
    input_pdf_path: str
    output_pdf_path: str
    staged_pdf_path: str | None
    staged_sha256: str | None
    state: TransactionState
    created_at: str
    version: int = 1

    def __post_init__(self) -> None:
        if self.version != 1:
            raise SigningTransactionJournalError("unsupported transaction journal version")
        if not self.transaction_id.strip():
            raise SigningTransactionJournalError("transaction_id must be non-empty")
        for name, value in (
            ("input_pdf_path", self.input_pdf_path),
            ("output_pdf_path", self.output_pdf_path),
        ):
            if not value or not Path(value).is_absolute():
                raise SigningTransactionJournalError(f"{name} must be an absolute path")
        if self.staged_pdf_path is not None and not Path(self.staged_pdf_path).is_absolute():
            raise SigningTransactionJournalError("staged_pdf_path must be absolute when present")
        if self.staged_sha256 is not None and (
            len(self.staged_sha256) != 64
            or any(character not in "0123456789abcdef" for character in self.staged_sha256)
        ):
            raise SigningTransactionJournalError("staged_sha256 must be a lowercase SHA-256 digest")
        if self.state not in ("started", "staged", "preserved", "committing"):
            raise SigningTransactionJournalError("invalid transaction journal state")
        try:
            datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise SigningTransactionJournalError("created_at must be an ISO timestamp") from exc

    @classmethod
    def new(
        cls,
        *,
        transaction_id: str,
        input_pdf_path: str,
        output_pdf_path: str,
    ) -> SigningTransactionRecord:
        return cls(
            transaction_id=transaction_id,
            input_pdf_path=str(Path(input_pdf_path).resolve()),
            output_pdf_path=str(Path(output_pdf_path).resolve()),
            staged_pdf_path=None,
            staged_sha256=None,
            state="started",
            created_at=datetime.now(UTC).isoformat(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "transaction_id": self.transaction_id,
            "input_pdf_path": self.input_pdf_path,
            "output_pdf_path": self.output_pdf_path,
            "staged_pdf_path": self.staged_pdf_path,
            "staged_sha256": self.staged_sha256,
            "state": self.state,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, payload: object) -> SigningTransactionRecord:
        if not isinstance(payload, dict) or set(payload) != _JOURNAL_FIELDS:
            raise SigningTransactionJournalError("transaction journal fields are not exact")
        if any(_SECRET_KEY.search(str(key)) for key in payload):
            raise SigningTransactionJournalError("secret-bearing journal fields are forbidden")
        values = dict(payload)
        if not isinstance(values["version"], int) or isinstance(values["version"], bool):
            raise SigningTransactionJournalError("journal version must be an integer")
        scalar_fields = (
            "transaction_id",
            "input_pdf_path",
            "output_pdf_path",
            "created_at",
            "state",
        )
        if not all(isinstance(values[key], str) for key in scalar_fields):
            raise SigningTransactionJournalError("journal scalar fields have invalid types")
        staged = values["staged_pdf_path"]
        if staged is not None and not isinstance(staged, str):
            raise SigningTransactionJournalError("staged_pdf_path must be a string or null")
        digest = values["staged_sha256"]
        if digest is not None and not isinstance(digest, str):
            raise SigningTransactionJournalError("staged_sha256 must be a string or null")
        return cls(
            version=values["version"],
            transaction_id=values["transaction_id"],
            input_pdf_path=values["input_pdf_path"],
            output_pdf_path=values["output_pdf_path"],
            staged_pdf_path=staged,
            staged_sha256=digest,
            state=values["state"],
            created_at=values["created_at"],
        )

    def with_stage(self, staged_pdf_path: str) -> SigningTransactionRecord:
        path = Path(staged_pdf_path).resolve()
        return replace(
            self,
            staged_pdf_path=str(path),
            state="staged",
        )

    def preserved(self) -> SigningTransactionRecord:
        if self.staged_pdf_path is None:
            raise SigningTransactionJournalError(
                "cannot preserve a transaction without a staged artifact"
            )
        return replace(self, state="preserved")

    def committing(self) -> SigningTransactionRecord:
        if self.staged_pdf_path is None or self.staged_sha256 is None:
            raise SigningTransactionJournalError(
                "cannot commit a transaction without a staged artifact digest"
            )
        return replace(self, state="committing")


@dataclass(frozen=True)
class SigningRecoveryCandidate:
    """An owned staged PDF that has passed a fresh local verification."""

    journal_path: Path
    record: SigningTransactionRecord

    @property
    def artifact_path(self) -> Path:
        assert self.record.staged_pdf_path is not None
        staged = Path(self.record.staged_pdf_path)
        if staged.is_file() or self.record.state != "committing":
            return staged
        return Path(self.record.output_pdf_path)


@dataclass(frozen=True)
class SigningRecoveryResolution:
    """Typed result returned after resolving one verified recovery candidate."""

    action: RecoveryAction
    success: bool
    artifact_path: str | None = None
    destination_path: str | None = None
    error: str | None = None


class SigningRecoveryResolutionPort(Protocol):
    """Resolve one already-verified candidate without exposing storage policy to Qt."""

    def resolve(
        self,
        candidate: SigningRecoveryCandidate,
        action: RecoveryAction,
        *,
        destination_path: str | None = None,
        replace_authorized: bool = False,
        overwrite_authorized: bool = False,
    ) -> SigningRecoveryResolution: ...


def is_owned_staged_artifact(record: SigningTransactionRecord, artifact_path: Path) -> bool:
    """Return whether an artifact has the exact sibling shape created by atomic staging."""

    if record.staged_pdf_path is None:
        return False
    staged = artifact_path.resolve()
    expected = Path(record.staged_pdf_path).resolve()
    output = Path(record.output_pdf_path).resolve()
    if record.state == "committing" and staged == output:
        if record.staged_sha256 is None or not staged.is_file():
            return False
        return sha256(staged.read_bytes()).hexdigest() == record.staged_sha256
    if staged != expected or staged.parent != output.parent:
        return False
    return staged.name.startswith(f".{output.name}.") and staged.name.endswith(".tmp")


def is_current_recovery_artifact(record: SigningTransactionRecord, artifact_path: Path) -> bool:
    """Return whether an owned artifact still matches its journaled digest."""

    if not is_owned_staged_artifact(record, artifact_path):
        return False
    if record.staged_sha256 is None:
        return False
    try:
        return sha256(artifact_path.read_bytes()).hexdigest() == record.staged_sha256
    except OSError:
        return False


class SigningTransactionJournal(Protocol):
    """Persistence boundary used by the signing use case and recovery surface."""

    def begin(self, record: SigningTransactionRecord) -> None: ...

    def mark_staged(self, transaction_id: str, staged_pdf_path: str) -> None: ...

    def mark_preserved(self, transaction_id: str) -> None: ...

    def mark_committing(self, transaction_id: str) -> None: ...

    def complete(self, transaction_id: str) -> None: ...

    def discard(self, transaction_id: str) -> None: ...

    def verified_candidates(
        self,
        verifier: Callable[[str], bool],
    ) -> tuple[SigningRecoveryCandidate, ...]: ...

    def discard_candidate(self, candidate: SigningRecoveryCandidate) -> None: ...
