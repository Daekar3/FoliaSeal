"""Offscreen proof that Page Up/Down navigation is handled exactly once."""

from __future__ import annotations

import os

import pytest

from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect
from foliaseal.infra.render import PdfPageGeometry, RenderPageResult
from foliaseal.presentation.qt.viewer_widget import (
    PdfViewerWidgetAdapter,
    build_qt_pdf_viewer_widget,
)


class _RenderBackend:
    def __init__(self) -> None:
        self.render_calls = 0

    def render_page(self, request) -> RenderPageResult:
        del request
        self.render_calls += 1
        return RenderPageResult(width_px=2, height_px=2, rgba_bytes=b"\x00" * 16)

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        del document_path, page_index
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 72.0, 72.0),
            crop_box=(0.0, 0.0, 72.0, 72.0),
            rotation=0,
        )

    def diagnostics(self):
        return None


def test_page_shortcut_navigates_once_with_viewer_focus() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-view-shortcut-test"])

    backend = _RenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/shortcut-test.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=3),
    )
    viewer = PdfViewerWidgetAdapter().create(workflow=workflow)
    window = QMainWindow()
    window.setCentralWidget(viewer)

    next_action = QAction("Next Page", window)
    next_action.setShortcut("Page Down")
    next_action.triggered.connect(
        lambda: (workflow.session.go_next(), viewer.refresh(navigation=True))
    )
    previous_action = QAction("Previous Page", window)
    previous_action.setShortcut("Page Up")
    previous_action.triggered.connect(
        lambda: (workflow.session.go_previous(), viewer.refresh(navigation=True))
    )
    window.addAction(next_action)
    window.addAction(previous_action)
    window.show()
    viewer.setFocus()
    app.processEvents()

    try:
        QTest.keyClick(viewer, Qt.Key_PageDown)
        app.processEvents()
        assert workflow.session.current_page == 1
        assert backend.render_calls == 1

        QTest.keyClick(viewer, Qt.Key_PageUp)
        app.processEvents()
        assert workflow.session.current_page == 0
        assert backend.render_calls == 2
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()


def test_fit_shortcuts_dispatch_once_and_initial_view_fits_page() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-fit-shortcut-test"])

    backend = _RenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/fit-shortcut-test.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=2),
    )
    viewer = build_qt_pdf_viewer_widget(workflow=workflow)
    window = QMainWindow()
    window.resize(640, 480)
    window.setCentralWidget(viewer)
    fit_page_action = QAction("Fit Page", window)
    fit_page_action.setShortcut("Ctrl+0")
    fit_page_action.triggered.connect(viewer.fit_page_view)
    fit_width_action = QAction("Fit Width", window)
    fit_width_action.setShortcut("Ctrl+Shift+0")
    fit_width_action.triggered.connect(viewer.fit_width_view)
    window.addAction(fit_page_action)
    window.addAction(fit_width_action)
    viewer.refresh()
    window.show()
    viewer.setFocus()
    app.processEvents()

    try:
        assert workflow.session.zoom_mode == "fit_page"
        assert workflow.session.zoom == 8.0
        initial_render_calls = backend.render_calls

        QTest.keyClick(viewer.widget(), Qt.Key_0, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        assert backend.render_calls == initial_render_calls + 1
        assert workflow.session.current_page == 0

        after_page_fit = backend.render_calls
        QTest.keyClick(
            viewer.widget(),
            Qt.Key_0,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        app.processEvents()
        assert backend.render_calls == after_page_fit + 1
        assert workflow.session.current_page == 0
        assert workflow.session.zoom_mode == "fit_width"
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()


def test_find_shortcut_focuses_and_selects_the_search_query() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QAction
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLineEdit, QMainWindow

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-find-shortcut-test"])

    query_input = QLineEdit()
    query_input.setText("Alice")
    window = QMainWindow()
    window.setCentralWidget(query_input)
    find_action = QAction("Find", window)
    find_action.setShortcut("Ctrl+F")
    find_action.triggered.connect(
        lambda: (query_input.setFocus(), query_input.selectAll())
    )
    window.addAction(find_action)
    window.show()
    query_input.setFocus()
    app.processEvents()

    try:
        QTest.keyClick(query_input, Qt.Key_F, Qt.KeyboardModifier.ControlModifier)
        app.processEvents()
        assert query_input.hasFocus()
        assert query_input.selectedText() == "Alice"
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()


def test_pointer_drag_creates_one_page_local_signature_rectangle_and_escape_cancels() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-pointer-placement-test"])

    backend = _RenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/pointer-placement-test.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=1),
    )
    selected = []
    viewer = build_qt_pdf_viewer_widget(workflow=workflow, on_selection=selected.append)
    window = QMainWindow()
    window.resize(240, 240)
    window.setCentralWidget(viewer)
    viewer.refresh()
    window.show()
    viewer.widget().setFocus()
    app.processEvents()

    try:
        QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
        QTest.mouseMove(viewer.widget(), pos=QPoint(100, 100))
        QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        app.processEvents()

        assert len(selected) == 1
        rect = selected[0].normalized()
        assert rect.x1 >= 0.0
        assert rect.y1 >= 0.0
        assert rect.x2 <= 72.0
        assert rect.y2 <= 72.0

        QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(30, 30))
        QTest.mouseMove(viewer.widget(), pos=QPoint(40, 40))
        QTest.keyClick(viewer.widget(), Qt.Key_Escape)
        QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(40, 40))
        app.processEvents()
        assert len(selected) == 1
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()


def test_pan_and_place_tools_are_explicit_and_mutually_exclusive() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-pan-place-mode-test"])

    workflow = ViewerWorkflow(
        document_path="/tmp/pan-place-mode-test.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    selected = []
    viewer = build_qt_pdf_viewer_widget(workflow=workflow, on_selection=selected.append)
    window = QMainWindow()
    window.resize(240, 240)
    window.setCentralWidget(viewer)
    viewer.refresh()
    window.show()
    viewer.widget().setFocus()
    app.processEvents()

    try:
        viewer.set_interaction_mode("pan")
        QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
        QTest.mouseMove(viewer.widget(), pos=QPoint(100, 100))
        QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        assert selected == []

        viewer.set_interaction_mode("signature")
        QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
        QTest.mouseMove(viewer.widget(), pos=QPoint(100, 100))
        QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        assert len(selected) == 1
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()


def test_keyboard_place_enter_and_shift_arrow_update_the_overlay() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMainWindow

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-keyboard-placement-test"])

    workflow = ViewerWorkflow(
        document_path="/tmp/keyboard-placement-test.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    current: list[SignatureRect | None] = [None]

    def create() -> SignatureRect:
        current[0] = SignatureRect(
            page_index=0,
            left_pt=0.0,
            bottom_pt=24.0,
            width_pt=72.0,
            height_pt=24.0,
        )
        return current[0]

    def move(delta_x: float, delta_y: float) -> SignatureRect:
        rect = current[0]
        assert rect is not None
        current[0] = SignatureRect(
            page_index=rect.page_index,
            left_pt=rect.left_pt + delta_x,
            bottom_pt=rect.bottom_pt + delta_y,
            width_pt=rect.width_pt,
            height_pt=rect.height_pt,
        )
        return current[0]

    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_keyboard_create=create,
        on_keyboard_move=move,
    )
    window = QMainWindow()
    window.resize(240, 240)
    window.setCentralWidget(viewer)
    viewer.refresh()
    viewer.set_interaction_mode("signature")
    window.show()
    viewer.widget().setFocus()
    app.processEvents()

    try:
        QTest.keyClick(viewer.widget(), Qt.Key_Return)
        app.processEvents()
        assert current[0] is not None
        assert viewer.widget()._overlay_signature_rect == current[0]

        QTest.keyClick(viewer.widget(), Qt.Key_Right, Qt.KeyboardModifier.ShiftModifier)
        app.processEvents()
        assert current[0] is not None
        assert current[0].left_pt == 10.0
        assert viewer.widget()._overlay_signature_rect == current[0]
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()
