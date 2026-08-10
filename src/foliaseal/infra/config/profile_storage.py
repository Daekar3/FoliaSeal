"""Persistent storage helpers for reusable signature preset catalogs."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from foliaseal.application.reusable_signing_models import (
    AppearanceProfile,
    ResolvedSignaturePreset,
    SignaturePresetCatalog,
    _deserialize_appearance,
    _deserialize_placement_defaults,
    _stable_id,
)
from foliaseal.infra.config.schemas import ConfigValidationError

PROFILE_DIRECTORY_NAME = "Signature Profiles"
PROFILE_CATALOG_FILENAME = "profiles.json"


def _migrate_legacy_profiles(payload: dict) -> SignaturePresetCatalog:
    """Read the former combined-profile file shape without discarding user data."""
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, list):
        raise ConfigValidationError("Legacy signature profiles must be a list.")
    catalog = SignaturePresetCatalog(schema_version=1)
    for raw_profile in raw_profiles:
        if not isinstance(raw_profile, dict):
            raise ConfigValidationError("Legacy signature profile entries must be objects.")
        name = raw_profile.get("name")
        appearance_payload = raw_profile.get("appearance")
        if not isinstance(name, str) or not isinstance(appearance_payload, dict):
            raise ConfigValidationError("Legacy signature profile requires name and appearance.")
        appearance = AppearanceProfile(
            schema_version=1,
            appearance_profile_id=_stable_id("appearance", name),
            display_name=name,
            appearance=_deserialize_appearance(appearance_payload),
        )
        defaults = _deserialize_placement_defaults(raw_profile.get("placement_defaults"))
        # The legacy combined file has no page dimensions or rotation. Preserve
        # the appearance, but deliberately omit the incompatible placement rather
        # than inventing a fixed-page geometry.
        del defaults
        preset = ResolvedSignaturePreset.from_parts(
            name=name,
            appearance=appearance.appearance,
        )
        catalog = catalog.upsert_preset(preset)
    return catalog


def default_signature_profiles_directory(app_name: str = "FoliaSeal") -> Path:
    """Return the historical user-visible storage directory for signature presets."""
    data_home = os.environ.get("XDG_DATA_HOME")
    base_dir = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base_dir / app_name / PROFILE_DIRECTORY_NAME


@dataclass(frozen=True)
class SignaturePresetCatalogStore:
    """Read/write helper for the signature preset catalog on disk."""

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
        """Build a store rooted in the standard user-visible preset directory."""
        return cls(storage_dir=default_signature_profiles_directory(app_name=app_name))

    def load_catalog(self) -> SignaturePresetCatalog:
        """Load the catalog from disk, or return an empty catalog if missing."""
        path = self.catalog_path
        if not path.exists():
            return SignaturePresetCatalog(schema_version=1)

        payload_text = path.read_text(encoding="utf-8")
        if not payload_text.strip():
            return SignaturePresetCatalog(schema_version=1)

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                f"Signature preset catalog at '{path}' is not valid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigValidationError("Signature preset catalog must be a JSON object.")
        if "profiles" in payload and "appearance_profiles" not in payload:
            return _migrate_legacy_profiles(payload)
        return SignaturePresetCatalog.from_dict(payload)

    def save_catalog(self, catalog: SignaturePresetCatalog) -> None:
        """Persist the full catalog to disk in a human-readable JSON format."""
        if not isinstance(catalog, SignaturePresetCatalog):
            raise ConfigValidationError("catalog must be a SignaturePresetCatalog value.")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        payload_text = json.dumps(catalog.to_dict(), indent=2, sort_keys=True)
        temp_path = self.catalog_path.with_name(f"{self.catalog_path.name}.tmp")
        try:
            temp_path.write_text(f"{payload_text}\n", encoding="utf-8")
            temp_path.replace(self.catalog_path)
        finally:
            temp_path.unlink(missing_ok=True)
