"""Persistent storage helpers for managed certificates and configurations."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from foliaseal.application.certificate_catalog_repository import (
    CertificateRepositoryError,
    ManagedCertificateCommit,
    ManagedCertificateMaterial,
)
from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
)
from foliaseal.domain.errors import ConfigValidationError
from foliaseal.infra.config.certificate_codecs import (
    decode_certificate_catalog,
    encode_certificate_catalog,
)

CERTIFICATE_DIRECTORY_NAME = "Certificates"
CERTIFICATE_CATALOG_FILENAME = "certificates.json"
MANAGED_CERTIFICATE_FILES_DIRECTORY_NAME = "Managed"


def default_certificate_config_directory(app_name: str = "FoliaSeal") -> Path:
    """Return the default user-visible storage directory for certificate config."""
    data_home = os.environ.get("XDG_DATA_HOME")
    base_dir = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base_dir / app_name / CERTIFICATE_DIRECTORY_NAME


@dataclass(frozen=True)
class CertificateCatalogStore:
    """Read/write helper for managed certificate records and configurations."""

    storage_dir: Path
    catalog_filename: str = CERTIFICATE_CATALOG_FILENAME
    managed_files_dirname: str = MANAGED_CERTIFICATE_FILES_DIRECTORY_NAME

    def __post_init__(self) -> None:
        object.__setattr__(self, "storage_dir", Path(self.storage_dir))
        if not isinstance(self.catalog_filename, str) or not self.catalog_filename.strip():
            raise ConfigValidationError("catalog_filename must be a non-empty str.")
        if (
            not isinstance(self.managed_files_dirname, str)
            or not self.managed_files_dirname.strip()
        ):
            raise ConfigValidationError("managed_files_dirname must be a non-empty str.")

    @property
    def catalog_path(self) -> Path:
        """Return the on-disk JSON catalog path."""
        return self.storage_dir / self.catalog_filename

    @property
    def managed_certificate_dir(self) -> Path:
        """Return the directory that owns app-managed PKCS#12 files."""
        return self.storage_dir / self.managed_files_dirname

    @classmethod
    def default(cls, app_name: str = "FoliaSeal") -> CertificateCatalogStore:
        """Build a store rooted in the standard user-visible certificate directory."""
        return cls(storage_dir=default_certificate_config_directory(app_name=app_name))

    def load_catalog(self) -> CertificateCatalog:
        """Load the catalog from disk, or return an empty catalog if missing."""
        path = self.catalog_path
        if not path.exists():
            return CertificateCatalog(schema_version=1)

        payload_text = path.read_text(encoding="utf-8")
        if not payload_text.strip():
            return CertificateCatalog(schema_version=1)

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                f"Certificate catalog at '{path}' is not valid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigValidationError("Certificate catalog must be a JSON object.")
        return decode_certificate_catalog(payload)

    def material_for(
        self, managed_certificate: ManagedCertificate
    ) -> ManagedCertificateMaterial:
        """Return backend material for a catalog-managed certificate."""
        if not isinstance(managed_certificate, ManagedCertificate):
            raise ConfigValidationError(
                "managed_certificate must be a ManagedCertificate value."
            )
        stored = self.load_catalog().managed_certificate_by_id(
            managed_certificate.managed_certificate_id
        )
        if stored != managed_certificate:
            raise ConfigValidationError(
                "catalog does not contain the supplied managed certificate."
            )
        path = self.managed_certificate_dir / managed_certificate.storage_filename
        if not path.exists():
            raise FileNotFoundError(f"Managed certificate file is missing: {path}")
        return ManagedCertificateMaterial(certificate_path=str(path))

    def save_catalog(self, catalog: CertificateCatalog) -> None:
        """Persist the full certificate catalog to disk as human-readable JSON."""
        if not isinstance(catalog, CertificateCatalog):
            raise ConfigValidationError("catalog must be a CertificateCatalog value.")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.managed_certificate_dir.mkdir(parents=True, exist_ok=True)
        payload_text = json.dumps(encode_certificate_catalog(catalog), indent=2, sort_keys=True)
        temp_path = self.catalog_path.with_name(f"{self.catalog_path.name}.tmp")
        try:
            temp_path.write_text(f"{payload_text}\n", encoding="utf-8")
            temp_path.replace(self.catalog_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def save_managed_certificate(self, certificate: ManagedCertificate) -> CertificateCatalog:
        """Upsert a managed certificate record and persist the resulting catalog."""
        if not isinstance(certificate, ManagedCertificate):
            raise ConfigValidationError("certificate must be a ManagedCertificate value.")
        catalog = self.load_catalog().upsert_managed_certificate(certificate)
        self.save_catalog(catalog)
        return catalog

    def save_configuration(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateCatalog:
        """Upsert a certificate configuration and persist the resulting catalog."""
        if not isinstance(configuration, CertificateConfiguration):
            raise ConfigValidationError(
                "configuration must be a CertificateConfiguration value."
            )
        catalog = self.load_catalog().upsert_configuration(configuration)
        self.save_catalog(catalog)
        return catalog

    def delete_configuration(self, name: str) -> CertificateCatalog:
        """Remove a certificate configuration by display name and persist the catalog."""
        catalog = self.load_catalog().remove_configuration(name)
        self.save_catalog(catalog)
        return catalog

    def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog:
        """Remove a certificate configuration by stable id and persist the catalog."""
        catalog = self.load_catalog().remove_configuration_by_id(configuration_id)
        self.save_catalog(catalog)
        return catalog

    def delete_managed_certificate_by_id(self, certificate_id: str) -> CertificateCatalog:
        """Remove an unreferenced managed certificate record and file."""
        catalog = self.load_catalog()
        certificate = catalog.managed_certificate_by_id(certificate_id)
        updated_catalog = catalog.remove_managed_certificate_by_id(certificate_id)
        self.delete_managed_certificate(
            managed_certificate=certificate,
            original_catalog=catalog,
            updated_catalog=updated_catalog,
        )
        return updated_catalog

    def commit_managed_certificate(
        self,
        *,
        payload: bytes,
        managed_certificate: ManagedCertificate,
        catalog: CertificateCatalog,
    ) -> ManagedCertificateCommit:
        """Atomically persist a managed PKCS#12 payload and candidate catalog."""
        if not isinstance(payload, bytes):
            raise ConfigValidationError("payload must be bytes.")
        stored = catalog.managed_certificate_by_id(managed_certificate.managed_certificate_id)
        if stored != managed_certificate:
            raise ConfigValidationError(
                "catalog does not contain the supplied managed certificate."
            )
        managed_path = self.managed_certificate_dir / managed_certificate.storage_filename
        previous_catalog = self._snapshot_file(self.catalog_path)
        previous_managed = self._snapshot_file(managed_path)
        staging_path = managed_path.with_name(f".{managed_path.name}.{uuid4().hex}.tmp")
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.managed_certificate_dir.mkdir(parents=True, exist_ok=True)
            staging_path.write_bytes(payload)
            staging_path.replace(managed_path)
            self.save_catalog(catalog)
        except Exception as exc:
            self._recover_transaction(
                operation_error=exc,
                catalog_snapshot=previous_catalog,
                managed_snapshot=previous_managed,
                catalog_path=self.catalog_path,
                managed_path=managed_path,
                staging_path=staging_path,
            )
            raise
        return ManagedCertificateCommit(catalog=catalog, managed_file_path=managed_path)

    def delete_managed_certificate(
        self,
        *,
        managed_certificate: ManagedCertificate,
        original_catalog: CertificateCatalog,
        updated_catalog: CertificateCatalog,
    ) -> None:
        """Atomically remove a managed file and its catalog record."""
        stored = original_catalog.managed_certificate_by_id(
            managed_certificate.managed_certificate_id
        )
        if stored != managed_certificate:
            raise ConfigValidationError(
                "catalog does not contain the supplied managed certificate."
            )
        expected = original_catalog.remove_managed_certificate_by_id(
            managed_certificate.managed_certificate_id
        )
        if expected != updated_catalog:
            raise ConfigValidationError(
                "updated catalog does not match managed certificate removal."
            )
        managed_path = self.managed_certificate_dir / managed_certificate.storage_filename
        previous_catalog = self._snapshot_file(self.catalog_path)
        previous_managed = self._snapshot_file(managed_path)
        quarantine_path = managed_path.with_name(f".{managed_path.name}.{uuid4().hex}.deleting")
        try:
            if managed_path.exists():
                managed_path.replace(quarantine_path)
            self.save_catalog(updated_catalog)
            if quarantine_path.exists():
                quarantine_path.unlink()
        except Exception as exc:
            self._recover_transaction(
                operation_error=exc,
                catalog_snapshot=previous_catalog,
                managed_snapshot=previous_managed,
                catalog_path=self.catalog_path,
                managed_path=managed_path,
                staging_path=quarantine_path,
            )
            raise

    @staticmethod
    def _snapshot_file(path: Path) -> bytes | None:
        return path.read_bytes() if path.exists() else None

    @classmethod
    def _recover_transaction(
        cls,
        *,
        operation_error: Exception,
        catalog_snapshot: bytes | None,
        managed_snapshot: bytes | None,
        catalog_path: Path,
        managed_path: Path,
        staging_path: Path,
    ) -> None:
        recovery_errors: list[str] = []
        try:
            if staging_path.exists():
                if managed_path.exists():
                    managed_path.unlink()
                staging_path.replace(managed_path)
        except Exception as exc:
            recovery_errors.append(f"managed staging recovery failed: {exc}")
        try:
            cls._restore_file(managed_path, managed_snapshot)
        except Exception as exc:
            recovery_errors.append(f"managed file recovery failed: {exc}")
        try:
            cls._restore_file(catalog_path, catalog_snapshot)
        except Exception as exc:
            recovery_errors.append(f"catalog recovery failed: {exc}")
        if recovery_errors:
            raise CertificateRepositoryError(
                "Managed certificate transaction failed and recovery was incomplete: "
                + "; ".join(recovery_errors)
            ) from operation_error

    @staticmethod
    def _restore_file(path: Path, previous: bytes | None) -> None:
        if previous is None:
            if path.exists():
                path.unlink()
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        restore_path = path.with_name(f".{path.name}.{uuid4().hex}.restore")
        try:
            restore_path.write_bytes(previous)
            restore_path.replace(path)
        finally:
            if restore_path.exists():
                restore_path.unlink()

    def export_managed_certificate_by_id(
        self,
        certificate_id: str,
        destination_path: str | Path,
    ) -> Path:
        """Copy a managed certificate file to a user-selected destination path."""
        catalog = self.load_catalog()
        certificate = catalog.managed_certificate_by_id(certificate_id)
        source_path = self.managed_certificate_dir / certificate.storage_filename
        if not source_path.exists():
            raise FileNotFoundError(f"Managed certificate file is missing: {source_path}")
        if isinstance(destination_path, str) and not destination_path.strip():
            raise ConfigValidationError("destination_path must be a non-empty path.")
        destination = Path(destination_path)
        destination_resolved = destination.resolve()
        managed_dir_resolved = self.managed_certificate_dir.resolve()
        if source_path.resolve() == destination_resolved:
            raise ConfigValidationError(
                "Export destination must be different from the managed certificate file."
            )
        if destination.is_symlink():
            raise ConfigValidationError("Export destination must not be a symbolic link.")
        if (
            destination_resolved == managed_dir_resolved
            or managed_dir_resolved in destination_resolved.parents
        ):
            raise ConfigValidationError(
                "Export destination must be outside FoliaSeal managed certificate storage."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        return destination
