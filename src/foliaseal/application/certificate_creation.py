"""Application service for creating managed self-signed certificates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import (
    CertificateCatalog,
    CertificateConfiguration,
    ConfigValidationError,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
)


class CertificateCreationError(ValueError):
    """Raised when a managed self-signed certificate cannot be created."""


class CertificateSecretStore(Protocol):
    """Store saved certificate passwords outside ordinary configuration JSON."""

    def is_available(self) -> bool:
        """Return whether secure password storage is available."""

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        """Return the secret reference for a certificate configuration id."""

    def set_secret(self, secret_ref: str, secret: str) -> None:
        """Store a certificate password."""

    def delete_secret(self, secret_ref: str) -> None:
        """Delete a stored certificate password."""


@dataclass(frozen=True)
class CertificateCreationResult:
    """Result of creating one managed self-signed certificate configuration."""

    catalog: CertificateCatalog
    managed_certificate: ManagedCertificate
    certificate_configuration: CertificateConfiguration
    managed_file_path: Path


@dataclass(frozen=True)
class CertificateCreationService:
    """Create self-signed certificates in FoliaSeal-managed storage."""

    store: CertificateCatalogStore
    id_factory: Callable[[], str] | None = None
    clock: Callable[[], datetime] | None = None
    secret_store: CertificateSecretStore | None = None

    def create_self_signed_certificate(
        self,
        *,
        display_name: str,
        passphrase: str,
        save_password: bool = False,
    ) -> CertificateCreationResult:
        """Create a self-signed PKCS#12 certificate and catalog configuration."""
        normalized_name = display_name.strip()
        if not normalized_name:
            raise ConfigValidationError("display_name must be a non-empty str.")
        if not isinstance(passphrase, str) or not passphrase.strip():
            raise CertificateCreationError("Certificate password cannot be blank.")

        catalog = self.store.load_catalog()
        if any(
            configuration.display_name == normalized_name
            for configuration in catalog.certificate_configurations
        ):
            raise ConfigValidationError(
                f"Certificate configuration '{normalized_name}' already exists."
            )

        managed_certificate_id = self._new_id()
        configuration_id = self._new_id()
        storage_filename = f"cert_{managed_certificate_id}.p12"
        managed_path = self.store.managed_certificate_dir / storage_filename
        created_at = self._now_iso()

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        certificate = self._build_certificate(
            key=key,
            display_name=normalized_name,
            created_at=self._now(),
        )
        pkcs12_payload = pkcs12.serialize_key_and_certificates(
            name=normalized_name.encode("utf-8"),
            key=key,
            cert=certificate,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(
                passphrase.encode("utf-8")
            ),
        )

        managed_certificate = ManagedCertificate(
            schema_version=1,
            managed_certificate_id=managed_certificate_id,
            display_name=normalized_name,
            storage_filename=storage_filename,
            source_kind="created",
            created_at=created_at,
            subject_summary=ManagedCertificateSubjectSummary(
                common_name=normalized_name,
            ),
        )
        configuration = CertificateConfiguration(
            schema_version=1,
            certificate_configuration_id=configuration_id,
            display_name=normalized_name,
            managed_certificate_id=managed_certificate_id,
            save_password=False,
            password_secret_ref=None,
            notes="Created self-signed certificate",
        )

        password_secret_ref: str | None = None
        try:
            if save_password:
                if self.secret_store is None or not self.secret_store.is_available():
                    raise ConfigValidationError(
                        "Saved password storage is not available. Leave password saving "
                        "disabled or configure secure storage."
                    )
                password_secret_ref = self.secret_store.secret_ref_for_configuration(
                    configuration_id
                )
                self.secret_store.set_secret(password_secret_ref, passphrase)
                configuration = replace(
                    configuration,
                    save_password=True,
                    password_secret_ref=password_secret_ref,
                )

            self.store.storage_dir.mkdir(parents=True, exist_ok=True)
            self.store.managed_certificate_dir.mkdir(parents=True, exist_ok=True)
            managed_path.write_bytes(pkcs12_payload)
            updated_catalog = catalog.upsert_managed_certificate(
                managed_certificate
            ).upsert_configuration(configuration)
            self.store.save_catalog(updated_catalog)
        except Exception:
            cleanup_errors: list[str] = []
            if managed_path.exists():
                try:
                    managed_path.unlink()
                except Exception as cleanup_exc:
                    cleanup_errors.append(
                        f"managed certificate file could not be removed: {cleanup_exc}"
                    )
            if password_secret_ref is not None and self.secret_store is not None:
                try:
                    self.secret_store.delete_secret(password_secret_ref)
                except Exception as cleanup_exc:
                    cleanup_errors.append(
                        f"saved password could not be removed: {cleanup_exc}"
                    )
            if cleanup_errors:
                raise CertificateCreationError(
                    "Certificate creation failed, and rollback cleanup was incomplete: "
                    + "; ".join(cleanup_errors)
                )
            raise

        return CertificateCreationResult(
            catalog=updated_catalog,
            managed_certificate=managed_certificate,
            certificate_configuration=configuration,
            managed_file_path=managed_path,
        )

    def _build_certificate(
        self,
        *,
        key: rsa.RSAPrivateKey,
        display_name: str,
        created_at: datetime,
    ) -> x509.Certificate:
        subject = issuer = x509.Name(
            [x509.NameAttribute(NameOID.COMMON_NAME, display_name)]
        )
        not_before = created_at.astimezone(UTC) - timedelta(days=1)
        not_after = created_at.astimezone(UTC) + timedelta(days=365)
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(not_before)
            .not_valid_after(not_after)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

    def _new_id(self) -> str:
        if self.id_factory is not None:
            return self.id_factory()
        return uuid4().hex

    def _now(self) -> datetime:
        now = self.clock() if self.clock is not None else datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return now.astimezone(UTC).replace(microsecond=0)

    def _now_iso(self) -> str:
        return self._now().isoformat().replace("+00:00", "Z")
