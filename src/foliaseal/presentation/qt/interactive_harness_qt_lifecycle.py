"""Fakeable Qt application/window lifecycle for the interactive evidence harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class HarnessQtBindings:
    """Late-bound Qt constructors shared by the lifecycle and harness adapters."""

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
class HarnessWindowSpec:
    """Stable window metadata for one interactive harness session."""

    title: str
    width: int = 1440
    height: int = 980


@dataclass(frozen=True)
class HarnessQtSurface:
    """Opaque layout targets returned by the lifecycle adapter."""

    app: Any
    window: Any
    central: Any
    toolbar: Any
    body: Any


class HarnessQtLifecyclePort(Protocol):
    """Lifecycle operations needed by the interactive harness runner."""

    def start(self, *, spec: HarnessWindowSpec) -> HarnessQtSurface: ...

    def mount(self, surface: HarnessQtSurface, widget: Any) -> None: ...

    def show(self, surface: HarnessQtSurface) -> None: ...

    def exec(self, surface: HarnessQtSurface) -> int: ...

    def close(self, surface: HarnessQtSurface) -> None: ...


class QtHarnessLifecycle:
    """Concrete Qt adapter for one standalone harness window and event loop."""

    def __init__(self, bindings: Any) -> None:
        self._bindings = bindings
        self._closed_surface_ids: set[int] = set()

    def start(self, *, spec: HarnessWindowSpec) -> HarnessQtSurface:
        application = self._bindings.q_application.instance()
        if application is None:
            application = self._bindings.q_application([])
        window = self._bindings.q_main_window()
        window.setWindowTitle(spec.title)
        window.resize(spec.width, spec.height)

        central = self._bindings.q_widget()
        layout = self._bindings.q_v_box_layout(central)
        toolbar = self._bindings.q_h_box_layout()
        layout.addLayout(toolbar)
        body = self._bindings.q_h_box_layout()
        layout.addLayout(body, 1)
        return HarnessQtSurface(
            app=application,
            window=window,
            central=central,
            toolbar=toolbar,
            body=body,
        )

    def mount(self, surface: HarnessQtSurface, widget: Any) -> None:
        surface.window.setCentralWidget(surface.central)
        surface.body.addWidget(widget, 1)

    def show(self, surface: HarnessQtSurface) -> None:
        surface.window.show()

    def exec(self, surface: HarnessQtSurface) -> int:
        return int(surface.app.exec())

    def close(self, surface: HarnessQtSurface) -> None:
        surface_id = id(surface)
        if surface_id in self._closed_surface_ids:
            return
        self._closed_surface_ids.add(surface_id)
        close = getattr(surface.window, "close", None)
        if callable(close):
            close()
