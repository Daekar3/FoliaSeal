"""Lifecycle port for the signed-acceptance matrix runner."""

from __future__ import annotations

from typing import Any, Protocol


class SignedAcceptanceLifecyclePort(Protocol):
    """Own only the Qt window/event-loop lifecycle for one matrix run."""

    def start(self, *, title: str) -> None:
        """Create the application/window before any QWidget is constructed."""

    def attach_shell(self, shell: Any) -> None:
        """Install and show the prepared shell."""

    def process_events(self) -> None:
        """Flush pending UI work after a scenario transition."""

    def close(self) -> None:
        """Close the run window and release its UI resources."""


class QtSignedAcceptanceLifecycle:
    """Production lifecycle adapter around the existing Qt bindings."""

    def __init__(self, bindings: Any) -> None:
        self._bindings = bindings
        self._application: Any | None = None
        self._window: Any | None = None

    def start(self, *, title: str) -> None:
        self._application = (
            self._bindings.q_application.instance()
            or self._bindings.q_application([])
        )
        self._window = self._bindings.q_main_window()
        self._window.setWindowTitle(title)
        self._window.resize(1440, 980)

    def attach_shell(self, shell: Any) -> None:
        if self._window is None:
            raise RuntimeError("Qt lifecycle must start before attaching the shell.")
        self._window.setCentralWidget(shell)
        self._window.show()

    def process_events(self) -> None:
        if self._application is not None:
            self._application.processEvents()

    def close(self) -> None:
        if self._window is not None:
            close = getattr(self._window, "close", None)
            if callable(close):
                close()
        self._window = None
        self._application = None


class FakeSignedAcceptanceLifecycle:
    """Deterministic lifecycle substitute for matrix orchestration tests."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []

    def start(self, *, title: str) -> None:
        self.calls.append(("start", title))

    def attach_shell(self, shell: Any) -> None:
        _ = shell
        self.calls.append(("attach_shell", None))

    def process_events(self) -> None:
        self.calls.append(("process_events", None))

    def close(self) -> None:
        self.calls.append(("close", None))
