"""Workspace-facing scenario application boundary for the Phase 3 harness."""

from __future__ import annotations

import importlib
from collections.abc import Callable
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
    SigningRequest,
    SigningResult,
)
from foliaseal.presentation.qt.signing_workspace_testing_port import (
    SigningWorkspaceTestingPort,
)


def _testing_surface(shell: Any) -> SigningWorkspaceTestingPort:
    testing_adapter = getattr(shell, "testing_adapter", None)
    if testing_adapter is not None:
        return testing_adapter
    raise TypeError(
        "Phase 3 harness shells must expose 'testing_adapter'."
    )


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


@dataclass(frozen=True)
class Phase3HarnessCaptureCommand:
    """Normalized capture inputs for live-shell and headless workspace snapshots."""

    request: SigningRequest | None
    artifacts_dir: str | None
    artifact_basename: str | None
    capture_index: int
    capture_kind: str


@dataclass(frozen=True)
class Phase3HarnessWorkspaceSnapshot:
    """Structured workspace capture shared by live-shell and headless harness paths."""

    current_request: SigningRequest | None
    last_signing_result: SigningResult | None
    capture_index: int
    capture_kind: str
    capture_label: str | None
    preview_snapshot: dict[str, Any]
    preview_text: str
    validation_text: str
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    backend_reservation_error: str | None

    def as_mapping(self) -> dict[str, Any]:
        payload = {
            "capture_index": self.capture_index,
            "capture_kind": self.capture_kind,
            "preview_snapshot": self.preview_snapshot,
            "preview_text": self.preview_text,
            "validation_text": self.validation_text,
            "sign_request_snapshot": self.sign_request_snapshot,
            "backend_reservation_snapshot": self.backend_reservation_snapshot,
            "backend_reservation_error": self.backend_reservation_error,
        }
        if self.capture_label is not None:
            payload["capture_label"] = self.capture_label
        return payload


class Phase3HarnessWorkspacePort(Protocol):
    """Narrow workspace boundary for Phase 3 harness scenario and capture flows."""

    def refresh_viewer(self) -> None: ...
    def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...
    def capture_snapshot(
        self, command: Phase3HarnessCaptureCommand
    ) -> Phase3HarnessWorkspaceSnapshot: ...


@dataclass(frozen=True)
class HeadlessPhase3HarnessWorkspaceDeps:
    """Typed collaborator bundle for the headless harness workspace."""

    headless_preview_text: Callable[[Any], str]
    headless_validation_text: Callable[[Any], str]
    capture_headless_preview_render: Callable[..., dict[str, Any] | None]
    snapshot_preview: Callable[..., dict[str, Any]]
    snapshot_signing_request: Callable[[SigningRequest | None], dict[str, Any] | None]
    build_backend_reservation_evidence: Callable[[SigningRequest | None], Any]


class HeadlessPhase3HarnessWorkspaceAdapter:
    """Apply preview scenarios directly to a headless signing workflow."""

    def __init__(
        self,
        *,
        workflow: SigningDraftWorkflow,
        profile_store: Any,
        deps: HeadlessPhase3HarnessWorkspaceDeps | None = None,
    ) -> None:
        self._workflow = workflow
        self._profile_store = profile_store
        self._deps = deps or HeadlessPhase3HarnessWorkspaceDeps(
            headless_preview_text=lambda _preview: "",
            headless_validation_text=lambda _preview: "",
            capture_headless_preview_render=lambda **_kwargs: None,
            snapshot_preview=lambda _preview, **_kwargs: {},
            snapshot_signing_request=lambda _request: None,
            build_backend_reservation_evidence=lambda _request: None,
        )

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

    def refresh_viewer(self) -> None:
        return None

    def capture_snapshot(
        self, command: Phase3HarnessCaptureCommand
    ) -> Phase3HarnessWorkspaceSnapshot:
        request = (
            command.request
            if command.request is not None
            else snapshot_current_draft_request(self._workflow)
        )
        preview = self._workflow.preview()
        render_capture = self._deps.capture_headless_preview_render(
            preview=preview,
            artifacts_dir=command.artifacts_dir,
            artifact_basename=command.artifact_basename,
        )
        backend_reservation = self._deps.build_backend_reservation_evidence(request)
        return Phase3HarnessWorkspaceSnapshot(
            current_request=request,
            last_signing_result=None,
            capture_index=command.capture_index,
            capture_kind=command.capture_kind,
            capture_label=None,
            preview_snapshot=self._deps.snapshot_preview(preview, render_capture=render_capture),
            preview_text=self._deps.headless_preview_text(preview),
            validation_text=self._deps.headless_validation_text(preview),
            sign_request_snapshot=self._deps.snapshot_signing_request(request),
            backend_reservation_snapshot=(
                None if backend_reservation is None else backend_reservation.snapshot
            ),
            backend_reservation_error=(
                None if backend_reservation is None else backend_reservation.error
            ),
        )


@dataclass(frozen=True)
class QtPhase3HarnessWorkspaceDeps:
    """Typed collaborator bundle for the live Qt harness workspace."""

    capture_preview_render: Callable[..., dict[str, Any] | None]
    snapshot_preview: Callable[..., dict[str, Any]]
    snapshot_signing_request: Callable[[SigningRequest | None], dict[str, Any] | None]
    build_backend_reservation_evidence: Callable[[SigningRequest | None], Any]
    snapshot_sign_time_fit_diagnostics: Callable[..., dict[str, Any] | None]
    interactive_capture_label: Callable[..., str]


class QtPhase3HarnessWorkspaceAdapter:
    """Apply preview scenarios to a live signing shell through the testing seam."""

    def __init__(
        self,
        *,
        shell: Any,
        profile_store: Any,
        deps: QtPhase3HarnessWorkspaceDeps | None = None,
    ) -> None:
        self._shell = shell
        self._profile_store = profile_store
        self._deps = deps or QtPhase3HarnessWorkspaceDeps(
            capture_preview_render=lambda **_kwargs: None,
            snapshot_preview=lambda _preview, **_kwargs: {},
            snapshot_signing_request=lambda _request: None,
            build_backend_reservation_evidence=lambda _request: None,
            snapshot_sign_time_fit_diagnostics=lambda **_kwargs: None,
            interactive_capture_label=lambda **_kwargs: "",
        )

    def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None:
        testing_surface = _testing_surface(self._shell)
        base_appearance = _base_appearance(
            profile_store=self._profile_store,
            profile_name=command.profile_name,
            fallback=testing_surface.signature_appearance() or SignatureAppearance(),
        )
        appearance = _apply_appearance_overrides(
            base_appearance,
            command.appearance_overrides,
        )
        testing_surface.panel.set_signature_appearance(appearance)
        if command.timestamp_required is not None:
            testing_surface.set_timestamp_required(command.timestamp_required)
        if command.signature_rect is not None:
            testing_surface.apply_signature_rect_placement(command.signature_rect)
        self.refresh_viewer()
        app = _widget_application(self._shell)
        if app is not None and hasattr(app, "processEvents"):
            app.processEvents()

    def refresh_viewer(self) -> None:
        _testing_surface(self._shell).refresh_viewer()

    def capture_snapshot(
        self, command: Phase3HarnessCaptureCommand
    ) -> Phase3HarnessWorkspaceSnapshot:
        testing_surface = _testing_surface(self._shell)
        request = (
            command.request
            if command.request is not None
            else testing_surface.current_request()
        )
        last_signing_result = getattr(testing_surface, "last_signing_result", None)
        if callable(last_signing_result):
            signing_result = last_signing_result()
        else:
            signing_result = last_signing_result
        signing_result = signing_result if isinstance(signing_result, SigningResult) else None
        preview = testing_surface.panel.refresh_preview()
        app = _widget_application(self._shell)
        if app is not None and hasattr(app, "processEvents"):
            app.processEvents()
        render_capture = self._deps.capture_preview_render(
            shell=self._shell,
            preview=preview,
            artifacts_dir=command.artifacts_dir,
            artifact_basename=command.artifact_basename,
        )
        backend_reservation = self._deps.build_backend_reservation_evidence(request)
        backend_reservation_snapshot = (
            None if backend_reservation is None else backend_reservation.snapshot
        )
        sign_time_diagnostics = self._deps.snapshot_sign_time_fit_diagnostics(
            preview_render_capture=render_capture,
            backend_reservation_snapshot=backend_reservation_snapshot,
        )
        return Phase3HarnessWorkspaceSnapshot(
            current_request=request,
            last_signing_result=signing_result,
            capture_index=command.capture_index,
            capture_kind=command.capture_kind,
            capture_label=self._deps.interactive_capture_label(
                preview=preview,
                capture_index=command.capture_index,
                capture_kind=command.capture_kind,
            ),
            preview_snapshot=self._deps.snapshot_preview(
                preview,
                render_capture=render_capture,
                sign_time_diagnostics=sign_time_diagnostics,
            ),
            preview_text=testing_surface.panel.preview_text(),
            validation_text=testing_surface.panel.validation_text(),
            sign_request_snapshot=self._deps.snapshot_signing_request(request),
            backend_reservation_snapshot=backend_reservation_snapshot,
            backend_reservation_error=(
                None if backend_reservation is None else backend_reservation.error
            ),
        )


def capture_qt_preview_render(
    *,
    shell: Any,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
    build_preview_render_capture_payload: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Capture the live Qt preview by reading shell anatomy only inside the workspace seam."""

    testing_surface = _testing_surface(shell)
    return testing_surface.panel.capture_preview_render(
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
        build_preview_render_capture_payload=build_preview_render_capture_payload,
    )


def snapshot_current_draft_request(workflow: SigningDraftWorkflow) -> SigningRequest | None:
    """Read the current draft signing request from workflow state when placement exists."""

    signature_rect = workflow.current_signature_rect
    signature_appearance = workflow.current_signature_appearance
    if signature_rect is None or signature_appearance is None:
        return None
    return SigningRequest(
        input_pdf_path=workflow.input_pdf_path,
        output_pdf_path=workflow.output_pdf_path,
        certificate_path=workflow.certificate_path,
        passphrase=workflow.passphrase,
        tsa_url=workflow.tsa_url,
        timestamp_required=workflow.timestamp_required,
        trust_policy=workflow.trust_policy,
        certificate_alias=workflow.certificate_alias,
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
    )


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
