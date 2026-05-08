"""Configuration schemas for phase 0 foundations."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from foliaseal.domain.models import (
    SignatureAnchor,
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignaturePlacementDefaults,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    TimestampTrustPolicy,
)


class ConfigValidationError(ValueError):
    """Raised when a persisted config payload has invalid shape or types."""


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


def _require_optional_non_empty_str_value(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_str_value(value, field)


def _stable_id(prefix: str, display_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", display_name.strip().lower()).strip("-")
    if not normalized:
        normalized = "unnamed"
    return f"{prefix}-{normalized}"


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


def _enum_from_str(value: str, field: str, enum_cls: type[Enum]) -> Enum:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_cls)
        raise ConfigValidationError(
            f"Field '{field}' must be one of: {allowed}."
        ) from exc


def _require_enum(payload: dict[str, Any], field: str, enum_cls: type[Enum]) -> Enum:
    value = _require_str(payload, field)
    return _enum_from_str(value, field, enum_cls)


def _optional_enum(payload: dict[str, Any], field: str, enum_cls: type[Enum]) -> Enum | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigValidationError(f"Field '{field}' must be a str when present.")
    return _enum_from_str(value, field, enum_cls)


def _serialize_enum(value: Enum) -> str:
    return value.value


def _serialize_field_binding(binding: SignatureFieldBinding) -> dict[str, Any]:
    return {
        "source": _serialize_enum(binding.source),
        "show_in_visible_appearance": binding.show_in_visible_appearance,
        "override_text": binding.override_text,
        "display_label": binding.display_label,
    }


def _deserialize_field_binding(payload: dict[str, Any]) -> SignatureFieldBinding:
    return SignatureFieldBinding(
        source=_require_enum(payload, "source", SignatureFieldSource),  # type: ignore[arg-type]
        show_in_visible_appearance=_require_bool(payload, "show_in_visible_appearance"),
        override_text=_optional_non_empty_str(payload, "override_text"),
        display_label=_optional_non_empty_str(payload, "display_label"),
    )


def _serialize_text_style(value: SignatureTextStyle) -> dict[str, Any]:
    return asdict(value)


def _deserialize_text_style(payload: dict[str, Any]) -> SignatureTextStyle:
    return SignatureTextStyle(
        font_family=_require_non_empty_str(payload, "font_family"),
        font_size_pt=_require_float(payload, "font_size_pt"),
        bold=_require_bool(payload, "bold"),
        italic=_require_bool(payload, "italic"),
        text_color_hex=_require_str(payload, "text_color_hex"),
    )


def _serialize_appearance(value: SignatureAppearance) -> dict[str, Any]:
    return {
        "signer_label_prefix": value.signer_label_prefix,
        "layout_template": _serialize_enum(value.layout_template),
        "stamp_position": _serialize_enum(value.stamp_position),
        "timezone_display_mode": _serialize_enum(value.timezone_display_mode),
        "show_field_names": value.show_field_names,
        "datetime_format": value.datetime_format,
        "field_order": [field_key.value for field_key in value.field_order],
        "distinguished_name": _serialize_field_binding(value.distinguished_name),
        "common_name": _serialize_field_binding(value.common_name),
        "email": _serialize_field_binding(value.email),
        "signing_time": _serialize_field_binding(value.signing_time),
        "reason": _serialize_field_binding(value.reason),
        "location": _serialize_field_binding(value.location),
        "title": _serialize_field_binding(value.title),
        "company": _serialize_field_binding(value.company),
        "text_style": _serialize_text_style(value.text_style),
        "box_style": asdict(value.box_style),
        "image_stamp_path": value.image_stamp_path,
    }


def _deserialize_field_order(payload: dict[str, Any]) -> tuple[SignatureFieldKey, ...]:
    value = _require_value(payload, "field_order")
    if not isinstance(value, list):
        raise ConfigValidationError("Field 'field_order' must be a list.")

    order: list[SignatureFieldKey] = []
    for entry in value:
        if not isinstance(entry, str):
            raise ConfigValidationError("Field 'field_order' must contain strings only.")
        order.append(_enum_from_str(entry, "field_order", SignatureFieldKey))  # type: ignore[arg-type]
    return tuple(order)


def _deserialize_appearance(payload: dict[str, Any]) -> SignatureAppearance:
    box_style_payload = _require_mapping(payload, "box_style")
    return SignatureAppearance(
        signer_label_prefix=_require_str(payload, "signer_label_prefix").strip(),
        layout_template=_require_enum(payload, "layout_template", SignatureLayoutTemplate),  # type: ignore[arg-type]
        stamp_position=_optional_enum(
            payload,
            "stamp_position",
            SignatureStampPosition,
        )
        or SignatureStampPosition.TOP,
        timezone_display_mode=_require_enum(
            payload,
            "timezone_display_mode",
            SignatureTimezoneDisplayMode,
        ),  # type: ignore[arg-type]
        show_field_names=_require_bool(payload, "show_field_names"),
        datetime_format=_require_non_empty_str(payload, "datetime_format"),
        field_order=_deserialize_field_order(payload),
        distinguished_name=_deserialize_field_binding(
            _require_mapping(payload, "distinguished_name")
        ),
        common_name=_deserialize_field_binding(_require_mapping(payload, "common_name")),
        email=_deserialize_field_binding(_require_mapping(payload, "email")),
        signing_time=_deserialize_field_binding(_require_mapping(payload, "signing_time")),
        reason=_deserialize_field_binding(_require_mapping(payload, "reason")),
        location=_deserialize_field_binding(_require_mapping(payload, "location")),
        title=_deserialize_field_binding(_require_mapping(payload, "title")),
        company=_deserialize_field_binding(_require_mapping(payload, "company")),
        text_style=_deserialize_text_style(_require_mapping(payload, "text_style")),
        box_style=SignatureBoxStyle(
            show_border=_require_bool(box_style_payload, "show_border"),
            border_color_hex=_require_non_empty_str(
                box_style_payload,
                "border_color_hex",
            ),
            border_width_pt=_require_float(box_style_payload, "border_width_pt"),
            background_color_hex=_require_non_empty_str(
                box_style_payload,
                "background_color_hex",
            ),
        ),
        image_stamp_path=_optional_non_empty_str(payload, "image_stamp_path"),
    )


def _serialize_placement_defaults(
    value: SignaturePlacementDefaults | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "width_pt": value.width_pt,
        "height_pt": value.height_pt,
        "anchor": _serialize_enum(value.anchor),
    }


def _deserialize_placement_defaults(
    payload: dict[str, Any] | None,
) -> SignaturePlacementDefaults | None:
    if payload is None:
        return None
    return SignaturePlacementDefaults(
        width_pt=_require_float(payload, "width_pt"),
        height_pt=_require_float(payload, "height_pt"),
        anchor=_require_enum(payload, "anchor", SignatureAnchor),  # type: ignore[arg-type]
    )


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


@dataclass(frozen=True)
class ManagedCertificateSubjectSummary:
    """Non-secret certificate subject fields shown in certificate lists."""

    common_name: str | None = None
    email: str | None = None
    title: str | None = None
    company: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("common_name", "email", "title", "company"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_non_empty_str_value(getattr(self, field_name), field_name),
            )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ManagedCertificateSubjectSummary:
        """Build from persisted mapping."""
        return cls(
            common_name=_optional_non_empty_str(payload, "common_name"),
            email=_optional_non_empty_str(payload, "email"),
            title=_optional_non_empty_str(payload, "title"),
            company=_optional_non_empty_str(payload, "company"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "common_name": self.common_name,
            "email": self.email,
            "title": self.title,
            "company": self.company,
        }


@dataclass(frozen=True)
class ManagedCertificate:
    """Application-managed certificate file record."""

    schema_version: int
    managed_certificate_id: str
    display_name: str
    storage_filename: str
    source_kind: str
    created_at: str
    subject_summary: ManagedCertificateSubjectSummary

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "managed_certificate_id",
            _require_non_empty_str_value(self.managed_certificate_id, "managed_certificate_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        storage_filename = _require_non_empty_str_value(
            self.storage_filename,
            "storage_filename",
        )
        if "/" in storage_filename or "\\" in storage_filename or storage_filename in {
            ".",
            "..",
        }:
            raise ConfigValidationError(
                "Field 'storage_filename' must be a filename, not a path."
            )
        object.__setattr__(self, "storage_filename", storage_filename)
        source_kind = _require_non_empty_str_value(self.source_kind, "source_kind")
        if source_kind not in {"created", "imported"}:
            raise ConfigValidationError("Field 'source_kind' must be 'created' or 'imported'.")
        object.__setattr__(self, "source_kind", source_kind)
        object.__setattr__(
            self,
            "created_at",
            _require_non_empty_str_value(self.created_at, "created_at"),
        )
        if not isinstance(self.subject_summary, ManagedCertificateSubjectSummary):
            raise ConfigValidationError(
                "Field 'subject_summary' must be a ManagedCertificateSubjectSummary."
            )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ManagedCertificate:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            managed_certificate_id=_require_non_empty_str(payload, "managed_certificate_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            storage_filename=_require_non_empty_str(payload, "storage_filename"),
            source_kind=_require_non_empty_str(payload, "source_kind"),
            created_at=_require_non_empty_str(payload, "created_at"),
            subject_summary=ManagedCertificateSubjectSummary.from_dict(
                _require_mapping(payload, "subject_summary")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "managed_certificate_id": self.managed_certificate_id,
            "display_name": self.display_name,
            "storage_filename": self.storage_filename,
            "source_kind": self.source_kind,
            "created_at": self.created_at,
            "subject_summary": self.subject_summary.to_dict(),
        }


@dataclass(frozen=True)
class CertificateConfiguration:
    """User-facing signing identity configuration."""

    schema_version: int
    certificate_configuration_id: str
    display_name: str
    managed_certificate_id: str
    save_password: bool
    password_secret_ref: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "certificate_configuration_id",
            _require_non_empty_str_value(
                self.certificate_configuration_id,
                "certificate_configuration_id",
            ),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        object.__setattr__(
            self,
            "managed_certificate_id",
            _require_non_empty_str_value(self.managed_certificate_id, "managed_certificate_id"),
        )
        object.__setattr__(
            self,
            "save_password",
            bool(_require_bool(asdict(self), "save_password")),
        )
        object.__setattr__(
            self,
            "password_secret_ref",
            _require_optional_non_empty_str_value(self.password_secret_ref, "password_secret_ref"),
        )
        if self.save_password and self.password_secret_ref is None:
            raise ConfigValidationError(
                "Field 'password_secret_ref' is required when 'save_password' is true."
            )
        if not self.save_password and self.password_secret_ref is not None:
            raise ConfigValidationError(
                "Field 'password_secret_ref' must be null when 'save_password' is false."
            )
        object.__setattr__(
            self,
            "notes",
            _require_optional_non_empty_str_value(self.notes, "notes"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CertificateConfiguration:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            certificate_configuration_id=_require_non_empty_str(
                payload,
                "certificate_configuration_id",
            ),
            display_name=_require_non_empty_str(payload, "display_name"),
            managed_certificate_id=_require_non_empty_str(payload, "managed_certificate_id"),
            save_password=_require_bool(payload, "save_password"),
            password_secret_ref=_optional_non_empty_str(payload, "password_secret_ref"),
            notes=_optional_non_empty_str(payload, "notes"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "certificate_configuration_id": self.certificate_configuration_id,
            "display_name": self.display_name,
            "managed_certificate_id": self.managed_certificate_id,
            "save_password": self.save_password,
            "password_secret_ref": self.password_secret_ref,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class CertificateCatalog:
    """Catalog of managed certificates and certificate configurations."""

    schema_version: int
    managed_certificates: tuple[ManagedCertificate, ...] = ()
    certificate_configurations: tuple[CertificateConfiguration, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        self._validate_object_tuple(
            self.managed_certificates,
            ManagedCertificate,
            "managed_certificates",
            "managed_certificate_id",
        )
        self._validate_object_tuple(
            self.certificate_configurations,
            CertificateConfiguration,
            "certificate_configurations",
            "certificate_configuration_id",
        )
        seen_names: set[str] = set()
        for configuration in self.certificate_configurations:
            if configuration.display_name in seen_names:
                raise ConfigValidationError(
                    "Field 'certificate_configurations' must not contain duplicate names."
                )
            seen_names.add(configuration.display_name)

    @staticmethod
    def _validate_object_tuple(
        values: tuple[Any, ...],
        expected_type: type,
        field_name: str,
        id_field_name: str,
    ) -> None:
        if not isinstance(values, tuple):
            raise ConfigValidationError(f"Field '{field_name}' must be a tuple.")
        seen_ids: set[str] = set()
        for value in values:
            if not isinstance(value, expected_type):
                raise ConfigValidationError(
                    f"Field '{field_name}' must contain {expected_type.__name__} values only."
                )
            object_id = getattr(value, id_field_name)
            if object_id in seen_ids:
                raise ConfigValidationError(
                    f"Field '{field_name}' must not contain duplicate ids."
                )
            seen_ids.add(object_id)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CertificateCatalog:
        """Build from persisted mapping."""
        raw_managed_certificates = _require_value(payload, "managed_certificates")
        raw_certificate_configurations = _require_value(payload, "certificate_configurations")
        for field_name, raw_entries in (
            ("managed_certificates", raw_managed_certificates),
            ("certificate_configurations", raw_certificate_configurations),
        ):
            if not isinstance(raw_entries, list):
                raise ConfigValidationError(f"Field '{field_name}' must be a list.")

        managed_certificates: list[ManagedCertificate] = []
        for entry in raw_managed_certificates:
            if not isinstance(entry, dict):
                raise ConfigValidationError(
                    "Field 'managed_certificates' must contain objects only."
                )
            managed_certificates.append(ManagedCertificate.from_dict(entry))
        certificate_configurations: list[CertificateConfiguration] = []
        for entry in raw_certificate_configurations:
            if not isinstance(entry, dict):
                raise ConfigValidationError(
                    "Field 'certificate_configurations' must contain objects only."
                )
            certificate_configurations.append(CertificateConfiguration.from_dict(entry))
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            managed_certificates=tuple(managed_certificates),
            certificate_configurations=tuple(certificate_configurations),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "managed_certificates": [
                certificate.to_dict() for certificate in self.managed_certificates
            ],
            "certificate_configurations": [
                configuration.to_dict()
                for configuration in self.certificate_configurations
            ],
        }

    def configuration_named(self, name: str) -> CertificateConfiguration:
        """Return a certificate configuration by display name."""
        normalized_name = _require_non_empty_str_value(name, "name")
        for configuration in self.certificate_configurations:
            if configuration.display_name == normalized_name:
                return configuration
        raise KeyError(normalized_name)

    def configuration_by_id(self, configuration_id: str) -> CertificateConfiguration:
        """Return a certificate configuration by stable id."""
        normalized_id = _require_non_empty_str_value(
            configuration_id,
            "certificate_configuration_id",
        )
        for configuration in self.certificate_configurations:
            if configuration.certificate_configuration_id == normalized_id:
                return configuration
        raise KeyError(normalized_id)

    def managed_certificate_by_id(self, certificate_id: str) -> ManagedCertificate:
        """Return a managed certificate by stable id."""
        normalized_id = _require_non_empty_str_value(
            certificate_id,
            "managed_certificate_id",
        )
        for certificate in self.managed_certificates:
            if certificate.managed_certificate_id == normalized_id:
                return certificate
        raise KeyError(normalized_id)

    def upsert_managed_certificate(
        self,
        certificate: ManagedCertificate,
    ) -> CertificateCatalog:
        """Return a catalog with a managed certificate inserted or replaced."""
        if not isinstance(certificate, ManagedCertificate):
            raise ConfigValidationError("certificate must be a ManagedCertificate value.")
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=tuple(
                self._upsert_by_id(
                    list(self.managed_certificates),
                    certificate,
                    "managed_certificate_id",
                )
            ),
            certificate_configurations=self.certificate_configurations,
        )

    def upsert_configuration(
        self,
        configuration: CertificateConfiguration,
    ) -> CertificateCatalog:
        """Return a catalog with a certificate configuration inserted or replaced."""
        if not isinstance(configuration, CertificateConfiguration):
            raise ConfigValidationError(
                "configuration must be a CertificateConfiguration value."
            )
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=self.managed_certificates,
            certificate_configurations=tuple(
                self._upsert_by_id(
                    list(self.certificate_configurations),
                    configuration,
                    "certificate_configuration_id",
                )
            ),
        )

    @staticmethod
    def _upsert_by_id(values: list[Any], replacement: Any, id_field_name: str) -> list[Any]:
        updated: list[Any] = []
        replaced = False
        replacement_id = getattr(replacement, id_field_name)
        for value in values:
            if getattr(value, id_field_name) == replacement_id:
                updated.append(replacement)
                replaced = True
            else:
                updated.append(value)
        if not replaced:
            updated.append(replacement)
        return updated

    def remove_configuration(self, name: str) -> CertificateCatalog:
        """Return a catalog without the named certificate configuration."""
        normalized_name = _require_non_empty_str_value(name, "name")
        updated_configurations = tuple(
            configuration
            for configuration in self.certificate_configurations
            if configuration.display_name != normalized_name
        )
        if len(updated_configurations) == len(self.certificate_configurations):
            raise KeyError(normalized_name)
        return CertificateCatalog(
            schema_version=self.schema_version,
            managed_certificates=self.managed_certificates,
            certificate_configurations=updated_configurations,
        )


@dataclass(frozen=True)
class PlacementProfileRect:
    """PDF-space rectangle data persisted in a placement profile."""

    left_pt: float
    bottom_pt: float
    width_pt: float
    height_pt: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "left_pt", _require_float(asdict(self), "left_pt"))
        object.__setattr__(self, "bottom_pt", _require_float(asdict(self), "bottom_pt"))
        object.__setattr__(self, "width_pt", _require_float(asdict(self), "width_pt"))
        object.__setattr__(self, "height_pt", _require_float(asdict(self), "height_pt"))
        if self.width_pt <= 0:
            raise ConfigValidationError("Field 'width_pt' must be positive.")
        if self.height_pt <= 0:
            raise ConfigValidationError("Field 'height_pt' must be positive.")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PlacementProfileRect:
        """Build from persisted mapping."""
        return cls(
            left_pt=_require_float(payload, "left_pt"),
            bottom_pt=_require_float(payload, "bottom_pt"),
            width_pt=_require_float(payload, "width_pt"),
            height_pt=_require_float(payload, "height_pt"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return asdict(self)


@dataclass(frozen=True)
class AppearanceProfile:
    """Reusable visible-signature appearance profile."""

    schema_version: int
    appearance_profile_id: str
    display_name: str
    appearance: SignatureAppearance

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "appearance_profile_id",
            _require_non_empty_str_value(self.appearance_profile_id, "appearance_profile_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        if not isinstance(self.appearance, SignatureAppearance):
            raise ConfigValidationError("Field 'appearance' must be a SignatureAppearance.")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AppearanceProfile:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            appearance_profile_id=_require_non_empty_str(payload, "appearance_profile_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            appearance=_deserialize_appearance(_require_mapping(payload, "appearance")),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "appearance_profile_id": self.appearance_profile_id,
            "display_name": self.display_name,
            "appearance": _serialize_appearance(self.appearance),
        }

    @property
    def name(self) -> str:
        """Compatibility alias for older profile-oriented call sites."""
        return self.display_name


@dataclass(frozen=True)
class PlacementProfile:
    """Reusable visible-signature placement profile."""

    schema_version: int
    placement_profile_id: str
    display_name: str
    page_selection_mode: str
    rect: PlacementProfileRect
    numeric_fine_tuning_enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "placement_profile_id",
            _require_non_empty_str_value(self.placement_profile_id, "placement_profile_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        object.__setattr__(
            self,
            "page_selection_mode",
            _require_non_empty_str_value(self.page_selection_mode, "page_selection_mode"),
        )
        if not isinstance(self.rect, PlacementProfileRect):
            raise ConfigValidationError("Field 'rect' must be a PlacementProfileRect.")
        object.__setattr__(
            self,
            "numeric_fine_tuning_enabled",
            _require_bool(asdict(self), "numeric_fine_tuning_enabled"),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PlacementProfile:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            placement_profile_id=_require_non_empty_str(payload, "placement_profile_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            page_selection_mode=_require_non_empty_str(payload, "page_selection_mode"),
            rect=PlacementProfileRect.from_dict(_require_mapping(payload, "rect")),
            numeric_fine_tuning_enabled=_require_bool(
                payload,
                "numeric_fine_tuning_enabled",
            ),
        )

    @classmethod
    def from_defaults(
        cls,
        *,
        display_name: str,
        placement_defaults: SignaturePlacementDefaults,
        schema_version: int = 1,
        placement_profile_id: str | None = None,
    ) -> PlacementProfile:
        """Build a placement profile from the old width/height default shape."""
        return cls(
            schema_version=schema_version,
            placement_profile_id=placement_profile_id
            or _stable_id("placement", display_name),
            display_name=display_name,
            page_selection_mode="current_page",
            rect=PlacementProfileRect(
                left_pt=0.0,
                bottom_pt=0.0,
                width_pt=placement_defaults.width_pt,
                height_pt=placement_defaults.height_pt,
            ),
            numeric_fine_tuning_enabled=True,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "placement_profile_id": self.placement_profile_id,
            "display_name": self.display_name,
            "page_selection_mode": self.page_selection_mode,
            "rect": self.rect.to_dict(),
            "numeric_fine_tuning_enabled": self.numeric_fine_tuning_enabled,
        }

    @property
    def name(self) -> str:
        """Compatibility alias for older profile-oriented call sites."""
        return self.display_name

    @property
    def placement_defaults(self) -> SignaturePlacementDefaults:
        """Return the width/height defaults expected by the current Qt shell."""
        return SignaturePlacementDefaults(
            width_pt=self.rect.width_pt,
            height_pt=self.rect.height_pt,
        )


@dataclass(frozen=True)
class SignaturePreset:
    """Reference-only reusable signature preset."""

    schema_version: int
    signature_preset_id: str
    display_name: str
    certificate_configuration_id: str | None = None
    appearance_profile_id: str | None = None
    placement_profile_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(
            self,
            "signature_preset_id",
            _require_non_empty_str_value(self.signature_preset_id, "signature_preset_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            _require_non_empty_str_value(self.display_name, "display_name"),
        )
        for field_name in (
            "certificate_configuration_id",
            "appearance_profile_id",
            "placement_profile_id",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_non_empty_str_value(getattr(self, field_name), field_name),
            )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignaturePreset:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            signature_preset_id=_require_non_empty_str(payload, "signature_preset_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            certificate_configuration_id=_optional_non_empty_str(
                payload,
                "certificate_configuration_id",
            ),
            appearance_profile_id=_optional_non_empty_str(payload, "appearance_profile_id"),
            placement_profile_id=_optional_non_empty_str(payload, "placement_profile_id"),
        )

    @classmethod
    def from_profile_parts(
        cls,
        *,
        display_name: str,
        appearance_profile_id: str,
        placement_profile_id: str | None = None,
        schema_version: int = 1,
        signature_preset_id: str | None = None,
    ) -> SignaturePreset:
        """Build a preset for the current combined save/select UI."""
        return cls(
            schema_version=schema_version,
            signature_preset_id=signature_preset_id or _stable_id("preset", display_name),
            display_name=display_name,
            appearance_profile_id=appearance_profile_id,
            placement_profile_id=placement_profile_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "signature_preset_id": self.signature_preset_id,
            "display_name": self.display_name,
            "certificate_configuration_id": self.certificate_configuration_id,
            "appearance_profile_id": self.appearance_profile_id,
            "placement_profile_id": self.placement_profile_id,
        }

    @property
    def name(self) -> str:
        """Compatibility alias for older profile-oriented call sites."""
        return self.display_name


@dataclass(frozen=True)
class ResolvedSignaturePreset:
    """Resolved preset data used by current shell and harness call sites."""

    preset: SignaturePreset
    appearance_profile: AppearanceProfile | None
    placement_profile: PlacementProfile | None = None

    @property
    def name(self) -> str:
        return self.preset.display_name

    @property
    def appearance(self) -> SignatureAppearance:
        if self.appearance_profile is None:
            raise ConfigValidationError(
                f"Signature preset '{self.name}' does not reference an appearance profile."
            )
        return self.appearance_profile.appearance

    @property
    def placement_defaults(self) -> SignaturePlacementDefaults | None:
        if self.placement_profile is None:
            return None
        return self.placement_profile.placement_defaults

    @classmethod
    def from_parts(
        cls,
        *,
        name: str,
        appearance: SignatureAppearance,
        placement_defaults: SignaturePlacementDefaults | None = None,
        schema_version: int = 1,
    ) -> ResolvedSignaturePreset:
        appearance_profile = AppearanceProfile(
            schema_version=schema_version,
            appearance_profile_id=_stable_id("appearance", name),
            display_name=name,
            appearance=appearance,
        )
        placement_profile = (
            PlacementProfile.from_defaults(
                schema_version=schema_version,
                display_name=name,
                placement_defaults=placement_defaults,
            )
            if placement_defaults is not None
            else None
        )
        return cls(
            preset=SignaturePreset.from_profile_parts(
                schema_version=schema_version,
                display_name=name,
                appearance_profile_id=appearance_profile.appearance_profile_id,
                placement_profile_id=(
                    placement_profile.placement_profile_id if placement_profile else None
                ),
            ),
            appearance_profile=appearance_profile,
            placement_profile=placement_profile,
        )


@dataclass(frozen=True)
class SignaturePresetCatalog:
    """Catalog of canonical reusable signing objects."""

    schema_version: int
    appearance_profiles: tuple[AppearanceProfile, ...] = ()
    placement_profiles: tuple[PlacementProfile, ...] = ()
    signature_presets: tuple[SignaturePreset, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        self._validate_object_tuple(
            self.appearance_profiles,
            AppearanceProfile,
            "appearance_profiles",
            "appearance_profile_id",
        )
        self._validate_object_tuple(
            self.placement_profiles,
            PlacementProfile,
            "placement_profiles",
            "placement_profile_id",
        )
        self._validate_object_tuple(
            self.signature_presets,
            SignaturePreset,
            "signature_presets",
            "signature_preset_id",
        )
        seen_preset_names: set[str] = set()
        for preset in self.signature_presets:
            if preset.display_name in seen_preset_names:
                raise ConfigValidationError(
                    "Field 'signature_presets' must not contain duplicate names."
                )
            seen_preset_names.add(preset.display_name)

    @staticmethod
    def _validate_object_tuple(
        values: tuple[Any, ...],
        expected_type: type,
        field_name: str,
        id_field_name: str,
    ) -> None:
        if not isinstance(values, tuple):
            raise ConfigValidationError(f"Field '{field_name}' must be a tuple.")
        seen_ids: set[str] = set()
        for value in values:
            if not isinstance(value, expected_type):
                raise ConfigValidationError(
                    f"Field '{field_name}' must contain {expected_type.__name__} values only."
                )
            object_id = getattr(value, id_field_name)
            if object_id in seen_ids:
                raise ConfigValidationError(
                    f"Field '{field_name}' must not contain duplicate ids."
                )
            seen_ids.add(object_id)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignaturePresetCatalog:
        """Build from persisted mapping."""
        raw_appearance_profiles = _require_value(payload, "appearance_profiles")
        raw_placement_profiles = _require_value(payload, "placement_profiles")
        raw_signature_presets = _require_value(payload, "signature_presets")
        for field_name, raw_entries in (
            ("appearance_profiles", raw_appearance_profiles),
            ("placement_profiles", raw_placement_profiles),
            ("signature_presets", raw_signature_presets),
        ):
            if not isinstance(raw_entries, list):
                raise ConfigValidationError(f"Field '{field_name}' must be a list.")

        appearance_profiles: list[AppearanceProfile] = []
        for entry in raw_appearance_profiles:
            if not isinstance(entry, dict):
                raise ConfigValidationError(
                    "Field 'appearance_profiles' must contain objects only."
                )
            appearance_profiles.append(AppearanceProfile.from_dict(entry))
        placement_profiles: list[PlacementProfile] = []
        for entry in raw_placement_profiles:
            if not isinstance(entry, dict):
                raise ConfigValidationError(
                    "Field 'placement_profiles' must contain objects only."
                )
            placement_profiles.append(PlacementProfile.from_dict(entry))
        signature_presets: list[SignaturePreset] = []
        for entry in raw_signature_presets:
            if not isinstance(entry, dict):
                raise ConfigValidationError(
                    "Field 'signature_presets' must contain objects only."
                )
            signature_presets.append(SignaturePreset.from_dict(entry))
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            appearance_profiles=tuple(appearance_profiles),
            placement_profiles=tuple(placement_profiles),
            signature_presets=tuple(signature_presets),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "appearance_profiles": [
                profile.to_dict() for profile in self.appearance_profiles
            ],
            "placement_profiles": [
                profile.to_dict() for profile in self.placement_profiles
            ],
            "signature_presets": [preset.to_dict() for preset in self.signature_presets],
        }

    def preset_names(self) -> tuple[str, ...]:
        """Return preset display names in stable dropdown order."""
        return tuple(preset.display_name for preset in self.signature_presets)

    def preset_named(self, name: str) -> ResolvedSignaturePreset:
        """Return a resolved preset by its user-visible name."""
        normalized_name = _require_non_empty_str_value(name, "name")
        for preset in self.signature_presets:
            if preset.display_name == normalized_name:
                return self.resolve_preset(preset)
        raise KeyError(normalized_name)

    def appearance_profile_named(self, name: str) -> AppearanceProfile:
        """Return an appearance profile by display name."""
        normalized_name = _require_non_empty_str_value(name, "name")
        for profile in self.appearance_profiles:
            if profile.display_name == normalized_name:
                return profile
        raise KeyError(normalized_name)

    def placement_profile_named(self, name: str) -> PlacementProfile:
        """Return a placement profile by display name."""
        normalized_name = _require_non_empty_str_value(name, "name")
        for profile in self.placement_profiles:
            if profile.display_name == normalized_name:
                return profile
        raise KeyError(normalized_name)

    def resolve_preset(self, preset: SignaturePreset) -> ResolvedSignaturePreset:
        """Resolve a reference-only preset to the objects it points at."""
        appearance_profile = None
        if preset.appearance_profile_id is not None:
            appearance_profile = self._appearance_profile_by_id(preset.appearance_profile_id)
        placement_profile = None
        if preset.placement_profile_id is not None:
            placement_profile = self._placement_profile_by_id(preset.placement_profile_id)
        return ResolvedSignaturePreset(
            preset=preset,
            appearance_profile=appearance_profile,
            placement_profile=placement_profile,
        )

    def _appearance_profile_by_id(self, profile_id: str) -> AppearanceProfile:
        for profile in self.appearance_profiles:
            if profile.appearance_profile_id == profile_id:
                return profile
        raise KeyError(profile_id)

    def _placement_profile_by_id(self, profile_id: str) -> PlacementProfile:
        for profile in self.placement_profiles:
            if profile.placement_profile_id == profile_id:
                return profile
        raise KeyError(profile_id)

    def upsert_preset(self, preset: ResolvedSignaturePreset) -> SignaturePresetCatalog:
        """Return a new catalog with a resolved preset inserted or replaced by name."""
        if not isinstance(preset, ResolvedSignaturePreset):
            raise ConfigValidationError("preset must be a ResolvedSignaturePreset value.")
        appearance_profiles = list(self.appearance_profiles)
        placement_profiles = list(self.placement_profiles)
        signature_presets = list(self.signature_presets)

        if preset.appearance_profile is not None:
            appearance_profiles = self._upsert_by_id(
                appearance_profiles,
                preset.appearance_profile,
                "appearance_profile_id",
            )
        if preset.placement_profile is not None:
            placement_profiles = self._upsert_by_id(
                placement_profiles,
                preset.placement_profile,
                "placement_profile_id",
            )

        replaced = False
        updated_presets: list[SignaturePreset] = []
        for existing in signature_presets:
            if existing.display_name == preset.name:
                updated_presets.append(preset.preset)
                replaced = True
            else:
                updated_presets.append(existing)
        if not replaced:
            updated_presets.append(preset.preset)
        return SignaturePresetCatalog(
            schema_version=self.schema_version,
            appearance_profiles=tuple(appearance_profiles),
            placement_profiles=tuple(placement_profiles),
            signature_presets=tuple(updated_presets),
        )

    @staticmethod
    def _upsert_by_id(values: list[Any], replacement: Any, id_field_name: str) -> list[Any]:
        updated: list[Any] = []
        replaced = False
        replacement_id = getattr(replacement, id_field_name)
        for value in values:
            if getattr(value, id_field_name) == replacement_id:
                updated.append(replacement)
                replaced = True
            else:
                updated.append(value)
        if not replaced:
            updated.append(replacement)
        return updated

    def remove_preset(self, name: str) -> SignaturePresetCatalog:
        """Return a new catalog without the named preset."""
        normalized_name = _require_non_empty_str_value(name, "name")
        preset_to_remove: SignaturePreset | None = None
        updated_presets: list[SignaturePreset] = []
        for preset in self.signature_presets:
            if preset.display_name == normalized_name:
                preset_to_remove = preset
            else:
                updated_presets.append(preset)
        if preset_to_remove is None:
            raise KeyError(normalized_name)
        referenced_appearance_ids = {
            preset.appearance_profile_id
            for preset in updated_presets
            if preset.appearance_profile_id is not None
        }
        referenced_placement_ids = {
            preset.placement_profile_id
            for preset in updated_presets
            if preset.placement_profile_id is not None
        }
        appearance_profiles = tuple(
            profile
            for profile in self.appearance_profiles
            if profile.appearance_profile_id in referenced_appearance_ids
            or profile.appearance_profile_id != preset_to_remove.appearance_profile_id
        )
        placement_profiles = tuple(
            profile
            for profile in self.placement_profiles
            if profile.placement_profile_id in referenced_placement_ids
            or profile.placement_profile_id != preset_to_remove.placement_profile_id
        )
        return SignaturePresetCatalog(
            schema_version=self.schema_version,
            appearance_profiles=appearance_profiles,
            placement_profiles=placement_profiles,
            signature_presets=tuple(updated_presets),
        )
