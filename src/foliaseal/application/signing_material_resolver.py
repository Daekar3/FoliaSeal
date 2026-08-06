"""Resolve reusable certificate configurations into runtime signing inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
)
from foliaseal.domain.errors import ConfigValidationError


class SigningMaterialResolutionError(ValueError):
    """Raised when a certificate configuration cannot produce signing inputs."""


class CertificateSecretProvider(Protocol):
    """Read saved certificate passwords from a secure provider."""

    def is_available(self) -> bool:
        """Return whether saved-password retrieval is available."""

    def get_secret(self, secret_ref: str) -> str | None:
        """Return the secret for a reference, or None if no secret exists."""


@dataclass(frozen=True)
class SigningMaterial:
    """Runtime certificate material required by the current signing backend."""

    certificate_path: str
    passphrase: str
    certificate_alias: str | None = None


@dataclass(frozen=True)
class CertificateSigningMaterialResolver:
    """Resolve certificate configurations to backend-ready certificate inputs."""

    managed_certificate_dir: Path
    secret_provider: CertificateSecretProvider | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "managed_certificate_dir", Path(self.managed_certificate_dir))

    def resolve_by_configuration_id(
        self,
        catalog: CertificateCatalog,
        certificate_configuration_id: str,
        *,
        passphrase: str | None = None,
        certificate_alias: str | None = None,
    ) -> SigningMaterial:
        """Resolve a certificate configuration by stable id."""
        if not isinstance(catalog, CertificateCatalog):
            raise ConfigValidationError("catalog must be a CertificateCatalog value.")
        try:
            configuration = catalog.configuration_by_id(certificate_configuration_id)
        except KeyError as exc:
            raise SigningMaterialResolutionError(
                f"Certificate configuration '{certificate_configuration_id}' was not found."
            ) from exc
        return self.resolve(
            catalog,
            configuration,
            passphrase=passphrase,
            certificate_alias=certificate_alias,
        )

    def resolve(
        self,
        catalog: CertificateCatalog,
        configuration: CertificateConfiguration,
        *,
        passphrase: str | None = None,
        certificate_alias: str | None = None,
    ) -> SigningMaterial:
        """Resolve a certificate configuration object to runtime signing material."""
        if not isinstance(catalog, CertificateCatalog):
            raise ConfigValidationError("catalog must be a CertificateCatalog value.")
        if not isinstance(configuration, CertificateConfiguration):
            raise ConfigValidationError(
                "configuration must be a CertificateConfiguration value."
            )
        try:
            managed_certificate = catalog.managed_certificate_by_id(
                configuration.managed_certificate_id
            )
        except KeyError as exc:
            raise SigningMaterialResolutionError(
                "The selected certificate configuration references a managed certificate "
                "that no longer exists. Edit the certificate configuration or import the "
                "certificate again."
            ) from exc

        certificate_path = self.managed_certificate_dir / managed_certificate.storage_filename
        if not certificate_path.exists():
            raise SigningMaterialResolutionError(
                "The selected managed certificate file is missing. Edit the certificate "
                "configuration, restore the certificate from backup, or import it again."
            )

        resolved_passphrase = passphrase
        if resolved_passphrase is None and configuration.save_password:
            resolved_passphrase = self._read_saved_password(configuration)
        if resolved_passphrase is None:
            raise SigningMaterialResolutionError(
                "The selected certificate configuration requires a certificate password. "
                "Enter the password or edit the configuration to save it securely."
            )
        if not isinstance(resolved_passphrase, str) or not resolved_passphrase:
            raise SigningMaterialResolutionError("The certificate password cannot be blank.")

        return SigningMaterial(
            certificate_path=str(certificate_path),
            passphrase=resolved_passphrase,
            certificate_alias=certificate_alias,
        )

    def _read_saved_password(self, configuration: CertificateConfiguration) -> str | None:
        if configuration.password_secret_ref is None:
            raise SigningMaterialResolutionError(
                "The selected certificate configuration is marked to save a password, "
                "but it has no saved-password reference."
            )
        if self.secret_provider is None or not self.secret_provider.is_available():
            raise SigningMaterialResolutionError(
                "Saved password storage is not available. Enter the certificate password "
                "manually or edit the certificate configuration."
            )
        try:
            secret = self.secret_provider.get_secret(configuration.password_secret_ref)
        except Exception as exc:
            raise SigningMaterialResolutionError(
                "Saved password storage could not read the certificate password. "
                "Enter the password manually or try again after fixing secure storage."
            ) from exc
        if secret is None:
            raise SigningMaterialResolutionError(
                "The saved certificate password could not be found. Enter the password "
                "manually or save it again."
            )
        return secret
