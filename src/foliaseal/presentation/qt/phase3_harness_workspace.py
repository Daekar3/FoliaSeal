"""Workspace-facing scenario application boundary for the Phase 3 harness."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, replace
from typing import Any, Protocol

from foliaseal.application import SigningDraftWorkflow
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


def _compat_surface(shell: Any) -> Any:
    compat = getattr(shell, "compat_surface", None)
    return compat if compat is not None else shell


def _widget_application(widget: Any) -> Any | None:
    app_getter = getattr(type(widget), "window", None)
    _ = app_getter
    try:
        app_module = importlib.import_module("PySide6.QtWidgets")
    except ModuleNotFoundError:
        return None
    q_application = getattr(app_module, "QApplication", None)
    if q_application is None:
        return None
    instance = getattr(q_application, "instance", None)
    return instance() if callable(instance) else None


@dataclass(frozen=True)
class Phase3HarnessScenarioCommand:
    """Normalized preview-matrix scenario fields used by both harness paths."""

    profile_name: str | None
    appearance_overrides: dict[str, Any] | None
    timestamp_required: bool | None
    signature_rect: SignatureRect | None

    @classmethod
    def from_mapping(cls, scenario: dict[str, Any]) -> Phase3HarnessScenarioCommand:
        profile_name = scenario.get("profile_name")
        if profile_name is not None:
            if not isinstance(profile_name, str) or not profile_name.strip():
                raise ValueError("Scenario 'profile_name' must be a non-empty string.")
        timestamp_required = None
        if "timestamp_required" in scenario:
            timestamp_required = bool(scenario["timestamp_required"])
        signature_rect = None
        if scenario.get("signature_rect") is not None:
            signature_rect = _signature_rect_from_payload(scenario["signature_rect"])
        appearance_overrides = scenario.get("appearance_overrides")
        return cls(
            profile_name=profile_name,
            appearance_overrides=appearance_overrides,
            timestamp_required=timestamp_required,
            signature_rect=signature_rect,
        )


class Phase3HarnessWorkspacePort(Protocol):
    """Narrow scenario-application boundary for the harness."""

    def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...


class HeadlessPhase3HarnessWorkspaceAdapter:
    """Apply preview scenarios directly to a headless signing workflow."""

    def __init__(self, *, workflow: SigningDraftWorkflow, profile_store: Any) -> None:
        self._workflow = workflow
        self._profile_store = profile_store

    def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None:
        base_appearance = _base_appearance(
            profile_store=self._profile_store,
            profile_name=command.profile_name,
            fallback=self._workflow.current_signature_appearance or SignatureAppearance(),
        )
        appearance = _apply_appearance_overrides(
            base_appearance,
            command.appearance_overrides,
        )
        self._workflow.set_signature_appearance(appearance)
        if command.timestamp_required is not None:
            self._workflow.timestamp_required = command.timestamp_required
        if command.signature_rect is not None:
            self._workflow.set_signature_rect(command.signature_rect)


class QtPhase3HarnessWorkspaceAdapter:
    """Apply preview scenarios to a live signing shell through private shell anatomy."""

    def __init__(self, *, shell: Any, profile_store: Any) -> None:
        self._shell = shell
        self._profile_store = profile_store

    def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None:
        compat = _compat_surface(self._shell)
        workflow = compat.properties_panel._workflow
        base_appearance = _base_appearance(
            profile_store=self._profile_store,
            profile_name=command.profile_name,
            fallback=workflow.current_signature_appearance or SignatureAppearance(),
        )
        appearance = _apply_appearance_overrides(
            base_appearance,
            command.appearance_overrides,
        )
        compat.properties_panel.set_signature_appearance(appearance)
        if command.timestamp_required is not None:
            workflow.timestamp_required = command.timestamp_required
        if command.signature_rect is not None:
            compat.properties_panel.set_signature_rect(command.signature_rect)
            viewer_workflow = getattr(compat, "viewer_workflow", None)
            viewer_widget = getattr(compat, "viewer_widget", None)
            if viewer_workflow is not None and hasattr(viewer_workflow, "jump_to_page"):
                viewer_workflow.jump_to_page(command.signature_rect.page_index)
            refresh = getattr(viewer_widget, "refresh", None)
            if callable(refresh):
                refresh(navigation=True)
            sync_placement = getattr(compat, "sync_placement_context_from_viewer", None)
            if callable(sync_placement):
                sync_placement()
            sync_overlay = getattr(compat, "sync_signature_overlay", None)
            if callable(sync_overlay):
                sync_overlay()
            refresh_sign_button = getattr(compat, "refresh_sign_button_state", None)
            if callable(refresh_sign_button):
                refresh_sign_button()
        compat.refresh_viewer()
        app = _widget_application(self._shell)
        if app is not None and hasattr(app, "processEvents"):
            app.processEvents()


def _base_appearance(
    *,
    profile_store: Any,
    profile_name: str | None,
    fallback: SignatureAppearance,
) -> SignatureAppearance:
    if profile_name is None:
        return fallback
    catalog = profile_store.load_catalog()
    preset = catalog.preset_named(profile_name)
    return preset.appearance


def _signature_rect_from_payload(payload: object) -> SignatureRect:
    if not isinstance(payload, dict):
        raise ValueError("Scenario 'signature_rect' must be an object.")
    return SignatureRect(
        page_index=int(payload["page_index"]),
        left_pt=float(payload["left_pt"]),
        bottom_pt=float(payload["bottom_pt"]),
        width_pt=float(payload["width_pt"]),
        height_pt=float(payload["height_pt"]),
    )


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

    visible_keys = {
        _signature_field_key_from_manifest_value(value) for value in visible_fields
    }
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
                    binding.override_text
                    if source == SignatureFieldSource.OVERRIDE
                    else None
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
