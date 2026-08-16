"""Filesystem actions for resolving verified signing-transaction candidates."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from foliaseal.application.signing_transaction_recovery import (
    RecoveryAction,
    SigningRecoveryCandidate,
    SigningRecoveryResolution,
    SigningRecoveryResolutionPort,
    is_current_recovery_artifact,
)
from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal


class FileSigningTransactionRecoveryResolver(SigningRecoveryResolutionPort):
    """Resolve candidates with ownership checks and sibling atomic writes."""

    def __init__(self, journal: FileSigningTransactionJournal) -> None:
        self._journal = journal

    def resolve(
        self,
        candidate: SigningRecoveryCandidate,
        action: RecoveryAction,
        *,
        destination_path: str | None = None,
        replace_authorized: bool = False,
        overwrite_authorized: bool = False,
    ) -> SigningRecoveryResolution:
        artifact = candidate.artifact_path
        if not is_current_recovery_artifact(candidate.record, artifact):
            return SigningRecoveryResolution(
                action=action,
                success=False,
                error="The recovery artifact is no longer owned by this transaction.",
            )
        if action == "open":
            return SigningRecoveryResolution(
                action=action,
                success=True,
                artifact_path=str(artifact),
            )
        if action == "copy":
            return self._copy(candidate, destination_path, overwrite_authorized)
        if action == "replace":
            return self._replace(candidate, replace_authorized)
        if action == "discard":
            return self._discard(candidate)
        return SigningRecoveryResolution(
            action=action,
            success=False,
            error="Unknown recovery action.",
        )

    def _copy(
        self,
        candidate: SigningRecoveryCandidate,
        destination_path: str | None,
        overwrite_authorized: bool,
    ) -> SigningRecoveryResolution:
        if not destination_path:
            return SigningRecoveryResolution(
                action="copy",
                success=False,
                error="A destination is required.",
            )
        destination = Path(destination_path).resolve()
        if destination == candidate.artifact_path.resolve():
            return SigningRecoveryResolution(
                action="copy",
                success=False,
                error="Copy destination must differ from the recovery artifact.",
            )
        if destination.exists() and not overwrite_authorized:
            return SigningRecoveryResolution(
                action="copy",
                success=False,
                error="Copy destination already exists and was not authorized for overwrite.",
            )
        temporary_path: Path | None = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                with candidate.artifact_path.open("rb") as source:
                    shutil.copyfileobj(source, temporary)
                temporary.flush()
                os.fsync(temporary.fileno())
            shutil.copystat(candidate.artifact_path, temporary_path)
            temporary_path.replace(destination)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            return SigningRecoveryResolution(action="copy", success=False, error=str(exc))
        return SigningRecoveryResolution(
            action="copy",
            success=True,
            artifact_path=str(candidate.artifact_path),
            destination_path=str(destination),
        )

    def _replace(
        self,
        candidate: SigningRecoveryCandidate,
        replace_authorized: bool,
    ) -> SigningRecoveryResolution:
        if not replace_authorized:
            return SigningRecoveryResolution(
                action="replace",
                success=False,
                error="Replacement was not authorized.",
            )
        destination = Path(candidate.record.output_pdf_path).resolve()
        artifact = candidate.artifact_path.resolve()
        try:
            if artifact != destination:
                artifact.replace(destination)
            self._journal.complete(candidate.record.transaction_id)
        except OSError as exc:
            return SigningRecoveryResolution(action="replace", success=False, error=str(exc))
        return SigningRecoveryResolution(
            action="replace",
            success=True,
            artifact_path=str(artifact),
            destination_path=str(destination),
        )

    def _discard(self, candidate: SigningRecoveryCandidate) -> SigningRecoveryResolution:
        try:
            self._journal.discard_candidate(candidate)
        except OSError as exc:
            return SigningRecoveryResolution(action="discard", success=False, error=str(exc))
        return SigningRecoveryResolution(
            action="discard",
            success=True,
            artifact_path=str(candidate.artifact_path),
        )
