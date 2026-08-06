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
from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.signature_properties_coordinator import (
    DefaultSignaturePropertiesCoordinator,
    SignaturePropertiesCoordinatorError,
    SignaturePropertiesViewState,
)
from foliaseal.application.signing_material_resolver import CertificateSecretProvider
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
)
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
from foliaseal.presentation.qt.signature_preview_layout import (
    QtSignaturePreviewLayout,
    _ensure_preview_fonts_registered,
    _preview_stamp_text,
)
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    QtCanonicalPreviewLifecycle,
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
    save_button: Any
    delete_button: Any


@dataclass(frozen=True)
class CertificateConfigurationControls:
    """Controls used to choose a saved certificate configuration."""

    container: Any
    configuration_combo: Any


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


@dataclass(frozen=True)
class RefinementDialogState:
    """Ephemeral dialog state retained only while the refinement dialog is open."""

    dialog: Any
    setup_form: QtVisibleSignatureSetupForm
    apply_button: Any
    save_appearance_button: Any
    save_placement_button: Any
    save_preset_button: Any
    appearance_profile_combo: Any
    placement_profile_combo: Any
    cancel_button: Any


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
        certificate_catalog_store: CertificateCatalogStore | None = None,
        certificate_secret_provider: CertificateSecretProvider | None = None,
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: Any | None = None,
        app_settings: AppSettings | None = None,
        on_change: Callable[[], None] | None = None,
        on_page_change: Callable[[int], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        _ensure_preview_fonts_registered()
        self._workflow = workflow
        self._certificate_catalog_store = certificate_catalog_store
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
        return self._render_setup_state()

    def load_from_workflow(self) -> None:
        self._render_setup_state()

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
        draft = self._setup_session.load(
            control_issue=self._control_issue
        ).visible_signature_setup_draft
        dialog = self._bindings.q_dialog(self.widget)
        if hasattr(dialog, "setWindowTitle"):
            dialog.setWindowTitle("Refine current PDF setup")
        layout = self._bindings.q_vbox_layout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        helper_label = self._bindings.q_label(
            "Use this dialog to adjust the current PDF's visible signature "
            "without reopening the old inline editor in the main window."
        )
        if hasattr(helper_label, "setWordWrap"):
            helper_label.setWordWrap(True)
        layout.addWidget(helper_label)

        setup_form = QtVisibleSignatureSetupForm(bindings=self._bindings)
        setup_form.load(draft)
        layout.addWidget(setup_form.visible_signature_controls.container)
        layout.addWidget(setup_form.placement_controls.container)

        profile_state = self._setup_session.load(control_issue=self._control_issue)
        appearance_profile_combo = self._bindings.q_combo_box()
        appearance_profile_combo.addItems(profile_state.appearance_profile_names)
        placement_profile_combo = self._bindings.q_combo_box()
        placement_profile_combo.addItem("No saved placement profile")
        placement_profile_combo.addItems(profile_state.placement_profile_names)
        profile_row = _compose_row(
            self._bindings,
            self._bindings.q_label("Appearance profile"),
            appearance_profile_combo,
            self._bindings.q_label("Placement profile"),
            placement_profile_combo,
        )
        layout.addWidget(profile_row)

        def _refresh_profile_choices(state: SignaturePropertiesViewState) -> None:
            appearance_profile_combo.clear()
            appearance_profile_combo.addItems(state.appearance_profile_names)
            placement_profile_combo.clear()
            placement_profile_combo.addItem("No saved placement profile")
            placement_profile_combo.addItems(state.placement_profile_names)

        apply_button = self._bindings.q_push_button("Apply")
        save_appearance_button = self._bindings.q_push_button("Save appearance for reuse...")
        save_placement_button = self._bindings.q_push_button("Save placement for reuse...")
        save_preset_button = self._bindings.q_push_button("Save signature preset for reuse...")
        cancel_button = self._bindings.q_push_button("Cancel")
        action_row = _compose_row(
            self._bindings,
            save_appearance_button,
            save_placement_button,
            save_preset_button,
            apply_button,
            cancel_button,
        )
        layout.addWidget(action_row)

        def _accept() -> None:
            dialog._selected_draft = setup_form.build_draft()  # type: ignore[attr-defined]
            accept = getattr(dialog, "accept", None)
            if callable(accept):
                accept()

        def _reject() -> None:
            reject = getattr(dialog, "reject", None)
            if callable(reject):
                reject()

        apply_button.clicked.connect(_accept)  # type: ignore[attr-defined]

        def _save_appearance() -> None:
            get_text = getattr(self._bindings.q_input_dialog, "getText", None)
            if not callable(get_text):
                return
            name, accepted = get_text(dialog, "Save appearance profile", "Profile name")
            if not accepted:
                return
            try:
                state = self._setup_session.save_appearance_profile(
                    str(name),
                    setup_form.build_draft().appearance,
                    control_issue=self._control_issue,
                )
                _refresh_profile_choices(state)
            except SignaturePropertiesCoordinatorError as exc:
                self._show_signature_preset_error(str(exc))

        save_appearance_button.clicked.connect(_save_appearance)  # type: ignore[attr-defined]

        def _save_placement() -> None:
            get_text = getattr(self._bindings.q_input_dialog, "getText", None)
            if not callable(get_text):
                return
            name, accepted = get_text(dialog, "Save placement profile", "Profile name")
            if not accepted:
                return
            try:
                state = self._setup_session.save_placement_profile(
                    str(name),
                    setup_form.build_draft().placement,
                    control_issue=self._control_issue,
                )
                _refresh_profile_choices(state)
            except SignaturePropertiesCoordinatorError as exc:
                self._show_signature_preset_error(str(exc))

        save_placement_button.clicked.connect(_save_placement)  # type: ignore[attr-defined]

        def _save_preset() -> None:
            appearance_name = _combo_text(appearance_profile_combo).strip()
            if not appearance_name:
                self._show_signature_preset_error(
                    "Save an appearance profile before composing a signature preset."
                )
                return
            get_text = getattr(self._bindings.q_input_dialog, "getText", None)
            if not callable(get_text):
                return
            name, accepted = get_text(dialog, "Save signature preset", "Preset name")
            if not accepted:
                return
            placement_name = _combo_text(placement_profile_combo).strip()
            if placement_name == "No saved placement profile":
                placement_name = ""
            try:
                state = self._setup_session.compose_signature_preset(
                    str(name),
                    appearance_name,
                    placement_profile_name=placement_name or None,
                    certificate_configuration_id=self._coordinator.workflow.selected_certificate_configuration_id,
                    control_issue=self._control_issue,
                )
                self._apply_coordinator_state(state)
            except SignaturePropertiesCoordinatorError as exc:
                self._show_signature_preset_error(str(exc))

        save_preset_button.clicked.connect(_save_preset)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(_reject)  # type: ignore[attr-defined]

        self._active_refinement_dialog = RefinementDialogState(
            dialog=dialog,
            setup_form=setup_form,
            apply_button=apply_button,
            save_appearance_button=save_appearance_button,
            save_placement_button=save_placement_button,
            save_preset_button=save_preset_button,
            appearance_profile_combo=appearance_profile_combo,
            placement_profile_combo=placement_profile_combo,
            cancel_button=cancel_button,
        )

        dialog_exec = getattr(dialog, "exec", None)
        result = dialog_exec() if callable(dialog_exec) else None
        self._active_refinement_dialog = None
        if result != self._accepted_dialog_code():
            return False

        selected_draft = getattr(dialog, "_selected_draft", None)
        if selected_draft is None:
            return False
        state = self._setup_session.apply_visible_setup(
            selected_draft,
            control_issue=self._control_issue,
        )
        self._apply_coordinator_state(state)
        self._notify_change()
        return True

    @property
    def app_settings(self) -> AppSettings:
        return self._app_settings

    def _accepted_dialog_code(self) -> Any:
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        if accepted is not None:
            return accepted
        dialog_code = getattr(self._bindings.q_dialog, "DialogCode", None)
        return getattr(dialog_code, "Accepted", None)

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

        layout.addRow("Signature preset", preset_combo)
        layout.addRow("", helper_label)

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
