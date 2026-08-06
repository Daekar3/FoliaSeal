"""Qt-free scenario policy for the Phase 3 harness workspace adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from foliaseal.application.qa_preview_stress_fixtures import (
    apply_preview_stress_fixture_profile,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
)


@dataclass(frozen=True)
class Phase3HarnessResolvedScenario:
    """Immutable effect values resolved from one manifest scenario."""

    appearance: SignatureAppearance
    timestamp_required: bool | None
    signature_rect: SignatureRect | None


class Phase3HarnessScenarioResolver:
    """Resolve profile and appearance policy without owning workflow or Qt effects."""

    def __init__(self, *, profile_store: Any) -> None:
        self._profile_store = profile_store

    def resolve(
        self,
        *,
        profile_name: str | None,
        appearance_overrides: Mapping[str, Any] | None,
        timestamp_required: bool | None,
        signature_rect: SignatureRect | None,
        fallback: SignatureAppearance,
    ) -> Phase3HarnessResolvedScenario:
        appearance = self._base_appearance(
            profile_name=profile_name,
            fallback=fallback,
        )
        return Phase3HarnessResolvedScenario(
            appearance=_apply_appearance_overrides(appearance, appearance_overrides),
            timestamp_required=timestamp_required,
            signature_rect=signature_rect,
        )

    def _base_appearance(
        self,
        *,
        profile_name: str | None,
        fallback: SignatureAppearance,
    ) -> SignatureAppearance:
        if profile_name is None:
            return fallback
        catalog = self._profile_store.load_catalog()
        preset = catalog.preset_named(profile_name)
        return preset.appearance


def _apply_appearance_overrides(
    appearance: SignatureAppearance,
    overrides: object,
) -> SignatureAppearance:
    if overrides is None:
        return appearance
    if not isinstance(overrides, dict):
        raise ValueError("Scenario 'appearance_overrides' must be an object.")

    updated = appearance
    direct_updates: dict[str, Any] = {}
    enum_mappings = {
        "layout_template": SignatureLayoutTemplate,
        "stamp_position": SignatureStampPosition,
        "timezone_display_mode": SignatureTimezoneDisplayMode,
    }
    fixture_profile = overrides.get("fixture_profile")
    if fixture_profile is not None:
        if not isinstance(fixture_profile, str) or not fixture_profile.strip():
            raise ValueError("Scenario 'fixture_profile' must be a non-empty string.")
        updated = apply_preview_stress_fixture_profile(
            appearance=updated,
            profile_name=fixture_profile,
        )

    for key in (
        "signer_label_prefix",
        "show_field_names",
        "datetime_format",
        "image_stamp_path",
    ):
        if key in overrides:
            direct_updates[key] = overrides[key]
    for key, enum_cls in enum_mappings.items():
        if key in overrides:
            direct_updates[key] = enum_cls(str(overrides[key]))
    if direct_updates:
        updated = replace(updated, **direct_updates)
    if "text_style" in overrides:
        updated = replace(
            updated,
            text_style=_apply_text_style_overrides(updated.text_style, overrides["text_style"]),
        )
    if "box_style" in overrides:
        updated = replace(
            updated,
            box_style=_apply_box_style_overrides(updated.box_style, overrides["box_style"]),
        )
    if "visible_fields" in overrides:
        updated = _apply_visible_fields_override(updated, overrides["visible_fields"])
    return updated


def _apply_text_style_overrides(style: SignatureTextStyle, overrides: object) -> SignatureTextStyle:
    if not isinstance(overrides, dict):
        raise ValueError("Scenario 'text_style' overrides must be an object.")
    allowed: dict[str, Any] = {}
    for key in ("font_family", "font_size_pt", "bold", "italic", "text_color_hex"):
        if key in overrides:
            allowed[key] = overrides[key]
    return replace(style, **allowed)


def _apply_box_style_overrides(style: SignatureBoxStyle, overrides: object) -> SignatureBoxStyle:
    if not isinstance(overrides, dict):
        raise ValueError("Scenario 'box_style' overrides must be an object.")
    allowed: dict[str, Any] = {}
    for key in (
        "show_border",
        "border_color_hex",
        "border_width_pt",
        "background_color_hex",
    ):
        if key in overrides:
            allowed[key] = overrides[key]
    return replace(style, **allowed)


def _apply_visible_fields_override(
    appearance: SignatureAppearance,
    visible_fields: object,
) -> SignatureAppearance:
    if not isinstance(visible_fields, list) or not visible_fields:
        raise ValueError("Scenario 'visible_fields' must be a non-empty array.")

    visible_keys = {_signature_field_key_from_manifest_value(value) for value in visible_fields}
    updates: dict[str, Any] = {}
    for field_key in appearance.field_order:
        binding = appearance.binding_for(field_key)
        if field_key in visible_keys:
            source = binding.source
            if source == SignatureFieldSource.HIDDEN:
                source = SignatureFieldSource.DERIVED
            updates[field_key.value] = SignatureFieldBinding(
                source=source,
                show_in_visible_appearance=True,
                override_text=(
                    binding.override_text if source == SignatureFieldSource.OVERRIDE else None
                ),
                display_label=binding.display_label,
            )
            continue
        updates[field_key.value] = SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
            display_label=binding.display_label,
        )
    return replace(appearance, **updates)


def _signature_field_key_from_manifest_value(value: object) -> SignatureFieldKey:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Scenario field names must be non-empty strings.")
    return SignatureFieldKey(value)
