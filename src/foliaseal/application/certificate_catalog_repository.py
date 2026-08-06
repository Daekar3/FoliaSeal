"""Application-owned persistence port for managed certificate catalogs.

The production filesystem adapter lives in :mod:`foliaseal.infra`; application
services depend only on this small, behavior-bearing port.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
)
from foliaseal.domain.errors import ConfigValidationError


class CertificateRepositoryError(RuntimeError):
    """Raised when a repository transaction cannot restore its prior state."""


def default_certificate_managed_dir(app_name: str = "FoliaSeal") -> Path:
    """Return the default managed-certificate directory used by composition defaults."""
    data_home = os.environ.get("XDG_DATA_HOME")
    base_dir = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base_dir / app_name / "Certificates" / "Managed"


@dataclass(frozen=True)
class ManagedCertificateCommit:
    """Result returned after a managed certificate/file catalog commit."""

    catalog: CertificateCatalog
    managed_file_path: Path


@runtime_checkable
class CertificateCatalogRepository(Protocol):
    """Persistence operations required by certificate application services."""

    def load_catalog(self) -> CertificateCatalog: ...

    def save_catalog(self, catalog: CertificateCatalog) -> None: ...

    def save_configuration(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateCatalog: ...

    def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog: ...

    def commit_managed_certificate(
        self,
        *,
        payload: bytes,
        managed_certificate: ManagedCertificate,
        catalog: CertificateCatalog,
    ) -> ManagedCertificateCommit: ...

    def delete_managed_certificate(
        self,
        *,
        managed_certificate: ManagedCertificate,
        original_catalog: CertificateCatalog,
        updated_catalog: CertificateCatalog,
    ) -> None: ...

    def export_managed_certificate_by_id(
        self,
        certificate_id: str,
        destination_path: str | Path,
    ) -> Path: ...


@dataclass
class InMemoryCertificateCatalogRepository:
    """Small application-only repository for state and boundary tests."""

    catalog: CertificateCatalog
    storage_dir: Path
    managed_certificate_dir: Path | None = None
    _managed_files: dict[str, bytes] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.storage_dir = Path(self.storage_dir)
        if self.managed_certificate_dir is None:
            self.managed_certificate_dir = self.storage_dir / "Managed"
        else:
            self.managed_certificate_dir = Path(self.managed_certificate_dir)

    def load_catalog(self) -> CertificateCatalog:
        return self.catalog

    def save_catalog(self, catalog: CertificateCatalog) -> None:
        if not isinstance(catalog, CertificateCatalog):
            raise ConfigValidationError("catalog must be a CertificateCatalog value.")
        self.catalog = catalog

    def save_configuration(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateCatalog:
        if not isinstance(configuration, CertificateConfiguration):
            raise ConfigValidationError(
                "configuration must be a CertificateConfiguration value."
            )
        catalog = self.catalog.upsert_configuration(configuration)
        self.save_catalog(catalog)
        return catalog

    def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog:
        catalog = self.catalog.remove_configuration_by_id(configuration_id)
        self.save_catalog(catalog)
        return catalog

    def commit_managed_certificate(
        self,
        *,
        payload: bytes,
        managed_certificate: ManagedCertificate,
        catalog: CertificateCatalog,
    ) -> ManagedCertificateCommit:
        if not isinstance(payload, bytes):
            raise ConfigValidationError("payload must be bytes.")
        catalog.managed_certificate_by_id(managed_certificate.managed_certificate_id)
        if (
            catalog.managed_certificate_by_id(managed_certificate.managed_certificate_id)
            != managed_certificate
        ):
            raise ConfigValidationError(
                "catalog does not contain the supplied managed certificate."
            )
        path = self.managed_certificate_dir / managed_certificate.storage_filename
        previous_catalog = self.catalog
        previous_bytes = self._managed_files.get(managed_certificate.storage_filename)
        try:
            self._managed_files[managed_certificate.storage_filename] = payload
            self.save_catalog(catalog)
        except Exception:
            self.catalog = previous_catalog
            if previous_bytes is None:
                self._managed_files.pop(managed_certificate.storage_filename, None)
            else:
                self._managed_files[managed_certificate.storage_filename] = previous_bytes
            raise
        return ManagedCertificateCommit(catalog=catalog, managed_file_path=path)

    def delete_managed_certificate(
        self,
        *,
        managed_certificate: ManagedCertificate,
        original_catalog: CertificateCatalog,
        updated_catalog: CertificateCatalog,
    ) -> None:
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
        filename = managed_certificate.storage_filename
        previous_bytes = self._managed_files.get(filename)
        previous_catalog = self.catalog
        try:
            self.save_catalog(updated_catalog)
            self._managed_files.pop(filename, None)
        except Exception:
            self.catalog = previous_catalog
            if previous_bytes is not None:
                self._managed_files[filename] = previous_bytes
            raise

    def export_managed_certificate_by_id(
        self,
        certificate_id: str,
        destination_path: str | Path,
    ) -> Path:
        certificate = self.catalog.managed_certificate_by_id(certificate_id)
        source_path = self.managed_certificate_dir / certificate.storage_filename
        source_bytes = self._managed_files.get(certificate.storage_filename)
        if source_bytes is None and not source_path.exists():
            raise FileNotFoundError(f"Managed certificate file is missing: {source_path}")
        if isinstance(destination_path, str) and not destination_path.strip():
            raise ConfigValidationError("destination_path must be a non-empty path.")
        destination = Path(destination_path)
        self._validate_export_destination(source_path, destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source_bytes is None:
            shutil.copy2(source_path, destination)
        else:
            destination.write_bytes(source_bytes)
        return destination

    def _validate_export_destination(self, source_path: Path, destination: Path) -> None:
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
