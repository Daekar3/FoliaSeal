from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import foliaseal.presentation.qt.interactive_harness_event_pump as event_pump_module
from foliaseal.presentation.qt.acceptance_harness_workspace import (
    InteractiveHarnessCaptureCommand,
    InteractiveHarnessScenarioCommand,
    QtAcceptanceHarnessWorkspaceAdapter,
    QtAcceptanceHarnessWorkspaceDeps,
)
from foliaseal.presentation.qt.interactive_harness_event_pump import (
    NoOpHarnessEventPump,
    QtHarnessEventPump,
)
from foliaseal.presentation.qt.preview_render_capture import (
    QtPreviewRenderCaptureAdapter,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import SigningWorkspaceSnapshot
from tests.support.signing_builders import build_signature_appearance, build_signature_rect


def test_qt_event_pump_processes_events_from_current_application(monkeypatch) -> None:
    calls: list[str] = []

    class _Application:
        def processEvents(self) -> None:  # noqa: N802
            calls.append("processed")

    class _QApplication:
        @staticmethod
        def instance():
            return _Application()

    monkeypatch.setattr(
        event_pump_module.importlib,
        "import_module",
        lambda _name: SimpleNamespace(QApplication=_QApplication),
    )

    QtHarnessEventPump(widget=object()).process_events()

    assert calls == ["processed"]


def test_qt_event_pump_is_noop_when_application_is_unavailable(monkeypatch) -> None:
    class _QApplication:
        @staticmethod
        def instance():
            return None

    monkeypatch.setattr(
        event_pump_module.importlib,
        "import_module",
        lambda _name: SimpleNamespace(QApplication=_QApplication),
    )

    QtHarnessEventPump(widget=object()).process_events()


def test_noop_event_pump_has_no_side_effect() -> None:
    assert NoOpHarnessEventPump().process_events() is None


def test_workspace_adapter_preserves_refresh_pump_and_capture_order() -> None:
    events: list[str] = []

    class _Pump:
        def process_events(self) -> None:
            events.append("pump")

    class _Panel:
        def set_signature_appearance(self, _appearance) -> None:
            events.append("appearance")

        def refresh_preview(self):
            events.append("preview")
            return object()

        def preview_text(self) -> str:
            return "Preview"

        def validation_text(self) -> str:
            return "Valid"

    class _Testing:
        def __init__(self) -> None:
            self.panel = _Panel()

        def snapshot(self):
            return SigningWorkspaceSnapshot(
                logical_page_index=0,
                signature_rect=None,
                signature_appearance=build_signature_appearance(),
                selected_certificate_configuration_id=None,
                timestamp_required=False,
                current_request=None,
                sign_action_enabled=True,
                last_signing_result=None,
            )

        def set_timestamp_required(self, _required: bool) -> None:
            events.append("timestamp")

        def apply_signature_rect_placement(self, _rect) -> None:
            events.append("rect")

    class _Session:
        def refresh_viewer(self) -> None:
            events.append("refresh")

    bundle = SimpleNamespace(
        testing=_Testing(),
        session=_Session(),
        view=SimpleNamespace(mount_target=lambda: object()),
    )
    adapter = QtAcceptanceHarnessWorkspaceAdapter(
        workspace=bundle,
        profile_store=object(),
        deps=QtAcceptanceHarnessWorkspaceDeps(
            capture_preview_render=QtPreviewRenderCaptureAdapter(
                callback=lambda **_kwargs: events.append("capture") or None,
            ),
            snapshot_preview=lambda _preview, **_kwargs: {},
            snapshot_signing_request=lambda _request: None,
            build_backend_reservation_evidence=lambda _request: None,
            snapshot_sign_time_fit_diagnostics=lambda **_kwargs: None,
            interactive_capture_label=lambda **_kwargs: "capture",
            event_pump=_Pump(),
        ),
    )
    command = InteractiveHarnessScenarioCommand(
        profile_name=None,
        appearance_overrides=None,
        timestamp_required=True,
        signature_rect=build_signature_rect(page_index=1),
    )

    adapter.apply_scenario(command)
    assert events == ["appearance", "timestamp", "rect", "refresh", "pump"]

    events.clear()
    adapter.capture_snapshot(
        InteractiveHarnessCaptureCommand(
            request=None,
            artifacts_dir=None,
            artifact_basename="preview",
            capture_index=1,
            capture_kind="preview",
        )
    )
    assert events == ["preview", "pump", "capture"]


def test_event_pump_module_import_is_free_of_optional_runtime_dependencies() -> None:
    code = (
        "import sys; "
        "import foliaseal.presentation.qt.interactive_harness_event_pump; "
        "print(any(name.startswith('PySide6') or name in {'PIL', 'pyhanko'} "
        "for name in sys.modules))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"
