"""Application service for certificate lifecycle operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Protocol

from foliaseal.application.certificate_creation import CertificateCreationService
from foliaseal.application.certificate_import import CertificateImportService
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import (
    CertificateCatalog,
    CertificateConfiguration,
    ConfigValidationError,
    ManagedCertificate,
)
from foliaseal.infra.secret_storage import SecretStorageError


class CertificateLifecycleError(RuntimeError):
    """Raised when lifecycle rollback cannot restore certificate state."""


class CertificateLifecycleSecretStore(Protocol):
    """Secure storage needed for saved certificate passwords."""

    def is_available(self) -> bool:
        """Return whether secure password storage is available."""

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        """Return the secret reference for a certificate configuration id."""

    def set_secret(self, secret_ref: str, secret: str) -> None:
        """Store a certificate password."""

    def get_secret(self, secret_ref: str) -> str | None:
        """Return a certificate password, or None when no secret exists."""

    def delete_secret(self, secret_ref: str) -> None:
        """Delete a stored certificate password."""


@dataclass(frozen=True)
class CertificateLifecycleResult:
    """Result metadata for a certificate lifecycle operation."""

    catalog: CertificateCatalog
    refresh_shell: bool
    user_message: str
    managed_certificate: ManagedCertificate | None = None
    certificate_configuration: CertificateConfiguration | None = None
    managed_file_path: Path | None = None
    exported_path: Path | None = None


@dataclass(frozen=True)
class CertificateLifecycleService:
    """Coordinate certificate catalog, managed files, and saved-password policy."""

    store: CertificateCatalogStore
    secret_store: CertificateLifecycleSecretStore | None = None
    id_factory: Callable[[], str] | None = None
    clock: Callable[[], datetime] | None = None

    def load_catalog(self) -> CertificateCatalog:
        """Return the current certificate catalog snapshot."""
        return self.store.load_catalog()

    def create_self_signed_certificate(
        self,
        *,
        display_name: str,
        passphrase: str,
        save_password: bool = False,
    ) -> CertificateLifecycleResult:
        """Create a self-signed certificate through the lifecycle boundary."""
        result = CertificateCreationService(
            store=self.store,
            id_factory=self.id_factory,
            clock=self.clock,
            secret_store=self.secret_store,
        ).create_self_signed_certificate(
            display_name=display_name,
            passphrase=passphrase,
            save_password=save_password,
        )
        return CertificateLifecycleResult(
            catalog=result.catalog,
            refresh_shell=True,
            user_message=(
                "Created certificate configuration "
                f"'{result.certificate_configuration.display_name}'."
            ),
            managed_certificate=result.managed_certificate,
            certificate_configuration=result.certificate_configuration,
            managed_file_path=result.managed_file_path,
        )

    def import_pkcs12(
        self,
        *,
        source_path: str | Path,
        display_name: str,
        passphrase: str = "",
        save_password: bool = False,
    ) -> CertificateLifecycleResult:
        """Import a PKCS#12 certificate through the lifecycle boundary."""
        result = CertificateImportService(
            store=self.store,
            id_factory=self.id_factory,
            clock=self.clock,
            secret_store=self.secret_store,
        ).import_pkcs12(
            source_path=source_path,
            display_name=display_name,
            passphrase=passphrase,
            save_password=save_password,
        )
        return CertificateLifecycleResult(
            catalog=result.catalog,
            refresh_shell=True,
            user_message=(
                "Imported certificate configuration "
                f"'{result.certificate_configuration.display_name}'."
            ),
            managed_certificate=result.managed_certificate,
            certificate_configuration=result.certificate_configuration,
            managed_file_path=result.managed_file_path,
        )

    def save_configuration(
        self,
        *,
        configuration_id: str,
        display_name: str,
        notes: str,
    ) -> CertificateLifecycleResult:
        """Rename or annotate a certificate configuration."""
        catalog = self.store.load_catalog()
        configuration = catalog.configuration_by_id(configuration_id)
        updated = replace(
            configuration,
            display_name=display_name.strip(),
            notes=notes.strip() or None,
        )
        updated_catalog = self.store.save_configuration(updated)
        return CertificateLifecycleResult(
            catalog=updated_catalog,
            refresh_shell=True,
            user_message="Certificate configuration saved.",
            certificate_configuration=updated,
        )

    def delete_configuration(self, configuration_id: str) -> CertificateLifecycleResult:
        """Delete a certificate configuration and any saved password secret."""
        catalog = self.store.load_catalog()
        configuration = catalog.configuration_by_id(configuration_id)
        secret_ref = configuration.password_secret_ref
        saved_secret: str | None = None
        if secret_ref is not None:
            if self.secret_store is None or not self.secret_store.is_available():
                raise ConfigValidationError(
                    "Saved password storage is not available. "
                    "The certificate configuration was not deleted."
                )
            try:
                saved_secret = self.secret_store.get_secret(secret_ref)
                self.secret_store.delete_secret(secret_ref)
            except (SecretStorageError, OSError, ValueError):
                raise

        try:
            updated_catalog = self.store.delete_configuration_by_id(configuration_id)
        except (ConfigValidationError, KeyError, OSError, ValueError) as exc:
            self._restore_saved_secret(
                secret_ref=secret_ref,
                saved_secret=saved_secret,
                original_error=exc,
            )
            raise

        return CertificateLifecycleResult(
            catalog=updated_catalog,
            refresh_shell=True,
            user_message="Certificate configuration deleted.",
        )

    def delete_managed_certificate(self, certificate_id: str) -> CertificateLifecycleResult:
        """Delete an unreferenced managed certificate record and file."""
        updated_catalog = self.store.delete_managed_certificate_by_id(certificate_id)
        return CertificateLifecycleResult(
            catalog=updated_catalog,
            refresh_shell=True,
            user_message="Managed certificate deleted.",
        )

    def export_managed_certificate(
        self,
        *,
        certificate_id: str,
        destination_path: str | Path,
    ) -> CertificateLifecycleResult:
        """Export a managed PKCS#12 file without mutating the catalog."""
        exported_path = self.store.export_managed_certificate_by_id(
            certificate_id,
            destination_path,
        )
        return CertificateLifecycleResult(
            catalog=self.store.load_catalog(),
            refresh_shell=False,
            user_message=f"Managed certificate exported to {exported_path}.",
            exported_path=exported_path,
        )

    def _restore_saved_secret(
        self,
        *,
        secret_ref: str | None,
        saved_secret: str | None,
        original_error: Exception,
    ) -> None:
        if secret_ref is None or saved_secret is None or self.secret_store is None:
            return
        try:
            self.secret_store.set_secret(secret_ref, saved_secret)
        except (SecretStorageError, OSError, ValueError) as restore_exc:
            raise CertificateLifecycleError(
                f"{original_error} The saved password could not be restored: "
                f"{restore_exc}"
            ) from restore_exc
