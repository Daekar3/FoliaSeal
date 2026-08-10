"""Configuration schemas for phase 0 foundations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from foliaseal.domain.errors import ConfigValidationError
from foliaseal.domain.models import TimestampTrustPolicy


def _require_value(payload: dict[str, Any], field: str) -> Any:
    if field not in payload:
        raise ConfigValidationError(f"Field '{field}' is required.")
    return payload[field]


def _require_mapping(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = _require_value(payload, field)
    if not isinstance(value, dict):
        raise ConfigValidationError(f"Field '{field}' must be an object.")
    return value


def _optional_mapping(payload: dict[str, Any], field: str) -> dict[str, Any] | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ConfigValidationError(f"Field '{field}' must be an object when present.")
    return value


def _require_int(payload: dict[str, Any], field: str) -> int:
    value = _require_value(payload, field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"Field '{field}' must be an int.")
    return value


def _require_int_value(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigValidationError(f"Field '{field}' must be an int.")
    return value


def _require_float(payload: dict[str, Any], field: str) -> float:
    value = _require_value(payload, field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigValidationError(f"Field '{field}' must be a number.")
    return float(value)


def _require_bool(payload: dict[str, Any], field: str) -> bool:
    value = _require_value(payload, field)
    if not isinstance(value, bool):
        raise ConfigValidationError(f"Field '{field}' must be a bool.")
    return value


def _require_str(payload: dict[str, Any], field: str) -> str:
    value = _require_value(payload, field)
    if not isinstance(value, str):
        raise ConfigValidationError(f"Field '{field}' must be a str.")
    return value


def _require_non_empty_str(payload: dict[str, Any], field: str) -> str:
    value = _require_str(payload, field)
    if not value.strip():
        raise ConfigValidationError(f"Field '{field}' must be a non-empty str.")
    return value


def _require_non_empty_str_value(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(f"Field '{field}' must be a non-empty str.")
    return value


def _optional_str(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigValidationError(f"Field '{field}' must be a str when present.")
    return value


def _optional_non_empty_str(payload: dict[str, Any], field: str) -> str | None:
    value = _optional_str(payload, field)
    if value is None:
        return None
    if not value.strip():
        raise ConfigValidationError(f"Field '{field}' must be a non-empty str when present.")
    return value


def _copy_mapping(value: dict[str, Any]) -> dict[str, Any]:
    return dict(value)


def _require_optional_non_empty_str_value(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_str_value(value, field)



@dataclass(frozen=True)
class TrustProfile:
    """Trust and revocation behavior for validation/timestamping."""

    schema_version: int
    use_system_store: bool
    extra_ca_bundle_path: str | None
    revocation_mode: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TrustProfile:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            use_system_store=_require_bool(payload, "use_system_store"),
            extra_ca_bundle_path=_optional_str(payload, "extra_ca_bundle_path"),
            revocation_mode=_require_non_empty_str(payload, "revocation_mode"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return asdict(self)

    def to_timestamp_trust_policy(self) -> TimestampTrustPolicy:
        """Convert to the runtime timestamp trust policy model."""
        return TimestampTrustPolicy(
            use_system_store=self.use_system_store,
            extra_ca_bundle_path=self.extra_ca_bundle_path,
            revocation_mode=self.revocation_mode,
        )


@dataclass(frozen=True)
class TimestampPolicy:
    """RFC 3161 timestamp requirements and connectivity settings."""

    schema_version: int
    required: bool
    tsa_url: str
    timeout_seconds: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> TimestampPolicy:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            required=_require_bool(payload, "required"),
            tsa_url=_require_non_empty_str(payload, "tsa_url"),
            timeout_seconds=_require_int(payload, "timeout_seconds"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return asdict(self)


@dataclass(frozen=True)
class AppSettings:
    """Global application settings that are not reusable signing objects."""

    schema_version: int
    default_output_directory: str
    default_open_directory: str
    linux_packaging_channel: str
    ui: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "default_output_directory",
            _require_non_empty_str_value(
                self.default_output_directory,
                "default_output_directory",
            ),
        )
        object.__setattr__(
            self,
            "default_open_directory",
            _require_non_empty_str_value(
                self.default_open_directory,
                "default_open_directory",
            ),
        )
        object.__setattr__(
            self,
            "linux_packaging_channel",
            _require_non_empty_str_value(
                self.linux_packaging_channel,
                "linux_packaging_channel",
            ),
        )
        if not isinstance(self.ui, dict):
            raise ConfigValidationError("Field 'ui' must be an object.")
        object.__setattr__(self, "ui", _copy_mapping(self.ui))

    @classmethod
    def default(cls, home_directory: Path | str | None = None) -> AppSettings:
        """Build default settings with open/output directories rooted at home."""
        home = Path.home() if home_directory is None else Path(home_directory)
        return cls(
            schema_version=1,
            default_output_directory=str(home),
            default_open_directory=str(home),
            linux_packaging_channel="primary",
            ui={},
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AppSettings:
        """Build from persisted mapping."""
        ui_payload = _require_mapping(payload, "ui")
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            default_output_directory=_require_non_empty_str(
                payload,
                "default_output_directory",
            ),
            default_open_directory=_require_non_empty_str(
                payload,
                "default_open_directory",
            ),
            linux_packaging_channel=_require_non_empty_str(
                payload,
                "linux_packaging_channel",
            ),
            ui=_copy_mapping(ui_payload),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "default_output_directory": self.default_output_directory,
            "default_open_directory": self.default_open_directory,
            "linux_packaging_channel": self.linux_packaging_channel,
            "ui": _copy_mapping(self.ui),
        }

    @property
    def ui_settings(self):
        """Return the typed UI preference projection with safe legacy fallback."""

        from foliaseal.infra.config.app_settings_ui import AppUiSettings

        return AppUiSettings.from_mapping(self.ui)
