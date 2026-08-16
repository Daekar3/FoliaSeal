#!/usr/bin/env python3
"""Run the parent signing-flow audit against real Qt widgets.

This is deliberately a *semantic* GUI driver: it opens the real FoliaSeal
window, finds controls by their Qt type/text/form label, and invokes their Qt
slots.  It does not depend on screen coordinates, X11 injection, or a user's
configuration directory.  The runner writes screenshots and a JSON report to
an artifact directory and always closes every Qt window it opened.

Run under a graphical Qt session, for example::

    DISPLAY=:0 .venv/bin/python scripts/live_gui_parent_audit.py \
        --artifacts-dir /tmp/foliaseal-parent-audit

The audit uses a temporary copy of the representative PDF and temporary
settings/certificate/profile stores.  It creates a managed self-signed
certificate through the visible Create certificate dialog, selects it, places
a visible signature, accepts the confirmation dialog, signs, and reopens the
result.  No user profile or source fixture is modified.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from foliaseal.application.signing_backend import build_signing_executor
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.presentation.qt.app_frame import build_qt_app_frame_host

DEFAULT_PDF = Path("artifacts/preview_sweep_assets/sweep_fixture.pdf")
AUDIT_CERTIFICATE_NAME = "Live GUI Audit Certificate"
AUDIT_PASSPHRASE = "foliaseal-live-gui-audit"
AUDIT_APPEARANCE_PROFILE = "Live GUI Audit Appearance"
AUDIT_PLACEMENT_PROFILE = "Live GUI Audit Placement"
AUDIT_SIGNATURE_PRESET = "Live GUI Audit Preset"


class _InMemorySecretStore:
    """Small audit-only secret store; prevents system-keyring side effects."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def is_available(self) -> bool:
        return True

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        return f"audit:{configuration_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        self._values[secret_ref] = secret

    def get_secret(self, secret_ref: str) -> str | None:
        return self._values.get(secret_ref)

    def delete_secret(self, secret_ref: str) -> None:
        self._values.pop(secret_ref, None)


@dataclass
class _Audit:
    app: Any
    window: Any
    artifact_dir: Path
    checkpoints: list[dict[str, str]]

    def process_events(self) -> None:
        self.app.processEvents()

    def checkpoint(self, name: str, stage: str) -> None:
        self.checkpoint_widget(name, stage, self.window)

    def checkpoint_widget(self, name: str, stage: str, widget: Any) -> None:
        self.process_events()
        screenshot = self.artifact_dir / f"{len(self.checkpoints) + 1:02d}-{name}.png"
        pixmap = widget.grab()
        if not pixmap.save(str(screenshot), "PNG"):
            raise RuntimeError(f"Could not write screenshot: {screenshot}")
        self.checkpoints.append({"name": name, "stage": stage, "screenshot": str(screenshot)})


@dataclass
class _NonNativeAuditSaveDialog:
    """Exercise a real, local Qt save dialog without depending on a WM-native one.

    ``QFileDialog.getSaveFileName`` delegates to the desktop's native dialog on
    several platforms.  That dialog is intentionally opaque to Qt's test/event
    loop and caused this unattended audit to hang.  This proxy keeps the
    *production* ``choose_output_pdf_path`` action intact, but supplies its
    ``q_file_dialog`` dependency with a real ``QFileDialog`` configured for
    Qt's non-native implementation.  The selected file is made through that
    dialog's normal selection and accept paths, rather than injected as a
    return value.
    """

    output_path: Path
    calls: list[tuple[str, str, str]]

    def getSaveFileName(
        self,
        parent: Any,
        caption: str,
        directory: str,
        file_filter: str,
    ) -> tuple[str, str]:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QDialog, QFileDialog

        self.calls.append((caption, directory, file_filter))
        if caption != "Save signed PDF":
            raise RuntimeError(f"Unexpected output-dialog caption: {caption!r}.")
        if file_filter != "PDF files (*.pdf)":
            raise RuntimeError(f"Unexpected output-dialog filter: {file_filter!r}.")

        dialog = QFileDialog(parent, caption, directory, file_filter)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setDefaultSuffix("pdf")
        if not dialog.testOption(QFileDialog.Option.DontUseNativeDialog):
            raise RuntimeError("Audit output dialog did not enter Qt non-native mode.")

        def select_and_accept() -> None:
            dialog.setDirectory(str(self.output_path.parent))
            dialog.selectFile(self.output_path.name)
            dialog.accept()

        # ``exec`` starts a local Qt event loop, so queue selection before it
        # begins.  This is the same modal behavior the production static helper
        # has, but it remains visible and deterministic to the audit runner.
        QTimer.singleShot(0, select_and_accept)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return ("", file_filter)
        selected = dialog.selectedFiles()
        if len(selected) != 1:
            raise RuntimeError(f"Output dialog accepted {len(selected)} paths, expected one.")
        return (selected[0], file_filter)


@dataclass
class _NonNativeAuditDirectoryDialog:
    """Drive the real Qt directory picker while avoiding an opaque WM-native dialog."""

    selections: dict[str, Path]
    calls: list[tuple[str, str]]

    def getExistingDirectory(self, parent: Any, caption: str, directory: str) -> str:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QDialog, QFileDialog

        self.calls.append((caption, directory))
        selected_path = self.selections.get(caption)
        if selected_path is None:
            raise RuntimeError(f"Unexpected directory-dialog caption: {caption!r}.")
        dialog = QFileDialog(parent, caption, directory)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)

        def select_and_accept() -> None:
            dialog.setDirectory(str(selected_path))
            dialog.accept()

        QTimer.singleShot(0, select_and_accept)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return ""
        selected = dialog.selectedFiles()
        if len(selected) != 1:
            raise RuntimeError(f"Directory dialog accepted {len(selected)} paths, expected one.")
        return selected[0]


def _button_with_text(root: Any, text: str) -> Any:
    from PySide6.QtWidgets import QPushButton

    for button in root.findChildren(QPushButton):
        if button.text().strip() == text:
            return button
    raise RuntimeError(f"Could not find button {text!r} in {root.windowTitle()!r}.")


def _line_edit_for_form_label(dialog: Any, label_text: str) -> Any:
    """Find an editor by its ``QFormLayout`` label, not insertion order."""
    from PySide6.QtWidgets import QFormLayout

    layout = dialog.layout()
    if not isinstance(layout, QFormLayout):
        raise RuntimeError(f"Expected a form layout in {dialog.windowTitle()!r}.")
    for row in range(layout.rowCount()):
        label_item = layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
        field_item = layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
        label = label_item.widget() if label_item is not None else None
        field = field_item.widget() if field_item is not None else None
        if label is not None and label.text().strip() == label_text and field is not None:
            return field
    raise RuntimeError(f"Could not find form field labelled {label_text!r}.")


def _single_line_edit(dialog: Any) -> Any:
    """Find the value editor in a standard Qt input dialog."""
    from PySide6.QtWidgets import QLineEdit

    editors = dialog.findChildren(QLineEdit)
    if len(editors) != 1:
        raise RuntimeError(
            f"Expected one text editor in {dialog.windowTitle()!r}, found {len(editors)}."
        )
    return editors[0]


def _assert_visible_text(root: Any, expected: str) -> None:
    from PySide6.QtWidgets import QLabel

    for label in root.findChildren(QLabel):
        is_visible = getattr(label, "isVisible", None)
        if (not callable(is_visible) or is_visible()) and expected in label.text():
            return
    raise RuntimeError(f"Could not find visible explanatory text: {expected!r}.")


def _active_modal(app: Any, title: str) -> Any | None:
    widget = app.activeModalWidget()
    if widget is not None and widget.windowTitle() == title:
        return widget
    # QInputDialog.getText() can be visible in a nested event loop before Qt
    # updates ``activeModalWidget`` on some window managers.  Scan the actual
    # visible top-level dialogs as the semantic fallback.
    for candidate in app.topLevelWidgets():
        if candidate.isVisible() and candidate.windowTitle() == title:
            return candidate
    return None


def _run_modal_action(app: Any, action: Callable[[], Any], driver: Callable[[Any], bool]) -> Any:
    """Run a blocking app-frame action while driving its Qt dialog semantically."""
    from PySide6.QtCore import QTimer

    completed = False

    def tick() -> None:
        nonlocal completed
        if completed:
            return
        completed = driver(app)
        if not completed:
            QTimer.singleShot(25, tick)

    QTimer.singleShot(0, tick)
    return action()


def _schedule_input_dialog_accept(app: Any, *, title: str, value: str) -> None:
    """Accept a static ``QInputDialog.getText`` while its click handler is nested.

    Clicking a save button synchronously enters Qt's nested ``getText`` event
    loop, so the outer audit driver's next tick cannot be scheduled *after*
    that click.  Queue this before the click so it runs inside that nested loop.
    """
    from PySide6.QtCore import QTimer

    def accept_when_visible() -> None:
        dialog = _active_modal(app, title)
        if dialog is None:
            QTimer.singleShot(10, accept_when_visible)
            return
        dialog.setTextValue(value)
        dialog.accept()

    QTimer.singleShot(0, accept_when_visible)


def _dismiss_information_box(app: Any) -> None:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QMessageBox

    def dismiss() -> None:
        modal = app.activeModalWidget()
        if isinstance(modal, QMessageBox):
            modal.accept()

    QTimer.singleShot(25, dismiss)


def _create_managed_certificate(frame: Any, audit: _Audit) -> Any:
    """Create one certificate through the visible Qt dialog and refresh the shell."""
    from PySide6.QtWidgets import QCheckBox

    clicked = False

    def drive(app: Any) -> bool:
        nonlocal clicked
        dialog = _active_modal(app, "Create certificate")
        if dialog is None:
            return False
        if clicked:
            return True
        _line_edit_for_form_label(dialog, "Display name").setText(AUDIT_CERTIFICATE_NAME)
        _line_edit_for_form_label(dialog, "Password").setText(AUDIT_PASSPHRASE)
        checkboxes = dialog.findChildren(QCheckBox)
        save_password = next(
            (box for box in checkboxes if box.text() == "Save password securely"),
            None,
        )
        if save_password is None:
            raise RuntimeError("Certificate dialog has no saved-password checkbox.")
        save_password.setChecked(True)
        # ``information`` enters a nested Qt event loop; schedule its dismissal
        # before clicking Create so no unattended dialog survives this audit.
        _dismiss_information_box(app)
        _button_with_text(dialog, "Create").click()
        clicked = True
        return True

    result = _run_modal_action(audit.app, frame.show_certificate_creation, drive)
    if result is None:
        raise RuntimeError("Create certificate dialog did not return a creation result.")
    return result


def _accept_confirm_signing(app: Any) -> bool:
    """Accept FoliaSeal's actual confirmation QMessageBox by its standard button."""
    from PySide6.QtWidgets import QMessageBox

    modal = app.activeModalWidget()
    if not isinstance(modal, QMessageBox) or modal.windowTitle() != "Confirm signing":
        return False
    button = modal.button(QMessageBox.StandardButton.Yes)
    if button is None:
        raise RuntimeError("Confirm signing dialog did not provide a Yes button.")
    button.click()
    return True


def _select_certificate_configuration(shell: Any, display_name: str) -> None:
    """Select the created identity through its real Qt combo-box signal path."""
    from PySide6.QtWidgets import QComboBox

    for combo in shell.findChildren(QComboBox):
        index = combo.findText(display_name)
        if index >= 0:
            combo.setCurrentIndex(index)
            return
    raise RuntimeError(f"Certificate configuration {display_name!r} is not visible in the shell.")


def _audit_certificate_and_preset_clarity(shell: Any, audit: _Audit) -> None:
    """Assert the mounted shell explains the two reusable-object choices."""
    _assert_visible_text(
        shell,
        "Certificate configurations are saved signing identities.",
    )
    _assert_visible_text(
        shell,
        "Signature presets reuse saved appearance and placement choices.",
    )
    audit.checkpoint("certificate-and-preset-clarity", "Step 2 of 6 — Choose signing setup")


def _visible_group_titles(root: Any) -> set[str]:
    """Return titles from group boxes that are actually visible in ``root``."""
    from PySide6.QtWidgets import QGroupBox

    return {
        group.title().strip()
        for group in root.findChildren(QGroupBox)
        if group.isVisible()
    }


def _audit_preset_first_shell(shell: Any, audit: _Audit) -> None:
    """Prove the narrow default shell keeps the full editor behind refinement."""
    expected_default_groups = {
        "Signature preset",
        "Certificate configuration",
        "Signed appearance preview",
        "Manual refinement",
    }
    forbidden_default_groups = {
        "Visible signature",
        "Signature style",
        "Visible text",
        "Placement on page",
    }
    default_groups = _visible_group_titles(shell)
    missing = expected_default_groups - default_groups
    leaked = forbidden_default_groups & default_groups
    if missing or leaked:
        raise RuntimeError(
            "Default shell is not preset-first "
            f"(missing={sorted(missing)!r}, leaked={sorted(leaked)!r})."
        )
    for forbidden_button in (
        "Save preset",
        "Delete preset",
        "Save appearance for reuse...",
        "Save placement for reuse...",
        "Save signature preset for reuse...",
    ):
        try:
            _visible_button_with_text(shell, forbidden_button)
        except RuntimeError:
            continue
        raise RuntimeError(f"Default shell leaked inline authoring action {forbidden_button!r}.")
    from PySide6.QtWidgets import QLineEdit

    if any(
        editor.isVisible() and editor.placeholderText().strip() == "Enter a preset name"
        for editor in shell.findChildren(QLineEdit)
    ):
        raise RuntimeError("Default shell leaked the inline preset-name editor.")
    audit.checkpoint("preset-first-default-shell", "Step 2 of 6 — Choose signing setup")

    def drive(app: Any) -> bool:
        dialog = _active_modal(app, "Refine current PDF setup")
        if dialog is None:
            return False
        dialog_groups = _visible_group_titles(dialog)
        required_dialog_groups = {"Visible signature", "Placement on page"}
        absent = required_dialog_groups - dialog_groups
        if absent:
            raise RuntimeError(
                "Manual refinement did not expose current-PDF editing controls "
                f"(missing={sorted(absent)!r})."
            )
        _button_with_text(dialog, "Apply")
        _button_with_text(dialog, "Cancel")
        audit.checkpoint_widget(
            "manual-refinement-dialog",
            "Manual refinement exposes current-PDF appearance and placement",
            dialog,
        )
        _button_with_text(dialog, "Cancel").click()
        return True

    _open_refinement_from_visible_control(shell, audit, drive)
    default_groups_after_cancel = _visible_group_titles(shell)
    if default_groups_after_cancel != default_groups:
        raise RuntimeError("Cancelling manual refinement changed the default shell layout.")


def _audit_profile_library(frame: Any, audit: _Audit) -> None:
    """Verify the visible Settings route manages saved presets without shell internals."""
    def drive(app: Any) -> bool:
        dialog = _active_modal(app, "Manage signing profiles")
        if dialog is None:
            return False
        _assert_visible_text(dialog, "References")
        from PySide6.QtWidgets import QComboBox

        combos = dialog.findChildren(QComboBox)
        if len(combos) != 1 or combos[0].findText(f"Preset: {AUDIT_SIGNATURE_PRESET}") < 0:
            raise RuntimeError("Profile library did not visibly list the saved signature preset.")
        _button_with_text(dialog, "Close").click()
        return True

    _run_modal_action(audit.app, frame.show_signature_profile_library, drive)
    audit.checkpoint("profile-library-clarity", "Step 4 of 6 — Review reusable signing objects")


def _audit_settings_directory_browsing(
    frame: Any,
    audit: _Audit,
    *,
    root: Path,
    settings_store: AppSettingsStore,
) -> None:
    """Select both settings directories through visible production Browse controls."""
    open_directory = root / "selected-open"
    output_directory = root / "selected-output"
    open_directory.mkdir()
    output_directory.mkdir()
    original_bindings = frame._bindings
    directory_dialog = _NonNativeAuditDirectoryDialog(
        selections={
            "Choose default open folder": open_directory,
            "Choose default output folder": output_directory,
        },
        calls=[],
    )
    frame._bindings = replace(original_bindings, q_file_dialog=directory_dialog)
    phase = "open"
    try:
        def drive(app: Any) -> bool:
            nonlocal phase
            dialog = _active_modal(app, "Application settings")
            if dialog is None:
                return False
            open_edit = _line_edit_for_form_label(dialog, "Default open folder")
            output_edit = _line_edit_for_form_label(dialog, "Default output folder")
            from PySide6.QtWidgets import QPushButton

            browse_buttons = [
                button
                for button in dialog.findChildren(QPushButton)
                if button.text().strip() == "Browse..." and button.isVisible()
            ]
            if len(browse_buttons) != 2:
                raise RuntimeError(
                    "Application settings did not expose two visible Browse controls."
                )
            if phase == "open":
                browse_buttons[0].click()
                phase = "output"
                return False
            if phase == "output":
                browse_buttons[1].click()
                phase = "save"
                return False
            if (
                str(open_edit.text()) != str(open_directory)
                or str(output_edit.text()) != str(output_directory)
            ):
                raise RuntimeError(
                    "Directory picker selection did not update both settings fields."
                )
            _button_with_text(dialog, "Save").click()
            return True

        _run_modal_action(audit.app, frame.show_app_settings, drive)
    finally:
        frame._bindings = original_bindings
    if [caption for caption, _directory in directory_dialog.calls] != [
        "Choose default open folder",
        "Choose default output folder",
    ]:
        raise RuntimeError(
            f"Unexpected settings directory-picker calls: {directory_dialog.calls!r}."
        )
    persisted = settings_store.load_settings()
    if (
        persisted.default_open_directory != str(open_directory)
        or persisted.default_output_directory != str(output_directory)
        or frame.app_settings != persisted
    ):
        raise RuntimeError("Application settings did not persist selected directory paths.")
    audit.checkpoint("settings-directory-browsing", "Step 2 of 6 — Configure application folders")


def _save_appearance_profile(shell: Any, audit: _Audit) -> None:
    """Persist the appearance before placement through the visible refinement dialog."""
    saved = False

    def drive(app: Any) -> bool:
        nonlocal saved
        modal = _active_modal(app, "Refine current PDF setup")
        if modal is None:
            return False
        if not saved:
            _schedule_input_dialog_accept(
                app,
                title="Save appearance profile",
                value=AUDIT_APPEARANCE_PROFILE,
            )
            _button_with_text(modal, "Save appearance for reuse...").click()
            saved = True
            return False
        _button_with_text(modal, "Apply").click()
        return True

    _open_refinement_from_visible_control(shell, audit, drive)


def _save_and_reselect_signature_preset(
    shell: Any,
    audit: _Audit,
    *,
    expected_certificate_name: str,
) -> None:
    """Persist placement and a composed preset through the real refinement dialog.

    This deliberately drives the same nested input dialogs a person sees.  It is
    stronger than directly writing the profile store: a missing signal refresh or
    a broken component-to-preset composition is caught before signing begins.
    """
    phase = "placement-button"

    def drive(app: Any) -> bool:
        nonlocal phase
        modal = _active_modal(app, "Refine current PDF setup")
        if modal is None:
            for title in (
                "Save placement profile",
                "Save signature preset",
            ):
                modal = _active_modal(app, title)
                if modal is not None:
                    break
        if modal is None:
            return False
        title = modal.windowTitle()
        if title == "Refine current PDF setup":
            if phase == "placement-button":
                if _combo_with_item(modal, AUDIT_APPEARANCE_PROFILE) is None:
                    raise RuntimeError(
                        "Saved appearance profile was not refreshed into the dialog."
                    )
                _schedule_input_dialog_accept(
                    app,
                    title="Save placement profile",
                    value=AUDIT_PLACEMENT_PROFILE,
                )
                _button_with_text(modal, "Save placement for reuse...").click()
                phase = "preset-button"
            elif phase == "preset-button":
                appearance_combo = _combo_with_item(modal, AUDIT_APPEARANCE_PROFILE)
                placement_combo = _combo_with_item(modal, AUDIT_PLACEMENT_PROFILE)
                if placement_combo is None:
                    raise RuntimeError(
                        "Saved placement profile was not refreshed into the dialog."
                    )
                if appearance_combo is None:
                    raise RuntimeError(
                        "Saved appearance profile was not available for preset composition."
                    )
                appearance_combo.setCurrentText(AUDIT_APPEARANCE_PROFILE)
                placement_combo.setCurrentText(AUDIT_PLACEMENT_PROFILE)
                _schedule_input_dialog_accept(
                    app,
                    title="Save signature preset",
                    value=AUDIT_SIGNATURE_PRESET,
                )
                _button_with_text(modal, "Save signature preset for reuse...").click()
                phase = "accept"
            elif phase == "accept":
                _button_with_text(modal, "Apply").click()
                phase = "done"
                return True
            return False
        return False

    _open_refinement_from_visible_control(shell, audit, drive)
    preset_combo = _combo_with_item(shell, AUDIT_SIGNATURE_PRESET)
    if preset_combo is None:
        raise RuntimeError("Saved signature preset was not refreshed into the workspace selector.")
    preset_combo.setCurrentText(AUDIT_SIGNATURE_PRESET)
    if preset_combo.currentText() != AUDIT_SIGNATURE_PRESET:
        raise RuntimeError(
            "Saved signature preset could not be reselected through the workspace selector."
        )
    certificate_combo = _combo_with_item(shell, expected_certificate_name)
    if certificate_combo is None or certificate_combo.currentText() != expected_certificate_name:
        raise RuntimeError(
            "Reselecting a signature preset changed the active certificate configuration."
        )


def _open_refinement_from_visible_control(
    shell: Any,
    audit: _Audit,
    driver: Callable[[Any], bool],
) -> None:
    """Open refinement by clicking FoliaSeal's mounted control, not a panel method."""
    button = _visible_button_with_text(shell, "Refine current setup...")
    _run_modal_action(audit.app, button.click, driver)


def _visible_button_with_text(root: Any, text: str) -> Any:
    from PySide6.QtWidgets import QPushButton

    for button in root.findChildren(QPushButton):
        if button.text().strip() != text:
            continue
        is_visible = getattr(button, "isVisible", None)
        if not callable(is_visible) or is_visible():
            return button
    raise RuntimeError(f"Could not find visible button {text!r} in the mounted shell.")


def _combo_with_item(root: Any, text: str) -> Any | None:
    """Return a visible Qt combo which exposes the expected persisted item."""
    from PySide6.QtWidgets import QComboBox

    for combo in root.findChildren(QComboBox):
        is_visible = getattr(combo, "isVisible", None)
        if callable(is_visible) and not is_visible():
            continue
        if combo.findText(text) >= 0:
            return combo
    return None


def _sidebar_button(shell: Any, attribute: str, *, label: str) -> Any:
    """Return one mounted, visible sidebar control rather than a shell port verb."""
    surface = getattr(shell, "sidebar_surface", None)
    button = getattr(surface, attribute, None)
    if button is None:
        raise RuntimeError(f"The mounted sidebar has no {label!r} control.")
    is_visible = getattr(button, "isVisible", None)
    if callable(is_visible) and not is_visible():
        raise RuntimeError(f"The {label!r} control is not visible to the audit.")
    return button


def _place_signature_with_viewer_drag(
    shell: Any,
    audit: _Audit,
    *,
    start: tuple[int, int] | None = None,
    end: tuple[int, int] | None = None,
) -> None:
    """Place a signature by sending real Qt mouse events to the visible PDF canvas."""
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    viewer = shell.viewer_widget
    canvas = viewer.widget()
    if canvas.width() < 220 or canvas.height() < 220:
        raise RuntimeError("PDF canvas is not large enough for a visible placement drag.")
    # These are canvas-local coordinates, intentionally away from page margins
    # and use Qt's own event dispatch rather than X11 coordinates.
    start_point = QPoint(*(start or (35, 35)))
    end_point = QPoint(*(end or (canvas.width() - 35, canvas.height() - 35)))
    if not (0 <= start_point.x() < end_point.x() <= canvas.width()):
        raise RuntimeError("Signature placement drag does not fit horizontally in the PDF canvas.")
    if not (0 <= start_point.y() < end_point.y() <= canvas.height()):
        raise RuntimeError("Signature placement drag does not fit vertically in the PDF canvas.")
    QTest.mousePress(
        canvas,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start_point,
    )
    QTest.mouseMove(canvas, end_point, delay=30)
    QTest.mouseRelease(
        canvas,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        end_point,
    )
    audit.process_events()
    if shell.signature_rect() is None:
        raise RuntimeError("Visible PDF-canvas drag did not create a signature placement.")
    _assert_on_page_preview(shell, require_signature_overlay=True)


def _assert_on_page_preview(
    shell: Any,
    *,
    require_signature_overlay: bool = False,
    require_visible_signed_content: bool = False,
) -> None:
    """Assert that the mounted PDF canvas contains a rendered page.

    This validates the actual Qt presentation surface, not merely the workflow
    state.  Reopen used to be able to mount a fresh workspace without a canvas
    render, so a valid document-backed pixmap whose bounds match the painted
    widget is required.  The representative sweep fixture is intentionally
    white, so document-content colour is *not* a valid rendered-page test.
    When placement is requested, require the live overlay geometry as well.
    """
    canvas = shell.viewer_widget.widget()
    pixmap = getattr(canvas, "_pixmap", None)
    is_null = getattr(pixmap, "isNull", None)
    if pixmap is None or (callable(is_null) and is_null()):
        raise RuntimeError("Mounted PDF canvas has no rendered page pixmap.")
    width, height = pixmap.width(), pixmap.height()
    if width <= 0 or height <= 0:
        raise RuntimeError("Mounted PDF canvas pixmap has no image bounds.")
    if canvas.width() != width or canvas.height() != height:
        raise RuntimeError(
            "Mounted PDF canvas dimensions do not match its rendered page pixmap."
        )
    if require_signature_overlay:
        overlay_rect = canvas._current_overlay_qrect()
        if overlay_rect is None or not overlay_rect.normalized().isValid():
            raise RuntimeError("Visible signature placement did not render an on-page overlay.")
    if require_visible_signed_content and not _canvas_has_visible_ink(canvas):
        raise RuntimeError(
            "Reopened signed-PDF Qt canvas did not paint the visible signature appearance."
        )


def _canvas_has_visible_ink(canvas: Any) -> bool:
    """Return whether the painted canvas has non-white content at any sampled pixel.

    The source fixture is deliberately blank, so this is only meaningful after
    signing: the output must expose its required visible signature appearance.
    Sampling every second pixel is enough to observe its two-pixel border while
    keeping the audit responsive on a high-DPI page.
    """
    image = canvas.grab().toImage()
    for y in range(0, image.height(), 2):
        for x in range(0, image.width(), 2):
            color = image.pixelColor(x, y)
            if min(color.red(), color.green(), color.blue()) < 245:
                return True
    return False


def _choose_output_path(shell: Any, audit: _Audit, output_path: Path) -> None:
    """Select an output via the production action and a real non-native dialog.

    The bridge's file-dialog binding is deliberately injected, so this invokes
    the same production ``choose_output_pdf_path`` method and exercises its
    post-selection workflow update.  Only the platform-native static helper is
    replaced: it cannot be driven reliably inside an unattended Qt test loop.
    """
    # Production installs the port verbs directly on the close-aware QWidget,
    # so the widget itself intentionally does not expose composition internals.
    # Recover the real shell surface from the installed bound method rather than
    # reaching through a compatibility-only widget attribute.
    surface = getattr(shell.choose_output_pdf_path, "__self__", None)
    bridge = getattr(surface, "_action_bridge", None)
    if bridge is None:
        raise RuntimeError("Could not resolve the production signing-action bridge.")
    original_bindings = bridge._bindings
    dialog = _NonNativeAuditSaveDialog(output_path=output_path, calls=[])
    bridge._bindings = replace(original_bindings, q_file_dialog=dialog)
    try:
        button = _sidebar_button(
            shell,
            "choose_output_button",
            label="Choose output...",
        )
        button.click()
    finally:
        bridge._bindings = original_bindings
    if len(dialog.calls) != 1:
        raise RuntimeError(f"Expected one output-dialog invocation, found {len(dialog.calls)}.")
    selected = str(bridge._draft_workflow.output_pdf_path)
    if selected != str(output_path):
        raise RuntimeError(f"Output chooser selected {selected!r}, not {str(output_path)!r}.")


def _accept_confirm_signing_with_assertion(app: Any, expected_output: Path) -> bool:
    """Assert the visible confirmation summary before accepting the real dialog."""
    from PySide6.QtWidgets import QMessageBox

    modal = app.activeModalWidget()
    if not isinstance(modal, QMessageBox) or modal.windowTitle() != "Confirm signing":
        return False
    text = modal.text()
    for expected in (
        str(expected_output),
        AUDIT_CERTIFICATE_NAME,
        AUDIT_SIGNATURE_PRESET,
        "Readiness:",
    ):
        if expected not in text:
            raise RuntimeError(f"Confirmation dialog omitted expected summary text: {expected!r}.")
    button = modal.button(QMessageBox.StandardButton.Yes)
    if button is None:
        raise RuntimeError("Confirm signing dialog did not provide a Yes button.")
    button.click()
    return True


def _sign_current_shell(
    frame: Any,
    shell: Any,
    audit: _Audit,
    output_path: Path,
    *,
    checkpoint_prefix: str,
) -> Path:
    """Choose output, confirm, and sign the currently mounted workspace."""
    _choose_output_path(shell, audit, output_path)
    audit.checkpoint(f"{checkpoint_prefix}-output-selected", "Step 5 of 6 — Confirm and sign")
    if not frame.current_shell.is_sign_action_enabled():
        raise RuntimeError(f"{checkpoint_prefix} sign action remained disabled.")
    audit.checkpoint(f"{checkpoint_prefix}-ready-to-sign", "Step 5 of 6 — Confirm and sign")
    sign_button = _sidebar_button(shell, "sign_button", label="Confirm and sign")
    if not sign_button.isEnabled():
        raise RuntimeError(f"{checkpoint_prefix} Confirm and sign control is disabled.")
    _run_modal_action(
        audit.app,
        sign_button.click,
        lambda app: _accept_confirm_signing_with_assertion(app, output_path),
    )
    audit.process_events()
    actual_output = Path(frame.current_signing_workflow.output_pdf_path)
    if not actual_output.is_file():
        raise RuntimeError(f"{checkpoint_prefix} signing did not create {actual_output}.")
    audit.checkpoint(f"{checkpoint_prefix}-signed", "Step 6 of 6 — Verify signed PDF")
    return actual_output


def _assert_two_signature_review(shell: Any, signed_output: Path) -> None:
    """Assert two locally verified review items in both model and mounted Qt UI."""
    from PySide6.QtWidgets import QLabel

    from foliaseal.application.document_review import PyHankoDocumentReviewInspector

    review = PyHankoDocumentReviewInspector().inspect(str(signed_output))
    if review.signature_count != 2 or len(review.signature_items) != 2:
        raise RuntimeError(
            f"Expected two signature review items, got {review.signature_count!r}."
        )
    if [item.label for item in review.signature_items] != [
        "Signature 1",
        "Signature 2 (latest)",
    ]:
        raise RuntimeError("Two-signature review labels were not stable.")
    if not all(item.cryptographic_validation_passed is True for item in review.signature_items):
        raise RuntimeError("Both signature review items must verify locally.")
    selector = getattr(
        getattr(shell, "sidebar_surface", None),
        "document_review_signature_selector",
        None,
    )
    if selector is None or selector.count() != 2:
        raise RuntimeError("Mounted review selector did not expose two signatures.")
    expected_labels = ("Signature 1", "Signature 2 (latest)")
    for index, expected_label in enumerate(expected_labels):
        selector.setCurrentIndex(index)
        if selector.currentText() != expected_label:
            raise RuntimeError(
                f"Mounted review selector item {index} was {selector.currentText()!r}."
            )
    review_text = "\n".join(label.text() for label in shell.findChildren(QLabel)).lower()
    if "signature 1" not in review_text or "signature 2" not in review_text:
        raise RuntimeError("Mounted review surface did not render both signature labels.")


def _signature_rects_overlap(first: Any, second: Any) -> bool:
    if first.page_index != second.page_index:
        return False
    return not (
        first.left_pt + first.width_pt <= second.left_pt
        or second.left_pt + second.width_pt <= first.left_pt
        or first.bottom_pt + first.height_pt <= second.bottom_pt
        or second.bottom_pt + second.height_pt <= first.bottom_pt
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF, help="Representative source PDF.")
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("/tmp/foliaseal-live-gui-parent-audit"),
        help="Directory for screenshots and audit.json (default: %(default)s).",
    )
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Keep isolated temporary input/config files.",
    )
    return parser.parse_args(argv)


def run_audit(
    pdf_path: Path, artifact_dir: Path, *, keep_workspace: bool = False
) -> dict[str, Any]:
    """Execute the full parent-plan audit and return its evidence manifest."""
    from PySide6.QtWidgets import QApplication

    pdf_path = pdf_path.resolve()
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Representative PDF does not exist: {pdf_path}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="foliaseal-live-gui-audit-")
    root = Path(temporary.name)
    app = QApplication.instance() or QApplication(["foliaseal-live-gui-parent-audit"])
    frame: Any | None = None
    audit: _Audit | None = None
    try:
        input_pdf = root / "input.pdf"
        shutil.copy2(pdf_path, input_pdf)
        cert_store = CertificateCatalogStore(storage_dir=root / "data" / "Certificates")
        profile_store = SignaturePresetCatalogStore(
            storage_dir=root / "data" / "Signature Profiles"
        )
        settings_store = AppSettingsStore(storage_dir=root / "config", default_home_directory=root)
        frame = build_qt_app_frame_host(
            app_settings_store=settings_store,
            certificate_catalog_store=cert_store,
            certificate_secret_provider=_InMemorySecretStore(),
            preset_catalog_store=profile_store,
            sign_executor=build_signing_executor(),
        )
        frame.window.resize(1440, 980)
        frame.window.show()
        audit = _Audit(app=app, window=frame.window, artifact_dir=artifact_dir, checkpoints=[])
        audit.process_events()

        shell = frame.open_pdf_path(input_pdf)
        if shell is None:
            raise RuntimeError("FoliaSeal did not open the representative PDF.")
        audit.checkpoint("document-review", "Step 2 of 6 — Choose signing setup")
        _audit_preset_first_shell(shell, audit)
        _audit_certificate_and_preset_clarity(shell, audit)
        _audit_settings_directory_browsing(
            frame,
            audit,
            root=root,
            settings_store=settings_store,
        )

        creation = _create_managed_certificate(frame, audit)
        catalog = cert_store.load_catalog()
        if len(catalog.certificate_configurations) != 1:
            raise RuntimeError(
                "Managed certificate creation did not persist exactly one configuration."
            )
        config = catalog.certificate_configurations[0]
        _select_certificate_configuration(shell, config.display_name)
        audit.process_events()
        _save_appearance_profile(shell, audit)
        audit.process_events()
        audit.checkpoint("appearance-profile-saved", "Step 3 of 6 — Place visible signature")

        canvas = shell.viewer_widget.widget()
        if canvas.height() < 520:
            raise RuntimeError("PDF canvas is not tall enough for two audit signature regions.")
        _place_signature_with_viewer_drag(
            shell,
            audit,
            start=(35, 35),
            end=(canvas.width() - 35, 220),
        )
        first_signature_rect = shell.signature_rect()
        if first_signature_rect is None:
            raise RuntimeError("First audit signature placement did not expose a rectangle.")
        _save_and_reselect_signature_preset(
            shell,
            audit,
            expected_certificate_name=config.display_name,
        )
        _audit_profile_library(frame, audit)
        audit.process_events()
        audit.checkpoint("saved-profile-reselected", "Step 4 of 6 — Review readiness")
        audit.checkpoint("visible-placement", "Step 4 of 6 — Review readiness")
        # The normal app starts with timestamping disabled but still requires a
        # syntactically valid endpoint in its request DTO.  Keep it disabled so
        # this offline GUI audit never calls a network TSA.
        frame.current_signing_workflow.tsa_url = "https://tsa.example.invalid"
        frame.current_signing_workflow.timestamp_required = False
        audit.process_events()
        selected_output = root / "chosen-signed-output.pdf"
        _choose_output_path(shell, audit, selected_output)
        audit.checkpoint("output-selected", "Step 5 of 6 — Confirm and sign")
        if not frame.current_shell.is_sign_action_enabled():
            workflow = frame.current_signing_workflow
            raise RuntimeError(
                "Sign action remained disabled after certificate setup and placement "
                f"(certificate_path={workflow.certificate_path!r}, "
                f"passphrase_present={bool(workflow.passphrase)}, "
                f"appearance_present={workflow.signature_appearance is not None}, "
                f"rect_present={workflow.signature_rect is not None}, "
                f"issues={[issue.message for issue in workflow.validation_issues()]})."
            )
        audit.checkpoint("ready-to-sign", "Step 5 of 6 — Confirm and sign")

        # The confirmation message box is real; accept it only by its semantic
        # standard button, then let the real signing executor produce the PDF.
        sign_button = _sidebar_button(
            shell,
            "sign_button",
            label="Confirm and sign",
        )
        if not sign_button.isEnabled():
            raise RuntimeError("Visible Confirm and sign control is disabled despite ready state.")
        _run_modal_action(
            audit.app,
            sign_button.click,
            lambda app: _accept_confirm_signing_with_assertion(app, selected_output),
        )
        audit.process_events()
        output_path = Path(frame.current_signing_workflow.output_pdf_path)
        if not output_path.is_file():
            raise RuntimeError(f"Signing did not create the expected output: {output_path}")
        audit.checkpoint("signed", "Step 6 of 6 — Verify signed PDF")

        open_signed_output_button = _sidebar_button(
            shell,
            "open_signed_output_button",
            label="Open signed PDF",
        )
        if not open_signed_output_button.isEnabled():
            raise RuntimeError("Visible Open signed PDF control was not enabled after signing.")
        open_signed_output_button.click()
        audit.process_events()
        reopened_shell = frame.current_shell
        if reopened_shell is shell:
            raise RuntimeError("Open signed output did not mount a fresh signed-PDF workspace.")
        if Path(frame.current_signing_workflow.input_pdf_path) != output_path:
            raise RuntimeError("Reopened workspace is not bound to the signed output path.")
        # Reopening replaces the central widget synchronously.  Force and
        # inspect one refresh here so a blank post-reopen page cannot be
        # mistaken for a successful verification-only sidebar update.
        reopened_shell.refresh_viewer()
        audit.process_events()
        audit.checkpoint(
            "reopened-before-visual-fidelity-check",
            "Signed PDF reopened before visible-appearance verification",
        )
        _assert_on_page_preview(reopened_shell, require_visible_signed_content=True)
        from PySide6.QtWidgets import QLabel

        review_text = "\n".join(
            label.text()
            for label in reopened_shell.findChildren(QLabel)
        ).lower()
        if "signature" not in review_text:
            raise RuntimeError(
                "Reopened signed-PDF workspace did not render signature verification review."
            )
        audit.checkpoint("reopened-and-verified", "Signed PDF reopened and verification reviewed")

        retained_first_output = artifact_dir / "first-signed-output.pdf"
        first_output_bytes = output_path.read_bytes()
        shutil.copy2(output_path, retained_first_output)

        _select_certificate_configuration(reopened_shell, config.display_name)
        preset_combo = _combo_with_item(reopened_shell, AUDIT_SIGNATURE_PRESET)
        if preset_combo is None:
            raise RuntimeError("Reopened workspace did not expose the stored signature preset.")
        preset_combo.setCurrentText(AUDIT_SIGNATURE_PRESET)
        frame.current_signing_workflow.tsa_url = "https://tsa.example.invalid"
        frame.current_signing_workflow.timestamp_required = False
        audit.process_events()
        second_canvas = reopened_shell.viewer_widget.widget()
        second_start = (35, second_canvas.height() - 220)
        second_end = (second_canvas.width() - 35, second_canvas.height() - 35)
        _place_signature_with_viewer_drag(
            reopened_shell,
            audit,
            start=second_start,
            end=second_end,
        )
        second_signature_rect = reopened_shell.signature_rect()
        if second_signature_rect is None:
            raise RuntimeError("Second audit signature placement did not expose a rectangle.")
        if _signature_rects_overlap(first_signature_rect, second_signature_rect):
            raise RuntimeError("Second audit signature rectangle overlaps the first signature.")
        audit.checkpoint("second-placement", "Step 4 of 6 — Review readiness")

        second_output = root / "second-chosen-signed-output.pdf"
        second_output_path = _sign_current_shell(
            frame,
            reopened_shell,
            audit,
            second_output,
            checkpoint_prefix="second-signature",
        )
        if output_path.read_bytes() != first_output_bytes:
            raise RuntimeError("The first signed output changed during the second signing.")

        second_open_button = _sidebar_button(
            reopened_shell,
            "open_signed_output_button",
            label="Open signed PDF",
        )
        if not second_open_button.isEnabled():
            raise RuntimeError("Open signed PDF was not enabled after the second signature.")
        second_open_button.click()
        audit.process_events()
        final_shell = frame.current_shell
        if final_shell is reopened_shell:
            raise RuntimeError("Second signed output did not mount a fresh workspace.")
        final_shell.refresh_viewer()
        audit.process_events()
        _assert_on_page_preview(final_shell, require_visible_signed_content=True)
        _assert_two_signature_review(final_shell, second_output_path)
        audit.checkpoint(
            "reopened-two-signatures",
            "Signed PDF reopened with two locally verified signatures",
        )

        retained_output = artifact_dir / "signed-output.pdf"
        shutil.copy2(second_output_path, retained_output)
        retained_second_output = artifact_dir / "second-signed-output.pdf"
        shutil.copy2(second_output_path, retained_second_output)

        report = {
            "status": "passed",
            "source_pdf": str(pdf_path),
            "signed_output": str(retained_output),
            "first_signed_output": str(retained_first_output),
            "second_signed_output": str(retained_second_output),
            "output_signature_count": 2,
            "certificate_configuration": creation.certificate_configuration.display_name,
            "checkpoints": audit.checkpoints,
            "isolated_workspace": str(root),
        }
        (artifact_dir / "audit.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report
    except Exception as exc:
        failure_report = {
            "status": "failed",
            "source_pdf": str(pdf_path),
            "failure": str(exc),
            "checkpoints": [] if audit is None else audit.checkpoints,
            "isolated_workspace": str(root),
        }
        (artifact_dir / "audit.json").write_text(
            json.dumps(failure_report, indent=2) + "\n", encoding="utf-8"
        )
        raise
    finally:
        # Close frame-owned and modal windows even on failures.  This avoids the
        # unattended FoliaSeal/dialog processes that coordinate-driven audit left.
        for widget in list(app.topLevelWidgets()):
            widget.close()
        app.processEvents()
        if keep_workspace:
            # TemporaryDirectory only cleans up on explicit cleanup or object
            # finalization.  Detach it so a retained diagnostic workspace is
            # intentional rather than an accidental leak.
            print(f"Isolated audit workspace retained: {root}", file=sys.stderr)
            temporary._finalizer.detach()  # type: ignore[attr-defined]
        else:
            temporary.cleanup()


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    try:
        report = run_audit(args.pdf, args.artifacts_dir, keep_workspace=args.keep_workspace)
    except Exception as exc:
        print(f"Live GUI parent audit failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
