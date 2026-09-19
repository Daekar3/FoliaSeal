import os
from pathlib import Path

import pytest


def test_import_certificate_dialog_minimum_layout_and_password_mode(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QLineEdit

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_certificate_management import (
        CertificateImportDialog,
    )

    app = QApplication.instance() or QApplication(["foliaseal-import-layout-test"])
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=tmp_path / "certificates"
        ),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    dialog = CertificateImportDialog(
        bindings=frame._bindings,  # noqa: SLF001 - exercise production Qt bindings
        parent=frame.window,
        certificate_manager=frame._certificate_manager,  # noqa: SLF001
    )
    try:
        frame.window.show()
        dialog.controls.dialog.show()
        dialog.controls.dialog.resize(600, 460)
        for _ in range(3):
            app.processEvents()

        window = dialog.controls.dialog
        cancel = dialog.controls.cancel_button
        import_button = dialog.controls.import_button
        assert (window.width(), window.height()) == (600, 460)
        assert cancel.isVisible() and import_button.isVisible()
        assert cancel.geometry().right() < import_button.geometry().left()
        assert import_button.geometry().right() <= window.rect().right()
        assert import_button.isDefault()
        assert dialog.controls.passphrase.echoMode() == QLineEdit.EchoMode.Password
    finally:
        dialog.controls.dialog.close()
        frame.window.close()
        app.processEvents()
