"""Configuration schemas for phase 0 foundations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
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
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
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
        signer_label_prefix=_require_non_empty_str(payload, "signer_label_prefix"),
        layout_template=_require_enum(payload, "layout_template", SignatureLayoutTemplate),  # type: ignore[arg-type]
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
class SignaturePreset:
    """Reusable visible signature appearance profile."""

    schema_version: int
    name: str
    appearance: SignatureAppearance
    placement_defaults: SignaturePlacementDefaults | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        object.__setattr__(self, "name", _require_non_empty_str_value(self.name, "name"))
        if not isinstance(self.appearance, SignatureAppearance):
            raise ConfigValidationError("Field 'appearance' must be a SignatureAppearance.")
        if self.placement_defaults is not None and not isinstance(
            self.placement_defaults,
            SignaturePlacementDefaults,
        ):
            raise ConfigValidationError(
                "Field 'placement_defaults' must be a SignaturePlacementDefaults value or None."
            )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignaturePreset:
        """Build from persisted mapping."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            name=_require_non_empty_str(payload, "name"),
            appearance=_deserialize_appearance(_require_mapping(payload, "appearance")),
            placement_defaults=_deserialize_placement_defaults(
                _optional_mapping(payload, "placement_defaults")
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "appearance": _serialize_appearance(self.appearance),
            "placement_defaults": _serialize_placement_defaults(self.placement_defaults),
        }


@dataclass(frozen=True)
class SignaturePresetCatalog:
    """Ordered collection of named signature profiles for dropdown selection."""

    schema_version: int
    profiles: tuple[SignaturePreset, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "schema_version",
            _require_int_value(self.schema_version, "schema_version"),
        )
        if not isinstance(self.profiles, tuple):
            raise ConfigValidationError("Field 'profiles' must be a tuple.")
        seen_names: set[str] = set()
        normalized_profiles: list[SignaturePreset] = []
        for profile in self.profiles:
            if not isinstance(profile, SignaturePreset):
                raise ConfigValidationError(
                    "Field 'profiles' must contain SignaturePreset values only."
                )
            if profile.name in seen_names:
                raise ConfigValidationError("Field 'profiles' must not contain duplicate names.")
            seen_names.add(profile.name)
            normalized_profiles.append(profile)
        object.__setattr__(self, "profiles", tuple(normalized_profiles))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignaturePresetCatalog:
        """Build from persisted mapping."""
        raw_profiles = _require_value(payload, "profiles")
        if not isinstance(raw_profiles, list):
            raise ConfigValidationError("Field 'profiles' must be a list.")
        profiles: list[SignaturePreset] = []
        for entry in raw_profiles:
            if not isinstance(entry, dict):
                raise ConfigValidationError("Field 'profiles' must contain objects only.")
            profiles.append(SignaturePreset.from_dict(entry))
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            profiles=tuple(profiles),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a persisted mapping."""
        return {
            "schema_version": self.schema_version,
            "profiles": [profile.to_dict() for profile in self.profiles],
        }

    def profile_names(self) -> tuple[str, ...]:
        """Return the profile names in stable dropdown order."""
        return tuple(profile.name for profile in self.profiles)

    def profile_named(self, name: str) -> SignaturePreset:
        """Return a profile by its user-visible name."""
        normalized_name = _require_non_empty_str_value(name, "name")
        for profile in self.profiles:
            if profile.name == normalized_name:
                return profile
        raise KeyError(normalized_name)

    def upsert_profile(self, profile: SignaturePreset) -> SignaturePresetCatalog:
        """Return a new catalog with the profile inserted or replaced by name."""
        if not isinstance(profile, SignaturePreset):
            raise ConfigValidationError("profile must be a SignaturePreset value.")
        updated: list[SignaturePreset] = []
        replaced = False
        for existing in self.profiles:
            if existing.name == profile.name:
                updated.append(profile)
                replaced = True
            else:
                updated.append(existing)
        if not replaced:
            updated.append(profile)
        return SignaturePresetCatalog(
            schema_version=self.schema_version,
            profiles=tuple(updated),
        )
