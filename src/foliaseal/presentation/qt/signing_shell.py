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
from foliaseal.application.signature_properties_coordinator import (
    SignaturePropertiesCoordinatorError as _SignaturePropertiesCoordinatorError,
)
from foliaseal.application.signing_material_resolver import CertificateSecretProvider
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
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import (
    AppSettings,
    CertificateCatalog,
    SignaturePresetCatalog,
)
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
    SigningWorkspaceComposition,
    build_signing_workspace_composition,
)
from foliaseal.presentation.qt.signing_workspace_runtime import (
    SigningWorkspaceRuntime,
)
from foliaseal.presentation.qt.signing_workspace_sidebar import (
    SigningWorkspaceSidebar as _SigningWorkspaceSidebar,
)
from foliaseal.presentation.qt.viewer_widget import (
    build_qt_pdf_viewer_widget as _build_qt_pdf_viewer_widget,
)

SIGNATURE_PRESET_PLACEHOLDER = "Current signature setup"
CERTIFICATE_CONFIGURATION_PLACEHOLDER = "Current certificate"
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
    q_pixmap: type[Any]
    q_double_spin_box: type[Any]
    q_spin_box: type[Any]
    q_push_button: type[Any]
    qt: Any

class SigningRequestExecutor(Protocol):
    """Executes a validated signing request and returns a signing result."""

    def execute(self, request: SigningRequest) -> SigningResult:
        """Apply the signing request and return the result."""


def _format_appearance_summary(appearance: SignatureAppearance) -> str:
    labels = {
        SignatureFieldKey.DISTINGUISHED_NAME: "Distinguished name",
        SignatureFieldKey.COMMON_NAME: "Common name",
        SignatureFieldKey.EMAIL: "Email",
        SignatureFieldKey.SIGNING_TIME: "Signing time",
        SignatureFieldKey.REASON: "Reason",
        SignatureFieldKey.LOCATION: "Location",
        SignatureFieldKey.TITLE: "Title",
        SignatureFieldKey.COMPANY: "Company",
    }
    visible_fields = [
        labels[field_key]
        for field_key, binding in appearance.iter_field_bindings()
        if binding.show_in_visible_appearance
    ]
    visible_fields_text = ", ".join(visible_fields) if visible_fields else "None"
    text_style = appearance.text_style
    box_style = appearance.box_style
    border_text = "on" if box_style.show_border else "off"
    stamp_text = appearance.image_stamp_path or "None"
    return "\n".join(
        [
            "Current appearance draft",
            f"Layout: {appearance.layout_template.value}",
            f"Stamp position: {appearance.stamp_position.value}",
            f"Timezone: {appearance.timezone_display_mode.value}",
            f"Datetime format: {appearance.datetime_format}",
            f"Visible fields: {visible_fields_text}",
            (
                "Text style: "
                f"{text_style.font_family}, {text_style.font_size_pt:g}pt, "
                f"{'bold' if text_style.bold else 'regular'}, "
                f"{'italic' if text_style.italic else 'upright'}, "
                f"{text_style.text_color_hex}"
            ),
            (
                "Box style: "
                f"border {border_text}, {box_style.border_color_hex}, "
                f"{box_style.border_width_pt:g}pt, {box_style.background_color_hex}"
            ),
            f"Image stamp: {stamp_text}",
        ]
    )


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
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: CertificateSecretProvider | None = None,
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
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
    ) -> None:
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
        self._runtime = SigningWorkspaceRuntime(
            draft_workflow=signing_workflow,
            on_error=on_error,
            on_status_change=on_status_change,
        )
        self.widget = _build_close_aware_widget(
            bindings.q_widget,
            on_close=lambda: self.properties_panel.dispose(),
        )
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)
        composition = build_signing_workspace_composition(
            bindings=bindings,
            widget=self.widget,
            layout=self._layout,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            certificate_catalog=certificate_catalog,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog=preset_catalog,
            preset_catalog_store=preset_catalog_store,
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
            viewer_widget_builder=build_qt_pdf_viewer_widget,
            runtime=self._runtime,
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
        )
        self._install_composition(composition)
        composition.bootstrap()

    def _install_composition(self, composition: SigningWorkspaceComposition) -> None:
        self._document_review_inspector = composition.document_review_inspector
        self._viewer_interaction_session = composition.viewer_interaction_session
        self._document_review_workspace = composition.document_review_workspace
        self._workspace_interaction_session = composition.workspace_interaction_session
        self._viewer_widget = composition.viewer_widget
        self.properties_panel = composition.properties_panel
        self._sidebar = composition.sidebar
        self._document_text_controls = composition.document_text_controls
        self._properties_scroll = composition.properties_scroll
        self._sign_button = composition.sign_button
        self._result_label = composition.result_label
        self._review_bridge = composition.review_bridge
        self._signing_action_coordinator = composition.signing_action_coordinator
        self._signing_action_boundary = composition.signing_action_boundary
        self._action_bridge = composition.action_bridge
        self._interaction_bridge = composition.interaction_bridge
        self._runtime = composition.runtime
        self._compatibility_surface = composition.compatibility_surface
        self._shell_surface = composition.shell_surface
        self._main_row = composition.main_row

    @property
    def container(self) -> Any:
        return self.widget

    @property
    def viewer_widget(self) -> Any:
        return self._viewer_widget

    @property
    def app_settings(self) -> AppSettings:
        return self._app_settings

    def refresh_viewer(self) -> None:
        self._compatibility_surface.refresh_viewer()

    def refresh_document_review(self) -> DocumentReviewSummary:
        return self._compatibility_surface.refresh_document_review()

    def search_document_text(self) -> DocumentTextSearchState:
        return self._compatibility_surface.search_document_text()

    def next_document_text_match(self) -> DocumentTextSearchState:
        return self._compatibility_surface.next_document_text_match()

    def previous_document_text_match(self) -> DocumentTextSearchState:
        return self._compatibility_surface.previous_document_text_match()

    def copy_current_document_text_match(self) -> str | None:
        return self._compatibility_surface.copy_current_document_text_match()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self._compatibility_surface.set_document_text_selection_mode(enabled)

    def copy_selected_document_text(self) -> str | None:
        return self._compatibility_surface.copy_selected_document_text()

    def clear_selected_document_text(self) -> DocumentTextSelectionState:
        return self._compatibility_surface.clear_selected_document_text()

    def apply_app_settings(self, settings: AppSettings) -> None:
        self._shell_surface.apply_app_settings(settings)

    def set_logical_page_index(self, page_index: int) -> None:
        self._compatibility_surface.set_logical_page_index(page_index)

    def logical_page_index(self) -> int:
        return self._compatibility_surface.logical_page_index()

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
        ) -> SignatureRect:
        return self._compatibility_surface.set_signature_rect(
            page_index=page_index,
            left_pt=left_pt,
            bottom_pt=bottom_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        )

    def signature_rect(self) -> SignatureRect | None:
        return self._compatibility_surface.signature_rect()

    def set_selected_certificate_configuration_id(self, configuration_id: str | None) -> None:
        self._compatibility_surface.set_selected_certificate_configuration_id(configuration_id)

    def selected_certificate_configuration_id(self) -> str | None:
        return self._compatibility_surface.selected_certificate_configuration_id()

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._compatibility_surface.signature_appearance()

    def set_timestamp_required(self, required: bool) -> None:
        self._compatibility_surface.set_timestamp_required(required)

    def current_request(self) -> SigningRequest | None:
        return self._compatibility_surface.current_request()

    def is_sign_action_enabled(self) -> bool:
        return self._compatibility_surface.is_sign_action_enabled()

    def submit_sign_request(self) -> SigningRequest | None:
        return self._shell_surface.submit_sign_request()

    def open_signed_output(self) -> str | None:
        return self._shell_surface.open_signed_output()

    def choose_output_pdf_path(self) -> str | None:
        return self._shell_surface.choose_output_pdf_path()

    @property
    def last_signing_result(self) -> SigningResult | None:
        """Return the most recent signing result, if a real executor ran."""
        return self._signing_action_coordinator.last_signing_result

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self._shell_surface.refresh_certificate_configurations()


class SigningShellAdapter:
    """Factory for the FoliaSeal Qt signing shell."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create(
        self,
        *,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        certificate_catalog: CertificateCatalog | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: CertificateSecretProvider | None = None,
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
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
    ) -> Any:
        copy_text_callback = on_copy_text or self._load_copy_text_callback()
        return SigningWorkspaceWidget(
            bindings=self._bindings,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            certificate_catalog=certificate_catalog,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog=preset_catalog,
            preset_catalog_store=preset_catalog_store,
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
        ).container

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
            q_pixmap=getattr(qt_gui, "QPixmap"),
            q_double_spin_box=getattr(qt_widgets, "QDoubleSpinBox"),
            q_spin_box=getattr(qt_widgets, "QSpinBox"),
            q_push_button=getattr(qt_widgets, "QPushButton"),
            qt=getattr(qt_core, "Qt"),
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
    certificate_catalog: CertificateCatalog | None = None,
    certificate_catalog_store: CertificateCatalogStore | None = None,
    certificate_secret_provider: CertificateSecretProvider | None = None,
    preset_catalog: SignaturePresetCatalog | None = None,
    preset_catalog_store: SignaturePresetCatalogStore | None = None,
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
) -> Any:
    """Build a QWidget instance for the FoliaSeal signing shell."""

    adapter = SigningShellAdapter()
    return adapter.create(
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        certificate_catalog=certificate_catalog,
        certificate_catalog_store=certificate_catalog_store,
        certificate_secret_provider=certificate_secret_provider,
        preset_catalog=preset_catalog,
        preset_catalog_store=preset_catalog_store,
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
    )
