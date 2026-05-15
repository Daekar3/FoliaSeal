"""Persistent storage helpers for global application settings."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from foliaseal.infra.config.schemas import AppSettings, ConfigValidationError

APP_SETTINGS_FILENAME = "settings.json"


def default_app_settings_directory(app_name: str = "FoliaSeal") -> Path:
    """Return the default Linux config directory for app settings."""
    config_home = os.environ.get("XDG_CONFIG_HOME")
    base_dir = Path(config_home) if config_home else Path.home() / ".config"
    return base_dir / app_name


@dataclass(frozen=True)
class AppSettingsStore:
    """Read/write helper for global app settings."""

    storage_dir: Path
    settings_filename: str = APP_SETTINGS_FILENAME
    default_home_directory: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "storage_dir", Path(self.storage_dir))
        if not isinstance(self.settings_filename, str) or not self.settings_filename.strip():
            raise ConfigValidationError("settings_filename must be a non-empty str.")
        if self.default_home_directory is not None:
            object.__setattr__(
                self,
                "default_home_directory",
                Path(self.default_home_directory),
            )

    @property
    def settings_path(self) -> Path:
        """Return the on-disk JSON settings path."""
        return self.storage_dir / self.settings_filename

    @classmethod
    def default(cls, app_name: str = "FoliaSeal") -> AppSettingsStore:
        """Build a store rooted in the standard Linux config directory."""
        return cls(storage_dir=default_app_settings_directory(app_name=app_name))

    def load_settings(self) -> AppSettings:
        """Load settings from disk, or return defaults if missing."""
        path = self.settings_path
        if not path.exists():
            return self._default_settings()

        payload_text = path.read_text(encoding="utf-8")
        if not payload_text.strip():
            return self._default_settings()

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                f"App settings at '{path}' is not valid JSON."
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigValidationError("App settings must be a JSON object.")
        return AppSettings.from_dict(payload)

    def save_settings(self, settings: AppSettings) -> None:
        """Persist settings to disk as human-readable JSON."""
        if not isinstance(settings, AppSettings):
            raise ConfigValidationError("settings must be an AppSettings value.")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        payload_text = json.dumps(settings.to_dict(), indent=2, sort_keys=True)
        temp_path = self.settings_path.with_name(f"{self.settings_path.name}.tmp")
        try:
            temp_path.write_text(f"{payload_text}\n", encoding="utf-8")
            temp_path.replace(self.settings_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            raise

    def _default_settings(self) -> AppSettings:
        return AppSettings.default(home_directory=self.default_home_directory)
