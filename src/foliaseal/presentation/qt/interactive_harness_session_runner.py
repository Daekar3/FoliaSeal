"""Interactive Qt session-runner boundary for the Acceptance harness."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.reusable_signing_objects import ReusableSigningObjects
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest, SigningResult
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.acceptance_harness_workspace import (
    AcceptanceHarnessWorkspacePort,
    AcceptanceHarnessWorkspaceSnapshot,
    InteractiveHarnessCaptureCommand,
)
from foliaseal.presentation.qt.interactive_harness_capture_assembler import (
    InteractiveHarnessCaptureAssembler,
)
from foliaseal.presentation.qt.interactive_harness_qt_lifecycle import (
    HarnessQtBindings as _QtHarnessBindings,
)
from foliaseal.presentation.qt.interactive_harness_qt_lifecycle import (
    HarnessQtLifecyclePort,
    HarnessWindowSpec,
    QtHarnessLifecycle,
)
from foliaseal.presentation.qt.signing_shell_port import (
    SigningWorkspaceBootstrap,
    SigningWorkspaceBundle,
)

BuildWorkspace = Callable[[SigningWorkspaceBundle], AcceptanceHarnessWorkspacePort]
CreateWorkspace = Callable[[SigningWorkspaceBootstrap], SigningWorkspaceBundle]
DefaultHarnessOutputPdfPath = Callable[..., str]


@dataclass(frozen=True)
class InteractiveHarnessSessionResult:
    """Raw interactive harness session state before capture assembly."""

    first_render_ms: float | None
    sign_requests: tuple[SigningRequest, ...]
    signed_runs: tuple[dict[str, Any], ...]
    errors: tuple[str, ...]
    interaction_counts: dict[str, int]
    captured_states: tuple[dict[str, Any], ...]
    final_state: dict[str, Any]
    capture_request: SigningRequest | None
    last_signing_result: SigningResult | None


@dataclass(frozen=True)
class InteractiveHarnessSessionRunnerDeps:
    """Typed collaborator bundle for one interactive harness session."""

    build_workspace: BuildWorkspace
    default_harness_output_pdf_path: DefaultHarnessOutputPdfPath
    create_workspace: CreateWorkspace
    lifecycle_factory: Callable[[Any], HarnessQtLifecyclePort] | None = None


@dataclass(frozen=True)
class InteractiveHarnessSessionRunner:
    """Own the Qt lifecycle and callback cluster for one interactive harness run."""

    deps: InteractiveHarnessSessionRunnerDeps

    def run(
        self,
        *,
        bindings: _QtHarnessBindings,
        source_path: Path,
        artifacts_dir: str | None,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        profile_store: Any,
        sign_executor: Any,
        capture_assembler: InteractiveHarnessCaptureAssembler,
    ) -> InteractiveHarnessSessionResult:
        sign_requests: list[SigningRequest] = []
        signed_runs: list[dict[str, Any]] = []
        errors: list[str] = []
        interaction_counts: Counter[str] = Counter()

        lifecycle = (self.deps.lifecycle_factory or QtHarnessLifecycle)(bindings)
        surface = lifecycle.start(
            spec=HarnessWindowSpec(
                title=f"FoliaSeal Acceptance Harness - {source_path.name}",
            )
        )
        closed = False

        def close_lifecycle() -> None:
            nonlocal closed
            if closed:
                return
            closed = True
            lifecycle.close(surface)

        toolbar = surface.toolbar

        captured_states: list[dict[str, Any]] = []

        workspace_bundle: SigningWorkspaceBundle | None = None
        workspace: AcceptanceHarnessWorkspacePort

        def dispose_workspace() -> None:
            if workspace_bundle is not None:
                workspace_bundle.view.dispose()

        def refocus_shell() -> None:
            workspace_bundle.session.focus()

        def on_sign_request(request: SigningRequest) -> None:
            sign_requests.append(request)
            signing_workflow.output_pdf_path = self.deps.default_harness_output_pdf_path(
                pdf_path=str(source_path),
                artifacts_dir=artifacts_dir,
                sign_attempt_index=len(sign_requests),
            )

        def on_error(message: str) -> None:
            errors.append(message)

        def on_status_change(name: str) -> None:
            interaction_counts[name] += 1
            if name != "sign_success" or not sign_requests:
                return
            request = sign_requests[-1]
            run_index = len(signed_runs) + 1
            sign_time_snapshot = workspace.capture_snapshot(
                InteractiveHarnessCaptureCommand(
                    request=request,
                    artifacts_dir=artifacts_dir,
                    artifact_basename=(
                        f"signed_run_{run_index:02d}_preview"
                        if artifacts_dir is not None
                        else None
                    ),
                    capture_index=run_index,
                    capture_kind="signed_run",
                )
            )
            signing_result = sign_time_snapshot.last_signing_result
            if signing_result is None or not signing_result.success:
                return
            signed_runs.append(
                capture_assembler.build_signed_run_bundle(
                    run_index=run_index,
                    sign_time_state=sign_time_snapshot.as_mapping(),
                    request=request,
                    signing_result=signing_result,
                    artifacts_dir=artifacts_dir,
                    artifact_basename=(
                        f"signed_run_{run_index:02d}_signed_output"
                        if artifacts_dir is not None
                        else None
                    ),
                )
            )

        try:
            reusable_objects = ReusableSigningObjects(profile_store)
            workspace_bundle = self.deps.create_workspace(
                SigningWorkspaceBootstrap(
                    viewer_workflow=viewer_workflow,
                    signing_workflow=signing_workflow,
                    app_settings=AppSettings.default(),
                    reusable_objects=reusable_objects,
                    sign_executor=sign_executor,
                    on_sign_request=on_sign_request,
                    on_error=on_error,
                    on_status_change=on_status_change,
                )
            )
            workspace = self.deps.build_workspace(workspace_bundle)
        except Exception:
            dispose_workspace()
            close_lifecycle()
            raise
        lifecycle.mount(surface, workspace_bundle.view.mount_target())

        def do_refresh() -> None:
            workspace_bundle.session.refresh_viewer()
            refocus_shell()

        def navigate(action_name: str) -> None:
            actions = {
                "go_to_previous_page": workspace_bundle.session.go_to_previous_page,
                "go_to_next_page": workspace_bundle.session.go_to_next_page,
                "reset_zoom_view": workspace_bundle.session.reset_zoom_view,
            }
            actions[action_name]()
            refocus_shell()

        controls = [
            ("Refresh", do_refresh),
            ("Prev Page", lambda: navigate("go_to_previous_page")),
            ("Next Page", lambda: navigate("go_to_next_page")),
            ("Reset Zoom", lambda: navigate("reset_zoom_view")),
        ]
        for label, callback in controls:
            button = bindings.q_push_button(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)

        capture_count_label = bindings.q_label("Captured states: 0")

        def capture_current_state(
            *,
            capture_kind: str,
            request: SigningRequest | None = None,
        ) -> AcceptanceHarnessWorkspaceSnapshot:
            capture_index = (
                len(captured_states) + 1 if capture_kind == "manual" else len(captured_states)
            )
            artifact_basename = None
            if artifacts_dir is not None:
                artifact_basename = (
                    f"interactive_state_{capture_index:02d}"
                    if capture_kind == "manual"
                    else "interactive_final"
                )
            return workspace.capture_snapshot(
                InteractiveHarnessCaptureCommand(
                    request=request,
                    artifacts_dir=artifacts_dir,
                    artifact_basename=artifact_basename,
                    capture_index=(
                        capture_index if capture_kind == "manual" else len(captured_states) + 1
                    ),
                    capture_kind=capture_kind,
                )
            )

        def update_capture_count_label() -> None:
            capture_count_label.setText(f"Captured states: {len(captured_states)}")

        def on_capture_state() -> None:
            captured_states.append(
                capture_current_state(capture_kind="manual").as_mapping()
            )
            update_capture_count_label()
            refocus_shell()

        capture_button = bindings.q_push_button("Capture State")
        capture_button.clicked.connect(on_capture_state)
        toolbar.addWidget(capture_button)

        confirm_button = bindings.q_push_button("Confirm/Sign")
        confirm_button.clicked.connect(workspace_bundle.session.submit_sign_request)
        toolbar.addWidget(confirm_button)

        toolbar.addStretch(1)
        toolbar.addWidget(capture_count_label)

        try:
            workspace_bundle.session.refresh_viewer()
            first_render_ms = viewer_workflow.timing_tracker.snapshot().first_render_ms
        except Exception:
            dispose_workspace()
            close_lifecycle()
            raise

        try:
            lifecycle.show(surface)
            refocus_shell()
            lifecycle.exec(surface)

            final_snapshot = capture_current_state(
                capture_kind="final",
                request=sign_requests[-1] if sign_requests else None,
            )
            capture_request = final_snapshot.current_request
            final_state = final_snapshot.as_mapping()
            last_signing_result = final_snapshot.last_signing_result
            return InteractiveHarnessSessionResult(
                first_render_ms=first_render_ms,
                sign_requests=tuple(sign_requests),
                signed_runs=tuple(signed_runs),
                errors=tuple(errors),
                interaction_counts=dict(sorted(interaction_counts.items())),
                captured_states=tuple(captured_states),
                final_state=final_state,
                capture_request=capture_request,
                last_signing_result=last_signing_result,
            )
        finally:
            dispose_workspace()
            close_lifecycle()
