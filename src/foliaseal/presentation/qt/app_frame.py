"""Qt application-frame wrapper for the FoliaSeal signing GUI."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import (
    CertificateManager,
    ReusableSigningObjects,
    SigningDraftWorkflow,
)
from foliaseal.application.signing_material_resolver import (
    CertificateSigningMaterialPort,
    RepositoryBackedCertificateSigningMaterialPort,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import (
    AppSettings,
    ConfigValidationError,
)
from foliaseal.infra.render import PopplerPdfRenderBackend
from foliaseal.infra.secret_storage import SecretToolCertificateSecretStore
from foliaseal.presentation.qt.app_frame_certificate_management import (
    AppFrameCertificateDialogService,
    CertificateDialogCompatibilityState,
    CertificateDialogPort,
)
from foliaseal.presentation.qt.app_frame_command_model import (
    AppFrameCommandId,
    file_command_definition,
)
from foliaseal.presentation.qt.app_frame_profile_library import (
    ReusableObjectLibraryDialog,
)
from foliaseal.presentation.qt.app_frame_workspace_action_state import (
    WorkspaceActionState,
    workspace_action_state_closed,
    workspace_action_state_open,
    workspace_action_state_with_selection_result,
)
from foliaseal.presentation.qt.app_frame_workspace_open import (
    QtPdfPageCountLoader,
    SigningWorkspaceCompositionService,
    WorkspaceHandle,
    WorkspaceOpenPort,
    WorkspaceOpenService,
)
from foliaseal.presentation.qt.signing_shell import (
    SigningRequestExecutor,
)
from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspaceFactory,
    SigningWorkspaceFactory,
    SigningWorkspacePort,
)
from foliaseal.presentation.qt.signing_workspace_host import (
    SigningWorkspaceEnvironment,
    SigningWorkspaceHost,
)
from foliaseal.presentation.qt.signing_workspace_lifecycle import QtWorkspaceMount
from foliaseal.resources.icons import icon_path


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
    q_icon: type[Any]
    q_application: type[Any]
    qpdf_document: type[Any]


@dataclass(frozen=True)
class AppSettingsDialogControls:
    """Controls used by the app-wide settings dialog."""

    dialog: Any
    default_open_directory: Any
    default_open_directory_browse_button: Any
    default_output_directory: Any
    default_output_directory_browse_button: Any
    save_button: Any
    cancel_button: Any


@dataclass(frozen=True)
class AppFrameDialogCompatibilityState:
    """Frame-owned dialog exposure retained for tests and compatibility callers."""

    settings_dialog: Any | None = None
    certificate_import_dialog: Any | None = None
    certificate_creation_dialog: Any | None = None
    certificate_management_dialog: Any | None = None
    reusable_object_library_dialog: Any | None = None


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
                default_output_directory=(self.controls.default_output_directory.text().strip()),
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

        default_open_directory = self._bindings.q_line_edit(self._settings.default_open_directory)
        default_open_directory_browse_button = self._bindings.q_push_button("Browse...")
        default_output_directory = self._bindings.q_line_edit(
            self._settings.default_output_directory
        )
        default_output_directory_browse_button = self._bindings.q_push_button("Browse...")
        save_button = self._bindings.q_push_button("Save")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("Default open folder", default_open_directory)
        layout.addRow("", default_open_directory_browse_button)
        layout.addRow("Default output folder", default_output_directory)
        layout.addRow("", default_output_directory_browse_button)
        layout.addRow("", save_button)
        layout.addRow("", cancel_button)

        default_open_directory_browse_button.clicked.connect(  # type: ignore[attr-defined]
            lambda: self._choose_directory(
                title="Choose default open folder",
                current_path=default_open_directory.text().strip(),
                target=default_open_directory,
            )
        )
        default_output_directory_browse_button.clicked.connect(  # type: ignore[attr-defined]
            lambda: self._choose_directory(
                title="Choose default output folder",
                current_path=default_output_directory.text().strip(),
                target=default_output_directory,
            )
        )
        save_button.clicked.connect(self.save)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.cancel)  # type: ignore[attr-defined]

        return AppSettingsDialogControls(
            dialog=dialog,
            default_open_directory=default_open_directory,
            default_open_directory_browse_button=default_open_directory_browse_button,
            default_output_directory=default_output_directory,
            default_output_directory_browse_button=default_output_directory_browse_button,
            save_button=save_button,
            cancel_button=cancel_button,
        )

    def _choose_directory(self, *, title: str, current_path: str, target: Any) -> None:
        selected = self._bindings.q_file_dialog.getExistingDirectory(
            self.controls.dialog,
            title,
            current_path or str(Path.home()),
        )
        selected_path = str(selected).strip()
        if selected_path:
            target.setText(selected_path)

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
        certificate_manager: CertificateManager | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        shell_factory: SigningWorkspaceFactory | None = None,
        render_backend_factory: Callable[[], Any] = PopplerPdfRenderBackend,
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
        self._certificate_material_port: CertificateSigningMaterialPort = (
            RepositoryBackedCertificateSigningMaterialPort(
                repository=self._certificate_catalog_store,
                secret_provider=self._certificate_secret_provider,
            )
        )
        self._certificate_manager = certificate_manager or (
            CertificateManager(
                store=self._certificate_catalog_store,
                secret_store=self._certificate_secret_provider,
            )
        )
        self._preset_catalog_store = preset_catalog_store or SignaturePresetCatalogStore.default()
        self._reusable_objects = ReusableSigningObjects(self._preset_catalog_store)
        self._sign_executor = sign_executor
        self._shell_factory = shell_factory or QtSigningWorkspaceFactory()
        self._render_backend_factory = render_backend_factory
        self._on_sign_request = on_sign_request
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._workspace_open_port: WorkspaceOpenPort = WorkspaceOpenService(
            page_count_port=QtPdfPageCountLoader(bindings.qpdf_document),
            composition_port=SigningWorkspaceCompositionService(
                render_backend_factory=self._render_backend_factory,
                shell_factory=self._shell_factory,
            ),
        )
        self._dialog_compatibility = AppFrameDialogCompatibilityState()
        self._open_action: Any | None = None
        self._save_action: Any | None = None
        self._save_as_action: Any | None = None
        self._close_action: Any | None = None
        self._exit_action: Any | None = None
        self._command_actions: dict[AppFrameCommandId, Any] = {}
        self._text_selection_mode_action: Any | None = None
        self._copy_selected_text_action: Any | None = None
        self._placeholder_open_button: Any | None = None
        self._placeholder_library_button: Any | None = None
        self._reusable_object_library: Any | None = None
        self._workspace_action_state = workspace_action_state_closed()

        self.window = bindings.q_main_window()
        self.window.setWindowTitle("FoliaSeal")
        self._workspace_mount = QtWorkspaceMount(self.window)
        self._workspace_host = SigningWorkspaceHost(
            environment=SigningWorkspaceEnvironment(
                app_settings=lambda: self._app_settings,
                app_settings_store=self._app_settings_store,
                certificate_catalog_store=self._certificate_catalog_store,
                certificate_material_port=self._certificate_material_port,
                reusable_objects=self._reusable_objects,
                sign_executor=self._sign_executor,
                on_sign_request=self._on_sign_request,
                reopen_target=self.open_pdf_path,
                on_error=self._emit_error,
                on_status_change=self._on_status_change,
            ),
            workspace_open_port=self._workspace_open_port,
            mount_port=self._workspace_mount,
        )
        self._certificate_dialog_port: CertificateDialogPort = AppFrameCertificateDialogService(
            bindings=self._bindings,
            parent=self.window,
            certificate_manager=self._certificate_manager,
            refresh_shell_certificate_configurations=(
                self._refresh_shell_certificate_configurations
            ),
        )
        self._install_menus()
        self._set_placeholder()

    @property
    def container(self) -> Any:
        return self.window

    @property
    def app_settings(self) -> AppSettings:
        return self._app_settings

    @property
    def workspace_action_state(self) -> WorkspaceActionState:
        """Return the immutable state currently applied to workspace actions."""

        return self._workspace_action_state

    @property
    def current_workspace(self) -> WorkspaceHandle | None:
        return self._workspace_host.active()

    @property
    def current_shell(self) -> Any | None:
        workspace = self._workspace_host.active()
        return None if workspace is None else workspace.view.mount_target()

    @property
    def current_viewer_workflow(self) -> ViewerWorkflow | None:
        workspace = self._workspace_host.active()
        return None if workspace is None else workspace.viewer_workflow

    @property
    def current_signing_workflow(self) -> SigningDraftWorkflow | None:
        workspace = self._workspace_host.active()
        return None if workspace is None else workspace.signing_workflow

    @property
    def dialog_compatibility(self) -> AppFrameDialogCompatibilityState:
        return self._dialog_compatibility

    @property
    def settings_dialog(self) -> Any | None:
        return self._dialog_compatibility.settings_dialog

    @property
    def certificate_import_dialog(self) -> Any | None:
        return self._dialog_compatibility.certificate_import_dialog

    @property
    def certificate_creation_dialog(self) -> Any | None:
        return self._dialog_compatibility.certificate_creation_dialog

    @property
    def certificate_management_dialog(self) -> Any | None:
        return self._dialog_compatibility.certificate_management_dialog

    @property
    def reusable_object_library_dialog(self) -> Any | None:
        return self._dialog_compatibility.reusable_object_library_dialog

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
        try:
            handle = self._workspace_host.open(pdf_path)
        except Exception as exc:
            self._emit_error(f"Unable to open PDF: {exc}")
            return None

        self._apply_workspace_action_state(workspace_action_state_open())
        return handle.view.mount_target()

    def close_workspace(self) -> None:
        """Close the active signing workspace and restore the placeholder view."""

        self._workspace_host.close()
        self._set_placeholder()

    def command_actions(self) -> dict[AppFrameCommandId, Any]:
        """Return a snapshot of frame-owned actions keyed by stable command ID."""

        return dict(self._command_actions)

    def show_app_settings(self) -> AppSettings | None:
        dialog = AppSettingsDialog(
            bindings=self._bindings,
            parent=self.window,
            settings=self._app_settings,
            settings_store=self._app_settings_store,
            on_save=self._apply_app_settings,
        )
        self._dialog_compatibility = AppFrameDialogCompatibilityState(
            settings_dialog=dialog,
            certificate_import_dialog=self.certificate_import_dialog,
            certificate_creation_dialog=self.certificate_creation_dialog,
            certificate_management_dialog=self.certificate_management_dialog,
        )
        settings = dialog.exec()
        if settings is None:
            return None
        self._apply_app_settings(settings)
        return settings

    def show_certificate_import(self) -> Any | None:
        outcome = self._certificate_dialog_port.show_import_dialog()
        self._apply_certificate_dialog_compatibility(outcome.compatibility)
        return outcome.result

    def show_certificate_creation(self) -> Any | None:
        outcome = self._certificate_dialog_port.show_creation_dialog()
        self._apply_certificate_dialog_compatibility(outcome.compatibility)
        return outcome.result

    def show_certificate_management(self) -> Any | None:
        outcome = self._certificate_dialog_port.show_management_dialog()
        self._apply_certificate_dialog_compatibility(outcome.compatibility)
        return outcome.result

    def show_reusable_object_library(self) -> Any:
        """Open Settings management for reusable signing profiles and presets."""
        if self._reusable_object_library is not None:
            self._reusable_object_library.refresh()
            self._reusable_object_library.show()
            return self._reusable_object_library
        dialog = ReusableObjectLibraryDialog(
            bindings=self._bindings,
            parent=self.window,
            library=self._reusable_objects,
            on_create=self._open_reusable_object_editor,
            on_edit=self._open_reusable_object_editor,
        )
        self._dialog_compatibility = AppFrameDialogCompatibilityState(
            settings_dialog=self.settings_dialog,
            certificate_import_dialog=self.certificate_import_dialog,
            certificate_creation_dialog=self.certificate_creation_dialog,
            certificate_management_dialog=self.certificate_management_dialog,
            reusable_object_library_dialog=dialog,
        )
        self._reusable_object_library = dialog
        dialog.show()
        return dialog

    def _open_reusable_object_editor(self) -> bool:
        workspace = self._workspace_host.active()
        if workspace is None:
            self._emit_error("Open a PDF before creating or editing reusable signing objects.")
            return False
        return workspace.maintenance.open_reusable_object_editor()

    def _install_menus(self) -> None:
        menu_bar = self.window.menuBar()
        file_menu = menu_bar.addMenu("File")
        self._open_action = self._command_action(
            file_menu,
            AppFrameCommandId.OPEN,
            self.choose_open_pdf,
        )
        self._save_action = self._command_action(
            file_menu,
            AppFrameCommandId.SAVE,
            self._save_document,
            enabled=False,
        )
        self._save_as_action = self._command_action(
            file_menu,
            AppFrameCommandId.SAVE_AS,
            self._choose_save_as,
            enabled=False,
        )
        self._close_action = self._command_action(
            file_menu,
            AppFrameCommandId.CLOSE,
            self.close_workspace,
            enabled=False,
        )
        self._exit_action = self._command_action(
            file_menu,
            AppFrameCommandId.EXIT,
            self._exit_application,
        )
        edit_menu = menu_bar.addMenu("Edit")
        self._text_selection_mode_action = self._action(
            "Text selection mode",
            self._toggle_text_selection_mode_from_action,
            enabled=False,
            checkable=True,
            icon_name="text-select.svg",
        )
        edit_menu.addAction(self._text_selection_mode_action)
        self._copy_selected_text_action = self._action(
            "Copy selected text",
            self._copy_selected_text_from_action,
            enabled=False,
            icon_name="copy.svg",
        )
        edit_menu.addAction(self._copy_selected_text_action)
        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.addAction(self._action("Application settings", self.show_app_settings))
        settings_menu.addAction(
            self._action(
                "Manage reusable signing objects...",
                self.show_reusable_object_library,
            )
        )
        settings_menu.addAction(
            self._action("Create certificate...", self.show_certificate_creation)
        )
        settings_menu.addAction(self._action("Import certificate...", self.show_certificate_import))
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
        checkable: bool = False,
        icon_name: str | None = None,
        object_name: str | None = None,
        accessible_name: str | None = None,
    ) -> Any:
        action = self._bindings.q_action(text, self.window)
        if icon_name is not None:
            set_icon = getattr(action, "setIcon", None)
            if callable(set_icon):
                set_icon(self._bindings.q_icon(icon_path(icon_name)))
        triggered = getattr(action, "triggered", None)
        if hasattr(triggered, "connect"):
            triggered.connect(callback)
        set_shortcut = getattr(action, "setShortcut", None)
        if shortcut is not None and callable(set_shortcut):
            set_shortcut(shortcut)
        set_enabled = getattr(action, "setEnabled", None)
        if callable(set_enabled):
            set_enabled(enabled)
        set_checkable = getattr(action, "setCheckable", None)
        if callable(set_checkable):
            set_checkable(checkable)
        set_object_name = getattr(action, "setObjectName", None)
        if object_name is not None and callable(set_object_name):
            set_object_name(object_name)
        set_tool_tip = getattr(action, "setToolTip", None)
        if accessible_name is not None and callable(set_tool_tip):
            set_tool_tip(accessible_name)
        set_status_tip = getattr(action, "setStatusTip", None)
        if accessible_name is not None and callable(set_status_tip):
            set_status_tip(accessible_name)
        return action

    def _command_action(
        self,
        menu: Any,
        command_id: AppFrameCommandId,
        callback: Callable[[], Any],
        *,
        enabled: bool = True,
    ) -> Any:
        definition = file_command_definition(command_id)
        action = self._action(
            definition.mnemonic_text,
            callback,
            shortcut=definition.shortcut,
            enabled=enabled,
            object_name=definition.command_id.value,
            accessible_name=definition.accessible_name,
        )
        self._command_actions[command_id] = action
        menu.addAction(action)
        return action

    def _choose_save_as(self) -> str | None:
        selected = self._with_current_shell_port(
            lambda shell_port: shell_port.choose_output_pdf_path()
        )
        return selected if selected else None

    def _save_document(self) -> Any | None:
        output_path_selected = self._with_current_shell_port(
            lambda shell_port: shell_port.has_explicit_output_pdf_path()
        )
        if not output_path_selected and self._choose_save_as() is None:
            return None
        return self._with_current_session_port(
            lambda session_port: session_port.submit_sign_request()
        )

    def _exit_application(self) -> Any | None:
        quit_application = getattr(self._bindings.q_application, "quit", None)
        if callable(quit_application):
            return quit_application()
        instance_factory = getattr(self._bindings.q_application, "instance", None)
        application = instance_factory() if callable(instance_factory) else None
        quit_instance = getattr(application, "quit", None)
        if callable(quit_instance):
            return quit_instance()
        return None

    def _apply_workspace_action_state(self, state: WorkspaceActionState) -> None:
        self._workspace_action_state = state
        self._set_action_enabled(self._save_action, state.save_enabled)
        self._set_action_enabled(self._save_as_action, state.save_as_enabled)
        self._set_action_enabled(self._close_action, state.close_enabled)
        self._set_action_enabled(self._text_selection_mode_action, state.text_selection_enabled)
        self._set_action_checked(self._text_selection_mode_action, state.text_selection_checked)
        self._set_action_enabled(self._copy_selected_text_action, state.copy_selected_text_enabled)

    @staticmethod
    def _set_action_enabled(action: Any | None, enabled: bool) -> None:
        if action is None:
            return
        set_enabled = getattr(action, "setEnabled", None)
        if callable(set_enabled):
            set_enabled(enabled)

    @staticmethod
    def _set_action_checked(action: Any | None, checked: bool) -> None:
        if action is None:
            return
        set_checked = getattr(action, "setChecked", None)
        if callable(set_checked):
            set_checked(checked)

    def _toggle_text_selection_mode_from_action(self) -> bool | None:
        action = self._text_selection_mode_action
        if action is None:
            return None
        is_checked = getattr(action, "isChecked", None)
        enabled = bool(is_checked()) if callable(is_checked) else False
        result = self._with_current_shell_port(
            lambda shell_port: shell_port.set_document_text_selection_mode(enabled)
        )
        if isinstance(result, bool):
            self._apply_workspace_action_state(
                workspace_action_state_with_selection_result(
                    self._workspace_action_state,
                    result,
                )
            )
        return result

    def _copy_selected_text_from_action(self) -> str | None:
        return self._with_current_shell_port(
            lambda shell_port: shell_port.copy_selected_document_text()
        )

    def _apply_certificate_dialog_compatibility(
        self,
        compatibility: CertificateDialogCompatibilityState,
    ) -> None:
        self._dialog_compatibility = AppFrameDialogCompatibilityState(
            settings_dialog=self.settings_dialog,
            certificate_import_dialog=(
                compatibility.import_dialog
                if compatibility.import_dialog is not None
                else self.certificate_import_dialog
            ),
            certificate_creation_dialog=(
                compatibility.creation_dialog
                if compatibility.creation_dialog is not None
                else self.certificate_creation_dialog
            ),
            certificate_management_dialog=(
                compatibility.management_dialog
                if compatibility.management_dialog is not None
                else self.certificate_management_dialog
            ),
        )

    def _set_placeholder(self) -> None:
        container = self._bindings.q_label()
        layout = self._bindings.q_form_layout(container)
        message = self._bindings.q_label(
            "No document open. Open a PDF to begin signing, or manage reusable signing objects."
        )
        if hasattr(message, "setWordWrap"):
            message.setWordWrap(True)
        open_button = self._bindings.q_push_button("Open a PDF…")
        library_button = self._bindings.q_push_button("Manage Signature Library…")
        open_button.clicked.connect(self.choose_open_pdf)
        library_button.clicked.connect(self.show_reusable_object_library)
        layout.addRow(message)
        layout.addRow(open_button)
        layout.addRow(library_button)
        self._placeholder_open_button = open_button
        self._placeholder_library_button = library_button
        self._workspace_mount.mount(container)
        self._apply_workspace_action_state(workspace_action_state_closed())

    def _emit_error(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.window, "FoliaSeal", message)

    def _apply_app_settings(self, settings: AppSettings) -> None:
        self._app_settings = settings
        self._with_current_shell_port(lambda shell_port: shell_port.apply_app_settings(settings))

    def _refresh_shell_certificate_configurations(self) -> None:
        self._with_current_shell_port(
            lambda shell_port: shell_port.refresh_certificate_configurations()
        )

    def _refresh_shell_signature_profiles(self) -> None:
        self._with_current_shell_port(
            lambda shell_port: shell_port.refresh_signature_profiles()
        )

    def _with_current_shell_port(
        self,
        action: Callable[[SigningWorkspacePort], Any | None],
    ) -> Any | None:
        workspace = self._workspace_host.active()
        if workspace is None:
            return None
        return action(workspace.maintenance)

    def _with_current_session_port(
        self,
        action: Callable[[Any], Any | None],
    ) -> Any | None:
        workspace = self._workspace_host.active()
        if workspace is None:
            return None
        return action(workspace.session)


class QtAppFrameAdapter:
    """Factory for the top-level FoliaSeal Qt app frame."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create_frame(
        self,
        *,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: Any | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        shell_factory: SigningWorkspaceFactory | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> FoliaSealAppFrame:
        return FoliaSealAppFrame(
            bindings=self._bindings,
            app_settings=app_settings,
            app_settings_store=app_settings_store,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog_store=preset_catalog_store,
            sign_executor=sign_executor,
            shell_factory=shell_factory,
            on_sign_request=on_sign_request,
            on_error=on_error,
            on_status_change=on_status_change,
        )

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
        shell_factory: SigningWorkspaceFactory | None = None,
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

        frame = self.create_frame(
            app_settings=app_settings,
            app_settings_store=app_settings_store,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog_store=preset_catalog_store,
            sign_executor=sign_executor,
            shell_factory=shell_factory,
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
            q_icon=getattr(qt_gui, "QIcon"),
            q_application=getattr(qt_widgets, "QApplication"),
            qpdf_document=getattr(qtpdf, "QPdfDocument"),
        )


def build_qt_app_frame_host(
    *,
    app_settings: AppSettings | None = None,
    app_settings_store: AppSettingsStore | None = None,
    certificate_catalog_store: CertificateCatalogStore | None = None,
    certificate_secret_provider: Any | None = None,
    preset_catalog_store: SignaturePresetCatalogStore | None = None,
    sign_executor: SigningRequestExecutor | None = None,
    shell_factory: SigningWorkspaceFactory | None = None,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> FoliaSealAppFrame:
    """Build the real FoliaSeal app-frame host."""

    adapter = QtAppFrameAdapter()
    return adapter.create_frame(
        app_settings=app_settings,
        app_settings_store=app_settings_store,
        certificate_catalog_store=certificate_catalog_store,
        certificate_secret_provider=certificate_secret_provider,
        preset_catalog_store=preset_catalog_store,
        sign_executor=sign_executor,
        shell_factory=shell_factory,
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
    shell_factory: SigningWorkspaceFactory | None = None,
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
        shell_factory=shell_factory,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )
