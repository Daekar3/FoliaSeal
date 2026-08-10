"""Qt signing shell for the FoliaSeal signing workspace."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from foliaseal.application import (
    SigningDraftPreview as _SigningDraftPreview,
)
from foliaseal.application import (
    SigningDraftWorkflow,
)
from foliaseal.application import (
    WorkspaceInteractionSession as _WorkspaceInteractionSession,
)
from foliaseal.application.certificate_catalog_repository import CertificateCatalogRepository
from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.document_review import (
    DocumentReviewInspector,
    DocumentReviewSummary,
)
from foliaseal.application.document_text_search import (
    DocumentTextSearchEngine,
    DocumentTextSearchState,
)
from foliaseal.application.document_text_selection import (
    DocumentTextSelectionEngine,
    DocumentTextSelectionState,
)
from foliaseal.application.reusable_signing_objects import ReusableSigningObjects
from foliaseal.application.signature_properties_coordinator import (
    SignaturePropertiesCoordinatorError as _SignaturePropertiesCoordinatorError,
)
from foliaseal.application.signing_material_resolver import (
    CertificateSigningMaterialPort,
)
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession as _ViewerInteractionSession,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
    SigningRequest,
    SigningResult,
)
from foliaseal.domain.models import (
    SignatureFieldKey as _SignatureFieldKey,
)
from foliaseal.domain.models import (
    SignatureFieldSource as _SignatureFieldSource,
)
from foliaseal.domain.models import (
    SignatureLayoutTemplate as _SignatureLayoutTemplate,
)
from foliaseal.domain.models import (
    SignatureTextStyle as _SignatureTextStyle,
)
from foliaseal.domain.models import (
    SignatureTimezoneDisplayMode as _SignatureTimezoneDisplayMode,
)
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signature_preview_layout import (
    _preview_stamp_text as _preview_stamp_text_impl,
)
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    QtCanonicalPreviewLifecycle as _QtCanonicalPreviewLifecycle,
)
from foliaseal.presentation.qt.signing_action_boundary import (
    SigningActionBoundary as _SigningActionBoundary,
)
from foliaseal.presentation.qt.signing_workspace_composition import (
    QtSigningWorkspaceComposition,
    QtSigningWorkspaceCompositionRequest,
    QtSigningWorkspaceHostActions,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import (
    SigningWorkspaceSnapshot,
)
from foliaseal.presentation.qt.signing_workspace_shell_controller import (
    SigningWorkspaceShellController,
)
from foliaseal.presentation.qt.signing_workspace_sidebar import (
    SigningWorkspaceSidebar as _SigningWorkspaceSidebar,
)
from foliaseal.presentation.qt.viewer_widget import (
    build_qt_pdf_viewer_widget as _build_qt_pdf_viewer_widget,
)

CERTIFICATE_CONFIGURATION_PLACEHOLDER = "Choose a certificate configuration"
SigningDraftPreview = _SigningDraftPreview
SignatureFieldKey = _SignatureFieldKey
SignatureFieldSource = _SignatureFieldSource
SignatureLayoutTemplate = _SignatureLayoutTemplate
SignaturePropertiesCoordinatorError = _SignaturePropertiesCoordinatorError
SignatureTextStyle = _SignatureTextStyle
SignatureTimezoneDisplayMode = _SignatureTimezoneDisplayMode
WorkspaceInteractionSession = _WorkspaceInteractionSession
ViewerInteractionSession = _ViewerInteractionSession
SigningActionBoundary = _SigningActionBoundary
SigningWorkspaceSidebar = _SigningWorkspaceSidebar
QtCanonicalPreviewLifecycle = _QtCanonicalPreviewLifecycle
build_qt_pdf_viewer_widget = _build_qt_pdf_viewer_widget
_preview_stamp_text = _preview_stamp_text_impl


class QtSigningBindingsUnavailable(RuntimeError):
    """Raised when PySide6 widget bindings are unavailable."""


@dataclass(frozen=True)
class QtSigningWidgetBindings:
    """Dynamically imported PySide6 symbols used by the signing shell."""

    q_widget: type[Any]
    q_vbox_layout: type[Any]
    q_hbox_layout: type[Any]
    q_form_layout: type[Any]
    q_scroll_area: type[Any]
    q_group_box: type[Any]
    q_label: type[Any]
    q_line_edit: type[Any]
    q_check_box: type[Any]
    q_combo_box: type[Any]
    q_file_dialog: Any
    q_input_dialog: Any
    q_message_box: type[Any]
    q_dialog: type[Any]
    q_icon: type[Any]
    q_pixmap: type[Any]
    q_double_spin_box: type[Any]
    q_spin_box: type[Any]
    q_push_button: type[Any]
    qt: Any
    q_shortcut: type[Any] | None = None
    q_key_sequence: type[Any] | None = None

class SigningRequestExecutor(Protocol):
    """Executes a validated signing request and returns a signing result."""

    def execute(self, request: SigningRequest) -> SigningResult:
        """Apply the signing request and return the result."""


def _build_close_aware_widget(
    widget_cls: type[Any],
    *,
    on_close: Callable[[], None],
) -> Any:
    close_handled = False

    def _handle_close() -> None:
        nonlocal close_handled
        if close_handled:
            return
        close_handled = True
        on_close()

    class _CloseAwareWidget(widget_cls):  # type: ignore[misc,valid-type]
        def close(self):  # type: ignore[override]
            _handle_close()
            close_method = getattr(super(), "close", None)
            if callable(close_method):
                return close_method()
            return None

        def closeEvent(self, event: Any) -> None:  # noqa: N802
            _handle_close()
            close_event = getattr(super(), "closeEvent", None)
            if callable(close_event):
                close_event(event)

    return _CloseAwareWidget()


class SigningWorkspaceWidget:
    """Composite widget that combines the viewer and signature editor."""

    def __init__(
        self,
        *,
        bindings: QtSigningWidgetBindings,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        certificate_catalog: CertificateCatalog | None = None,
        certificate_catalog_store: CertificateCatalogRepository | None = None,
        certificate_material_port: CertificateSigningMaterialPort | None = None,
        reusable_objects: ReusableSigningObjects | None = None,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        document_review_inspector: DocumentReviewInspector | None = None,
        document_text_selection_engine: DocumentTextSelectionEngine | None = None,
        document_text_search_engine: DocumentTextSearchEngine | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_open_signed_output: Callable[[str], Any] | None = None,
        on_copy_text: Callable[[str], Any] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
        on_open_signature_library: Callable[[], Any] | None = None,
        untrusted_recovery: bool = False,
    ) -> None:
        if reusable_objects is None:
            raise ValueError("reusable_objects is required for the signing workspace widget.")
        self._bindings = bindings
        self._viewer_workflow = viewer_workflow
        self._draft_workflow = signing_workflow
        self._on_sign_request = on_sign_request
        self._on_open_signed_output = on_open_signed_output
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._app_settings_store = app_settings_store
        self._on_copy_text = on_copy_text
        if app_settings is not None:
            self._app_settings = app_settings
        elif app_settings_store is not None:
            self._app_settings = app_settings_store.load_settings()
        else:
            self._app_settings = AppSettings.default()
        self.widget = _build_close_aware_widget(
            bindings.q_widget,
            on_close=self._dispose_composition,
        )
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)
        composition = QtSigningWorkspaceComposition.from_request(
            QtSigningWorkspaceCompositionRequest(
                bindings=bindings,
                widget=self.widget,
                layout=self._layout,
                viewer_workflow=viewer_workflow,
                signing_workflow=signing_workflow,
                certificate_catalog=certificate_catalog,
                certificate_catalog_store=certificate_catalog_store,
                certificate_material_port=certificate_material_port,
                reusable_objects=reusable_objects,
                app_settings=self._app_settings,
                app_settings_store=app_settings_store,
                document_review_inspector=document_review_inspector,
                document_text_selection_engine=document_text_selection_engine,
                document_text_search_engine=document_text_search_engine,
                sign_executor=sign_executor,
                on_sign_request=on_sign_request,
                on_open_signed_output=on_open_signed_output,
                on_copy_text=on_copy_text,
                on_error=on_error,
                on_status_change=on_status_change,
                on_open_signature_library=on_open_signature_library,
                untrusted_recovery=untrusted_recovery,
                viewer_widget_builder=build_qt_pdf_viewer_widget,
                host_actions=QtSigningWorkspaceHostActions(
                    choose_output_pdf_path=self.choose_output_pdf_path,
                    submit_sign_request=self.submit_sign_request,
                    open_signed_output=self.open_signed_output,
                    search_document_text=self.search_document_text,
                    previous_document_text_match=self.previous_document_text_match,
                    next_document_text_match=self.next_document_text_match,
                    copy_current_document_text_match=self.copy_current_document_text_match,
                    set_document_text_selection_mode=self.set_document_text_selection_mode,
                    copy_selected_document_text=self.copy_selected_document_text,
                    clear_selected_document_text=self.clear_selected_document_text,
                    get_app_settings=lambda: self._app_settings,
                    set_app_settings=lambda settings: setattr(self, "_app_settings", settings),
                ),
            )
        )
        self._composition_boundary = composition
        self._shell_controller = SigningWorkspaceShellController.build(
            widget=self.widget,
            compose=composition.build,
        )
        self._shell_controller.install_into(self)
        self._shell_controller.bootstrap()

    def _dispose_composition(self) -> None:
        composition = getattr(self, "_composition_boundary", None)
        if composition is not None:
            composition.dispose()
            return
        properties_panel = getattr(self, "_properties_panel", None)
        dispose = getattr(properties_panel, "dispose", None)
        if callable(dispose):
            dispose()

    @property
    def container(self) -> Any:
        return self.widget

    @property
    def layout(self) -> Any:
        return self._layout

    def close(self) -> Any:
        """Close the mounted Qt container and release shell-owned resources."""
        return self._shell_controller.close()

    def has_unsaved_changes(self) -> bool:
        """Expose the draft's typed dirty projection to the frame lifecycle."""
        return self._draft_workflow.has_unsaved_changes

    def discard_draft(self) -> None:
        """Clear the draft and session credentials before lifecycle disposal."""
        self.cleanup_recovery_artifact()
        self._draft_workflow.discard_draft()

    def cleanup_recovery_artifact(self) -> None:
        """Release a preserved recovery artifact without changing draft state."""
        self._composition_boundary.action_bridge.cleanup_recovery_artifact()

    def clear_session_secrets(self) -> None:
        """Clear credentials retained for this mounted signing session."""
        self._draft_workflow.clear_session_secrets()

    def setFocus(self) -> Any:  # noqa: N802
        """Focus the mounted Qt container for harness/session interactions."""
        focus = getattr(self.widget, "setFocus", None)
        return focus() if callable(focus) else None

    @property
    def viewer_widget(self) -> Any:
        return self._viewer_widget

    @property
    def properties_panel(self) -> Any:
        return self._properties_panel

    @property
    def viewer_navigation_controls(self) -> Any:
        return self._viewer_navigation_controls

    @property
    def sidebar(self) -> Any:
        return self._sidebar.container

    @property
    def sidebar_surface(self) -> Any:
        return self._sidebar.surface

    @property
    def properties_scroll(self) -> Any:
        return self._properties_scroll

    @property
    def app_settings(self) -> AppSettings:
        return self._app_settings

    @property
    def testing_adapter(self) -> Any:
        """Expose the explicit harness adapter at the typed Qt edge."""
        return self._testing_adapter

    def refresh_viewer(self) -> None:
        self._runtime.refresh_viewer()

    def go_to_previous_page(self) -> None:
        target = max(self._viewer_workflow.session.current_page - 1, 0)
        self._runtime.refresh_review_jump_to_page_index(target)

    def go_to_next_page(self) -> None:
        target = min(
            self._viewer_workflow.session.current_page + 1,
            self._viewer_workflow.session.page_count - 1,
        )
        self._runtime.refresh_review_jump_to_page_index(target)

    def can_go_previous_page(self) -> bool:
        return self._viewer_workflow.session.can_go_previous()

    def can_go_next_page(self) -> bool:
        return self._viewer_workflow.session.can_go_next()

    def reset_zoom_view(self) -> None:
        self._viewer_widget.reset_zoom_view()

    def fit_page_view(self) -> None:
        self._viewer_widget.fit_page_view()

    def fit_width_view(self) -> None:
        self._viewer_widget.fit_width_view()

    def refresh_document_review(self) -> DocumentReviewSummary:
        return self._runtime.refresh_document_review()

    def document_review_state(self) -> Any:
        return self._runtime.document_review_state()

    def select_document_review_item(self, signature_id: str) -> Any:
        return self._runtime.select_document_review_item(signature_id)

    def clear_document_review_highlight(self) -> None:
        self._runtime.clear_document_review_highlight()

    def search_document_text(self) -> DocumentTextSearchState:
        return self._runtime.search_document_text()

    def focus_document_search(self) -> None:
        self._runtime.focus_document_search()

    def next_document_text_match(self) -> DocumentTextSearchState:
        return self._runtime.next_document_text_match()

    def previous_document_text_match(self) -> DocumentTextSearchState:
        return self._runtime.previous_document_text_match()

    def copy_current_document_text_match(self) -> str | None:
        return self._runtime.copy_current_document_text_match()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self._runtime.set_document_text_selection_mode(enabled)

    def set_viewer_interaction_mode(self, mode: str) -> str:
        return self._runtime.set_viewer_interaction_mode(mode)

    def document_text_selection_mode_enabled(self) -> bool:
        return self._runtime.document_text_selection_mode_enabled()

    def can_copy_selected_document_text(self) -> bool:
        return self._runtime.can_copy_selected_document_text()

    def copy_selected_document_text(self) -> str | None:
        return self._runtime.copy_selected_document_text()

    def clear_selected_document_text(self) -> DocumentTextSelectionState:
        return self._runtime.clear_selected_document_text()

    def apply_app_settings(self, settings: AppSettings) -> None:
        self._shell_surface.apply_app_settings(settings)

    def set_logical_page_index(self, page_index: int) -> None:
        self._runtime.set_logical_page_index(page_index)

    def logical_page_index(self) -> int:
        return self._runtime.logical_page_index()

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
        ) -> SignatureRect:
        return self._runtime.set_signature_rect(
            page_index=page_index,
            left_pt=left_pt,
            bottom_pt=bottom_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        )

    def signature_rect(self) -> SignatureRect | None:
        return self._runtime.signature_rect()

    def set_selected_certificate_configuration_id(self, configuration_id: str | None) -> None:
        self._runtime.set_selected_certificate_configuration_id(configuration_id)

    def selected_certificate_configuration_id(self) -> str | None:
        return self._runtime.selected_certificate_configuration_id()

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._runtime.signature_appearance()

    def set_timestamp_required(self, required: bool) -> None:
        self._runtime.set_timestamp_required(required)

    def current_request(self) -> SigningRequest | None:
        return self._runtime.current_request()

    def preview(self) -> _SigningDraftPreview:
        """Return the current read-only signing preview."""
        return self.properties_panel.preview()

    def snapshot(self) -> SigningWorkspaceSnapshot:
        """Return one coherent primary-workflow snapshot."""
        return self._runtime.snapshot(last_signing_result=self.last_signing_result)

    def is_sign_action_enabled(self) -> bool:
        return self._runtime.is_sign_action_enabled()

    def submit_sign_request(self) -> SigningRequest | None:
        return self._shell_surface.submit_sign_request()

    def open_signed_output(self) -> str | None:
        return self._shell_surface.open_signed_output()

    def choose_output_pdf_path(self) -> str | None:
        return self._shell_surface.choose_output_pdf_path()

    def has_explicit_output_pdf_path(self) -> bool:
        return self._shell_surface.has_explicit_output_pdf_path()

    @property
    def last_signing_result(self) -> SigningResult | None:
        """Return the most recent signing result, if a real executor ran."""
        return self._signing_action_coordinator.last_signing_result

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self._shell_surface.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> None:
        """Refresh reusable signing-profile selectors after Settings changes."""
        self._shell_surface.refresh_signature_profiles()


class SigningShellAdapter:
    """Factory for the FoliaSeal Qt signing shell."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create(
        self,
        *,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        reusable_objects: ReusableSigningObjects,
        certificate_catalog: CertificateCatalog | None = None,
        certificate_catalog_store: CertificateCatalogRepository | None = None,
        certificate_material_port: CertificateSigningMaterialPort | None = None,
        app_settings: AppSettings | None = None,
        app_settings_store: AppSettingsStore | None = None,
        document_review_inspector: DocumentReviewInspector | None = None,
        document_text_selection_engine: DocumentTextSelectionEngine | None = None,
        document_text_search_engine: DocumentTextSearchEngine | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_open_signed_output: Callable[[str], Any] | None = None,
        on_copy_text: Callable[[str], Any] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
        on_open_signature_library: Callable[[], Any] | None = None,
        untrusted_recovery: bool = False,
    ) -> Any:
        copy_text_callback = on_copy_text or self._load_copy_text_callback()
        return SigningWorkspaceWidget(
            bindings=self._bindings,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            certificate_catalog=certificate_catalog,
            certificate_catalog_store=certificate_catalog_store,
            certificate_material_port=certificate_material_port,
            reusable_objects=reusable_objects,
            app_settings=app_settings,
            app_settings_store=app_settings_store,
            document_review_inspector=document_review_inspector,
            document_text_selection_engine=document_text_selection_engine,
            document_text_search_engine=document_text_search_engine,
            sign_executor=sign_executor,
            on_sign_request=on_sign_request,
            on_open_signed_output=on_open_signed_output,
            on_copy_text=copy_text_callback,
            on_error=on_error,
            on_status_change=on_status_change,
            on_open_signature_library=on_open_signature_library,
            untrusted_recovery=untrusted_recovery,
        )

    def create_from_bootstrap(self, bootstrap: Any) -> SigningWorkspaceWidget:
        """Create from the stable application bootstrap without exposing Qt wiring."""
        return self.create(
            viewer_workflow=bootstrap.viewer_workflow,
            signing_workflow=bootstrap.signing_workflow,
            certificate_catalog_store=bootstrap.certificate_catalog_store,
            certificate_material_port=bootstrap.certificate_material_port,
            reusable_objects=bootstrap.reusable_objects,
            app_settings=bootstrap.app_settings,
            app_settings_store=bootstrap.app_settings_store,
            sign_executor=bootstrap.sign_executor,
            on_sign_request=bootstrap.on_sign_request,
            on_open_signed_output=bootstrap.on_open_signed_output,
            on_error=bootstrap.on_error,
            on_status_change=bootstrap.on_status_change,
            on_open_signature_library=bootstrap.on_open_signature_library,
            untrusted_recovery=bootstrap.untrusted_recovery,
        )

    def _load_bindings(self) -> QtSigningWidgetBindings:
        try:
            qt_widgets = importlib.import_module("PySide6.QtWidgets")
            qt_core = importlib.import_module("PySide6.QtCore")
            qt_gui = importlib.import_module("PySide6.QtGui")
        except Exception as exc:  # pragma: no cover - environment dependent
            raise QtSigningBindingsUnavailable(
                "PySide6 QtWidgets are required for the Qt signing shell. "
                f"Details: {exc}"
            ) from exc

        return QtSigningWidgetBindings(
            q_widget=getattr(qt_widgets, "QWidget"),
            q_vbox_layout=getattr(qt_widgets, "QVBoxLayout"),
            q_hbox_layout=getattr(qt_widgets, "QHBoxLayout"),
            q_form_layout=getattr(qt_widgets, "QFormLayout"),
            q_scroll_area=getattr(qt_widgets, "QScrollArea"),
            q_group_box=getattr(qt_widgets, "QGroupBox"),
            q_label=getattr(qt_widgets, "QLabel"),
            q_line_edit=getattr(qt_widgets, "QLineEdit"),
            q_check_box=getattr(qt_widgets, "QCheckBox"),
            q_combo_box=getattr(qt_widgets, "QComboBox"),
            q_file_dialog=getattr(qt_widgets, "QFileDialog"),
            q_input_dialog=getattr(qt_widgets, "QInputDialog"),
            q_message_box=getattr(qt_widgets, "QMessageBox"),
            q_dialog=getattr(qt_widgets, "QDialog"),
            q_icon=getattr(qt_gui, "QIcon"),
            q_pixmap=getattr(qt_gui, "QPixmap"),
            q_double_spin_box=getattr(qt_widgets, "QDoubleSpinBox"),
            q_spin_box=getattr(qt_widgets, "QSpinBox"),
            q_push_button=getattr(qt_widgets, "QPushButton"),
            qt=getattr(qt_core, "Qt"),
            q_shortcut=getattr(qt_gui, "QShortcut", None),
            q_key_sequence=getattr(qt_gui, "QKeySequence", None),
        )

    def _load_copy_text_callback(self) -> Callable[[str], Any] | None:
        try:
            qt_gui = importlib.import_module("PySide6.QtGui")
        except Exception:
            return None
        application_cls = getattr(qt_gui, "QGuiApplication", None)
        clipboard_getter = getattr(application_cls, "clipboard", None)
        if not callable(clipboard_getter):
            return None

        def _copy_text(value: str) -> None:
            clipboard = clipboard_getter()
            set_text = getattr(clipboard, "setText", None)
            if callable(set_text):
                set_text(value)

        return _copy_text


def build_qt_signing_shell(
    *,
    viewer_workflow: ViewerWorkflow,
    signing_workflow: SigningDraftWorkflow,
    reusable_objects: ReusableSigningObjects,
    certificate_catalog: CertificateCatalog | None = None,
    certificate_catalog_store: CertificateCatalogRepository | None = None,
    certificate_material_port: CertificateSigningMaterialPort | None = None,
    app_settings: AppSettings | None = None,
    app_settings_store: AppSettingsStore | None = None,
    document_review_inspector: DocumentReviewInspector | None = None,
    document_text_selection_engine: DocumentTextSelectionEngine | None = None,
    document_text_search_engine: DocumentTextSearchEngine | None = None,
    sign_executor: SigningRequestExecutor | None = None,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_open_signed_output: Callable[[str], Any] | None = None,
    on_copy_text: Callable[[str], Any] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
    on_open_signature_library: Callable[[], Any] | None = None,
) -> SigningWorkspaceWidget:
    """Build the declared signing-shell facade around its Qt container."""

    adapter = SigningShellAdapter()
    return adapter.create(
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        reusable_objects=reusable_objects,
        certificate_catalog=certificate_catalog,
        certificate_catalog_store=certificate_catalog_store,
        certificate_material_port=certificate_material_port,
        app_settings=app_settings,
        app_settings_store=app_settings_store,
        document_review_inspector=document_review_inspector,
        document_text_selection_engine=document_text_selection_engine,
        document_text_search_engine=document_text_search_engine,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        on_open_signed_output=on_open_signed_output,
        on_copy_text=on_copy_text,
        on_error=on_error,
        on_status_change=on_status_change,
        on_open_signature_library=on_open_signature_library,
    )
