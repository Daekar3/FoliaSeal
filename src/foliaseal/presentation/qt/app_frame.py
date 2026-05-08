"""Qt application-frame wrapper for the FoliaSeal signing GUI."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.infra.render import QtPdfRenderBackend
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
    q_label: type[Any]
    q_file_dialog: Any
    q_message_box: Any
    q_action: type[Any]
    qpdf_document: type[Any]


class FoliaSealAppFrame:
    """Application frame that owns top-level menus and document opening."""

    def __init__(
        self,
        *,
        bindings: QtAppFrameBindings,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
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
        self._certificate_catalog_store = certificate_catalog_store
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

        self.window = bindings.q_main_window()
        self.window.setWindowTitle("FoliaSeal")
        self._install_menus()
        self._set_placeholder()

        self.window.open_file = self.choose_open_pdf  # type: ignore[attr-defined]
        self.window.open_pdf_path = self.open_pdf_path  # type: ignore[attr-defined]
        self.window.show_app_settings = self.show_app_settings  # type: ignore[attr-defined]
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
                    Path(self._app_settings.default_output_directory)
                    / f"{source_path.stem}-signed.pdf"
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
                preset_catalog_store=self._preset_catalog_store,
                app_settings=self._app_settings,
                app_settings_store=self._app_settings_store,
                sign_executor=self._sign_executor,
                on_sign_request=self._on_sign_request,
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
        return shell

    def show_app_settings(self) -> None:
        message = (
            "Application settings\n\n"
            f"Default open folder: {self._app_settings.default_open_directory}\n"
            f"Default output folder: {self._app_settings.default_output_directory}\n"
            f"Settings file: {self._app_settings_store.settings_path}"
        )
        information = getattr(self._bindings.q_message_box, "information", None)
        if callable(information):
            information(self.window, "Application settings", message)

    def _install_menus(self) -> None:
        menu_bar = self.window.menuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction(self._action("Open file", self.choose_open_pdf))
        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.addAction(
            self._action("Application settings", self.show_app_settings)
        )

    def _action(self, text: str, callback: Callable[[], Any]) -> Any:
        action = self._bindings.q_action(text, self.window)
        triggered = getattr(action, "triggered", None)
        if hasattr(triggered, "connect"):
            triggered.connect(callback)
        return action

    def _set_placeholder(self) -> None:
        label = self._bindings.q_label("Open a PDF to begin signing.")
        if hasattr(label, "setWordWrap"):
            label.setWordWrap(True)
        self.window.setCentralWidget(label)

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
            preset_catalog_store=preset_catalog_store,
            sign_executor=sign_executor,
            on_sign_request=on_sign_request,
            on_error=on_error,
            on_status_change=on_status_change,
        ).container

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
            q_label=getattr(qt_widgets, "QLabel"),
            q_file_dialog=getattr(qt_widgets, "QFileDialog"),
            q_message_box=getattr(qt_widgets, "QMessageBox"),
            q_action=getattr(qt_gui, "QAction"),
            qpdf_document=getattr(qtpdf, "QPdfDocument"),
        )


def build_qt_app_frame(
    *,
    app_settings: AppSettings | None = None,
    app_settings_store: AppSettingsStore | None = None,
    certificate_catalog_store: CertificateCatalogStore | None = None,
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
        preset_catalog_store=preset_catalog_store,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )
