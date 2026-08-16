from __future__ import annotations

import os
from pathlib import Path

import pytest

from foliaseal.application.reusable_signing_objects import SaveAppearance, SavePlacement
from tests.support.signing_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
    build_placement_profile,
    build_signature_appearance,
)


def test_library_is_modeless_three_column_and_document_independent(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QLineEdit, QListWidget, QScrollArea, QSplitter

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
    assert isinstance(library.controls.detail_scroll_area, QScrollArea)
    assert library.controls.detail_scroll_area.widget() is library.controls.detail_view

    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()


def test_library_geometry_and_columns_persist_through_frame_store_reload(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QSplitter

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-persistence"])
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    common = {
        "app_settings_store": store,
        "certificate_catalog_store": CertificateCatalogStore(
            storage_dir=tmp_path / "certificates"
        ),
        "preset_catalog_store": SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    }
    initial = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "home"),
        default_open_directory=str(tmp_path / "home"),
        linux_packaging_channel="primary",
        ui={"future_preference": "keep"},
    )
    first_frame = QtAppFrameAdapter().create_frame(app_settings=initial, **common)
    first_library = first_frame.show_reusable_object_library()
    app.processEvents()
    try:
        first_library.controls.dialog.setGeometry(48, 64, 1120, 700)
        splitter = first_library.controls.splitter
        assert isinstance(splitter, QSplitter)
        splitter.setSizes([180, 300, 560])
        show_maximized = getattr(first_library.controls.dialog, "showMaximized", None)
        assert callable(show_maximized)
        show_maximized()
        app.processEvents()

        captured = first_frame.capture_window_geometry()
        first_frame.persist_captured_window_geometry()
        expected_geometry = captured.ui_settings.library_geometry
        expected_sizes = captured.ui_settings.library_splitter_sizes
        assert expected_geometry is not None
        assert expected_geometry.maximized is True
        assert expected_sizes == tuple(splitter.sizes())
    finally:
        first_library.controls.dialog.close()
        first_frame.window.close()
        app.processEvents()

    loaded = store.load_settings()
    assert loaded.ui["future_preference"] == "keep"
    assert loaded.ui_settings.library_geometry == expected_geometry
    assert loaded.ui_settings.library_splitter_sizes == expected_sizes

    second_frame = QtAppFrameAdapter().create_frame(app_settings=loaded, **common)
    assert second_frame._reusable_object_library is None  # noqa: SLF001
    second_library = second_frame.show_reusable_object_library()
    app.processEvents()
    try:
        assert second_library.controls.dialog.isVisible() is True
        assert second_library.controls.dialog.isMaximized() is True
        restored = second_library.capture_ui_settings(loaded)
        assert restored.ui_settings.library_geometry == expected_geometry
        restored_splitter = second_library.controls.splitter
        assert isinstance(restored_splitter, QSplitter)
        assert tuple(restored_splitter.sizes()) == expected_sizes
    finally:
        second_library.controls.dialog.close()
        second_frame.window.close()
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


def test_library_real_qt_nested_preset_attaches_created_blank_placement(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-preset-placement"])
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
    frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))
    created = build_placement_profile(display_name="Blank-page placement")

    def create_placement():
        frame._reusable_objects.execute(
            SavePlacement(
                name=created.display_name,
                rect=created.rect,
                source_page=created.source_page,
                page_number=created.page_number,
                pinned=created.pinned,
                placement_profile_id=created.placement_profile_id,
            )
        )
        return created

    frame._open_placement_profile_editor = create_placement
    library = frame.show_reusable_object_library()
    app.processEvents()
    try:
        library.controls.catalog_selector.setCurrentRow(list(LibraryCatalog).index(LibraryCatalog.PRESETS))
        library.controls.create_button.click()
        app.processEvents()

        editor = library.controls.preset_editor
        assert editor is not None
        editor.controls.name_input.setText("Preset with placement")
        editor.controls.appearance_selector.setCurrentText("Approval")
        editor.controls.create_placement_button.click()
        app.processEvents()

        assert editor.controls.placement_selector.currentText() == "Blank-page placement"
        editor.controls.save_button.click()
        app.processEvents()
        assert library.controls.preset_editor is None
        resolved = frame._reusable_objects.view().presets[0]
        assert resolved.display_name == "Preset with placement"
        saved = frame._reusable_objects.resolve(resolved.ref)
        assert saved.preset.placement_profile_id == created.placement_profile_id
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_library_real_qt_nested_preset_attaches_created_certificate(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-preset-certificate"])
    certificate_store = CertificateCatalogStore(storage_dir=tmp_path / "certificates")
    initial_catalog = build_certificate_catalog(
        managed_certificates=(build_managed_certificate(),),
        certificate_configurations=(),
    )
    certificate_store.save_catalog(initial_catalog)
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=certificate_store,
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))
    created = build_certificate_configuration(
        certificate_configuration_id="nested-certificate",
        display_name="Nested certificate",
        managed_certificate_id=initial_catalog.managed_certificates[0].managed_certificate_id,
    )

    def create_certificate():
        certificate_store.save_catalog(
            build_certificate_catalog(
                managed_certificates=initial_catalog.managed_certificates,
                certificate_configurations=(created,),
            )
        )
        return created

    frame._create_certificate_for_preset = create_certificate
    library = frame.show_reusable_object_library()
    app.processEvents()
    try:
        library.controls.catalog_selector.setCurrentRow(list(LibraryCatalog).index(LibraryCatalog.PRESETS))
        library.controls.create_button.click()
        app.processEvents()
        editor = library.controls.preset_editor
        assert editor is not None
        editor.controls.name_input.setText("Preset with certificate")
        editor.controls.appearance_selector.setCurrentText("Approval")
        editor.controls.create_certificate_button.click()
        app.processEvents()

        assert editor.controls.certificate_selector.currentText() == "Nested certificate"
        editor.controls.save_button.click()
        app.processEvents()
        assert library.controls.preset_editor is None
        resolved = frame._reusable_objects.view().presets[0]
        saved = frame._reusable_objects.resolve(resolved.ref)
        assert saved.preset.certificate_configuration_id == created.certificate_configuration_id
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_first_use_library_forces_presets_and_returns_saved_preset(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-first-use"])
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={"library_last_catalog": "appearances"},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    library = frame.show_first_use_preset_library()
    app.processEvents()

    assert library._session.catalog is LibraryCatalog.PRESETS  # noqa: SLF001
    library.controls.create_button.click()
    preset_editor = library.controls.preset_editor
    assert preset_editor is not None
    preset_editor.controls.name_input.setText("First-use preset")
    preset_editor.controls.create_appearance_button.click()
    appearance_editor = preset_editor.appearance_child
    assert appearance_editor is not None
    appearance_editor.controls.name_input.setText("First-use appearance")
    appearance_editor.controls.save_button.click()
    preset_editor.controls.save_button.click()
    app.processEvents()

    assert frame._reusable_objects.view().preset_names == ("First-use preset",)  # noqa: SLF001
    assert library.controls.preset_editor is None
    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()
