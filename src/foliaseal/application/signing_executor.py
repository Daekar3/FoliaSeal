"""Neutral lazy boundary for the production signing request executor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from foliaseal.domain.models import SigningRequest, SigningResult


def _build_historical_backend() -> object:
    """Load the existing concrete backend only when the first sign is requested."""

    from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor

    return build_phase3_signing_executor()


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


def build_default_signing_executor() -> LazySigningRequestExecutor:
    """Build the production GUI executor without importing the backend at startup."""

    return LazySigningRequestExecutor()


__all__ = ["LazySigningRequestExecutor", "build_default_signing_executor"]
