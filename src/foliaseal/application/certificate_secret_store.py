"""Application-owned certificate secret boundary."""

from __future__ import annotations

from typing import Protocol


class CertificateSecretStoreError(RuntimeError):
    """Raised when a certificate password operation cannot complete."""


class CertificateSecretStore(Protocol):
    """Narrow secure-password boundary used by certificate workflows."""

    def is_available(self) -> bool: ...

    def secret_ref_for_configuration(self, configuration_id: str) -> str: ...

    def set_secret(self, secret_ref: str, secret: str) -> None: ...

    def get_secret(self, secret_ref: str) -> str | None: ...

    def delete_secret(self, secret_ref: str) -> None: ...
