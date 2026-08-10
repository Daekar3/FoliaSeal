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
    font_family: Any
    font_size: Any
    bold: Any
    italic: Any
    show_field_names: Any
    datetime_format: Any
    field_order: Any
    move_field_up: Any
    move_field_down: Any
    text_color: Any
    border_show: Any
    border_color: Any
    border_width: Any
    background_color: Any


@dataclass(frozen=True)
class VisibleTextControls:
    """Widgets used to edit visible signature field content."""

    container: Any
    summary_label: Any
    detail_label: Any
    show_field_names: Any
    field_checks_container: Any


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


def _enum_display_text(
    value: SignatureLayoutTemplate
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
    return str(value)


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
    enum_cls: type[
        SignatureLayoutTemplate
        | SignatureStampPosition
        | SignatureTimezoneDisplayMode
    ],
) -> tuple[str, ...]:
    return tuple(_enum_display_text(member) for member in enum_cls)


_BOUNDED_DATETIME_FORMATS = (
    ("2026-08-08 14:35 UTC", "%Y-%m-%d %H:%M %Z"),
    ("Aug 8, 2026, 2:35 PM UTC", "%b %-d, %Y, %-I:%M %p %Z"),
    ("2026-08-08T18:35:00Z", "%Y-%m-%dT%H:%M:%SZ"),
)


def _field_order_label(field_key: SignatureFieldKey) -> str:
    return _field_label(field_key)


def _standard_field_binding() -> SignatureFieldBinding:
    return SignatureFieldBinding(
        source=SignatureFieldSource.DERIVED,
        show_in_visible_appearance=True,
        override_text=None,
    )


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
        self._field_order = SIGNATURE_FIELD_DISPLAY_ORDER
        self._appearance_template = SignatureAppearance()

        self._placement_controls = self._build_placement_controls()
        self._appearance_controls = self._build_appearance_controls()
        self._field_visibility_checks: dict[SignatureFieldKey, Any] = {}
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
            self._load_field_visibility_controls(draft.appearance)
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

    def set_placement_editable(self, editable: bool) -> None:
        """Enable or lock page/geometry controls for fixed existing fields."""
        for widget in (
            self._placement_controls.page_spin,
            self._placement_controls.left_spin,
            self._placement_controls.bottom_spin,
            self._placement_controls.width_spin,
            self._placement_controls.height_spin,
        ):
            setter = getattr(widget, "setEnabled", None)
            if callable(setter):
                setter(bool(editable))

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

        for spin, name in (
            (page_spin, "Signature page"),
            (left_spin, "Signature left position in points"),
            (bottom_spin, "Signature bottom position in points"),
            (width_spin, "Signature width in points"),
            (height_spin, "Signature height in points"),
        ):
            set_accessible_name = getattr(spin, "setAccessibleName", None)
            if callable(set_accessible_name):
                set_accessible_name(name)

        layout.addRow("Page", page_spin)
        layout.addRow(
            "Position",
            _compose_row(
                bindings,
                bindings.q_label("Left (pt)"),
                left_spin,
                bindings.q_label("Bottom (pt)"),
                bottom_spin,
            ),
        )
        layout.addRow(
            "Size",
            _compose_row(
                bindings,
                bindings.q_label("Width (pt)"),
                width_spin,
                bindings.q_label("Height (pt)"),
                height_spin,
            ),
        )

        set_tab_order = getattr(container, "setTabOrder", None)
        if callable(set_tab_order):
            for first, second in (
                (page_spin, left_spin),
                (left_spin, bottom_spin),
                (bottom_spin, width_spin),
                (width_spin, height_spin),
            ):
                set_tab_order(first, second)

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
            "Refine the preset's visible signature with the bounded choices used by the MVP."
        )
        if hasattr(summary_label, "setWordWrap"):
            summary_label.setWordWrap(True)
        if hasattr(summary_label, "setStyleSheet"):
            summary_label.setStyleSheet("color: #374151;")

        text_group = bindings.q_group_box("Text and layout")
        text_layout = bindings.q_form_layout(text_group)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        signer_label_prefix = bindings.q_line_edit()
        signer_label_prefix.setPlaceholderText("Digitally signed by")

        layout_template = bindings.q_combo_box()
        layout_template.addItems(_enum_combo_items(SignatureLayoutTemplate))

        stamp_position = bindings.q_combo_box()
        stamp_position.addItems(_enum_combo_items(SignatureStampPosition))

        timezone_display_mode = bindings.q_combo_box()
        timezone_display_mode.addItems(_enum_combo_items(SignatureTimezoneDisplayMode))

        datetime_format = bindings.q_combo_box()
        datetime_format.addItems(tuple(label for label, _value in _BOUNDED_DATETIME_FORMATS))

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
        show_field_names = bindings.q_check_box("Show field names")
        field_order = bindings.q_combo_box()
        field_order.addItems(
            tuple(_field_order_label(key) for key in SIGNATURE_FIELD_DISPLAY_ORDER)
        )
        move_field_up = bindings.q_push_button("Move field up")
        move_field_down = bindings.q_push_button("Move field down")
        text_color = bindings.q_line_edit()
        text_color.setPlaceholderText("#RRGGBB")
        border_show = bindings.q_check_box("Border")
        border_color = bindings.q_line_edit()
        border_color.setPlaceholderText("#RRGGBB")
        border_width = bindings.q_double_spin_box()
        border_width.setRange(0.1, 12.0)
        border_width.setDecimals(1)
        border_width.setSingleStep(0.5)
        background_color = bindings.q_line_edit()
        background_color.setPlaceholderText("#RRGGBB")

        text_layout.addRow(
            "Signer label / Stamp Position",
            _compose_row(bindings, signer_label_prefix, stamp_position),
        )
        text_layout.addRow(
            "Layout / Timezone",
            _compose_row(bindings, layout_template, timezone_display_mode, datetime_format),
        )
        text_layout.addRow(
            "Font / Size",
            _compose_row(bindings, font_family, font_size),
        )
        text_layout.addRow(
            "Weight / Labels",
            _compose_row(bindings, bold, italic, show_field_names),
        )
        text_layout.addRow(
            "Field order",
            _compose_row(bindings, field_order, move_field_up, move_field_down),
        )
        text_layout.addRow("Text color", text_color)
        text_layout.addRow(
            "Border",
            _compose_row(bindings, border_show, border_color, border_width),
        )
        text_layout.addRow("Background color", background_color)

        layout.addWidget(summary_label)
        layout.addWidget(text_group)

        for control in (
            signer_label_prefix,
            layout_template,
            stamp_position,
            timezone_display_mode,
            font_family,
            font_size,
            bold,
            italic,
            show_field_names,
            datetime_format,
            field_order,
            text_color,
            border_show,
            border_color,
            border_width,
            background_color,
        ):
            self._connect_change_signal(control)
        move_field_up.clicked.connect(self._move_field_up)  # type: ignore[attr-defined]
        move_field_down.clicked.connect(self._move_field_down)  # type: ignore[attr-defined]

        return AppearanceControls(
            container=container,
            summary_label=summary_label,
            signer_label_prefix=signer_label_prefix,
            layout_template=layout_template,
            stamp_position=stamp_position,
            timezone_display_mode=timezone_display_mode,
            font_family=font_family,
            font_size=font_size,
            bold=bold,
            italic=italic,
            show_field_names=show_field_names,
            datetime_format=datetime_format,
            field_order=field_order,
            move_field_up=move_field_up,
            move_field_down=move_field_down,
            text_color=text_color,
            border_show=border_show,
            border_color=border_color,
            border_width=border_width,
            background_color=background_color,
        )

    def _build_visible_text_controls(self) -> VisibleTextControls:
        bindings = self._bindings
        container = bindings.q_group_box("Visible text")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        summary_label = bindings.q_label(
            "Use the preset's standard signing details, and hide fields only when needed."
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
        field_checks_container = bindings.q_widget()
        field_checks_layout = bindings.q_vbox_layout(field_checks_container)
        field_checks_layout.setContentsMargins(12, 0, 0, 0)
        field_checks_layout.setSpacing(3)

        for field_key in SIGNATURE_FIELD_DISPLAY_ORDER:
            check_box = bindings.q_check_box(_field_label(field_key))
            self._field_visibility_checks[field_key] = check_box
            check_box.stateChanged.connect(self._on_any_control_changed)  # type: ignore[attr-defined]
            field_checks_layout.addWidget(check_box)

        layout.addWidget(summary_label)
        layout.addWidget(self._appearance_controls.show_field_names)
        layout.addWidget(detail_label)
        layout.addWidget(field_checks_container)

        return VisibleTextControls(
            container=container,
            summary_label=summary_label,
            detail_label=detail_label,
            show_field_names=self._appearance_controls.show_field_names,
            field_checks_container=field_checks_container,
        )

    def _build_visible_signature_controls(self) -> VisibleSignatureControls:
        bindings = self._bindings
        container = bindings.q_group_box("Visible signature")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        summary_label = bindings.q_label(
            "Start from a signature preset, then adjust the visible approval signature as needed."
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
        self._field_order = appearance.field_order
        self._appearance_template = appearance
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
        format_label = next(
            (
                label
                for label, value in _BOUNDED_DATETIME_FORMATS
                if value == appearance.datetime_format
            ),
            appearance.datetime_format,
        )
        _set_combo_text(self._appearance_controls.datetime_format, format_label, allow_custom=True)
        _set_checked(self._appearance_controls.show_field_names, appearance.show_field_names)
        _set_combo_text(
            self._appearance_controls.field_order,
            _field_order_label(appearance.field_order[0]),
        )
        self._set_field_order_items(appearance.field_order)
        _set_combo_text(
            self._appearance_controls.font_family,
            appearance.text_style.font_family,
            allow_custom=True,
        )
        _set_spin_value(self._appearance_controls.font_size, appearance.text_style.font_size_pt)
        _set_checked(self._appearance_controls.bold, appearance.text_style.bold)
        _set_checked(self._appearance_controls.italic, appearance.text_style.italic)
        _set_text(self._appearance_controls.text_color, appearance.text_style.text_color_hex)
        _set_checked(self._appearance_controls.border_show, appearance.box_style.show_border)
        _set_text(self._appearance_controls.border_color, appearance.box_style.border_color_hex)
        _set_spin_value(
            self._appearance_controls.border_width,
            appearance.box_style.border_width_pt,
        )
        _set_text(
            self._appearance_controls.background_color,
            appearance.box_style.background_color_hex,
        )

    def _build_appearance_from_controls(self) -> SignatureAppearance:
        preserved = self._appearance_template
        text_style = SignatureTextStyle(
            font_family=_combo_text(self._appearance_controls.font_family),
            font_size_pt=_spin_value(self._appearance_controls.font_size),
            bold=_is_checked(self._appearance_controls.bold),
            italic=_is_checked(self._appearance_controls.italic),
            text_color_hex=preserved.text_style.text_color_hex,
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
            datetime_format=self._datetime_format_value(),
            field_order=self._field_order_from_controls(),
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
            image_stamp_path=preserved.image_stamp_path,
        )

    def _datetime_format_value(self) -> str:
        selected = _combo_text(self._appearance_controls.datetime_format)
        for label, value in _BOUNDED_DATETIME_FORMATS:
            if selected == label:
                return value
        return selected

    def _field_order_from_controls(self) -> tuple[SignatureFieldKey, ...]:
        labels = _combo_items(self._appearance_controls.field_order)
        by_label = {_field_order_label(key): key for key in SIGNATURE_FIELD_DISPLAY_ORDER}
        return tuple(by_label[label] for label in labels if label in by_label)

    def _set_field_order_items(self, field_order: tuple[SignatureFieldKey, ...]) -> None:
        combo = self._appearance_controls.field_order
        clear = getattr(combo, "clear", None)
        if callable(clear):
            clear()
        labels = tuple(_field_order_label(key) for key in field_order)
        add_items = getattr(combo, "addItems", None)
        if callable(add_items):
            add_items(labels)

    def _move_field_up(self) -> None:
        self._move_field(-1)

    def _move_field_down(self) -> None:
        self._move_field(1)

    def _move_field(self, offset: int) -> None:
        combo = self._appearance_controls.field_order
        index_getter = getattr(combo, "currentIndex", None)
        setter = getattr(combo, "setCurrentIndex", None)
        if not callable(index_getter) or not callable(setter):
            return
        current = int(index_getter())
        labels = list(_combo_items(combo))
        target = current + offset
        if current < 0 or target < 0 or target >= len(labels):
            return
        labels[current], labels[target] = labels[target], labels[current]
        clear = getattr(combo, "clear", None)
        add_items = getattr(combo, "addItems", None)
        if callable(clear) and callable(add_items):
            clear()
            add_items(tuple(labels))
            setter(target)
            self._field_order = self._field_order_from_controls()
            self._on_any_control_changed()

    def _load_field_visibility_controls(self, appearance: SignatureAppearance) -> None:
        for field_key, binding in appearance.iter_field_bindings():
            _set_checked(
                self._field_visibility_checks[field_key],
                binding.show_in_visible_appearance,
            )

    def _build_field_binding(self, field_key: SignatureFieldKey) -> SignatureFieldBinding:
        visible = _is_checked(self._field_visibility_checks[field_key])
        if visible:
            return _standard_field_binding()
        return SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
            override_text=None,
        )

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
        field_names = "on" if _is_checked(self._visible_text_controls.show_field_names) else "off"
        visible_count = sum(
            1 for check_box in self._field_visibility_checks.values() if _is_checked(check_box)
        )
        summary = (
            f"Showing {visible_count} of {len(SIGNATURE_FIELD_DISPLAY_ORDER)} standard "
            f"signing fields with labels {field_names}."
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

    def _on_placement_changed(self, *_args: object) -> None:
        if self._suspend_updates:
            return
        self._placement_enabled = True
        if self._on_change is not None:
            self._on_change()
        if self._on_page_change is not None:
            self._on_page_change(int(_spin_value(self._placement_controls.page_spin)))
