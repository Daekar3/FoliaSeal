"""Workspace-facing scenario application boundary for the Acceptance harness."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
    SigningRequest,
)
from foliaseal.presentation.qt.acceptance_harness_workspace_capture import (
    AcceptanceHarnessWorkspaceCaptureInput,
    AcceptanceHarnessWorkspaceCaptureService,
    AcceptanceHarnessWorkspaceSnapshot,
)
from foliaseal.presentation.qt.interactive_harness_event_pump import (
    HarnessEventPumpPort,
    NoOpHarnessEventPump,
    QtHarnessEventPump,
)
from foliaseal.presentation.qt.interactive_harness_scenario_policy import (
    InteractiveHarnessScenarioResolver,
)
from foliaseal.presentation.qt.preview_render_capture import (
    HeadlessPreviewRenderCaptureAdapter,
    PreviewRenderCapturePort,
    PreviewRenderCaptureRequest,
    QtPreviewRenderCaptureAdapter,
)
from foliaseal.presentation.qt.signing_shell_port import SigningWorkspaceBundle


@dataclass(frozen=True)
class InteractiveHarnessScenarioCommand:
    """Normalized preview-matrix scenario fields used by both harness paths."""

    profile_name: str | None
    appearance_overrides: dict[str, Any] | None
    timestamp_required: bool | None
    signature_rect: SignatureRect | None

    @classmethod
    def from_mapping(cls, scenario: dict[str, Any]) -> InteractiveHarnessScenarioCommand:
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
class InteractiveHarnessCaptureCommand:
    """Normalized capture inputs for live-shell and headless workspace snapshots."""

    request: SigningRequest | None
    artifacts_dir: str | None
    artifact_basename: str | None
    capture_index: int
    capture_kind: str


class AcceptanceHarnessWorkspacePort(Protocol):
    """Narrow workspace boundary for Acceptance harness scenario and capture flows."""

    def refresh_viewer(self) -> None: ...
    def apply_scenario(self, command: InteractiveHarnessScenarioCommand) -> None: ...
    def capture_snapshot(
        self, command: InteractiveHarnessCaptureCommand
    ) -> AcceptanceHarnessWorkspaceSnapshot: ...


@dataclass(frozen=True)
class HeadlessAcceptanceHarnessWorkspaceDeps:
    """Typed collaborator bundle for the headless harness workspace."""

    headless_preview_text: Callable[[Any], str]
    headless_validation_text: Callable[[Any], str]
    capture_headless_preview_render: PreviewRenderCapturePort
    snapshot_preview: Callable[..., dict[str, Any]]
    snapshot_signing_request: Callable[[SigningRequest | None], dict[str, Any] | None]
    build_backend_reservation_evidence: Callable[[SigningRequest | None], Any]
    event_pump: HarnessEventPumpPort | None = None


class HeadlessAcceptanceHarnessWorkspaceAdapter:
    """Apply preview scenarios directly to a headless signing workflow."""

    def __init__(
        self,
        *,
        workflow: SigningDraftWorkflow,
        profile_store: Any,
        deps: HeadlessAcceptanceHarnessWorkspaceDeps | None = None,
    ) -> None:
        self._workflow = workflow
        self._deps = deps or HeadlessAcceptanceHarnessWorkspaceDeps(
            headless_preview_text=lambda _preview: "",
            headless_validation_text=lambda _preview: "",
            capture_headless_preview_render=HeadlessPreviewRenderCaptureAdapter(
                callback=lambda **_kwargs: None,
            ),
            snapshot_preview=lambda _preview, **_kwargs: {},
            snapshot_signing_request=lambda _request: None,
            build_backend_reservation_evidence=lambda _request: None,
        )
        self._capture_service = AcceptanceHarnessWorkspaceCaptureService()
        self._scenario_resolver = InteractiveHarnessScenarioResolver(profile_store=profile_store)
        self._event_pump = self._deps.event_pump or NoOpHarnessEventPump()

    def apply_scenario(self, command: InteractiveHarnessScenarioCommand) -> None:
        resolved = self._scenario_resolver.resolve(
            profile_name=command.profile_name,
            appearance_overrides=command.appearance_overrides,
            timestamp_required=command.timestamp_required,
            signature_rect=command.signature_rect,
            fallback=self._workflow.current_signature_appearance or SignatureAppearance(),
        )
        self._workflow.set_signature_appearance(resolved.appearance)
        if resolved.timestamp_required is not None:
            self._workflow.timestamp_required = resolved.timestamp_required
        if resolved.signature_rect is not None:
            self._workflow.set_signature_rect(resolved.signature_rect)
        self._event_pump.process_events()

    def refresh_viewer(self) -> None:
        return None

    def capture_snapshot(
        self, command: InteractiveHarnessCaptureCommand
    ) -> AcceptanceHarnessWorkspaceSnapshot:
        request = (
            command.request
            if command.request is not None
            else snapshot_current_draft_request(self._workflow)
        )
        preview = self._workflow.preview()
        self._event_pump.process_events()
        render_capture_result = self._deps.capture_headless_preview_render.capture(
            PreviewRenderCaptureRequest(
                preview=preview,
                artifacts_dir=command.artifacts_dir,
                artifact_basename=command.artifact_basename or "preview",
            )
        )
        render_capture = (
            None if render_capture_result is None else render_capture_result.as_mapping()
        )
        backend_reservation = self._deps.build_backend_reservation_evidence(request)
        return self._capture_service.build_snapshot(
            AcceptanceHarnessWorkspaceCaptureInput(
                current_request=request,
                last_signing_result=None,
                capture_index=command.capture_index,
                capture_kind=command.capture_kind,
                capture_label=None,
                preview_snapshot=self._deps.snapshot_preview(
                    preview, render_capture=render_capture
                ),
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
        )


@dataclass(frozen=True)
class QtAcceptanceHarnessWorkspaceDeps:
    """Typed collaborator bundle for the live Qt harness workspace."""

    capture_preview_render: PreviewRenderCapturePort
    snapshot_preview: Callable[..., dict[str, Any]]
    snapshot_signing_request: Callable[[SigningRequest | None], dict[str, Any] | None]
    build_backend_reservation_evidence: Callable[[SigningRequest | None], Any]
    snapshot_sign_time_fit_diagnostics: Callable[..., dict[str, Any] | None]
    interactive_capture_label: Callable[..., str]
    event_pump: HarnessEventPumpPort | None = None


class QtAcceptanceHarnessWorkspaceAdapter:
    """Apply preview scenarios to a live signing shell through the testing seam."""

    def __init__(
        self,
        *,
        workspace: SigningWorkspaceBundle,
        profile_store: Any,
        deps: QtAcceptanceHarnessWorkspaceDeps | None = None,
    ) -> None:
        self._workspace = workspace
        self._deps = deps or QtAcceptanceHarnessWorkspaceDeps(
            capture_preview_render=QtPreviewRenderCaptureAdapter(
                callback=lambda **_kwargs: None,
            ),
            snapshot_preview=lambda _preview, **_kwargs: {},
            snapshot_signing_request=lambda _request: None,
            build_backend_reservation_evidence=lambda _request: None,
            snapshot_sign_time_fit_diagnostics=lambda **_kwargs: None,
            interactive_capture_label=lambda **_kwargs: "",
        )
        self._capture_service = AcceptanceHarnessWorkspaceCaptureService()
        self._scenario_resolver = InteractiveHarnessScenarioResolver(profile_store=profile_store)
        self._event_pump = self._deps.event_pump or _default_qt_event_pump(self._workspace)

    def apply_scenario(self, command: InteractiveHarnessScenarioCommand) -> None:
        testing_surface = self._workspace.testing
        workspace_state = testing_surface.snapshot()
        resolved = self._scenario_resolver.resolve(
            profile_name=command.profile_name,
            appearance_overrides=command.appearance_overrides,
            timestamp_required=command.timestamp_required,
            signature_rect=command.signature_rect,
            fallback=workspace_state.signature_appearance or SignatureAppearance(),
        )
        testing_surface.panel.set_signature_appearance(resolved.appearance)
        if resolved.timestamp_required is not None:
            testing_surface.set_timestamp_required(resolved.timestamp_required)
        if resolved.signature_rect is not None:
            testing_surface.apply_signature_rect_placement(resolved.signature_rect)
        self.refresh_viewer()
        self._event_pump.process_events()

    def refresh_viewer(self) -> None:
        self._workspace.session.refresh_viewer()

    def capture_snapshot(
        self, command: InteractiveHarnessCaptureCommand
    ) -> AcceptanceHarnessWorkspaceSnapshot:
        testing_surface = self._workspace.testing
        workspace_state = testing_surface.snapshot()
        request = (
            command.request if command.request is not None else workspace_state.current_request
        )
        signing_result = workspace_state.last_signing_result
        preview = testing_surface.panel.refresh_preview()
        self._event_pump.process_events()
        render_capture_result = self._deps.capture_preview_render.capture(
            PreviewRenderCaptureRequest(
                workspace=self._workspace,
                preview=preview,
                artifacts_dir=command.artifacts_dir,
                artifact_basename=command.artifact_basename or "preview",
            )
        )
        render_capture = (
            None if render_capture_result is None else render_capture_result.as_mapping()
        )
        backend_reservation = self._deps.build_backend_reservation_evidence(request)
        backend_reservation_snapshot = (
            None if backend_reservation is None else backend_reservation.snapshot
        )
        sign_time_diagnostics = self._deps.snapshot_sign_time_fit_diagnostics(
            preview_render_capture=render_capture,
            backend_reservation_snapshot=backend_reservation_snapshot,
        )
        return self._capture_service.build_snapshot(
            AcceptanceHarnessWorkspaceCaptureInput(
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
        )


def capture_qt_preview_render(
    *,
    workspace: SigningWorkspaceBundle,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
    build_preview_render_capture_payload: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """Capture the live Qt preview by reading shell anatomy only inside the workspace seam."""

    testing_surface = workspace.testing
    return testing_surface.panel.capture_preview_render(
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
        build_preview_render_capture_payload=build_preview_render_capture_payload,
    )


def _default_qt_event_pump(workspace: SigningWorkspaceBundle) -> HarnessEventPumpPort:
    try:
        mount_target = workspace.view.mount_target()
    except (AttributeError, TypeError):
        return NoOpHarnessEventPump()
    return QtHarnessEventPump(widget=mount_target)


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
