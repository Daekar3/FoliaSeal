"""Neutral lazy boundary for the production signing request executor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from foliaseal.application.signing_transaction_recovery import SigningRecoveryCandidate
from foliaseal.domain.models import SigningRequest, SigningResult, VerificationSummary


def _build_historical_backend() -> object:
    """Load the existing concrete backend only when the first sign is requested."""

    from foliaseal.application.signing_backend import build_signing_executor
    from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal

    return build_signing_executor(transaction_journal=FileSigningTransactionJournal.default())


@dataclass
class LazySigningRequestExecutor:
    """Defer heavy backend construction while exposing one stable execute verb."""

    factory: Callable[[], object] = _build_historical_backend
    _delegate: object | None = field(default=None, init=False, repr=False)

    def execute(self, request: SigningRequest) -> SigningResult:
        if self._delegate is None:
            self._delegate = self.factory()
        execute = getattr(self._delegate, "execute")
        return execute(request)

    def verify_preserved_artifact(self, artifact_path: str) -> VerificationSummary:
        """Re-run local verification through the lazily-created backend."""

        if self._delegate is None:
            self._delegate = self.factory()
        verify = getattr(self._delegate, "verify_preserved_artifact")
        return verify(artifact_path)

    def verified_recovery_candidates(self) -> tuple[SigningRecoveryCandidate, ...]:
        """Return verified crash-recovery candidates from the concrete executor."""

        if self._delegate is None:
            self._delegate = self.factory()
        recover = getattr(self._delegate, "verified_recovery_candidates", None)
        return () if not callable(recover) else tuple(recover())


def build_default_signing_executor() -> LazySigningRequestExecutor:
    """Build the production GUI executor without importing the backend at startup."""

    return LazySigningRequestExecutor()


__all__ = ["LazySigningRequestExecutor", "build_default_signing_executor"]
