"""Application-owned reusable signing-object models and catalog policy.

The models in this module describe reusable signing behavior. JSON encoding and
filesystem ownership remain at the infrastructure edge. Placement profiles are
validated here against the schema-approved fixed-page v2 contract so persistence
cannot emit the retired current-page/bottom-left shape.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any

from foliaseal.domain.errors import ConfigValidationError
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
)

ReusableObjectValidationError = ConfigValidationError


def _require_value(payload: dict[str, Any], field: str) -> Any:
    if field not in payload:
        raise ReusableObjectValidationError(f"Field '{field}' is required.")
    return payload[field]


def _require_mapping(payload: dict[str, Any], field: str) -> dict[str, Any]:
    value = _require_value(payload, field)
    if not isinstance(value, dict):
        raise ReusableObjectValidationError(f"Field '{field}' must be an object.")
    return value


def _require_int(payload: dict[str, Any], field: str) -> int:
    value = _require_value(payload, field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReusableObjectValidationError(f"Field '{field}' must be an int.")
    return value


def _require_int_value(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReusableObjectValidationError(f"Field '{field}' must be an int.")
    return value


def _require_float(payload: dict[str, Any], field: str) -> float:
    value = _require_value(payload, field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReusableObjectValidationError(f"Field '{field}' must be a number.")
    return float(value)


def _require_bool(payload: dict[str, Any], field: str) -> bool:
    value = _require_value(payload, field)
    if not isinstance(value, bool):
        raise ReusableObjectValidationError(f"Field '{field}' must be a bool.")
    return value


def _require_str(payload: dict[str, Any], field: str) -> str:
    value = _require_value(payload, field)
    if not isinstance(value, str):
        raise ReusableObjectValidationError(f"Field '{field}' must be a str.")
    return value


def _require_non_empty_str(payload: dict[str, Any], field: str) -> str:
    value = _require_str(payload, field)
    value = value.strip()
    if not value:
        raise ReusableObjectValidationError(f"Field '{field}' must be a non-empty str.")
    return value


def _require_non_empty_str_value(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReusableObjectValidationError(f"Field '{field}' must be a non-empty str.")
    return value.strip()


def _optional_non_empty_str(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ReusableObjectValidationError(
            f"Field '{field}' must be a non-empty str when present."
        )
    return value


def _require_optional_non_empty_str_value(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_str_value(value, field)


def _stable_id(prefix: str, display_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", display_name.strip().lower()).strip("-") or "unnamed"
    return f"{prefix}-{normalized}"


def _enum_from_str(value: str, field: str, enum_cls: type[Enum]) -> Enum:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_cls)
        raise ReusableObjectValidationError(f"Field '{field}' must be one of: {allowed}.") from exc


def _require_enum(payload: dict[str, Any], field: str, enum_cls: type[Enum]) -> Enum:
    return _enum_from_str(_require_str(payload, field), field, enum_cls)


def _optional_enum(payload: dict[str, Any], field: str, enum_cls: type[Enum]) -> Enum | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ReusableObjectValidationError(f"Field '{field}' must be a str when present.")
    return _enum_from_str(value, field, enum_cls)


def _serialize_field_binding(binding: SignatureFieldBinding) -> dict[str, Any]:
    return {
        "source": binding.source.value,
        "show_in_visible_appearance": binding.show_in_visible_appearance,
        "override_text": binding.override_text,
        "display_label": binding.display_label,
    }


def _deserialize_field_binding(payload: dict[str, Any]) -> SignatureFieldBinding:
    override_text = payload.get("override_text")
    display_label = payload.get("display_label")
    if override_text is not None and (
        not isinstance(override_text, str) or not override_text.strip()
    ):
        raise ReusableObjectValidationError(
            "Field 'override_text' must be a non-empty str when present."
        )
    if display_label is not None and (
        not isinstance(display_label, str) or not display_label.strip()
    ):
        raise ReusableObjectValidationError(
            "Field 'display_label' must be a non-empty str when present."
        )
    return SignatureFieldBinding(
        source=_require_enum(payload, "source", SignatureFieldSource),  # type: ignore[arg-type]
        show_in_visible_appearance=_require_bool(payload, "show_in_visible_appearance"),
        override_text=override_text,
        display_label=display_label,
    )


def _serialize_appearance(value: SignatureAppearance) -> dict[str, Any]:
    return {
        "signer_label_prefix": value.signer_label_prefix,
        "layout_template": value.layout_template.value,
        "stamp_position": value.stamp_position.value,
        "timezone_display_mode": value.timezone_display_mode.value,
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
        "text_style": asdict(value.text_style),
        "box_style": asdict(value.box_style),
        "image_stamp_path": value.image_stamp_path,
    }


def _deserialize_appearance(payload: dict[str, Any]) -> SignatureAppearance:
    field_order = _require_value(payload, "field_order")
    if not isinstance(field_order, list) or not all(isinstance(item, str) for item in field_order):
        raise ReusableObjectValidationError("Field 'field_order' must be a list of strings.")
    text_payload = _require_mapping(payload, "text_style")
    box_payload = _require_mapping(payload, "box_style")
    return SignatureAppearance(
        signer_label_prefix=_require_str(payload, "signer_label_prefix").strip(),
        layout_template=_require_enum(payload, "layout_template", SignatureLayoutTemplate),  # type: ignore[arg-type]
        stamp_position=_optional_enum(payload, "stamp_position", SignatureStampPosition)
        or SignatureStampPosition.TOP,
        timezone_display_mode=_require_enum(
            payload, "timezone_display_mode", SignatureTimezoneDisplayMode
        ),  # type: ignore[arg-type]
        show_field_names=_require_bool(payload, "show_field_names"),
        datetime_format=_require_non_empty_str(payload, "datetime_format"),
        field_order=tuple(
            _enum_from_str(item, "field_order", SignatureFieldKey) for item in field_order
        ),  # type: ignore[arg-type]
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
        text_style=SignatureTextStyle(
            font_family=_require_non_empty_str(text_payload, "font_family"),
            font_size_pt=_require_float(text_payload, "font_size_pt"),
            bold=_require_bool(text_payload, "bold"),
            italic=_require_bool(text_payload, "italic"),
            text_color_hex=_require_str(text_payload, "text_color_hex"),
        ),
        box_style=SignatureBoxStyle(
            show_border=_require_bool(box_payload, "show_border"),
            border_color_hex=_require_non_empty_str(box_payload, "border_color_hex"),
            border_width_pt=_require_float(box_payload, "border_width_pt"),
            background_color_hex=_require_non_empty_str(box_payload, "background_color_hex"),
        ),
        image_stamp_path=(
            None
            if payload.get("image_stamp_path") is None
            else _require_non_empty_str(payload, "image_stamp_path")
        ),
    )


def _serialize_placement_defaults(
    value: SignaturePlacementDefaults | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"width_pt": value.width_pt, "height_pt": value.height_pt, "anchor": value.anchor.value}


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


def _require_finite_float_value(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ReusableObjectValidationError(f"Field '{field}' must be a number.")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ReusableObjectValidationError(f"Field '{field}' must be finite.")
    return normalized


@dataclass(frozen=True)
class PlacementProfileSourcePage:
    """Visible page geometry captured with a reusable placement."""

    visible_width_pt: float
    visible_height_pt: float
    rotation_degrees: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "visible_width_pt",
            _require_finite_float_value(self.visible_width_pt, "visible_width_pt"),
        )
        object.__setattr__(
            self,
            "visible_height_pt",
            _require_finite_float_value(self.visible_height_pt, "visible_height_pt"),
        )
        object.__setattr__(
            self,
            "rotation_degrees",
            _require_int_value(self.rotation_degrees, "rotation_degrees"),
        )
        if self.visible_width_pt <= 0 or self.visible_height_pt <= 0:
            raise ReusableObjectValidationError("Visible source-page dimensions must be positive.")
        if self.rotation_degrees % 90 != 0:
            raise ReusableObjectValidationError(
                "Field 'rotation_degrees' must be a multiple of 90."
            )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PlacementProfileSourcePage:
        return cls(
            visible_width_pt=_require_float(payload, "visible_width_pt"),
            visible_height_pt=_require_float(payload, "visible_height_pt"),
            rotation_degrees=_require_int(payload, "rotation_degrees"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "visible_width_pt": self.visible_width_pt,
            "visible_height_pt": self.visible_height_pt,
            "rotation_degrees": self.rotation_degrees,
        }


DEFAULT_PLACEMENT_SOURCE_PAGE = PlacementProfileSourcePage(
    visible_width_pt=612.0,
    visible_height_pt=792.0,
    rotation_degrees=0,
)


@dataclass(frozen=True)
class PlacementProfileRect:
    """Top-left rectangle relative to the visible source page."""

    left_pt: float
    top_pt: float
    width_pt: float
    height_pt: float

    def __post_init__(self) -> None:
        for field in ("left_pt", "top_pt", "width_pt", "height_pt"):
            object.__setattr__(
                self,
                field,
                _require_finite_float_value(getattr(self, field), field),
            )
        if self.width_pt <= 0 or self.height_pt <= 0:
            raise ReusableObjectValidationError(
                "Placement rectangle width and height must be positive."
            )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PlacementProfileRect:
        return cls(
            left_pt=_require_float(payload, "left_pt"),
            top_pt=_require_float(payload, "top_pt"),
            width_pt=_require_float(payload, "width_pt"),
            height_pt=_require_float(payload, "height_pt"),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AppearanceProfile:
    schema_version: int
    appearance_profile_id: str
    display_name: str
    appearance: SignatureAppearance
    pinned: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _require_int_value(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self,
            "appearance_profile_id",
            _require_non_empty_str_value(self.appearance_profile_id, "appearance_profile_id"),
        )
        object.__setattr__(
            self, "display_name", _require_non_empty_str_value(self.display_name, "display_name")
        )
        if not isinstance(self.appearance, SignatureAppearance):
            raise ReusableObjectValidationError("Field 'appearance' must be a SignatureAppearance.")
        if not isinstance(self.pinned, bool):
            raise ReusableObjectValidationError("Field 'pinned' must be a bool.")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AppearanceProfile:
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            appearance_profile_id=_require_non_empty_str(payload, "appearance_profile_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            appearance=_deserialize_appearance(_require_mapping(payload, "appearance")),
            pinned=_require_bool(payload, "pinned") if "pinned" in payload else False,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "appearance_profile_id": self.appearance_profile_id,
            "display_name": self.display_name,
            "appearance": _serialize_appearance(self.appearance),
            "pinned": self.pinned,
        }


@dataclass(frozen=True)
class PlacementProfile:
    schema_version: int
    placement_profile_id: str
    display_name: str
    pinned: bool
    page_number: int
    source_page: PlacementProfileSourcePage
    rect: PlacementProfileRect

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _require_int_value(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self,
            "placement_profile_id",
            _require_non_empty_str_value(self.placement_profile_id, "placement_profile_id"),
        )
        object.__setattr__(
            self, "display_name", _require_non_empty_str_value(self.display_name, "display_name")
        )
        if self.schema_version != 2:
            raise ReusableObjectValidationError(
                "PlacementProfile schema_version 1 requires explicit migration context; "
                "only schema_version 2 is serialized."
            )
        if not isinstance(self.pinned, bool):
            raise ReusableObjectValidationError("Field 'pinned' must be a bool.")
        object.__setattr__(self, "page_number", _require_int_value(self.page_number, "page_number"))
        if self.page_number < 1:
            raise ReusableObjectValidationError("Field 'page_number' must be one or greater.")
        if not isinstance(self.source_page, PlacementProfileSourcePage):
            raise ReusableObjectValidationError(
                "Field 'source_page' must be a PlacementProfileSourcePage."
            )
        if not isinstance(self.rect, PlacementProfileRect):
            raise ReusableObjectValidationError("Field 'rect' must be a PlacementProfileRect.")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> PlacementProfile:
        schema_version = _require_int(payload, "schema_version")
        if schema_version != 2:
            if schema_version == 1:
                raise ReusableObjectValidationError(
                    "Legacy PlacementProfile requires explicit migration context."
                )
            raise ReusableObjectValidationError(
                f"Unsupported PlacementProfile schema_version {schema_version}; expected 2."
            )
        return cls(
            schema_version=schema_version,
            placement_profile_id=_require_non_empty_str(payload, "placement_profile_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            pinned=_require_bool(payload, "pinned"),
            page_number=_require_int(payload, "page_number"),
            source_page=PlacementProfileSourcePage.from_dict(
                _require_mapping(payload, "source_page")
            ),
            rect=PlacementProfileRect.from_dict(_require_mapping(payload, "rect")),
        )

    @classmethod
    def from_defaults(
        cls,
        *,
        display_name: str,
        placement_defaults: SignaturePlacementDefaults,
        source_page: PlacementProfileSourcePage,
        page_number: int = 1,
        schema_version: int = 2,
        placement_profile_id: str | None = None,
    ) -> PlacementProfile:
        return cls(
            schema_version=schema_version,
            placement_profile_id=placement_profile_id or _stable_id("placement", display_name),
            display_name=display_name,
            pinned=False,
            page_number=page_number,
            source_page=source_page,
            rect=PlacementProfileRect(
                left_pt=0.0,
                top_pt=0.0,
                width_pt=placement_defaults.width_pt,
                height_pt=placement_defaults.height_pt,
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "placement_profile_id": self.placement_profile_id,
            "display_name": self.display_name,
            "pinned": self.pinned,
            "page_number": self.page_number,
            "source_page": self.source_page.to_dict(),
            "rect": self.rect.to_dict(),
        }

    @property
    def placement_defaults(self) -> SignaturePlacementDefaults:
        return SignaturePlacementDefaults(
            width_pt=self.rect.width_pt, height_pt=self.rect.height_pt
        )


def migrate_legacy_placement_payload(
    payload: dict[str, Any],
    *,
    source_page: PlacementProfileSourcePage | None,
    page_number: int | None,
) -> PlacementProfile:
    """Convert a v1 bottom-left payload when page context is supplied."""

    schema_version = _require_int(payload, "schema_version")
    if schema_version != 1:
        raise ReusableObjectValidationError(
            f"Legacy placement migration requires schema_version 1, got {schema_version}."
        )
    if source_page is None or page_number is None:
        raise ReusableObjectValidationError(
            "Legacy PlacementProfile requires explicit migration context: source_page and "
            "page_number."
        )
    rect_payload = _require_mapping(payload, "rect")
    left_pt = _require_float(rect_payload, "left_pt")
    bottom_pt = _require_float(rect_payload, "bottom_pt")
    width_pt = _require_float(rect_payload, "width_pt")
    height_pt = _require_float(rect_payload, "height_pt")
    pinned = _require_bool(payload, "pinned") if "pinned" in payload else False
    return PlacementProfile(
        schema_version=2,
        placement_profile_id=_require_non_empty_str(payload, "placement_profile_id"),
        display_name=_require_non_empty_str(payload, "display_name"),
        pinned=pinned,
        page_number=page_number,
        source_page=source_page,
        rect=PlacementProfileRect(
            left_pt=left_pt,
            top_pt=source_page.visible_height_pt - bottom_pt - height_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        ),
    )


@dataclass(frozen=True)
class SignaturePreset:
    schema_version: int
    signature_preset_id: str
    display_name: str
    certificate_configuration_id: str | None = None
    appearance_profile_id: str | None = None
    placement_profile_id: str | None = None
    pinned: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _require_int_value(self.schema_version, "schema_version")
        )
        object.__setattr__(
            self,
            "signature_preset_id",
            _require_non_empty_str_value(self.signature_preset_id, "signature_preset_id"),
        )
        object.__setattr__(
            self, "display_name", _require_non_empty_str_value(self.display_name, "display_name")
        )
        for field in (
            "certificate_configuration_id",
            "appearance_profile_id",
            "placement_profile_id",
        ):
            object.__setattr__(
                self, field, _require_optional_non_empty_str_value(getattr(self, field), field)
            )
        if not isinstance(self.pinned, bool):
            raise ReusableObjectValidationError("Field 'pinned' must be a bool.")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignaturePreset:
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            signature_preset_id=_require_non_empty_str(payload, "signature_preset_id"),
            display_name=_require_non_empty_str(payload, "display_name"),
            certificate_configuration_id=_optional_non_empty_str(
                payload, "certificate_configuration_id"
            ),
            appearance_profile_id=_optional_non_empty_str(payload, "appearance_profile_id"),
            placement_profile_id=_optional_non_empty_str(payload, "placement_profile_id"),
            pinned=_require_bool(payload, "pinned") if "pinned" in payload else False,
        )

    @classmethod
    def from_profile_parts(
        cls,
        *,
        display_name: str,
        appearance_profile_id: str,
        placement_profile_id: str | None = None,
        certificate_configuration_id: str | None = None,
        schema_version: int = 2,
        signature_preset_id: str | None = None,
        pinned: bool = False,
    ) -> SignaturePreset:
        return cls(
            schema_version=schema_version,
            signature_preset_id=signature_preset_id or _stable_id("preset", display_name),
            display_name=display_name,
            certificate_configuration_id=certificate_configuration_id,
            appearance_profile_id=appearance_profile_id,
            placement_profile_id=placement_profile_id,
            pinned=pinned,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "signature_preset_id": self.signature_preset_id,
            "display_name": self.display_name,
            "certificate_configuration_id": self.certificate_configuration_id,
            "appearance_profile_id": self.appearance_profile_id,
            "placement_profile_id": self.placement_profile_id,
            "pinned": self.pinned,
        }


@dataclass(frozen=True)
class ResolvedSignaturePreset:
    preset: SignaturePreset
    appearance_profile: AppearanceProfile | None
    placement_profile: PlacementProfile | None = None

    @property
    def name(self) -> str:
        return self.preset.display_name

    @property
    def appearance(self) -> SignatureAppearance:
        if self.appearance_profile is None:
            raise ReusableObjectValidationError(
                f"Signature preset '{self.name}' does not reference an appearance profile."
            )
        return self.appearance_profile.appearance

    @property
    def placement_defaults(self) -> SignaturePlacementDefaults | None:
        return None if self.placement_profile is None else self.placement_profile.placement_defaults

    @classmethod
    def from_parts(
        cls,
        *,
        name: str,
        appearance: SignatureAppearance,
        placement_defaults: SignaturePlacementDefaults | None = None,
        source_page: PlacementProfileSourcePage | None = None,
        page_number: int = 1,
        certificate_configuration_id: str | None = None,
        schema_version: int = 2,
    ) -> ResolvedSignaturePreset:
        appearance_profile = AppearanceProfile(
            schema_version=schema_version,
            appearance_profile_id=_stable_id("appearance", name),
            display_name=name,
            appearance=appearance,
        )
        if placement_defaults is not None and source_page is None:
            raise ReusableObjectValidationError(
                "A placement source_page is required when capturing placement defaults."
            )
        placement_profile = (
            PlacementProfile.from_defaults(
                schema_version=schema_version,
                display_name=name,
                placement_defaults=placement_defaults,
                source_page=source_page,
                page_number=page_number,
            )
            if placement_defaults is not None
            else None
        )
        return cls(
            preset=SignaturePreset.from_profile_parts(
                schema_version=schema_version,
                display_name=name,
                certificate_configuration_id=certificate_configuration_id,
                appearance_profile_id=appearance_profile.appearance_profile_id,
                placement_profile_id=None
                if placement_profile is None
                else placement_profile.placement_profile_id,
            ),
            appearance_profile=appearance_profile,
            placement_profile=placement_profile,
        )


@dataclass(frozen=True)
class SignaturePresetCatalog:
    schema_version: int
    appearance_profiles: tuple[AppearanceProfile, ...] = ()
    placement_profiles: tuple[PlacementProfile, ...] = ()
    signature_presets: tuple[SignaturePreset, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "schema_version", _require_int_value(self.schema_version, "schema_version")
        )
        self._validate_object_tuple(
            self.appearance_profiles,
            AppearanceProfile,
            "appearance_profiles",
            "appearance_profile_id",
        )
        self._validate_object_tuple(
            self.placement_profiles, PlacementProfile, "placement_profiles", "placement_profile_id"
        )
        self._validate_object_tuple(
            self.signature_presets, SignaturePreset, "signature_presets", "signature_preset_id"
        )
        names: set[str] = set()
        for preset in self.signature_presets:
            normalized_name = preset.display_name.casefold()
            if normalized_name in names:
                raise ReusableObjectValidationError(
                    "Field 'signature_presets' must not contain duplicate names."
                )
            names.add(normalized_name)
        for field_name, entries in (
            ("appearance_profiles", self.appearance_profiles),
            ("placement_profiles", self.placement_profiles),
        ):
            names = set()
            for entry in entries:
                normalized_name = entry.display_name.casefold()
                if normalized_name in names:
                    raise ReusableObjectValidationError(
                        f"Field '{field_name}' must not contain duplicate names."
                    )
                names.add(normalized_name)
        appearance_ids = {item.appearance_profile_id for item in self.appearance_profiles}
        placement_ids = {item.placement_profile_id for item in self.placement_profiles}
        for preset in self.signature_presets:
            if preset.appearance_profile_id is None:
                raise ReusableObjectValidationError(
                    f"Signature preset '{preset.display_name}' must reference "
                    "an appearance profile."
                )
            if preset.appearance_profile_id not in appearance_ids:
                raise ReusableObjectValidationError(
                    f"Signature preset '{preset.display_name}' references a missing "
                    "appearance profile."
                )
            if (
                preset.placement_profile_id is not None
                and preset.placement_profile_id not in placement_ids
            ):
                raise ReusableObjectValidationError(
                    f"Signature preset '{preset.display_name}' references a missing "
                    "placement profile."
                )

    @staticmethod
    def _validate_object_tuple(
        values: tuple[Any, ...], expected_type: type, field_name: str, id_field_name: str
    ) -> None:
        if not isinstance(values, tuple):
            raise ReusableObjectValidationError(f"Field '{field_name}' must be a tuple.")
        seen: set[str] = set()
        for value in values:
            if not isinstance(value, expected_type):
                raise ReusableObjectValidationError(
                    f"Field '{field_name}' must contain {expected_type.__name__} values only."
                )
            object_id = getattr(value, id_field_name)
            if object_id in seen:
                raise ReusableObjectValidationError(
                    f"Field '{field_name}' must not contain duplicate ids."
                )
            seen.add(object_id)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SignaturePresetCatalog:
        values: dict[str, list[Any]] = {}
        for field in ("appearance_profiles", "placement_profiles", "signature_presets"):
            raw = _require_value(payload, field)
            if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
                raise ReusableObjectValidationError(f"Field '{field}' must contain objects only.")
            values[field] = raw
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            appearance_profiles=tuple(
                AppearanceProfile.from_dict(item) for item in values["appearance_profiles"]
            ),
            placement_profiles=tuple(
                PlacementProfile.from_dict(item) for item in values["placement_profiles"]
            ),
            signature_presets=tuple(
                SignaturePreset.from_dict(item) for item in values["signature_presets"]
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "appearance_profiles": [item.to_dict() for item in self.appearance_profiles],
            "placement_profiles": [item.to_dict() for item in self.placement_profiles],
            "signature_presets": [item.to_dict() for item in self.signature_presets],
        }

    def preset_names(self) -> tuple[str, ...]:
        return tuple(item.display_name for item in self.signature_presets)

    def preset_named(self, name: str) -> ResolvedSignaturePreset:
        normalized = _require_non_empty_str_value(name, "name")
        for preset in self.signature_presets:
            if preset.display_name.casefold() == normalized.casefold():
                return self.resolve_preset(preset)
        raise KeyError(normalized)

    def appearance_profile_named(self, name: str) -> AppearanceProfile:
        normalized = _require_non_empty_str_value(name, "name")
        for item in self.appearance_profiles:
            if item.display_name.casefold() == normalized.casefold():
                return item
        raise KeyError(normalized)

    def placement_profile_named(self, name: str) -> PlacementProfile:
        normalized = _require_non_empty_str_value(name, "name")
        for item in self.placement_profiles:
            if item.display_name.casefold() == normalized.casefold():
                return item
        raise KeyError(normalized)

    def resolve_preset(self, preset: SignaturePreset) -> ResolvedSignaturePreset:
        appearance = next(
            (
                item
                for item in self.appearance_profiles
                if item.appearance_profile_id == preset.appearance_profile_id
            ),
            None,
        )
        placement = next(
            (
                item
                for item in self.placement_profiles
                if item.placement_profile_id == preset.placement_profile_id
            ),
            None,
        )
        if appearance is None:
            raise KeyError(preset.appearance_profile_id)
        return ResolvedSignaturePreset(
            preset=preset, appearance_profile=appearance, placement_profile=placement
        )

    def upsert_preset(self, preset: ResolvedSignaturePreset) -> SignaturePresetCatalog:
        if not isinstance(preset, ResolvedSignaturePreset):
            raise ReusableObjectValidationError("preset must be a ResolvedSignaturePreset value.")
        appearances = (
            self._upsert_by_id(
                list(self.appearance_profiles), preset.appearance_profile, "appearance_profile_id"
            )
            if preset.appearance_profile
            else list(self.appearance_profiles)
        )
        placements = (
            self._upsert_by_id(
                list(self.placement_profiles), preset.placement_profile, "placement_profile_id"
            )
            if preset.placement_profile
            else list(self.placement_profiles)
        )
        presets = [
            item
            for item in self.signature_presets
            if item.display_name.casefold() != preset.name.casefold()
        ]
        presets.append(preset.preset)
        return SignaturePresetCatalog(
            self.schema_version, tuple(appearances), tuple(placements), tuple(presets)
        )

    def upsert_reference_preset(self, preset: SignaturePreset) -> SignaturePresetCatalog:
        if not isinstance(preset, SignaturePreset):
            raise ReusableObjectValidationError("preset must be a SignaturePreset value.")
        values = [
            item
            for item in self.signature_presets
            if item.display_name.casefold() != preset.display_name.casefold()
        ]
        values.append(preset)
        return SignaturePresetCatalog(
            self.schema_version, self.appearance_profiles, self.placement_profiles, tuple(values)
        )

    def upsert_appearance_profile(self, profile: AppearanceProfile) -> SignaturePresetCatalog:
        if not isinstance(profile, AppearanceProfile):
            raise ReusableObjectValidationError("profile must be an AppearanceProfile value.")
        return SignaturePresetCatalog(
            self.schema_version,
            tuple(
                self._upsert_by_id(list(self.appearance_profiles), profile, "appearance_profile_id")
            ),
            self.placement_profiles,
            self.signature_presets,
        )

    def upsert_placement_profile(self, profile: PlacementProfile) -> SignaturePresetCatalog:
        if not isinstance(profile, PlacementProfile):
            raise ReusableObjectValidationError("profile must be a PlacementProfile value.")
        return SignaturePresetCatalog(
            self.schema_version,
            self.appearance_profiles,
            tuple(
                self._upsert_by_id(list(self.placement_profiles), profile, "placement_profile_id")
            ),
            self.signature_presets,
        )

    @staticmethod
    def _upsert_by_id(values: list[Any], replacement: Any, id_field_name: str) -> list[Any]:
        if replacement is None:
            return values
        replacement_id = getattr(replacement, id_field_name)
        return [
            replacement if getattr(value, id_field_name) == replacement_id else value
            for value in values
        ] + (
            []
            if any(getattr(value, id_field_name) == replacement_id for value in values)
            else [replacement]
        )

    def remove_preset(self, name: str) -> SignaturePresetCatalog:
        normalized = _require_non_empty_str_value(name, "name")
        values = tuple(
            item
            for item in self.signature_presets
            if item.display_name.casefold() != normalized.casefold()
        )
        if len(values) == len(self.signature_presets):
            raise KeyError(normalized)
        return SignaturePresetCatalog(
            self.schema_version, self.appearance_profiles, self.placement_profiles, values
        )

    def remove_appearance_profile(self, name: str) -> SignaturePresetCatalog:
        profile = self.appearance_profile_named(name)
        if any(
            item.appearance_profile_id == profile.appearance_profile_id
            for item in self.signature_presets
        ):
            raise ReusableObjectValidationError(
                f"Appearance profile '{profile.display_name}' is referenced by signature preset(s)."
            )
        return SignaturePresetCatalog(
            self.schema_version,
            tuple(
                item
                for item in self.appearance_profiles
                if item.appearance_profile_id != profile.appearance_profile_id
            ),
            self.placement_profiles,
            self.signature_presets,
        )

    def remove_placement_profile(self, name: str) -> SignaturePresetCatalog:
        profile = self.placement_profile_named(name)
        if any(
            item.placement_profile_id == profile.placement_profile_id
            for item in self.signature_presets
        ):
            raise ReusableObjectValidationError(
                f"Placement profile '{profile.display_name}' is referenced by signature preset(s)."
            )
        return SignaturePresetCatalog(
            self.schema_version,
            self.appearance_profiles,
            tuple(
                item
                for item in self.placement_profiles
                if item.placement_profile_id != profile.placement_profile_id
            ),
            self.signature_presets,
        )

    def rename_preset(self, name: str, new_name: str) -> SignaturePresetCatalog:
        return self._renamed_catalog(name, new_name, "signature_presets")

    def rename_appearance_profile(self, name: str, new_name: str) -> SignaturePresetCatalog:
        return self._renamed_catalog(name, new_name, "appearance_profiles")

    def rename_placement_profile(self, name: str, new_name: str) -> SignaturePresetCatalog:
        return self._renamed_catalog(name, new_name, "placement_profiles")

    def _renamed_catalog(self, name: str, new_name: str, attribute: str) -> SignaturePresetCatalog:
        normalized = _require_non_empty_str_value(name, "name")
        replacement = _require_non_empty_str_value(new_name, "new_name")
        entries = getattr(self, attribute)
        if normalized.casefold() == replacement.casefold():
            return self
        if any(item.display_name.casefold() == replacement.casefold() for item in entries):
            raise ReusableObjectValidationError(f"Reusable object '{replacement}' already exists.")
        renamed = tuple(
            replace(item, display_name=replacement)
            if item.display_name.casefold() == normalized.casefold()
            else item
            for item in entries
        )
        if renamed == entries:
            raise KeyError(normalized)
        return SignaturePresetCatalog(
            self.schema_version,
            renamed if attribute == "appearance_profiles" else self.appearance_profiles,
            renamed if attribute == "placement_profiles" else self.placement_profiles,
            renamed if attribute == "signature_presets" else self.signature_presets,
        )


__all__ = [
    "AppearanceProfile",
    "PlacementProfile",
    "PlacementProfileRect",
    "ResolvedSignaturePreset",
    "ReusableObjectValidationError",
    "SignaturePreset",
    "SignaturePresetCatalog",
    "_deserialize_appearance",
    "_deserialize_placement_defaults",
    "_serialize_appearance",
    "_stable_id",
]
