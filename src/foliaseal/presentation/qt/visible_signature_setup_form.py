"""Qt boundary for visible-signature setup form construction and state mapping."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.signature_font_registry import validate_signature_font_request
from foliaseal.application.signature_properties_coordinator import (
    VisibleSignaturePlacementDraft,
    VisibleSignatureSetupDraft,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
)

SIGNATURE_FIELD_DISPLAY_ORDER: tuple[SignatureFieldKey, ...] = (
    SignatureFieldKey.DISTINGUISHED_NAME,
    SignatureFieldKey.COMMON_NAME,
    SignatureFieldKey.EMAIL,
    SignatureFieldKey.TITLE,
    SignatureFieldKey.COMPANY,
    SignatureFieldKey.SIGNING_TIME,
    SignatureFieldKey.REASON,
    SignatureFieldKey.LOCATION,
)


@dataclass(frozen=True)
class FieldControls:
    """Controls used to edit one visible signature field."""

    container: Any
    source_combo: Any
    override_edit: Any


@dataclass(frozen=True)
class PlacementControls:
    """Controls used to edit placement and page selection."""

    container: Any
    summary_label: Any
    form_container: Any
    page_spin: Any
    left_spin: Any
    bottom_spin: Any
    width_spin: Any
    height_spin: Any


@dataclass(frozen=True)
class AppearanceControls:
    """Controls and summary used to edit the current appearance draft."""

    container: Any
    summary_label: Any
    signer_label_prefix: Any
    layout_template: Any
    stamp_position: Any
    timezone_display_mode: Any
    datetime_format: Any
    font_family: Any
    font_size: Any
    bold: Any
    italic: Any
    text_color: Any
    image_stamp_path: Any
    border_show: Any
    border_color: Any
    border_width: Any
    background_color: Any
    show_field_names: Any


@dataclass(frozen=True)
class VisibleTextControls:
    """Widgets used to edit visible signature field content."""

    container: Any
    summary_label: Any
    detail_label: Any
    show_field_names: Any
    advanced_toggle: Any
    advanced_container: Any


@dataclass(frozen=True)
class VisibleSignatureControls:
    """Top-level widgets for visible signature setup."""

    container: Any
    summary_label: Any


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


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


def _enum_display_text(
    value: SignatureFieldSource
    | SignatureLayoutTemplate
    | SignatureStampPosition
    | SignatureTimezoneDisplayMode
    | str,
) -> str:
    if isinstance(value, SignatureTimezoneDisplayMode):
        return "UTC" if value == SignatureTimezoneDisplayMode.UTC else "Local"
    if isinstance(value, SignatureStampPosition):
        return value.value.replace("_", " ").title()
    if isinstance(value, SignatureLayoutTemplate):
        return value.value.replace("_", " ").title()
    if isinstance(value, SignatureFieldSource):
        return value.value.title()
    return str(value)


def _enum_combo_items(
    enum_cls: type[
        SignatureFieldSource
        | SignatureLayoutTemplate
        | SignatureStampPosition
        | SignatureTimezoneDisplayMode
    ],
) -> tuple[str, ...]:
    return tuple(_enum_display_text(member) for member in enum_cls)


def _choice_combo_items(*, preferred: str, options: tuple[str, ...]) -> tuple[str, ...]:
    items = [preferred] if preferred not in options else []
    items.extend(options)
    return tuple(items)


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


def _set_widget_visible(widget: Any, visible: bool) -> None:
    setter = getattr(widget, "setVisible", None)
    if callable(setter):
        setter(visible)


def _selected_enum(value: str, enum_cls: type[Any]) -> Any:
    for member in enum_cls:
        if value == member.value or value == _enum_display_text(member):
            return member
    try:
        return enum_cls(value)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_cls)
        raise ValueError(f"Value must be one of: {allowed}.") from exc


class QtVisibleSignatureSetupForm:
    """Owns visible-signature setup controls and mapping to application draft state."""

    def __init__(
        self,
        *,
        bindings: Any,
        on_change: Callable[[], None] | None = None,
        on_page_change: Callable[[int], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._on_change = on_change
        self._on_page_change = on_page_change
        self._suspend_updates = False
        self._placement_enabled = False
        self._advanced_visible_text_expanded = False

        self._placement_controls = self._build_placement_controls()
        self._appearance_controls = self._build_appearance_controls()
        self.field_controls = self._build_field_controls()
        self._visible_text_controls = self._build_visible_text_controls()
        self._visible_signature_controls = self._build_visible_signature_controls()

    @property
    def placement_controls(self) -> PlacementControls:
        return self._placement_controls

    @property
    def appearance_controls(self) -> AppearanceControls:
        return self._appearance_controls

    @property
    def visible_text_controls(self) -> VisibleTextControls:
        return self._visible_text_controls

    @property
    def visible_signature_controls(self) -> VisibleSignatureControls:
        return self._visible_signature_controls

    def load(self, draft: VisibleSignatureSetupDraft) -> None:
        self._suspend_updates = True
        try:
            self._load_placement_controls(draft.placement)
            self._load_appearance_controls(draft.appearance)
            self._load_field_controls(draft.appearance)
        finally:
            self._suspend_updates = False
        self._sync_font_style_control_availability()
        self._refresh_visible_text_summary()

    def build_draft(self) -> VisibleSignatureSetupDraft:
        return VisibleSignatureSetupDraft(
            appearance=self._build_appearance_from_controls(),
            placement=VisibleSignaturePlacementDraft(
                page_number=int(_spin_value(self._placement_controls.page_spin)),
                left_pt=_spin_value(self._placement_controls.left_spin),
                bottom_pt=_spin_value(self._placement_controls.bottom_spin),
                width_pt=_spin_value(self._placement_controls.width_spin),
                height_pt=_spin_value(self._placement_controls.height_spin),
                enabled=self._placement_enabled,
            ),
        )

    def set_placement_enabled(self, enabled: bool) -> None:
        self._placement_enabled = bool(enabled)

    def _build_placement_controls(self) -> PlacementControls:
        bindings = self._bindings
        container = bindings.q_group_box("Placement on page")
        outer_layout = bindings.q_vbox_layout(container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(4)
        summary_label = bindings.q_label(
            "Drag on the PDF, or fine-tune the page, position, and size here."
        )
        if hasattr(summary_label, "setWordWrap"):
            summary_label.setWordWrap(True)
        if hasattr(summary_label, "setStyleSheet"):
            summary_label.setStyleSheet("color: #374151;")
        form_container = bindings.q_widget()
        layout = bindings.q_form_layout(form_container)
        layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(summary_label)
        outer_layout.addWidget(form_container)

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
        layout.addRow("Position", _compose_row(bindings, left_spin, bottom_spin))
        layout.addRow("Size", _compose_row(bindings, width_spin, height_spin))

        page_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        left_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        bottom_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        width_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]
        height_spin.valueChanged.connect(self._on_placement_changed)  # type: ignore[attr-defined]

        return PlacementControls(
            container=container,
            summary_label=summary_label,
            form_container=form_container,
            page_spin=page_spin,
            left_spin=left_spin,
            bottom_spin=bottom_spin,
            width_spin=width_spin,
            height_spin=height_spin,
        )

    def _build_appearance_controls(self) -> AppearanceControls:
        bindings = self._bindings
        container = bindings.q_group_box("Signature style")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        summary_label = bindings.q_label(
            "Choose how the visible signature should look on the page."
        )
        if hasattr(summary_label, "setWordWrap"):
            summary_label.setWordWrap(True)
        if hasattr(summary_label, "setStyleSheet"):
            summary_label.setStyleSheet("color: #374151;")

        text_group = bindings.q_group_box("Text and layout")
        text_layout = bindings.q_form_layout(text_group)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        box_group = bindings.q_group_box("Stamp and border")
        box_layout = bindings.q_form_layout(box_group)
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(4)

        signer_label_prefix = bindings.q_line_edit()
        signer_label_prefix.setPlaceholderText("Digitally signed by")

        layout_template = bindings.q_combo_box()
        layout_template.addItems(_enum_combo_items(SignatureLayoutTemplate))

        stamp_position = bindings.q_combo_box()
        stamp_position.addItems(_enum_combo_items(SignatureStampPosition))

        timezone_display_mode = bindings.q_combo_box()
        timezone_display_mode.addItems(_enum_combo_items(SignatureTimezoneDisplayMode))

        datetime_format = bindings.q_combo_box()
        datetime_format.addItems(
            _choice_combo_items(
                preferred="%Y-%m-%d %H:%M:%S %Z",
                options=(
                    "%Y-%m-%d %H:%M:%S %Z",
                    "%Y-%m-%d %H:%M",
                    "%d/%m/%Y %H:%M",
                    "%b %d, %Y %I:%M %p",
                ),
            )
        )

        font_family = bindings.q_combo_box()
        font_family.addItems(
            _choice_combo_items(
                preferred="Sans Serif",
                options=("Sans Serif", "Serif", "Monospace"),
            )
        )

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
        show_field_names = bindings.q_check_box("Show field names")

        text_layout.addRow(
            "Signer label / Stamp Position",
            _compose_row(bindings, signer_label_prefix, stamp_position),
        )
        text_layout.addRow(
            "Layout / Timezone",
            _compose_row(bindings, layout_template, timezone_display_mode),
        )
        text_layout.addRow(
            "Datetime / Font",
            _compose_row(bindings, datetime_format, font_family),
        )
        text_layout.addRow(
            "Style / Size",
            _compose_row(bindings, font_size, bold, italic),
        )
        text_layout.addRow("Text color", text_color)

        box_layout.addRow("Image stamp", image_stamp_path)
        box_layout.addRow(
            "Border / Background",
            _compose_row(bindings, border_show, border_color, border_width, background_color),
        )

        layout.addWidget(summary_label)
        layout.addWidget(text_group)
        layout.addWidget(box_group)

        for control in (
            signer_label_prefix,
            layout_template,
            stamp_position,
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
            show_field_names,
        ):
            self._connect_change_signal(control)

        return AppearanceControls(
            container=container,
            summary_label=summary_label,
            signer_label_prefix=signer_label_prefix,
            layout_template=layout_template,
            stamp_position=stamp_position,
            timezone_display_mode=timezone_display_mode,
            datetime_format=datetime_format,
            font_family=font_family,
            font_size=font_size,
            bold=bold,
            italic=italic,
            text_color=text_color,
            image_stamp_path=image_stamp_path,
            border_show=border_show,
            border_color=border_color,
            border_width=border_width,
            background_color=background_color,
            show_field_names=show_field_names,
        )

    def _build_field_controls(self) -> dict[SignatureFieldKey, FieldControls]:
        bindings = self._bindings
        controls: dict[SignatureFieldKey, FieldControls] = {}
        for field_key in SIGNATURE_FIELD_DISPLAY_ORDER:
            container = bindings.q_widget()
            layout = bindings.q_hbox_layout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(6)

            label = bindings.q_label(_field_label(field_key))
            if hasattr(label, "setMinimumWidth"):
                label.setMinimumWidth(132)
            source_combo = bindings.q_combo_box()
            source_items = _enum_combo_items(SignatureFieldSource)
            if field_key == SignatureFieldKey.SIGNING_TIME:
                source_items = tuple(
                    item for item in source_items if item != SignatureFieldSource.OVERRIDE.value
                )
            source_combo.addItems(source_items)
            override_edit = bindings.q_line_edit()
            if field_key == SignatureFieldKey.SIGNING_TIME:
                override_edit.setPlaceholderText("Derived at sign time")
            else:
                override_edit.setPlaceholderText("Override text")

            layout.addWidget(label)
            layout.addWidget(source_combo)
            layout.addWidget(override_edit)

            source_combo.currentTextChanged.connect(  # type: ignore[attr-defined]
                lambda _text, key=field_key: self._on_field_source_changed(key)
            )
            index_changed = getattr(source_combo, "currentIndexChanged", None)
            if hasattr(index_changed, "connect"):
                index_changed.connect(  # type: ignore[attr-defined]
                    lambda _index, key=field_key: self._on_field_source_changed(key)
                )
            override_edit.textChanged.connect(  # type: ignore[attr-defined]
                lambda _text, key=field_key: self._on_field_changed(key)
            )

            controls[field_key] = FieldControls(
                container=container,
                source_combo=source_combo,
                override_edit=override_edit,
            )
        return controls

    def _build_visible_text_controls(self) -> VisibleTextControls:
        bindings = self._bindings
        container = bindings.q_group_box("Visible text")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        summary_label = bindings.q_label(
            "Use the default visible signature text unless this document needs field-level changes."
        )
        if hasattr(summary_label, "setWordWrap"):
            summary_label.setWordWrap(True)
        if hasattr(summary_label, "setStyleSheet"):
            summary_label.setStyleSheet("color: #374151;")
        detail_label = bindings.q_label("")
        if hasattr(detail_label, "setWordWrap"):
            detail_label.setWordWrap(True)
        if hasattr(detail_label, "setStyleSheet"):
            detail_label.setStyleSheet("color: #4b5563;")
        advanced_toggle = bindings.q_check_box("Customize individual text fields")
        advanced_container = bindings.q_widget()
        advanced_layout = bindings.q_vbox_layout(advanced_container)
        advanced_layout.setContentsMargins(12, 0, 0, 0)
        advanced_layout.setSpacing(4)

        layout.addWidget(summary_label)
        layout.addWidget(self._appearance_controls.show_field_names)
        layout.addWidget(detail_label)
        layout.addWidget(advanced_toggle)
        layout.addWidget(advanced_container)
        for controls in self.field_controls.values():
            advanced_layout.addWidget(controls.container)

        advanced_toggle.stateChanged.connect(  # type: ignore[attr-defined]
            self._on_advanced_text_toggle
        )
        _set_widget_visible(advanced_container, False)

        return VisibleTextControls(
            container=container,
            summary_label=summary_label,
            detail_label=detail_label,
            show_field_names=self._appearance_controls.show_field_names,
            advanced_toggle=advanced_toggle,
            advanced_container=advanced_container,
        )

    def _build_visible_signature_controls(self) -> VisibleSignatureControls:
        bindings = self._bindings
        container = bindings.q_group_box("Visible signature")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        summary_label = bindings.q_label(
            "Configure the visible signature exactly as it should appear on the PDF."
        )
        if hasattr(summary_label, "setWordWrap"):
            summary_label.setWordWrap(True)
        if hasattr(summary_label, "setStyleSheet"):
            summary_label.setStyleSheet("color: #374151;")
        layout.addWidget(summary_label)
        layout.addWidget(self._appearance_controls.container)
        layout.addWidget(self._visible_text_controls.container)
        return VisibleSignatureControls(
            container=container,
            summary_label=summary_label,
        )

    def _load_placement_controls(self, placement: VisibleSignaturePlacementDraft) -> None:
        _set_spin_value(self._placement_controls.page_spin, placement.page_number)
        _set_spin_value(self._placement_controls.left_spin, placement.left_pt)
        _set_spin_value(self._placement_controls.bottom_spin, placement.bottom_pt)
        _set_spin_value(self._placement_controls.width_spin, placement.width_pt)
        _set_spin_value(self._placement_controls.height_spin, placement.height_pt)
        self._placement_enabled = placement.enabled

    def _load_appearance_controls(self, appearance: SignatureAppearance) -> None:
        _set_text(self._appearance_controls.signer_label_prefix, appearance.signer_label_prefix)
        _set_combo_text(
            self._appearance_controls.layout_template,
            _enum_display_text(appearance.layout_template),
        )
        _set_combo_text(
            self._appearance_controls.stamp_position,
            _enum_display_text(appearance.stamp_position),
        )
        _set_combo_text(
            self._appearance_controls.timezone_display_mode,
            _enum_display_text(appearance.timezone_display_mode),
        )
        _set_checked(self._appearance_controls.show_field_names, appearance.show_field_names)
        _set_combo_text(
            self._appearance_controls.datetime_format,
            appearance.datetime_format,
            allow_custom=True,
        )
        _set_combo_text(
            self._appearance_controls.font_family,
            appearance.text_style.font_family,
            allow_custom=True,
        )
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

    def _load_field_controls(self, appearance: SignatureAppearance) -> None:
        for field_key, binding in appearance.iter_field_bindings():
            controls = self.field_controls[field_key]
            _set_combo_text(controls.source_combo, _enum_display_text(binding.source))
            _set_text(controls.override_edit, binding.override_text or "")
            self._sync_field_control_state(field_key)
        _set_checked(
            self._visible_text_controls.advanced_toggle,
            self._advanced_visible_text_expanded,
        )
        _set_widget_visible(
            self._visible_text_controls.advanced_container,
            self._advanced_visible_text_expanded,
        )

    def _build_appearance_from_controls(self) -> SignatureAppearance:
        text_style = SignatureTextStyle(
            font_family=_combo_text(self._appearance_controls.font_family),
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
            for field_key in SIGNATURE_FIELD_DISPLAY_ORDER
        }
        return SignatureAppearance(
            signer_label_prefix=_text(self._appearance_controls.signer_label_prefix),
            layout_template=_selected_enum(
                _combo_text(self._appearance_controls.layout_template),
                SignatureLayoutTemplate,
            ),
            stamp_position=_selected_enum(
                _combo_text(self._appearance_controls.stamp_position),
                SignatureStampPosition,
            ),
            timezone_display_mode=_selected_enum(
                _combo_text(self._appearance_controls.timezone_display_mode),
                SignatureTimezoneDisplayMode,
            ),
            show_field_names=_is_checked(self._appearance_controls.show_field_names),
            datetime_format=_combo_text(self._appearance_controls.datetime_format),
            field_order=SIGNATURE_FIELD_DISPLAY_ORDER,
            distinguished_name=field_bindings[SignatureFieldKey.DISTINGUISHED_NAME],
            common_name=field_bindings[SignatureFieldKey.COMMON_NAME],
            email=field_bindings[SignatureFieldKey.EMAIL],
            title=field_bindings[SignatureFieldKey.TITLE],
            company=field_bindings[SignatureFieldKey.COMPANY],
            signing_time=field_bindings[SignatureFieldKey.SIGNING_TIME],
            reason=field_bindings[SignatureFieldKey.REASON],
            location=field_bindings[SignatureFieldKey.LOCATION],
            text_style=text_style,
            box_style=box_style,
            image_stamp_path=_text(self._appearance_controls.image_stamp_path) or None,
        )

    def _build_field_binding(self, field_key: SignatureFieldKey) -> SignatureFieldBinding:
        controls = self.field_controls[field_key]
        source = _selected_enum(_combo_text(controls.source_combo), SignatureFieldSource)
        if field_key == SignatureFieldKey.SIGNING_TIME and source == SignatureFieldSource.OVERRIDE:
            source = SignatureFieldSource.DERIVED
        override_text = _text(controls.override_edit) or None
        if source != SignatureFieldSource.OVERRIDE:
            override_text = None
        return SignatureFieldBinding(
            source=source,
            show_in_visible_appearance=source != SignatureFieldSource.HIDDEN,
            override_text=override_text,
        )

    def _sync_field_control_state(self, field_key: SignatureFieldKey) -> None:
        controls = self.field_controls[field_key]
        source = _selected_enum(_combo_text(controls.source_combo), SignatureFieldSource)
        if field_key == SignatureFieldKey.SIGNING_TIME:
            controls.override_edit.setEnabled(False)
            return
        if source == SignatureFieldSource.HIDDEN:
            controls.override_edit.setEnabled(False)
        elif source == SignatureFieldSource.OVERRIDE:
            controls.override_edit.setEnabled(True)
        else:
            controls.override_edit.setEnabled(False)

    def _sync_font_style_control_availability(self) -> None:
        family = _combo_text(self._appearance_controls.font_family)
        bold_checked = _is_checked(self._appearance_controls.bold)
        italic_checked = _is_checked(self._appearance_controls.italic)
        bold_supported = validate_signature_font_request(
            family,
            bold=True,
            italic=False,
        ) is None
        italic_supported = validate_signature_font_request(
            family,
            bold=False,
            italic=True,
        ) is None
        bold_setter = getattr(self._appearance_controls.bold, "setEnabled", None)
        if callable(bold_setter):
            bold_setter(bold_supported or bold_checked)
        italic_setter = getattr(self._appearance_controls.italic, "setEnabled", None)
        if callable(italic_setter):
            italic_setter(italic_supported or italic_checked)

    def _refresh_visible_text_summary(self) -> None:
        bindings = tuple(
            self._build_field_binding(field_key)
            for field_key in SIGNATURE_FIELD_DISPLAY_ORDER
        )
        visible_count = sum(1 for binding in bindings if binding.show_in_visible_appearance)
        override_count = sum(
            1
            for binding in bindings
            if binding.source == SignatureFieldSource.OVERRIDE
        )
        field_names = "on" if _is_checked(self._visible_text_controls.show_field_names) else "off"
        summary = (
            f"Showing {visible_count} visible fields with labels {field_names}. "
            f"{override_count} field override"
            f"{'' if override_count == 1 else 's'} configured. "
            "Open the advanced editor only when individual fields need different sources or text."
        )
        _set_text(self._visible_text_controls.detail_label, summary)

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
        self._sync_font_style_control_availability()
        self._refresh_visible_text_summary()
        if self._on_change is not None:
            self._on_change()

    def _on_field_changed(self, field_key: SignatureFieldKey) -> None:
        if self._suspend_updates:
            return
        self._sync_field_control_state(field_key)
        self._refresh_visible_text_summary()
        if self._on_change is not None:
            self._on_change()

    def _on_field_source_changed(self, field_key: SignatureFieldKey) -> None:
        if self._suspend_updates:
            return
        self._sync_field_control_state(field_key)
        self._refresh_visible_text_summary()
        if self._on_change is not None:
            self._on_change()

    def _on_placement_changed(self, *_args: object) -> None:
        if self._suspend_updates:
            return
        self._placement_enabled = True
        if self._on_change is not None:
            self._on_change()
        if self._on_page_change is not None:
            self._on_page_change(int(_spin_value(self._placement_controls.page_spin)))

    def _on_advanced_text_toggle(self, *_args: object) -> None:
        self._advanced_visible_text_expanded = _is_checked(
            self._visible_text_controls.advanced_toggle
        )
        _set_widget_visible(
            self._visible_text_controls.advanced_container,
            self._advanced_visible_text_expanded,
        )
