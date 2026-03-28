import importlib

import pytest

from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.presentation.qt import PdfViewerWidgetAdapter, QtViewerBindingsUnavailable
from foliaseal.presentation.qt.viewer_widget import (
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
    MiddleButton = 2
    NoModifier = 0
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

    class KeyboardModifier:
        ShiftModifier = 1 << 0


class _FakePoint:
    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class _FakePosition:
    def __init__(self, point: _FakePoint):
        self._point = point

    def toPoint(self):
        return self._point


class _FakeMouseEvent:
    def __init__(self, *, button: int, x: int, y: int, modifiers: int = _FakeQt.NoModifier):
        self._button = button
        self._position = _FakePosition(_FakePoint(x, y))
        self._modifiers = modifiers
        self.accepted = False

    def button(self):
        return self._button

    def position(self):
        return self._position

    def modifiers(self):
        return self._modifiers

    def accept(self):
        self.accepted = True


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
        self._x1 = p1.x()
        self._y1 = p1.y()
        self._x2 = p2.x()
        self._y2 = p2.y()

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
        self.mouse_grabbed = False

    def update(self):
        self.update_calls += 1

    def setMinimumSize(self, width: int, height: int):  # noqa: N802
        return None

    def grabMouse(self):  # noqa: N802
        self.mouse_grabbed = True

    def releaseMouse(self):  # noqa: N802
        self.mouse_grabbed = False

    def mousePressEvent(self, event):  # noqa: N802
        return None

    def mouseReleaseEvent(self, event):  # noqa: N802
        return None

    def hideEvent(self, event):  # noqa: N802
        return None

    def keyPressEvent(self, event):  # noqa: N802
        return None


class _FakeScrollArea(_FakeWidget):
    def __init__(self):
        super().__init__()
        self.widget = None
        self.widget_resizable = None
        self.focus_proxy = None
        self._horizontal_scroll_bar = _FakeScrollBar()
        self._vertical_scroll_bar = _FakeScrollBar()

    def setWidget(self, widget):  # noqa: N802
        self.widget = widget

    def setWidgetResizable(self, value):  # noqa: N802
        self.widget_resizable = value

    def setFocusProxy(self, widget):  # noqa: N802
        self.focus_proxy = widget

    def horizontalScrollBar(self):  # noqa: N802
        return self._horizontal_scroll_bar

    def verticalScrollBar(self):  # noqa: N802
        return self._vertical_scroll_bar


class _FakeScrollBar:
    def __init__(self):
        self._value = 0

    def value(self):
        return self._value

    def setValue(self, value):  # noqa: N802
        self._value = value


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
        q_scroll_area=_FakeScrollArea,
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
    assert workflow.actions.count(("render", True)) == 4


def test_key_press_event_reports_navigation_render_errors(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _BrokenNavigationWorkflow:
        def __init__(self):
            self.session = ViewerSession(page_count=2)

        def go_next_page(self, *, elapsed_ms=None):
            raise RuntimeError("render backend unavailable")

    errors = []
    widget = PdfViewerWidgetAdapter().create(
        workflow=_BrokenNavigationWorkflow(),
        on_error=errors.append,
    )

    widget.keyPressEvent(_FakeKeyEvent(key=_FakeQt.Key_PageDown))

    assert len(errors) == 1
    assert "Unable to render PDF preview after navigating to the next page." in errors[0]


def test_build_qt_pdf_viewer_widget_wraps_preview_in_scroll_area(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithRender:
        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    widget = build_qt_pdf_viewer_widget(workflow=_WorkflowWithRender())
    widget.refresh()

    assert isinstance(widget, _FakeScrollArea)
    assert isinstance(widget.widget, _FakeWidget)
    assert widget.widget_resizable is False
    assert widget.focus_proxy is widget.widget


def test_middle_drag_pans_scrollbars(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithRender:
        def __init__(self):
            self.pan_updates = []

        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

        def set_pan(self, *, pan_x, pan_y):
            self.pan_updates.append((pan_x, pan_y))

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    workflow = _WorkflowWithRender()
    widget = build_qt_pdf_viewer_widget(workflow=workflow)
    preview = widget.widget
    widget.horizontalScrollBar().setValue(100)
    widget.verticalScrollBar().setValue(80)

    preview.mousePressEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=50, y=40))
    assert preview.mouse_grabbed is True
    preview.mouseMoveEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=70, y=65))
    preview.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=70, y=65))

    assert widget.horizontalScrollBar().value() == 80
    assert widget.verticalScrollBar().value() == 55
    assert preview.mouse_grabbed is False
    assert workflow.pan_updates[-1] == (-80.0, -55.0)


def test_middle_drag_does_not_emit_selection(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithSelection:
        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

        def selection_to_pdf_rect(self, *, selection):
            return selection

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    selected = []
    widget = build_qt_pdf_viewer_widget(
        workflow=_WorkflowWithSelection(),
        on_selection=selected.append,
    )
    preview = widget.widget

    preview.mousePressEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=10, y=10))
    preview.mouseMoveEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=30, y=30))
    preview.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=30, y=30))

    assert selected == []


def test_shift_left_drag_pans_scrollbars(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithRender:
        def __init__(self):
            self.pan_updates = []

        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

        def set_pan(self, *, pan_x, pan_y):
            self.pan_updates.append((pan_x, pan_y))

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    workflow = _WorkflowWithRender()
    widget = build_qt_pdf_viewer_widget(workflow=workflow)
    preview = widget.widget
    widget.horizontalScrollBar().setValue(120)
    widget.verticalScrollBar().setValue(90)

    preview.mousePressEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=60,
            y=50,
            modifiers=_FakeQt.KeyboardModifier.ShiftModifier,
        )
    )
    assert preview.mouse_grabbed is True
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=90,
            y=70,
            modifiers=_FakeQt.KeyboardModifier.ShiftModifier,
        )
    )
    preview.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=90, y=70))

    assert widget.horizontalScrollBar().value() == 90
    assert widget.verticalScrollBar().value() == 70
    assert preview.mouse_grabbed is False
    assert workflow.pan_updates[-1] == (-90.0, -70.0)


def test_plain_left_drag_emits_selection_with_viewport_relative_coords(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithSelection:
        def __init__(self):
            self.pan_updates = []

        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

        def set_pan(self, *, pan_x, pan_y):
            self.pan_updates.append((pan_x, pan_y))

        def selection_to_pdf_rect(self, *, selection):
            return selection

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    selected = []
    workflow = _WorkflowWithSelection()
    widget = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_selection=selected.append,
    )
    preview = widget.widget
    widget.horizontalScrollBar().setValue(100)
    widget.verticalScrollBar().setValue(80)

    preview.mousePressEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=110, y=95))
    preview.mouseMoveEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=130, y=115))
    preview.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=130, y=115))

    assert len(selected) == 1
    assert selected[0].x1 == 10.0
    assert selected[0].y1 == 15.0
    assert selected[0].x2 == 30.0
    assert selected[0].y2 == 35.0
    assert workflow.pan_updates[-1] == (-100.0, -80.0)


def test_hide_event_releases_active_middle_drag(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithRender:
        def render_current_page(self, *, elapsed_ms=None, navigation=False):
            return type(
                "_RenderResult",
                (),
                {
                    "rgba_bytes": b"\x00" * 16,
                    "width_px": 2,
                    "height_px": 2,
                },
            )()

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    widget = build_qt_pdf_viewer_widget(workflow=_WorkflowWithRender())
    preview = widget.widget

    preview.mousePressEvent(_FakeMouseEvent(button=_FakeQt.MiddleButton, x=10, y=10))
    assert preview.mouse_grabbed is True

    preview.hideEvent(object())

    assert preview.mouse_grabbed is False
