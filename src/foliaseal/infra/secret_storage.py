"""Secure certificate password storage adapters."""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass


class SecretStorageError(RuntimeError):
    """Raised when secure secret storage cannot complete an operation."""


@dataclass(frozen=True)
class SecretToolCertificateSecretStore:
    """Store certificate passwords through the Linux Secret Service tool."""

    executable: str = "secret-tool"
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None
    availability_checker: Callable[[], bool] | None = None

    _REF_PREFIX = "secret-tool://foliaseal/certificate-password/"

    def is_available(self) -> bool:
        """Return whether the secret-tool executable is available."""
        if self.availability_checker is not None:
            return bool(self.availability_checker())
        return shutil.which(self.executable) is not None

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        """Return the stable secret reference for a certificate configuration."""
        normalized_id = self._require_configuration_id(configuration_id)
        return f"{self._REF_PREFIX}{normalized_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        """Store a certificate password for a secret reference."""
        configuration_id = self._configuration_id_from_ref(secret_ref)
        if not secret:
            raise SecretStorageError("Certificate password cannot be blank.")
        self._require_available()
        result = self._run(
            [
                self.executable,
                "store",
                "--label",
                f"FoliaSeal certificate password {configuration_id}",
                *self._attributes(configuration_id),
            ],
            input=secret,
        )
        self._raise_if_failed(result, "store certificate password")

    def get_secret(self, secret_ref: str) -> str | None:
        """Return a stored certificate password, or None if no secret exists."""
        configuration_id = self._configuration_id_from_ref(secret_ref)
        if not self.is_available():
            return None
        result = self._run(
            [self.executable, "lookup", *self._attributes(configuration_id)],
        )
        if result.returncode != 0:
            return None
        secret = result.stdout.rstrip("\n")
        return secret or None

    def delete_secret(self, secret_ref: str) -> None:
        """Delete a stored certificate password if it exists."""
        configuration_id = self._configuration_id_from_ref(secret_ref)
        self._require_available()
        result = self._run(
            [self.executable, "clear", *self._attributes(configuration_id)],
        )
        if result.returncode not in {0, 1}:
            self._raise_if_failed(result, "delete certificate password")

    def _run(
        self,
        args: list[str],
        *,
        input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        runner = self.runner or subprocess.run
        return runner(
            args,
            input=input,
            text=True,
            capture_output=True,
            check=False,
        )

    def _require_available(self) -> None:
        if not self.is_available():
            raise SecretStorageError(
                "Secret Service storage is not available. Install libsecret's "
                "secret-tool or leave password saving disabled."
            )

    @classmethod
    def _configuration_id_from_ref(cls, secret_ref: str) -> str:
        if not isinstance(secret_ref, str) or not secret_ref.startswith(cls._REF_PREFIX):
            raise SecretStorageError("Unsupported certificate password secret reference.")
        return cls._require_configuration_id(secret_ref.removeprefix(cls._REF_PREFIX))

    @staticmethod
    def _require_configuration_id(configuration_id: str) -> str:
        if not isinstance(configuration_id, str) or not configuration_id.strip():
            raise SecretStorageError("certificate configuration id must be non-empty.")
        normalized_id = configuration_id.strip()
        if "/" in normalized_id:
            raise SecretStorageError("certificate configuration id must not contain '/'.")
        return normalized_id

    @staticmethod
    def _attributes(configuration_id: str) -> list[str]:
        return [
            "application",
            "FoliaSeal",
            "kind",
            "certificate-password",
            "configuration_id",
            configuration_id,
        ]

    @staticmethod
    def _raise_if_failed(
        result: subprocess.CompletedProcess[str],
        operation: str,
    ) -> None:
        if result.returncode == 0:
            return
        detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise SecretStorageError(f"Unable to {operation}: {detail}")
