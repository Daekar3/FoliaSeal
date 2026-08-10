"""Display-independent integration coverage for the no-document landing frame."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_real_qt_no_document_frame_exposes_primary_actions(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QPushButton

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal"])

    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings.default(tmp_path / "home"),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    frame.window.show()
    app.processEvents()

    assert frame.current_workspace is None
    assert {button.text() for button in frame.window.findChildren(QPushButton)} >= {
        "Open a PDF…",
        "Manage Signature Library…",
    }

    library_button = next(
        button
        for button in frame.window.findChildren(QPushButton)
        if button.text() == "Manage Signature Library…"
    )
    library_button.click()
    app.processEvents()
    library_dialog = frame.reusable_object_library_dialog
    assert library_dialog is not None
    assert library_dialog.controls.dialog.isVisible()
    assert not library_dialog.controls.dialog.isModal()
    library_dialog.controls.dialog.close()

    frame.window.close()
    app.processEvents()
    if created_app:
        app.quit()
