"""Unit tests for the optional host AT-SPI probe boundary."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


def _probe_module() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts" / "x11_atspi_probe.py"
    spec = importlib.util.spec_from_file_location("x11_atspi_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bus_result(stdout: str) -> SimpleNamespace:
    return SimpleNamespace(stdout=stdout, returncode=0)


def _busctl_runner(session_output: str):
    def run(args, **_kwargs):
        if "call" in args:
            return _bus_result('s "unix:path=/run/user/1000/at-spi/bus_0"')
        return _bus_result(session_output)

    return run


def test_probe_requires_atspi_bus_launcher_on_session_bus(monkeypatch) -> None:
    module = _probe_module()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        _busctl_runner("org.a11y.atspi.Registry\n"),
    )

    result = module.inspect(42, "FoliaSeal X11 Accessibility Audit", 0.1)

    assert result["status"] == "unavailable"
    assert "org.a11y.Bus" in result["reason"]


def test_probe_reports_registry_connection_failure(monkeypatch) -> None:
    module = _probe_module()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        _busctl_runner("org.a11y.Bus\n"),
    )

    class _Registry:
        @staticmethod
        def getDesktop(_screen: int):
            raise RuntimeError("AT-SPI socket missing")

    monkeypatch.setitem(sys.modules, "pyatspi", SimpleNamespace(Registry=_Registry))

    result = module.inspect(42, "FoliaSeal X11 Accessibility Audit", 0.1)

    assert result == {
        "status": "unavailable",
        "reason": "registry: RuntimeError: AT-SPI socket missing",
    }


def test_probe_traverses_only_owned_frame(monkeypatch) -> None:
    module = _probe_module()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        _busctl_runner("org.a11y.Bus\n"),
    )

    class _State:
        def contains(self, _value: int) -> bool:
            return True

    class _Action:
        def get_n_actions(self) -> int:
            return 1

        def get_action_name(self, _index: int) -> str:
            return "click"

    class _Leaf:
        name = "Open a PDF"
        childCount = 0

        def getRoleName(self) -> str:
            return "push button"

    class _Frame:
        name = "FoliaSeal X11 Accessibility Audit"
        childCount = 1

        def getRoleName(self) -> str:
            return "frame"

        def getState(self) -> _State:
            return _State()

        def queryAction(self) -> _Action:
            return _Action()

        def queryComponent(self):
            return SimpleNamespace(
                get_extents=lambda _coords: SimpleNamespace(x=10, y=20, width=1100, height=700)
            )

        def getChildAtIndex(self, index: int):
            assert index == 0
            return _Leaf()

    class _Application:
        name = "FoliaSeal"
        childCount = 1

        def get_process_id(self) -> int:
            return 42

        def getChildAtIndex(self, index: int):
            assert index == 0
            return _Frame()

    class _Desktop:
        childCount = 1

        def getChildAtIndex(self, index: int):
            assert index == 0
            return _Application()

    class _Registry:
        @staticmethod
        def getDesktop(_screen: int):
            return _Desktop()

    fake_pyatspi = SimpleNamespace(
        Registry=_Registry,
        STATE_VISIBLE=1,
        STATE_SHOWING=2,
        STATE_FOCUSED=3,
        STATE_ENABLED=4,
        DESKTOP_COORDS=5,
    )
    monkeypatch.setitem(sys.modules, "pyatspi", fake_pyatspi)

    result = module.inspect(42, "FoliaSeal X11 Accessibility Audit", 0.1)

    assert result["status"] == "available"
    assert result["process_id"] == 42
    assert result["frame"]["role"] == "frame"
    assert result["frame"]["extents"] == {"x": 10, "y": 20, "width": 1100, "height": 700}
    assert result["children"][0]["name"] == "Open a PDF"
    assert result["children_truncated"] is False


def test_children_honors_expired_deadline_without_touching_tree() -> None:
    module = _probe_module()

    children, truncated = module._children(object(), SimpleNamespace(), deadline=0.0)  # noqa: SLF001

    assert children == []
    assert truncated is True
