import importlib

import pytest

from foliaseal.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewTransform,
    pdf_rect_to_view_rect,
)
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect
from foliaseal.infra.render import PdfPageGeometry, RenderPageResult
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
    IBeamCursor = "ibeam"
    CrossCursor = "cross"
    OpenHandCursor = "open-hand"
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
    Key_Escape = 23
    Key_Return = 24
    Key_Enter = 25
    ControlModifier = 1 << 1

    class KeyboardModifier:
        ShiftModifier = 1 << 0
        ControlModifier = 1 << 1


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

    def x(self):
        return self._point.x()

    def y(self):
        return self._point.y()

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
    def __init__(self, *, key: int, modifiers: int = _FakeQt.NoModifier):
        self._key = key
        self.accepted = False
        self._modifiers = modifiers

    def key(self):
        return self._key

    def modifiers(self):
        return self._modifiers

    def accept(self):
        self.accepted = True


class _FakeWheelDelta:
    def __init__(self, y: int):
        self._y = y

    def y(self):
        return self._y


class _FakeWheelEvent:
    def __init__(self, *, delta_y: int, modifiers: int = _FakeQt.NoModifier):
        self._delta = _FakeWheelDelta(delta_y)
        self._modifiers = modifiers
        self.accepted = False

    def angleDelta(self):
        return self._delta

    def modifiers(self):
        return self._modifiers

    def accept(self):
        self.accepted = True


def test_wheel_pans_without_changing_page_and_ctrl_wheel_zoom_is_explicit(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=2),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    scroll = _FakeScrollArea()
    preview.attach_scroll_container(scroll)
    preview.refresh()
    initial_zoom = workflow.session.zoom

    preview.wheelEvent(_FakeWheelEvent(delta_y=120))
    assert workflow.session.current_page == 0
    assert workflow.session.zoom == initial_zoom
    assert scroll.verticalScrollBar().value() < 0 or scroll.horizontalScrollBar().value() < 0

    preview.wheelEvent(
        _FakeWheelEvent(delta_y=120, modifiers=_FakeQt.ControlModifier)
    )
    assert workflow.session.current_page == 0
    assert workflow.session.zoom > initial_zoom


def test_fit_page_and_width_use_scroll_viewport_without_changing_page(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=2),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    preview.attach_scroll_container(_FakeScrollArea())
    preview.refresh()

    preview.fit_page_view()
    assert workflow.session.zoom == pytest.approx(0.8)
    assert workflow.session.zoom_mode == "fit_page"
    assert workflow.session.current_page == 0

    preview.fit_width_view()
    assert workflow.session.zoom == pytest.approx(0.9)
    assert workflow.session.zoom_mode == "fit_width"
    assert workflow.session.current_page == 0


def test_first_visible_view_uses_fit_page(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    scroll = _FakeScrollArea()
    preview.attach_scroll_container(scroll)
    preview.refresh()

    preview.showEvent(object())

    assert workflow.session.zoom_mode == "fit_page"
    assert workflow.session.zoom == pytest.approx(0.8)


def test_fit_modes_preserve_signature_overlay_page_and_coordinates(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=2),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    preview.attach_scroll_container(_FakeScrollArea())
    preview.refresh()
    signature = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    preview.set_signature_overlay(signature)

    for fit in (preview.fit_page_view, preview.fit_width_view):
        fit()
        snapshot = workflow.snapshot
        assert snapshot is not None
        assert snapshot.page_index == signature.page_index
        actual = preview._current_overlay_view_rect()
        expected = pdf_rect_to_view_rect(
            pdf_rect=PdfRect(
                x1=signature.left_pt,
                y1=signature.bottom_pt,
                x2=signature.left_pt + signature.width_pt,
                y2=signature.bottom_pt + signature.height_pt,
            ),
            transform=ViewTransform(
                zoom=snapshot.zoom,
                pan_x=snapshot.pan_x,
                pan_y=snapshot.pan_y,
            ),
            page_box=snapshot.page_box,
            rotation=snapshot.rotation,
        )
        assert actual is not None
        assert actual.x1 == pytest.approx(expected.x1)
        assert actual.y1 == pytest.approx(expected.y1)
        assert actual.x2 == pytest.approx(expected.x2)
        assert actual.y2 == pytest.approx(expected.y2)


def test_search_highlights_keep_current_and_quiet_rectangles_independent(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    preview.attach_scroll_container(_FakeScrollArea())
    preview.refresh()
    current = PdfRect(x1=10.0, y1=20.0, x2=30.0, y2=30.0)
    quiet = PdfRect(x1=10.0, y1=40.0, x2=30.0, y2=50.0)

    preview.set_text_search_highlight_overlay(
        page_index=0,
        current_highlight_rects=(current,),
        secondary_highlight_rects=(quiet,),
    )

    assert len(preview._current_text_search_qrects()) == 1
    assert len(preview._current_text_search_secondary_qrects()) == 1
    preview.clear_text_search_highlight_overlay()
    assert preview._current_text_search_qrects() == ()
    assert preview._current_text_search_secondary_qrects() == ()


def test_review_highlight_overlay_is_independent_and_clears(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    preview.attach_scroll_container(_FakeScrollArea())
    preview.refresh()
    rect = PdfRect(x1=20.0, y1=25.0, x2=80.0, y2=65.0)

    preview.set_review_highlight_overlay(page_index=0, highlight_rect=rect)

    assert preview._current_review_highlight_qrect() is not None
    assert preview._current_text_highlight_qrects() == ()
    preview.clear_review_highlight_overlay()
    assert preview._current_review_highlight_qrect() is None


def test_wheel_without_scroll_container_cannot_change_page(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=2),
    )
    preview = PdfViewerWidgetAdapter().create(workflow=workflow)
    event = _FakeWheelEvent(delta_y=-120)

    preview.wheelEvent(event)

    assert event.accepted is True
    assert workflow.session.current_page == 0


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
        self.minimum_size = None
        self.size = None
        self.cursor = None

    def update(self):
        self.update_calls += 1

    def setMinimumSize(self, width: int, height: int):  # noqa: N802
        self.minimum_size = (width, height)

    def resize(self, width: int, height: int):  # noqa: N802
        self.size = (width, height)

    def grabMouse(self):  # noqa: N802
        self.mouse_grabbed = True

    def releaseMouse(self):  # noqa: N802
        self.mouse_grabbed = False

    def setCursor(self, cursor):  # noqa: N802
        self.cursor = cursor

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
        self._viewport = _FakeViewport()

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

    def viewport(self):
        return self._viewport


class _FakeViewport:
    def width(self):
        return 180

    def height(self):
        return 160


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

    def fillRect(self, *args):
        return None

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


class _OverlayRenderBackend:
    def render_page(self, request):  # pragma: no cover - simple test helper
        size = int(200 * request.zoom)
        return RenderPageResult(
            width_px=size,
            height_px=size,
            rgba_bytes=b"\x00" * (size * size * 4),
        )

    def get_page_geometry(self, document_path: str, page_index: int):  # pragma: no cover
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 100.0, 100.0),
            crop_box=(0.0, 0.0, 100.0, 100.0),
            rotation=0,
        )

    def diagnostics(self):  # pragma: no cover
        raise NotImplementedError


class _ZoomSensitiveRenderBackend:
    def render_page(self, request):
        if request.zoom < 1.0:
            return RenderPageResult(
                width_px=140,
                height_px=180,
                rgba_bytes=b"\x00" * (140 * 180 * 4),
            )
        return RenderPageResult(
            width_px=260,
            height_px=320,
            rgba_bytes=b"\x00" * (260 * 320 * 4),
        )

    def get_page_geometry(self, document_path: str, page_index: int):  # pragma: no cover
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 100.0, 100.0),
            crop_box=(0.0, 0.0, 100.0, 100.0),
            rotation=0,
        )

    def diagnostics(self):  # pragma: no cover
        raise NotImplementedError


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


def test_plain_click_does_not_emit_selection(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithSelection:
        def selection_to_pdf_rect(self, *, selection):
            return selection

    selected = []
    widget = PdfViewerWidgetAdapter().create(
        workflow=_WorkflowWithSelection(),
        on_selection=selected.append,
    )

    widget.mousePressEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=20, y=30))
    widget.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=20, y=30))

    assert selected == []


def test_escape_cancels_unfinished_signature_drag_without_emitting_selection(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    class _WorkflowWithSelection:
        def selection_to_pdf_rect(self, *, selection):
            return selection

    selected = []
    widget = PdfViewerWidgetAdapter().create(
        workflow=_WorkflowWithSelection(),
        on_selection=selected.append,
    )

    widget.mousePressEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=20, y=30))
    widget.mouseMoveEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=60, y=70))
    widget.keyPressEvent(_FakeKeyEvent(key=_FakeQt.Key_Escape))
    widget.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=60, y=70))

    assert selected == []
    assert widget._drag_origin is None
    assert widget._selection_rect is None


def test_overlay_corner_handle_resizes_persistent_signature_overlay(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    errors = []
    preview = PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    preview.refresh()

    preview.set_signature_overlay(
        SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=30.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    view_rect = pdf_rect_to_view_rect(
        pdf_rect=PdfRect(x1=20.0, y1=30.0, x2=60.0, y2=50.0),
        transform=ViewTransform(zoom=1.0, pan_x=0.0, pan_y=0.0),
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )

    preview.mousePressEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1),
            y=int(view_rect.y1),
        )
    )
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1 + 10),
            y=int(view_rect.y1 + 8),
        )
    )
    preview.mouseReleaseEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1 + 10),
            y=int(view_rect.y1 + 8),
        )
    )

    assert len(selected) == 1
    assert errors == []
    normalized = selected[0].normalized()
    assert normalized.x1 > 20.0
    assert normalized.x2 == 60.0
    assert normalized.y2 > normalized.y1


def test_escape_cancels_overlay_resize_without_mutating_completed_placement(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    preview = PdfViewerWidgetAdapter().create(workflow=workflow, on_selection=selected.append)
    preview.refresh()
    original = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    preview.set_signature_overlay(original)
    view_rect = pdf_rect_to_view_rect(
        pdf_rect=PdfRect(x1=20.0, y1=30.0, x2=60.0, y2=50.0),
        transform=ViewTransform(zoom=1.0, pan_x=0.0, pan_y=0.0),
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )

    preview.mousePressEvent(
        _FakeMouseEvent(button=_FakeQt.LeftButton, x=int(view_rect.x1), y=int(view_rect.y1))
    )
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1 + 12),
            y=int(view_rect.y1 + 8),
        )
    )
    preview.keyPressEvent(_FakeKeyEvent(key=_FakeQt.Key_Escape))
    preview.mouseReleaseEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1 + 12),
            y=int(view_rect.y1 + 8),
        )
    )

    assert selected == []
    assert preview._overlay_drag_handle is None
    assert preview._overlay_signature_rect == original


def test_text_interaction_mode_ignores_signature_overlay_resize_handles(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    errors = []
    preview = PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    preview.refresh()
    preview.set_interaction_mode("text")
    preview.set_signature_overlay(
        SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=30.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    view_rect = pdf_rect_to_view_rect(
        pdf_rect=PdfRect(x1=20.0, y1=30.0, x2=60.0, y2=50.0),
        transform=ViewTransform(zoom=1.0, pan_x=0.0, pan_y=0.0),
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )

    preview.mousePressEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1),
            y=int(view_rect.y1),
        )
    )
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1 + 10),
            y=int(view_rect.y1 + 8),
        )
    )
    preview.mouseReleaseEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1 + 10),
            y=int(view_rect.y1 + 8),
        )
    )

    assert errors == []
    assert len(selected) == 1
    normalized = selected[0].normalized()
    assert normalized.x1 == 20.0
    assert normalized.y1 == 22.0
    assert normalized.x2 == 30.0
    assert normalized.y2 == 30.0


def test_set_interaction_mode_changes_cursor(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    preview = PdfViewerWidgetAdapter().create(workflow=_build_workflow())

    assert preview.cursor is None

    preview.set_interaction_mode("text")

    assert preview.cursor == _FakeQt.IBeamCursor

    preview.set_interaction_mode("signature")

    assert preview.cursor == _FakeQt.CrossCursor

    preview.set_interaction_mode("pan")

    assert preview.cursor == _FakeQt.OpenHandCursor


def test_keyboard_place_enter_and_shift_arrow_are_only_active_in_place_mode(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    created = []
    moved = []
    rect = SignatureRect(
        page_index=0,
        left_pt=10.0,
        bottom_pt=20.0,
        width_pt=30.0,
        height_pt=10.0,
    )
    preview = PdfViewerWidgetAdapter().create(
        workflow=_build_workflow(),
        on_keyboard_create=lambda: (created.append(rect) or rect),
        on_keyboard_move=lambda dx, dy: (moved.append((dx, dy)) or rect),
    )
    preview.set_interaction_mode("pan")
    preview.keyPressEvent(_FakeKeyEvent(key=_FakeQt.Key_Return))
    assert created == []

    preview.set_interaction_mode("signature")
    preview.keyPressEvent(_FakeKeyEvent(key=_FakeQt.Key_Return))
    preview.keyPressEvent(
        _FakeKeyEvent(key=_FakeQt.Key_Right, modifiers=_FakeQt.KeyboardModifier.ShiftModifier)
    )

    assert created == [rect]
    assert moved == [(10.0, 0.0)]


def test_overlay_resize_handle_clamps_before_inverting_rectangle(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    errors = []
    preview = PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    preview.refresh()

    preview.set_signature_overlay(
        SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=30.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    view_rect = pdf_rect_to_view_rect(
        pdf_rect=PdfRect(x1=20.0, y1=30.0, x2=60.0, y2=50.0),
        transform=ViewTransform(zoom=1.0, pan_x=0.0, pan_y=0.0),
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )

    preview.mousePressEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x1),
            y=int(view_rect.y1),
        )
    )
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x2 + 25),
            y=int(view_rect.y2 + 25),
        )
    )
    preview.mouseReleaseEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x2 + 25),
            y=int(view_rect.y2 + 25),
        )
    )

    assert len(selected) == 1
    assert errors == []
    normalized = selected[0].normalized()
    assert normalized.x2 > normalized.x1
    assert normalized.y2 > normalized.y1


def test_overlay_resize_handle_remains_stable_with_pan_offset(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    workflow.set_pan(pan_x=-18.0, pan_y=-24.0)

    selected = []
    errors = []
    preview = PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    preview.refresh()

    preview.set_signature_overlay(
        SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=30.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    view_rect = pdf_rect_to_view_rect(
        pdf_rect=PdfRect(x1=20.0, y1=30.0, x2=60.0, y2=50.0),
        transform=ViewTransform(zoom=1.0, pan_x=-18.0, pan_y=-24.0),
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )

    preview.mousePressEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x2),
            y=int(view_rect.y2),
        )
    )
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x2 + 12),
            y=int(view_rect.y2 + 10),
        )
    )
    preview.mouseReleaseEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=int(view_rect.x2 + 12),
            y=int(view_rect.y2 + 10),
        )
    )

    assert len(selected) == 1
    assert errors == []
    normalized = selected[0].normalized()
    assert normalized.x2 > normalized.x1
    assert normalized.y2 > normalized.y1


def test_overlay_resize_handle_preserves_grab_offset_without_snapping(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    errors = []
    preview = PdfViewerWidgetAdapter().create(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    preview.refresh()

    preview.set_signature_overlay(
        SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=30.0,
            width_pt=40.0,
            height_pt=20.0,
        )
    )

    view_rect = pdf_rect_to_view_rect(
        pdf_rect=PdfRect(x1=20.0, y1=30.0, x2=60.0, y2=50.0),
        transform=ViewTransform(zoom=1.0, pan_x=0.0, pan_y=0.0),
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )

    start_x = int(min(view_rect.x1, view_rect.x2) + 4)
    start_y = int(min(view_rect.y1, view_rect.y2) + 3)
    end_x = start_x + 10
    end_y = start_y + 8

    preview.mousePressEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=start_x,
            y=start_y,
        )
    )
    preview.mouseMoveEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=end_x,
            y=end_y,
        )
    )
    preview.mouseReleaseEvent(
        _FakeMouseEvent(
            button=_FakeQt.LeftButton,
            x=end_x,
            y=end_y,
        )
    )

    assert len(selected) == 1
    assert errors == []
    expected_view_top = min(view_rect.y1, view_rect.y2) + 8.0
    expected_view_bottom = max(view_rect.y1, view_rect.y2)
    expected = workflow.selection_to_pdf_rect(
        selection=type(view_rect)(
            x1=min(view_rect.x1, view_rect.x2) + 10.0,
            y1=expected_view_top,
            x2=max(view_rect.x1, view_rect.x2),
            y2=expected_view_bottom,
        )
    ).normalized()
    normalized = selected[0].normalized()
    assert normalized.x1 == pytest.approx(expected.x1)
    assert normalized.y1 == pytest.approx(expected.y1)
    assert normalized.x2 == pytest.approx(expected.x2)
    assert normalized.y2 == pytest.approx(expected.y2)


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


def test_zoom_refresh_resizes_widget_with_rendered_page(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_ZoomSensitiveRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    widget = PdfViewerWidgetAdapter().create(workflow=workflow)

    widget.refresh()
    assert widget.minimum_size == (260, 320)
    assert widget.size == (260, 320)

    widget.attach_scroll_container(_FakeScrollArea())
    widget.wheelEvent(
        _FakeWheelEvent(delta_y=-120, modifiers=_FakeQt.ControlModifier)
    )

    assert widget.minimum_size == (140, 180)
    assert widget.size == (140, 180)


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
    assert workflow.pan_updates[-1] == (0.0, 0.0)


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
    assert workflow.pan_updates[-1] == (0.0, 0.0)


def test_plain_left_drag_emits_selection_with_widget_relative_coords(monkeypatch):
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
    assert selected[0].x1 == 110.0
    assert selected[0].y1 == 95.0
    assert selected[0].x2 == 130.0
    assert selected[0].y2 == 115.0
    assert workflow.pan_updates[-1] == (0.0, 0.0)


def test_plain_left_drag_with_real_workflow_remains_in_bounds_after_scroll(monkeypatch):
    monkeypatch.setattr(PdfViewerWidgetAdapter, "_load_bindings", lambda self: _fake_bindings())

    from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_OverlayRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    errors = []
    widget = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_selection=selected.append,
        on_error=errors.append,
    )
    widget.refresh()
    widget.horizontalScrollBar().setValue(18)
    widget.verticalScrollBar().setValue(24)
    preview = widget.widget

    preview.mousePressEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=30, y=60))
    preview.mouseMoveEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=60, y=80))
    preview.mouseReleaseEvent(_FakeMouseEvent(button=_FakeQt.LeftButton, x=60, y=80))

    assert errors == []
    assert len(selected) == 1
    normalized = selected[0].normalized()
    assert normalized.x1 == 30.0
    assert normalized.y1 == 20.0
    assert normalized.x2 == 60.0
    assert normalized.y2 == 40.0


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
