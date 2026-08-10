"""Offscreen proof that Page Up/Down navigation is handled exactly once."""

from __future__ import annotations

import os

import pytest

from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.infra.render import PdfPageGeometry, RenderPageResult
from foliaseal.presentation.qt.viewer_widget import PdfViewerWidgetAdapter


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
