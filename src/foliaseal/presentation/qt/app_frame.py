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
from foliaseal.infra.render import QtPdfRenderBackend
from foliaseal.infra.secret_storage import SecretToolCertificateSecretStore
from foliaseal.presentation.qt.app_frame_certificate_management import (
    AppFrameCertificateDialogService,
    CertificateDialogCompatibilityState,
    CertificateDialogPort,
)
from foliaseal.presentation.qt.app_frame_workspace_open import (
    OpenWorkspaceCommand,
    QtPdfPageCountLoader,
    SigningWorkspaceCompositionService,
    WorkspaceCompatibilityState,
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
class AppFrameDialogCompatibilityState:
    """Frame-owned dialog exposure retained for tests and compatibility callers."""

    settings_dialog: Any | None = None
    certificate_import_dialog: Any | None = None
    certificate_creation_dialog: Any | None = None
    certificate_management_dialog: Any | None = None


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
        shell_factory: SigningWorkspaceFactory | None = None,
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
        self._current_shell_port: SigningWorkspacePort | None = None
        self._current_workspace: WorkspaceCompatibilityState | None = None
        self._dialog_compatibility = AppFrameDialogCompatibilityState()
        self._open_action: Any | None = None
        self._save_as_action: Any | None = None

        self.window = bindings.q_main_window()
        self.window.setWindowTitle("FoliaSeal")
        self._certificate_dialog_port: CertificateDialogPort = (
            AppFrameCertificateDialogService(
                bindings=self._bindings,
                parent=self.window,
                lifecycle_service=self._certificate_lifecycle_service,
                refresh_shell_certificate_configurations=(
                    self._refresh_shell_certificate_configurations
                ),
            )
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
    def current_workspace(self) -> WorkspaceCompatibilityState | None:
        return self._current_workspace

    @property
    def current_shell(self) -> Any | None:
        workspace = self._current_workspace
        return None if workspace is None else workspace.shell_widget

    @property
    def current_viewer_workflow(self) -> ViewerWorkflow | None:
        workspace = self._current_workspace
        return None if workspace is None else workspace.viewer_workflow

    @property
    def current_signing_workflow(self) -> SigningDraftWorkflow | None:
        workspace = self._current_workspace
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
            outcome = self._workspace_open_port.open_workspace(
                OpenWorkspaceCommand(
                    source_pdf=Path(pdf_path),
                    app_settings=self._app_settings,
                    app_settings_store=self._app_settings_store,
                    certificate_catalog_store=self._certificate_catalog_store,
                    certificate_secret_provider=self._certificate_secret_provider,
                    preset_catalog_store=self._preset_catalog_store,
                    sign_executor=self._sign_executor,
                    on_sign_request=self._on_sign_request,
                    reopen_target=self.open_pdf_path,
                    on_error=self._emit_error,
                    on_status_change=self._on_status_change,
                )
            )
        except Exception as exc:
            self._emit_error(f"Unable to open PDF: {exc}")
            return None

        self._current_shell_port = outcome.shell_port
        self._current_workspace = outcome.compatibility
        self.window.setCentralWidget(outcome.compatibility.shell_widget)
        self._set_save_as_enabled(True)
        return outcome.compatibility.shell_widget

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
        return self._with_current_shell_port(
            lambda shell_port: shell_port.choose_output_pdf_path()
        )

    def _set_save_as_enabled(self, enabled: bool) -> None:
        action = self._save_as_action
        if action is None:
            return
        set_enabled = getattr(action, "setEnabled", None)
        if callable(set_enabled):
            set_enabled(enabled)

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
        label = self._bindings.q_label("Open a PDF to begin signing.")
        if hasattr(label, "setWordWrap"):
            label.setWordWrap(True)
        self.window.setCentralWidget(label)
        self._set_save_as_enabled(False)

    def _emit_error(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.window, "FoliaSeal", message)

    def _apply_app_settings(self, settings: AppSettings) -> None:
        self._app_settings = settings
        self._with_current_shell_port(
            lambda shell_port: shell_port.apply_app_settings(settings)
        )

    def _refresh_shell_certificate_configurations(self) -> None:
        self._with_current_shell_port(
            lambda shell_port: shell_port.refresh_certificate_configurations()
        )

    def _with_current_shell_port(
        self,
        action: Callable[[SigningWorkspacePort], Any | None],
    ) -> Any | None:
        shell_port = self._current_shell_port
        if shell_port is None:
            return None
        return action(shell_port)


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

    def create(
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
    ) -> Any:
        """Build and return the raw Qt window for compatibility callers."""

        return self.create_frame(
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
    shell_factory: SigningWorkspaceFactory | None = None,
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
