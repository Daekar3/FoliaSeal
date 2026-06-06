from pathlib import Path
from types import SimpleNamespace

import foliaseal.presentation.qt.phase3_harness_session_runner as runner_module
from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningResult
from tests.support.phase3_builders import build_signing_request


def test_run_phase3_harness_session_returns_raw_session_state(tmp_path: Path) -> None:
    input_pdf = tmp_path / "input.pdf"
    cert_path = tmp_path / "cert.p12"
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
        def setWindowTitle(self, title):  # noqa: N802
            self.title = title

        def resize(self, width, height):  # noqa: N802
            self.size = (width, height)

        def setCentralWidget(self, widget):  # noqa: N802
            self.central_widget = widget

        def show(self):
            self.shown = True

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
            self._on_sign_request = kwargs["on_sign_request"]
            self._on_error = kwargs["on_error"]
            self._on_status_change = kwargs["on_status_change"]
            self.properties_panel = SimpleNamespace(_workflow=object())
            self.viewer_widget = _FakeViewerWidget()
            self.last_signing_result = None

        def refresh_viewer(self):
            return None

        def setFocus(self):  # noqa: N802
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

    def fake_capture_interactive_state(*, capture_kind: str, **_kwargs):
        titles = {
            "manual": "Manual preview",
            "signed_run": "Sign-time preview",
            "final": "Final preview",
        }
        return {
            "capture_kind": capture_kind,
            "preview_snapshot": {"title": titles[capture_kind]},
            "sign_request_snapshot": {"signature_appearance": {"layout_template": "single_line"}},
            "backend_reservation_snapshot": {"layout_template": "single_line"},
            "backend_reservation_error": None,
            "preview_text": f"{capture_kind} preview",
            "validation_text": f"{capture_kind} validation",
        }

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
    signing_workflow = SigningDraftWorkflow(
        input_pdf_path=str(input_pdf),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(cert_path),
        passphrase="secret",
        tsa_url="https://tsa.example.invalid",
        timestamp_required=False,
    )

    result = runner_module.Phase3HarnessSessionRunner(
        build_qt_signing_shell=fake_build_qt_signing_shell,
        snapshot_current_draft_request=lambda _workflow: request,
        capture_interactive_state=fake_capture_interactive_state,
        default_harness_output_pdf_path=(
            lambda **kwargs: str(
                tmp_path / f"{Path(kwargs['pdf_path']).stem}_{kwargs['sign_attempt_index']}.pdf"
            )
        ),
        compat_surface=lambda shell: shell,
    ).run(
        bindings=bindings,
        source_path=input_pdf,
        artifacts_dir=str(tmp_path / "artifacts"),
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        profile_store=object(),
        sign_executor=object(),
        capture_assembler=fake_capture_assembler,
    )

    assert result.sign_requests == (request,)
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
    assert result.last_signing_result is not None
    assert result.last_signing_result.success is True
