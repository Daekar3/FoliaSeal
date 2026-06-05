"""Qt signing shell for the FoliaSeal signing workspace."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from foliaseal.application import (
    SignaturePlacementContext,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
    WorkspaceInteractionPlan,
    WorkspaceInteractionSession,
)
from foliaseal.application import (
    SigningDraftPreview as _SigningDraftPreview,
)
from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewInspector,
    DocumentReviewSummary,
    PyHankoDocumentReviewInspector,
)
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
)
from foliaseal.application.document_text_search import (
    DocumentTextSearchEngine,
    DocumentTextSearchSession,
    DocumentTextSearchState,
)
from foliaseal.application.document_text_selection import (
    DocumentTextSelectionEngine,
    DocumentTextSelectionSession,
    DocumentTextSelectionState,
)
from foliaseal.application.signature_properties_coordinator import (
    SignaturePropertiesCoordinatorError as _SignaturePropertiesCoordinatorError,
)
from foliaseal.application.signing_material_resolver import CertificateSecretProvider
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
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
from foliaseal.infra.document_text_search import QtPdfDocumentTextSearchEngine
from foliaseal.infra.document_text_selection import QtPdfDocumentTextSelectionEngine
from foliaseal.presentation.qt.signing_action_boundary import (
    SigningActionBoundary,
)
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionCoordinator,
)
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)
from foliaseal.presentation.qt.signing_workspace_interaction_bridge import (
    SigningWorkspaceInteractionBridge,
)
from foliaseal.presentation.qt.signing_workspace_properties_panel import (
    SignaturePropertiesPanel,
)
from foliaseal.presentation.qt.signing_workspace_review_bridge import (
    SigningWorkspaceReviewBridge,
)
from foliaseal.presentation.qt.signing_workspace_sidebar import (
    SigningWorkspaceSidebar,
)
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

SIGNATURE_PRESET_PLACEHOLDER = "Current signature setup"
CERTIFICATE_CONFIGURATION_PLACEHOLDER = "Current certificate"
SigningDraftPreview = _SigningDraftPreview
SignatureFieldKey = _SignatureFieldKey
SignatureFieldSource = _SignatureFieldSource
SignatureLayoutTemplate = _SignatureLayoutTemplate
SignaturePropertiesCoordinatorError = _SignaturePropertiesCoordinatorError
SignatureTextStyle = _SignatureTextStyle
SignatureTimezoneDisplayMode = _SignatureTimezoneDisplayMode


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


@dataclass(frozen=True)
class SignaturePresetControls:
    """Controls used to manage reusable signature presets."""

    container: Any
    preset_combo: Any
    preset_name: Any
    save_button: Any
    delete_button: Any


@dataclass(frozen=True)
class CertificateConfigurationControls:
    """Controls used to choose a saved certificate configuration."""

    container: Any
    configuration_combo: Any
    apply_button: Any


class SigningRequestExecutor(Protocol):
    """Executes a validated signing request and returns a signing result."""

    def execute(self, request: SigningRequest) -> SigningResult:
        """Apply the signing request and return the result."""

@dataclass(frozen=True)
class PreviewControls:
    """Widgets used to present the visible-signature preview."""

    container: Any
    summary_label: Any
    card_container: Any
    title_label: Any
    stamp_label: Any
    detail_label: Any
    single_render_label: Any
    single_body_container: Any
    multi_body_container: Any
    multi_content_container: Any
    multi_stamp_label: Any
    multi_detail_label: Any
    multi_render_label: Any
    footer_label: Any


class _QtCertificatePassphrasePrompter:
    """Qt adapter for manual certificate-passphrase entry."""

    def __init__(self, *, bindings: QtSigningWidgetBindings, parent: Any) -> None:
        self._bindings = bindings
        self._parent = parent

    def prompt(self, label: str) -> str | None:
        input_dialog = getattr(self._bindings, "q_input_dialog", None)
        get_text = getattr(input_dialog, "getText", None)
        if not callable(get_text):
            return None
        password_mode = getattr(self._bindings.q_line_edit, "Password", None)
        if password_mode is None:
            echo_mode = getattr(self._bindings.q_line_edit, "EchoMode", None)
            password_mode = getattr(echo_mode, "Password", None)
        if password_mode is None:
            text, accepted = get_text(
                self._parent,
                "Certificate password",
                label,
            )
        else:
            text, accepted = get_text(
                self._parent,
                "Certificate password",
                label,
                password_mode,
            )
        if not accepted:
            return None
        return str(text)


def _compose_row(bindings: QtSigningWidgetBindings, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def _compose_preview_column(bindings: QtSigningWidgetBindings, *widgets: Any) -> Any:
    container = bindings.q_widget()
    if hasattr(container, "setStyleSheet"):
        container.setStyleSheet("background: transparent; border: none;")
    layout = bindings.q_vbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def _set_preview_surface_chrome(widget: Any) -> None:
    if hasattr(widget, "setStyleSheet"):
        widget.setStyleSheet("background: transparent; border: none; padding: 0px;")


def _container_layout(container: Any) -> Any | None:
    layout_attr = getattr(container, "layout", None)
    if callable(layout_attr):
        return layout_attr()
    return layout_attr


def _layout_spacing(layout: Any) -> int:
    spacing_getter = getattr(layout, "spacing", None)
    if callable(spacing_getter):
        try:
            value = spacing_getter()
        except TypeError:
            value = None
        if isinstance(value, int):
            return value
    if isinstance(spacing_getter, int):
        return spacing_getter
    value = getattr(layout, "spacing_value", None)
    if isinstance(value, int):
        return value
    return 0


def _clear_layout(layout: Any) -> None:
    take_at = getattr(layout, "takeAt", None)
    count = getattr(layout, "count", None)
    if callable(take_at) and callable(count):
        while count():
            item = take_at(0)
            if item is None:
                break
        return

    items = getattr(layout, "items", None)
    if isinstance(items, list):
        items.clear()


def _set_container_widgets(container: Any, *widgets: Any) -> None:
    layout = _container_layout(container)
    if layout is None:
        return
    _clear_layout(layout)
    for widget in widgets:
        if isinstance(widget, tuple):
            item, *args = widget
            layout.addWidget(item, *args)
            continue
        layout.addWidget(widget)


def _set_combo_text(combo: Any, value: str, *, allow_custom: bool = False) -> None:
    index = getattr(combo, "findText", None)
    if callable(index):
        found = index(value)
        if found >= 0:
            setter = getattr(combo, "setCurrentIndex", None)
            if callable(setter):
                setter(found)
            return
    setter = getattr(combo, "setCurrentText", None)
    if callable(setter) and not allow_custom:
        setter(value)
        return
    if allow_custom:
        if value not in _combo_items(combo):
            adder = getattr(combo, "addItem", None)
            if callable(adder):
                adder(value)
            elif hasattr(combo, "addItems"):
                combo.addItems((value,))
        if callable(setter):
            setter(value)
        return
    if callable(setter):
        setter(value)


def _combo_text(combo: Any) -> str:
    getter = getattr(combo, "currentText", None)
    if callable(getter):
        return str(getter())
    return ""


def _combo_items(combo: Any) -> tuple[str, ...]:
    count_getter = getattr(combo, "count", None)
    item_text_getter = getattr(combo, "itemText", None)
    if callable(count_getter) and callable(item_text_getter):
        return tuple(str(item_text_getter(index)) for index in range(int(count_getter())))
    items = getattr(combo, "_items", None)
    if items is not None:
        return tuple(str(item) for item in items)
    return ()


def _set_checked(check_box: Any, value: bool) -> None:
    setter = getattr(check_box, "setChecked", None)
    if callable(setter):
        setter(value)


def _is_checked(check_box: Any) -> bool:
    getter = getattr(check_box, "isChecked", None)
    if callable(getter):
        return bool(getter())
    return False


def _set_spin_value(spin_box: Any, value: float | int) -> None:
    setter = getattr(spin_box, "setValue", None)
    if callable(setter):
        setter(value)


def _spin_value(spin_box: Any) -> float:
    getter = getattr(spin_box, "value", None)
    if callable(getter):
        return float(getter())
    return 0.0


def _set_text(line_edit: Any, value: str) -> None:
    setter = getattr(line_edit, "setText", None)
    if callable(setter):
        setter(value)


def _text(line_edit: Any) -> str:
    getter = getattr(line_edit, "text", None)
    if callable(getter):
        return str(getter())
    return ""


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


def _build_preview_issue(
    *,
    code: str,
    message: str,
    field_name: str | None = None,
    ) -> SigningDraftValidationIssue:
    return SigningDraftValidationIssue(
        code=code,
        message=message,
        field_name=field_name,
        severity=SigningDraftValidationSeverity.ERROR,
    )


def _set_widget_visible(widget: Any, visible: bool) -> None:
    setter = getattr(widget, "setVisible", None)
    if callable(setter):
        setter(visible)


def _widget_width(widget: Any) -> int | None:
    width_getter = getattr(widget, "width", None)
    if callable(width_getter):
        try:
            value = width_getter()
        except TypeError:
            value = None
        if isinstance(value, int) and value > 0:
            return value
    for attr in ("fixed_width", "maximum_width", "minimum_width"):
        value = getattr(widget, attr, None)
        if isinstance(value, int) and value > 0:
            return value
    return None


def _widget_parent(widget: Any) -> Any | None:
    parent_getter = getattr(widget, "parentWidget", None)
    if callable(parent_getter):
        try:
            parent = parent_getter()
        except TypeError:
            parent = None
        if parent is not None:
            return parent
    return getattr(widget, "parent", None)


def _ancestor_width(widget: Any) -> int | None:
    current = _widget_parent(widget)
    widths: list[int] = []
    while current is not None:
        width = _widget_width(current)
        if isinstance(width, int) and width > 0:
            widths.append(width)
        current = _widget_parent(current)
    if not widths:
        return None
    return min(widths)


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
        self._sign_executor = sign_executor
        self._on_sign_request = on_sign_request
        self._on_open_signed_output = on_open_signed_output
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._app_settings_store = app_settings_store
        self._viewer_interaction_session = ViewerInteractionSession(
            viewer_workflow=viewer_workflow
        )
        self._document_review_inspector = (
            document_review_inspector or PyHankoDocumentReviewInspector()
        )
        document_text_selection_session = DocumentTextSelectionSession(
            input_pdf_path=viewer_workflow.document_path,
            selection_engine=document_text_selection_engine
            or QtPdfDocumentTextSelectionEngine(),
        )
        document_text_search_session = DocumentTextSearchSession(
            input_pdf_path=viewer_workflow.document_path,
            search_engine=document_text_search_engine or QtPdfDocumentTextSearchEngine(),
        )
        self._on_copy_text = on_copy_text
        self._document_review_workspace = DocumentReviewWorkspaceSession(
            document_review_inspector=self._document_review_inspector,
            document_text_search_session=document_text_search_session,
            document_text_selection_session=document_text_selection_session,
            input_pdf_path=viewer_workflow.document_path,
        )
        self._workspace_interaction_session = WorkspaceInteractionSession(
            viewer_workflow=viewer_workflow,
            viewer_interaction_session=self._viewer_interaction_session,
            document_review_workspace=self._document_review_workspace,
        )
        if app_settings is not None:
            self._app_settings = app_settings
        elif app_settings_store is not None:
            self._app_settings = app_settings_store.load_settings()
        else:
            self._app_settings = AppSettings.default()
        self.widget = _build_close_aware_widget(
            bindings.q_widget,
            on_close=lambda: self.properties_panel.dispose(),
        )
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)

        self._viewer_widget = build_qt_pdf_viewer_widget(
            workflow=viewer_workflow,
            on_selection=self._handle_viewer_selection,
            on_error=self._handle_viewer_error,
            on_interaction=self._handle_viewer_interaction,
        )
        self.properties_panel = SignaturePropertiesPanel(
            bindings=bindings,
            workflow=signing_workflow,
            certificate_catalog=certificate_catalog,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog=preset_catalog,
            preset_catalog_store=preset_catalog_store,
            app_settings=self._app_settings,
            on_change=self._handle_panel_change,
            on_page_change=self._handle_page_change,
            on_error=self._emit_error,
        )
        self._sidebar = SigningWorkspaceSidebar(
            bindings=bindings,
            properties_widget=self.properties_panel.container,
            on_choose_output=self.choose_output_pdf_path,
            on_sign=self.submit_sign_request,
            on_open_signed_output=self.open_signed_output,
            on_find_text=self.search_document_text,
            on_previous_text_match=self.previous_document_text_match,
            on_next_text_match=self.next_document_text_match,
            on_copy_text_match=self.copy_current_document_text_match,
            on_review_signature_selected=self._on_document_review_signature_selected,
            on_text_selection_mode_changed=self.set_document_text_selection_mode,
            on_copy_selected_text=self.copy_selected_document_text,
            on_clear_selected_text=self.clear_selected_document_text,
        )
        self._document_text_controls = self._sidebar.document_text_controls
        self._properties_scroll = self._sidebar.properties_scroll
        self._sign_button = self._sidebar.sign_button
        self._result_label = self._sidebar.result_label
        self._review_bridge = SigningWorkspaceReviewBridge(
            sidebar=self._sidebar,
            viewer_widget=self._viewer_widget,
            document_review_workspace=self._document_review_workspace,
            on_jump_to_page_index=lambda page_index: self._apply_workspace_interaction_plan(
                self._workspace_interaction_session.refresh_navigation_to_page_index(
                    page_index
                )
            ),
            can_copy_text=self._on_copy_text is not None,
        )
        self._signing_action_coordinator = SigningActionCoordinator(
            workflow=self._draft_workflow,
            apply_changes=self.properties_panel.apply_changes,
            is_ready_to_sign=self.properties_panel.is_ready_to_sign,
            validation_text=self.properties_panel.validation_text,
            sign_executor=self._sign_executor,
            on_sign_request=self._on_sign_request,
            can_open_signed_output=self._on_open_signed_output is not None,
        )
        self._signing_action_boundary = SigningActionBoundary(
            coordinator=self._signing_action_coordinator,
            emit_error=self._emit_error,
            on_error=self._on_error,
            on_status_change=self._on_status_change,
            on_open_signed_output=self._on_open_signed_output,
        )
        self._action_bridge = SigningWorkspaceActionBridge(
            widget=self.widget,
            bindings=bindings,
            sidebar=self._sidebar,
            properties_panel=self.properties_panel,
            signing_action_boundary=self._signing_action_boundary,
            draft_workflow=self._draft_workflow,
            app_settings_getter=lambda: self._app_settings,
        )
        self._interaction_bridge = SigningWorkspaceInteractionBridge(
            review_bridge=self._review_bridge,
            viewer_widget=self._viewer_widget,
            viewer_interaction_session=self._viewer_interaction_session,
            apply_placement_context=self._apply_placement_context_result,
            apply_signature_rect=lambda signature_rect, notify: (
                self.properties_panel.set_signature_rect(
                    signature_rect,
                    notify=notify,
                )
            ),
            sync_signature_overlay=self._sync_signature_overlay,
            refresh_preview=lambda: self.properties_panel.refresh_preview(),
            load_signing_action_state=self._action_bridge.reload_state,
            invalidate_signing_action_state=self._action_bridge.invalidate_state,
            emit_error=self._emit_error,
        )
        self._main_row = bindings.q_hbox_layout()
        self._main_row.setContentsMargins(0, 0, 0, 0)
        self._main_row.setSpacing(8)
        self._main_row.addWidget(self._viewer_widget, 3)
        self._main_row.addWidget(self._sidebar.container, 2)
        self._layout.addLayout(self._main_row)

        self.widget.properties_panel = self.properties_panel  # type: ignore[attr-defined]
        self.widget.viewer_widget = self._viewer_widget  # type: ignore[attr-defined]
        self.widget.properties_scroll = self._properties_scroll  # type: ignore[attr-defined]
        self.widget.sidebar = self._sidebar.container  # type: ignore[attr-defined]
        self.widget.sidebar_surface = self._sidebar.surface  # type: ignore[attr-defined]
        destroyed_signal = getattr(self.widget, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: self.properties_panel.dispose())
        self.widget.app_settings = self._app_settings  # type: ignore[attr-defined]
        self.widget.last_signing_result = None  # type: ignore[attr-defined]
        self.widget.refresh_viewer = self.refresh_viewer  # type: ignore[attr-defined]
        self.widget.refresh_document_review = self.refresh_document_review  # type: ignore[attr-defined]
        self.widget.search_document_text = self.search_document_text  # type: ignore[attr-defined]
        self.widget.next_document_text_match = self.next_document_text_match  # type: ignore[attr-defined]
        self.widget.previous_document_text_match = self.previous_document_text_match  # type: ignore[attr-defined]
        self.widget.copy_current_document_text_match = (  # type: ignore[attr-defined]
            self.copy_current_document_text_match
        )
        self.widget.set_document_text_selection_mode = (  # type: ignore[attr-defined]
            self.set_document_text_selection_mode
        )
        self.widget.copy_selected_document_text = self.copy_selected_document_text  # type: ignore[attr-defined]
        self.widget.clear_selected_document_text = self.clear_selected_document_text  # type: ignore[attr-defined]
        self.widget.apply_app_settings = self.apply_app_settings  # type: ignore[attr-defined]
        self.widget.set_logical_page_index = self.set_logical_page_index  # type: ignore[attr-defined]
        self.widget.logical_page_index = self.logical_page_index  # type: ignore[attr-defined]
        self.widget.set_signature_rect = self.set_signature_rect  # type: ignore[attr-defined]
        self.widget.signature_rect = self.signature_rect  # type: ignore[attr-defined]
        self.widget.set_selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self.set_selected_certificate_configuration_id
        )
        self.widget.selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self.selected_certificate_configuration_id
        )
        self.widget.signature_appearance = self.signature_appearance  # type: ignore[attr-defined]
        self.widget.is_sign_action_enabled = self.is_sign_action_enabled  # type: ignore[attr-defined]
        self.widget.choose_output_pdf_path = self.choose_output_pdf_path  # type: ignore[attr-defined]
        self.widget.refresh_certificate_configurations = (  # type: ignore[attr-defined]
            self.refresh_certificate_configurations
        )
        self.widget.submit_sign_request = self.submit_sign_request  # type: ignore[attr-defined]
        self.widget.open_signed_output = self.open_signed_output  # type: ignore[attr-defined]

        self.refresh_viewer()
        self._review_bridge.apply_state(self._document_review_workspace.load())
        self._action_bridge.reload_state()

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
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.refresh_after_viewer_refresh(),
        )

    def refresh_document_review(self) -> DocumentReviewSummary:
        state = self._document_review_workspace.refresh_review()
        self._review_bridge.apply_state(state)
        return state.review.review_summary

    def search_document_text(self) -> DocumentTextSearchState:
        query = _text(self._document_text_controls.query_input)
        transition = self._document_review_workspace.search_text(query)
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.search_state

    def next_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.next_text_match()
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.search_state

    def previous_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.previous_text_match()
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.search_state

    def copy_current_document_text_match(self) -> str | None:
        copy_text = self._document_review_workspace.copy_current_text_match()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        transition = self._document_review_workspace.set_text_selection_mode(enabled)
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.selection_mode_enabled

    def copy_selected_document_text(self) -> str | None:
        copy_text = self._document_review_workspace.copy_selected_text()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def clear_selected_document_text(self) -> DocumentTextSelectionState:
        transition = self._document_review_workspace.clear_selected_text()
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.selection_state

    def apply_app_settings(self, settings: AppSettings) -> None:
        """Apply new app-level settings to the live shell state."""
        self._app_settings = settings
        self.widget.app_settings = settings  # type: ignore[attr-defined]

    def set_logical_page_index(self, page_index: int) -> None:
        """Update the logical session page without forcing a viewer rerender."""
        self._viewer_interaction_session.set_logical_page_index(page_index)

    def logical_page_index(self) -> int:
        """Return the current logical viewer page index."""
        return self._viewer_workflow.session.current_page

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
        ) -> SignatureRect:
        """Apply a signature rectangle through the shell surface."""
        signature_rect = SignatureRect(
            page_index=page_index,
            left_pt=left_pt,
            bottom_pt=bottom_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        )
        self.properties_panel.set_signature_rect(signature_rect, notify=False)
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.refresh_after_panel_change()
        )
        return signature_rect

    def signature_rect(self) -> SignatureRect | None:
        """Return the current signature rectangle, if any."""
        return self._draft_workflow.signature_rect

    def set_selected_certificate_configuration_id(self, configuration_id: str | None) -> None:
        """Apply a selected certificate configuration identifier to the live draft."""
        self._draft_workflow.selected_certificate_configuration_id = configuration_id
        self.properties_panel.load_from_workflow()

    def selected_certificate_configuration_id(self) -> str | None:
        """Return the selected certificate configuration identifier, if any."""
        return self._draft_workflow.selected_certificate_configuration_id

    def signature_appearance(self) -> SignatureAppearance | None:
        """Return the current signature appearance."""
        return self._draft_workflow.signature_appearance

    def is_sign_action_enabled(self) -> bool:
        """Return whether the sign action is currently enabled."""
        is_enabled = getattr(self._sign_button, "isEnabled", None)
        if callable(is_enabled):
            return bool(is_enabled())
        if hasattr(self._sign_button, "_enabled"):
            return bool(self._sign_button._enabled)  # type: ignore[attr-defined]
        return bool(getattr(self._sign_button, "enabled", False))

    def submit_sign_request(self) -> SigningRequest | None:
        return self._action_bridge.submit_sign_request()

    def open_signed_output(self) -> str | None:
        return self._action_bridge.open_signed_output()

    def choose_output_pdf_path(self) -> str | None:
        return self._action_bridge.choose_output_pdf_path()

    @property
    def last_signing_result(self) -> SigningResult | None:
        """Return the most recent signing result, if a real executor ran."""
        return self._signing_action_coordinator.last_signing_result

    def _handle_viewer_selection(self, pdf_rect: PdfRect) -> None:
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.select_in_viewer(pdf_rect),
        )

    def _handle_viewer_error(self, message: str) -> None:
        self._emit_error(message)

    def _handle_viewer_interaction(self, name: str) -> None:
        if self._on_status_change is not None:
            self._on_status_change(name)

    def _handle_panel_change(self) -> None:
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.refresh_after_panel_change()
        )

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        """Reload certificate configurations from storage and refresh shell controls."""
        return self._action_bridge.refresh_certificate_configurations()

    def _handle_page_change(self, page_number: int) -> None:
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.change_page(page_number),
        )

    def _sync_signature_overlay(self) -> None:
        setter = getattr(self._viewer_widget, "set_signature_overlay", None)
        if callable(setter):
            setter(self._draft_workflow.signature_rect)

    def _on_document_review_signature_selected(self, index: int) -> None:
        self._review_bridge.select_review_signature(index)

    def _apply_placement_context_result(
        self,
        placement_context: SignaturePlacementContext | None,
    ) -> None:
        if placement_context is None:
            return
        self._draft_workflow.set_placement_context(placement_context)

    def _apply_workspace_interaction_plan(
        self,
        plan: WorkspaceInteractionPlan,
    ) -> None:
        self._interaction_bridge.apply_plan(plan)

    def _emit_error(self, message: str) -> None:
        self._set_sign_result_text(message, success=False)
        if self._on_error is not None:
            self._on_error(message)
            return
        raise RuntimeError(message)

    def _set_sign_result_text(self, message: str, *, success: bool | None = None) -> None:
        self._result_label.setText(message)
        if not hasattr(self._result_label, "setStyleSheet"):
            return
        if success is True:
            self._result_label.setStyleSheet("color: #1f6f2a; font-weight: 600;")
        elif success is False:
            self._result_label.setStyleSheet("color: #9f1d1d; font-weight: 600;")
        else:
            self._result_label.setStyleSheet("color: #444;")


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
