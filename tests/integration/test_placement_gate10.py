"""Composed Qt coverage for Gate 10 placement mode and cancellation behavior."""

from __future__ import annotations

import os

import pytest

from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect
from foliaseal.infra.render import PdfPageGeometry, RenderPageResult
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget


def _write_blank_pdf(path) -> None:
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 160 160] "
            b"/Resources << >> /Contents 4 0 R >>"
        ),
        4: b"<< /Length 0 >>\nstream\nendstream",
    }
    payload = b"%PDF-1.4\n"
    offsets = [0]
    for number in range(1, 5):
        offsets.append(len(payload))
        payload += f"{number} 0 obj\n".encode() + objects[number] + b"\nendobj\n"
    xref_offset = len(payload)
    payload += b"xref\n0 5\n0000000000 65535 f \n"
    payload += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    payload += (
        f"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    path.write_bytes(payload)


class _RenderBackend:
    def __init__(self) -> None:
        self.render_calls = 0

    def render_page(self, request) -> RenderPageResult:
        self.render_calls += 1
        return RenderPageResult(
            width_px=160,
            height_px=160,
            rgba_bytes=b"\xff" * (160 * 160 * 4),
        )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        del document_path, page_index
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 160.0, 160.0),
            crop_box=(0.0, 0.0, 160.0, 160.0),
            rotation=0,
        )

    def diagnostics(self):  # pragma: no cover - not used by the widget
        raise NotImplementedError


def test_real_offscreen_adjust_focus_keyboard_and_escape_cancel(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(["foliaseal-placement-gate10-test"])
    workflow = ViewerWorkflow(
        document_path="/tmp/placement-gate10.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    original = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    moved = SignatureRect(
        page_index=0,
        left_pt=21.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    selected: list[object] = []
    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_selection=selected.append,
        on_keyboard_move=lambda _dx, _dy: moved,
    )
    viewer.show()
    viewer.refresh()
    viewer.set_signature_overlay(original)
    viewer.set_interaction_mode("signature")
    viewer.focus_viewer()
    app.processEvents()

    assert QApplication.focusWidget() is viewer.widget()
    QTest.keyClick(viewer.widget(), Qt.Key_Right)
    assert viewer.widget()._overlay_signature_rect == moved

    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(8, 8))
    QTest.mouseMove(viewer.widget(), QPoint(45, 45), delay=1)
    QTest.keyClick(viewer.widget(), Qt.Key_Escape)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(45, 45))
    assert selected == []
    assert viewer.widget()._drag_origin is None
    assert viewer.widget()._selection_rect is None

    QTest.keyClick(viewer.widget(), Qt.Key_Escape)
    assert viewer.interaction_mode() == "pan"
    assert viewer.widget()._overlay_signature_rect == moved

    viewer.close()
    app.processEvents()


@pytest.mark.parametrize("gesture", ["click", "drag", "conversion-error"])
def test_real_offscreen_new_placement_releases_mouse_grab(monkeypatch, gesture: str) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QWidget

    app = QApplication.instance() or QApplication(["foliaseal-placement-grab-test"])
    workflow = ViewerWorkflow(
        document_path="/tmp/placement-grab.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    errors: list[str] = []
    if gesture == "conversion-error":
        def reject_selection(*, selection):
            del selection
            raise ValueError("bad selection")

        monkeypatch.setattr(workflow, "selection_to_pdf_rect", reject_selection)
    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_error=errors.append,
    )
    viewer.show()
    viewer.refresh()
    viewer.set_interaction_mode("signature")
    app.processEvents()

    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(12, 12))
    if gesture != "click":
        QTest.mouseMove(viewer.widget(), QPoint(48, 48), delay=1)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(48, 48))
    app.processEvents()

    assert QWidget.mouseGrabber() is None
    if gesture == "conversion-error":
        assert errors == [
            "Selection could not be placed on the PDF page. Please keep the selection "
            "inside page bounds. (details: bad selection)"
        ]
    else:
        assert errors == []
    viewer.close()
    app.processEvents()


def test_real_offscreen_existing_handle_escape_preserves_geometry_and_releases_grab(
    monkeypatch,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QWidget

    app = QApplication.instance() or QApplication(["foliaseal-placement-handle-cancel-test"])
    workflow = ViewerWorkflow(
        document_path="/tmp/placement-handle-cancel.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    original = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    viewer = build_qt_pdf_viewer_widget(workflow=workflow)
    viewer.show()
    viewer.refresh()
    viewer.widget().record_signature_edit(original)
    viewer.set_signature_overlay(original)
    viewer.set_interaction_mode("signature")
    app.processEvents()

    overlay = viewer.widget()._current_overlay_view_rect()
    assert overlay is not None
    handle_x, handle_y = viewer.widget()._overlay_handle_targets(overlay)["bottom_right"]
    start = QPoint(int(handle_x), int(handle_y))
    end = QPoint(int(handle_x + 12), int(handle_y + 8))
    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(viewer.widget(), end, delay=1)
    QTest.keyClick(viewer.widget(), Qt.Key_Escape)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=end)
    app.processEvents()

    assert viewer.widget()._overlay_signature_rect == original
    assert viewer.widget()._overlay_drag_handle is None
    assert QWidget.mouseGrabber() is None
    assert viewer.widget().can_undo_signature_placement() is True

    viewer.close()
    app.processEvents()


def test_real_offscreen_pan_escape_clears_active_drag_without_late_link_or_commit(
    monkeypatch,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QWidget

    app = QApplication.instance() or QApplication(["foliaseal-pan-cancel-test"])
    workflow = ViewerWorkflow(
        document_path="/tmp/foliaseal-pan-cancel.pdf",
        render_backend=_RenderBackend(),
        session=ViewerSession(page_count=1),
    )
    link_clicks: list[tuple[float, float]] = []
    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_link_click=lambda x, y: link_clicks.append((x, y)),
    )
    viewer.show()
    viewer.refresh()
    viewer.set_interaction_mode("pan")
    app.processEvents()

    start = QPoint(20, 20)
    end = QPoint(48, 48)
    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(viewer.widget(), end, delay=1)
    QTest.keyClick(viewer.widget(), Qt.Key_Escape)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=end)
    app.processEvents()

    assert viewer.widget()._pan_origin is None
    assert viewer.widget()._pan_click_candidate is False
    assert QWidget.mouseGrabber() is None
    assert link_clicks == []

    viewer.close()
    app.processEvents()


def test_real_offscreen_app_frame_adjust_projects_mode_and_focus(tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

    from foliaseal.domain.models import SignatureRect
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId

    app = QApplication.instance() or QApplication(["foliaseal-placement-composition-test"])
    source = tmp_path / "placement-composition.pdf"
    _write_blank_pdf(source)
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    frame.window.show()
    assert frame.open_pdf_path(source) is not None
    app.processEvents()
    workspace = frame.current_workspace
    shell = frame.current_shell
    assert workspace is not None
    assert shell is not None
    placement = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    workspace.testing.apply_signature_rect_placement(placement)
    app.processEvents()
    viewer = next(
        child
        for child in shell.findChildren(QWidget)
        if callable(getattr(child, "interaction_mode", None))
    )
    labels = shell.findChildren(QLabel)
    buttons = shell.findChildren(QPushButton)
    adjust = frame.command_actions()[AppFrameCommandId.ADJUST_PLACEMENT]
    adjust.trigger()
    app.processEvents()

    assert viewer.interaction_mode() == "signature"
    assert QApplication.focusWidget() is viewer.widget()
    assert next(button for button in buttons if button.text() == "Place").isChecked() is True
    assert any("Place mode" in label.text() for label in labels)

    QTest.keyClick(viewer.widget(), Qt.Key_Escape)
    app.processEvents()
    assert viewer.interaction_mode() == "pan"
    assert next(button for button in buttons if button.text() == "Pan").isChecked() is True
    assert any("Pan mode" in label.text() for label in labels)
    assert viewer.widget()._overlay_signature_rect == placement

    frame._workspace_host.close()
    frame.window.close()
    app.processEvents()


def test_real_offscreen_app_frame_pointer_history_and_remove_routes(tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId

    app = QApplication.instance() or QApplication(["foliaseal-placement-history-composition-test"])
    source = tmp_path / "placement-history-composition.pdf"
    _write_blank_pdf(source)
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    frame.window.show()
    assert frame.open_pdf_path(source) is not None
    app.processEvents()
    shell = frame.current_shell
    workspace = frame.current_workspace
    assert shell is not None
    assert workspace is not None
    viewer = workspace.view.shell._viewer_widget
    placement = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    workspace.session.set_signature_rect(
        page_index=placement.page_index,
        left_pt=placement.left_pt,
        bottom_pt=placement.bottom_pt,
        width_pt=placement.width_pt,
        height_pt=placement.height_pt,
    )
    viewer.set_interaction_mode("signature")
    viewer.focus_viewer()
    app.processEvents()
    overlay = viewer.widget()._current_overlay_view_rect()
    assert overlay is not None
    handle_x, handle_y = viewer.widget()._overlay_handle_targets(overlay)["bottom_right"]
    start = QPoint(int(handle_x), int(handle_y))
    end = QPoint(int(handle_x + 12), int(handle_y + 8))
    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(viewer.widget(), end, delay=1)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=end)
    app.processEvents()
    created = workspace.signing_workflow.signature_rect
    assert created is not None
    assert workspace.session.can_undo_placement() is True

    actions = frame.command_actions()
    actions[AppFrameCommandId.UNDO].trigger()
    app.processEvents()
    assert workspace.signing_workflow.signature_rect is None
    assert viewer.widget()._overlay_signature_rect is None
    actions[AppFrameCommandId.REDO].trigger()
    app.processEvents()
    assert workspace.signing_workflow.signature_rect == created
    assert viewer.widget()._overlay_signature_rect == created

    actions[AppFrameCommandId.REMOVE_PLACEMENT].trigger()
    app.processEvents()
    assert workspace.signing_workflow.signature_rect is None
    actions[AppFrameCommandId.UNDO].trigger()
    app.processEvents()
    assert workspace.signing_workflow.signature_rect == created

    viewer.focus_viewer()
    QTest.keyClick(viewer.widget(), Qt.Key_Delete)
    app.processEvents()
    assert workspace.signing_workflow.signature_rect is None
    actions[AppFrameCommandId.UNDO].trigger()
    app.processEvents()
    assert workspace.signing_workflow.signature_rect == created

    frame._workspace_host.close()
    frame.window.close()
    app.processEvents()


def test_real_offscreen_overlay_projection_keeps_pointer_edit_undo_branch(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(["foliaseal-placement-history-test"])
    backend = _RenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/placement-gate10-history.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=1),
    )
    original = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=40.0,
        height_pt=20.0,
    )
    edited = SignatureRect(
        page_index=0,
        left_pt=20.0,
        bottom_pt=30.0,
        width_pt=48.0,
        height_pt=24.0,
    )
    selected: list[object] = []

    def accept_pointer_edit(_pdf_rect: object) -> None:
        selected.append(_pdf_rect)
        viewer.widget().record_signature_edit(edited)

    viewer = build_qt_pdf_viewer_widget(
        workflow=workflow,
        on_selection=accept_pointer_edit,
    )
    viewer.show()
    viewer.refresh()
    render_calls_after_initial_refresh = backend.render_calls
    viewer.widget().record_signature_edit(original)
    viewer.set_signature_overlay(original)
    viewer.set_interaction_mode("signature")
    app.processEvents()

    QTest.mousePress(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(20, 30))
    QTest.mouseMove(viewer.widget(), QPoint(28, 36), delay=1)
    QTest.mouseRelease(viewer.widget(), Qt.MouseButton.LeftButton, pos=QPoint(28, 36))

    assert selected
    assert backend.render_calls == render_calls_after_initial_refresh
    assert viewer.widget().can_undo_signature_placement() is True
    assert viewer.widget().undo_signature_placement() == original
    assert viewer.widget().can_redo_signature_placement() is True
    assert viewer.widget().redo_signature_placement() == edited

    viewer.close()
    app.processEvents()
