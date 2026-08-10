"""Real offscreen Qt proof for Pan-only link click gesture separation."""

from __future__ import annotations

import os

import pytest

from foliaseal.application.coordinate_transform import ViewTransform, view_point_to_pdf
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.infra.render import PdfPageGeometry, RenderPageResult
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget


class _RenderBackend:
    def render_page(self, request) -> RenderPageResult:
        return RenderPageResult(
            width_px=160,
            height_px=160,
            rgba_bytes=b"\xff" * (160 * 160 * 4),
        )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 160.0, 160.0),
            crop_box=(0.0, 0.0, 160.0, 160.0),
            rotation=0,
        )

    def diagnostics(self):  # pragma: no cover - not used by the widget
        raise NotImplementedError


def test_real_offscreen_pan_click_drag_and_other_modes(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(["foliaseal-safe-links-pan-test"])
    workflow = ViewerWorkflow(
        document_path="/tmp/safe-links.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    callbacks: list[tuple[float, float]] = []
    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_link_click=lambda pdf_x, pdf_y: callbacks.append((pdf_x, pdf_y)),
    )
    viewer.show()
    viewer.refresh()
    app.processEvents()

    viewer.set_interaction_mode("pan")
    snapshot = workflow.snapshot
    assert snapshot is not None
    expected_point = view_point_to_pdf(
        view_x=25.0,
        view_y=25.0,
        transform=ViewTransform(
            zoom=snapshot.zoom,
            pan_x=snapshot.pan_x,
            pan_y=snapshot.pan_y,
        ),
        page_box=snapshot.page_box,
        rotation=snapshot.rotation,
    )
    QTest.mouseClick(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(25, 25))
    assert callbacks == [pytest.approx(expected_point)]

    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(25, 25))
    QTest.mouseMove(viewer.widget(), QPoint(40, 25), delay=1)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(40, 25))
    assert callbacks == [pytest.approx(expected_point)]

    viewer.set_interaction_mode("text")
    QTest.mouseClick(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(25, 25))
    viewer.set_interaction_mode("signature")
    QTest.mouseClick(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(25, 25))
    assert callbacks == [pytest.approx(expected_point)]

    viewer.close()
    app.processEvents()
