"""Injectable event-processing adapters for the Acceptance harness workspace."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Protocol


class HarnessEventPumpPort(Protocol):
    """One stable operation for processing pending GUI events."""

    def process_events(self) -> None: ...


@dataclass(frozen=True)
class NoOpHarnessEventPump:
    """Headless event-pump adapter."""

    def process_events(self) -> None:
        return None


@dataclass(frozen=True)
class QtHarnessEventPump:
    """Late-bound Qt event-pump adapter for one mounted widget."""

    widget: Any

    def process_events(self) -> None:
        app = _widget_application(self.widget)
        process_events = getattr(app, "processEvents", None)
        if callable(process_events):
            process_events()


def _widget_application(widget: Any) -> Any | None:
    try:
        app_module = importlib.import_module("PySide6.QtWidgets")
    except ModuleNotFoundError:
        return None
    q_application = getattr(app_module, "QApplication", None)
    if q_application is None:
        return None
    instance = getattr(q_application, "instance", None)
    return instance() if callable(instance) else None
