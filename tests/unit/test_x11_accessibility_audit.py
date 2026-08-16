"""Headless tests for the bounded native-X11 audit retry seam."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


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
