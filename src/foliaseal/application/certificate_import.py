"""Application service for importing managed PKCS#12 certificates."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

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


class CertificateImportError(ValueError):
    """Raised when a PKCS#12 certificate cannot be imported."""


@dataclass(frozen=True)
class CertificateImportResult:
    """Result of importing one managed certificate configuration."""

    catalog: CertificateCatalog
    managed_certificate: ManagedCertificate
    certificate_configuration: CertificateConfiguration
    managed_file_path: Path


@dataclass(frozen=True)
class CertificateImportService:
    """Import PKCS#12 files into FoliaSeal-managed certificate storage."""

    store: CertificateCatalogStore
    id_factory: Callable[[], str] | None = None
    clock: Callable[[], datetime] | None = None

    def import_pkcs12(
        self,
        *,
        source_path: str | Path,
        display_name: str,
        passphrase: str = "",
    ) -> CertificateImportResult:
        """Copy a PKCS#12 file into managed storage and create catalog records."""
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            raise CertificateImportError(f"Certificate file does not exist: {source}")

        normalized_name = display_name.strip()
        if not normalized_name:
            raise ConfigValidationError("display_name must be a non-empty str.")

        catalog = self.store.load_catalog()
        if any(
            configuration.display_name == normalized_name
            for configuration in catalog.certificate_configurations
        ):
            raise ConfigValidationError(
                f"Certificate configuration '{normalized_name}' already exists."
            )

        key, certificate = self._load_pkcs12(source, passphrase)
        managed_certificate_id = self._new_id()
        configuration_id = self._new_id()
        storage_filename = f"cert_{managed_certificate_id}.p12"
        managed_path = self.store.managed_certificate_dir / storage_filename
        created_at = self._now_iso()

        managed_certificate = ManagedCertificate(
            schema_version=1,
            managed_certificate_id=managed_certificate_id,
            display_name=normalized_name,
            storage_filename=storage_filename,
            source_kind="imported",
            created_at=created_at,
            subject_summary=self._subject_summary(certificate),
        )
        configuration = CertificateConfiguration(
            schema_version=1,
            certificate_configuration_id=configuration_id,
            display_name=normalized_name,
            managed_certificate_id=managed_certificate_id,
            save_password=False,
            password_secret_ref=None,
            notes="Imported PKCS#12 certificate",
        )

        self.store.storage_dir.mkdir(parents=True, exist_ok=True)
        self.store.managed_certificate_dir.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(source, managed_path)
            updated_catalog = catalog.upsert_managed_certificate(
                managed_certificate
            ).upsert_configuration(configuration)
            self.store.save_catalog(updated_catalog)
        except Exception:
            if managed_path.exists():
                managed_path.unlink()
            raise

        return CertificateImportResult(
            catalog=updated_catalog,
            managed_certificate=managed_certificate,
            certificate_configuration=configuration,
            managed_file_path=managed_path,
        )

    def _load_pkcs12(self, source: Path, passphrase: str) -> tuple[object, object]:
        if not passphrase:
            raise CertificateImportError(
                "Certificate import requires a password-protected PKCS#12 file."
            )
        passphrase_bytes = passphrase.encode("utf-8") if passphrase else None
        try:
            key, certificate, _extra = pkcs12.load_key_and_certificates(
                source.read_bytes(),
                passphrase_bytes,
            )
        except Exception as exc:
            raise CertificateImportError(
                "Unable to load PKCS#12 certificate. Check the file and password."
            ) from exc
        if key is None or certificate is None:
            raise CertificateImportError(
                "PKCS#12 file must contain both a private key and a certificate."
            )
        return key, certificate

    def _subject_summary(self, certificate: object) -> ManagedCertificateSubjectSummary:
        subject = certificate.subject

        def _first_attr(oid: NameOID) -> str | None:
            attributes = subject.get_attributes_for_oid(oid)
            if not attributes:
                return None
            value = attributes[0].value.strip()
            return value or None

        return ManagedCertificateSubjectSummary(
            common_name=_first_attr(NameOID.COMMON_NAME),
            email=_first_attr(NameOID.EMAIL_ADDRESS),
            title=_first_attr(NameOID.TITLE)
            or _first_attr(NameOID.ORGANIZATIONAL_UNIT_NAME),
            company=_first_attr(NameOID.ORGANIZATION_NAME),
        )

    def _new_id(self) -> str:
        if self.id_factory is not None:
            return self.id_factory()
        return uuid4().hex

    def _now_iso(self) -> str:
        now = self.clock() if self.clock is not None else datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return now.astimezone(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00",
            "Z",
        )
