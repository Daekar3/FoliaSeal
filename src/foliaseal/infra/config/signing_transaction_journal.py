"""Atomic JSON storage for secret-free signing transaction recovery records."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

from foliaseal.application.signing_transaction_recovery import (
    SigningRecoveryCandidate,
    SigningTransactionJournalError,
    SigningTransactionRecord,
    is_current_recovery_artifact,
    is_owned_staged_artifact,
)


class FileSigningTransactionJournal:
    """Store one transaction record per file under a private configuration directory."""

    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = Path(storage_dir)

    @classmethod
    def default(cls, app_name: str = "FoliaSeal") -> FileSigningTransactionJournal:
        from foliaseal.infra.config.app_settings_storage import default_app_settings_directory

        return cls(default_app_settings_directory(app_name) / "signing-transactions")

    def _path(self, transaction_id: str) -> Path:
        if not transaction_id or Path(transaction_id).name != transaction_id:
            raise SigningTransactionJournalError("invalid transaction id")
        return self.storage_dir / f"{transaction_id}.json"

    def _read(self, transaction_id: str) -> SigningTransactionRecord:
        try:
            payload = json.loads(self._path(transaction_id).read_text(encoding="utf-8"))
            return SigningTransactionRecord.from_dict(payload)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SigningTransactionJournalError("transaction journal is unreadable") from exc

    def _write(self, record: SigningTransactionRecord) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        target = self._path(record.transaction_id)
        temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(record.to_dict(), sort_keys=True) + "\n", encoding="utf-8")
        try:
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)

    def begin(self, record: SigningTransactionRecord) -> None:
        self._write(record)

    def mark_staged(self, transaction_id: str, staged_pdf_path: str) -> None:
        record = self._read(transaction_id).with_stage(staged_pdf_path)
        digest = sha256(Path(staged_pdf_path).read_bytes()).hexdigest()
        self._write(replace(record, staged_sha256=digest))

    def mark_preserved(self, transaction_id: str) -> None:
        self._write(self._read(transaction_id).preserved())

    def mark_committing(self, transaction_id: str) -> None:
        self._write(self._read(transaction_id).committing())

    def complete(self, transaction_id: str) -> None:
        self._path(transaction_id).unlink(missing_ok=True)

    def discard(self, transaction_id: str) -> None:
        self._path(transaction_id).unlink(missing_ok=True)

    def verified_candidates(
        self,
        verifier: Callable[[str], bool],
    ) -> tuple[SigningRecoveryCandidate, ...]:
        candidates: list[SigningRecoveryCandidate] = []
        if not self.storage_dir.is_dir():
            return ()
        for journal_path in sorted(self.storage_dir.glob("*.json")):
            try:
                record = SigningTransactionRecord.from_dict(
                    json.loads(journal_path.read_text(encoding="utf-8"))
                )
                artifact = SigningRecoveryCandidate(journal_path, record).artifact_path
                if record.state not in ("staged", "preserved", "committing"):
                    continue
                if not artifact.is_file() or not is_current_recovery_artifact(record, artifact):
                    continue
                if verifier(str(artifact)):
                    candidates.append(SigningRecoveryCandidate(journal_path, record))
            except (OSError, UnicodeError, json.JSONDecodeError, SigningTransactionJournalError):
                continue
            except Exception:
                # A single corrupt/unreadable candidate must not abort startup
                # recovery scanning for every other transaction.
                continue
        return tuple(candidates)

    def discard_candidate(self, candidate: SigningRecoveryCandidate) -> None:
        record = candidate.record
        artifact = candidate.artifact_path if record.staged_pdf_path else None
        if artifact is not None and is_owned_staged_artifact(record, artifact):
            artifact.unlink(missing_ok=True)
        if candidate.journal_path.resolve().parent == self.storage_dir.resolve():
            candidate.journal_path.unlink(missing_ok=True)
