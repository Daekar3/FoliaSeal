"""Persistent storage helpers for named signature appearance profiles."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from foliaseal.infra.config.schemas import (
    ConfigValidationError,
    SignaturePreset,
    SignaturePresetCatalog,
)

PROFILE_DIRECTORY_NAME = "Signature Profiles"
PROFILE_CATALOG_FILENAME = "profiles.json"


def default_signature_profiles_directory(app_name: str = "FoliaSeal") -> Path:
    """Return the default user-visible storage directory for signature profiles."""
    data_home = os.environ.get("XDG_DATA_HOME")
    base_dir = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base_dir / app_name / PROFILE_DIRECTORY_NAME


@dataclass(frozen=True)
class SignaturePresetCatalogStore:
    """Read/write helper for the named profile catalog on disk."""

    storage_dir: Path
    catalog_filename: str = PROFILE_CATALOG_FILENAME

    def __post_init__(self) -> None:
        object.__setattr__(self, "storage_dir", Path(self.storage_dir))
        if not isinstance(self.catalog_filename, str) or not self.catalog_filename.strip():
            raise ConfigValidationError("catalog_filename must be a non-empty str.")

    @property
    def catalog_path(self) -> Path:
        """Return the on-disk JSON catalog path."""
        return self.storage_dir / self.catalog_filename

    @classmethod
    def default(cls, app_name: str = "FoliaSeal") -> SignaturePresetCatalogStore:
        """Build a store rooted in the standard user-visible profile directory."""
        return cls(storage_dir=default_signature_profiles_directory(app_name=app_name))

    def load_catalog(self) -> SignaturePresetCatalog:
        """Load the catalog from disk, or return an empty catalog if missing."""
        path = self.catalog_path
        if not path.exists():
            return SignaturePresetCatalog(schema_version=1, profiles=())

        payload_text = path.read_text(encoding="utf-8")
        if not payload_text.strip():
            return SignaturePresetCatalog(schema_version=1, profiles=())

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                f"Profile catalog at '{path}' is not valid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigValidationError("Profile catalog must be a JSON object.")
        return SignaturePresetCatalog.from_dict(payload)

    def save_catalog(self, catalog: SignaturePresetCatalog) -> None:
        """Persist the full catalog to disk in a human-readable JSON format."""
        if not isinstance(catalog, SignaturePresetCatalog):
            raise ConfigValidationError("catalog must be a SignaturePresetCatalog value.")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        payload_text = json.dumps(catalog.to_dict(), indent=2, sort_keys=True)
        temp_path = self.catalog_path.with_name(f"{self.catalog_path.name}.tmp")
        temp_path.write_text(f"{payload_text}\n", encoding="utf-8")
        temp_path.replace(self.catalog_path)

    def save_profile(self, profile: SignaturePreset) -> SignaturePresetCatalog:
        """Upsert a profile and persist the resulting catalog."""
        if not isinstance(profile, SignaturePreset):
            raise ConfigValidationError("profile must be a SignaturePreset value.")
        catalog = self.load_catalog().upsert_profile(profile)
        self.save_catalog(catalog)
        return catalog

    def delete_profile(self, name: str) -> SignaturePresetCatalog:
        """Remove a profile by name and persist the resulting catalog."""
        catalog = self.load_catalog().remove_profile(name)
        self.save_catalog(catalog)
        return catalog
