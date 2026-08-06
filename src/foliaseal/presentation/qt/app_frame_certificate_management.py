"""Certificate dialog orchestration for the Qt app frame."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import (
    CertificateManager,
    CreateCertificateRequest,
    ExportCertificateRequest,
    ImportCertificateRequest,
    SaveConfigurationRequest,
)
from foliaseal.application.certificate_models import CertificateConfiguration, ManagedCertificate


def _accepted_dialog_code(bindings: Any) -> Any:
    accepted = getattr(bindings.q_dialog, "Accepted", None)
    if accepted is not None:
        return accepted
    dialog_code = getattr(bindings.q_dialog, "DialogCode", None)
    accepted = getattr(dialog_code, "Accepted", None)
    if accepted is not None:
        return accepted
    return 1


@dataclass(frozen=True)
class CertificateImportDialogControls:
    """Controls used by the certificate import dialog."""

    dialog: Any
    certificate_path: Any
    display_name: Any
    passphrase: Any
    save_password: Any
    choose_button: Any
    import_button: Any
    cancel_button: Any


@dataclass(frozen=True)
class CertificateCreationDialogControls:
    """Controls used by the certificate creation dialog."""

    dialog: Any
    display_name: Any
    passphrase: Any
    save_password: Any
    create_button: Any
    cancel_button: Any


@dataclass(frozen=True)
class CertificateConfigurationManagementDialogControls:
    """Controls used by the certificate-configuration management dialog."""

    dialog: Any
    introduction_label: Any
    configuration_selector: Any
    configuration_helper_label: Any
    display_name: Any
    notes: Any
    managed_certificate_selector: Any
    managed_certificate_helper_label: Any
    save_button: Any
    delete_button: Any
    export_certificate_button: Any
    delete_certificate_button: Any
    cancel_button: Any


@dataclass(frozen=True)
class CertificateDialogCompatibilityState:
    """Explicit dialog exposure retained for tests and compatibility callers."""

    import_dialog: Any | None = None
    creation_dialog: Any | None = None
    management_dialog: Any | None = None


@dataclass(frozen=True)
class CertificateDialogOutcome:
    """Result plus explicit dialog exposure for the app frame."""

    result: Any | None
    compatibility: CertificateDialogCompatibilityState


class CertificateDialogPort(Protocol):
    """App-frame-facing certificate dialog surface."""

    def show_import_dialog(self) -> CertificateDialogOutcome: ...

    def show_creation_dialog(self) -> CertificateDialogOutcome: ...

    def show_management_dialog(self) -> CertificateDialogOutcome: ...


class CertificateImportDialog:
    """Small dialog for importing an existing PKCS#12 certificate."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        certificate_manager: CertificateManager,
        on_import: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._certificate_manager = certificate_manager
        self._on_import = on_import
        self.import_result = None
        self.controls = self._build_controls(parent=parent)

    def exec(self) -> Any | None:
        dialog_exec = getattr(self.controls.dialog, "exec", None)
        if callable(dialog_exec):
            result = dialog_exec()
            if result != _accepted_dialog_code(self._bindings):
                return None
        return self.import_result

    def choose_certificate_file(self) -> str | None:
        selected = self._bindings.q_file_dialog.getOpenFileName(
            self.controls.dialog,
            "Import certificate",
            "",
            "PKCS#12 files (*.p12 *.pfx);;All files (*)",
        )
        selected_path = str(selected[0] if isinstance(selected, tuple) else selected).strip()
        if not selected_path:
            return None
        self.controls.certificate_path.setText(selected_path)
        if not self.controls.display_name.text().strip():
            self.controls.display_name.setText(Path(selected_path).stem)
        return selected_path

    def import_certificate(self) -> Any | None:
        source_path = self.controls.certificate_path.text().strip()
        display_name = self.controls.display_name.text().strip() or Path(source_path).stem
        passphrase = self.controls.passphrase.text()
        save_password = bool(self.controls.save_password.isChecked())
        try:
            result = self._certificate_manager.import_(
                ImportCertificateRequest(
                    source_path=source_path,
                    display_name=display_name,
                    passphrase=passphrase,
                    save_password=save_password,
                )
            )
        except Exception as exc:
            self._show_error(str(exc))
            return None

        self.import_result = result
        if result.operation != "exported" and self._on_import is not None:
            self._on_import()
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(
                self.controls.dialog,
                "Certificate imported",
                "Certificate imported successfully.",
            )
        accept = getattr(self.controls.dialog, "accept", None)
        if callable(accept):
            accept()
        return result

    def cancel(self) -> None:
        reject = getattr(self.controls.dialog, "reject", None)
        if callable(reject):
            reject()

    def _build_controls(self, *, parent: Any) -> CertificateImportDialogControls:
        dialog = self._bindings.q_dialog(parent)
        if hasattr(dialog, "setWindowTitle"):
            dialog.setWindowTitle("Import certificate")
        layout = self._bindings.q_form_layout(dialog)

        introduction_label = self._bindings.q_label(
            "Import a PKCS#12 file to store it as a managed certificate and "
            "create a reusable certificate configuration for signing."
        )
        introduction_label.setWordWrap(True)
        certificate_path = self._bindings.q_line_edit("")
        display_name = self._bindings.q_line_edit("")
        passphrase = self._bindings.q_line_edit("")
        save_password = self._bindings.q_check_box("Save password securely")
        choose_button = self._bindings.q_push_button("Choose...")
        import_button = self._bindings.q_push_button("Import")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("", introduction_label)
        layout.addRow("PKCS#12 file", certificate_path)
        layout.addRow("", choose_button)
        layout.addRow("Display name", display_name)
        layout.addRow("Password", passphrase)
        layout.addRow("", save_password)
        layout.addRow("", import_button)
        layout.addRow("", cancel_button)

        choose_button.clicked.connect(self.choose_certificate_file)  # type: ignore[attr-defined]
        import_button.clicked.connect(self.import_certificate)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.cancel)  # type: ignore[attr-defined]

        return CertificateImportDialogControls(
            dialog=dialog,
            certificate_path=certificate_path,
            display_name=display_name,
            passphrase=passphrase,
            save_password=save_password,
            choose_button=choose_button,
            import_button=import_button,
            cancel_button=cancel_button,
        )

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Certificate import error", message)


class CertificateCreationDialog:
    """Small dialog for creating a self-signed managed certificate."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        certificate_manager: CertificateManager,
        on_create: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._certificate_manager = certificate_manager
        self._on_create = on_create
        self.creation_result = None
        self.controls = self._build_controls(parent=parent)

    def exec(self) -> Any | None:
        dialog_exec = getattr(self.controls.dialog, "exec", None)
        if callable(dialog_exec):
            result = dialog_exec()
            if result != _accepted_dialog_code(self._bindings):
                return None
        return self.creation_result

    def create_certificate(self) -> Any | None:
        display_name = self.controls.display_name.text().strip()
        passphrase = self.controls.passphrase.text()
        save_password = bool(self.controls.save_password.isChecked())
        try:
            result = self._certificate_manager.create(
                CreateCertificateRequest(
                    display_name=display_name,
                    passphrase=passphrase,
                    save_password=save_password,
                )
            )
        except Exception as exc:
            self._show_error(str(exc))
            return None

        self.creation_result = result
        if result.operation != "exported" and self._on_create is not None:
            self._on_create()
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(
                self.controls.dialog,
                "Certificate created",
                "Certificate created successfully.",
            )
        accept = getattr(self.controls.dialog, "accept", None)
        if callable(accept):
            accept()
        return result

    def cancel(self) -> None:
        reject = getattr(self.controls.dialog, "reject", None)
        if callable(reject):
            reject()

    def _build_controls(self, *, parent: Any) -> CertificateCreationDialogControls:
        dialog = self._bindings.q_dialog(parent)
        if hasattr(dialog, "setWindowTitle"):
            dialog.setWindowTitle("Create certificate")
        layout = self._bindings.q_form_layout(dialog)

        introduction_label = self._bindings.q_label(
            "Create a managed certificate and a matching certificate "
            "configuration for the main signing workflow."
        )
        introduction_label.setWordWrap(True)
        display_name = self._bindings.q_line_edit("")
        passphrase = self._bindings.q_line_edit("")
        save_password = self._bindings.q_check_box("Save password securely")
        create_button = self._bindings.q_push_button("Create")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("", introduction_label)
        layout.addRow("Display name", display_name)
        layout.addRow("Password", passphrase)
        layout.addRow("", save_password)
        layout.addRow(create_button, cancel_button)

        create_button.clicked.connect(self.create_certificate)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.cancel)  # type: ignore[attr-defined]

        return CertificateCreationDialogControls(
            dialog=dialog,
            display_name=display_name,
            passphrase=passphrase,
            save_password=save_password,
            create_button=create_button,
            cancel_button=cancel_button,
        )

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Certificate creation error", message)


class CertificateConfigurationManagementDialog:
    """Small dialog for renaming, annotating, and deleting configurations."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        certificate_manager: CertificateManager,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._certificate_manager = certificate_manager
        self._on_change = on_change
        self._configurations_by_id: dict[str, CertificateConfiguration] = {}
        self._managed_certificates_by_id: dict[str, ManagedCertificate] = {}
        self.controls = self._build_controls(parent=parent)
        self.reload_configurations()

    def exec(self) -> Any | None:
        dialog_exec = getattr(self.controls.dialog, "exec", None)
        if callable(dialog_exec):
            return dialog_exec()
        return None

    def reload_configurations(self) -> None:
        catalog = self._certificate_manager.snapshot()
        configurations = catalog.certificate_configurations
        managed_certificates = catalog.managed_certificates
        self._configurations_by_id = {
            configuration.certificate_configuration_id: configuration
            for configuration in configurations
        }
        self._managed_certificates_by_id = {
            certificate.managed_certificate_id: certificate
            for certificate in managed_certificates
        }
        selector = self.controls.configuration_selector
        clear = getattr(selector, "clear", None)
        if callable(clear):
            clear()
        for configuration in configurations:
            self._add_selector_item(
                configuration.display_name,
                configuration.certificate_configuration_id,
            )
        certificate_selector = self.controls.managed_certificate_selector
        clear_certificates = getattr(certificate_selector, "clear", None)
        if callable(clear_certificates):
            clear_certificates()
        for certificate in managed_certificates:
            self._add_certificate_selector_item(
                certificate.display_name,
                certificate.managed_certificate_id,
            )
        self.controls.configuration_helper_label.setText(
            "Certificate configurations are the saved signing identities shown "
            "in the main window."
            if configurations
            else "No certificate configurations yet. Create or import a "
            "certificate to make one available for signing."
        )
        self.controls.managed_certificate_helper_label.setText(
            "Managed certificates are the stored certificate files used by "
            "those configurations."
            if managed_certificates
            else "No managed certificates are stored yet. Import or create one "
            "to back a certificate configuration."
        )
        self.load_selected_configuration()

    def load_selected_configuration(self, *_args: Any) -> CertificateConfiguration | None:
        configuration_id = self._selected_configuration_id()
        configuration = (
            self._configurations_by_id.get(configuration_id)
            if configuration_id is not None
            else None
        )
        if configuration is None:
            self.controls.display_name.setText("")
            self.controls.notes.setText("")
            return None
        self.controls.display_name.setText(configuration.display_name)
        self.controls.notes.setText(configuration.notes or "")
        return configuration

    def save_selected_configuration(self) -> CertificateConfiguration | None:
        configuration_id = self._selected_configuration_id()
        configuration = (
            self._configurations_by_id.get(configuration_id)
            if configuration_id is not None
            else None
        )
        if configuration is None:
            self._show_error("Select a certificate configuration to save.")
            return None
        try:
            result = self._certificate_manager.save_configuration(
                SaveConfigurationRequest(
                    configuration_id=configuration.certificate_configuration_id,
                    display_name=self.controls.display_name.text(),
                    notes=self.controls.notes.text(),
                )
            )
        except Exception as exc:
            self._show_error(str(exc))
            return None

        self.reload_configurations()
        updated = result.certificate_configuration
        if updated is None:
            self._show_error("Certificate configuration was not saved.")
            return None
        self._select_configuration(updated.certificate_configuration_id)
        self.load_selected_configuration()
        self._emit_changed_if_needed(result.operation != "exported")
        self._show_information("Certificate configuration saved.")
        return updated

    def delete_selected_configuration(self) -> bool:
        configuration_id = self._selected_configuration_id()
        if configuration_id is None:
            self._show_error("Select a certificate configuration to delete.")
            return False
        configuration = self._configurations_by_id.get(configuration_id)
        if configuration is None:
            self._show_error("Select a certificate configuration to delete.")
            self.reload_configurations()
            return False
        try:
            result = self._certificate_manager.delete_configuration(configuration_id)
        except Exception as exc:
            self._show_error(str(exc))
            self.reload_configurations()
            return False

        self.reload_configurations()
        self._emit_changed_if_needed(result.operation != "exported")
        self._show_information("Certificate configuration deleted.")
        return True

    def delete_selected_managed_certificate(self) -> bool:
        certificate_id = self._selected_managed_certificate_id()
        if certificate_id is None:
            self._show_error("Select a managed certificate to delete.")
            return False
        try:
            result = self._certificate_manager.delete_managed_certificate(certificate_id)
        except Exception as exc:
            self._show_error(str(exc))
            self.reload_configurations()
            return False

        self.reload_configurations()
        self._emit_changed_if_needed(result.operation != "exported")
        self._show_information("Managed certificate deleted.")
        return True

    def export_selected_managed_certificate(self) -> Path | None:
        certificate_id = self._selected_managed_certificate_id()
        if certificate_id is None:
            self._show_error("Select a managed certificate to export.")
            return None
        certificate = self._managed_certificates_by_id.get(certificate_id)
        if certificate is None:
            self._show_error("Select a managed certificate to export.")
            self.reload_configurations()
            return None
        selected = self._bindings.q_file_dialog.getSaveFileName(
            self.controls.dialog,
            "Export managed certificate",
            certificate.storage_filename,
            "PKCS#12 files (*.p12 *.pfx);;All files (*)",
        )
        selected_path = str(selected[0] if isinstance(selected, tuple) else selected).strip()
        if not selected_path:
            return None
        try:
            result = self._certificate_manager.export(
                ExportCertificateRequest(
                    certificate_id=certificate_id,
                    destination_path=selected_path,
                )
            )
        except Exception as exc:
            self._show_error(str(exc))
            self.reload_configurations()
            return None

        self._emit_changed_if_needed(result.operation != "exported")
        self._show_information(f"Managed certificate exported to {result.exported_path}.")
        return result.exported_path

    def cancel(self) -> None:
        reject = getattr(self.controls.dialog, "reject", None)
        if callable(reject):
            reject()

    def _build_controls(
        self,
        *,
        parent: Any,
    ) -> CertificateConfigurationManagementDialogControls:
        dialog = self._bindings.q_dialog(parent)
        if hasattr(dialog, "setWindowTitle"):
            dialog.setWindowTitle("Manage certificate configurations")
        layout = self._bindings.q_form_layout(dialog)

        introduction_label = self._bindings.q_label(
            "Certificate configurations are the reusable signing identities "
            "shown in the main window. Each one points to a managed "
            "certificate stored by the app."
        )
        introduction_label.setWordWrap(True)
        configuration_selector = self._bindings.q_combo_box()
        configuration_helper_label = self._bindings.q_label("")
        configuration_helper_label.setWordWrap(True)
        display_name = self._bindings.q_line_edit("")
        notes = self._bindings.q_line_edit("")
        managed_certificate_selector = self._bindings.q_combo_box()
        managed_certificate_helper_label = self._bindings.q_label("")
        managed_certificate_helper_label.setWordWrap(True)
        save_button = self._bindings.q_push_button("Save")
        delete_button = self._bindings.q_push_button("Delete")
        export_certificate_button = self._bindings.q_push_button("Export certificate")
        delete_certificate_button = self._bindings.q_push_button("Delete certificate")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("", introduction_label)
        layout.addRow("Certificate configuration", configuration_selector)
        layout.addRow("", configuration_helper_label)
        layout.addRow("Display name", display_name)
        layout.addRow("Notes", notes)
        layout.addRow("Managed certificate", managed_certificate_selector)
        layout.addRow("", managed_certificate_helper_label)
        layout.addRow("", save_button)
        layout.addRow("", delete_button)
        layout.addRow("", export_certificate_button)
        layout.addRow("", delete_certificate_button)
        layout.addRow("", cancel_button)

        index_changed = getattr(configuration_selector, "currentIndexChanged", None)
        if hasattr(index_changed, "connect"):
            index_changed.connect(self.load_selected_configuration)
        save_button.clicked.connect(self.save_selected_configuration)  # type: ignore[attr-defined]
        delete_button.clicked.connect(self.delete_selected_configuration)  # type: ignore[attr-defined]
        export_certificate_button.clicked.connect(self.export_selected_managed_certificate)  # type: ignore[attr-defined]
        delete_certificate_button.clicked.connect(self.delete_selected_managed_certificate)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.cancel)  # type: ignore[attr-defined]

        return CertificateConfigurationManagementDialogControls(
            dialog=dialog,
            introduction_label=introduction_label,
            configuration_selector=configuration_selector,
            configuration_helper_label=configuration_helper_label,
            display_name=display_name,
            notes=notes,
            managed_certificate_selector=managed_certificate_selector,
            managed_certificate_helper_label=managed_certificate_helper_label,
            save_button=save_button,
            delete_button=delete_button,
            export_certificate_button=export_certificate_button,
            delete_certificate_button=delete_certificate_button,
            cancel_button=cancel_button,
        )

    def _add_selector_item(self, text: str, configuration_id: str) -> None:
        add_item = getattr(self.controls.configuration_selector, "addItem", None)
        if callable(add_item):
            add_item(text, configuration_id)

    def _add_certificate_selector_item(self, text: str, certificate_id: str) -> None:
        add_item = getattr(self.controls.managed_certificate_selector, "addItem", None)
        if callable(add_item):
            add_item(text, certificate_id)

    def _selected_configuration_id(self) -> str | None:
        selector = self.controls.configuration_selector
        current_data = getattr(selector, "currentData", None)
        if callable(current_data):
            selected = current_data()
            return str(selected) if selected else None
        current_index = getattr(selector, "currentIndex", None)
        item_data = getattr(selector, "itemData", None)
        if callable(current_index) and callable(item_data):
            selected = item_data(current_index())
            return str(selected) if selected else None
        return None

    def _selected_managed_certificate_id(self) -> str | None:
        selector = self.controls.managed_certificate_selector
        current_data = getattr(selector, "currentData", None)
        if callable(current_data):
            selected = current_data()
            return str(selected) if selected else None
        current_index = getattr(selector, "currentIndex", None)
        item_data = getattr(selector, "itemData", None)
        if callable(current_index) and callable(item_data):
            selected = item_data(current_index())
            return str(selected) if selected else None
        return None

    def _select_configuration(self, configuration_id: str) -> None:
        selector = self.controls.configuration_selector
        count = getattr(selector, "count", None)
        item_data = getattr(selector, "itemData", None)
        set_current_index = getattr(selector, "setCurrentIndex", None)
        if not (callable(count) and callable(item_data) and callable(set_current_index)):
            return
        for index in range(count()):
            if item_data(index) == configuration_id:
                set_current_index(index)
                return

    def _emit_changed(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def _emit_changed_if_needed(self, refresh_shell: bool) -> None:
        if refresh_shell:
            self._emit_changed()

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Certificate configuration error", message)

    def _show_information(self, message: str) -> None:
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(self.controls.dialog, "Certificate configuration", message)


class AppFrameCertificateDialogService:
    """Own certificate dialog construction and execution for the app frame."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        certificate_manager: CertificateManager,
        refresh_shell_certificate_configurations: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._parent = parent
        self._certificate_manager = certificate_manager
        self._refresh_shell_certificate_configurations = (
            refresh_shell_certificate_configurations
        )

    def show_import_dialog(self) -> CertificateDialogOutcome:
        dialog = CertificateImportDialog(
            bindings=self._bindings,
            parent=self._parent,
            certificate_manager=self._certificate_manager,
            on_import=self._refresh_shell_certificate_configurations,
        )
        return CertificateDialogOutcome(
            result=dialog.exec(),
            compatibility=CertificateDialogCompatibilityState(import_dialog=dialog),
        )

    def show_creation_dialog(self) -> CertificateDialogOutcome:
        dialog = CertificateCreationDialog(
            bindings=self._bindings,
            parent=self._parent,
            certificate_manager=self._certificate_manager,
            on_create=self._refresh_shell_certificate_configurations,
        )
        return CertificateDialogOutcome(
            result=dialog.exec(),
            compatibility=CertificateDialogCompatibilityState(creation_dialog=dialog),
        )

    def show_management_dialog(self) -> CertificateDialogOutcome:
        dialog = CertificateConfigurationManagementDialog(
            bindings=self._bindings,
            parent=self._parent,
            certificate_manager=self._certificate_manager,
            on_change=self._refresh_shell_certificate_configurations,
        )
        return CertificateDialogOutcome(
            result=dialog.exec(),
            compatibility=CertificateDialogCompatibilityState(management_dialog=dialog),
        )
