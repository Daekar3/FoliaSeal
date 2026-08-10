"""Offscreen proof for the adjustable, remembered signing-rail divider."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from foliaseal.application.document_source_monitor import DocumentSourceMonitor
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureAppearance
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.infra.render.base import PdfPageGeometry, RenderPageRequest, RenderPageResult
from foliaseal.presentation.qt import build_qt_signing_shell
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame, QtAppFrameAdapter
from tests.support.signing_builders import build_reusable_objects_fixture, write_test_pdf


class _StaticRenderBackend:
    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 612.0, 792.0),
            crop_box=(0.0, 0.0, 612.0, 792.0),
            rotation=0,
        )

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        return RenderPageResult(width_px=612, height_px=792, rgba_bytes=b"\xff" * (612 * 792 * 4))

    def diagnostics(self):
        return None


def _build_shell(source: Path, settings: AppSettings, store: AppSettingsStore):
    return build_qt_signing_shell(
        viewer_workflow=ViewerWorkflow(
            document_path=str(source),
            render_backend=_StaticRenderBackend(),
            session=ViewerSession(page_count=1),
        ),
        signing_workflow=SigningDraftWorkflow(
            input_pdf_path=str(source),
            output_pdf_path=str(source.with_name("signed.pdf")),
            certificate_path="",
            passphrase="",
            tsa_url="",
            timestamp_required=False,
            signature_appearance=SignatureAppearance(),
            document_source_monitor=DocumentSourceMonitor.for_path(source),
        ),
        reusable_objects=build_reusable_objects_fixture(),
        app_settings=settings,
        app_settings_store=store,
    )


def test_real_qt_signing_rail_divider_moves_and_round_trips(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QMainWindow, QScrollArea, QSplitter

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-rail-divider-test"])
    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    settings = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path),
        default_open_directory=str(tmp_path),
        linux_packaging_channel="primary",
        ui={"future_preference": 7},
    )
    first = _build_shell(source, settings, store)
    first_window = QMainWindow()
    first_window.setCentralWidget(first.container)
    first_window.resize(1200, 700)
    first_window.show()
    app.processEvents()

    try:
        first_splitter = first.container.findChild(QSplitter)
        assert first_splitter is not None
        assert len(first_splitter.sizes()) == 2
        assert first.sidebar.width() == 320
        assert isinstance(first.viewer_widget, QScrollArea)
        assert isinstance(first.properties_scroll, QScrollArea)

        initial_width = first.sidebar.width()
        first_splitter.setSizes([500, 400])
        app.processEvents()
        moved_width = first.sidebar.width()
        assert moved_width > initial_width
        captured = first.capture_ui_settings(settings)
        assert captured.ui_settings.rail_width == moved_width
        assert captured.ui["future_preference"] == 7
        store.save_settings(captured)
        reloaded = store.load_settings()
        assert reloaded.ui_settings.rail_width == moved_width
        assert reloaded.ui["future_preference"] == 7

        second = _build_shell(source, reloaded, store)
        second_window = QMainWindow()
        second_window.setCentralWidget(second.container)
        second_window.resize(1200, 700)
        second_window.show()
        app.processEvents()
        try:
            second_splitter = second.container.findChild(QSplitter)
            assert second_splitter is not None
            assert second.sidebar.width() == moved_width
            assert isinstance(second.viewer_widget, QScrollArea)
            assert isinstance(second.properties_scroll, QScrollArea)
        finally:
            second_window.close()
            second.close()
            app.processEvents()
    finally:
        first_window.close()
        first.close()
        app.processEvents()
        if created_app:
            app.quit()


def test_real_qt_app_frame_captures_and_persists_workspace_divider(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication, QScrollArea, QSplitter

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-frame-rail-divider-test"])
    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    adapter = QtAppFrameAdapter()
    frame = FoliaSealAppFrame(
        bindings=adapter._bindings,  # noqa: SLF001 - real adapter bindings in this integration test
        app_settings=AppSettings.default(home_directory=tmp_path),
        app_settings_store=store,
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        render_backend_factory=_StaticRenderBackend,
    )
    frame.window.resize(1200, 700)
    frame.window.show()
    app.processEvents()

    try:
        assert frame.open_pdf_path(source) is not None
        app.processEvents()
        workspace = frame.current_workspace
        assert workspace is not None
        shell = workspace.view.mount_target()
        splitter = shell.findChild(QSplitter)
        assert splitter is not None
        assert splitter.widget(0).findChild(QScrollArea) is not None

        splitter.setSizes([500, 400])
        app.processEvents()
        moved_width = splitter.widget(1).width()
        assert moved_width > 320
        frame.capture_window_geometry()
        frame.persist_captured_window_geometry()
        reloaded = store.load_settings()
        assert reloaded.ui_settings.rail_width == moved_width
    finally:
        frame._workspace_host.close()  # noqa: SLF001 - bypass discard prompt during test teardown
        frame.window.close()
        app.processEvents()
        if created_app:
            app.quit()
