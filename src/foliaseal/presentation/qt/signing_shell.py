"""Qt signing shell for the Phase 3 visible-signature workflow."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from foliaseal.application import (
    SignaturePlacementContext,
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
    render_signing_preview,
)
from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningRequest,
)
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget


class QtSigningBindingsUnavailable(RuntimeError):
    """Raised when PySide6 widget bindings are unavailable."""


@dataclass(frozen=True)
class QtSigningWidgetBindings:
    """Dynamically imported PySide6 symbols used by the signing shell."""

    q_widget: type[Any]
    q_vbox_layout: type[Any]
    q_hbox_layout: type[Any]
    q_form_layout: type[Any]
    q_group_box: type[Any]
    q_label: type[Any]
    q_line_edit: type[Any]
    q_check_box: type[Any]
    q_combo_box: type[Any]
    q_double_spin_box: type[Any]
    q_spin_box: type[Any]
    q_push_button: type[Any]
    qt: Any


@dataclass(frozen=True)
class FieldControls:
    """Controls used to edit one visible signature field."""

    container: Any
    visible_check: Any
    source_combo: Any
    override_edit: Any


@dataclass(frozen=True)
class PlacementControls:
    """Controls used to edit placement and page selection."""

    container: Any
    page_spin: Any
    left_spin: Any
    bottom_spin: Any
    width_spin: Any
    height_spin: Any


def _field_label(field_key: SignatureFieldKey) -> str:
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
    return labels[field_key]


def _enum_combo_items(
    enum_cls: type[SignatureFieldSource | SignatureLayoutTemplate | SignatureTimezoneDisplayMode],
) -> tuple[str, ...]:
    return tuple(member.value for member in enum_cls)


def _set_combo_text(combo: Any, value: str) -> None:
    setter = getattr(combo, "setCurrentText", None)
    if callable(setter):
        setter(value)
        return
    index = getattr(combo, "findText", None)
    if callable(index):
        found = index(value)
        if found >= 0:
            combo.setCurrentIndex(found)


def _combo_text(combo: Any) -> str:
    getter = getattr(combo, "currentText", None)
    if callable(getter):
        return str(getter())
    return ""


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


def _selected_enum(value: str, enum_cls: type[Any]) -> Any:
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_cls)
        raise ValueError(f"Value must be one of: {allowed}.") from exc


def _format_preview_text(
    preview: SigningDraftPreview,
) -> str:
    return "\n".join(line.text for line in render_signing_preview(preview).lines)


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


class SignaturePropertiesPanel:
    """Signature editing controls and preview/validation summary."""

    def __init__(
        self,
        *,
        bindings: QtSigningWidgetBindings,
        workflow: SigningDraftWorkflow,
        on_change: Callable[[], None] | None = None,
        on_page_change: Callable[[int], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._workflow = workflow
        self._on_change = on_change
        self._on_page_change = on_page_change
        self._suspend_updates = False
        self._placement_initialized = workflow.signature_rect is not None
        self._control_issue: SigningDraftValidationIssue | None = None
        self.widget = bindings.q_widget()
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)

        self._placement_controls = self._build_placement_controls()
        self._appearance_controls = self._build_appearance_controls()
        self.field_controls = self._build_field_controls()
        self._preview_label = bindings.q_label("")
        self._validation_label = bindings.q_label("")

        self._layout.addWidget(self._heading("Placement"))
        self._layout.addWidget(self._placement_controls.container)
        self._layout.addWidget(self._heading("Appearance"))
        self._layout.addWidget(self._appearance_controls.container)
        self._layout.addWidget(self._heading("Visible Fields"))
        for controls in self.field_controls.values():
            self._layout.addWidget(controls.container)
        self._layout.addWidget(self._heading("Preview"))
        self._layout.addWidget(self._preview_label)
        self._layout.addWidget(self._heading("Validation"))
        self._layout.addWidget(self._validation_label)

        if self._workflow.signature_appearance is None:
            self._workflow.set_signature_appearance(SignatureAppearance())

        self.load_from_workflow()

    @property
    def container(self) -> Any:
        return self.widget

    @property
    def preview(self) -> SigningDraftPreview:
        return self._current_preview()

    def is_ready_to_sign(self) -> bool:
        preview = self._current_preview()
        if not preview.can_submit:
            return False
        if self._control_issue is None:
            return True
        return self._control_issue.severity != SigningDraftValidationSeverity.ERROR

    def validation_text(self) -> str:
        text = _text(self._validation_label)
        return text

    def preview_text(self) -> str:
        return _text(self._preview_label)

    def refresh_preview(self) -> SigningDraftPreview:
        preview = self._current_preview()
        self._preview_label.setText(_format_preview_text(preview))
        self._validation_label.setText(self._format_validation_text(preview))
        return preview

    def load_from_workflow(self) -> None:
        self._suspend_updates = True
        try:
            self._load_placement_controls()
            self._load_appearance_controls()
            self._load_field_controls()
        finally:
            self._suspend_updates = False
        self.refresh_preview()

    def apply_changes(self) -> SigningDraftPreview:
        self._control_issue = None
        try:
            appearance = self._build_appearance_from_controls()
            self._workflow.set_signature_appearance(appearance)
            if self._placement_initialized or self._workflow.signature_rect is not None:
                self._workflow.set_signature_rect(self._build_rect_from_controls())
        except ValueError as exc:
            self._control_issue = _build_preview_issue(
                code="signature_appearance_invalid",
                message=str(exc),
                field_name="signature_appearance",
            )
        preview = self.refresh_preview()
        self._notify_change()
        return preview

    def set_signature_rect(self, signature_rect: SignatureRect | None) -> None:
        self._suspend_updates = True
        try:
            if signature_rect is None:
                self._workflow.clear_signature_rect()
                self._placement_initialized = False
            else:
                self._workflow.set_signature_rect(signature_rect)
                self._placement_initialized = True
                _set_spin_value(self._placement_controls.page_spin, signature_rect.page_index + 1)
                _set_spin_value(self._placement_controls.left_spin, signature_rect.left_pt)
                _set_spin_value(self._placement_controls.bottom_spin, signature_rect.bottom_pt)
                _set_spin_value(self._placement_controls.width_spin, signature_rect.width_pt)
                _set_spin_value(self._placement_controls.height_spin, signature_rect.height_pt)
        finally:
            self._suspend_updates = False
        self.refresh_preview()
        self._notify_change()

    def set_signature_appearance(self, signature_appearance: SignatureAppearance | None) -> None:
        self._workflow.set_signature_appearance(signature_appearance)
        self.load_from_workflow()
        self._notify_change()

    def _build_placement_controls(self) -> PlacementControls:
        bindings = self._bindings
        container = bindings.q_widget()
        layout = bindings.q_form_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        page_spin = bindings.q_spin_box()
        page_spin.setRange(1, 9999)
        page_spin.setValue(1)

        left_spin = bindings.q_double_spin_box()
        bottom_spin = bindings.q_double_spin_box()
        width_spin = bindings.q_double_spin_box()
        height_spin = bindings.q_double_spin_box()
        for spin in (left_spin, bottom_spin, width_spin, height_spin):
            spin.setRange(-100000.0, 100000.0)
            spin.setDecimals(2)
            spin.setSingleStep(1.0)

        width_spin.setRange(1.0, 100000.0)
        height_spin.setRange(1.0, 100000.0)

        layout.addRow("Page", page_spin)
        layout.addRow("Left", left_spin)
        layout.addRow("Bottom", bottom_spin)
        layout.addRow("Width", width_spin)
        layout.addRow("Height", height_spin)

        page_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        left_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        bottom_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        width_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        height_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]

        return PlacementControls(
            container=container,
            page_spin=page_spin,
            left_spin=left_spin,
            bottom_spin=bottom_spin,
            width_spin=width_spin,
            height_spin=height_spin,
        )

    def _build_appearance_controls(self) -> Any:
        bindings = self._bindings
        container = bindings.q_widget()
        layout = bindings.q_form_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        signer_label_prefix = bindings.q_line_edit()
        signer_label_prefix.setPlaceholderText("Digitally signed by")

        layout_template = bindings.q_combo_box()
        layout_template.addItems(_enum_combo_items(SignatureLayoutTemplate))

        timezone_display_mode = bindings.q_combo_box()
        timezone_display_mode.addItems(_enum_combo_items(SignatureTimezoneDisplayMode))

        datetime_format = bindings.q_line_edit()
        datetime_format.setPlaceholderText("%Y-%m-%d %H:%M:%S %Z")

        font_family = bindings.q_line_edit()
        font_family.setPlaceholderText("Sans Serif")

        font_size = bindings.q_double_spin_box()
        font_size.setRange(4.0, 48.0)
        font_size.setDecimals(1)
        font_size.setSingleStep(0.5)

        bold = bindings.q_check_box("Bold")
        italic = bindings.q_check_box("Italic")

        text_color = bindings.q_line_edit()
        text_color.setPlaceholderText("#000000")

        image_stamp_path = bindings.q_line_edit()
        image_stamp_path.setPlaceholderText("/path/to/stamp.png")

        border_show = bindings.q_check_box("Show border")
        border_color = bindings.q_line_edit()
        border_color.setPlaceholderText("#000000")
        border_width = bindings.q_double_spin_box()
        border_width.setRange(0.5, 10.0)
        border_width.setDecimals(1)
        border_width.setSingleStep(0.5)
        background_color = bindings.q_line_edit()
        background_color.setPlaceholderText("#FFFFFF")

        layout.addRow("Signer label prefix", signer_label_prefix)
        layout.addRow("Layout template", layout_template)
        layout.addRow("Timezone display", timezone_display_mode)
        layout.addRow("Datetime format", datetime_format)
        layout.addRow("Font family", font_family)
        layout.addRow("Font size", font_size)
        layout.addRow("", bold)
        layout.addRow("", italic)
        layout.addRow("Text color", text_color)
        layout.addRow("Image stamp", image_stamp_path)
        layout.addRow("", border_show)
        layout.addRow("Border color", border_color)
        layout.addRow("Border width", border_width)
        layout.addRow("Background color", background_color)

        for control in (
            signer_label_prefix,
            layout_template,
            timezone_display_mode,
            datetime_format,
            font_family,
            font_size,
            bold,
            italic,
            text_color,
            image_stamp_path,
            border_show,
            border_color,
            border_width,
            background_color,
        ):
            self._connect_change_signal(control)

        return type(
            "AppearanceControls",
            (),
            {
                "container": container,
                "signer_label_prefix": signer_label_prefix,
                "layout_template": layout_template,
                "timezone_display_mode": timezone_display_mode,
                "datetime_format": datetime_format,
                "font_family": font_family,
                "font_size": font_size,
                "bold": bold,
                "italic": italic,
                "text_color": text_color,
                "image_stamp_path": image_stamp_path,
                "border_show": border_show,
                "border_color": border_color,
                "border_width": border_width,
                "background_color": background_color,
            },
        )()

    def _build_field_controls(self) -> dict[SignatureFieldKey, FieldControls]:
        bindings = self._bindings
        controls: dict[SignatureFieldKey, FieldControls] = {}
        for field_key in SignatureFieldKey:
            container = bindings.q_widget()
            layout = bindings.q_hbox_layout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            label = bindings.q_label(_field_label(field_key))
            visible_check = bindings.q_check_box("Visible")
            source_combo = bindings.q_combo_box()
            source_combo.addItems(_enum_combo_items(SignatureFieldSource))
            override_edit = bindings.q_line_edit()
            override_edit.setPlaceholderText("Override text")

            layout.addWidget(label)
            layout.addWidget(visible_check)
            layout.addWidget(source_combo)
            layout.addWidget(override_edit)

            visible_check.stateChanged.connect(  # type: ignore[attr-defined]
                lambda _state, key=field_key: self._on_field_changed(key)
            )
            source_combo.currentTextChanged.connect(  # type: ignore[attr-defined]
                lambda _text, key=field_key: self._on_field_source_changed(key)
            )
            override_edit.textChanged.connect(  # type: ignore[attr-defined]
                lambda _text, key=field_key: self._on_field_changed(key)
            )

            controls[field_key] = FieldControls(
                container=container,
                visible_check=visible_check,
                source_combo=source_combo,
                override_edit=override_edit,
            )
        return controls

    def _load_placement_controls(self) -> None:
        rect = self._workflow.signature_rect
        if rect is None:
            _set_spin_value(self._placement_controls.page_spin, 1)
            _set_spin_value(self._placement_controls.left_spin, 24.0)
            _set_spin_value(self._placement_controls.bottom_spin, 18.0)
            _set_spin_value(self._placement_controls.width_spin, 72.0)
            _set_spin_value(self._placement_controls.height_spin, 24.0)
            self._placement_initialized = False
            return

        _set_spin_value(self._placement_controls.page_spin, rect.page_index + 1)
        _set_spin_value(self._placement_controls.left_spin, rect.left_pt)
        _set_spin_value(self._placement_controls.bottom_spin, rect.bottom_pt)
        _set_spin_value(self._placement_controls.width_spin, rect.width_pt)
        _set_spin_value(self._placement_controls.height_spin, rect.height_pt)
        self._placement_initialized = True

    def _load_appearance_controls(self) -> None:
        appearance = self._workflow.signature_appearance or SignatureAppearance()
        _set_text(self._appearance_controls.signer_label_prefix, appearance.signer_label_prefix)
        _set_combo_text(self._appearance_controls.layout_template, appearance.layout_template.value)
        _set_combo_text(
            self._appearance_controls.timezone_display_mode,
            appearance.timezone_display_mode.value,
        )
        _set_text(self._appearance_controls.datetime_format, appearance.datetime_format)
        _set_text(self._appearance_controls.font_family, appearance.text_style.font_family)
        _set_spin_value(self._appearance_controls.font_size, appearance.text_style.font_size_pt)
        _set_checked(self._appearance_controls.bold, appearance.text_style.bold)
        _set_checked(self._appearance_controls.italic, appearance.text_style.italic)
        _set_text(self._appearance_controls.text_color, appearance.text_style.text_color_hex)
        _set_text(
            self._appearance_controls.image_stamp_path,
            appearance.image_stamp_path or "",
        )
        _set_checked(self._appearance_controls.border_show, appearance.box_style.show_border)
        _set_text(
            self._appearance_controls.border_color,
            appearance.box_style.border_color_hex,
        )
        _set_spin_value(
            self._appearance_controls.border_width,
            appearance.box_style.border_width_pt,
        )
        _set_text(
            self._appearance_controls.background_color,
            appearance.box_style.background_color_hex,
        )

    def _load_field_controls(self) -> None:
        appearance = self._workflow.signature_appearance or SignatureAppearance()
        for field_key, binding in appearance.iter_field_bindings():
            controls = self.field_controls[field_key]
            _set_checked(controls.visible_check, binding.show_in_visible_appearance)
            _set_combo_text(controls.source_combo, binding.source.value)
            _set_text(controls.override_edit, binding.override_text or "")
            self._sync_field_control_state(field_key)

    def _build_appearance_from_controls(self) -> SignatureAppearance:
        text_style = SignatureTextStyle(
            font_family=_text(self._appearance_controls.font_family),
            font_size_pt=_spin_value(self._appearance_controls.font_size),
            bold=_is_checked(self._appearance_controls.bold),
            italic=_is_checked(self._appearance_controls.italic),
            text_color_hex=_text(self._appearance_controls.text_color),
        )
        box_style = SignatureBoxStyle(
            show_border=_is_checked(self._appearance_controls.border_show),
            border_color_hex=_text(self._appearance_controls.border_color),
            border_width_pt=_spin_value(self._appearance_controls.border_width),
            background_color_hex=_text(self._appearance_controls.background_color),
        )

        field_bindings = {
            field_key: self._build_field_binding(field_key)
            for field_key in SignatureFieldKey
        }
        return SignatureAppearance(
            signer_label_prefix=_text(self._appearance_controls.signer_label_prefix),
            layout_template=_selected_enum(
                _combo_text(self._appearance_controls.layout_template),
                SignatureLayoutTemplate,
            ),
            timezone_display_mode=_selected_enum(
                _combo_text(self._appearance_controls.timezone_display_mode),
                SignatureTimezoneDisplayMode,
            ),
            datetime_format=_text(self._appearance_controls.datetime_format),
            field_order=tuple(SignatureFieldKey),
            distinguished_name=field_bindings[SignatureFieldKey.DISTINGUISHED_NAME],
            common_name=field_bindings[SignatureFieldKey.COMMON_NAME],
            email=field_bindings[SignatureFieldKey.EMAIL],
            signing_time=field_bindings[SignatureFieldKey.SIGNING_TIME],
            reason=field_bindings[SignatureFieldKey.REASON],
            location=field_bindings[SignatureFieldKey.LOCATION],
            title=field_bindings[SignatureFieldKey.TITLE],
            company=field_bindings[SignatureFieldKey.COMPANY],
            text_style=text_style,
            box_style=box_style,
            image_stamp_path=_text(self._appearance_controls.image_stamp_path) or None,
        )

    def _build_field_binding(self, field_key: SignatureFieldKey) -> SignatureFieldBinding:
        controls = self.field_controls[field_key]
        source = _selected_enum(_combo_text(controls.source_combo), SignatureFieldSource)
        visible = _is_checked(controls.visible_check)
        override_text = _text(controls.override_edit) or None
        if source != SignatureFieldSource.OVERRIDE:
            override_text = None
        return SignatureFieldBinding(
            source=source,
            show_in_visible_appearance=visible,
            override_text=override_text,
        )

    def _build_rect_from_controls(self) -> SignatureRect:
        return SignatureRect(
            page_index=int(_spin_value(self._placement_controls.page_spin) - 1),
            left_pt=_spin_value(self._placement_controls.left_spin),
            bottom_pt=_spin_value(self._placement_controls.bottom_spin),
            width_pt=_spin_value(self._placement_controls.width_spin),
            height_pt=_spin_value(self._placement_controls.height_spin),
        )

    def _current_preview(self) -> SigningDraftPreview:
        preview = self._workflow.preview()
        if self._control_issue is None:
            return preview
        combined_issues = preview.issues + (self._control_issue,)
        can_submit = preview.can_submit
        if self._control_issue.severity == SigningDraftValidationSeverity.ERROR:
            can_submit = False
        return replace(
            preview,
            issues=combined_issues,
            can_submit=can_submit,
        )

    def _format_validation_text(self, preview: SigningDraftPreview) -> str:
        blocking_issues = [
            issue
            for issue in preview.issues
            if issue.severity == SigningDraftValidationSeverity.ERROR
        ]
        warning_issues = [
            issue
            for issue in preview.issues
            if issue.severity == SigningDraftValidationSeverity.WARNING
        ]
        if not blocking_issues:
            lines = ["Ready to sign."]
            lines.extend(
                f"{issue.severity.value.upper()} {issue.code}: {issue.message}"
                for issue in warning_issues
            )
            return "\n".join(lines)
        return "\n".join(
            f"{issue.severity.value.upper()} {issue.code}: {issue.message}"
            for issue in blocking_issues
        )

    def _sync_field_control_state(self, field_key: SignatureFieldKey) -> None:
        controls = self.field_controls[field_key]
        source = _selected_enum(_combo_text(controls.source_combo), SignatureFieldSource)
        if source == SignatureFieldSource.HIDDEN:
            _set_checked(controls.visible_check, False)
            controls.visible_check.setEnabled(False)
            controls.override_edit.setEnabled(False)
        elif source == SignatureFieldSource.OVERRIDE:
            controls.visible_check.setEnabled(True)
            controls.override_edit.setEnabled(True)
        else:
            controls.visible_check.setEnabled(True)
            controls.override_edit.setEnabled(False)

    def _notify_change(self) -> None:
        if self._on_change is not None:
            self._on_change()

    def _heading(self, text: str) -> Any:
        label = self._bindings.q_label(text)
        if hasattr(label, "setStyleSheet"):
            label.setStyleSheet("font-weight: 600;")
        return label

    def _connect_change_signal(self, control: Any) -> None:
        changed_signal = getattr(control, "textChanged", None)
        if hasattr(control, "currentTextChanged"):
            changed_signal = getattr(control, "currentTextChanged")
        elif hasattr(control, "valueChanged"):
            changed_signal = getattr(control, "valueChanged")
        elif hasattr(control, "stateChanged"):
            changed_signal = getattr(control, "stateChanged")
        if changed_signal is not None and hasattr(changed_signal, "connect"):
            changed_signal.connect(self._on_any_control_changed)  # type: ignore[attr-defined]

    def _on_any_control_changed(self, *_args: object) -> None:
        if self._suspend_updates:
            return
        self.apply_changes()

    def _on_field_changed(self, field_key: SignatureFieldKey) -> None:
        if self._suspend_updates:
            return
        self._sync_field_control_state(field_key)
        self.apply_changes()

    def _on_field_source_changed(self, field_key: SignatureFieldKey) -> None:
        if self._suspend_updates:
            return
        self._sync_field_control_state(field_key)
        self.apply_changes()

    def _on_placement_changed(self, *_args: object) -> None:
        if self._suspend_updates:
            return
        self._placement_initialized = True
        self.apply_changes()
        if self._on_page_change is not None:
            self._on_page_change(int(_spin_value(self._placement_controls.page_spin)))


class SigningWorkspaceWidget:
    """Composite widget that combines the viewer and signature editor."""

    def __init__(
        self,
        *,
        bindings: QtSigningWidgetBindings,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._viewer_workflow = viewer_workflow
        self._draft_workflow = signing_workflow
        self._on_sign_request = on_sign_request
        self._on_error = on_error
        self._on_status_change = on_status_change
        self.widget = bindings.q_widget()
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
            on_change=self._handle_panel_change,
            on_page_change=self._handle_page_change,
        )
        self._sign_button = bindings.q_push_button("Confirm and sign")
        self._sign_button.clicked.connect(self.submit_sign_request)  # type: ignore[attr-defined]

        self._layout.addWidget(self._viewer_widget)
        self._layout.addWidget(self.properties_panel.container)
        self._layout.addWidget(self._sign_button)

        self.widget.properties_panel = self.properties_panel  # type: ignore[attr-defined]
        self.widget.viewer_widget = self._viewer_widget  # type: ignore[attr-defined]
        self.widget.refresh_viewer = self.refresh_viewer  # type: ignore[attr-defined]
        self.widget.submit_sign_request = self.submit_sign_request  # type: ignore[attr-defined]
        self.widget._signing_workspace = self  # type: ignore[attr-defined]

        self.refresh_viewer()
        self._refresh_sign_button_state()

    @property
    def container(self) -> Any:
        return self.widget

    @property
    def viewer_widget(self) -> Any:
        return self._viewer_widget

    def refresh_viewer(self) -> None:
        self._viewer_widget.refresh()
        self._sync_placement_context_from_viewer()
        self.properties_panel.refresh_preview()
        self._refresh_sign_button_state()

    def submit_sign_request(self) -> SigningRequest | None:
        self.properties_panel.apply_changes()
        if not self.properties_panel.is_ready_to_sign():
            self._emit_error(self.properties_panel.validation_text())
            return None
        request = self._draft_workflow.build_signing_request()
        if self._on_sign_request is not None:
            self._on_sign_request(request)
        return request

    def _handle_viewer_selection(self, pdf_rect: PdfRect) -> None:
        page_index = self._viewer_workflow.session.current_page
        signature_rect = SignatureRect(
            page_index=page_index,
            left_pt=pdf_rect.x1,
            bottom_pt=pdf_rect.y1,
            width_pt=pdf_rect.x2 - pdf_rect.x1,
            height_pt=pdf_rect.y2 - pdf_rect.y1,
        )
        self.properties_panel.set_signature_rect(signature_rect)
        self._sync_placement_context_from_viewer()
        self._refresh_sign_button_state()

    def _handle_viewer_error(self, message: str) -> None:
        self._emit_error(message)

    def _handle_viewer_interaction(self, name: str) -> None:
        if self._on_status_change is not None:
            self._on_status_change(name)

    def _handle_panel_change(self) -> None:
        self._sync_placement_context_from_viewer()
        self._refresh_sign_button_state()

    def _handle_page_change(self, page_number: int) -> None:
        target_index = max(page_number - 1, 0)
        try:
            self._viewer_workflow.jump_to_page(target_index)
            self._viewer_widget.refresh(navigation=True)
        except Exception as exc:
            self._emit_error(f"Unable to change PDF page: {exc}")
            return
        self._sync_placement_context_from_viewer()
        self._refresh_sign_button_state()

    def _sync_placement_context_from_viewer(self) -> None:
        snapshot = getattr(self._viewer_workflow, "snapshot", None)
        if snapshot is None:
            return
        page_box = snapshot.page_box
        self._draft_workflow.set_placement_context(
            SignaturePlacementContext(
                page_index=snapshot.page_index,
                page_box=PageBox(
                    left=page_box.left,
                    bottom=page_box.bottom,
                    right=page_box.right,
                    top=page_box.top,
                ),
                rotation=snapshot.rotation,
            )
        )

    def _refresh_sign_button_state(self) -> None:
        self._sign_button.setEnabled(self.properties_panel.is_ready_to_sign())

    def _emit_error(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)
            return
        raise RuntimeError(message)


class SigningShellAdapter:
    """Factory for the Phase 3 Qt signing shell."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create(
        self,
        *,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> Any:
        return SigningWorkspaceWidget(
            bindings=self._bindings,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            on_sign_request=on_sign_request,
            on_error=on_error,
            on_status_change=on_status_change,
        ).container

    def _load_bindings(self) -> QtSigningWidgetBindings:
        try:
            qt_widgets = importlib.import_module("PySide6.QtWidgets")
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
            q_group_box=getattr(qt_widgets, "QGroupBox"),
            q_label=getattr(qt_widgets, "QLabel"),
            q_line_edit=getattr(qt_widgets, "QLineEdit"),
            q_check_box=getattr(qt_widgets, "QCheckBox"),
            q_combo_box=getattr(qt_widgets, "QComboBox"),
            q_double_spin_box=getattr(qt_widgets, "QDoubleSpinBox"),
            q_spin_box=getattr(qt_widgets, "QSpinBox"),
            q_push_button=getattr(qt_widgets, "QPushButton"),
            qt=None,
        )


def build_qt_signing_shell(
    *,
    viewer_workflow: ViewerWorkflow,
    signing_workflow: SigningDraftWorkflow,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> Any:
    """Build a QWidget instance for the Phase 3 signing shell."""

    adapter = SigningShellAdapter()
    return adapter.create(
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )
