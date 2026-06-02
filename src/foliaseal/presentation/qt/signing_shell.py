"""Qt signing shell for the FoliaSeal signing workspace."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import (
    ApplyPlacementContext,
    ApplyReviewTransition,
    ApplySignatureRect,
    EmitInteractionError,
    InvalidateSigningAction,
    RefreshCurrentPlacementContext,
    RefreshPreview,
    RefreshViewer,
    ReloadSigningActionState,
    SignaturePlacementContext,
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
    SigningSetupSession,
    SyncSignatureOverlay,
    WorkspaceInteractionEffect,
    WorkspaceInteractionPlan,
    WorkspaceInteractionSession,
    suggest_signed_output_path,
)
from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewInspector,
    DocumentReviewSummary,
    PyHankoDocumentReviewInspector,
)
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
    DocumentReviewWorkspaceState,
    DocumentReviewWorkspaceTransition,
    DocumentReviewWorkspaceViewerEffects,
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
    DefaultSignaturePropertiesCoordinator,
    SignaturePropertiesCoordinatorError,
    SignaturePropertiesViewState,
)
from foliaseal.application.signing_material_resolver import CertificateSecretProvider
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldKey,
    SignatureRect,
    SigningRequest,
    SigningResult,
)
from foliaseal.domain.models import (
    SignatureFieldSource as _SignatureFieldSource,
)
from foliaseal.domain.models import (
    SignatureLayoutTemplate as _SignatureLayoutTemplate,
)
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import (
    AppSettings,
    CertificateCatalog,
    ResolvedSignaturePreset,
    SignaturePresetCatalog,
)
from foliaseal.infra.document_text_search import QtPdfDocumentTextSearchEngine
from foliaseal.infra.document_text_selection import QtPdfDocumentTextSelectionEngine
from foliaseal.presentation.qt.signature_preview_layout import (
    QtSignaturePreviewLayout,
    _ensure_preview_fonts_registered,
    _preview_stamp_text,
)
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    QtCanonicalPreviewLifecycle,
)
from foliaseal.presentation.qt.signing_action_boundary import (
    SigningActionBoundary,
)
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionCoordinator,
    SigningActionState,
)
from foliaseal.presentation.qt.signing_workspace_sidebar import (
    SigningWorkspaceSidebar,
    format_document_signature_items,
)
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget
from foliaseal.presentation.qt.visible_signature_setup_form import (
    QtVisibleSignatureSetupForm,
)

SIGNATURE_PRESET_PLACEHOLDER = "Current signature setup"
CERTIFICATE_CONFIGURATION_PLACEHOLDER = "Current certificate"
SignatureFieldSource = _SignatureFieldSource
SignatureLayoutTemplate = _SignatureLayoutTemplate


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


class SignaturePropertiesPanel:
    """Signature editing controls and preview/validation summary."""

    def __init__(
        self,
        *,
        bindings: QtSigningWidgetBindings,
        workflow: SigningDraftWorkflow,
        certificate_catalog: CertificateCatalog | None = None,
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: CertificateSecretProvider | None = None,
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        app_settings: AppSettings | None = None,
        on_change: Callable[[], None] | None = None,
        on_page_change: Callable[[int], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        _ensure_preview_fonts_registered()
        self._workflow = workflow
        self._certificate_catalog_store = certificate_catalog_store
        self._preset_catalog_store = preset_catalog_store
        self._coordinator = DefaultSignaturePropertiesCoordinator(
            workflow=workflow,
            certificate_catalog=certificate_catalog,
            certificate_catalog_store=certificate_catalog_store,
            certificate_secret_provider=certificate_secret_provider,
            preset_catalog=preset_catalog,
            preset_catalog_store=preset_catalog_store,
        )
        self._app_settings = app_settings or AppSettings.default()
        self._on_change = on_change
        self._on_page_change = on_page_change
        self._on_error = on_error
        self._suspend_updates = False
        self._control_issue: SigningDraftValidationIssue | None = None
        self._canonical_preview_lifecycle = QtCanonicalPreviewLifecycle(
            q_pixmap=bindings.q_pixmap,
            qt=bindings.qt,
        )
        self._preview_layout = QtSignaturePreviewLayout(bindings=bindings)
        self.widget = _build_close_aware_widget(
            bindings.q_widget,
            on_close=self.dispose,
        )
        self._setup_session = SigningSetupSession(
            coordinator=self._coordinator,
            passphrase_prompter=_QtCertificatePassphrasePrompter(
                bindings=bindings,
                parent=self.widget,
            ),
        )
        destroyed_signal = getattr(self.widget, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: self.dispose())
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)

        self._certificate_controls = self._build_certificate_configuration_controls()
        self._signature_preset_controls = self._build_signature_preset_controls()
        self._setup_form = QtVisibleSignatureSetupForm(
            bindings=bindings,
            on_change=self._handle_visible_signature_form_change,
            on_page_change=self._handle_visible_signature_page_change,
        )
        self._placement_controls = self._setup_form.placement_controls
        self._appearance_controls = self._setup_form.appearance_controls
        self._visible_text_controls = self._setup_form.visible_text_controls
        self._visible_signature_controls = self._setup_form.visible_signature_controls
        self._preview_controls = self._build_preview_controls()
        self.preview_controls = self._preview_controls
        self._validation_text = ""

        self._layout.addWidget(self._signature_preset_controls.container)
        self._layout.addWidget(self._certificate_controls.container)
        self._layout.addWidget(self._visible_signature_controls.container)
        self._layout.addWidget(self._placement_controls.container)
        self._layout.addWidget(self._preview_controls.container)

        if self._workflow.signature_appearance is None:
            self._workflow.set_signature_appearance(SignatureAppearance())

        self.load_from_workflow()

    @property
    def container(self) -> Any:
        return self.widget

    @property
    def preview(self) -> SigningDraftPreview:
        return self._workflow.preview()

    def is_ready_to_sign(self) -> bool:
        return self._setup_session.load(control_issue=self._control_issue).ready_to_sign

    def validation_text(self) -> str:
        return self._validation_text

    def dispose(self) -> None:
        self._canonical_preview_lifecycle.dispose()
        self._preview_controls.card_container._canonical_preview_snapshot = None

    def preview_text(self) -> str:
        preview = self._workflow.preview()
        return _preview_stamp_text(preview).strip()

    def refresh_preview(self) -> SigningDraftPreview:
        state = self._setup_session.load(control_issue=self._control_issue)
        return self._apply_coordinator_state(state)

    def load_from_workflow(self) -> None:
        state = self._setup_session.load(control_issue=self._control_issue)
        self._apply_coordinator_state(state)

    def apply_changes(self) -> SigningDraftPreview:
        self._control_issue = None
        try:
            state = self._setup_session.apply_visible_setup(
                self._setup_form.build_draft(),
                control_issue=self._control_issue,
            )
        except ValueError as exc:
            self._control_issue = _build_preview_issue(
                code="signature_appearance_invalid",
                message=str(exc),
                field_name="signature_appearance",
            )
            preview = self.refresh_preview()
        else:
            preview = self._apply_coordinator_state(state)
        self._notify_change()
        return preview

    def _build_preview_controls(self) -> PreviewControls:
        bindings = self._bindings
        container = bindings.q_group_box("Signed appearance preview")
        if hasattr(container, "setStyleSheet"):
            container.setStyleSheet(
                "QGroupBox {"
                " border: 1px solid #cfcfcf;"
                " border-radius: 8px;"
                " padding: 6px;"
                " background: #fcfcfc;"
                "}"
            )
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        summary_label = bindings.q_label(
            "This preview should match the signed PDF."
        )
        if hasattr(summary_label, "setWordWrap"):
            summary_label.setWordWrap(True)
        if hasattr(summary_label, "setStyleSheet"):
            summary_label.setStyleSheet("color: #374151;")

        card_container = bindings.q_group_box("")
        if hasattr(card_container, "setStyleSheet"):
            card_container.setStyleSheet(
                "QGroupBox {"
                " border: 1px solid #d8d8d8;"
                " border-radius: 6px;"
                " padding: 2px;"
                " background: #ffffff;"
                "}"
            )
        card_layout = bindings.q_vbox_layout(card_container)
        card_layout.setContentsMargins(2, 2, 2, 2)
        card_layout.setSpacing(2)

        title_label = bindings.q_label("")
        stamp_label = bindings.q_label("")
        detail_label = bindings.q_label("")
        single_render_label = bindings.q_label("")
        footer_label = bindings.q_label("")
        multi_stamp_label = bindings.q_label("")
        multi_detail_label = bindings.q_label("")
        multi_render_label = bindings.q_label("")
        single_body_container = _compose_preview_column(bindings)
        _set_container_widgets(single_body_container, single_render_label)
        multi_content_container = _compose_preview_column(bindings)
        multi_body_container = bindings.q_widget()
        _set_preview_surface_chrome(multi_body_container)
        multi_body_layout = bindings.q_hbox_layout(multi_body_container)
        multi_body_layout.setContentsMargins(0, 0, 0, 0)
        multi_body_layout.setSpacing(6)
        multi_body_layout.addWidget(multi_render_label)

        for label in (
            title_label,
            stamp_label,
            detail_label,
            single_render_label,
            multi_stamp_label,
            multi_detail_label,
            multi_render_label,
            footer_label,
        ):
            if hasattr(label, "setWordWrap"):
                label.setWordWrap(True)
        for label in (stamp_label, multi_stamp_label, single_render_label, multi_render_label):
            if hasattr(label, "setAlignment"):
                align_center = getattr(bindings.qt, "AlignCenter", None)
                if align_center is not None:
                    label.setAlignment(align_center)
            _set_preview_surface_chrome(label)

        for widget in (single_body_container, multi_content_container):
            _set_preview_surface_chrome(widget)

        if hasattr(stamp_label, "setStyleSheet"):
            stamp_label.setStyleSheet(
                "font-weight: 600; color: #1f2937; border: none;"
                " padding: 0px; background: transparent;"
            )
        if hasattr(multi_stamp_label, "setStyleSheet"):
            multi_stamp_label.setStyleSheet(
                "font-weight: 600; color: #1f2937; border: none;"
                " padding: 0px; background: transparent;"
            )
        if hasattr(title_label, "setStyleSheet"):
            title_label.setStyleSheet(
                "font-weight: 700; font-size: 11pt; color: #111827; margin-bottom: 2px;"
            )
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #111827;")
        if hasattr(multi_detail_label, "setStyleSheet"):
            multi_detail_label.setStyleSheet("color: #111827;")
        if hasattr(footer_label, "setStyleSheet"):
            footer_label.setStyleSheet("color: #374151;")

        card_layout.addWidget(title_label)
        card_layout.addWidget(single_body_container)
        card_layout.addWidget(multi_body_container)
        layout.addWidget(summary_label)
        layout.addWidget(card_container)

        return PreviewControls(
            container=container,
            summary_label=summary_label,
            card_container=card_container,
            title_label=title_label,
            stamp_label=stamp_label,
            detail_label=detail_label,
            single_render_label=single_render_label,
            single_body_container=single_body_container,
            multi_body_container=multi_body_container,
            multi_content_container=multi_content_container,
            multi_stamp_label=multi_stamp_label,
            multi_detail_label=multi_detail_label,
            multi_render_label=multi_render_label,
            footer_label=footer_label,
        )

    def set_signature_rect(
        self,
        signature_rect: SignatureRect | None,
        *,
        notify: bool = True,
    ) -> None:
        self._suspend_updates = True
        try:
            if signature_rect is None:
                self._workflow.clear_signature_rect()
                self._setup_form.set_placement_enabled(False)
            else:
                self._workflow.set_signature_rect(signature_rect)
                self._setup_form.set_placement_enabled(True)
        finally:
            self._suspend_updates = False
        self.load_from_workflow()
        if notify:
            self._notify_change()

    def set_signature_appearance(self, signature_appearance: SignatureAppearance | None) -> None:
        state = self._setup_session.set_signature_appearance(
            signature_appearance,
            control_issue=self._control_issue,
        )
        self._apply_coordinator_state(state)
        self._notify_change()

    def save_current_signature_preset(self) -> ResolvedSignaturePreset | None:
        name = _text(self._signature_preset_controls.preset_name).strip()
        existing = name and name in self._setup_session.load(
            control_issue=self._control_issue
        ).signature_preset_names

        if existing:
            message_box = self._bindings.q_message_box
            yes_value = getattr(message_box, "Yes", None)
            if yes_value is None:
                standard_button = getattr(message_box, "StandardButton", None)
                yes_value = getattr(standard_button, "Yes", None)
            result = message_box.question(
                self.widget,
                "Overwrite signature preset?",
                f"Signature preset '{name}' already exists. Overwrite it?",
            )
            if result != yes_value:
                return None

        try:
            state = self._setup_session.save_preset(
                name,
                overwrite=bool(existing),
                control_issue=self._control_issue,
            )
        except SignaturePropertiesCoordinatorError as exc:
            self._show_signature_preset_error(str(exc))
            return None
        self._apply_coordinator_state(state)
        self._notify_change()
        return self._coordinator.preset_catalog.preset_named(name)

    def delete_current_signature_preset(self) -> SignaturePresetCatalog | None:
        selected_name = _combo_text(self._signature_preset_controls.preset_combo)
        normalized_name = (
            "" if selected_name == SIGNATURE_PRESET_PLACEHOLDER else selected_name
        )
        if not normalized_name.strip():
            self._show_signature_preset_error("Select a signature preset before deleting it.")
            return None

        message_box = self._bindings.q_message_box
        yes_value = getattr(message_box, "Yes", None)
        if yes_value is None:
            standard_button = getattr(message_box, "StandardButton", None)
            yes_value = getattr(standard_button, "Yes", None)
        result = message_box.question(
            self.widget,
            "Delete signature preset?",
            f"Delete signature preset '{selected_name}'?",
        )
        if result != yes_value:
            return None

        try:
            state = self._setup_session.delete_preset(
                normalized_name,
                control_issue=self._control_issue,
            )
        except SignaturePropertiesCoordinatorError as exc:
            self._show_signature_preset_error(str(exc))
            return None
        self._apply_coordinator_state(state)
        self._notify_change()
        return self._coordinator.preset_catalog

    def apply_selected_certificate_configuration(self) -> bool:
        selected_name = _combo_text(self._certificate_controls.configuration_combo)
        normalized_name = (
            "" if selected_name == CERTIFICATE_CONFIGURATION_PLACEHOLDER else selected_name
        )

        try:
            state = self._setup_session.select_certificate_configuration(
                normalized_name,
                control_issue=self._control_issue,
            )
        except SignaturePropertiesCoordinatorError as exc:
            self._show_certificate_configuration_error(str(exc))
            return False
        self._apply_coordinator_state(state.state)
        if not state.applied:
            return False
        self._notify_change()
        return True

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        """Reload certificate configurations from storage and refresh the selector."""
        state = self._setup_session.refresh_catalogs(
            control_issue=self._control_issue,
        )
        self._apply_coordinator_state(state)
        return self._coordinator.certificate_catalog

    @property
    def app_settings(self) -> AppSettings:
        return self._app_settings

    def _build_certificate_configuration_controls(self) -> CertificateConfigurationControls:
        bindings = self._bindings
        container = bindings.q_group_box("Certificate configuration")
        layout = bindings.q_form_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        configuration_combo = bindings.q_combo_box()
        apply_button = bindings.q_push_button("Apply certificate")

        layout.addRow("Saved certificate", configuration_combo)
        layout.addRow("", apply_button)

        apply_button.clicked.connect(  # type: ignore[attr-defined]
            self.apply_selected_certificate_configuration
        )

        return CertificateConfigurationControls(
            container=container,
            configuration_combo=configuration_combo,
            apply_button=apply_button,
        )

    def _build_signature_preset_controls(self) -> SignaturePresetControls:
        bindings = self._bindings
        container = bindings.q_group_box("Signature presets")
        layout = bindings.q_form_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        preset_combo = bindings.q_combo_box()
        preset_name = bindings.q_line_edit()
        preset_name.setPlaceholderText("Enter a preset name")
        save_button = bindings.q_push_button("Save preset")
        delete_button = bindings.q_push_button("Delete preset")

        layout.addRow("Saved preset", preset_combo)
        layout.addRow("Preset name", preset_name)
        layout.addRow("", _compose_row(bindings, save_button, delete_button))

        preset_combo.currentTextChanged.connect(  # type: ignore[attr-defined]
            lambda _text: self._on_signature_preset_selected()
        )
        index_changed = getattr(preset_combo, "currentIndexChanged", None)
        if hasattr(index_changed, "connect"):
            index_changed.connect(  # type: ignore[attr-defined]
                lambda _index: self._on_signature_preset_selected()
            )
        save_button.clicked.connect(  # type: ignore[attr-defined]
            self.save_current_signature_preset
        )
        delete_button.clicked.connect(  # type: ignore[attr-defined]
            self.delete_current_signature_preset
        )

        controls = SignaturePresetControls(
            container=container,
            preset_combo=preset_combo,
            preset_name=preset_name,
            save_button=save_button,
            delete_button=delete_button,
        )
        return controls

    def _render_certificate_configuration_controls(
        self,
        *,
        names: tuple[str, ...],
        selected_name: str | None = None,
    ) -> None:
        configuration_combo = self._certificate_controls.configuration_combo
        clear = getattr(configuration_combo, "clear", None)
        if callable(clear):
            clear()
        elif hasattr(configuration_combo, "_items"):
            configuration_combo._items = []  # type: ignore[attr-defined]
            configuration_combo._current = ""  # type: ignore[attr-defined]

        configuration_combo.addItem(CERTIFICATE_CONFIGURATION_PLACEHOLDER)
        configuration_combo.addItems(names)

        current_name = selected_name if selected_name in names else None

        _set_combo_text(
            configuration_combo,
            current_name or CERTIFICATE_CONFIGURATION_PLACEHOLDER,
        )
        _set_widget_visible(
            self._certificate_controls.container,
            bool(names) or self._certificate_catalog_store is not None,
        )

    def _render_signature_preset_controls(
        self,
        *,
        preset_names: tuple[str, ...],
        selected_name: str | None = None,
    ) -> None:
        preset_combo = self._signature_preset_controls.preset_combo
        clear = getattr(preset_combo, "clear", None)
        if callable(clear):
            clear()
        elif hasattr(preset_combo, "_items"):
            preset_combo._items = []  # type: ignore[attr-defined]
            preset_combo._current = ""  # type: ignore[attr-defined]

        preset_combo.addItem(SIGNATURE_PRESET_PLACEHOLDER)
        preset_combo.addItems(preset_names)
        current_name = selected_name if selected_name in preset_names else None
        _set_combo_text(preset_combo, current_name or SIGNATURE_PRESET_PLACEHOLDER)
        if current_name is None:
            if not _text(self._signature_preset_controls.preset_name).strip():
                _set_text(self._signature_preset_controls.preset_name, "")
        else:
            _set_text(self._signature_preset_controls.preset_name, current_name)

    def _on_signature_preset_selected(self) -> None:
        if self._suspend_updates:
            return
        selected_name = _combo_text(self._signature_preset_controls.preset_combo)
        if selected_name == SIGNATURE_PRESET_PLACEHOLDER:
            selected_name = ""
        try:
            if not selected_name.strip():
                state = self._setup_session.clear_selected_signature_preset(
                    control_issue=self._control_issue,
                )
            else:
                outcome = self._setup_session.select_signature_preset(
                    selected_name,
                    control_issue=self._control_issue,
                )
        except SignaturePropertiesCoordinatorError as exc:
            self._show_signature_preset_error(str(exc))
            self._apply_coordinator_state(
                self._setup_session.load(control_issue=self._control_issue)
            )
            self._notify_change()
            return
        if not selected_name.strip():
            self._apply_coordinator_state(state)
            self._notify_change()
            return
        self._apply_coordinator_state(outcome.state)
        if outcome.applied:
            self._notify_change()

    def _update_preview_controls(self, preview: SigningDraftPreview) -> None:
        layout_state = self._preview_layout.plan(
            preview=preview,
            controls=self._preview_controls,
        )
        canonical_render_state = self._canonical_preview_lifecycle.refresh(
            preview=preview,
            preview_scale=layout_state.preview_scale,
            inner_body_width=layout_state.inner_body_size[0],
            inner_body_height=layout_state.inner_body_size[1],
            fallback_card_style=layout_state.fallback_card_style,
        )
        self._preview_layout.apply(
            preview=preview,
            controls=self._preview_controls,
            state=layout_state,
            canonical_render_state=canonical_render_state,
        )

    def _apply_coordinator_state(
        self,
        state: SignaturePropertiesViewState,
    ) -> SigningDraftPreview:
        self._suspend_updates = True
        try:
            self._setup_form.load(state.visible_signature_setup_draft)
            self._render_certificate_configuration_controls(
                names=state.certificate_configuration_names,
                selected_name=state.selected_certificate_configuration_name,
            )
            self._render_signature_preset_controls(
                preset_names=state.signature_preset_names,
                selected_name=state.selected_signature_preset_name,
            )
        finally:
            self._suspend_updates = False
        preview = state.preview
        self._update_preview_controls(preview)
        self._validation_text = state.validation_text
        return preview

    def _notify_change(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def _handle_visible_signature_form_change(self) -> None:
        if self._suspend_updates:
            return
        self.apply_changes()

    def _handle_visible_signature_page_change(self, page_number: int) -> None:
        if self._suspend_updates:
            return
        self.apply_changes()
        if self._on_page_change is not None:
            self._on_page_change(page_number)

    def _emit_error(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)

    def _show_signature_preset_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.widget, "Signature preset error", message)
            return
        self._emit_error(message)

    def _show_certificate_configuration_error(self, message: str) -> None:
        self._emit_error(message)
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.widget, "Certificate configuration error", message)


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
            on_text_selection_mode_changed=self.set_document_text_selection_mode,
            on_copy_selected_text=self.copy_selected_document_text,
            on_clear_selected_text=self.clear_selected_document_text,
        )
        self._flow_summary_controls = self._sidebar.signing_action_controls
        self._document_review_controls = self._sidebar.document_review_controls
        self._document_text_controls = self._sidebar.document_text_controls
        self._properties_scroll = self._sidebar.properties_scroll
        self._choose_output_button = self._sidebar.choose_output_button
        self._sign_button = self._sidebar.sign_button
        self._open_signed_output_button = self._sidebar.open_signed_output_button
        self._result_label = self._sidebar.result_label
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
        index_changed = getattr(
            self._document_review_controls.signature_selector,
            "currentIndexChanged",
            None,
        )
        self._updating_document_review_selector = False
        if hasattr(index_changed, "connect"):
            index_changed.connect(  # type: ignore[attr-defined]
                self._on_document_review_signature_selected
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
        self.widget.signing_action_panel = (  # type: ignore[attr-defined]
            self._flow_summary_controls.container
        )
        self.widget.choose_output_button = self._choose_output_button  # type: ignore[attr-defined]
        self.widget.open_signed_output_button = (  # type: ignore[attr-defined]
            self._open_signed_output_button
        )
        destroyed_signal = getattr(self.widget, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: self.properties_panel.dispose())
        self.widget.flow_stage_label = (  # type: ignore[attr-defined]
            self._flow_summary_controls.stage_label
        )
        self.widget.flow_detail_label = (  # type: ignore[attr-defined]
            self._flow_summary_controls.detail_label
        )
        self.widget.document_review_headline_label = (  # type: ignore[attr-defined]
            self._document_review_controls.headline_label
        )
        self.widget.document_review_detail_label = (  # type: ignore[attr-defined]
            self._document_review_controls.detail_label
        )
        self.widget.document_review_signature_items_label = (  # type: ignore[attr-defined]
            self._document_review_controls.signature_items_label
        )
        self.widget.document_review_signature_selector = (  # type: ignore[attr-defined]
            self._document_review_controls.signature_selector
        )
        self.widget.document_review_signature_detail_label = (  # type: ignore[attr-defined]
            self._document_review_controls.signature_detail_label
        )
        self.widget.document_text_query_input = (  # type: ignore[attr-defined]
            self._document_text_controls.query_input
        )
        self.widget.document_text_find_button = self._document_text_controls.find_button  # type: ignore[attr-defined]
        self.widget.document_text_previous_button = (  # type: ignore[attr-defined]
            self._document_text_controls.previous_button
        )
        self.widget.document_text_next_button = self._document_text_controls.next_button  # type: ignore[attr-defined]
        self.widget.document_text_copy_button = self._document_text_controls.copy_button  # type: ignore[attr-defined]
        self.widget.document_text_select_mode_checkbox = (  # type: ignore[attr-defined]
            self._document_text_controls.select_mode_checkbox
        )
        self.widget.document_text_copy_selection_button = (  # type: ignore[attr-defined]
            self._document_text_controls.copy_selection_button
        )
        self.widget.document_text_clear_selection_button = (  # type: ignore[attr-defined]
            self._document_text_controls.clear_selection_button
        )
        self.widget.document_text_status_label = (  # type: ignore[attr-defined]
            self._document_text_controls.status_label
        )
        self.widget.document_text_detail_label = (  # type: ignore[attr-defined]
            self._document_text_controls.detail_label
        )
        self.widget.app_settings = self._app_settings  # type: ignore[attr-defined]
        self.widget.sign_result_label = self._result_label  # type: ignore[attr-defined]
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
        self._apply_document_review_workspace_state(
            self._document_review_workspace.load()
        )
        self._apply_signing_action_state(self._signing_action_boundary.load())

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
        self._apply_document_review_workspace_state(state)
        return state.review.review_summary

    def search_document_text(self) -> DocumentTextSearchState:
        query = _text(self._document_text_controls.query_input)
        transition = self._document_review_workspace.search_text(query)
        self._apply_document_review_workspace_transition(transition)
        return transition.state.document_text.search_state

    def next_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.next_text_match()
        self._apply_document_review_workspace_transition(transition)
        return transition.state.document_text.search_state

    def previous_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.previous_text_match()
        self._apply_document_review_workspace_transition(transition)
        return transition.state.document_text.search_state

    def copy_current_document_text_match(self) -> str | None:
        copy_text = self._document_review_workspace.copy_current_text_match()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        transition = self._document_review_workspace.set_text_selection_mode(enabled)
        self._apply_document_review_workspace_transition(transition)
        return transition.state.document_text.selection_mode_enabled

    def copy_selected_document_text(self) -> str | None:
        copy_text = self._document_review_workspace.copy_selected_text()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def clear_selected_document_text(self) -> DocumentTextSelectionState:
        transition = self._document_review_workspace.clear_selected_text()
        self._apply_document_review_workspace_transition(transition)
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
        result = self._signing_action_boundary.submit()
        self._apply_signing_action_state(result.state)
        return result.request

    def open_signed_output(self) -> str | None:
        result = self._signing_action_boundary.open_signed_output()
        return result.opened_output_path

    def choose_output_pdf_path(self) -> str | None:
        initial_path = self._default_output_dialog_path()
        selected = self._bindings.q_file_dialog.getSaveFileName(
            self.widget,
            "Save signed PDF",
            str(initial_path),
            "PDF files (*.pdf)",
        )
        if isinstance(selected, tuple):
            selected_path = str(selected[0])
        else:
            selected_path = str(selected)
        selected_path = selected_path.strip()
        if not selected_path:
            return None
        if not self._confirm_output_overwrite(selected_path):
            return None
        self._apply_signing_action_state(
            self._signing_action_boundary.accept_output_path(selected_path).state
        )
        return selected_path

    def _confirm_output_overwrite(self, selected_path: str) -> bool:
        selected = Path(selected_path)
        if not selected.exists():
            return True
        message_box = self._bindings.q_message_box
        question = getattr(message_box, "question", None)
        if not callable(question):
            return False
        yes_value = getattr(message_box, "Yes", None)
        if yes_value is None:
            standard_button = getattr(message_box, "StandardButton", None)
            yes_value = getattr(standard_button, "Yes", None)
        result = question(
            self.widget,
            "Overwrite signed PDF?",
            f"Replace existing signed PDF at {selected_path}?",
        )
        return result == yes_value

    @property
    def last_signing_result(self) -> SigningResult | None:
        """Return the most recent signing result, if a real executor ran."""
        return self._signing_action_coordinator.last_signing_result

    def _clear_previous_signing_result(self) -> None:
        self._apply_signing_action_state(
            self._signing_action_boundary.invalidate("clear").state
        )

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
        catalog = self.properties_panel.refresh_certificate_configurations()
        self._apply_signing_action_state(self._signing_action_boundary.load())
        return catalog

    def _handle_page_change(self, page_number: int) -> None:
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.change_page(page_number),
        )

    def _sync_signature_overlay(self) -> None:
        setter = getattr(self._viewer_widget, "set_signature_overlay", None)
        if callable(setter):
            setter(self._draft_workflow.signature_rect)

    def _refresh_sign_button_state(self) -> None:
        self._apply_signing_action_state(self._signing_action_boundary.load())

    def _apply_document_review_workspace_state(
        self,
        state: DocumentReviewWorkspaceState,
    ) -> None:
        review_state = state.review
        document_text_state = state.document_text
        self._document_review_controls.headline_label.setText(
            review_state.review_summary.headline
        )
        self._document_review_controls.detail_label.setText(
            review_state.review_summary.detail
        )
        self._document_review_controls.signature_items_label.setText(
            format_document_signature_items(review_state.review_summary.signature_items)
        )
        selector = self._document_review_controls.signature_selector
        self._updating_document_review_selector = True
        try:
            selector.clear()
            if not review_state.signature_labels:
                selector.setEnabled(False)
            else:
                selector.addItems(list(review_state.signature_labels))
                selector.setEnabled(review_state.selector_enabled)
                setter = getattr(selector, "setCurrentIndex", None)
                current_text = getattr(selector, "currentText", None)
                current_label = current_text() if callable(current_text) else None
                if (
                    callable(setter)
                    and review_state.selected_signature_index is not None
                    and current_label != review_state.selected_signature_label
                ):
                    setter(review_state.selected_signature_index)
        finally:
            self._updating_document_review_selector = False
        self._document_review_controls.signature_detail_label.setText(
            review_state.selected_signature_detail
        )
        checkbox = self._document_text_controls.select_mode_checkbox
        is_checked = getattr(checkbox, "isChecked", None)
        if (
            callable(is_checked)
            and bool(is_checked()) != document_text_state.selection_mode_enabled
        ):
            checkbox.setChecked(document_text_state.selection_mode_enabled)
        self._document_text_controls.status_label.setText(
            document_text_state.status_text
        )
        self._document_text_controls.detail_label.setText(
            document_text_state.detail_text
        )
        self._document_text_controls.previous_button.setEnabled(
            document_text_state.search_state.can_go_previous
        )
        self._document_text_controls.next_button.setEnabled(
            document_text_state.search_state.can_go_next
        )
        self._document_text_controls.copy_button.setEnabled(
            document_text_state.search_state.can_copy and self._on_copy_text is not None
        )
        self._document_text_controls.copy_selection_button.setEnabled(
            document_text_state.selection_state.can_copy and self._on_copy_text is not None
        )
        self._document_text_controls.clear_selection_button.setEnabled(
            document_text_state.selection_state.can_clear
        )

    def _on_document_review_signature_selected(self, index: int) -> None:
        if self._updating_document_review_selector:
            return
        state = self._document_review_workspace.select_review_signature(index)
        self._apply_document_review_workspace_state(state)

    def _clear_document_text_highlight_overlay(self) -> None:
        clearer = getattr(self._viewer_widget, "clear_text_highlight_overlay", None)
        if callable(clearer):
            clearer()

    def _apply_document_review_workspace_transition(
        self,
        transition: DocumentReviewWorkspaceTransition,
    ) -> None:
        self._apply_document_review_workspace_state(transition.state)
        self._apply_document_review_workspace_effects(transition.effects)

    def _apply_document_review_workspace_effects(
        self,
        effects: DocumentReviewWorkspaceViewerEffects,
    ) -> None:
        if effects.interaction_mode is not None:
            setter = getattr(self._viewer_widget, "set_interaction_mode", None)
            if callable(setter):
                setter(effects.interaction_mode)
        if effects.clear_highlights:
            self._clear_document_text_highlight_overlay()
        elif effects.highlight_page_index is not None:
            setter = getattr(self._viewer_widget, "set_text_highlight_overlay", None)
            if callable(setter):
                setter(
                    page_index=effects.highlight_page_index,
                    highlight_rects=effects.highlight_rects,
                )
        if effects.jump_to_page_index is None:
            return
        self._apply_workspace_interaction_plan(
            self._workspace_interaction_session.refresh_navigation_to_page_index(
                effects.jump_to_page_index
            ),
        )

    def _apply_placement_context_result(
        self,
        placement_context: SignaturePlacementContext | None,
    ) -> None:
        if placement_context is None:
            return
        self._draft_workflow.set_placement_context(placement_context)

    def _apply_current_placement_context(self) -> None:
        result = self._viewer_interaction_session.current_placement_context()
        self._apply_placement_context_result(result.placement_context)

    def _apply_workspace_interaction_plan(
        self,
        plan: WorkspaceInteractionPlan,
    ) -> None:
        for effect in plan.effects:
            self._apply_workspace_interaction_effect(effect)

    def _apply_workspace_interaction_effect(
        self,
        effect: WorkspaceInteractionEffect,
    ) -> None:
        if isinstance(effect, ApplyReviewTransition):
            self._apply_document_review_workspace_transition(effect.transition)
            return
        if isinstance(effect, EmitInteractionError):
            self._emit_error(effect.message)
            return
        if isinstance(effect, RefreshViewer):
            try:
                self._viewer_widget.refresh(navigation=effect.navigation)
            except Exception as exc:
                self._emit_error(f"{effect.error_summary}: {exc}")
            return
        if isinstance(effect, RefreshCurrentPlacementContext):
            self._apply_current_placement_context()
            return
        if isinstance(effect, ApplyPlacementContext):
            self._apply_placement_context_result(effect.placement_context)
            return
        if isinstance(effect, ApplySignatureRect):
            self.properties_panel.set_signature_rect(
                effect.signature_rect,
                notify=effect.notify,
            )
            return
        if isinstance(effect, SyncSignatureOverlay):
            self._sync_signature_overlay()
            return
        if isinstance(effect, RefreshPreview):
            self.properties_panel.refresh_preview()
            return
        if isinstance(effect, ReloadSigningActionState):
            self._apply_signing_action_state(self._signing_action_boundary.load())
            return
        if isinstance(effect, InvalidateSigningAction):
            self._apply_signing_action_state(
                self._signing_action_boundary.invalidate(effect.reason).state
            )
            return
        raise TypeError(f"Unsupported workspace interaction effect: {effect!r}")

    def _refresh_flow_summary(self) -> None:
        self._apply_signing_action_state(self._signing_action_boundary.load())

    def _apply_signing_action_state(self, state: SigningActionState) -> None:
        self.widget.last_signing_result = state.last_signing_result  # type: ignore[attr-defined]
        self._sidebar.render_signing_action_state(state)

    def _default_output_dialog_path(self) -> Path:
        return suggest_signed_output_path(
            input_pdf_path=self._draft_workflow.input_pdf_path,
            default_output_directory=self._app_settings.default_output_directory,
            current_output_path=self._draft_workflow.output_pdf_path,
        )

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
