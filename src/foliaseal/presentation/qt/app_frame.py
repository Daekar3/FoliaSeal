"""Qt application-frame wrapper for the FoliaSeal signing GUI."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from foliaseal.application import (
    CertificateManager,
    ConfigureCertificateRequest,
    PlacementEditorState,
    ReusableSigningObjects,
    SigningDraftWorkflow,
    build_default_signing_executor,
)
from foliaseal.application.reusable_signing_models import PlacementProfile
from foliaseal.application.reusable_signing_objects import ReusableObjectRef, SavePlacement
from foliaseal.application.signature_library_session import (
    CertificateLibraryRef,
)
from foliaseal.application.signing_material_resolver import (
    CertificateSigningMaterialPort,
    RepositoryBackedCertificateSigningMaterialPort,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.app_settings_ui import (
    AppearanceMode,
    AppUiSettings,
    MainWindowGeometry,
)
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
    command_definition,
)
from foliaseal.presentation.qt.app_frame_profile_library import (
    ReusableObjectLibraryDialog,
)
from foliaseal.presentation.qt.app_frame_theme import apply_appearance_mode
from foliaseal.presentation.qt.app_frame_workspace_action_state import (
    WorkspaceActionState,
    workspace_action_state_closed,
    workspace_action_state_open,
    workspace_action_state_with_document_text_result,
    workspace_action_state_with_selection_result,
)
from foliaseal.presentation.qt.app_frame_workspace_open import (
    QtPdfPageCountLoader,
    SigningWorkspaceCompositionService,
    WorkspaceHandle,
    WorkspaceOpenPort,
    WorkspaceOpenService,
)
from foliaseal.presentation.qt.appearance_profile_editor_dialog import (
    AppearanceProfileEditorDialog,
)
from foliaseal.presentation.qt.document_signatures_dialog import DocumentSignaturesDialog
from foliaseal.presentation.qt.placement_profile_editor_dialog import (
    PlacementProfileEditorDialog,
)
from foliaseal.presentation.qt.signature_preset_editor_dialog import (
    SignaturePresetEditorDialog,
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
from foliaseal.presentation.qt.single_instance import (
    NoopSingleInstanceCoordinator,
    OpenRequest,
    QtLocalInstanceCoordinator,
    SingleInstanceCoordinator,
    endpoint_name,
    request_for_path,
)
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
    q_input_dialog: Any | None = None
    q_palette: type[Any] | None = None
    q_color: type[Any] | None = None
    q_local_server: type[Any] | None = None
    q_local_socket: type[Any] | None = None
    q_widget: type[Any] | None = None
    q_hbox_layout: type[Any] | None = None
    q_vbox_layout: type[Any] | None = None
    q_list_widget: type[Any] | None = None
    q_splitter: type[Any] | None = None
    q_text_edit: type[Any] | None = None
    q_double_spin_box: type[Any] | None = None
    q_spin_box: type[Any] | None = None


@dataclass(frozen=True)
class AppSettingsDialogControls:
    """Controls used by the app-wide settings dialog."""

    dialog: Any
    default_open_directory: Any
    default_open_directory_browse_button: Any
    default_output_directory: Any
    default_output_directory_browse_button: Any
    appearance_mode: Any
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
                ui=AppUiSettings.from_mapping(
                    {
                        **self._settings.ui,
                        "appearance_mode": str(
                            self.controls.appearance_mode.currentData() or AppearanceMode.SYSTEM
                        ),
                    }
                ).to_mapping(self._settings.ui),
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
        appearance_mode = self._bindings.q_combo_box()
        for mode in AppearanceMode:
            appearance_mode.addItem(mode.value.title(), mode.value)
        current_mode = self._settings.ui_settings.appearance_mode.value
        mode_index = next(
            index for index, mode in enumerate(AppearanceMode) if mode.value == current_mode
        )
        appearance_mode.setCurrentIndex(mode_index)
        save_button = self._bindings.q_push_button("Save")
        cancel_button = self._bindings.q_push_button("Cancel")

        layout.addRow("Default open folder", default_open_directory)
        layout.addRow("", default_open_directory_browse_button)
        layout.addRow("Default output folder", default_output_directory)
        layout.addRow("", default_output_directory_browse_button)
        layout.addRow("Appearance", appearance_mode)
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
            appearance_mode=appearance_mode,
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

    MAIN_WINDOW_MINIMUM_SIZE = (1100, 700)

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
        self._preset_catalog_store = preset_catalog_store or SignaturePresetCatalogStore.default()
        self._certificate_manager = certificate_manager or (
            CertificateManager(
                store=self._certificate_catalog_store,
                secret_store=self._certificate_secret_provider,
                referenced_configuration_ids=self._referenced_preset_configuration_ids,
            )
        )
        self._reusable_objects = ReusableSigningObjects(
            self._preset_catalog_store,
            certificate_configuration_exists=self._certificate_configuration_exists,
        )
        self._sign_executor = (
            sign_executor if sign_executor is not None else build_default_signing_executor()
        )
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
        self._previous_page_action: Any | None = None
        self._next_page_action: Any | None = None
        self._command_actions: dict[AppFrameCommandId, Any] = {}
        self._text_selection_mode_action: Any | None = None
        self._copy_selected_text_action: Any | None = None
        self._find_action: Any | None = None
        self._document_signatures_action: Any | None = None
        self._placeholder_open_button: Any | None = None
        self._placeholder_library_button: Any | None = None
        self._reusable_object_library: Any | None = None
        self._document_signatures_dialog: DocumentSignaturesDialog | None = None
        self._closing_document_signatures = False
        self._workspace_action_state = workspace_action_state_closed()

        self.window = bindings.q_main_window()
        self.window.setWindowTitle("FoliaSeal")
        setattr(self.window, "_foliaseal_close_event_handler", self._handle_window_close_event)
        self._apply_window_baseline()
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
                recovery_reopen_target=self.open_recovery_pdf_path,
                on_error=self._emit_error,
                on_status_change=self._handle_status_change,
                on_open_signature_library=self.show_reusable_object_library,
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
    def appearance_mode(self) -> str:
        """Return the normalized application-chrome appearance mode."""

        return self._app_settings.ui_settings.appearance_mode.value

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

    def _certificate_configuration_exists(self, configuration_id: str) -> bool:
        """Return whether a preset certificate reference resolves in the live catalog."""

        try:
            self._certificate_catalog_store.load_catalog().configuration_by_id(configuration_id)
        except KeyError:
            return False
        return True

    def _referenced_preset_configuration_ids(self) -> set[str]:
        """Return certificate configuration ids retained by saved signature presets."""

        catalog = self._preset_catalog_store.load_catalog()
        return {
            preset.certificate_configuration_id
            for preset in catalog.signature_presets
            if preset.certificate_configuration_id is not None
        }

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

    @property
    def document_signatures_dialog(self) -> DocumentSignaturesDialog | None:
        return self._document_signatures_dialog

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
            candidate = self._workspace_host.prepare(pdf_path)
        except Exception as exc:
            self._emit_error(f"Unable to open PDF: {exc}")
            return None

        if not self._confirm_discard_if_dirty(action="open"):
            candidate.view.dispose()
            return None
        self._close_document_signatures()
        try:
            handle = self._workspace_host.replace_prepared(candidate)
        except Exception as exc:
            self._emit_error(f"Unable to open PDF: {exc}")
            return None

        self._apply_workspace_action_state(workspace_action_state_open())
        self._sync_page_navigation_actions()
        return handle.view.mount_target()

    def open_recovery_pdf_path(self, pdf_path: str | Path) -> Any | None:
        """Open a preserved artifact in an explicit untrusted recovery workspace."""

        try:
            candidate = self._workspace_host.prepare_recovery(pdf_path)
        except Exception as exc:
            self._emit_error(f"Unable to open preserved PDF: {exc}")
            return None
        if not self._confirm_discard_if_dirty(action="open preserved copy"):
            candidate.view.dispose()
            return None
        self._close_document_signatures()
        try:
            handle = self._workspace_host.replace_prepared(candidate)
        except Exception as exc:
            self._emit_error(f"Unable to open preserved PDF: {exc}")
            return None
        self._apply_workspace_action_state(workspace_action_state_open())
        self._sync_page_navigation_actions()
        return handle.view.mount_target()

    def close_workspace(self) -> bool:
        """Close the active signing workspace and restore the placeholder view."""

        if not self._confirm_discard_if_dirty():
            return False
        self._close_document_signatures()
        self._workspace_host.close()
        self._set_placeholder()
        return True

    def _confirm_discard_if_dirty(self, *, action: str = "close") -> bool:
        """Apply the UI_SPEC draft decision before a close, exit, or replacement."""
        workspace = self._workspace_host.active()
        if workspace is None:
            return True
        if not workspace.maintenance.has_unsaved_changes():
            workspace.maintenance.clear_session_secrets()
            return True

        ready_to_sign = self._workspace_ready_to_sign(workspace)
        message_box = self._bindings.q_message_box
        question = getattr(message_box, "question", None)
        if not callable(question):
            return False
        title = "Discard unsigned signing draft?"
        action_text = {"open": "open another PDF", "exit": "exit FoliaSeal"}.get(
            action, "close this document"
        )
        choice_text = (
            f"Sign and save it before {action_text}"
            if ready_to_sign
            else f"{action_text} without saving"
        )
        body = f"Continue editing, discard this unsigned signing draft, or {choice_text}?"
        decision = self._ask_workspace_decision(
            message_box,
            parent=self.window,
            question=question,
            title=title,
            text=body,
            offer_save=ready_to_sign,
        )
        if decision == "continue":
            return False
        if ready_to_sign and decision == "save":
            return self._sign_and_save_current_workspace(workspace)
        if decision == "discard":
            workspace.maintenance.discard_draft()
            return True
        return False

    def _workspace_ready_to_sign(self, workspace: WorkspaceHandle) -> bool:
        try:
            return bool(workspace.session.preview().can_submit)
        except Exception:
            return False

    def _sign_and_save_current_workspace(self, workspace: WorkspaceHandle) -> bool:
        workspace.session.submit_sign_request()
        result = workspace.session.snapshot().last_signing_result
        return bool(result is not None and result.success)

    @classmethod
    def _ask_workspace_decision(
        cls,
        message_box: Any,
        *,
        parent: Any,
        question: Callable[..., Any],
        title: str,
        text: str,
        offer_save: bool,
    ) -> str:
        """Return ``continue``, ``discard``, or ``save`` from the lifecycle prompt."""
        custom_decision = cls._ask_workspace_decision_with_custom_buttons(
            message_box,
            parent=parent,
            title=title,
            text=text,
            offer_save=offer_save,
        )
        if custom_decision is not None:
            return custom_decision

        discard_value = cls._message_box_button(message_box, "Discard", "Yes")
        cancel_value = cls._message_box_button(message_box, "Cancel", "No")
        save_value = cls._message_box_button(message_box, "Save", "Save")
        buttons = [discard_value, cancel_value]
        if offer_save and save_value is not None:
            buttons.insert(0, save_value)
        result = cls._question_with_buttons(
            question,
            parent=parent,
            title=title,
            text=text,
            buttons=buttons,
            default_button=cancel_value,
        )
        if result == discard_value:
            return "discard"
        if offer_save and result == save_value:
            return "save"
        return "continue"

    @staticmethod
    def _ask_workspace_decision_with_custom_buttons(
        message_box: Any,
        *,
        parent: Any,
        title: str,
        text: str,
        offer_save: bool,
    ) -> str | None:
        """Use explicit consequence-verb buttons when the real QMessageBox is available."""
        if not isinstance(message_box, type):
            return None
        try:
            dialog = message_box(parent)
        except Exception:
            return None
        add_button = getattr(dialog, "addButton", None)
        if not callable(add_button):
            return None
        role_type = getattr(message_box, "ButtonRole", None)
        if role_type is None:
            return None
        try:
            continue_button = add_button("Continue editing", role_type.RejectRole)
            discard_button = add_button("Discard draft", role_type.DestructiveRole)
            save_button = add_button("Sign and save", role_type.AcceptRole) if offer_save else None
            dialog.setWindowTitle(title)
            dialog.setText(text)
            set_default = getattr(dialog, "setDefaultButton", None)
            if callable(set_default):
                set_default(continue_button)
            exec_method = getattr(dialog, "exec", None) or getattr(dialog, "exec_", None)
            if not callable(exec_method):
                return None
            exec_method()
            clicked = getattr(dialog, "clickedButton", lambda: None)()
        except Exception:
            return None
        if clicked is discard_button:
            return "discard"
        if save_button is not None and clicked is save_button:
            return "save"
        if clicked is continue_button:
            return "continue"
        return "continue"

    @staticmethod
    def _message_box_button(message_box: Any, name: str, fallback: str) -> Any:
        value = getattr(message_box, name, None)
        if value is not None:
            return value
        return getattr(getattr(message_box, "StandardButton", None), name, None) or getattr(
            message_box, fallback, None
        )

    @staticmethod
    def _question_with_buttons(
        question: Callable[..., Any],
        *,
        parent: Any,
        title: str,
        text: str,
        buttons: list[Any],
        default_button: Any,
    ) -> Any:
        usable_buttons = [button for button in buttons if button is not None]
        if len(usable_buttons) >= 2:
            try:
                combined = usable_buttons[0]
                for button in usable_buttons[1:]:
                    combined = combined | button
                return question(parent, title, text, combined, default_button)
            except TypeError:
                pass
        return question(parent, title, text)

    def _handle_window_close_event(self, event: Any) -> None:
        """Route native main-window close through the same draft policy as File > Close."""
        if self._confirm_discard_if_dirty(action="close"):
            self._close_document_signatures()
            self._workspace_host.close()
            accept = getattr(event, "accept", None)
            if callable(accept):
                accept()
            return
        ignore = getattr(event, "ignore", None)
        if callable(ignore):
            ignore()

    def _go_to_previous_page(self) -> None:
        self._with_current_session_port(lambda session: session.go_to_previous_page())
        self._sync_page_navigation_actions()

    def _go_to_next_page(self) -> None:
        self._with_current_session_port(lambda session: session.go_to_next_page())
        self._sync_page_navigation_actions()

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
            certificate_catalog=self._certificate_catalog_store.load_catalog(),
            certificate_catalog_provider=self._certificate_catalog_store.load_catalog,
            initial_catalog=self._app_settings.ui_settings.library_last_catalog,
            library_sort=self._app_settings.ui_settings.library_sort.value,
            on_preferences_changed=self._persist_library_preferences,
            on_toggle_certificate_pin=self._toggle_certificate_pin,
            on_rename_certificate=self._rename_certificate,
            on_delete_certificate=self._delete_certificate,
            on_configure_certificate=self._configure_certificate,
            on_create_appearance=self._open_appearance_profile_editor,
            on_edit_appearance=self._edit_appearance_profile,
            on_create=self._open_signature_preset_editor,
            on_edit=self._edit_signature_preset,
            on_create_placement=self._open_placement_profile_editor,
            on_edit_placement=self._edit_placement_profile,
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

    def _persist_library_preferences(self, catalog: str, sort: str) -> None:
        """Persist Library navigation/sort without restoring its open session."""

        ui = self._app_settings.ui_settings
        updated_ui = AppUiSettings(
            appearance_mode=ui.appearance_mode,
            main_window_geometry=ui.main_window_geometry,
            library_last_catalog=catalog.strip().lower() or "presets",
            library_sort=ui.library_sort.__class__.from_value(sort),
        )
        ui_mapping = updated_ui.to_mapping(self._app_settings.ui)
        ui_mapping["library_last_catalog"] = updated_ui.library_last_catalog
        ui_mapping["library_sort"] = updated_ui.library_sort.value
        self._app_settings = AppSettings(
            schema_version=self._app_settings.schema_version,
            default_output_directory=self._app_settings.default_output_directory,
            default_open_directory=self._app_settings.default_open_directory,
            linux_packaging_channel=self._app_settings.linux_packaging_channel,
            ui=ui_mapping,
        )
        try:
            self._app_settings_store.save_settings(self._app_settings)
        except (ConfigValidationError, OSError, ValueError) as exc:
            self._emit_error(f"Unable to save Library preferences: {exc}")

    def _toggle_certificate_pin(self, ref: CertificateLibraryRef, pinned: bool) -> bool:
        try:
            catalog = self._certificate_catalog_store.load_catalog()
            has_managed = any(
                item.managed_certificate_id == ref.object_id
                for item in catalog.managed_certificates
            )
            updated = (
                catalog.set_managed_certificate_pinned(ref.object_id, pinned)
                if has_managed
                else catalog
            )
            if ref.configuration_id is not None:
                updated = updated.set_configuration_pinned(ref.configuration_id, pinned)
            elif not has_managed:
                raise ConfigValidationError("Certificate entry is no longer available.")
            self._certificate_catalog_store.save_catalog(updated)
            return True
        except (ConfigValidationError, KeyError, OSError) as exc:
            self._emit_error(f"Unable to update certificate pin: {exc}")
            return False

    def _rename_certificate(self, ref: CertificateLibraryRef, new_name: str) -> bool:
        try:
            catalog = self._certificate_catalog_store.load_catalog()
            normalized = new_name.strip()
            if not normalized:
                raise ConfigValidationError("Certificate name is required.")
            certificate = next(
                (
                    item
                    for item in catalog.managed_certificates
                    if item.managed_certificate_id == ref.object_id
                ),
                None,
            )
            if any(
                item.managed_certificate_id != ref.object_id
                and item.display_name.casefold() == normalized.casefold()
                for item in catalog.managed_certificates
            ):
                raise ConfigValidationError(f"Certificate '{normalized}' already exists.")
            updated = (
                catalog.upsert_managed_certificate(replace(certificate, display_name=normalized))
                if certificate is not None
                else catalog
            )
            if ref.configuration_id is not None:
                configuration = catalog.configuration_by_id(ref.configuration_id)
                if any(
                    item.certificate_configuration_id != ref.configuration_id
                    and item.display_name.casefold() == normalized.casefold()
                    for item in catalog.certificate_configurations
                ):
                    raise ConfigValidationError(
                        f"Certificate configuration '{normalized}' already exists."
                    )
                updated = updated.upsert_configuration(
                    replace(configuration, display_name=normalized)
                )
            elif certificate is None:
                raise ConfigValidationError("Certificate entry is no longer available.")
            self._certificate_catalog_store.save_catalog(updated)
            return True
        except (ConfigValidationError, KeyError, OSError, ValueError) as exc:
            self._emit_error(f"Unable to rename certificate: {exc}")
            return False

    def _delete_certificate(self, ref: CertificateLibraryRef) -> bool:
        try:
            if (
                ref.configuration_id is not None
                and ref.configuration_id in self._referenced_preset_configuration_ids()
            ):
                self._emit_error(
                    "Certificate configuration is referenced by a signature preset "
                    "and cannot be deleted."
                )
                return False
            if ref.configuration_id is not None:
                self._certificate_manager.delete_configuration(ref.configuration_id)
            else:
                self._certificate_manager.delete_managed_certificate(ref.object_id)
            return True
        except (ConfigValidationError, KeyError, OSError, ValueError) as exc:
            self._emit_error(f"Unable to delete certificate: {exc}")
            return False

    def _configure_certificate(self, ref: CertificateLibraryRef) -> bool:
        """Create a signing configuration for a retained managed certificate file."""
        if ref.configuration_id is not None:
            self._emit_error("Certificate is already configured for signing.")
            return False
        catalog = self._certificate_catalog_store.load_catalog()
        try:
            certificate = catalog.managed_certificate_by_id(ref.object_id)
        except KeyError:
            self._emit_error("The retained certificate file is no longer available.")
            return False
        input_dialog = getattr(self._bindings, "q_input_dialog", None)
        get_text = getattr(input_dialog, "getText", None)
        if not callable(get_text):
            self._emit_error("Certificate configuration naming is unavailable.")
            return False
        selected = get_text(
            self.window,
            "Configure certificate",
            "Display name",
        )
        if isinstance(selected, tuple):
            name, accepted = selected
        else:
            name, accepted = selected, True
        if not accepted:
            return False
        try:
            result = self._certificate_manager.configure_managed_certificate(
                ConfigureCertificateRequest(
                    managed_certificate_id=certificate.managed_certificate_id,
                    display_name=str(name),
                )
            )
        except (ConfigValidationError, KeyError, OSError, ValueError) as exc:
            self._emit_error(f"Unable to configure certificate: {exc}")
            return False
        self._refresh_shell_certificate_configurations()
        self._show_information(
            f"Certificate configuration '{result.certificate_configuration.display_name}' created."
            if result.certificate_configuration is not None
            else "Certificate configured for signing."
        )
        return True

    def show_document_signatures(self) -> Any | None:
        """Open or refresh the one modeless Document Signatures surface."""

        workspace = self._workspace_host.active()
        if workspace is None:
            return None
        if self._document_signatures_dialog is not None:
            self._document_signatures_dialog.refresh(workspace.session.document_review_state())
            return self._document_signatures_dialog.show()
        self._document_signatures_dialog = DocumentSignaturesDialog(
            bindings=self._bindings,
            parent=self.window,
            state=workspace.session.document_review_state(),
            on_select=self._select_document_signature,
            on_close=self._close_document_signatures,
        )
        return self._document_signatures_dialog.show()

    def _select_document_signature(self, signature_id: str) -> None:
        workspace = self._workspace_host.active()
        if workspace is None:
            return
        state = workspace.session.select_document_review_item(signature_id)
        if self._document_signatures_dialog is not None:
            self._document_signatures_dialog.refresh(state)
        workspace.session.focus()

    def _close_document_signatures(self) -> None:
        if self._closing_document_signatures:
            return
        self._closing_document_signatures = True
        dialog = self._document_signatures_dialog
        self._document_signatures_dialog = None
        try:
            workspace = self._workspace_host.active()
            if workspace is not None:
                clear_highlight = getattr(
                    workspace.session,
                    "clear_document_review_highlight",
                    None,
                )
                if callable(clear_highlight):
                    clear_highlight()
            if dialog is not None:
                close = getattr(dialog.controls.dialog, "close", None)
                if callable(close):
                    close()
        finally:
            self._closing_document_signatures = False

    def _open_signature_preset_editor(self) -> bool:
        return self._run_signature_preset_editor()

    def _open_appearance_profile_editor(self) -> bool:
        return self._run_appearance_profile_editor()

    def _edit_appearance_profile(self, ref: ReusableObjectRef) -> bool:
        return self._run_appearance_profile_editor(initial_ref=ref)

    def _run_appearance_profile_editor(
        self,
        *,
        initial_ref: ReusableObjectRef | None = None,
    ) -> bool:
        saved = False

        def on_saved() -> None:
            nonlocal saved
            saved = True
            if self._reusable_object_library is not None:
                self._reusable_object_library.refresh()

        editor = AppearanceProfileEditorDialog(
            bindings=self._bindings,
            parent=self.window,
            library=self._reusable_objects,
            initial_ref=initial_ref,
            on_saved=on_saved,
            on_error=self._emit_error,
        )
        editor.open()
        return saved

    def _edit_signature_preset(self, ref: ReusableObjectRef) -> bool:
        return self._run_signature_preset_editor(initial_ref=ref)

    def _run_signature_preset_editor(
        self,
        *,
        initial_ref: ReusableObjectRef | None = None,
    ) -> bool:
        saved = False

        def on_saved() -> None:
            nonlocal saved
            saved = True
            if self._reusable_object_library is not None:
                self._reusable_object_library.refresh()

        editor = SignaturePresetEditorDialog(
            bindings=self._bindings,
            parent=self.window,
            library=self._reusable_objects,
            certificate_catalog=self._certificate_catalog_store.load_catalog(),
            initial_ref=initial_ref,
            on_saved=on_saved,
            on_error=self._emit_error,
        )
        editor.open()
        return saved

    def _open_placement_profile_editor(self) -> bool:
        """Open a document-independent placement editor from the Library."""
        initial = PlacementEditorState.from_blank_page(
            visible_width_pt=612.0,
            visible_height_pt=792.0,
        )
        return self._run_placement_profile_editor(initial)

    def _edit_placement_profile(self, profile: PlacementProfile) -> bool:
        return self._run_placement_profile_editor(PlacementEditorState.from_profile(profile))

    def _run_placement_profile_editor(self, initial: PlacementEditorState) -> bool:
        if self._bindings.q_double_spin_box is None or self._bindings.q_spin_box is None:
            self._emit_error("The placement editor requires the Qt numeric-input bindings.")
            return False
        saved = False

        def save(profile: PlacementProfile) -> None:
            nonlocal saved
            self._reusable_objects.execute(
                SavePlacement(
                    name=profile.display_name,
                    rect=profile.rect,
                    source_page=profile.source_page,
                    page_number=profile.page_number,
                    pinned=profile.pinned,
                    placement_profile_id=profile.placement_profile_id,
                    overwrite=initial.placement_profile_id is not None,
                )
            )
            saved = True
            if self._reusable_object_library is not None:
                self._reusable_object_library.refresh()

        editor = PlacementProfileEditorDialog(
            bindings=self._bindings,
            parent=self.window,
            initial=initial,
            on_save=save,
            on_error=self._emit_error,
        )
        editor.open()
        return saved

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
        self._copy_selected_text_action = self._command_action(
            edit_menu,
            AppFrameCommandId.COPY,
            self._copy_selected_text_from_action,
            enabled=False,
            icon_name="copy.svg",
        )
        view_menu = menu_bar.addMenu("View")
        self._previous_page_action = self._command_action(
            view_menu,
            AppFrameCommandId.PREVIOUS_PAGE,
            self._go_to_previous_page,
            enabled=False,
        )
        self._next_page_action = self._command_action(
            view_menu,
            AppFrameCommandId.NEXT_PAGE,
            self._go_to_next_page,
            enabled=False,
        )
        self._text_selection_mode_action = self._command_action(
            view_menu,
            AppFrameCommandId.SELECT_TEXT,
            self._toggle_text_selection_mode_from_action,
            enabled=False,
            checkable=True,
            icon_name="text-select.svg",
        )
        self._fit_page_action = self._command_action(
            view_menu,
            AppFrameCommandId.FIT_PAGE,
            self._fit_page_view,
            enabled=False,
        )
        self._fit_width_action = self._command_action(
            view_menu,
            AppFrameCommandId.FIT_WIDTH,
            self._fit_width_view,
            enabled=False,
        )
        self._find_action = self._command_action(
            view_menu,
            AppFrameCommandId.FIND,
            self._focus_document_search,
            enabled=False,
        )
        self._document_signatures_action = self._command_action(
            view_menu,
            AppFrameCommandId.DOCUMENT_SIGNATURES,
            self.show_document_signatures,
            enabled=False,
        )
        settings_menu = menu_bar.addMenu("Settings")
        self._command_action(
            settings_menu,
            AppFrameCommandId.APPLICATION_SETTINGS,
            self.show_app_settings,
        )
        self._command_action(
            settings_menu,
            AppFrameCommandId.MANAGE_REUSABLE_OBJECTS,
            self.show_reusable_object_library,
        )
        self._command_action(
            settings_menu,
            AppFrameCommandId.CREATE_CERTIFICATE,
            self.show_certificate_creation,
        )
        self._command_action(
            settings_menu,
            AppFrameCommandId.IMPORT_CERTIFICATE,
            self.show_certificate_import,
        )
        self._command_action(
            settings_menu,
            AppFrameCommandId.MANAGE_CERTIFICATE_CONFIGURATIONS,
            self.show_certificate_management,
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
        checkable: bool = False,
        icon_name: str | None = None,
    ) -> Any:
        definition = command_definition(command_id)
        action = self._action(
            definition.mnemonic_text,
            callback,
            shortcut=definition.shortcut,
            enabled=enabled,
            checkable=checkable,
            icon_name=icon_name,
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
        if not self._confirm_discard_if_dirty(action="exit"):
            return None
        self._close_document_signatures()
        self._workspace_host.close()
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
        self._set_action_enabled(self._previous_page_action, state.previous_page_enabled)
        self._set_action_enabled(self._next_page_action, state.next_page_enabled)
        self._set_action_enabled(self._text_selection_mode_action, state.text_selection_enabled)
        self._set_action_checked(self._text_selection_mode_action, state.text_selection_checked)
        self._set_action_enabled(self._copy_selected_text_action, state.copy_selected_text_enabled)
        self._set_action_enabled(self._fit_page_action, state.workspace_open)
        self._set_action_enabled(self._fit_width_action, state.workspace_open)
        self._set_action_enabled(self._find_action, state.workspace_open)
        self._set_action_enabled(self._document_signatures_action, state.workspace_open)

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

    def _sync_page_navigation_actions(self) -> None:
        workspace = self._workspace_host.active()
        if workspace is None:
            self._apply_workspace_action_state(workspace_action_state_closed())
            return
        session = workspace.session
        self._apply_workspace_action_state(
            replace(
                self._workspace_action_state,
                previous_page_enabled=session.can_go_previous_page(),
                next_page_enabled=session.can_go_next_page(),
            )
        )
        self._sync_document_text_actions()

    def _sync_document_text_actions(self) -> None:
        workspace = self._workspace_host.active()
        if workspace is None:
            return
        maintenance = workspace.maintenance
        mode_getter = getattr(maintenance, "document_text_selection_mode_enabled", None)
        copy_getter = getattr(maintenance, "can_copy_selected_document_text", None)
        mode_enabled = (
            bool(mode_getter())
            if callable(mode_getter)
            else self._workspace_action_state.text_selection_checked
        )
        can_copy = (
            bool(copy_getter())
            if callable(copy_getter)
            else self._workspace_action_state.copy_selected_text_enabled
        )
        self._apply_workspace_action_state(
            workspace_action_state_with_document_text_result(
                self._workspace_action_state,
                selection_mode_enabled=mode_enabled,
                can_copy_selected_text=can_copy,
            )
        )

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
            self._sync_document_text_actions()
        return result

    def _fit_page_view(self) -> None:
        self._with_current_session_port(lambda session_port: session_port.fit_page_view())

    def _fit_width_view(self) -> None:
        self._with_current_session_port(lambda session_port: session_port.fit_width_view())

    def _focus_document_search(self) -> None:
        self._with_current_session_port(lambda session_port: session_port.focus_document_search())

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

    def _show_information(self, message: str) -> None:
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(self.window, "FoliaSeal", message)

    def _handle_status_change(self, status: str) -> None:
        if status == "navigation_changed":
            self._sync_page_navigation_actions()
        elif status in {"document_text_selection_changed", "document_text_mode_changed"}:
            self._sync_document_text_actions()
        if self._on_status_change is not None:
            self._on_status_change(status)

    def _apply_window_baseline(self) -> None:
        set_minimum_size = getattr(self.window, "setMinimumSize", None)
        if callable(set_minimum_size):
            set_minimum_size(*self.MAIN_WINDOW_MINIMUM_SIZE)
        ui_settings = self._app_settings.ui_settings
        apply_appearance_mode(
            mode=ui_settings.appearance_mode,
            q_application=self._bindings.q_application,
            q_palette=self._bindings.q_palette,
            q_color=self._bindings.q_color,
        )

    def restore_window_geometry(self) -> bool:
        """Restore the saved main-window rectangle before the frame is shown."""

        geometry = self._app_settings.ui_settings.main_window_geometry
        if geometry is None:
            self._restore_maximized = False
            return False

        x, y = geometry.x, geometry.y
        screen = self._window_screen()
        available_geometry = (
            getattr(screen, "availableGeometry", lambda: None)() if screen is not None else None
        )
        if available_geometry is not None:
            available_x = _qt_rect_value(available_geometry, "x")
            available_y = _qt_rect_value(available_geometry, "y")
            available_width = _qt_rect_value(available_geometry, "width")
            available_height = _qt_rect_value(available_geometry, "height")
            if None not in (
                available_x,
                available_y,
                available_width,
                available_height,
            ):
                x = min(
                    max(x, available_x),
                    max(available_x, available_x + available_width - geometry.width),
                )
                y = min(
                    max(y, available_y),
                    max(available_y, available_y + available_height - geometry.height),
                )

        set_geometry = getattr(self.window, "setGeometry", None)
        if callable(set_geometry):
            set_geometry(x, y, geometry.width, geometry.height)
        self._restore_maximized = geometry.maximized
        return True

    def apply_restored_window_state(self) -> None:
        """Apply the saved maximized state after the frame has been shown."""

        if not getattr(self, "_restore_maximized", False):
            return
        show_maximized = getattr(self.window, "showMaximized", None)
        if callable(show_maximized):
            show_maximized()

    def capture_window_geometry(self) -> AppSettings:
        """Capture the current main-window rectangle into the in-memory settings."""

        geometry_getter = getattr(self.window, "geometry", None)
        if not callable(geometry_getter):
            return self._app_settings
        rectangle = geometry_getter()
        values = {name: _qt_rect_value(rectangle, name) for name in ("x", "y", "width", "height")}
        if any(value is None for value in values.values()):
            return self._app_settings
        try:
            geometry = MainWindowGeometry(
                x=values["x"],
                y=values["y"],
                width=max(values["width"], MainWindowGeometry.MIN_WIDTH),
                height=max(values["height"], MainWindowGeometry.MIN_HEIGHT),
                maximized=bool(getattr(self.window, "isMaximized", lambda: False)()),
            )
        except (TypeError, ValueError):
            return self._app_settings
        ui_settings = AppUiSettings(
            appearance_mode=self._app_settings.ui_settings.appearance_mode,
            main_window_geometry=geometry,
            library_last_catalog=self._app_settings.ui_settings.library_last_catalog,
            library_sort=self._app_settings.ui_settings.library_sort,
        )
        self._app_settings = AppSettings(
            schema_version=self._app_settings.schema_version,
            default_output_directory=self._app_settings.default_output_directory,
            default_open_directory=self._app_settings.default_open_directory,
            linux_packaging_channel=self._app_settings.linux_packaging_channel,
            ui=ui_settings.to_mapping(self._app_settings.ui),
        )
        return self._app_settings

    def persist_captured_window_geometry(self) -> None:
        """Atomically save captured settings without preventing application shutdown."""

        try:
            self._app_settings_store.save_settings(self._app_settings)
        except (ConfigValidationError, OSError, ValueError) as exc:
            if self._on_error is not None:
                self._on_error(f"Unable to save window settings: {exc}")

    def _window_screen(self) -> Any | None:
        screen_getter = getattr(self.window, "screen", None)
        screen = screen_getter() if callable(screen_getter) else None
        if screen is not None:
            return screen
        application = self._bindings.q_application
        primary_screen = getattr(application, "primaryScreen", None)
        return primary_screen() if callable(primary_screen) else None

    def _apply_app_settings(self, settings: AppSettings) -> None:
        self._app_settings = settings
        self._apply_window_baseline()
        self._with_current_shell_port(lambda shell_port: shell_port.apply_app_settings(settings))

    def _refresh_shell_certificate_configurations(self) -> None:
        self._with_current_shell_port(
            lambda shell_port: shell_port.refresh_certificate_configurations()
        )

    def _refresh_shell_signature_profiles(self) -> None:
        self._with_current_shell_port(lambda shell_port: shell_port.refresh_signature_profiles())

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


def _qt_rect_value(rectangle: Any, name: str) -> int | None:
    """Read a QRect-like integer property from real or fake Qt objects."""

    value = getattr(rectangle, name, None)
    if not callable(value):
        return None
    result = value()
    return result if type(result) is int else None


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
        instance_coordinator: SingleInstanceCoordinator | None = None,
    ) -> int:
        q_application = self._bindings.q_application
        instance_getter = getattr(q_application, "instance", None)
        app = instance_getter() if callable(instance_getter) else None
        if app is None:
            launch_argv = list(argv) if argv is not None else list(sys.argv)
            if not launch_argv:
                launch_argv = ["foliaseal", "gui"]
            app = q_application(launch_argv)

        coordinator = instance_coordinator or self._build_instance_coordinator(
            app_settings_store=app_settings_store,
        )
        pending_requests: list[OpenRequest] = []
        frame_holder: list[Any] = []

        def handle_open_request(request: OpenRequest) -> None:
            if not frame_holder:
                pending_requests.append(request)
                return
            frame = frame_holder[0]
            if request.pdf_path is not None:
                frame.open_pdf_path(request.pdf_path)
            self._raise_frame_window(frame)

        coordinator.set_request_handler(handle_open_request)
        try:
            is_primary = coordinator.start_or_forward(request_for_path(initial_pdf_path))
            if not is_primary:
                return 0

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
            frame_holder.append(frame)
            restore_geometry = getattr(frame, "restore_window_geometry", None)
            if callable(restore_geometry):
                restore_geometry()
            show = getattr(frame.window, "show", None)
            if callable(show):
                show()
            apply_restored_state = getattr(frame, "apply_restored_window_state", None)
            if callable(apply_restored_state):
                apply_restored_state()
            if initial_pdf_path is not None:
                frame.open_pdf_path(initial_pdf_path)
            for request in pending_requests:
                handle_open_request(request)
            exec_method = getattr(app, "exec", None)
            if not callable(exec_method):
                return 0
            try:
                exit_code = int(exec_method())
            finally:
                capture_geometry = getattr(frame, "capture_window_geometry", None)
                if callable(capture_geometry):
                    capture_geometry()
                persist_geometry = getattr(frame, "persist_captured_window_geometry", None)
                if callable(persist_geometry):
                    persist_geometry()
            return exit_code
        finally:
            coordinator.close()

    def _build_instance_coordinator(
        self,
        *,
        app_settings_store: AppSettingsStore | None,
    ) -> SingleInstanceCoordinator:
        if self._bindings.q_local_server is None or self._bindings.q_local_socket is None:
            return NoopSingleInstanceCoordinator()
        store = app_settings_store or AppSettingsStore.default()
        return QtLocalInstanceCoordinator(
            endpoint=endpoint_name(store.storage_dir),
            q_local_server=self._bindings.q_local_server,
            q_local_socket=self._bindings.q_local_socket,
        )

    @staticmethod
    def _raise_frame_window(frame: Any) -> None:
        window = getattr(frame, "window", None)
        if window is None:
            return
        raise_window = getattr(window, "raise_", None)
        if callable(raise_window):
            raise_window()
        activate = getattr(window, "activateWindow", None)
        if callable(activate):
            activate()

    def _load_bindings(self) -> QtAppFrameBindings:
        try:
            qt_widgets = importlib.import_module("PySide6.QtWidgets")
            qt_gui = importlib.import_module("PySide6.QtGui")
            qt_network = importlib.import_module("PySide6.QtNetwork")
            qtpdf = importlib.import_module("PySide6.QtPdf")
        except Exception as exc:  # pragma: no cover - environment dependent
            raise QtAppFrameBindingsUnavailable(
                "PySide6 QtWidgets and QtPdf are required for the FoliaSeal app frame. "
                f"Details: {exc}"
            ) from exc

        q_main_window_base = getattr(qt_widgets, "QMainWindow")

        class _FoliaSealMainWindow(q_main_window_base):
            def closeEvent(self, event: Any) -> None:  # noqa: N802
                handler = getattr(self, "_foliaseal_close_event_handler", None)
                if callable(handler):
                    handler(event)
                    return
                super().closeEvent(event)

        return QtAppFrameBindings(
            q_main_window=_FoliaSealMainWindow,
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
            q_input_dialog=getattr(qt_widgets, "QInputDialog"),
            q_palette=getattr(qt_gui, "QPalette"),
            q_color=getattr(qt_gui, "QColor"),
            q_local_server=getattr(qt_network, "QLocalServer"),
            q_local_socket=getattr(qt_network, "QLocalSocket"),
            q_widget=getattr(qt_widgets, "QWidget"),
            q_hbox_layout=getattr(qt_widgets, "QHBoxLayout"),
            q_vbox_layout=getattr(qt_widgets, "QVBoxLayout"),
            q_list_widget=getattr(qt_widgets, "QListWidget"),
            q_splitter=getattr(qt_widgets, "QSplitter"),
            q_text_edit=getattr(qt_widgets, "QTextEdit"),
            q_double_spin_box=getattr(qt_widgets, "QDoubleSpinBox"),
            q_spin_box=getattr(qt_widgets, "QSpinBox"),
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
    instance_coordinator: SingleInstanceCoordinator | None = None,
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
        instance_coordinator=instance_coordinator,
    )
