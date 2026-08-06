"""Application-owned persistence port for managed certificate catalogs.

The production filesystem adapter lives in :mod:`foliaseal.infra`; application
services depend only on this small, behavior-bearing port.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
)
from foliaseal.domain.errors import ConfigValidationError


def default_certificate_managed_dir(app_name: str = "FoliaSeal") -> Path:
    """Return the default managed-certificate directory used by composition defaults."""
    data_home = os.environ.get("XDG_DATA_HOME")
    base_dir = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base_dir / app_name / "Certificates" / "Managed"


@runtime_checkable
class CertificateCatalogRepository(Protocol):
    """Persistence operations required by certificate application services."""

    @property
    def storage_dir(self) -> Path: ...

    @property
    def managed_certificate_dir(self) -> Path: ...

    def load_catalog(self) -> CertificateCatalog: ...

    def save_catalog(self, catalog: CertificateCatalog) -> None: ...

    def save_configuration(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateCatalog: ...

    def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog: ...

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

    def export_managed_certificate_by_id(
        self,
        certificate_id: str,
        destination_path: str | Path,
    ) -> Path:
        certificate = self.catalog.managed_certificate_by_id(certificate_id)
        source_path = self.managed_certificate_dir / certificate.storage_filename
        if not source_path.exists():
            raise FileNotFoundError(f"Managed certificate file is missing: {source_path}")
        if isinstance(destination_path, str) and not destination_path.strip():
            raise ConfigValidationError("destination_path must be a non-empty path.")
        destination = Path(destination_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination)
        return destination
