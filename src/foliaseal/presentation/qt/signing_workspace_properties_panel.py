"""Qt signing-workspace properties panel and its local helper surface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application import (
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
    SigningSetupSession,
)
from foliaseal.application.certificate_catalog_repository import CertificateCatalogRepository
from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.document_safety import SourceChangeDecision, SourceChangeStatus
from foliaseal.application.reusable_signing_objects import ReusableSigningObjects
from foliaseal.application.signature_properties_coordinator import (
    DefaultSignaturePropertiesCoordinator,
    SignaturePropertiesCoordinatorError,
    SignaturePropertiesViewState,
)
from foliaseal.application.signing_material_resolver import (
    CertificateSigningMaterialPort,
)
from foliaseal.application.signing_readiness import (
    SigningReadiness,
    SigningReadinessInputs,
    project_signing_readiness,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
)
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signature_preview_layout import (
    QtSignaturePreviewLayout,
    _ensure_preview_fonts_registered,
    _preview_stamp_text,
)
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    QtCanonicalPreviewLifecycle,
)
from foliaseal.presentation.qt.signing_workspace_refinement_dialog import (
    RefinementDialogState,
    SignatureRefinementDialog,
)
from foliaseal.presentation.qt.visible_signature_setup_form import (
    QtVisibleSignatureSetupForm,
)

SIGNATURE_PRESET_PLACEHOLDER = "Current document setup"
CERTIFICATE_CONFIGURATION_PLACEHOLDER = "Choose a certificate configuration"


@dataclass(frozen=True)
class SignaturePresetControls:
    """Controls used to manage reusable signature presets."""

    container: Any
    preset_combo: Any
    preset_name: Any
    helper_label: Any
    save_button: Any
    delete_button: Any
    open_library_button: Any


@dataclass(frozen=True)
class CertificateConfigurationControls:
    """Controls used to choose a saved certificate configuration."""

    container: Any
    configuration_combo: Any
    helper_label: Any


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


@dataclass(frozen=True)
class RefinementControls:
    """Compact controls that open the manual refinement dialog."""

    container: Any
    helper_label: Any
    refine_button: Any


class _QtCertificatePassphrasePrompter:
    """Qt adapter for manual certificate-passphrase entry."""

    def __init__(self, *, bindings: Any, parent: Any) -> None:
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


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def _compose_preview_column(bindings: Any, *widgets: Any) -> Any:
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


def _combo_items(combo: Any) -> tuple[str, ...]:
    count_getter = getattr(combo, "count", None)
    item_text_getter = getattr(combo, "itemText", None)
    if callable(count_getter) and callable(item_text_getter):
        return tuple(str(item_text_getter(index)) for index in range(int(count_getter())))
    items = getattr(combo, "_items", None)
    if items is not None:
        return tuple(str(item) for item in items)
    return ()


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


def _set_text(line_edit: Any, value: str) -> None:
    setter = getattr(line_edit, "setText", None)
    if callable(setter):
        setter(value)


def _set_widget_text(widget: Any, value: str) -> None:
    setter = getattr(widget, "setText", None)
    if callable(setter):
        setter(value)


def _set_widget_enabled(widget: Any, enabled: bool) -> None:
    setter = getattr(widget, "setEnabled", None)
    if callable(setter):
        setter(enabled)


def _text(line_edit: Any) -> str:
    getter = getattr(line_edit, "text", None)
    if callable(getter):
        return str(getter())
    return ""


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
        bindings: Any,
        workflow: SigningDraftWorkflow,
        certificate_catalog: CertificateCatalog | None = None,
        certificate_catalog_store: CertificateCatalogRepository | None = None,
        certificate_material_port: CertificateSigningMaterialPort | None = None,
        reusable_objects: ReusableSigningObjects | None = None,
        app_settings: AppSettings | None = None,
        on_change: Callable[[], None] | None = None,
        on_page_change: Callable[[int], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_open_library: Callable[[], Any] | None = None,
        on_source_reload: Callable[[], Any] | None = None,
        on_source_ignore: Callable[[], Any] | None = None,
        on_source_locate: Callable[[], Any] | None = None,
        on_source_close: Callable[[], Any] | None = None,
        source_safety_overlay_parent: Any | None = None,
    ) -> None:
        if reusable_objects is None:
            raise ValueError("reusable_objects is required for the signature properties panel.")
        self._bindings = bindings
        _ensure_preview_fonts_registered()
        self._workflow = workflow
        self._certificate_catalog_store = certificate_catalog_store
        self._coordinator = DefaultSignaturePropertiesCoordinator(
            workflow=workflow,
            certificate_catalog=certificate_catalog,
            certificate_catalog_store=certificate_catalog_store,
            certificate_material_port=certificate_material_port,
            reusable_objects=reusable_objects,
        )
        self._app_settings = app_settings or AppSettings.default()
        self._on_change = on_change
        self._on_page_change = on_page_change
        self._on_error = on_error
        self._on_open_library = on_open_library
        self._on_source_reload = on_source_reload or (lambda: None)
        self._on_source_ignore = on_source_ignore or (lambda: None)
        self._on_source_locate = on_source_locate or (lambda: None)
        self._on_source_close = on_source_close or (lambda: None)
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
        self._source_safety_overlay_parent = source_safety_overlay_parent
        self._source_safety_resize_filter: Any | None = None
        self._source_safety_container = bindings.q_widget()
        if source_safety_overlay_parent is not None:
            set_parent = getattr(self._source_safety_container, "setParent", None)
            if callable(set_parent):
                set_parent(source_safety_overlay_parent)
            elif hasattr(self._source_safety_container, "parent"):
                # Keep lightweight fake bindings parent-aware without requiring
                # a Qt-only API surface.
                self._source_safety_container.parent = source_safety_overlay_parent
            install_filter = getattr(source_safety_overlay_parent, "installEventFilter", None)
            if callable(install_filter):
                panel = self

                class _SourceSafetyResizeFilter(bindings.q_widget):  # type: ignore[misc,valid-type]
                    def eventFilter(self, watched: Any, event: Any) -> bool:  # noqa: N802, ARG002
                        panel._position_source_safety_overlay()
                        return False

                self._source_safety_resize_filter = _SourceSafetyResizeFilter()
                install_filter(self._source_safety_resize_filter)
        source_safety_layout = bindings.q_vbox_layout(self._source_safety_container)
        source_safety_layout.setContentsMargins(8, 8, 8, 8)
        source_safety_layout.setSpacing(4)
        self._source_safety_label = bindings.q_label()
        if hasattr(self._source_safety_label, "setWordWrap"):
            self._source_safety_label.setWordWrap(True)
        source_safety_buttons = bindings.q_hbox_layout()
        self._source_reload_button = bindings.q_push_button("Reload")
        self._source_ignore_button = bindings.q_push_button("Ignore")
        self._source_locate_button = bindings.q_push_button("Locate")
        self._source_close_button = bindings.q_push_button("Close")
        self._source_reload_button.clicked.connect(self._on_source_reload)  # type: ignore[attr-defined]
        self._source_ignore_button.clicked.connect(self._on_source_ignore)  # type: ignore[attr-defined]
        self._source_locate_button.clicked.connect(self._on_source_locate)  # type: ignore[attr-defined]
        self._source_close_button.clicked.connect(self._on_source_close)  # type: ignore[attr-defined]
        source_safety_layout.addWidget(self._source_safety_label)
        source_safety_layout.addLayout(source_safety_buttons)
        for button in (
            self._source_reload_button,
            self._source_ignore_button,
            self._source_locate_button,
            self._source_close_button,
        ):
            source_safety_buttons.addWidget(button)
        if source_safety_overlay_parent is None:
            self._layout.addWidget(self._source_safety_container)

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
        self._refinement_controls = self._build_refinement_controls()
        self.preview_controls = self._preview_controls
        self._validation_text = ""
        self._active_refinement_dialog: Any | None = None

        self._layout.addWidget(self._signature_preset_controls.container)
        self._layout.addWidget(self._certificate_controls.container)
        self._layout.addWidget(self._preview_controls.container)
        self._layout.addWidget(self._refinement_controls.container)

        if self._workflow.signature_appearance is None:
            self._workflow.set_signature_appearance(SignatureAppearance())

        self.load_from_workflow()
        self.refresh_source_safety()

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

    def readiness(self) -> SigningReadiness:
        state = self.load_setup_state()
        certificate_readiness = state.certificate_readiness
        document_safety = self._workflow.document_safety_decision()
        direct_certificate_available = bool(self._coordinator.workflow.certificate_path)
        certificate_selected = (
            state.selected_certificate_configuration_name is not None
            or direct_certificate_available
        )
        return project_signing_readiness(
            SigningReadinessInputs(
                document_safety_status=document_safety.status,
                document_safety_detail=(
                    {
                        SourceChangeStatus.CHANGED: (
                            "The source PDF changed on disk. Review or reload it before signing."
                        ),
                        SourceChangeStatus.MISSING: (
                            "The source PDF is no longer available. Locate it or close "
                            "this document."
                        ),
                        SourceChangeStatus.UNKNOWN: (
                            "The source PDF identity could not be verified. Review it "
                            "before signing."
                        ),
                    }.get(document_safety.status, "")
                ),
                selected_preset_name=state.selected_signature_preset_name,
                has_saved_presets=bool(state.signature_preset_names),
                certificate_selected=certificate_selected,
                certificate_blocking=(
                    False
                    if direct_certificate_available
                    else (
                        certificate_readiness.blocking
                        if certificate_readiness is not None
                        else False
                    )
                ),
                certificate_detail=(
                    certificate_readiness.detail if certificate_readiness is not None else ""
                ),
                certificate_warning=(
                    certificate_readiness.warning if certificate_readiness is not None else False
                ),
                placement_present=self._coordinator.workflow.signature_rect is not None,
                validation_text=state.validation_text,
                ready_to_sign=state.ready_to_sign,
            )
        )

    def dispose(self) -> None:
        parent = self._source_safety_overlay_parent
        resize_filter = self._source_safety_resize_filter
        remove_filter = getattr(parent, "removeEventFilter", None)
        if resize_filter is not None and callable(remove_filter):
            remove_filter(resize_filter)
        self._source_safety_resize_filter = None
        self._canonical_preview_lifecycle.dispose()
        self._preview_controls.card_container._canonical_preview_snapshot = None

    def preview_text(self) -> str:
        preview = self._workflow.preview()
        return _preview_stamp_text(preview).strip()

    def refresh_preview(self) -> SigningDraftPreview:
        return self._render_setup_state()

    def refresh_source_safety(self) -> SourceChangeDecision:
        """Refresh the condition-only source banner and return its current decision."""
        decision = self._workflow.document_safety_decision()
        changed = decision.status in {SourceChangeStatus.CHANGED, SourceChangeStatus.UNKNOWN}
        missing = decision.status is SourceChangeStatus.MISSING
        visible = changed or missing
        set_visible = getattr(self._source_safety_container, "setVisible", None)
        if callable(set_visible):
            set_visible(visible)
        self._position_source_safety_overlay()
        if not visible:
            return decision
        message = (
            "The source PDF changed on disk. Reload it or keep the currently mounted copy."
            if changed
            else "The source PDF is no longer available. Locate it or close this document."
        )
        setter = getattr(self._source_safety_label, "setText", None)
        if callable(setter):
            setter(message)
        for button, button_visible in (
            (self._source_reload_button, changed),
            (self._source_ignore_button, changed),
            (self._source_locate_button, missing),
            (self._source_close_button, missing),
        ):
            set_button_visible = getattr(button, "setVisible", None)
            if callable(set_button_visible):
                set_button_visible(button_visible)
        return decision

    def _position_source_safety_overlay(self) -> None:
        """Keep the source notice over the document canvas, outside the rail layout."""
        parent = self._source_safety_overlay_parent
        if parent is None:
            return
        parent_width = getattr(parent, "width", lambda: 0)()
        parent_height = getattr(parent, "height", lambda: 0)()
        size_hint = getattr(self._source_safety_container, "sizeHint", None)
        hint = size_hint() if callable(size_hint) else None
        hint_height = getattr(hint, "height", lambda: 0)()
        width = max(0, int(parent_width) - 24)
        height = min(max(0, int(hint_height)), max(0, int(parent_height) - 24))
        set_geometry = getattr(self._source_safety_container, "setGeometry", None)
        if callable(set_geometry):
            set_geometry(12, 12, width, height)
        elif hasattr(self._source_safety_container, "properties"):
            self._source_safety_container.properties["overlay_geometry"] = (
                12,
                12,
                width,
                height,
            )
        raise_widget = getattr(self._source_safety_container, "raise", None)
        if callable(raise_widget):
            raise_widget()

    def load_from_workflow(self) -> None:
        self._render_setup_state()

    def load_setup_state(self) -> SignaturePropertiesViewState:
        """Return the current setup through the shell-facing capability boundary."""
        return self._setup_session.load(control_issue=self._control_issue)

    def apply_changes(self) -> SigningDraftPreview:
        self._control_issue = None
        try:
            draft = self._setup_form.build_draft()
        except ValueError as exc:
            self._control_issue = _build_preview_issue(
                code="signature_appearance_invalid",
                message=str(exc),
                field_name="signature_appearance",
            )
            preview = self._render_setup_state()
        else:
            state = self._setup_session.apply_visible_setup(
                draft,
                control_issue=self._control_issue,
            )
            preview = self._render_setup_state(state)
        self._notify_change()
        return preview

    def _render_setup_state(
        self,
        state: SignaturePropertiesViewState | None = None,
    ) -> SigningDraftPreview:
        if state is None:
            state = self._setup_session.load(control_issue=self._control_issue)
        return self._apply_coordinator_state(state)

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

    def _build_refinement_controls(self) -> RefinementControls:
        bindings = self._bindings
        container = bindings.q_group_box("Manual refinement")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        helper_label = bindings.q_label(
            "Adjust appearance or placement for this PDF in a separate dialog."
        )
        if hasattr(helper_label, "setWordWrap"):
            helper_label.setWordWrap(True)
        refine_button = bindings.q_push_button("Refine current setup...")
        refine_button.clicked.connect(  # type: ignore[attr-defined]
            self.open_refinement_dialog
        )
        layout.addWidget(helper_label)
        layout.addWidget(refine_button)
        return RefinementControls(
            container=container,
            helper_label=helper_label,
            refine_button=refine_button,
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

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        """Reload certificate configurations from storage and refresh the selector."""
        state = self._setup_session.refresh_catalogs(
            control_issue=self._control_issue,
        )
        self._apply_coordinator_state(state)
        return self._coordinator.certificate_catalog

    def refresh_signature_profiles(self) -> SignaturePropertiesViewState:
        """Reload reusable profiles and presets, then refresh live selectors."""
        state = self._setup_session.refresh_catalogs(
            control_issue=self._control_issue,
        )
        self._apply_coordinator_state(state)
        return state

    def save_current_signature_preset(self) -> SignaturePropertiesViewState | None:
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
        return state

    def delete_current_signature_preset(self) -> SignaturePropertiesViewState | None:
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
        return state

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

    def open_refinement_dialog(self) -> bool:
        state = self._setup_session.load(control_issue=self._control_issue)
        dialog = SignatureRefinementDialog(
            bindings=self._bindings,
            parent=self.widget,
            setup_session=self._setup_session,
            control_issue_getter=lambda: self._control_issue,
            apply_state=self._apply_coordinator_state,
            on_error=self._show_signature_preset_error,
            certificate_configuration_id_getter=lambda: (
                self._coordinator.workflow.selected_certificate_configuration_id
            ),
            active_state_changed=self._set_active_refinement_dialog,
        )
        result = dialog.open(state.visible_signature_setup_draft)
        if not result.accepted or result.draft is None:
            return False
        applied_state = self._setup_session.apply_visible_setup(
            result.draft,
            control_issue=self._control_issue,
        )
        self._apply_coordinator_state(applied_state)
        self._notify_change()
        return True

    def _set_active_refinement_dialog(
        self,
        state: RefinementDialogState | None,
    ) -> None:
        self._active_refinement_dialog = state

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
        helper_label = bindings.q_label(
            "Certificate configurations are saved signing identities. "
            "Choosing one immediately activates its managed certificate for this PDF."
        )
        helper_label.setWordWrap(True)

        layout.addRow("Certificate configuration", configuration_combo)
        layout.addRow("", helper_label)

        configuration_combo.currentTextChanged.connect(  # type: ignore[attr-defined]
            lambda _text: self._on_certificate_configuration_selected()
        )
        return CertificateConfigurationControls(
            container=container,
            configuration_combo=configuration_combo,
            helper_label=helper_label,
        )

    def _build_signature_preset_controls(self) -> SignaturePresetControls:
        bindings = self._bindings
        container = bindings.q_group_box("Signature preset")
        layout = bindings.q_form_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        preset_combo = bindings.q_combo_box()
        helper_label = bindings.q_label(
            "Signature presets reuse saved appearance and placement choices. "
            "A preset may leave the current certificate unchanged."
        )
        helper_label.setWordWrap(True)
        preset_name = bindings.q_line_edit()
        preset_name.setPlaceholderText("Enter a preset name")
        save_button = bindings.q_push_button("Save preset")
        delete_button = bindings.q_push_button("Delete preset")
        open_library_button = bindings.q_push_button("Create or manage presets…")

        layout.addRow("Signature preset", preset_combo)
        layout.addRow("", helper_label)
        layout.addRow("", open_library_button)

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
        if self._on_open_library is not None:
            open_library_button.clicked.connect(self._on_open_library)  # type: ignore[attr-defined]
        else:
            _set_widget_enabled(open_library_button, False)

        controls = SignaturePresetControls(
            container=container,
            preset_combo=preset_combo,
            preset_name=preset_name,
            helper_label=helper_label,
            save_button=save_button,
            delete_button=delete_button,
            open_library_button=open_library_button,
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
        helper_text = (
            "No saved presets yet. Open the Signature Library to create a required Appearance "
            "and your first preset."
            if not preset_names
            else "Signature presets reuse saved appearance and placement choices. "
            "A preset may leave the current certificate unchanged."
        )
        _set_widget_text(self._signature_preset_controls.helper_label, helper_text)
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

    def _on_certificate_configuration_selected(self) -> None:
        if self._suspend_updates:
            return
        selected_name = _combo_text(self._certificate_controls.configuration_combo)
        normalized_name = (
            "" if selected_name == CERTIFICATE_CONFIGURATION_PLACEHOLDER else selected_name
        )
        if not normalized_name.strip():
            return
        try:
            state = self._setup_session.select_certificate_configuration(
                normalized_name,
                control_issue=self._control_issue,
            )
        except SignaturePropertiesCoordinatorError as exc:
            self._show_certificate_configuration_error(str(exc))
            self._apply_coordinator_state(
                self._setup_session.load(control_issue=self._control_issue)
            )
            self._notify_change()
            return
        self._apply_coordinator_state(state.state)
        if state.applied:
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
            self._setup_form.set_placement_editable(
                self._coordinator.workflow.signature_field_name is None
            )
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
        if state.certificate_readiness is not None:
            _set_widget_text(
                self._certificate_controls.helper_label,
                state.certificate_readiness.detail,
            )
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
