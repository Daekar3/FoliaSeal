from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from foliaseal.application.reusable_signing_objects import (
    ReusableObjectMutationRejected,
    SaveAppearance,
    SavePlacement,
)
from foliaseal.domain.models import SignatureRect
from foliaseal.infra.render.base import PdfPageGeometry, RenderPageRequest, RenderPageResult
from tests.support.signing_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
    build_placement_profile,
    build_signature_appearance,
    write_test_pdf,
)


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


def test_library_is_modeless_compact_header_and_document_independent(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QScrollArea, QSplitter

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
    assert isinstance(library.controls.catalog_selector, QComboBox)
    assert library.controls.catalog_selector.count() == 4
    assert library.controls.catalog_selector.currentText() == "Presets"
    assert isinstance(library.controls.object_selector, QComboBox)
    assert isinstance(library.controls.search_input, QLineEdit)
    assert library.controls.splitter is None
    assert len(library.controls.dialog.findChildren(QSplitter)) == 0
    assert isinstance(library.controls.detail_scroll_area, QScrollArea)
    assert library.controls.detail_scroll_area.widget() is library.controls.detail_view

    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()


def test_library_uses_compact_selectors_without_active_splitter(tmp_path: Path) -> None:
    """The Library header owns selection; the editor owns the window's space."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QSplitter

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-compact-header"])
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
    try:
        assert isinstance(library.controls.catalog_selector, QComboBox)
        assert isinstance(library.controls.object_selector, QComboBox)
        assert library.controls.object_selector.isEditable() is True
        assert library.controls.search_input is library.controls.object_selector.lineEdit()
        assert library.controls.splitter is None
        assert library.controls.dialog.findChildren(QSplitter) == []

        footer = library.controls.library_footer_host
        assert footer.isVisible() is True
        assert footer.width() >= library.controls.dialog.width() * 0.9
        assert library.controls.detail_container.width() > library.controls.dialog.width() * 0.6
        assert isinstance(library.controls.search_input, QLineEdit)
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_library_header_labels_stay_with_their_selectors_at_supported_size(
    tmp_path: Path,
) -> None:
    """Header labels must read as captions for the controls beside them."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QLabel

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-header-labels"])
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
    library.controls.dialog.resize(1000, 650)
    app.processEvents()
    try:
        labels = {
            label.text(): label
            for label in library.controls.dialog.findChildren(QLabel)
            if label.text() in {"Catalog", "Saved object"}
        }
        assert set(labels) == {"Catalog", "Saved object"}

        def rect_in_dialog(widget):
            origin = widget.mapTo(library.controls.dialog, widget.rect().topLeft())
            return widget.rect().translated(origin)

        for caption, control in (
            ("Catalog", library.controls.catalog_selector),
            ("Saved object", library.controls.object_selector),
        ):
            caption_rect = rect_in_dialog(labels[caption])
            control_rect = rect_in_dialog(control)
            gap = control_rect.left() - caption_rect.right()
            assert 0 <= gap <= 12
            assert abs(caption_rect.center().y() - control_rect.center().y()) <= 12
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_library_legacy_splitter_setting_is_readable_but_inert(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QSplitter

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-inert-splitter"])
    stale_sizes = [123, 234, 345]
    settings = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "home"),
        default_open_directory=str(tmp_path / "home"),
        linux_packaging_channel="primary",
        ui={"library_splitter_sizes": stale_sizes},
    )
    frame = QtAppFrameAdapter().create_frame(
        app_settings=settings,
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    library = frame.show_reusable_object_library()
    app.processEvents()
    try:
        assert library.controls.splitter is None
        assert library.controls.dialog.findChildren(QSplitter) == []
        captured = library.capture_ui_settings(settings)
        assert captured.ui["library_splitter_sizes"] == stale_sizes
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_saved_object_selector_keeps_query_separate_from_activation(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-search-selector"])
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
    frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))  # noqa: SLF001
    frame._reusable_objects.execute(SaveAppearance("Board", build_signature_appearance()))  # noqa: SLF001
    library = frame.show_reusable_object_library(initial_catalog="appearances")
    app.processEvents()
    try:
        selected = library._session.selected_ref  # noqa: SLF001 - state contract under test
        assert selected is not None
        query = library.controls.search_input
        query.setFocus()
        query.clear()
        QTest.keyClicks(query, "board")
        app.processEvents()

        assert library._session.selected_ref == selected  # noqa: SLF001
        assert library._session.search == "board"  # noqa: SLF001
        QTest.keyClick(query, Qt.Key.Key_Escape)
        app.processEvents()
        assert library.controls.object_selector.currentText() == "Approval"
        assert library._session.selected_ref == selected  # noqa: SLF001
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_saved_object_query_restores_label_on_focus_loss_without_dirty_transition(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-query-focus"])
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
    frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))  # noqa: SLF001
    frame._reusable_objects.execute(SaveAppearance("Board", build_signature_appearance()))  # noqa: SLF001
    library = frame.show_reusable_object_library(initial_catalog="appearances")
    app.processEvents()
    try:
        selected = library._session.selected_ref  # noqa: SLF001
        assert selected is not None
        query = library.controls.search_input
        query.setText("board")
        app.processEvents()
        assert library._session.search == "board"  # noqa: SLF001

        library.controls.sort_selector.setFocus()
        app.processEvents()

        assert library._session.search == ""  # noqa: SLF001
        assert library.controls.object_selector.currentText() == "Approval"
        assert library._session.selected_ref == selected  # noqa: SLF001
        assert library._session.detail_dirty is False  # noqa: SLF001
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_saved_object_completer_enter_activates_exactly_once_after_navigation(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-completer-activation"])
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
    frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))  # noqa: SLF001
    frame._reusable_objects.execute(SaveAppearance("Board", build_signature_appearance()))  # noqa: SLF001
    library = frame.show_reusable_object_library(initial_catalog="appearances")
    app.processEvents()
    try:
        query = library.controls.search_input
        popup = library._object_completer.popup()  # noqa: SLF001
        activation_count = 0

        def observe_activation(_index: object) -> None:
            nonlocal activation_count
            activation_count += 1

        popup.activated.connect(observe_activation)
        query.setFocus()
        QTest.keyClicks(query, "board")
        app.processEvents()
        QTest.keyClick(query, Qt.Key.Key_Down)
        popup.setFocus()
        QTest.keyClick(popup, Qt.Key.Key_Return)
        app.processEvents()

        assert activation_count == 1
        assert library._session.selected_row().display_name == "Board"  # noqa: SLF001
        assert library._session.search == ""  # noqa: SLF001
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_library_controls_expose_accessible_names_and_catalog_action_visibility(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-library-accessibility"])
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
    library = frame.show_reusable_object_library(initial_catalog="appearances")
    app.processEvents()
    try:
        assert library.controls.catalog_selector.accessibleName() == "Library catalog"
        assert library.controls.object_selector.accessibleName() == "Saved object"
        assert library.controls.sort_selector.accessibleName() == "Saved object sort"
        assert library.controls.create_button.accessibleName() == "Create saved object"
        assert library.controls.rename_button.accessibleName() == "Rename saved object"
        assert library.controls.duplicate_button.accessibleName() == "Duplicate saved object"
        assert library.controls.pin_button.accessibleName() == "Pin saved object"
        assert library.controls.delete_button.accessibleName() == "Delete saved object"
        assert library.controls.create_button.isVisible() is False
        assert library.controls.empty_create_button.isVisible() is True

        frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))  # noqa: SLF001
        library.refresh()
        app.processEvents()
        library.controls.search_input.setText("does-not-match")
        app.processEvents()
        assert library.controls.details_label.text().startswith("No matches")
        assert library.controls.create_button.isVisible() is True
        assert library.controls.empty_create_button.isVisible() is False
        assert library._session.catalog is LibraryCatalog.APPEARANCES  # noqa: SLF001
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_library_geometry_persists_while_legacy_splitter_setting_stays_inert(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

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
        ui={
            "future_preference": "keep",
            "library_splitter_sizes": [123, 234, 345],
        },
    )
    first_frame = QtAppFrameAdapter().create_frame(app_settings=initial, **common)
    first_library = first_frame.show_reusable_object_library()
    app.processEvents()
    try:
        first_library.controls.dialog.setGeometry(48, 64, 1120, 700)
        assert first_library.controls.splitter is None
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
        assert expected_sizes == (123, 234, 345)
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
        assert second_library.controls.splitter is None
        assert restored.ui_settings.library_splitter_sizes == expected_sizes
    finally:
        second_library.controls.dialog.close()
        second_frame.window.close()
        app.processEvents()

def test_library_real_qt_mounts_nested_appearance_editor(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication, QGroupBox

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

    library.controls.catalog_selector.setCurrentText(LibraryCatalog.APPEARANCES.value)
    app.processEvents()
    library.controls.create_button.click()
    app.processEvents()

    editor = library.controls.appearance_editor
    assert editor is not None
    assert editor.controls.breadcrumb_label.text().endswith("New Appearance")
    editor_copy = "\n".join(
        widget.text()
        for widget in editor.findChildren(QGroupBox)
        if hasattr(widget, "text")
    ).lower()
    assert "signature style" not in editor_copy
    assert not any(
        phrase in editor_copy for phrase in ("prototype", "synthetic", "mvp", "preset's")
    )
    preview_copy = editor.controls.sample_preview_label.text().lower()
    assert not any(
        phrase in preview_copy
        for phrase in ("synthetic", "mvp", "preset's", "never saved", "never persisted")
    )

    editor.controls.name_input.setText("Offscreen appearance")
    editor.controls.save_button.click()
    app.processEvents()

    assert library.controls.appearance_editor is None
    assert "Offscreen appearance" in frame._reusable_objects.view().appearance_names  # noqa: SLF001
    library.controls.dialog.close()
    frame.window.close()
    app.processEvents()


def test_appearance_editor_minimum_layout_scroll_and_cancel(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    class DiscardQuestion:
        Save = QMessageBox.StandardButton.Save
        Discard = QMessageBox.StandardButton.Discard
        Cancel = QMessageBox.StandardButton.Cancel
        calls = 0

        @classmethod
        def question(cls, *_args: object) -> QMessageBox.StandardButton:
            cls.calls += 1
            return cls.Discard

    app = QApplication.instance() or QApplication(["foliaseal-appearance-layout"])
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
    frame._bindings = replace(frame._bindings, q_message_box=DiscardQuestion)  # noqa: SLF001
    frame.window.show()
    library = frame.show_reusable_object_library()
    try:
        library.controls.catalog_selector.setCurrentText(LibraryCatalog.APPEARANCES.value)
        library.controls.create_button.click()
        dialog = library.controls.dialog
        dialog.resize(1000, 650)
        for _ in range(3):
            app.processEvents()
        editor = library.controls.appearance_editor
        assert editor is not None
        assert (dialog.width(), dialog.height()) == (1000, 650)
        assert editor.controls.cancel_button.text() == "Cancel"
        assert library.controls.library_footer_host.isVisible()
        assert editor.controls.sample_preview_image.isVisible()
        assert editor.controls.sample_preview_image.pixmap() is not None
        assert editor.controls.save_button.isDefault()
        assert editor.controls.cancel_button.width() < 200
        assert editor.controls.save_button.width() < 200
        assert editor.controls.form_scroll_area.horizontalScrollBar().maximum() == 0

        # Visible content and image controls are primary inputs. Secondary
        # typography and decoration choices follow them in the scrollable form.
        appearance_controls = editor.controls.setup_form.appearance_controls
        visible_text = editor.controls.setup_form.visible_text_controls

        field_checks = visible_text.field_checks_container.findChildren(QCheckBox)
        assert len(field_checks) == 8
        field_x = sorted(
            {
                check.mapTo(visible_text.field_checks_container, check.rect().topLeft()).x()
                for check in field_checks
            }
        )
        assert len(field_x) >= 2
        assert field_x[-1] - field_x[0] > 24
        field_y = [
            check.mapTo(visible_text.field_checks_container, check.rect().topLeft()).y()
            for check in field_checks
        ]
        tallest_check = max(check.height() for check in field_checks)
        assert max(field_y) - min(field_y) <= tallest_check * 5

        def top_in_form(widget):
            form = editor.controls.form_scroll_area.widget()
            return widget.mapTo(form, widget.rect().topLeft()).y()

        image_y = top_in_form(appearance_controls.browse_image_button)
        layout_y = top_in_form(appearance_controls.layout_template)
        typography_y = top_in_form(appearance_controls.font_family)
        color_y = top_in_form(appearance_controls.text_color)
        assert image_y < layout_y < typography_y < color_y

        image_path = tmp_path / "synthetic-preview.png"
        image = QImage(360, 72, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        assert image.save(str(image_path), "PNG")
        editor.controls.setup_form.set_image_stamp_path(str(image_path))
        app.processEvents()

        pixmap = editor.controls.sample_preview_image.pixmap()
        assert editor.controls.sample_preview_image.isVisible()
        assert pixmap is not None
        assert pixmap.width() > pixmap.height() > 0
        assert pixmap.width() <= editor.controls.sample_preview_image.width()
        assert pixmap.height() <= editor.controls.sample_preview_image.height()
        editor.controls.setup_form.set_image_stamp_path(None)
        app.processEvents()
        assert editor.controls.sample_preview_image.isVisible()
        assert editor.controls.sample_preview_image.pixmap() is not None

        def top_left(widget):
            point = widget.mapTo(dialog, widget.rect().topLeft())
            return point.x(), point.y()

        preview_before = top_left(editor.controls.sample_preview_label)
        cancel_before = top_left(editor.controls.cancel_button)
        save_before = top_left(editor.controls.save_button)
        bar = editor.controls.form_scroll_area.verticalScrollBar()
        assert bar.maximum() > 0
        bar.setValue(bar.maximum())
        app.processEvents()
        assert bar.value() > 0
        assert top_left(editor.controls.sample_preview_label) == preview_before
        assert top_left(editor.controls.cancel_button) == cancel_before
        assert top_left(editor.controls.save_button) == save_before
        assert library.controls.library_footer_host.width() > dialog.width() * 0.9
        assert cancel_before[0] > dialog.width() // 2
        assert save_before[0] > cancel_before[0]
        assert cancel_before[1] > editor.controls.container.y()
        editor.controls.name_input.setText("Unsaved appearance")
        editor.controls.cancel_button.click()
        app.processEvents()
        assert DiscardQuestion.calls == 1
        assert library.controls.appearance_editor is None
        assert frame._reusable_objects.view().appearance_names == ()  # noqa: SLF001
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_repeated_preset_editor_open_close_keeps_shared_footer_and_width(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-preset-footer-stability"])
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
    frame._reusable_objects.execute(SaveAppearance("Approval", build_signature_appearance()))  # noqa: SLF001
    library = frame.show_reusable_object_library(initial_catalog="presets")
    app.processEvents()
    try:
        library.controls.dialog.resize(1000, 650)
        library.controls.catalog_selector.setCurrentText(LibraryCatalog.PRESETS.value)
        app.processEvents()
        for _ in ("First preset", "Second preset"):
            library.controls.create_button.click()
            app.processEvents()
            editor = library.controls.preset_editor
            assert editor is not None
            footer = library.controls.library_footer_host
            footer_position = footer.mapTo(library.controls.dialog, footer.rect().topLeft())
            assert footer.isVisible() is True
            if library.controls.detail_scroll_area is not None:
                assert library.controls.detail_scroll_area.horizontalScrollBar().maximum() == 0
            editor.controls.cancel_button.click()
            app.processEvents()
            assert library.controls.preset_editor is None
            assert footer.mapTo(library.controls.dialog, footer.rect().topLeft()) == footer_position
            assert library.controls.library_footer_host.isVisible() is True
    finally:
        library.controls.dialog.close()
        frame.window.close()
        app.processEvents()


def test_real_offscreen_library_mutation_protects_active_placed_signature(
    tmp_path: Path,
) -> None:
    """Exercise production AppFrame → Library → service invalidation wiring."""

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame, QtAppFrameAdapter

    class QuestionBox:
        Yes = 1
        Cancel = 2
        No = Cancel
        prompts: list[tuple[object, object, object, object, object]] = []
        result = Cancel

        @classmethod
        def question(cls, parent, title, text, buttons, default_button):
            cls.prompts.append((parent, title, text, buttons, default_button))
            return cls.result

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-placement-invalidation"])

    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    adapter = QtAppFrameAdapter()
    frame = FoliaSealAppFrame(
        bindings=adapter._bindings,  # noqa: SLF001 - real adapter bindings for integration evidence
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "signed"),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        render_backend_factory=lambda: _StaticRenderBackend(),
    )
    frame._bindings = replace(frame._bindings, q_message_box=QuestionBox)  # noqa: SLF001
    frame.window.show()
    app.processEvents()

    try:
        frame._reusable_objects.execute(  # noqa: SLF001 - seed the production catalog boundary
            SaveAppearance("Approval", build_signature_appearance())
        )
        appearance_ref = frame._reusable_objects.view().appearances[0].ref  # noqa: SLF001
        assert frame.open_pdf_path(source) is not None
        workflow = frame.current_signing_workflow
        assert workflow is not None
        workflow.selected_appearance_profile_id = appearance_ref.object_id
        original_rect = SignatureRect(
            page_index=0,
            left_pt=20.0,
            bottom_pt=30.0,
            width_pt=180.0,
            height_pt=60.0,
        )
        workflow.set_signature_rect(original_rect)
        active_session = frame._workspace_host.active().session  # noqa: SLF001
        assert active_session.signature_rect() == original_rect
        assert active_session.selected_appearance_profile_id() == appearance_ref.object_id

        library = frame.show_reusable_object_library(initial_catalog="appearances")
        library.controls.catalog_selector.setCurrentText(LibraryCatalog.APPEARANCES.value)
        library.controls.object_selector.setCurrentIndex(0)
        library.controls.edit_button.click()
        app.processEvents()
        editor = library.controls.appearance_editor
        assert editor is not None
        assert editor.initial_ref == appearance_ref
        assert editor.controls.name_input.text() == "Approval"
        editor.controls.setup_form.appearance_controls.signer_label_prefix.setText("Changed")
        changed_appearance = editor.controls.setup_form.build_draft().appearance
        assert changed_appearance.signer_label_prefix == "Changed"
        assert any(
            binding.show_in_visible_appearance
            for _field_key, binding in changed_appearance.iter_field_bindings()
        )
        command = SaveAppearance(
            "Approval",
            changed_appearance,
            appearance_profile_id=appearance_ref.object_id,
            overwrite=True,
        )

        QuestionBox.result = QuestionBox.Cancel
        with pytest.raises(ReusableObjectMutationRejected):
            frame._reusable_objects.execute(command)  # noqa: SLF001
        app.processEvents()
        assert workflow.signature_rect == original_rect
        assert (
            frame._reusable_objects.resolve(appearance_ref).appearance.signer_label_prefix
            != "Changed"
        )  # noqa: SLF001
        assert QuestionBox.prompts[-1][2] == "Remove the placed signature and continue?"
        assert QuestionBox.prompts[-1][4] == QuestionBox.Cancel

        QuestionBox.result = QuestionBox.Yes
        frame._reusable_objects.execute(command)  # noqa: SLF001
        app.processEvents()
        assert workflow.signature_rect is None
        assert (
            frame._reusable_objects.resolve(appearance_ref).appearance.signer_label_prefix
            == "Changed"
        )  # noqa: SLF001
    finally:
        frame._workspace_host.close()  # noqa: SLF001 - bypass draft prompt during teardown
        frame.window.close()
        app.processEvents()
        if created_app:
            app.quit()

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

    library.controls.catalog_selector.setCurrentText(LibraryCatalog.PRESETS.value)
    library.controls.create_button.click()
    app.processEvents()
    preset_editor = library.controls.preset_editor
    assert preset_editor is not None
    preset_editor.controls.name_input.setText("Offscreen preset")
    preset_editor.controls.create_appearance_button.click()
    app.processEvents()
    appearance_editor = preset_editor.appearance_child
    assert appearance_editor is not None
    assert "Appearance / New Appearance" in appearance_editor.controls.breadcrumb_label.text()
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
        library.controls.catalog_selector.setCurrentText(LibraryCatalog.PRESETS.value)
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
        library.controls.catalog_selector.setCurrentText(LibraryCatalog.PRESETS.value)
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


def test_library_real_qt_nested_preset_captures_current_placement(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signature_library_session import LibraryCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    app = QApplication.instance() or QApplication(["foliaseal-preset-current-placement"])
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
    created = build_placement_profile(display_name="Captured current placement")

    def capture_placement():
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

    fake_session = SimpleNamespace(
        can_undo_placement=lambda: False,
        can_redo_placement=lambda: False,
        can_select_all_document_text=lambda: False,
        can_copy_selected_document_text=lambda: False,
    )
    fake_maintenance = SimpleNamespace(
        has_unsaved_changes=lambda: False,
        clear_session_secrets=lambda: None,
        refresh_signature_profiles=lambda: None,
    )
    frame._workspace_host.active = lambda: SimpleNamespace(
        session=fake_session,
        maintenance=fake_maintenance,
    )
    frame._open_current_placement_profile_editor = capture_placement
    library = frame.show_reusable_object_library()
    app.processEvents()
    try:
        library.controls.catalog_selector.setCurrentText(LibraryCatalog.PRESETS.value)
        library.controls.create_button.click()
        app.processEvents()
        editor = library.controls.preset_editor
        assert editor is not None
        editor.controls.name_input.setText("Preset with current placement")
        editor.controls.appearance_selector.setCurrentText("Approval")
        editor.controls.capture_placement_button.click()
        app.processEvents()

        assert editor.controls.placement_selector.currentText() == "Captured current placement"
        editor.controls.save_button.click()
        app.processEvents()
        assert library.controls.preset_editor is None
        resolved = frame._reusable_objects.view().presets[0]
        saved = frame._reusable_objects.resolve(resolved.ref)
        assert saved.preset.placement_profile_id == created.placement_profile_id
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
