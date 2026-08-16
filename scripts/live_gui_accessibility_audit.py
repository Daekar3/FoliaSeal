"""Run a bounded, semantic accessibility audit against the supported X11 display.

This is intentionally an audit-only boundary.  It uses the public Qt frame
adapter for product semantics and ctypes for one native X11/XTest F1 event so
that the result distinguishes desktop input delivery from Qt test injection.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

XK_F1 = 0xFFBE
CURRENT_TIME = 0
REVERT_TO_PARENT = 2
AUDIT_WINDOW_TITLE = "FoliaSeal X11 Accessibility Audit"


class _X11Input:
    """Small audit-local wrapper around libX11/libXtst."""

    def __init__(self) -> None:
        self._x11 = ctypes.CDLL("libX11.so.6")
        self._xtst = ctypes.CDLL("libXtst.so.6")
        self._x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self._x11.XOpenDisplay.restype = ctypes.c_void_p
        self._x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self._x11.XCloseDisplay.restype = ctypes.c_int
        self._x11.XSetInputFocus.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        self._x11.XSetInputFocus.restype = ctypes.c_int
        self._x11.XGetInputFocus.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.c_int),
        ]
        self._x11.XGetInputFocus.restype = ctypes.c_int
        self._x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self._x11.XKeysymToKeycode.restype = ctypes.c_ubyte
        self._x11.XFlush.argtypes = [ctypes.c_void_p]
        self._x11.XFlush.restype = ctypes.c_int
        self._xtst.XTestFakeKeyEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        self._xtst.XTestFakeKeyEvent.restype = ctypes.c_int
        self._display: ctypes.c_void_p | None = None

    def __enter__(self) -> _X11Input:
        display_name = os.environ.get("DISPLAY", "").encode() or None
        self._display = self._x11.XOpenDisplay(display_name)
        if not self._display:
            raise RuntimeError("XOpenDisplay could not open DISPLAY")
        return self

    def __exit__(self, *_exc: object) -> None:
        if self._display:
            self._x11.XCloseDisplay(self._display)
            self._display = None

    def focus_and_press_f1(self, window_id: int) -> None:
        if not self._display:
            raise RuntimeError("X11 display is not open")
        display = self._display
        self._x11.XSetInputFocus(
            display, ctypes.c_ulong(window_id), REVERT_TO_PARENT, CURRENT_TIME
        )
        keycode = self._x11.XKeysymToKeycode(display, XK_F1)
        if not keycode:
            raise RuntimeError("XKeysymToKeycode could not resolve XK_F1")
        self._x11.XFlush(display)
        time.sleep(0.1)
        for pressed in (1, 0):
            if not self._xtst.XTestFakeKeyEvent(display, keycode, pressed, CURRENT_TIME):
                raise RuntimeError("XTestFakeKeyEvent failed for F1")
            self._x11.XFlush(display)
            time.sleep(0.05)

    def focused_window_id(self) -> int | None:
        """Return the X11 input-focus window currently observed by this display."""

        if not self._display:
            raise RuntimeError("X11 display is not open")
        focus_window = ctypes.c_ulong()
        revert_to = ctypes.c_int()
        self._x11.XGetInputFocus(
            self._display,
            ctypes.byref(focus_window),
            ctypes.byref(revert_to),
        )
        return int(focus_window.value)


def _deliver_native_f1_with_retries(
    *,
    window_id: int,
    x11: Any,
    activate_window: Callable[[int], bool],
    wait_for_help: Callable[[float], bool],
    max_attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Deliver native F1 with bounded WM-focus retries and JSON-safe diagnostics."""

    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")
    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, max_attempts + 1):
        focus_before = x11.focused_window_id()
        attempt: dict[str, Any] = {
            "attempt": attempt_number,
            "wmctrl_activation": False,
            "focus_window_before": focus_before,
            "focus_window_after": None,
            "help_opened": False,
        }
        try:
            activated = bool(activate_window(window_id))
            attempt["wmctrl_activation"] = activated
            if activated:
                x11.focus_and_press_f1(window_id)
                attempt["help_opened"] = bool(wait_for_help(2.0))
        except Exception as exc:  # pragma: no cover - live X11 boundary
            attempt["error"] = f"{type(exc).__name__}: {exc}"
        finally:
            try:
                attempt["focus_window_after"] = x11.focused_window_id()
            except Exception as exc:  # pragma: no cover - live X11 boundary
                attempt["focus_observation_error"] = f"{type(exc).__name__}: {exc}"
        attempts.append(attempt)
        if attempt["help_opened"]:
            return {
                "opened": True,
                "attempt_count": attempt_number,
                "attempts": attempts,
            }
        if attempt_number < max_attempts:
            sleep(0.1)
    return {
        "opened": False,
        "attempt_count": len(attempts),
        "attempts": attempts,
    }


def _run_context(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or result.stderr).strip()
    return output or None


def _activate_window(window_id: int) -> bool:
    """Ask the local X11 WM to activate only the audit-owned window."""

    try:
        result = subprocess.run(
            ["wmctrl", "-ia", hex(window_id)],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def _probe_atspi(pid: int, title: str, timeout_seconds: float) -> dict[str, Any]:
    """Run the optional host-Python AT-SPI probe for this exact audit process."""

    try:
        result = subprocess.run(
            [
                "/usr/bin/python3",
                str(Path(__file__).with_name("x11_atspi_probe.py")),
                "--pid",
                str(pid),
                "--title",
                title,
                "--timeout-seconds",
                str(max(0.1, timeout_seconds)),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=max(1.0, timeout_seconds + 1.0),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": "unavailable", "reason": f"probe process: {type(exc).__name__}: {exc}"}
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        return {"status": "unavailable", "reason": f"probe output: {type(exc).__name__}: {exc}"}
    if not isinstance(payload, dict):
        return {"status": "unavailable", "reason": "probe output was not a JSON object"}
    return payload


def _window_is_present(title: str) -> bool:
    windows = _run_context(["wmctrl", "-l"]) or ""
    return any(title in line for line in windows.splitlines())


def _owned_child_processes() -> str | None:
    children: list[str] = []
    proc_root = Path("/proc")
    for entry in proc_root.iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            status = (entry / "status").read_text(encoding="utf-8")
            parent = next(
                line.split("\t", 1)[1].strip()
                for line in status.splitlines()
                if line.startswith("PPid:\t")
            )
            if int(parent) != os.getpid():
                continue
            command = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode(
                errors="replace"
            ).strip()
            children.append(f"{entry.name} {command}".strip())
        except (OSError, StopIteration, ValueError):
            continue
    return "\n".join(children) or None


@contextmanager
def _deadline(seconds: float):
    def handle_timeout(_signum: int, _frame: Any) -> None:
        raise TimeoutError(f"audit exceeded {seconds:.1f}s deadline")

    previous = signal.signal(signal.SIGALRM, handle_timeout)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_frame(root: Path) -> tuple[Any, Any, Any]:
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    settings = AppSettings(
        schema_version=1,
        default_open_directory=str(root / "open"),
        default_output_directory=str(root / "signed"),
        linux_packaging_channel="primary",
        ui={},
    )
    settings_store = AppSettingsStore(storage_dir=root / "config")
    settings_store.save_settings(settings)
    frame = QtAppFrameAdapter().create_frame(
        app_settings=settings,
        app_settings_store=settings_store,
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=root / "certificates"
        ),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=root / "profiles"),
    )
    return frame, settings_store, settings


def _metadata(frame: Any) -> dict[str, Any]:
    from PySide6.QtWidgets import QMenu, QPushButton

    buttons = sorted(
        button.accessibleName()
        for button in frame.window.findChildren(QPushButton)
        if button.accessibleName()
    )
    menus: dict[str, list[dict[str, Any]]] = {}
    for menu in frame.window.menuBar().findChildren(QMenu):
        if not menu.title():
            continue
        menus[menu.title().replace("&", "")] = [
            {
                "object_name": action.objectName(),
                "accessible_name": action.toolTip(),
                "shortcut": action.shortcut().toString(),
                "enabled": action.isEnabled(),
            }
            for action in menu.actions()
        ]
    return {
        "minimum_size": [frame.window.minimumWidth(), frame.window.minimumHeight()],
        "accessible_buttons": buttons,
        "menus": menus,
        "help_shortcut_context": str(
            frame.command_actions()[_help_command_id()].shortcutContext()
        ),
    }


def _rect_metadata(rect: Any) -> dict[str, int]:
    return {
        "x": int(rect.x()),
        "y": int(rect.y()),
        "width": int(rect.width()),
        "height": int(rect.height()),
    }


def _capture_window(window: Any, window_id: int, path: Path, screen: Any) -> None:
    grab = getattr(window, "grab", None)
    if callable(grab):
        pixmap = grab()
        if not pixmap.isNull() and pixmap.save(str(path), "PNG"):
            return
    pixmap = screen.grabWindow(window_id)
    if pixmap.isNull() or not pixmap.save(str(path), "PNG"):
        raise RuntimeError("display screenshot capture failed")


def _visual_metadata(frame: Any, app: Any, artifacts_dir: Path, *, capture: bool) -> dict[str, Any]:
    from PySide6.QtWidgets import QPushButton

    screen = frame.window.screen() or app.primaryScreen()
    if screen is None:
        raise RuntimeError("audit window has no associated display screen")
    buttons = {
        button.accessibleName(): _rect_metadata(button.geometry())
        for button in frame.window.findChildren(QPushButton)
        if getattr(button, "accessibleName", lambda: "")()
    }
    metadata: dict[str, Any] = {
        "window_geometry": _rect_metadata(frame.window.geometry()),
        "window_size": [int(frame.window.width()), int(frame.window.height())],
        "screen_name": str(screen.name()),
        "screen_count": len(app.screens()),
        "screen_geometry": _rect_metadata(screen.geometry()),
        "available_geometry": _rect_metadata(screen.availableGeometry()),
        "device_pixel_ratio": float(screen.devicePixelRatio()),
        "logical_dpi": {
            "x": float(screen.logicalDotsPerInchX()),
            "y": float(screen.logicalDotsPerInchY()),
        },
        "primary_button_geometries": buttons,
        "menu_bar_geometry": _rect_metadata(frame.window.menuBar().geometry()),
        "central_widget_geometry": (
            _rect_metadata(frame.window.centralWidget().geometry())
            if frame.window.centralWidget() is not None
            else None
        ),
    }
    if capture:
        screenshot_path = artifacts_dir / "frame.png"
        _capture_window(frame.window, int(frame.window.winId()), screenshot_path, screen)
        metadata["screenshot"] = screenshot_path.name
    return metadata


def _help_command_id() -> Any:
    from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId

    return AppFrameCommandId.HELP


def _wait_for_help(app: Any, frame: Any, timeout_seconds: float) -> bool:
    """Pump Qt until the modeless Help viewer exists or the bounded wait expires."""

    deadline = time.monotonic() + timeout_seconds
    while frame.help_viewer is None and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.025)
    return frame.help_viewer is not None


def run_audit(
    artifacts_dir: Path,
    timeout_seconds: float,
    capture_screenshot: bool,
    probe_atspi: bool,
) -> int:
    report: dict[str, Any] = {
        "status": "failed",
        "display": os.environ.get("DISPLAY"),
        "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        "context": {
            "xrandr": _run_context(["xrandr", "--query"]),
            "gtk_theme": _run_context(
                ["gsettings", "get", "org.cinnamon.desktop.interface", "gtk-theme"]
            ),
            "text_scaling_factor": _run_context(
                [
                    "gsettings",
                    "get",
                    "org.cinnamon.desktop.interface",
                    "text-scaling-factor",
                ]
            ),
            "orca": _run_context(["orca", "--version"]),
        },
    }
    report_path = artifacts_dir / "audit.json"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    app: Any = None
    frame: Any = None
    exit_code = 1
    temp_root: Path | None = None
    cleanup: dict[str, Any] = {}
    try:
        with _deadline(timeout_seconds):
            with TemporaryDirectory(prefix="foliaseal-x11-accessibility-") as temp_dir:
                temp_root = Path(temp_dir)
                try:
                    if not os.environ.get("DISPLAY"):
                        raise RuntimeError("DISPLAY is not set; this audit requires Cinnamon/X11")
                    from PySide6.QtWidgets import QApplication

                    app = QApplication.instance() or QApplication(
                        ["foliaseal-x11-accessibility-audit"]
                    )
                    frame, _settings_store, _settings = _build_frame(temp_root)
                    frame.window.setWindowTitle(AUDIT_WINDOW_TITLE)
                    frame.window.resize(1100, 700)
                    frame.window.show()
                    frame.window.raise_()
                    frame.window.activateWindow()
                    if hasattr(frame.window, "requestActivate"):
                        frame.window.requestActivate()
                    app.processEvents()
                    wmctrl_activation = _activate_window(int(frame.window.winId()))
                    report["native_input"] = {"wmctrl_activation": wmctrl_activation}
                    if not wmctrl_activation:
                        raise RuntimeError("wmctrl could not activate the audit-owned window")
                    app.processEvents()
                    report["metadata"] = _metadata(frame)
                    if capture_screenshot:
                        report["visual"] = _visual_metadata(
                            frame, app, artifacts_dir, capture=True
                        )
                    frame.command_actions()[_help_command_id()].trigger()
                    app.processEvents()
                    if frame.help_viewer is None:
                        raise AssertionError("direct Help QAction did not open the Help viewer")
                    frame.help_viewer.close()
                    app.processEvents()
                    if frame.help_viewer is not None:
                        raise AssertionError("direct Help viewer did not close cleanly")
                    wmctrl_activation = _activate_window(int(frame.window.winId()))
                    report["native_input"]["wmctrl_activation_before_f1"] = wmctrl_activation
                    if not wmctrl_activation:
                        raise RuntimeError("wmctrl could not reactivate the audit-owned window")
                    with _X11Input() as x11:
                        report["native_input"]["focus_window_before_f1"] = (
                            x11.focused_window_id()
                        )
                        native_result = _deliver_native_f1_with_retries(
                            window_id=int(frame.window.winId()),
                            x11=x11,
                            activate_window=_activate_window,
                            wait_for_help=lambda timeout: _wait_for_help(app, frame, timeout),
                        )
                    report["native_input"].update(native_result)
                    if not native_result["opened"]:
                        raise AssertionError("native X11 F1 did not open the Help viewer")
                    report["help"] = {
                        "opened": True,
                        "modal": frame.help_viewer.dialog.isModal(),
                        "search_accessible_name": frame.help_viewer.search_input.accessibleName(),
                        "content_accessible_name": (
                            frame.help_viewer.content_browser.accessibleName()
                        ),
                        "close_accessible_name": frame.help_viewer.close_button.accessibleName(),
                    }
                    if probe_atspi:
                        report["atspi"] = _probe_atspi(
                            os.getpid(), AUDIT_WINDOW_TITLE, min(2.0, timeout_seconds / 4)
                        )
                    report["status"] = "passed"
                    exit_code = 0
                except Exception as exc:  # pragma: no cover - display environment dependent
                    report["error"] = f"{type(exc).__name__}: {exc}"
                finally:
                    if frame is not None:
                        if frame.help_viewer is not None:
                            frame.help_viewer.close()
                        frame.window.close()
                    if app is not None:
                        app.processEvents()
                    cleanup["owned_window_present_after_close"] = _window_is_present(
                        AUDIT_WINDOW_TITLE
                    )
                    cleanup["owned_temp_root_exists_before_cleanup"] = temp_root.exists()
    except Exception as exc:  # pragma: no cover - signal/display environment dependent
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        exit_code = 1
    cleanup["owned_temp_root_exists_after_cleanup"] = (
        temp_root.exists() if temp_root is not None else False
    )
    cleanup["owned_child_processes_after_close"] = _owned_child_processes()
    cleanup["passed"] = not cleanup.get("owned_window_present_after_close", True) and not (
        cleanup["owned_temp_root_exists_after_cleanup"]
    ) and not cleanup["owned_child_processes_after_close"]
    report["cleanup"] = cleanup
    if exit_code == 0 and not cleanup["passed"]:
        report["status"] = "failed"
        report["error"] = "owned audit resources remained after teardown"
        exit_code = 1
    _write_report(report_path, report)
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("/tmp/foliaseal-x11-accessibility-audit"),
    )
    parser.add_argument("--timeout-seconds", type=float, default=15.0)
    parser.add_argument(
        "--capture-screenshot",
        action="store_true",
        help="Capture the audit-owned X11 frame as frame.png and record display geometry.",
    )
    parser.add_argument(
        "--probe-atspi",
        action="store_true",
        help="Inspect the audit-owned window through host Python AT-SPI (read-only, optional).",
    )
    args = parser.parse_args()
    return run_audit(
        args.artifacts_dir,
        args.timeout_seconds,
        args.capture_screenshot,
        args.probe_atspi,
    )


if __name__ == "__main__":
    sys.exit(main())
