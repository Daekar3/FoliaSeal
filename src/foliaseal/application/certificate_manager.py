"""Neutral application boundary for managed certificate operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, Protocol
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
from foliaseal.domain.errors import ConfigValidationError
from foliaseal.infra.secret_storage import SecretStorageError


class CertificateManagerError(RuntimeError):
    """Raised when a certificate operation cannot complete or roll back."""


class CertificateSecretStore(Protocol):
    """Narrow secure-password boundary used by the application manager."""

    def is_available(self) -> bool: ...

    def secret_ref_for_configuration(self, configuration_id: str) -> str: ...

    def set_secret(self, secret_ref: str, secret: str) -> None: ...

    def get_secret(self, secret_ref: str) -> str | None: ...

    def delete_secret(self, secret_ref: str) -> None: ...


@dataclass(frozen=True)
class CreateCertificateRequest:
    display_name: str
    passphrase: str
    save_password: bool = False


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


@dataclass(frozen=True)
class ExportCertificateRequest:
    certificate_id: str
    destination_path: str | Path


CertificateOperation = Literal[
    "created",
    "imported",
    "configuration_saved",
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

    def snapshot(self) -> CertificateCatalog:
        return self.store.load_catalog()

    def create(self, request: CreateCertificateRequest) -> CertificateOperationResult:
        name = self._normalized_name(request.display_name)
        if not isinstance(request.passphrase, str) or not request.passphrase.strip():
            raise ValueError("Certificate password cannot be blank.")
        catalog = self.snapshot()
        self._ensure_unique_name(catalog, name)
        managed_id, configuration_id = self._new_id(), self._new_id()
        created_at = self._now()
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        certificate = self._build_certificate(key=key, display_name=name, created_at=created_at)
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
            subject_summary=ManagedCertificateSubjectSummary(common_name=name),
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
        managed_id, configuration_id = self._new_id(), self._new_id()
        managed = ManagedCertificate(
            schema_version=1,
            managed_certificate_id=managed_id,
            display_name=name,
            storage_filename=f"cert_{managed_id}.p12",
            source_kind="imported",
            created_at=self._now_iso(self._now()),
            subject_summary=self._subject_summary(certificate),
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
            and item.display_name == name
            for item in catalog.certificate_configurations
        ):
            raise ConfigValidationError(f"Certificate configuration '{name}' already exists.")
        updated = replace(configuration, display_name=name, notes=request.notes.strip() or None)
        return CertificateOperationResult(
            catalog=self.store.save_configuration(updated),
            operation="configuration_saved",
            certificate_configuration=updated,
        )

    def delete_configuration(self, configuration_id: str) -> CertificateOperationResult:
        catalog = self.snapshot()
        configuration = catalog.configuration_by_id(configuration_id)
        secret_ref = configuration.password_secret_ref
        saved_secret: str | None = None
        if secret_ref is not None:
            self._require_secret_store()
            saved_secret = self.secret_store.get_secret(secret_ref)  # type: ignore[union-attr]
            self.secret_store.delete_secret(secret_ref)  # type: ignore[union-attr]
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
        managed_path = self.store.managed_certificate_dir / certificate.storage_filename
        staged_path = managed_path.with_name(f".{managed_path.name}.deleting")
        if managed_path.exists():
            managed_path.replace(staged_path)
        try:
            self.store.save_catalog(updated)
            if staged_path.exists():
                staged_path.unlink()
        except Exception as exc:
            try:
                if staged_path.exists() and not managed_path.exists():
                    staged_path.replace(managed_path)
                self.store.save_catalog(catalog)
            except Exception as restore_exc:
                raise CertificateManagerError(
                    "Managed certificate deletion failed and recovery was incomplete: "
                    f"{restore_exc}"
                ) from exc
            raise
        return CertificateOperationResult(
            catalog=updated,
            operation="managed_certificate_deleted",
        )

    def export(self, request: ExportCertificateRequest) -> CertificateOperationResult:
        exported = self.store.export_managed_certificate_by_id(
            request.certificate_id,
            request.destination_path,
        )
        return CertificateOperationResult(
            catalog=self.snapshot(),
            operation="exported",
            exported_path=exported,
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
        managed_path = self.store.managed_certificate_dir / managed.storage_filename
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
            self.store.storage_dir.mkdir(parents=True, exist_ok=True)
            self.store.managed_certificate_dir.mkdir(parents=True, exist_ok=True)
            managed_path.write_bytes(payload)
            updated = catalog.upsert_managed_certificate(managed).upsert_configuration(
                configuration
            )
            self.store.save_catalog(updated)
        except Exception:
            cleanup_errors: list[str] = []
            if managed_path.exists():
                try:
                    managed_path.unlink()
                except Exception as exc:
                    cleanup_errors.append(f"managed certificate file could not be removed: {exc}")
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
            managed_file_path=managed_path,
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
        except (SecretStorageError, OSError, ValueError) as exc:
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
        if any(item.display_name == name for item in catalog.certificate_configurations):
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
        *, key: rsa.RSAPrivateKey, display_name: str, created_at: datetime
    ) -> x509.Certificate:
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, display_name)])
        return (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(created_at - timedelta(days=1))
            .not_valid_after(created_at + timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

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
            email=first(NameOID.EMAIL_ADDRESS),
            title=first(NameOID.TITLE) or first(NameOID.ORGANIZATIONAL_UNIT_NAME),
            company=first(NameOID.ORGANIZATION_NAME),
        )
