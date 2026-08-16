"""Real offscreen proof for the typed AppFrame View → Pan command."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.infra.render.base import PdfPageGeometry, RenderPageRequest, RenderPageResult
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame, QtAppFrameAdapter
from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId
from tests.support.signing_builders import write_test_pdf


class _StaticRenderBackend:
    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        del document_path, page_index
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 612.0, 792.0),
            crop_box=(0.0, 0.0, 612.0, 792.0),
            rotation=0,
        )

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        del request
        return RenderPageResult(width_px=612, height_px=792, rgba_bytes=b"\xff" * (612 * 792 * 4))

    def diagnostics(self):
        return None


def test_real_qt_app_frame_pan_action_preserves_placement_and_exits_text_mode(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-pan-command-test"])

    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    adapter = QtAppFrameAdapter()
    frame = FoliaSealAppFrame(
        bindings=adapter._bindings,  # noqa: SLF001 - real adapter bindings for integration evidence
        app_settings=AppSettings.default(home_directory=tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        render_backend_factory=_StaticRenderBackend,
    )
    frame.window.show()
    app.processEvents()

    try:
        assert frame.open_pdf_path(source) is not None
        app.processEvents()
        workspace = frame.current_workspace
        assert workspace is not None
        original = workspace.session.set_signature_rect(
            page_index=0,
            left_pt=40.0,
            bottom_pt=60.0,
            width_pt=180.0,
            height_pt=90.0,
        )
        assert workspace.maintenance.set_document_text_selection_mode(True) is True
        pan_action = frame.command_actions()[AppFrameCommandId.PAN]
        assert pan_action.isEnabled()

        pan_action.trigger()
        app.processEvents()

        assert workspace.maintenance.document_text_selection_mode_enabled() is False
        workflow = frame.current_signing_workflow
        assert workflow is not None
        assert workflow.signature_rect == original
    finally:
        frame._workspace_host.close()  # noqa: SLF001 - bypass discard prompt during test teardown
        frame.window.close()
        app.processEvents()
        if created_app:
            app.quit()
