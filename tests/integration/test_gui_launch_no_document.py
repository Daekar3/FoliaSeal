"""Display-independent integration coverage for the no-document landing frame."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_real_qt_no_document_frame_exposes_primary_actions(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtGui import QKeySequence, QPalette
    from PySide6.QtWidgets import QApplication, QMenu, QPushButton

    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_command_model import (
        EDIT_COMMAND_DEFINITIONS,
        SETTINGS_COMMAND_DEFINITIONS,
        SIGNING_COMMAND_DEFINITIONS,
        VIEW_COMMAND_DEFINITIONS,
    )

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal"])
    accent_before = app.palette().color(QPalette.Highlight).name()

    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "home"),
            default_open_directory=str(tmp_path / "home"),
            linux_packaging_channel="primary",
            ui={"appearance_mode": "dark"},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    frame.window.show()
    app.processEvents()

    assert frame.current_workspace is None
    assert frame.window.minimumWidth() == 1100
    assert frame.window.minimumHeight() == 700
    assert frame.appearance_mode == "dark"
    assert app.palette().color(QPalette.Window).name() == "#202124"
    assert app.palette().color(QPalette.Highlight).name() == accent_before
    assert {button.text() for button in frame.window.findChildren(QPushButton)} >= {
        "Open a PDF…",
        "Manage Signature Library…",
    }

    file_menu = next(
        menu for menu in frame.window.menuBar().findChildren(QMenu) if menu.title() == "File"
    )
    assert file_menu.title() == "File"
    file_actions = file_menu.actions()
    assert [action.text() for action in file_actions] == [
        "&Open",
        "&Save",
        "Save &As",
        "&Close",
        "E&xit",
    ]
    assert [action.shortcut().toString() for action in file_actions] == [
        "Ctrl+O",
        "Ctrl+S",
        "Ctrl+Shift+S",
        "Ctrl+W",
        "Ctrl+Q",
    ]
    assert [action.toolTip() for action in file_actions] == [
        "Open PDF",
        "Sign and save PDF",
        "Save signed PDF as",
        "Close PDF",
        "Exit FoliaSeal",
    ]
    assert [action.isEnabled() for action in file_actions] == [True, False, False, False, True]

    edit_menu = next(
        menu for menu in frame.window.menuBar().findChildren(QMenu) if menu.title() == "Edit"
    )
    assert [action.text() for action in edit_menu.actions()] == [
        definition.mnemonic_text for definition in EDIT_COMMAND_DEFINITIONS
    ]
    assert [action.toolTip() for action in edit_menu.actions()] == [
        definition.accessible_name for definition in EDIT_COMMAND_DEFINITIONS
    ]
    assert [action.shortcut().toString() for action in edit_menu.actions()] == [
        definition.shortcut or "" for definition in EDIT_COMMAND_DEFINITIONS
    ]

    view_menu = next(
        menu for menu in frame.window.menuBar().findChildren(QMenu) if menu.title() == "View"
    )
    assert [action.text() for action in view_menu.actions()] == [
        definition.mnemonic_text for definition in VIEW_COMMAND_DEFINITIONS
    ]
    assert [action.toolTip() for action in view_menu.actions()] == [
        definition.accessible_name for definition in VIEW_COMMAND_DEFINITIONS
    ]
    assert [action.isCheckable() for action in view_menu.actions()] == [
        False,
        False,
        False,
        False,
        True,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]
    assert [action.isEnabled() for action in view_menu.actions()] == [
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
        False,
    ]
    assert [action.shortcut().toString() for action in view_menu.actions()] == [
        QKeySequence(definition.shortcut).toString() if definition.shortcut else ""
        for definition in VIEW_COMMAND_DEFINITIONS
    ]

    signing_menu = next(
        menu for menu in frame.window.menuBar().findChildren(QMenu) if menu.title() == "Signing"
    )
    assert [action.text() for action in signing_menu.actions()] == [
        definition.mnemonic_text for definition in SIGNING_COMMAND_DEFINITIONS
    ]
    assert [action.toolTip() for action in signing_menu.actions()] == [
        definition.accessible_name for definition in SIGNING_COMMAND_DEFINITIONS
    ]
    assert [action.isEnabled() for action in signing_menu.actions()] == [
        True,
        False,
        False,
        False,
        False,
    ]

    settings_menu = next(
        menu for menu in frame.window.menuBar().findChildren(QMenu) if menu.title() == "Settings"
    )
    assert [action.text() for action in settings_menu.actions()] == [
        definition.mnemonic_text for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert [action.objectName() for action in settings_menu.actions()] == [
        definition.command_id.value for definition in SETTINGS_COMMAND_DEFINITIONS
    ]
    assert [action.toolTip() for action in settings_menu.actions()] == [
        definition.accessible_name for definition in SETTINGS_COMMAND_DEFINITIONS
    ]

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


def test_real_qt_view_history_actions_dispatch_through_open_workspace(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

    from foliaseal.application.certificate_models import CertificateCatalog
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
    from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId
    from foliaseal.presentation.qt.signing_shell_port import (
        QtSigningWorkspacePort,
        QtSigningWorkspaceSessionPort,
        QtWorkspaceView,
        SigningWorkspaceBootstrap,
        SigningWorkspaceBundle,
    )

    class HistoryShell(QWidget):
        def __init__(self, bootstrap: SigningWorkspaceBootstrap) -> None:
            super().__init__()
            self.status_callback = bootstrap.on_status_change
            self.back_available = False
            self.forward_available = False
            self.back_calls = 0
            self.forward_calls = 0
            self.placement_mode_calls: list[str] = []
            self.remove_placement_calls = 0
            self.place_available = True
            self.adjust_available = False
            self.remove_available = False
            self.undo_available = False
            self.redo_available = False
            self.undo_calls = 0
            self.redo_calls = 0
            self.container = self

        def has_unsaved_changes(self) -> bool:
            return False

        def discard_draft(self) -> None:
            return None

        def cleanup_recovery_artifact(self) -> None:
            return None

        def clear_session_secrets(self) -> None:
            return None

        def choose_output_pdf_path(self) -> None:
            return None

        def has_explicit_output_pdf_path(self) -> bool:
            return False

        def apply_app_settings(self, settings: AppSettings) -> None:
            return None

        def refresh_certificate_configurations(self) -> CertificateCatalog:
            return CertificateCatalog(schema_version=1)

        def refresh_signature_profiles(self) -> None:
            return None

        def open_reusable_object_editor(self) -> bool:
            return False

        def set_document_text_selection_mode(self, enabled: bool) -> bool:
            return bool(enabled)

        def document_text_selection_mode_enabled(self) -> bool:
            return False

        def can_copy_selected_document_text(self) -> bool:
            return False

        def copy_selected_document_text(self) -> None:
            return None

        def set_viewer_interaction_mode(self, mode: str) -> str:
            self.placement_mode_calls.append(mode)
            return mode

        def can_place_signature_placement(self) -> bool:
            return self.place_available

        def can_adjust_signature_placement(self) -> bool:
            return self.adjust_available

        def can_remove_signature_placement(self) -> bool:
            return self.remove_available

        def remove_signature_placement(self) -> bool:
            self.remove_placement_calls += 1
            return True

        def can_undo_placement(self) -> bool:
            return self.undo_available

        def can_redo_placement(self) -> bool:
            return self.redo_available

        def undo_placement(self):
            self.undo_calls += 1
            self.undo_available = False
            self.redo_available = True
            return "undo-target"

        def redo_placement(self):
            self.redo_calls += 1
            self.redo_available = False
            self.undo_available = True
            return "redo-target"

        def go_to_previous_page(self) -> None:
            return None

        def go_to_next_page(self) -> None:
            return None

        def can_go_previous_page(self) -> bool:
            return False

        def can_go_next_page(self) -> bool:
            return False

        def go_back_link(self) -> None:
            self.back_calls += 1
            self.back_available = False
            self.forward_available = True
            self.status_callback("link_history_back")

        def go_forward_link(self) -> None:
            self.forward_calls += 1
            self.forward_available = False
            self.back_available = True
            self.status_callback("link_history_forward")

        def can_go_back_link(self) -> bool:
            return self.back_available

        def can_go_forward_link(self) -> bool:
            return self.forward_available

        def reset_zoom_view(self) -> None:
            return None

        def zoom_in_view(self) -> None:
            return None

        def zoom_out_view(self) -> None:
            return None

        def fit_page_view(self) -> None:
            return None

        def fit_width_view(self) -> None:
            return None

        def focus_document_search(self) -> None:
            return None

        def refresh_viewer(self) -> None:
            return None

        def close(self) -> bool:
            return super().close()

    class HistoryShellFactory:
        def __init__(self) -> None:
            self.shell: HistoryShell | None = None

        def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
            self.shell = HistoryShell(bootstrap)
            return SigningWorkspaceBundle(
                maintenance=QtSigningWorkspacePort(self.shell),
                session=QtSigningWorkspaceSessionPort(self.shell),
                testing=object(),
                view=QtWorkspaceView(self.shell),
            )

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal"])
    factory = HistoryShellFactory()
    adapter = QtAppFrameAdapter()
    frame = adapter.create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "output"),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        shell_factory=factory,
    )
    frame.window.show()
    app.processEvents()

    fixture = Path("artifacts/preview_sweep_assets/sweep_fixture.pdf").resolve()
    assert frame.open_pdf_path(fixture) is not None
    app.processEvents()
    assert factory.shell is not None
    shell = factory.shell
    actions = frame.command_actions()
    back_action = actions[AppFrameCommandId.BACK]
    forward_action = actions[AppFrameCommandId.FORWARD]
    undo_action = actions[AppFrameCommandId.UNDO]
    redo_action = actions[AppFrameCommandId.REDO]
    place_action = actions[AppFrameCommandId.PLACE_SIGNATURE]
    adjust_action = actions[AppFrameCommandId.ADJUST_PLACEMENT]
    remove_action = actions[AppFrameCommandId.REMOVE_PLACEMENT]
    assert back_action.isEnabled() is False
    assert forward_action.isEnabled() is False
    assert undo_action.isEnabled() is False
    assert redo_action.isEnabled() is False
    assert place_action.isEnabled() is True
    assert adjust_action.isEnabled() is False
    assert remove_action.isEnabled() is False

    shell.undo_available = True
    shell.status_callback("signing_readiness_changed")
    app.processEvents()
    assert undo_action.isEnabled() is True
    assert redo_action.isEnabled() is False
    frame.window.activateWindow()
    QTest.keyClick(frame.window, Qt.Key.Key_Z, Qt.KeyboardModifier.ControlModifier)
    assert shell.undo_calls == 1
    assert undo_action.isEnabled() is False
    assert redo_action.isEnabled() is True
    QTest.keyClick(
        frame.window,
        Qt.Key.Key_Z,
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
    )
    assert shell.redo_calls == 1
    assert undo_action.isEnabled() is True
    assert redo_action.isEnabled() is False

    editor = QLineEdit(frame.window)
    editor.show()
    editor.setText("12")
    editor.setFocus(Qt.FocusReason.OtherFocusReason)
    QTest.keyClicks(editor, "3")
    frame.window.activateWindow()
    editor.setFocus(Qt.FocusReason.OtherFocusReason)
    app.processEvents()
    frame._sync_edit_history_actions()
    assert undo_action.isEnabled() is True
    undo_action.trigger()
    app.processEvents()
    assert editor.text() == "12"
    assert shell.undo_calls == 1
    assert redo_action.isEnabled() is True
    redo_action.trigger()
    app.processEvents()
    assert editor.text() == "123"
    assert shell.redo_calls == 1
    editor.deleteLater()

    place_action.trigger()
    assert shell.placement_mode_calls == ["signature"]
    shell.adjust_available = True
    shell.remove_available = True
    shell.status_callback("placement_changed")
    app.processEvents()
    assert adjust_action.isEnabled() is True
    assert remove_action.isEnabled() is True
    adjust_action.trigger()
    remove_action.trigger()
    assert shell.placement_mode_calls == ["signature", "signature"]
    assert shell.remove_placement_calls == 1

    shell.back_available = True
    shell.status_callback("link_internal_navigation")
    app.processEvents()
    assert back_action.isEnabled() is True

    frame.window.activateWindow()
    QTest.keyClick(frame.window, Qt.Key.Key_Left, Qt.KeyboardModifier.AltModifier)
    app.processEvents()
    assert shell.back_calls == 1
    assert back_action.isEnabled() is False
    assert forward_action.isEnabled() is True

    QTest.keyClick(frame.window, Qt.Key.Key_Right, Qt.KeyboardModifier.AltModifier)
    app.processEvents()
    assert shell.forward_calls == 1
    assert back_action.isEnabled() is True
    assert forward_action.isEnabled() is False

    frame.window.close()
    app.processEvents()
    if created_app:
        app.quit()
