from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_library_is_modeless_three_column_and_document_independent(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QLineEdit, QListWidget, QSplitter

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-topology"])
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    frame.window.show()
    library = frame.show_reusable_object_library()
    app.processEvents()

    assert library.controls.dialog.isModal() is False
    assert library.controls.dialog.isVisible() is True
    assert isinstance(library.controls.catalog_selector, QListWidget)
    assert library.controls.catalog_selector.count() == 4
    assert library.controls.catalog_selector.currentItem().text() == "Presets"
    assert isinstance(library.controls.object_selector, QListWidget)
    assert isinstance(library.controls.search_input, QLineEdit)
    assert len(library.controls.dialog.findChildren(QSplitter)) == 1

    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()


def test_library_real_qt_mounts_nested_appearance_editor(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-appearance-editor"])
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    library = frame.show_reusable_object_library()
    app.processEvents()

    library.controls.catalog_selector.setCurrentRow(list(LibraryCatalog).index(LibraryCatalog.APPEARANCES))
    app.processEvents()
    library.controls.create_button.click()
    app.processEvents()

    editor = library.controls.appearance_editor
    assert editor is not None
    assert editor.controls.breadcrumb_label.text().endswith("New appearance")
    assert "Sample preview (synthetic data" in editor.controls.sample_preview_label.text()

    editor.controls.name_input.setText("Offscreen appearance")
    editor.controls.save_button.click()
    app.processEvents()

    assert library.controls.appearance_editor is None
    assert "Offscreen appearance" in frame._reusable_objects.view().appearance_names  # noqa: SLF001
    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()


def test_library_real_qt_returns_from_appearance_child_to_preset_editor(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-preset-child"])
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    library = frame.show_reusable_object_library()
    app.processEvents()

    library.controls.catalog_selector.setCurrentRow(list(LibraryCatalog).index(LibraryCatalog.PRESETS))
    library.controls.create_button.click()
    app.processEvents()
    preset_editor = library.controls.preset_editor
    assert preset_editor is not None
    preset_editor.controls.name_input.setText("Offscreen preset")
    preset_editor.controls.create_appearance_button.click()
    app.processEvents()
    appearance_editor = preset_editor.appearance_child
    assert appearance_editor is not None
    assert "Appearance / New appearance" in appearance_editor.controls.breadcrumb_label.text()
    appearance_editor.controls.name_input.setText("Offscreen appearance")
    appearance_editor.controls.save_button.click()
    app.processEvents()

    assert preset_editor.appearance_child is None
    assert preset_editor.controls.appearance_selector.currentText() == "Offscreen appearance"
    preset_editor.controls.save_button.click()
    app.processEvents()

    assert library.controls.preset_editor is None
    assert frame._reusable_objects.view().preset_names == ("Offscreen preset",)  # noqa: SLF001
    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()
