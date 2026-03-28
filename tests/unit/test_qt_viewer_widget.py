import importlib

import pytest

from pdf_signer.application.viewer_session import ViewerSession
from pdf_signer.application.viewer_workflow import ViewerWorkflow
from pdf_signer.presentation.qt import PdfViewerWidgetAdapter, QtViewerBindingsUnavailable
from pdf_signer.presentation.qt.viewer_widget import (
    QtWidgetBindings,
)


class _FakeRenderBackend:
    def render_page(self, request):  # pragma: no cover - not used in this suite
        raise NotImplementedError

    def get_page_geometry(self, document_path: str, page_index: int):  # pragma: no cover
        raise NotImplementedError

    def diagnostics(self):  # pragma: no cover
        raise NotImplementedError


def _build_workflow() -> ViewerWorkflow:
    return ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_FakeRenderBackend(),
        session=ViewerSession(page_count=1),
    )


def test_qt_viewer_widget_adapter_raises_actionable_error_without_pyside6(monkeypatch):
    original_import_module = importlib.import_module

    def _raise_for_pyside6(module_name: str):
        if module_name.startswith("PySide6"):
            raise ModuleNotFoundError("PySide6 is not installed")
        return original_import_module(module_name)

    monkeypatch.setattr(importlib, "import_module", _raise_for_pyside6)

    with pytest.raises(QtViewerBindingsUnavailable, match="PySide6"):
        PdfViewerWidgetAdapter().create(workflow=_build_workflow())


class _FakeQt:
    LeftButton = 1
    Key_Plus = 10
    Key_Equal = 11
    Key_Minus = 12
    Key_Underscore = 13
    Key_0 = 14
    Key_PageDown = 15
    Key_Down = 16
    Key_Right = 17
    Key_PageUp = 18
    Key_Up = 19
    Key_Left = 20
    Key_Home = 21
    Key_End = 22


class _FakePoint:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class _FakePosition:
    def __init__(self, point: _FakePoint):
        self._point = point

    def toPoint(self):
        return self._point


class _FakeMouseEvent:
    def __init__(self, *, button: int, x: int, y: int):
        self._button = button
        self._position = _FakePosition(_FakePoint(x, y))

    def button(self):
        return self._button

    def position(self):
        return self._position


class _FakeKeyEvent:
    def __init__(self, *, key: int):
        self._key = key
        self.accepted = False

    def key(self):
        return self._key

    def accept(self):
        self.accepted = True


class _FakeRect:
    def __init__(self, p1: _FakePoint, p2: _FakePoint):
        self._x1 = p1.x
        self._y1 = p1.y
        self._x2 = p2.x
        self._y2 = p2.y

    def normalized(self):
        self._x1, self._x2 = sorted((self._x1, self._x2))
        self._y1, self._y2 = sorted((self._y1, self._y2))
        return self

    def left(self):
        return self._x1

    def top(self):
        return self._y1

    def right(self):
        return self._x2

    def bottom(self):
        return self._y2


class _FakeWidget:
    def __init__(self):
        self.update_calls = 0

    def update(self):
        self.update_calls += 1

    def setMinimumSize(self, width: int, height: int):  # noqa: N802
        return None

    def mousePressEvent(self, event):  # noqa: N802
        return None

    def mouseReleaseEvent(self, event):  # noqa: N802
        return None

    def keyPressEvent(self, event):  # noqa: N802
        return None


class _FakePainter:
    def __init__(self, widget):
        self.widget = widget

    def drawPixmap(self, *args):
        return None

    def setPen(self, pen):
        return None

    def drawRect(self, rect):
        return None

    def end(self):
        return None


class _FakeImage:
    Format_RGBA8888 = object()

    def __init__(self, *args, **kwargs):
        return None

    def copy(self):
        return self


class _FakePixmap:
    @classmethod
    def fromImage(cls, image):  # noqa: N802
        return cls()


def _fake_bindings() -> QtWidgetBindings:
    return QtWidgetBindings(
        q_widget=_FakeWidget,
        q_painter=_FakePainter,
        q_color=lambda *args: object(),
        q_pen=lambda *args: object(),
        q_pixmap=_FakePixmap,
        q_image=_FakeImage,
        q_rect=_FakeRect,
        q_point=_FakePoint,
        qt=_FakeQt,
    )


def test_mouse_release_event_handles_selection_conversion_failures(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = _build_workflow()
    selected = []

    widget = PdfViewerWidgetAdapter().create(workflow=workflow, on_selection=selected.append)
    widget.mousePressEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=10, y=10))
    widget.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=20, y=20))

    assert selected == []


def test_mouse_release_event_reports_selection_mapping_errors(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = _build_workflow()
    selected = []
    errors = []

    widget = PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    widget.mousePressEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=10, y=10))
    widget.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=20, y=20))

    assert selected == []
    assert len(errors) == 1
    assert "Selection could not be placed on the PDF page." in errors[0]


def test_refresh_reports_render_errors(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _BrokenWorkflow:
        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            raise RuntimeError("render backend unavailable")

    errors = []
    widget = PdfViewerWidgetAdapter().create(
        workflow=_BrokenWorkflow(),
        on_error=errors.append,
    )

    widget.refresh()

    assert len(errors) == 1
    assert "Unable to render PDF preview." in errors[0]


def test_refresh_reraises_render_errors_without_error_callback(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _BrokenWorkflow:
        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            raise RuntimeError("render backend unavailable")

    widget = PdfViewerWidgetAdapter().create(workflow=_BrokenWorkflow())

    with pytest.raises(RuntimeError, match="render backend unavailable"):
        widget.refresh()


def test_key_press_event_wires_keyboard_affordances(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithKeyboardActions:
        def __init__(self):
            self.actions = []
            self.session = ViewerSession(page_count=4)

        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            self.actions.append(("render", navigation))
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

        def zoom_in(self):
            self.actions.append("zoom_in")
            return 1.0

        def zoom_out(self):
            self.actions.append("zoom_out")
            return 1.0

        def reset_zoom(self):
            self.actions.append("reset_zoom")
            return 1.0

        def go_next_page(self, *, elapsed_ms=None):
            self.actions.append("go_next_page")
            return self.render_current_page(elapsed_ms=elapsed_ms, navigation=True)

        def go_previous_page(self, *, elapsed_ms=None):
            self.actions.append("go_previous_page")
            return self.render_current_page(elapsed_ms=elapsed_ms, navigation=True)

        def jump_to_page(self, page_index):
            self.actions.append(("jump_to_page", page_index))
            return self.render_current_page(navigation=True)

    workflow = _WorkflowWithKeyboardActions()
    widget = PdfViewerWidgetAdapter().create(workflow=workflow)

    for key in (
        _FakeQt.Key_Plus,
        _FakeQt.Key_Minus,
        _FakeQt.Key_0,
        _FakeQt.Key_PageDown,
        _FakeQt.Key_PageUp,
        _FakeQt.Key_Home,
        _FakeQt.Key_End,
    ):
        widget.keyPressEvent(_FakeKeyEvent(key=key))

    assert "zoom_in" in workflow.actions
    assert "zoom_out" in workflow.actions
    assert "reset_zoom" in workflow.actions
    assert "go_next_page" in workflow.actions
    assert "go_previous_page" in workflow.actions
    assert ("jump_to_page", 0) in workflow.actions
    assert ("jump_to_page", 3) in workflow.actions
