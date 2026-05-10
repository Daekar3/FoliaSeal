"""Persistent storage helpers for managed certificates and configurations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from foliaseal.infra.config.schemas import (
    CertificateCatalog,
    CertificateConfiguration,
    ConfigValidationError,
    ManagedCertificate,
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
        return CertificateCatalog.from_dict(payload)

    def save_catalog(self, catalog: CertificateCatalog) -> None:
        """Persist the full certificate catalog to disk as human-readable JSON."""
        if not isinstance(catalog, CertificateCatalog):
            raise ConfigValidationError("catalog must be a CertificateCatalog value.")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.managed_certificate_dir.mkdir(parents=True, exist_ok=True)
        payload_text = json.dumps(catalog.to_dict(), indent=2, sort_keys=True)
        temp_path = self.catalog_path.with_name(f"{self.catalog_path.name}.tmp")
        temp_path.write_text(f"{payload_text}\n", encoding="utf-8")
        temp_path.replace(self.catalog_path)

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
