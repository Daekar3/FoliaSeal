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
