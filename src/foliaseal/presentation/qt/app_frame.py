"""Qt application-frame wrapper for the FoliaSeal signing GUI."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import (
    CertificateLifecycleService,
    SigningDraftWorkflow,
    suggest_signed_output_path,
)
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import (
    AppSettings,
    CertificateConfiguration,
    ConfigValidationError,
    ManagedCertificate,
)
from foliaseal.infra.render import QtPdfRenderBackend
from foliaseal.infra.secret_storage import SecretToolCertificateSecretStore
from foliaseal.presentation.qt.signing_shell import (
    SigningRequestExecutor,
    build_qt_signing_shell,
)


class QtAppFrameBindingsUnavailable(RuntimeError):
    """Raised when PySide6 app-frame bindings are unavailable."""


@dataclass(frozen=True)
class QtAppFrameBindings:
    """Dynamically imported PySide6 symbols used by the app frame."""

    q_main_window: type[Any]
    q_dialog: type[Any]
    q_form_layout: type[Any]
    q_label: type[Any]
    q_line_edit: type[Any]
    q_check_box: type[Any]
    q_combo_box: type[Any]
    q_push_button: type[Any]
    q_file_dialog: Any
    q_message_box: Any
    q_action: type[Any]
    q_application: type[Any]
    qpdf_document: type[Any]


@dataclass(frozen=True)
class AppSettingsDialogControls:
    """Controls used by the app-wide settings dialog."""

    dialog: Any
    default_open_directory: Any
    default_output_directory: Any
    save_button: Any
    cancel_button: Any


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
    configuration_selector: Any
    display_name: Any
    notes: Any
    managed_certificate_selector: Any
    save_button: Any
    delete_button: Any
    export_certificate_button: Any
    delete_certificate_button: Any
    cancel_button: Any


class AppSettingsDialog:
    """Small dialog for editing app-wide directory defaults."""

    def __init__(
        self,
        *,
        bindings: QtAppFrameBindings,
        parent: Any,
        settings: AppSettings,
        settings_store: AppSettingsStore,
        on_save: Callable[[AppSettings], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._settings = settings
        self._settings_store = settings_store
        self._on_save = on_save
        self.saved_settings: AppSettings | None = None
        self.controls = self._build_controls(parent=parent)

    def exec(self) -> AppSettings | None:
        dialog_exec = getattr(self.controls.dialog, "exec", None)
        if callable(dialog_exec):
            result = dialog_exec()
            if result != self._accepted_dialog_code():
                return None
        return self.saved_settings

    def save(self) -> AppSettings | None:
        try:
            settings = AppSettings(
                schema_version=self._settings.schema_version,
                default_open_directory=self.controls.default_open_directory.text().strip(),
                default_output_directory=(
                    self.controls.default_output_directory.text().strip()
                ),
                linux_packaging_channel=self._settings.linux_packaging_channel,
                ui=dict(self._settings.ui),
            )
            self._settings_store.save_settings(settings)
        except (ConfigValidationError, OSError, ValueError) as exc:
            self._show_error(str(exc))
            return None

        self.saved_settings = settings
        if self._on_save is not None:
            self._on_save(settings)
        accept = getattr(self.controls.dialog, "accept", None)
        if callable(accept):
            accept()
        return settings

    def cancel(self) -> None:
        reject = getattr(self.controls.dialog, "reject", None)
        if callable(reject):
            reject()

    def _build_controls(self, *, parent: Any) -> AppSettingsDialogControls:
        dialog = self._bindings.q_dialog(parent)
        if hasattr(dialog, "setWindowTitle"):
            dialog.setWindowTitle("Application settings")
        layout = self._bindings.q_form_layout(dialog)

        default_open_directory = self._bindings.q_line_edit(
            self._settings.default_open_directory
        )
        default_output_directory = self._bindings.q_line_edit(
            self._settings.default_output_directory
        )
        save_button = self._bindings.q_push_button("Save")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("Default open folder", default_open_directory)
        layout.addRow("Default output folder", default_output_directory)
        layout.addRow("", save_button)
        layout.addRow("", cancel_button)

        save_button.clicked.connect(self.save)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.cancel)  # type: ignore[attr-defined]

        return AppSettingsDialogControls(
            dialog=dialog,
            default_open_directory=default_open_directory,
            default_output_directory=default_output_directory,
            save_button=save_button,
            cancel_button=cancel_button,
        )

    def _accepted_dialog_code(self) -> Any:
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        if accepted is not None:
            return accepted
        dialog_code = getattr(self._bindings.q_dialog, "DialogCode", None)
        accepted = getattr(dialog_code, "Accepted", None)
        if accepted is not None:
            return accepted
        return 1

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Settings error", message)


class CertificateImportDialog:
    """Small dialog for importing an existing PKCS#12 certificate."""

    def __init__(
        self,
        *,
        bindings: QtAppFrameBindings,
        parent: Any,
        lifecycle_service: CertificateLifecycleService,
        on_import: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._lifecycle_service = lifecycle_service
        self._on_import = on_import
        self.import_result = None
        self.controls = self._build_controls(parent=parent)

    def exec(self) -> Any | None:
        dialog_exec = getattr(self.controls.dialog, "exec", None)
        if callable(dialog_exec):
            result = dialog_exec()
            if result != self._accepted_dialog_code():
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
            result = self._lifecycle_service.import_pkcs12(
                source_path=source_path,
                display_name=display_name,
                passphrase=passphrase,
                save_password=save_password,
            )
        except Exception as exc:
            self._show_error(str(exc))
            return None

        self.import_result = result
        if result.refresh_shell and self._on_import is not None:
            self._on_import()
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(
                self.controls.dialog,
                "Certificate imported",
                result.user_message,
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

        certificate_path = self._bindings.q_line_edit("")
        display_name = self._bindings.q_line_edit("")
        passphrase = self._bindings.q_line_edit("")
        save_password = self._bindings.q_check_box("Save password securely")
        choose_button = self._bindings.q_push_button("Choose...")
        import_button = self._bindings.q_push_button("Import")
        cancel_button = self._bindings.q_push_button("Cancel")

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

    def _accepted_dialog_code(self) -> Any:
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        if accepted is not None:
            return accepted
        dialog_code = getattr(self._bindings.q_dialog, "DialogCode", None)
        accepted = getattr(dialog_code, "Accepted", None)
        if accepted is not None:
            return accepted
        return 1

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Certificate import error", message)


class CertificateCreationDialog:
    """Small dialog for creating a self-signed managed certificate."""

    def __init__(
        self,
        *,
        bindings: QtAppFrameBindings,
        parent: Any,
        lifecycle_service: CertificateLifecycleService,
        on_create: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._lifecycle_service = lifecycle_service
        self._on_create = on_create
        self.creation_result = None
        self.controls = self._build_controls(parent=parent)

    def exec(self) -> Any | None:
        dialog_exec = getattr(self.controls.dialog, "exec", None)
        if callable(dialog_exec):
            result = dialog_exec()
            if result != self._accepted_dialog_code():
                return None
        return self.creation_result

    def create_certificate(self) -> Any | None:
        display_name = self.controls.display_name.text().strip()
        passphrase = self.controls.passphrase.text()
        save_password = bool(self.controls.save_password.isChecked())
        try:
            result = self._lifecycle_service.create_self_signed_certificate(
                display_name=display_name,
                passphrase=passphrase,
                save_password=save_password,
            )
        except Exception as exc:
            self._show_error(str(exc))
            return None

        self.creation_result = result
        if result.refresh_shell and self._on_create is not None:
            self._on_create()
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(
                self.controls.dialog,
                "Certificate created",
                result.user_message,
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

        display_name = self._bindings.q_line_edit("")
        passphrase = self._bindings.q_line_edit("")
        save_password = self._bindings.q_check_box("Save password securely")
        create_button = self._bindings.q_push_button("Create")
        cancel_button = self._bindings.q_push_button("Cancel")

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

    def _accepted_dialog_code(self) -> Any:
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        if accepted is not None:
            return accepted
        dialog_code = getattr(self._bindings.q_dialog, "DialogCode", None)
        accepted = getattr(dialog_code, "Accepted", None)
        if accepted is not None:
            return accepted
        return 1

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Certificate creation error", message)


class CertificateConfigurationManagementDialog:
    """Small dialog for renaming, annotating, and deleting configurations."""

    def __init__(
        self,
        *,
        bindings: QtAppFrameBindings,
        parent: Any,
        lifecycle_service: CertificateLifecycleService,
        on_change: Callable[[], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._lifecycle_service = lifecycle_service
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
        catalog = self._lifecycle_service.load_catalog()
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
            result = self._lifecycle_service.save_configuration(
                configuration_id=configuration.certificate_configuration_id,
                display_name=self.controls.display_name.text(),
                notes=self.controls.notes.text(),
            )
        except (Exception,) as exc:
            self._show_error(str(exc))
            return None

        self.reload_configurations()
        updated = result.certificate_configuration
        if updated is None:
            self._show_error("Certificate configuration was not saved.")
            return None
        self._select_configuration(updated.certificate_configuration_id)
        self.load_selected_configuration()
        self._emit_changed_if_needed(result.refresh_shell)
        self._show_information(result.user_message)
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
            result = self._lifecycle_service.delete_configuration(configuration_id)
        except (Exception,) as exc:
            self._show_error(str(exc))
            self.reload_configurations()
            return False

        self.reload_configurations()
        self._emit_changed_if_needed(result.refresh_shell)
        self._show_information(result.user_message)
        return True

    def delete_selected_managed_certificate(self) -> bool:
        certificate_id = self._selected_managed_certificate_id()
        if certificate_id is None:
            self._show_error("Select a managed certificate to delete.")
            return False
        try:
            result = self._lifecycle_service.delete_managed_certificate(certificate_id)
        except (Exception,) as exc:
            self._show_error(str(exc))
            self.reload_configurations()
            return False

        self.reload_configurations()
        self._emit_changed_if_needed(result.refresh_shell)
        self._show_information(result.user_message)
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
            result = self._lifecycle_service.export_managed_certificate(
                certificate_id=certificate_id,
                destination_path=selected_path,
            )
        except (Exception,) as exc:
            self._show_error(str(exc))
            self.reload_configurations()
            return None

        self._emit_changed_if_needed(result.refresh_shell)
        self._show_information(result.user_message)
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

        configuration_selector = self._bindings.q_combo_box()
        display_name = self._bindings.q_line_edit("")
        notes = self._bindings.q_line_edit("")
        managed_certificate_selector = self._bindings.q_combo_box()
        save_button = self._bindings.q_push_button("Save")
        delete_button = self._bindings.q_push_button("Delete")
        export_certificate_button = self._bindings.q_push_button("Export certificate")
        delete_certificate_button = self._bindings.q_push_button("Delete certificate")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("Configuration", configuration_selector)
        layout.addRow("Display name", display_name)
        layout.addRow("Notes", notes)
        layout.addRow("Managed certificate", managed_certificate_selector)
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
            configuration_selector=configuration_selector,
            display_name=display_name,
            notes=notes,
            managed_certificate_selector=managed_certificate_selector,
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
            information(
                self.controls.dialog,
                "Certificate configuration",
                message,
            )


class FoliaSealAppFrame:
    """Application frame that owns top-level menus and document opening."""

    def __init__(
        self,
        *,
        bindings: QtAppFrameBindings,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: Any | None = None,
        certificate_lifecycle_service: CertificateLifecycleService | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        shell_builder: Callable[..., Any] = build_qt_signing_shell,
        render_backend_factory: Callable[[], Any] = QtPdfRenderBackend,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._app_settings_store = app_settings_store or AppSettingsStore.default()
        self._app_settings = app_settings or self._app_settings_store.load_settings()
        self._certificate_catalog_store = certificate_catalog_store or (
            CertificateCatalogStore.default()
        )
        self._certificate_secret_provider = (
            certificate_secret_provider or SecretToolCertificateSecretStore()
        )
        self._certificate_lifecycle_service = certificate_lifecycle_service or (
            CertificateLifecycleService(
                store=self._certificate_catalog_store,
                secret_store=self._certificate_secret_provider,
            )
        )
        self._preset_catalog_store = preset_catalog_store
        self._sign_executor = sign_executor
        self._shell_builder = shell_builder
        self._render_backend_factory = render_backend_factory
        self._on_sign_request = on_sign_request
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._current_shell: Any | None = None
        self._current_viewer_workflow: ViewerWorkflow | None = None
        self._current_signing_workflow: SigningDraftWorkflow | None = None
        self._settings_dialog: AppSettingsDialog | None = None
        self._certificate_import_dialog: CertificateImportDialog | None = None
        self._certificate_management_dialog: (
            CertificateConfigurationManagementDialog | None
        ) = None
        self._open_action: Any | None = None
        self._save_as_action: Any | None = None

        self.window = bindings.q_main_window()
        self.window.setWindowTitle("FoliaSeal")
        self._install_menus()
        self._set_placeholder()

        self.window.open_file = self.choose_open_pdf  # type: ignore[attr-defined]
        self.window.open_pdf_path = self.open_pdf_path  # type: ignore[attr-defined]
        self.window.show_app_settings = self.show_app_settings  # type: ignore[attr-defined]
        self.window.show_certificate_creation = self.show_certificate_creation  # type: ignore[attr-defined]
        self.window.show_certificate_import = self.show_certificate_import  # type: ignore[attr-defined]
        self.window.show_certificate_management = self.show_certificate_management  # type: ignore[attr-defined]
        self.window.app_settings = self._app_settings  # type: ignore[attr-defined]
        self.window.current_shell = None  # type: ignore[attr-defined]
        self.window.current_viewer_workflow = None  # type: ignore[attr-defined]
        self.window.current_signing_workflow = None  # type: ignore[attr-defined]
        self.window._foliaseal_app_frame = self  # type: ignore[attr-defined]

    @property
    def container(self) -> Any:
        return self.window

    @property
    def app_settings(self) -> AppSettings:
        return self._app_settings

    @property
    def current_signing_workflow(self) -> SigningDraftWorkflow | None:
        return self._current_signing_workflow

    def choose_open_pdf(self) -> str | None:
        selected = self._bindings.q_file_dialog.getOpenFileName(
            self.window,
            "Open PDF",
            self._app_settings.default_open_directory,
            "PDF files (*.pdf)",
        )
        if isinstance(selected, tuple):
            selected_path = str(selected[0])
        else:
            selected_path = str(selected)
        selected_path = selected_path.strip()
        if not selected_path:
            return None
        self.open_pdf_path(selected_path)
        return selected_path

    def open_pdf_path(self, pdf_path: str | Path) -> Any | None:
        source_path = Path(pdf_path)
        try:
            page_count = self._load_page_count(source_path)
            viewer_workflow = ViewerWorkflow(
                document_path=str(source_path),
                render_backend=self._render_backend_factory(),
                session=ViewerSession(page_count=page_count),
            )
            signing_workflow = SigningDraftWorkflow(
                input_pdf_path=str(source_path),
                output_pdf_path=str(
                    suggest_signed_output_path(
                        input_pdf_path=source_path,
                        default_output_directory=(
                            self._app_settings.default_output_directory
                        ),
                    )
                ),
                certificate_path="",
                passphrase="",
                tsa_url="",
                timestamp_required=False,
            )
            shell = self._shell_builder(
                viewer_workflow=viewer_workflow,
                signing_workflow=signing_workflow,
                certificate_catalog_store=self._certificate_catalog_store,
                certificate_secret_provider=self._certificate_secret_provider,
                preset_catalog_store=self._preset_catalog_store,
                app_settings=self._app_settings,
                app_settings_store=self._app_settings_store,
                sign_executor=self._sign_executor,
                on_sign_request=self._on_sign_request,
                on_open_signed_output=self.open_pdf_path,
                on_error=self._emit_error,
                on_status_change=self._on_status_change,
            )
        except Exception as exc:
            self._emit_error(f"Unable to open PDF: {exc}")
            return None

        self._current_shell = shell
        self._current_viewer_workflow = viewer_workflow
        self._current_signing_workflow = signing_workflow
        self.window.current_shell = shell  # type: ignore[attr-defined]
        self.window.current_viewer_workflow = viewer_workflow  # type: ignore[attr-defined]
        self.window.current_signing_workflow = signing_workflow  # type: ignore[attr-defined]
        self.window.setCentralWidget(shell)
        self._set_save_as_enabled(True)
        return shell

    def show_app_settings(self) -> AppSettings | None:
        dialog = AppSettingsDialog(
            bindings=self._bindings,
            parent=self.window,
            settings=self._app_settings,
            settings_store=self._app_settings_store,
            on_save=self._apply_app_settings,
        )
        self._settings_dialog = dialog
        self.window.settings_dialog = dialog  # type: ignore[attr-defined]
        settings = dialog.exec()
        if settings is None:
            return None
        self._apply_app_settings(settings)
        return settings

    def show_certificate_import(self) -> Any | None:
        dialog = CertificateImportDialog(
            bindings=self._bindings,
            parent=self.window,
            lifecycle_service=self._certificate_lifecycle_service,
            on_import=self._refresh_shell_certificate_configurations,
        )
        self._certificate_import_dialog = dialog
        self.window.certificate_import_dialog = dialog  # type: ignore[attr-defined]
        return dialog.exec()

    def show_certificate_creation(self) -> Any | None:
        dialog = CertificateCreationDialog(
            bindings=self._bindings,
            parent=self.window,
            lifecycle_service=self._certificate_lifecycle_service,
            on_create=self._refresh_shell_certificate_configurations,
        )
        self._certificate_creation_dialog = dialog
        self.window.certificate_creation_dialog = dialog  # type: ignore[attr-defined]
        return dialog.exec()

    def show_certificate_management(self) -> Any | None:
        dialog = CertificateConfigurationManagementDialog(
            bindings=self._bindings,
            parent=self.window,
            lifecycle_service=self._certificate_lifecycle_service,
            on_change=self._refresh_shell_certificate_configurations,
        )
        self._certificate_management_dialog = dialog
        self.window.certificate_management_dialog = dialog  # type: ignore[attr-defined]
        return dialog.exec()

    def _install_menus(self) -> None:
        menu_bar = self.window.menuBar()
        file_menu = menu_bar.addMenu("File")
        self._open_action = self._action(
            "Open file",
            self.choose_open_pdf,
            shortcut="Ctrl+O",
        )
        file_menu.addAction(self._open_action)
        self._save_as_action = self._action(
            "Save As...",
            self._choose_save_as,
            shortcut="Ctrl+Shift+S",
            enabled=False,
        )
        file_menu.addAction(self._save_as_action)
        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.addAction(
            self._action("Application settings", self.show_app_settings)
        )
        settings_menu.addAction(
            self._action("Create certificate...", self.show_certificate_creation)
        )
        settings_menu.addAction(
            self._action("Import certificate...", self.show_certificate_import)
        )
        settings_menu.addAction(
            self._action(
                "Manage certificate configurations...",
                self.show_certificate_management,
            )
        )

    def _action(
        self,
        text: str,
        callback: Callable[[], Any],
        *,
        shortcut: str | None = None,
        enabled: bool = True,
    ) -> Any:
        action = self._bindings.q_action(text, self.window)
        triggered = getattr(action, "triggered", None)
        if hasattr(triggered, "connect"):
            triggered.connect(callback)
        set_shortcut = getattr(action, "setShortcut", None)
        if shortcut is not None and callable(set_shortcut):
            set_shortcut(shortcut)
        set_enabled = getattr(action, "setEnabled", None)
        if callable(set_enabled):
            set_enabled(enabled)
        return action

    def _choose_save_as(self) -> str | None:
        shell = self._current_shell
        if shell is None:
            return None
        choose_output = getattr(shell, "choose_output_pdf_path", None)
        if not callable(choose_output):
            return None
        return choose_output()

    def _set_save_as_enabled(self, enabled: bool) -> None:
        action = self._save_as_action
        if action is None:
            return
        set_enabled = getattr(action, "setEnabled", None)
        if callable(set_enabled):
            set_enabled(enabled)

    def _set_placeholder(self) -> None:
        label = self._bindings.q_label("Open a PDF to begin signing.")
        if hasattr(label, "setWordWrap"):
            label.setWordWrap(True)
        self.window.setCentralWidget(label)
        self._set_save_as_enabled(False)

    def _load_page_count(self, pdf_path: Path) -> int:
        document = self._bindings.qpdf_document()
        status = document.load(str(pdf_path))
        if status != self._bindings.qpdf_document.Error.None_:
            raise RuntimeError(f"Failed to load PDF document: {pdf_path}")
        page_count = int(document.pageCount())
        if page_count <= 0:
            raise RuntimeError(f"PDF has no pages: {pdf_path}")
        return page_count

    def _emit_error(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.window, "FoliaSeal", message)

    def _apply_app_settings(self, settings: AppSettings) -> None:
        self._app_settings = settings
        self.window.app_settings = settings  # type: ignore[attr-defined]
        shell = self._current_shell
        if shell is None:
            return
        update_settings = getattr(shell, "apply_app_settings", None)
        if callable(update_settings):
            update_settings(settings)

    def _refresh_shell_certificate_configurations(self) -> None:
        shell = self._current_shell
        if shell is None:
            return
        refresh = getattr(shell, "refresh_certificate_configurations", None)
        if callable(refresh):
            refresh()


class QtAppFrameAdapter:
    """Factory for the top-level FoliaSeal Qt app frame."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create(
        self,
        *,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: Any | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> Any:
        return FoliaSealAppFrame(
            bindings=self._bindings,
            app_settings=app_settings,
            app_settings_store=app_settings_store,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog_store=preset_catalog_store,
            sign_executor=sign_executor,
            on_sign_request=on_sign_request,
            on_error=on_error,
            on_status_change=on_status_change,
        ).container

    def launch(
        self,
        *,
        argv: Sequence[str] | None = None,
        initial_pdf_path: str | Path | None = None,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: Any | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> int:
        q_application = self._bindings.q_application
        instance_getter = getattr(q_application, "instance", None)
        app = instance_getter() if callable(instance_getter) else None
        if app is None:
            launch_argv = list(argv) if argv is not None else list(sys.argv)
            if not launch_argv:
                launch_argv = ["foliaseal", "gui"]
            app = q_application(launch_argv)

        frame = FoliaSealAppFrame(
            bindings=self._bindings,
            app_settings=app_settings,
            app_settings_store=app_settings_store,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog_store=preset_catalog_store,
            sign_executor=sign_executor,
            on_sign_request=on_sign_request,
            on_error=on_error,
            on_status_change=on_status_change,
        )
        show = getattr(frame.window, "show", None)
        if callable(show):
            show()
        if initial_pdf_path is not None:
            frame.open_pdf_path(initial_pdf_path)
        exec_method = getattr(app, "exec", None)
        if not callable(exec_method):
            return 0
        return int(exec_method())

    def _load_bindings(self) -> QtAppFrameBindings:
        try:
            qt_widgets = importlib.import_module("PySide6.QtWidgets")
            qt_gui = importlib.import_module("PySide6.QtGui")
            qtpdf = importlib.import_module("PySide6.QtPdf")
        except Exception as exc:  # pragma: no cover - environment dependent
            raise QtAppFrameBindingsUnavailable(
                "PySide6 QtWidgets and QtPdf are required for the FoliaSeal app frame. "
                f"Details: {exc}"
            ) from exc

        return QtAppFrameBindings(
            q_main_window=getattr(qt_widgets, "QMainWindow"),
            q_dialog=getattr(qt_widgets, "QDialog"),
            q_form_layout=getattr(qt_widgets, "QFormLayout"),
            q_label=getattr(qt_widgets, "QLabel"),
            q_line_edit=getattr(qt_widgets, "QLineEdit"),
            q_check_box=getattr(qt_widgets, "QCheckBox"),
            q_combo_box=getattr(qt_widgets, "QComboBox"),
            q_push_button=getattr(qt_widgets, "QPushButton"),
            q_file_dialog=getattr(qt_widgets, "QFileDialog"),
            q_message_box=getattr(qt_widgets, "QMessageBox"),
            q_action=getattr(qt_gui, "QAction"),
            q_application=getattr(qt_widgets, "QApplication"),
            qpdf_document=getattr(qtpdf, "QPdfDocument"),
        )


def build_qt_app_frame(
    *,
    app_settings: AppSettings | None = None,
    app_settings_store: AppSettingsStore | None = None,
    certificate_catalog_store: CertificateCatalogStore | None = None,
    certificate_secret_provider: Any | None = None,
    preset_catalog_store: SignaturePresetCatalogStore | None = None,
    sign_executor: SigningRequestExecutor | None = None,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> Any:
    """Build a QMainWindow for the FoliaSeal signing GUI."""

    adapter = QtAppFrameAdapter()
    return adapter.create(
        app_settings=app_settings,
        app_settings_store=app_settings_store,
        certificate_catalog_store=certificate_catalog_store,
        certificate_secret_provider=certificate_secret_provider,
        preset_catalog_store=preset_catalog_store,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )


def launch_qt_app_frame(
    *,
    argv: Sequence[str] | None = None,
    initial_pdf_path: str | Path | None = None,
    app_settings: AppSettings | None = None,
    app_settings_store: AppSettingsStore | None = None,
    certificate_catalog_store: CertificateCatalogStore | None = None,
    certificate_secret_provider: Any | None = None,
    preset_catalog_store: SignaturePresetCatalogStore | None = None,
    sign_executor: SigningRequestExecutor | None = None,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> int:
    """Create QApplication, show the FoliaSeal main window, and run the event loop."""

    adapter = QtAppFrameAdapter()
    return adapter.launch(
        argv=argv,
        initial_pdf_path=initial_pdf_path,
        app_settings=app_settings,
        app_settings_store=app_settings_store,
        certificate_catalog_store=certificate_catalog_store,
        certificate_secret_provider=certificate_secret_provider,
        preset_catalog_store=preset_catalog_store,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )
