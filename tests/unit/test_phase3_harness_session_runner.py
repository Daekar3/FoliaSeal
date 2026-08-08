from pathlib import Path
from types import SimpleNamespace

import pytest

import foliaseal.presentation.qt.phase3_harness_session_runner as runner_module
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningResult
from foliaseal.presentation.qt.phase3_harness_session_runner import (
    Phase3HarnessSessionRunnerDeps,
)
from foliaseal.presentation.qt.phase3_harness_workspace import (
    Phase3HarnessCaptureCommand,
    Phase3HarnessWorkspaceSnapshot,
)
from foliaseal.presentation.qt.signing_shell_port import SigningWorkspaceBundle
from tests.support.signing_builders import build_signing_request


@pytest.mark.parametrize("raise_on_final_capture", [False, True])
def test_session_runner_returns_raw_session_state(
    tmp_path: Path,
    raise_on_final_capture: bool,
) -> None:
    input_pdf = tmp_path / "input.pdf"
    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
    )
    button_registry = {}
    shell_holder = {}
    workspace_holder = {}
    window_holder = {}
    dispose_calls = []
    attempt_indices = []

    class _FakeSignal:
        def __init__(self) -> None:
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args):
            for callback in list(self._callbacks):
                callback(*args)

    class _FakeButton:
        def __init__(self, label: str) -> None:
            self.label = label
            self.clicked = _FakeSignal()
            button_registry[label] = self

        def click(self):
            self.clicked.emit()

    class _FakeLabel:
        def __init__(self, text: str = "") -> None:
            self._text = text

        def setText(self, text):  # noqa: N802
            self._text = text

        def text(self):
            return self._text

    class _FakeWidget:
        def setLayout(self, layout):  # noqa: N802
            self.layout = layout

    class _FakeLayout:
        def __init__(self, parent=None) -> None:
            self.items = []
            if parent is not None and hasattr(parent, "setLayout"):
                parent.setLayout(self)

        def addLayout(self, layout, *args):  # noqa: N802
            self.items.append((layout, args))

        def addWidget(self, widget, *args):  # noqa: N802
            self.items.append((widget, args))

        def addStretch(self, value):  # noqa: N802
            self.items.append(("stretch", value))

    class _FakeMainWindow:
        def __init__(self) -> None:
            self.closed = False
            window_holder["window"] = self

        def setWindowTitle(self, title):  # noqa: N802
            self.title = title

        def resize(self, width, height):  # noqa: N802
            self.size = (width, height)

        def setCentralWidget(self, widget):  # noqa: N802
            self.central_widget = widget

        def show(self):
            self.shown = True

        def close(self):
            self.closed = True

    class _FakeApplication:
        _instance = None

        def __init__(self, _args=None) -> None:
            type(self)._instance = self

        @classmethod
        def instance(cls):
            return cls._instance

        def exec(self):
            shell = shell_holder["shell"]
            shell._on_status_change("selection_success")
            button_registry["Capture State"].click()
            shell._on_error("debug issue")
            button_registry["Confirm/Sign"].click()
            return 0

    class _FakeViewerWidget:
        def go_to_previous_page(self):
            return None

        def go_to_next_page(self):
            return None

        def reset_zoom_view(self):
            return None

    class _FakeShell:
        def __init__(self, **kwargs) -> None:
            self.testing_adapter = object()
            self._on_sign_request = kwargs["on_sign_request"]
            self._on_error = kwargs["on_error"]
            self._on_status_change = kwargs["on_status_change"]
            self.viewer_widget = _FakeViewerWidget()
            self.last_signing_result = None

        def refresh_viewer(self):
            return None

        def setFocus(self):  # noqa: N802
            return None

        def focus(self):
            return None

        def submit_sign_request(self):
            self._on_sign_request(request)
            self.last_signing_result = SigningResult(
                success=True,
                failure_code=None,
                message="Signed",
            )
            self._on_status_change("sign_success")

    def fake_build_qt_signing_shell(**kwargs):
        shell = _FakeShell(**kwargs)
        shell_holder["shell"] = shell
        return shell

    class _FakeWorkspace:
        def __init__(self, shell) -> None:
            self._shell = shell
            self.capture_snapshot_commands = []

        def capture_snapshot(self, command: Phase3HarnessCaptureCommand):
            self.capture_snapshot_commands.append(command)
            capture_kind = command.capture_kind
            if capture_kind == "manual":
                assert command.request is None
                assert command.artifact_basename == "interactive_state_01"
            if capture_kind == "signed_run":
                assert command.request == request
                assert command.artifact_basename == "signed_run_01_preview"
            if capture_kind == "final":
                assert command.request == request
                assert command.artifact_basename == "interactive_final"
                if raise_on_final_capture:
                    raise RuntimeError("final capture failed")
            titles = {
                "manual": "Manual preview",
                "signed_run": "Sign-time preview",
                "final": "Final preview",
            }
            current_request = request if command.request is None else command.request
            return Phase3HarnessWorkspaceSnapshot(
                current_request=current_request,
                last_signing_result=self._shell.last_signing_result,
                capture_index=command.capture_index,
                capture_kind=capture_kind,
                capture_label=None,
                preview_snapshot={"title": titles[capture_kind]},
                sign_request_snapshot={
                    "signature_appearance": {"layout_template": "single_line"}
                },
                backend_reservation_snapshot={"layout_template": "single_line"},
                backend_reservation_error=None,
                preview_text=f"{capture_kind} preview",
                validation_text=f"{capture_kind} validation",
            )

    fake_capture_assembler = SimpleNamespace(
        build_signed_run_bundle=lambda **kwargs: {
            "run_index": kwargs["run_index"],
            "output_pdf_path": kwargs["request"].output_pdf_path,
            "output_file_exists": False,
            "output_file_size_bytes": None,
            "output_signature_count": None,
            "output_signature_snapshot": None,
            "output_verification_snapshot": None,
            "output_visible_appearance_snapshot": None,
            "signed_output_render_snapshot": None,
        }
    )

    bindings = runner_module._QtHarnessBindings(
        q_application=_FakeApplication,
        q_main_window=_FakeMainWindow,
        q_widget=_FakeWidget,
        q_v_box_layout=_FakeLayout,
        q_h_box_layout=_FakeLayout,
        q_group_box=_FakeWidget,
        q_push_button=_FakeButton,
        q_label=_FakeLabel,
        q_plain_text_edit=_FakeWidget,
        qpdf_document=object,
    )
    viewer_workflow = ViewerWorkflow(
        document_path=str(input_pdf),
        render_backend=object(),
        session=ViewerSession(page_count=1),
    )

    def create_workspace(bootstrap):
        shell = fake_build_qt_signing_shell(
            on_sign_request=bootstrap.on_sign_request,
            on_error=bootstrap.on_error,
            on_status_change=bootstrap.on_status_change,
        )
        return SigningWorkspaceBundle(
            maintenance=SimpleNamespace(),
            session=shell,
            testing=shell.testing_adapter,
            view=SimpleNamespace(
                mount_target=lambda: shell,
                dispose=lambda: dispose_calls.append("disposed"),
            ),
        )

    runner = runner_module.Phase3HarnessSessionRunner(
        deps=Phase3HarnessSessionRunnerDeps(
            build_workspace=lambda workspace: workspace_holder.setdefault(
                "workspace", _FakeWorkspace(workspace.view.mount_target())
            ),
            default_harness_output_pdf_path=lambda **kwargs: (
                attempt_indices.append(kwargs["sign_attempt_index"])
                or str(
                    tmp_path
                    / f"{Path(kwargs['pdf_path']).stem}_{kwargs['sign_attempt_index']}.pdf"
                )
            ),
            create_workspace=create_workspace,
        ),
    )

    run_kwargs = {
        "bindings": bindings,
        "source_path": input_pdf,
        "artifacts_dir": str(tmp_path / "artifacts"),
        "viewer_workflow": viewer_workflow,
        "signing_workflow": SimpleNamespace(output_pdf_path=str(tmp_path / "output.pdf")),
        "profile_store": object(),
        "sign_executor": object(),
        "capture_assembler": fake_capture_assembler,
    }
    if raise_on_final_capture:
        with pytest.raises(RuntimeError, match="final capture failed"):
            runner.run(**run_kwargs)
        assert window_holder["window"].closed is True
        assert dispose_calls == ["disposed"]
        return

    result = runner.run(**run_kwargs)

    assert result.sign_requests == (request,)
    assert attempt_indices == [1]
    assert window_holder["window"].closed is True
    assert dispose_calls == ["disposed"]
    assert result.errors == ("debug issue",)
    assert result.interaction_counts == {
        "selection_success": 1,
        "sign_success": 1,
    }
    assert len(result.signed_runs) == 1
    assert result.signed_runs[0]["run_index"] == 1
    assert len(result.captured_states) == 1
    assert result.captured_states[0]["capture_kind"] == "manual"
    assert result.final_state["capture_kind"] == "final"
    assert result.final_state["preview_snapshot"]["title"] == "Final preview"
    assert len(workspace_holder["workspace"].capture_snapshot_commands) == 3
    assert result.last_signing_result is not None
    assert result.last_signing_result.success is True


@pytest.mark.parametrize("failure_stage", ["shell", "workspace", "refresh"])
def test_session_runner_closes_window_when_setup_fails(
    tmp_path: Path,
    failure_stage: str,
) -> None:
    window_holder = {}

    class _Signal:
        def connect(self, callback):
            self.callback = callback

    class _Button:
        def __init__(self, label: str) -> None:
            self.label = label
            self.clicked = _Signal()

    class _Widget:
        def setLayout(self, layout):  # noqa: N802
            self.layout = layout

    class _Layout:
        def __init__(self, parent=None) -> None:
            if parent is not None:
                parent.setLayout(self)

        def addLayout(self, layout, *args):  # noqa: N802
            return None

        def addWidget(self, widget, *args):  # noqa: N802
            return None

        def addStretch(self, value):  # noqa: N802
            return None

    class _Window:
        def __init__(self) -> None:
            self.closed = False
            window_holder["window"] = self

        def setWindowTitle(self, title):  # noqa: N802
            return None

        def resize(self, width, height):  # noqa: N802
            return None

        def setCentralWidget(self, widget):  # noqa: N802
            return None

        def close(self):
            self.closed = True

    class _Application:
        @classmethod
        def instance(cls):
            return None

        def __init__(self, args=None) -> None:
            return None

    class _Shell:
        viewer_widget = SimpleNamespace()
        testing_adapter = SimpleNamespace()

        def refresh_viewer(self):
            if failure_stage == "refresh":
                raise RuntimeError("refresh failed")

        def setFocus(self):  # noqa: N802
            return None

        def submit_sign_request(self):
            return None

    def create_workspace(_bootstrap):
        if failure_stage == "shell":
            raise RuntimeError("shell failed")
        shell = _Shell()
        return SimpleNamespace(
            view=SimpleNamespace(mount_target=lambda: shell, dispose=lambda: None),
            session=shell,
            testing=SimpleNamespace(),
        )

    def build_workspace(workspace):
        if failure_stage == "workspace":
            raise RuntimeError("workspace failed")
        return SimpleNamespace()

    bindings = runner_module._QtHarnessBindings(
        q_application=_Application,
        q_main_window=_Window,
        q_widget=_Widget,
        q_v_box_layout=_Layout,
        q_h_box_layout=_Layout,
        q_group_box=_Widget,
        q_push_button=_Button,
        q_label=lambda text="": SimpleNamespace(setText=lambda value: None),
        q_plain_text_edit=_Widget,
        qpdf_document=object,
    )
    runner = runner_module.Phase3HarnessSessionRunner(
        deps=Phase3HarnessSessionRunnerDeps(
            build_workspace=build_workspace,
            default_harness_output_pdf_path=lambda **kwargs: str(tmp_path / "out.pdf"),
            create_workspace=create_workspace,
        )
    )

    with pytest.raises(RuntimeError, match=failure_stage):
        runner.run(
            bindings=bindings,
            source_path=tmp_path / "input.pdf",
            artifacts_dir=None,
            viewer_workflow=SimpleNamespace(),
            signing_workflow=SimpleNamespace(),
            profile_store=object(),
            sign_executor=object(),
            capture_assembler=SimpleNamespace(),
        )

    assert window_holder["window"].closed is True
