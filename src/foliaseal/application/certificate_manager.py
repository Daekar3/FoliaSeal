"""Neutral application boundary for managed certificate operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import uuid4

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application.certificate_catalog_repository import CertificateCatalogRepository
from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
)
from foliaseal.application.certificate_secret_store import (
    CertificateSecretStore,
)
from foliaseal.domain.errors import ConfigValidationError


class CertificateManagerError(RuntimeError):
    """Raised when a certificate operation cannot complete or roll back."""


@dataclass(frozen=True)
class CreateCertificateRequest:
    display_name: str
    passphrase: str
    save_password: bool = False
    passphrase_confirmation: str | None = None
    common_name: str | None = None
    email: str | None = None
    title: str | None = None
    organization: str | None = None


@dataclass(frozen=True)
class ImportCertificateRequest:
    source_path: str | Path
    display_name: str
    passphrase: str = ""
    save_password: bool = False


@dataclass(frozen=True)
class SaveConfigurationRequest:
    configuration_id: str
    display_name: str
    notes: str
    save_password: bool | None = None
    passphrase: str | None = None
    passphrase_confirmation: str | None = None


@dataclass(frozen=True)
class ConfigureCertificateRequest:
    """Create a signing configuration for an existing managed certificate file."""

    managed_certificate_id: str
    display_name: str
    notes: str = ""


@dataclass(frozen=True)
class ExportCertificateRequest:
    certificate_id: str
    destination_path: str | Path
    passphrase: str | None = None


@dataclass(frozen=True)
class CertificateImportInspection:
    """Non-secret inspection facts shown before a PKCS#12 import."""

    subject: str
    issuer: str
    valid_from: datetime
    valid_until: datetime
    private_key_present: bool
    self_signed: bool
    warnings: tuple[str, ...] = ()


CertificateOperation = Literal[
    "created",
    "imported",
    "configuration_saved",
    "configuration_created",
    "configuration_deleted",
    "managed_certificate_deleted",
    "exported",
]


@dataclass(frozen=True)
class CertificateOperationResult:
    """Observable result of one certificate-manager operation."""

    catalog: CertificateCatalog
    operation: CertificateOperation
    managed_certificate: ManagedCertificate | None = None
    certificate_configuration: CertificateConfiguration | None = None
    managed_file_path: Path | None = None
    exported_path: Path | None = None


@dataclass(frozen=True)
class CertificateManager:
    """Own certificate policy, persistence sequencing, and rollback."""

    store: CertificateCatalogRepository
    secret_store: CertificateSecretStore | None = None
    id_factory: Callable[[], str] | None = None
    clock: Callable[[], datetime] | None = None
    referenced_configuration_ids: Callable[[], set[str]] | None = None

    def snapshot(self) -> CertificateCatalog:
        return self.store.load_catalog()

    def inspect_import(
        self,
        source_path: str | Path,
        passphrase: str,
    ) -> CertificateImportInspection:
        """Validate and inspect a PKCS#12 source without changing managed state."""
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            raise ValueError(f"Certificate file does not exist: {source}")
        key, certificate = self._load_pkcs12(source, passphrase)
        valid_from = self._certificate_datetime(certificate, "not_valid_before")
        valid_until = self._certificate_datetime(certificate, "not_valid_after")
        now = self._now()
        warnings: list[str] = []
        if now < valid_from:
            warnings.append(f"Certificate is not valid until {valid_from.date().isoformat()}.")
        elif now > valid_until:
            warnings.append(f"Certificate expired on {valid_until.date().isoformat()}.")
        elif valid_until - now <= timedelta(days=30):
            warnings.append(
                f"Certificate expires on {valid_until.date().isoformat()} within 30 days."
            )
        self_signed = certificate.subject == certificate.issuer
        if self_signed:
            warnings.append(
                "This certificate was created locally and may not be independently recognized "
                "unless other systems trust it."
            )
        return CertificateImportInspection(
            subject=certificate.subject.rfc4514_string(),
            issuer=certificate.issuer.rfc4514_string(),
            valid_from=valid_from,
            valid_until=valid_until,
            private_key_present=key is not None,
            self_signed=self_signed,
            warnings=tuple(warnings),
        )

    def create(self, request: CreateCertificateRequest) -> CertificateOperationResult:
        name = self._normalized_name(request.display_name)
        if not isinstance(request.passphrase, str) or not request.passphrase.strip():
            raise ValueError("Certificate password cannot be blank.")
        if (
            request.passphrase_confirmation is not None
            and request.passphrase != request.passphrase_confirmation
        ):
            raise ValueError("Certificate passwords do not match.")
        common_name = self._normalized_name(request.common_name or name)
        catalog = self.snapshot()
        self._ensure_unique_name(catalog, name)
        managed_id, configuration_id = self._new_id(), self._new_id()
        created_at = self._now()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        certificate = self._build_certificate(
            key=key,
            common_name=common_name,
            email=self._optional_value(request.email),
            title=self._optional_value(request.title),
            organization=self._optional_value(request.organization),
            created_at=created_at,
        )
        metadata = self._certificate_metadata(certificate)
        payload = pkcs12.serialize_key_and_certificates(
            name=name.encode("utf-8"),
            key=key,
            cert=certificate,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(
                request.passphrase.encode("utf-8")
            ),
        )
        managed = ManagedCertificate(
            schema_version=1,
            managed_certificate_id=managed_id,
            display_name=name,
            storage_filename=f"cert_{managed_id}.p12",
            source_kind="created",
            created_at=self._now_iso(created_at),
            subject_summary=self._subject_summary(certificate),
            **metadata,
        )
        configuration = CertificateConfiguration(
            schema_version=1,
            certificate_configuration_id=configuration_id,
            display_name=name,
            managed_certificate_id=managed_id,
            save_password=False,
            password_secret_ref=None,
            notes="Created self-signed certificate",
        )
        return self._commit_new_certificate(
            catalog=catalog,
            managed=managed,
            configuration=configuration,
            payload=payload,
            passphrase=request.passphrase,
            save_password=request.save_password,
            operation="created",
        )

    def import_(self, request: ImportCertificateRequest) -> CertificateOperationResult:
        source = Path(request.source_path)
        if not source.exists() or not source.is_file():
            raise ValueError(f"Certificate file does not exist: {source}")
        name = self._normalized_name(request.display_name)
        catalog = self.snapshot()
        self._ensure_unique_name(catalog, name)
        key, certificate = self._load_pkcs12(source, request.passphrase)
        del key
        metadata = self._certificate_metadata(certificate)
        managed_id, configuration_id = self._new_id(), self._new_id()
        managed = ManagedCertificate(
            schema_version=1,
            managed_certificate_id=managed_id,
            display_name=name,
            storage_filename=f"cert_{managed_id}.p12",
            source_kind="imported",
            created_at=self._now_iso(self._now()),
            subject_summary=self._subject_summary(certificate),
            **metadata,
        )
        configuration = CertificateConfiguration(
            schema_version=1,
            certificate_configuration_id=configuration_id,
            display_name=name,
            managed_certificate_id=managed_id,
            save_password=False,
            password_secret_ref=None,
            notes="Imported PKCS#12 certificate",
        )
        return self._commit_new_certificate(
            catalog=catalog,
            managed=managed,
            configuration=configuration,
            payload=source.read_bytes(),
            passphrase=request.passphrase,
            save_password=request.save_password,
            operation="imported",
        )

    def save_configuration(self, request: SaveConfigurationRequest) -> CertificateOperationResult:
        catalog = self.snapshot()
        configuration = catalog.configuration_by_id(request.configuration_id)
        name = self._normalized_name(request.display_name)
        if any(
            item.certificate_configuration_id != configuration.certificate_configuration_id
            and item.display_name.casefold() == name.casefold()
            for item in catalog.certificate_configurations
        ):
            raise ConfigValidationError(f"Certificate configuration '{name}' already exists.")
        updated = replace(configuration, display_name=name, notes=request.notes.strip() or None)
        requested_save = request.save_password
        if requested_save is None:
            return CertificateOperationResult(
                catalog=self.store.save_configuration(updated),
                operation="configuration_saved",
                certificate_configuration=updated,
            )
        if requested_save:
            return self._save_configuration_with_password(
                updated,
                request.passphrase,
                request.passphrase_confirmation,
            )
        return self._disable_configuration_password(updated)

    def configure_managed_certificate(
        self,
        request: ConfigureCertificateRequest,
    ) -> CertificateOperationResult:
        """Create a configuration for a retained managed certificate file."""
        catalog = self.snapshot()
        managed = catalog.managed_certificate_by_id(request.managed_certificate_id)
        if any(
            configuration.managed_certificate_id == managed.managed_certificate_id
            for configuration in catalog.certificate_configurations
        ):
            raise ConfigValidationError("Managed certificate is already configured for signing.")
        name = self._normalized_name(request.display_name)
        self._ensure_unique_name(catalog, name)
        configuration = CertificateConfiguration(
            schema_version=1,
            certificate_configuration_id=self._new_id(),
            display_name=name,
            managed_certificate_id=managed.managed_certificate_id,
            save_password=False,
            password_secret_ref=None,
            notes=request.notes.strip() or None,
        )
        updated = self.store.save_configuration(configuration)
        return CertificateOperationResult(
            catalog=updated,
            operation="configuration_created",
            certificate_configuration=configuration,
        )

    def delete_configuration(self, configuration_id: str) -> CertificateOperationResult:
        catalog = self.snapshot()
        configuration = catalog.configuration_by_id(configuration_id)
        if (
            self.referenced_configuration_ids is not None
            and configuration_id in self.referenced_configuration_ids()
        ):
            raise ConfigValidationError(
                "Certificate configuration is referenced by a signature preset "
                "and cannot be deleted."
            )
        secret_ref = configuration.password_secret_ref
        saved_secret: str | None = None
        if secret_ref is not None:
            self._require_secret_store()
            saved_secret = self.secret_store.get_secret(secret_ref)  # type: ignore[union-attr]
            try:
                self.secret_store.delete_secret(secret_ref)  # type: ignore[union-attr]
            except Exception as exc:
                self._restore_secret(secret_ref, saved_secret, exc)
                raise CertificateManagerError(
                    f"{exc} The saved password was restored after the delete failed."
                ) from exc
        try:
            updated = self.store.delete_configuration_by_id(configuration_id)
        except Exception as exc:
            self._restore_secret(secret_ref, saved_secret, exc)
            raise
        return CertificateOperationResult(catalog=updated, operation="configuration_deleted")

    def delete_managed_certificate(self, certificate_id: str) -> CertificateOperationResult:
        catalog = self.snapshot()
        certificate = catalog.managed_certificate_by_id(certificate_id)
        updated = catalog.remove_managed_certificate_by_id(certificate_id)
        self.store.delete_managed_certificate(
            managed_certificate=certificate,
            original_catalog=catalog,
            updated_catalog=updated,
        )
        return CertificateOperationResult(
            catalog=updated,
            operation="managed_certificate_deleted",
        )

    def export(self, request: ExportCertificateRequest) -> CertificateOperationResult:
        catalog = self.snapshot()
        passphrase = request.passphrase
        if passphrase is None:
            configuration = next(
                (
                    item
                    for item in catalog.certificate_configurations
                    if item.managed_certificate_id == request.certificate_id
                ),
                None,
            )
            if configuration is not None and configuration.save_password:
                if self.secret_store is None or configuration.password_secret_ref is None:
                    raise ConfigValidationError(
                        "Saved certificate password is unavailable. Enter it manually to export."
                    )
                passphrase = self.secret_store.get_secret(configuration.password_secret_ref)
                if not passphrase:
                    raise ConfigValidationError(
                        "Saved certificate password is unavailable. Enter it manually to export."
                    )
        if passphrase is not None:
            self._validate_export_password(request.certificate_id, passphrase)
        exported = self.store.export_managed_certificate_by_id(
            request.certificate_id,
            request.destination_path,
        )
        return CertificateOperationResult(
            catalog=catalog,
            operation="exported",
            exported_path=exported,
        )

    def _save_configuration_with_password(
        self,
        configuration: CertificateConfiguration,
        passphrase: str | None,
        passphrase_confirmation: str | None,
    ) -> CertificateOperationResult:
        self._require_secret_store()
        if passphrase is None:
            if not configuration.save_password or configuration.password_secret_ref is None:
                raise ConfigValidationError(
                    "Enter the certificate password before enabling secure password saving."
                )
            return CertificateOperationResult(
                catalog=self.store.save_configuration(configuration),
                operation="configuration_saved",
                certificate_configuration=configuration,
            )
        self._validate_password_confirmation(passphrase, passphrase_confirmation)
        self._validate_export_password(configuration.managed_certificate_id, passphrase)
        secret_ref = configuration.password_secret_ref
        if secret_ref is None:
            secret_ref = self.secret_store.secret_ref_for_configuration(  # type: ignore[union-attr]
                configuration.certificate_configuration_id
            )
        previous_secret = self.secret_store.get_secret(secret_ref)  # type: ignore[union-attr]
        self.secret_store.set_secret(secret_ref, passphrase)  # type: ignore[union-attr]
        updated = replace(configuration, save_password=True, password_secret_ref=secret_ref)
        try:
            catalog = self.store.save_configuration(updated)
        except Exception as exc:
            self._restore_secret_value(secret_ref, previous_secret, exc)
            raise
        return CertificateOperationResult(
            catalog=catalog,
            operation="configuration_saved",
            certificate_configuration=updated,
        )

    def _disable_configuration_password(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateOperationResult:
        secret_ref = configuration.password_secret_ref
        previous_secret: str | None = None
        if secret_ref is not None:
            self._require_secret_store()
            previous_secret = self.secret_store.get_secret(secret_ref)  # type: ignore[union-attr]
            self.secret_store.delete_secret(secret_ref)  # type: ignore[union-attr]
        updated = replace(configuration, save_password=False, password_secret_ref=None)
        try:
            catalog = self.store.save_configuration(updated)
        except Exception as exc:
            if secret_ref is not None:
                self._restore_secret_value(secret_ref, previous_secret, exc)
            raise
        return CertificateOperationResult(
            catalog=catalog,
            operation="configuration_saved",
            certificate_configuration=updated,
        )

    def _commit_new_certificate(
        self,
        *,
        catalog: CertificateCatalog,
        managed: ManagedCertificate,
        configuration: CertificateConfiguration,
        payload: bytes,
        passphrase: str,
        save_password: bool,
        operation: Literal["created", "imported"],
    ) -> CertificateOperationResult:
        secret_ref: str | None = None
        if save_password:
            self._require_secret_store()
            secret_ref = self.secret_store.secret_ref_for_configuration(  # type: ignore[union-attr]
                configuration.certificate_configuration_id
            )
            self.secret_store.set_secret(secret_ref, passphrase)  # type: ignore[union-attr]
            configuration = replace(
                configuration,
                save_password=True,
                password_secret_ref=secret_ref,
            )
        try:
            updated = catalog.upsert_managed_certificate(managed).upsert_configuration(
                configuration
            )
            committed = self.store.commit_managed_certificate(
                payload=payload,
                managed_certificate=managed,
                catalog=updated,
            )
        except Exception:
            cleanup_errors: list[str] = []
            if secret_ref is not None:
                try:
                    self.secret_store.delete_secret(secret_ref)  # type: ignore[union-attr]
                except Exception as exc:
                    cleanup_errors.append(f"saved password could not be removed: {exc}")
            if cleanup_errors:
                raise CertificateManagerError(
                    "Certificate operation failed, and rollback cleanup was incomplete: "
                    + "; ".join(cleanup_errors)
                )
            raise
        return CertificateOperationResult(
            catalog=updated,
            operation=operation,
            managed_certificate=managed,
            certificate_configuration=configuration,
            managed_file_path=committed.managed_file_path,
        )

    def _require_secret_store(self) -> None:
        if self.secret_store is None or not self.secret_store.is_available():
            raise ConfigValidationError(
                "Saved password storage is not available. Leave password saving "
                "disabled or configure secure storage."
            )

    def _restore_secret(
        self,
        secret_ref: str | None,
        saved_secret: str | None,
        original_error: Exception,
    ) -> None:
        if secret_ref is None or saved_secret is None or self.secret_store is None:
            return
        try:
            self.secret_store.set_secret(secret_ref, saved_secret)
        except Exception as exc:
            raise CertificateManagerError(
                f"{original_error} The saved password could not be restored: {exc}"
            ) from exc

    def _restore_secret_value(
        self,
        secret_ref: str,
        previous_secret: str | None,
        original_error: Exception,
    ) -> None:
        try:
            if previous_secret is None:
                self.secret_store.delete_secret(secret_ref)  # type: ignore[union-attr]
            else:
                self.secret_store.set_secret(secret_ref, previous_secret)  # type: ignore[union-attr]
        except Exception as exc:
            raise CertificateManagerError(
                f"{original_error} The saved password could not be restored: {exc}"
            ) from exc

    @staticmethod
    def _normalized_name(value: str) -> str:
        name = value.strip()
        if not name:
            raise ConfigValidationError("display_name must be a non-empty str.")
        return name

    @staticmethod
    def _ensure_unique_name(catalog: CertificateCatalog, name: str) -> None:
        if any(
            item.display_name.casefold() == name.casefold()
            for item in catalog.certificate_configurations
        ):
            raise ConfigValidationError(f"Certificate configuration '{name}' already exists.")

    def _new_id(self) -> str:
        return self.id_factory() if self.id_factory is not None else uuid4().hex

    def _now(self) -> datetime:
        now = self.clock() if self.clock is not None else datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return now.astimezone(UTC).replace(microsecond=0)

    @staticmethod
    def _now_iso(value: datetime) -> str:
        return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _build_certificate(
        *,
        key: rsa.RSAPrivateKey,
        common_name: str,
        email: str | None,
        title: str | None,
        organization: str | None,
        created_at: datetime,
    ) -> x509.Certificate:
        attributes = [x509.NameAttribute(NameOID.COMMON_NAME, common_name)]
        if email is not None:
            attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, email))
        if title is not None:
            attributes.append(x509.NameAttribute(NameOID.TITLE, title))
        if organization is not None:
            attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        subject = issuer = x509.Name(attributes)
        try:
            valid_until = created_at.replace(year=created_at.year + 5)
        except ValueError:
            valid_until = created_at.replace(year=created_at.year + 5, day=28)
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(created_at - timedelta(days=1))
            .not_valid_after(valid_until)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

    @staticmethod
    def _optional_value(value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @staticmethod
    def _validate_password_confirmation(
        passphrase: str,
        confirmation: str | None,
    ) -> None:
        if not passphrase.strip():
            raise ValueError("Certificate password cannot be blank.")
        if confirmation is not None and passphrase != confirmation:
            raise ValueError("Certificate passwords do not match.")

    def _validate_export_password(self, certificate_id: str, passphrase: str) -> None:
        if not passphrase.strip():
            raise ValueError("Certificate export requires a password.")
        certificate = self.snapshot().managed_certificate_by_id(certificate_id)
        material = self.store.material_for(certificate)
        self._load_pkcs12(Path(material.certificate_path), passphrase)

    @staticmethod
    def _load_pkcs12(source: Path, passphrase: str) -> tuple[object, object]:
        if not passphrase:
            raise ValueError("Certificate import requires a password-protected PKCS#12 file.")
        try:
            key, certificate, _extra = pkcs12.load_key_and_certificates(
                source.read_bytes(), passphrase.encode("utf-8")
            )
        except Exception as exc:
            raise ValueError(
                "Unable to load PKCS#12 certificate. Check the file and password."
            ) from exc
        if key is None or certificate is None:
            raise ValueError("PKCS#12 file must contain both a private key and a certificate.")
        return key, certificate

    @staticmethod
    def _certificate_datetime(certificate: object, name: str) -> datetime:
        utc_value = getattr(certificate, f"{name}_utc", None)
        value = utc_value if utc_value is not None else getattr(certificate, name)
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @staticmethod
    def _subject_summary(certificate: object) -> ManagedCertificateSubjectSummary:
        subject = certificate.subject

        def first(oid: NameOID) -> str | None:
            attributes = subject.get_attributes_for_oid(oid)
            if not attributes:
                return None
            value = attributes[0].value.strip()
            return value or None

        return ManagedCertificateSubjectSummary(
            common_name=first(NameOID.COMMON_NAME),
            distinguished_name=certificate.subject.rfc4514_string() or None,
            email=first(NameOID.EMAIL_ADDRESS),
            title=first(NameOID.TITLE) or first(NameOID.ORGANIZATIONAL_UNIT_NAME),
            company=first(NameOID.ORGANIZATION_NAME),
        )

    @classmethod
    def _certificate_metadata(cls, certificate: object) -> dict[str, str]:
        """Return public, secret-free identity and validity facts for persistence."""

        return {
            "issuer_summary": certificate.issuer.rfc4514_string() or "Unknown issuer",
            "valid_from": cls._now_iso(cls._certificate_datetime(certificate, "not_valid_before")),
            "valid_until": cls._now_iso(cls._certificate_datetime(certificate, "not_valid_after")),
            "fingerprint_sha256": certificate.fingerprint(hashes.SHA256()).hex(),
        }
