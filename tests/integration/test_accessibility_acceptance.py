"""Real-Qt acceptance for keyboard reachability and support-surface semantics."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_real_qt_keyboard_accessibility_and_support_surfaces(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt, QTimer, QUrl
    from PySide6.QtGui import QDesktopServices, QKeySequence
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QMenu, QPushButton

    from foliaseal.application.support_diagnostics import SupportLocations
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_command_model import (
        EDIT_COMMAND_DEFINITIONS,
        FILE_COMMAND_DEFINITIONS,
        HELP_COMMAND_DEFINITIONS,
        SETTINGS_COMMAND_DEFINITIONS,
        SIGNING_COMMAND_DEFINITIONS,
        VIEW_COMMAND_DEFINITIONS,
        AppFrameCommandId,
    )

    unicode_root = tmp_path / "FoliaSeal-日本語"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(unicode_root / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(unicode_root / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(unicode_root / "state"))
    opened_urls: list[str] = []

    def capture_open_url(url: QUrl) -> bool:
        opened_urls.append(url.toString())
        return True

    monkeypatch.setattr(QDesktopServices, "openUrl", staticmethod(capture_open_url))
    app = QApplication.instance() or QApplication(["foliaseal"])
    settings = AppSettings(
        schema_version=1,
        default_open_directory=str(unicode_root / "open"),
        default_output_directory=str(unicode_root / "signed"),
        linux_packaging_channel="primary",
        ui={},
    )
    settings_store = AppSettingsStore(storage_dir=unicode_root / "config-store")
    settings_store.save_settings(settings)
    frame = QtAppFrameAdapter().create_frame(
        app_settings=settings,
        app_settings_store=settings_store,
        certificate_catalog_store=CertificateCatalogStore(
            storage_dir=unicode_root / "certificates"
        ),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=unicode_root / "profiles"),
    )
    support_dialogs: list[object] = []

    try:
        frame.window.show()
        app.processEvents()
        assert frame.window.minimumWidth() == 1100
        assert frame.window.minimumHeight() == 700

        primary_buttons = {
            button.accessibleName(): button
            for button in frame.window.findChildren(QPushButton)
            if button.accessibleName()
        }
        assert "Open a PDF" in primary_buttons
        assert "Manage Signature Library" in primary_buttons
        assert primary_buttons["Open a PDF"].isEnabled()
        assert primary_buttons["Manage Signature Library"].isEnabled()

        menu_definitions = (
            ("File", FILE_COMMAND_DEFINITIONS),
            ("Edit", EDIT_COMMAND_DEFINITIONS),
            ("View", VIEW_COMMAND_DEFINITIONS),
            ("Signing", SIGNING_COMMAND_DEFINITIONS),
            ("Settings", SETTINGS_COMMAND_DEFINITIONS),
            ("Help", HELP_COMMAND_DEFINITIONS),
        )
        menus = {
            menu.title().replace("&", ""): menu
            for menu in frame.window.menuBar().findChildren(QMenu)
            if menu.title()
        }
        top_level_menus = [
            menu for menu in frame.window.menuBar().findChildren(QMenu) if menu.title()
        ]
        assert [menu.title() for menu in top_level_menus] == [
            "&File",
            "&Edit",
            "&View",
            "S&igning",
            "Se&ttings",
            "&Help",
        ]
        top_level_mnemonics = [
            menu.title()[menu.title().index("&") + 1].lower()
            for menu in top_level_menus
        ]
        assert len(top_level_mnemonics) == len(set(top_level_mnemonics))
        expected_enabled = {
            "File": [True, False, False, False, True],
            "Edit": [False] * len(EDIT_COMMAND_DEFINITIONS),
            "View": [False] * len(VIEW_COMMAND_DEFINITIONS),
            "Signing": [True, False, False, False, False],
            "Settings": [True] * len(SETTINGS_COMMAND_DEFINITIONS),
            "Help": [True] * len(HELP_COMMAND_DEFINITIONS),
        }
        for menu_name, definitions in menu_definitions:
            actions = menus[menu_name].actions()
            assert [action.objectName() for action in actions] == [
                definition.command_id.value for definition in definitions
            ]
            assert [action.toolTip() for action in actions] == [
                definition.accessible_name for definition in definitions
            ]
            assert [action.shortcut().toString() for action in actions] == [
                QKeySequence(definition.shortcut).toString() if definition.shortcut else ""
                for definition in definitions
            ]
            assert [action.isEnabled() for action in actions] == expected_enabled[menu_name]
            assert len(
                [
                    text[text.index("&") + 1].lower()
                    for text in (action.text() for action in actions)
                    if "&" in text
                ]
            ) == len(
                {
                    text[text.index("&") + 1].lower()
                    for text in (action.text() for action in actions)
                    if "&" in text
                }
            )

        frame.window.activateWindow()
        frame.window.setFocus()
        QTest.keyClick(frame.window, Qt.Key_F1)
        app.processEvents()
        help_viewer = frame.help_viewer
        assert help_viewer is not None
        assert help_viewer.dialog.isModal() is False
        assert help_viewer.search_input.accessibleName() == "Search Help topics"
        assert help_viewer.content_browser.accessibleName() == "Help topic content"
        assert help_viewer.close_button.accessibleName() == "Close Help"
        help_viewer.close()
        app.processEvents()

        support_dialogs = [
            frame.show_keyboard_shortcuts(),
            frame.show_data_locations(),
            frame.show_about(),
        ]
        for dialog in support_dialogs:
            assert dialog.dialog.isModal() is False
            assert dialog.content.isReadOnly()
            assert dialog.content.accessibleName().endswith(" content")
            assert dialog.close_button.accessibleName().startswith("Close ")
            assert dialog.close_button.focusPolicy() & Qt.TabFocus
            dialog.close()
        app.processEvents()

        locations = frame.show_data_locations()
        assert str(unicode_root) in locations.content.toPlainText()
        locations.close()
        app.processEvents()

        diagnostic_action = frame.command_actions()[AppFrameCommandId.OPEN_DIAGNOSTIC_LOGS]
        diagnostic_action.trigger()
        app.processEvents()
        logs_dir = SupportLocations.for_environment().logs_dir
        assert logs_dir.is_dir()
        assert opened_urls == [QUrl.fromLocalFile(str(logs_dir)).toString()]

        settings_observations: dict[str, object] = {}

        def exercise_settings() -> None:
            settings_dialog = frame.settings_dialog
            if settings_dialog is None:
                settings_observations["error"] = "settings dialog was not created"
                return
            try:
                restore = settings_dialog.controls.restore_defaults_button
                settings_observations["accessible_name"] = restore.accessibleName()
                settings_observations["tab_focus"] = bool(restore.focusPolicy() & Qt.TabFocus)
                settings_dialog.controls.default_open_directory.setText(
                    str(unicode_root / "changed")
                )
                restore.click()
                settings_observations["restored_open"] = (
                    settings_dialog.controls.default_open_directory.text()
                )
            except Exception as exc:  # pragma: no cover - Qt callback safety
                settings_observations["error"] = repr(exc)
            finally:
                settings_dialog.cancel()

        QTimer.singleShot(0, exercise_settings)
        frame.command_actions()[AppFrameCommandId.APPLICATION_SETTINGS].trigger()
        assert settings_store.load_settings() == settings
        assert settings_observations == {
            "accessible_name": "Restore application settings defaults",
            "tab_focus": True,
            "restored_open": AppSettings.default().default_open_directory,
        }
    finally:
        for dialog in support_dialogs:
            dialog.close()
        if frame.help_viewer is not None:
            frame.help_viewer.close()
        frame.window.close()
        app.processEvents()
