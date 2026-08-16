from __future__ import annotations

from foliaseal.presentation.qt.interactive_harness_qt_lifecycle import (
    HarnessWindowSpec,
    QtHarnessLifecycle,
)


class _FakeApplication:
    current = None
    created = 0

    def __init__(self, _args):
        type(self).current = self
        type(self).created += 1
        self.exec_calls = 0

    @classmethod
    def instance(cls):
        return cls.current

    def exec(self):
        self.exec_calls += 1
        return 7


class _FakeLayout:
    def __init__(self, parent=None):
        self.parent = parent
        self.items = []

    def addLayout(self, layout, *args):  # noqa: N802
        self.items.append((layout, args))

    def addWidget(self, widget, *args):  # noqa: N802
        self.items.append((widget, args))


class _FakeWidget:
    def __init__(self):
        self.layout = None

    def setLayout(self, layout):  # noqa: N802
        self.layout = layout


class _FakeWindow:
    def __init__(self):
        self.closed = 0
        self.central = None
        self.shown = False

    def setWindowTitle(self, value):  # noqa: N802
        self.title = value

    def resize(self, width, height):  # noqa: N802
        self.size = (width, height)

    def setCentralWidget(self, widget):  # noqa: N802
        self.central = widget

    def show(self):
        self.shown = True

    def close(self):
        self.closed += 1


class _Bindings:
    q_application = _FakeApplication
    q_main_window = _FakeWindow
    q_widget = _FakeWidget
    q_v_box_layout = _FakeLayout
    q_h_box_layout = _FakeLayout


def test_qt_harness_lifecycle_owns_window_setup_and_cleanup() -> None:
    _FakeApplication.current = None
    _FakeApplication.created = 0
    lifecycle = QtHarnessLifecycle(_Bindings)

    surface = lifecycle.start(
        spec=HarnessWindowSpec(title="Harness", width=100, height=200)
    )
    child = object()
    lifecycle.mount(surface, child)
    lifecycle.show(surface)

    assert _FakeApplication.created == 1
    assert surface.window.title == "Harness"
    assert surface.window.size == (100, 200)
    assert surface.window.central is surface.central
    assert surface.body.items == [(child, (1,))]
    assert surface.window.shown is True
    assert lifecycle.exec(surface) == 7
    assert surface.app.exec_calls == 1

    lifecycle.close(surface)
    lifecycle.close(surface)
    assert surface.window.closed == 1


def test_qt_harness_lifecycle_reuses_existing_application() -> None:
    _FakeApplication.current = _FakeApplication([])
    _FakeApplication.created = 1
    lifecycle = QtHarnessLifecycle(_Bindings)

    surface = lifecycle.start(spec=HarnessWindowSpec(title="Reuse"))

    assert surface.app is _FakeApplication.current
    assert _FakeApplication.created == 1
