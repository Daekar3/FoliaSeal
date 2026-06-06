"""Interactive Qt session-runner boundary for the Phase 3 harness."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest, SigningResult
from foliaseal.presentation.qt.phase3_harness_capture_assembler import (
    Phase3HarnessCaptureAssembler,
)

BuildQtSigningShell = Callable[..., Any]
CaptureInteractiveState = Callable[..., dict[str, Any]]
DefaultHarnessOutputPdfPath = Callable[..., str]
SnapshotCurrentDraftRequest = Callable[[SigningDraftWorkflow], SigningRequest | None]
CompatSurface = Callable[[Any], Any]


@dataclass(frozen=True)
class Phase3HarnessSessionResult:
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
class _QtHarnessBindings:
    q_application: type[Any]
    q_main_window: type[Any]
    q_widget: type[Any]
    q_v_box_layout: type[Any]
    q_h_box_layout: type[Any]
    q_group_box: type[Any]
    q_push_button: type[Any]
    q_label: type[Any]
    q_plain_text_edit: type[Any]
    qpdf_document: type[Any]


@dataclass(frozen=True)
class Phase3HarnessSessionRunner:
    """Own the Qt lifecycle and callback cluster for one interactive harness run."""

    build_qt_signing_shell: BuildQtSigningShell
    snapshot_current_draft_request: SnapshotCurrentDraftRequest
    capture_interactive_state: CaptureInteractiveState
    default_harness_output_pdf_path: DefaultHarnessOutputPdfPath
    compat_surface: CompatSurface

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
        capture_assembler: Phase3HarnessCaptureAssembler,
    ) -> Phase3HarnessSessionResult:
        sign_requests: list[SigningRequest] = []
        signed_runs: list[dict[str, Any]] = []
        errors: list[str] = []
        interaction_counts: Counter[str] = Counter()

        app = bindings.q_application.instance() or bindings.q_application([])
        window = bindings.q_main_window()
        window.setWindowTitle(f"FoliaSeal Phase 3 Harness - {source_path.name}")
        window.resize(1440, 980)

        central = bindings.q_widget()
        layout = bindings.q_v_box_layout(central)
        toolbar = bindings.q_h_box_layout()
        layout.addLayout(toolbar)
        body_layout = bindings.q_h_box_layout()
        layout.addLayout(body_layout, 1)

        window.setCentralWidget(central)

        captured_states: list[dict[str, Any]] = []

        shell: Any

        def refocus_shell() -> None:
            focus_setter = getattr(shell, "setFocus", None)
            if callable(focus_setter):
                focus_setter()

        def on_sign_request(request: SigningRequest) -> None:
            sign_requests.append(request)
            signing_workflow.output_pdf_path = self.default_harness_output_pdf_path(
                pdf_path=str(source_path),
                artifacts_dir=artifacts_dir,
                sign_attempt_index=len(sign_requests) + 1,
            )

        def on_error(message: str) -> None:
            errors.append(message)

        def on_status_change(name: str) -> None:
            interaction_counts[name] += 1
            if name != "sign_success" or not sign_requests:
                return
            signing_result = getattr(self.compat_surface(shell), "last_signing_result", None)
            if not isinstance(signing_result, SigningResult) or not signing_result.success:
                return
            request = sign_requests[-1]
            run_index = len(signed_runs) + 1
            sign_time_state = self.capture_interactive_state(
                shell=shell,
                request=request,
                artifacts_dir=artifacts_dir,
                artifact_basename=(
                    f"signed_run_{run_index:02d}_preview" if artifacts_dir is not None else None
                ),
                capture_index=run_index,
                capture_kind="signed_run",
            )
            signed_runs.append(
                capture_assembler.build_signed_run_bundle(
                    run_index=run_index,
                    sign_time_state=sign_time_state,
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

        shell = self.build_qt_signing_shell(
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            preset_catalog_store=profile_store,
            sign_executor=sign_executor,
            on_sign_request=on_sign_request,
            on_error=on_error,
            on_status_change=on_status_change,
        )
        body_layout.addWidget(shell, 1)

        def do_refresh() -> None:
            self.compat_surface(shell).refresh_viewer()
            refocus_shell()

        def navigate(action_name: str) -> None:
            action = getattr(self.compat_surface(shell).viewer_widget, action_name)
            action()
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
        ) -> dict[str, Any]:
            current_request = request
            if current_request is None:
                current_request = self.snapshot_current_draft_request(
                    self.compat_surface(shell).properties_panel._workflow
                )
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
            return self.capture_interactive_state(
                shell=shell,
                request=current_request,
                artifacts_dir=artifacts_dir,
                artifact_basename=artifact_basename,
                capture_index=(
                    capture_index if capture_kind == "manual" else len(captured_states) + 1
                ),
                capture_kind=capture_kind,
            )

        def update_capture_count_label() -> None:
            capture_count_label.setText(f"Captured states: {len(captured_states)}")

        def on_capture_state() -> None:
            captured_states.append(capture_current_state(capture_kind="manual"))
            update_capture_count_label()
            refocus_shell()

        capture_button = bindings.q_push_button("Capture State")
        capture_button.clicked.connect(on_capture_state)
        toolbar.addWidget(capture_button)

        confirm_button = bindings.q_push_button("Confirm/Sign")
        confirm_button.clicked.connect(shell.submit_sign_request)
        toolbar.addWidget(confirm_button)

        toolbar.addStretch(1)
        toolbar.addWidget(capture_count_label)

        self.compat_surface(shell).refresh_viewer()
        first_render_ms = viewer_workflow.timing_tracker.snapshot().first_render_ms

        window.show()
        refocus_shell()
        app.exec()

        capture_request = (
            sign_requests[-1]
            if sign_requests
            else self.snapshot_current_draft_request(
                self.compat_surface(shell).properties_panel._workflow
            )
        )
        final_state = capture_current_state(capture_kind="final", request=capture_request)
        last_signing_result = getattr(self.compat_surface(shell), "last_signing_result", None)
        return Phase3HarnessSessionResult(
            first_render_ms=first_render_ms,
            sign_requests=tuple(sign_requests),
            signed_runs=tuple(signed_runs),
            errors=tuple(errors),
            interaction_counts=dict(sorted(interaction_counts.items())),
            captured_states=tuple(captured_states),
            final_state=final_state,
            capture_request=capture_request,
            last_signing_result=(
                last_signing_result if isinstance(last_signing_result, SigningResult) else None
            ),
        )
