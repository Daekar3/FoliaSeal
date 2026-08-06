"""Resolve reusable certificate configurations into signing inputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from foliaseal.application.certificate_catalog_repository import CertificateCatalogRepository
from foliaseal.application.certificate_models import CertificateCatalog, CertificateConfiguration
from foliaseal.domain.errors import ConfigValidationError


class SigningMaterialResolutionError(ValueError):
    """Raised when a certificate configuration cannot produce signing inputs."""


class CertificateSecretProvider(Protocol):
    def is_available(self) -> bool: ...
    def get_secret(self, secret_ref: str) -> str | None: ...


@dataclass(frozen=True)
class SigningMaterial:
    certificate_path: str
    passphrase: str
    certificate_alias: str | None = None


class CertificateSigningMaterialPort(Protocol):
    def resolve(
        self,
        *,
        certificate_configuration_id: str,
        passphrase: str | None = None,
        certificate_alias: str | None = None,
    ) -> SigningMaterial: ...


@dataclass(frozen=True)
class RepositoryBackedCertificateSigningMaterialPort:
    repository: CertificateCatalogRepository
    secret_provider: CertificateSecretProvider | None = None

    def resolve(
        self,
        *,
        certificate_configuration_id: str,
        passphrase: str | None = None,
        certificate_alias: str | None = None,
    ) -> SigningMaterial:
        catalog = self.repository.load_catalog()
        if not isinstance(catalog, CertificateCatalog):
            raise ConfigValidationError("catalog must be a CertificateCatalog value.")
        try:
            configuration = catalog.configuration_by_id(certificate_configuration_id)
        except KeyError as exc:
            raise SigningMaterialResolutionError(
                f"Certificate configuration '{certificate_configuration_id}' was not found."
            ) from exc
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
        try:
            material = self.repository.material_for(managed_certificate)
        except (FileNotFoundError, KeyError) as exc:
            raise SigningMaterialResolutionError(
                "The selected managed certificate file is missing. Edit the certificate "
                "configuration, restore the certificate from backup, or import it again."
            ) from exc
        resolved = passphrase
        if resolved is None and configuration.save_password:
            resolved = self._read_saved_password(configuration)
        if resolved is None:
            raise SigningMaterialResolutionError(
                "The selected certificate configuration requires a certificate password. "
                "Enter the password or edit the configuration to save it securely."
            )
        if not isinstance(resolved, str) or not resolved:
            raise SigningMaterialResolutionError("The certificate password cannot be blank.")
        return SigningMaterial(
            certificate_path=material.certificate_path,
            passphrase=resolved,
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
