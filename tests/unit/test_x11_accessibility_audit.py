"""Headless tests for the bounded native-X11 audit retry seam."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _audit_module() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts" / "live_gui_accessibility_audit.py"
    spec = importlib.util.spec_from_file_location("live_gui_accessibility_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeX11Input:
    def __init__(self, focus_ids: list[int | None]) -> None:
        self._focus_ids = iter(focus_ids)
        self.pressed_window_ids: list[int] = []

    def focused_window_id(self) -> int | None:
        return next(self._focus_ids, None)

    def focus_and_press_f1(self, window_id: int) -> None:
        self.pressed_window_ids.append(window_id)


def test_native_f1_retry_records_focus_and_stops_after_success() -> None:
    module = _audit_module()
    x11 = _FakeX11Input([11, 12, 13, 14])
    activation_results = iter([True, True])
    help_results = iter([False, True])
    sleeps: list[float] = []

    result = module._deliver_native_f1_with_retries(  # noqa: SLF001
        window_id=42,
        x11=x11,
        activate_window=lambda _window_id: next(activation_results),
        wait_for_help=lambda _timeout: next(help_results),
        sleep=sleeps.append,
    )

    assert result["opened"] is True
    assert result["attempt_count"] == 2
    assert result["attempts"] == [
        {
            "attempt": 1,
            "wmctrl_activation": True,
            "focus_window_before": 11,
            "focus_window_after": 12,
            "help_opened": False,
        },
        {
            "attempt": 2,
            "wmctrl_activation": True,
            "focus_window_before": 13,
            "focus_window_after": 14,
            "help_opened": True,
        },
    ]
    assert x11.pressed_window_ids == [42, 42]
    assert sleeps == [0.1]


def test_native_f1_retry_reports_activation_failure_and_exhausts_bound() -> None:
    module = _audit_module()
    x11 = _FakeX11Input([None, None, None])
    sleeps: list[float] = []

    result = module._deliver_native_f1_with_retries(  # noqa: SLF001
        window_id=42,
        x11=x11,
        activate_window=lambda _window_id: False,
        wait_for_help=lambda _timeout: True,
        max_attempts=3,
        sleep=sleeps.append,
    )

    assert result["opened"] is False
    assert result["attempt_count"] == 3
    assert result["attempts"] == [
        {
            "attempt": 1,
            "wmctrl_activation": False,
            "focus_window_before": None,
            "focus_window_after": None,
            "help_opened": False,
        },
        {
            "attempt": 2,
            "wmctrl_activation": False,
            "focus_window_before": None,
            "focus_window_after": None,
            "help_opened": False,
        },
        {
            "attempt": 3,
            "wmctrl_activation": False,
            "focus_window_before": None,
            "focus_window_after": None,
            "help_opened": False,
        },
    ]
    assert x11.pressed_window_ids == []
    assert sleeps == [0.1, 0.1]


def test_native_f1_retry_keeps_delivery_errors_in_attempt_record() -> None:
    module = _audit_module()
    x11 = _FakeX11Input([7, 8])

    def _raise(_window_id: int) -> bool:
        raise RuntimeError("focus helper failed")

    result = module._deliver_native_f1_with_retries(  # noqa: SLF001
        window_id=42,
        x11=x11,
        activate_window=_raise,
        wait_for_help=lambda _timeout: False,
        max_attempts=1,
        sleep=lambda _seconds: None,
    )

    assert result["opened"] is False
    assert result["attempts"] == [
        {
            "attempt": 1,
            "wmctrl_activation": False,
            "focus_window_before": 7,
            "focus_window_after": 8,
            "help_opened": False,
            "error": "RuntimeError: focus helper failed",
        }
    ]


def test_native_f1_retry_rejects_non_positive_attempt_bound() -> None:
    module = _audit_module()
    x11 = _FakeX11Input([])

    try:
        module._deliver_native_f1_with_retries(  # noqa: SLF001
            window_id=42,
            x11=x11,
            activate_window=lambda _window_id: True,
            wait_for_help=lambda _timeout: False,
            max_attempts=0,
        )
    except ValueError as exc:
        assert str(exc) == "max_attempts must be positive"
    else:
        raise AssertionError("expected max_attempts validation")


def test_atspi_startup_preflight_sets_forced_environment_and_parses_status(monkeypatch) -> None:
    module = _audit_module()
    calls: list[list[str]] = []

    def _run(args, **_kwargs):
        calls.append(args)
        if "call" in args:
            return SimpleNamespace(
                returncode=0,
                stdout='s "unix:path=/run/user/1000/at-spi/bus_0"',
                stderr="",
            )
        property_name = args[-1]
        value = "true" if property_name == "IsEnabled" else "false"
        return SimpleNamespace(returncode=0, stdout=f"b {value}", stderr="")

    monkeypatch.delenv("QT_LINUX_ACCESSIBILITY_ALWAYS_ON", raising=False)
    monkeypatch.delenv("AT_SPI_BUS_ADDRESS", raising=False)
    monkeypatch.setattr(module.subprocess, "run", _run)

    result = module._atspi_startup_preflight(True)  # noqa: SLF001

    assert result["forced"] is True
    assert result["address_resolved"] is True
    assert result["status"]["IsEnabled"]["value"] is True
    assert result["status"]["ScreenReaderEnabled"]["value"] is False
    assert module.os.environ["QT_LINUX_ACCESSIBILITY_ALWAYS_ON"] == "1"
    assert calls[0][2] == "call"


def test_qt_initialization_runs_atspi_preflight_before_factory_and_restores_environment(
    monkeypatch,
) -> None:
    module = _audit_module()
    events: list[str] = []

    def _preflight(force: bool):
        events.append(f"preflight:{force}")
        module.os.environ["QT_LINUX_ACCESSIBILITY_ALWAYS_ON"] = "1"
        return {"forced": force}

    def _factory():
        events.append("factory")
        assert module.os.environ["QT_LINUX_ACCESSIBILITY_ALWAYS_ON"] == "1"
        return object()

    monkeypatch.setenv("QT_LINUX_ACCESSIBILITY_ALWAYS_ON", "original")
    monkeypatch.setattr(module, "_atspi_startup_preflight", _preflight)
    app, startup = module._initialize_qt_application(  # noqa: SLF001
        probe_atspi=True,
        force_atspi=True,
        application_factory=_factory,
    )

    assert app is not None
    assert startup == {"forced": True}
    assert events == ["preflight:True", "factory"]
    module._restore_environment({"QT_LINUX_ACCESSIBILITY_ALWAYS_ON": "original"})  # noqa: SLF001
    assert module.os.environ["QT_LINUX_ACCESSIBILITY_ALWAYS_ON"] == "original"


def test_probe_atspi_preserves_exit_and_stderr_diagnostics(monkeypatch) -> None:
    module = _audit_module()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=7,
            stdout="",
            stderr="bridge failed",
        ),
    )

    result = module._probe_atspi(42, "FoliaSeal X11 Accessibility Audit", 1.0)  # noqa: SLF001

    assert result == {
        "status": "unavailable",
        "reason": "probe exited with code 7",
        "returncode": 7,
        "stderr": "bridge failed",
    }


def test_probe_atspi_classifies_malformed_output_with_stderr(monkeypatch) -> None:
    module = _audit_module()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="not-json",
            stderr="bridge warning",
        ),
    )

    result = module._probe_atspi(42, "FoliaSeal X11 Accessibility Audit", 1.0)  # noqa: SLF001

    assert result["status"] == "unavailable"
    assert result["reason"].startswith("probe output: JSONDecodeError:")
    assert result["stderr"] == "bridge warning"


def test_probe_atspi_classifies_non_object_output_with_diagnostics(monkeypatch) -> None:
    module = _audit_module()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="[]",
            stderr="bridge warning",
        ),
    )

    result = module._probe_atspi(42, "FoliaSeal X11 Accessibility Audit", 1.0)  # noqa: SLF001

    assert result == {
        "status": "unavailable",
        "reason": "probe output was not a JSON object",
        "returncode": 0,
        "stderr": "bridge warning",
    }


def test_probe_atspi_classifies_timeout(monkeypatch) -> None:
    module = _audit_module()

    def _timeout(*_args, **_kwargs):
        raise module.subprocess.TimeoutExpired("probe", 3, stderr=b"timed out")

    monkeypatch.setattr(module.subprocess, "run", _timeout)

    result = module._probe_atspi(42, "FoliaSeal X11 Accessibility Audit", 1.0)  # noqa: SLF001

    assert result == {
        "status": "unavailable",
        "reason": "probe process: TimeoutExpired: Command 'probe' timed out after 3 seconds",
        "returncode": None,
        "stderr": "timed out",
    }
