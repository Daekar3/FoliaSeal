"""Qt signing shell for the Phase 3 visible-signature workflow."""

from __future__ import annotations

import importlib
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import (
    SignaturePlacementContext,
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
)
from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.phase3_signing_backend import (
    _single_line_horizontal_stamp_vertical_inset,
    _single_line_stamp_content_inset,
    _single_line_vertical_stamp_border_gap,
)
from foliaseal.application.signature_font_registry import (
    bundled_font_root,
    resolve_signature_font_face,
    validate_signature_font_request,
)
from foliaseal.application.signing_preview_renderer import (
    CanonicalSignaturePreviewSnapshot,
    render_canonical_signature_preview,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.application.visible_signature_layout import (
    ImageMetrics,
    LayoutRequest,
    SignatureLayoutPlan,
    VisibleSignatureLayoutEngine,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningRequest,
    SigningResult,
)
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import ResolvedSignaturePreset, SignaturePresetCatalog
from foliaseal.infra.render import QtPdfRenderBackend
from foliaseal.presentation.qt.viewer_widget import build_qt_pdf_viewer_widget

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

PROFILE_PLACEHOLDER = "Current draft"
_PREVIEW_FONTS_REGISTERED = False


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
    q_message_box: type[Any]
    q_pixmap: type[Any]
    q_double_spin_box: type[Any]
    q_spin_box: type[Any]
    q_push_button: type[Any]
    qt: Any


@dataclass(frozen=True)
class FieldControls:
    """Controls used to edit one visible signature field."""

    container: Any
    source_combo: Any
    override_edit: Any


@dataclass(frozen=True)
class ProfileControls:
    """Controls used to manage named appearance profiles."""

    container: Any
    profile_combo: Any
    profile_name: Any
    save_button: Any
    delete_button: Any


class SigningRequestExecutor(Protocol):
    """Executes a validated signing request and returns a signing result."""

    def execute(self, request: SigningRequest) -> SigningResult:
        """Apply the signing request and return the result."""


@dataclass(frozen=True)
class PlacementControls:
    """Controls used to edit placement and page selection."""

    container: Any
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
class PreviewControls:
    """Widgets used to present the visible-signature preview."""

    container: Any
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


def _set_widget_width_limit(widget: Any, width: int) -> None:
    fixed_width = getattr(widget, "setFixedWidth", None)
    if callable(fixed_width):
        fixed_width(width)
        return
    max_width = getattr(widget, "setMaximumWidth", None)
    if callable(max_width):
        max_width(width)


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


def _load_stamp_pixmap(
    bindings: QtSigningWidgetBindings,
    path: str,
    *,
    max_width: int | None = None,
    max_height: int | None = None,
) -> Any | None:
    if not path:
        return None
    pixmap = bindings.q_pixmap(path)
    is_null = getattr(pixmap, "isNull", None)
    if callable(is_null) and is_null():
        return None
    scaled = getattr(pixmap, "scaled", None)
    if callable(scaled):
        keep_aspect = getattr(bindings.qt, "KeepAspectRatio", None)
        smooth = getattr(bindings.qt, "SmoothTransformation", None)
        if keep_aspect is not None and smooth is not None:
            candidate = scaled(
                max_width or 148,
                max_height or 92,
                keep_aspect,
                smooth,
            )
            is_candidate_null = getattr(candidate, "isNull", None)
            if not callable(is_candidate_null) or not is_candidate_null():
                return candidate
    return pixmap


_PREVIEW_MAX_WIDTH_PX = 520
_PREVIEW_MAX_HEIGHT_PX = 180
_PREVIEW_DEFAULT_WIDTH_PX = 320
_PREVIEW_DEFAULT_HEIGHT_PX = 120
_PREVIEW_SCREEN_PX_PER_PT = 96.0 / 72.0
_PREVIEW_HORIZONTAL_PADDING_PX = 24
_PREVIEW_GROUP_OVERHEAD_PX = 28
_PREVIEW_CARD_CONTENT_INSET_PX = 4


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


def _preview_available_width(preview: SigningDraftPreview, container: Any | None = None) -> int:
    container_width = _ancestor_width(container) if container is not None else None
    if isinstance(container_width, int) and container_width > 0:
        return max(
            _PREVIEW_DEFAULT_WIDTH_PX,
            container_width
            - _PREVIEW_HORIZONTAL_PADDING_PX
            - _PREVIEW_GROUP_OVERHEAD_PX,
        )
    if preview.signature_rect is None:
        return _PREVIEW_DEFAULT_WIDTH_PX
    return _PREVIEW_MAX_WIDTH_PX


def _preview_body_size(
    preview: SigningDraftPreview,
    *,
    available_width_px: int | None = None,
) -> tuple[int, int]:
    if preview.signature_rect is None:
        max_width_px = min(
            available_width_px or _PREVIEW_MAX_WIDTH_PX,
            int(
                round(
                    _PREVIEW_MAX_HEIGHT_PX
                    * (_PREVIEW_DEFAULT_WIDTH_PX / _PREVIEW_DEFAULT_HEIGHT_PX)
                )
            ),
        )
        width = max(_PREVIEW_DEFAULT_WIDTH_PX, max_width_px)
        height = max(
            1,
            int(round(width * (_PREVIEW_DEFAULT_HEIGHT_PX / _PREVIEW_DEFAULT_WIDTH_PX))),
        )
        return (width, min(height, _PREVIEW_MAX_HEIGHT_PX))

    width_pt = max(1.0, preview.signature_rect.width_pt)
    height_pt = max(1.0, preview.signature_rect.height_pt)
    max_width_px = available_width_px or _PREVIEW_MAX_WIDTH_PX
    # Keep the preview card tied to a physical PDF-to-screen scale instead of
    # stretching it to fill the pane. Otherwise narrow rectangles look much
    # roomier than the same text can ever be in the signed PDF.
    scale = min(
        _PREVIEW_SCREEN_PX_PER_PT,
        max_width_px / width_pt,
        _PREVIEW_MAX_HEIGHT_PX / height_pt,
    )
    width = max(1, int(round(width_pt * scale)))
    height = max(1, int(round(height_pt * scale)))
    return (width, height)


def _preview_display_scale(
    preview: SigningDraftPreview,
    *,
    available_width_px: int | None = None,
) -> float:
    if preview.signature_rect is None:
        return 1.0
    body_width, _body_height = _preview_body_size(
        preview,
        available_width_px=available_width_px,
    )
    width_pt = max(1.0, preview.signature_rect.width_pt)
    return body_width / width_pt


def _preview_text_width_limit(
    preview: SigningDraftPreview,
    *,
    title_line: str | None = None,
    detail_text: str | None = None,
    stamp_text: str | None = None,
    available_width_px: int | None = None,
    stamp_aspect_ratio: float | None = None,
) -> int:
    body_width, _body_height = _preview_body_size(
        preview,
        available_width_px=available_width_px,
    )
    if (
        preview.signature_rect is None
        or preview.text_style is None
        or preview.layout_template is None
        or preview.stamp_position is None
    ):
        return body_width

    if stamp_text is None:
        if title_line and detail_text:
            stamp_text = f"{title_line}\n{detail_text}"
        elif title_line:
            stamp_text = title_line
        elif detail_text:
            stamp_text = detail_text
    geometry = _preview_layout_geometry(
        preview,
        stamp_text=stamp_text,
        stamp_aspect_ratio=stamp_aspect_ratio,
    )
    if geometry is None:
        return body_width
    text_width_pt = max(1, geometry.text_area_width_pt)
    return max(
        1,
        int(
            round(
                text_width_pt
                * _preview_display_scale(preview, available_width_px=available_width_px)
            )
        ),
    )


def _preview_border_safe_inset_pt(box_style: SignatureBoxStyle | None) -> float:
    if box_style is None or not box_style.show_border:
        return 0.0
    return float(max(0, int(ceil(box_style.border_width_pt / 2.0)) + 1))


def _preview_card_padding_pt(preview: SigningDraftPreview) -> float:
    if preview.signature_rect is None:
        return 6.0
    shortest_edge_pt = max(
        1.0,
        min(preview.signature_rect.width_pt, preview.signature_rect.height_pt),
    )
    geometry_padding = max(2.0, min(4.0, shortest_edge_pt * 0.12))
    return max(geometry_padding, _preview_border_safe_inset_pt(preview.box_style))


def _preview_stamp_content_gutter_pt(preview: SigningDraftPreview) -> float:
    if preview.signature_rect is None:
        return 0.0
    return 0.0


def _raw_pixmap_aspect_ratio(raw_pixmap: Any | None) -> float | None:
    if raw_pixmap is None:
        return None
    pixmap_width = getattr(raw_pixmap, "width", None)
    pixmap_height = getattr(raw_pixmap, "height", None)
    if callable(pixmap_width):
        pixmap_width = pixmap_width()
    if callable(pixmap_height):
        pixmap_height = pixmap_height()
    if (
        not isinstance(pixmap_width, int)
        or not isinstance(pixmap_height, int)
        or pixmap_width <= 0
        or pixmap_height <= 0
    ):
        return None
    return pixmap_width / pixmap_height


@dataclass(frozen=True)
class _PreviewStampImageProbe:
    stamp_aspect_ratio: float | None

    def inspect(self, image_stamp_path: str | None) -> ImageMetrics | None:
        if image_stamp_path is None:
            return None
        aspect_ratio = self.stamp_aspect_ratio if self.stamp_aspect_ratio else 1.0
        if aspect_ratio <= 0:
            aspect_ratio = 1.0
        return ImageMetrics(
            width_px=max(1, int(round(aspect_ratio * 1000))),
            height_px=1000,
            aspect_ratio=aspect_ratio,
        )


@dataclass(frozen=True)
class _QtPreviewLayoutGeometry:
    text_area_width_pt: int
    text_area_height_pt: int
    stamp_area_width_pt: int
    stamp_area_height_pt: int

    @classmethod
    def from_plan(cls, plan: SignatureLayoutPlan) -> _QtPreviewLayoutGeometry:
        return cls(
            text_area_width_pt=plan.text_area_width_pt,
            text_area_height_pt=plan.text_area_height_pt,
            stamp_area_width_pt=plan.stamp_area_width_pt,
            stamp_area_height_pt=plan.stamp_area_height_pt,
        )


def _preview_stamp_max_size(
    preview: SigningDraftPreview,
    *,
    title_line: str | None = None,
    detail_text: str | None = None,
    stamp_text: str | None = None,
    raw_pixmap: Any,
    available_width_px: int | None = None,
    stamp_aspect_ratio: float | None = None,
) -> tuple[int, int]:
    if (
        preview.signature_rect is None
        or preview.text_style is None
        or preview.layout_template is None
        or preview.stamp_position is None
    ):
        return (148, 92)

    if stamp_text is None:
        if title_line and detail_text:
            stamp_text = f"{title_line}\n{detail_text}"
        elif title_line:
            stamp_text = title_line
        elif detail_text:
            stamp_text = detail_text
    geometry = _preview_layout_geometry(
        preview,
        stamp_text=stamp_text,
        stamp_aspect_ratio=stamp_aspect_ratio,
    )
    if geometry is None:
        return (148, 92)
    area_width = max(1, geometry.stamp_area_width_pt)
    area_height = max(1, geometry.stamp_area_height_pt)
    content_inset = 0
    if preview.layout_template == SignatureLayoutTemplate.SINGLE_LINE:
        content_inset = _single_line_stamp_content_inset(
            stamp_position=preview.stamp_position,
            box_width=max(1, int(round(preview.signature_rect.width_pt))),
            box_height=max(1, int(round(preview.signature_rect.height_pt))),
            reserved_width=area_width,
            reserved_height=area_height,
        )
    vertical_inset = content_inset
    if (
        preview.layout_template == SignatureLayoutTemplate.SINGLE_LINE
        and preview.stamp_position
        in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        vertical_inset = _single_line_horizontal_stamp_vertical_inset(
            box_style=preview.box_style,
            content_inset=content_inset,
        )
    area_width = max(1, area_width - content_inset * 2)
    area_height = max(1, area_height - vertical_inset * 2)

    pixmap_width = getattr(raw_pixmap, "width", None)
    pixmap_height = getattr(raw_pixmap, "height", None)
    if callable(pixmap_width):
        pixmap_width = pixmap_width()
    if callable(pixmap_height):
        pixmap_height = pixmap_height()
    if (
        not isinstance(pixmap_width, int)
        or not isinstance(pixmap_height, int)
        or pixmap_height <= 0
    ):
        return (148, 92)

    aspect_ratio = pixmap_width / pixmap_height
    target_width = area_width
    target_height = max(1, int(round(target_width / aspect_ratio)))
    if target_height > area_height:
        target_height = area_height
        target_width = max(1, int(round(target_height * aspect_ratio)))

    preview_scale = _preview_display_scale(
        preview,
        available_width_px=available_width_px,
    )
    scaled_width = max(1, int(round(target_width * preview_scale)))
    scaled_height = max(1, int(round(target_height * preview_scale)))
    return (scaled_width, scaled_height)


def _preview_vertical_band_geometry(
    preview: SigningDraftPreview,
    *,
    title_line: str | None = None,
    detail_text: str | None = None,
    stamp_text: str | None = None,
    inner_body_height_px: int,
    available_width_px: int | None = None,
    stamp_aspect_ratio: float | None = None,
) -> tuple[int, int, int] | None:
    if (
        preview.signature_rect is None
        or preview.text_style is None
        or preview.stamp_position not in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}
    ):
        return None

    if stamp_text is None:
        if title_line and detail_text:
            stamp_text = f"{title_line}\n{detail_text}"
        elif title_line:
            stamp_text = title_line
        elif detail_text:
            stamp_text = detail_text
    geometry = _preview_layout_geometry(
        preview,
        stamp_text=stamp_text,
        stamp_aspect_ratio=stamp_aspect_ratio,
    )
    if geometry is None:
        return None
    preview_scale = _preview_display_scale(
        preview,
        available_width_px=available_width_px,
    )
    text_height = max(1, int(round(geometry.text_area_height_pt * preview_scale)))
    stamp_height = max(1, int(round(geometry.stamp_area_height_pt * preview_scale)))
    separator_height = max(0, inner_body_height_px - text_height - stamp_height)
    return (text_height, stamp_height, separator_height)


def _preview_layout_geometry(
    preview: SigningDraftPreview,
    *,
    detail_text: str | None = None,
    stamp_text: str | None = None,
    stamp_aspect_ratio: float | None = None,
) -> _QtPreviewLayoutGeometry | None:
    plan = _preview_layout_plan(
        preview,
        detail_text=detail_text,
        stamp_text=stamp_text,
        stamp_aspect_ratio=stamp_aspect_ratio,
    )
    if plan is None:
        return None
    return _QtPreviewLayoutGeometry.from_plan(plan)


def _preview_layout_plan(
    preview: SigningDraftPreview,
    *,
    detail_text: str | None = None,
    stamp_text: str | None = None,
    stamp_aspect_ratio: float | None = None,
) -> SignatureLayoutPlan | None:
    if (
        preview.signature_rect is None
        or preview.text_style is None
        or preview.layout_template is None
        or preview.stamp_position is None
    ):
        return None

    if stamp_text is None and detail_text is not None:
        stamp_text = detail_text
    stamp_text = (stamp_text or _preview_stamp_text(preview)).strip() or " "
    return VisibleSignatureLayoutEngine(
        image_probe=_PreviewStampImageProbe(stamp_aspect_ratio),
    ).plan(
        LayoutRequest(
            signature_rect=preview.signature_rect,
            layout_template=preview.layout_template,
            stamp_position=preview.stamp_position,
            text_style=preview.text_style,
            box_style=preview.box_style,
            stamp_text=stamp_text,
            image_stamp_path=preview.image_stamp_path,
            use_horizontal_ink_reservation=False,
        )
    )


def _size_hint_height(widget: Any) -> int | None:
    size_hint = getattr(widget, "sizeHint", None)
    if not callable(size_hint):
        return None
    hint = size_hint()
    height = getattr(hint, "height", None)
    if callable(height):
        return int(height())
    return None


def _qt_alignment_flag(qt_namespace: Any, name: str) -> Any | None:
    direct = getattr(qt_namespace, name, None)
    if direct is not None:
        return direct
    alignment_flag = getattr(qt_namespace, "AlignmentFlag", None)
    if alignment_flag is None:
        return None
    return getattr(alignment_flag, name, None)


def _reset_widget_size_constraints(widget: Any) -> None:
    """Clear prior fixed-size constraints before recomputing preview geometry."""

    maximum_extent = 16_777_215
    for method_name, value in (
        ("setMinimumWidth", 0),
        ("setMaximumWidth", maximum_extent),
        ("setMinimumHeight", 0),
        ("setMaximumHeight", maximum_extent),
    ):
        setter = getattr(widget, method_name, None)
        if callable(setter):
            setter(value)

    # Test doubles track fixed geometry via attributes rather than Qt setters.
    for attribute in ("fixed_size", "fixed_width", "maximum_width", "minimum_width"):
        if hasattr(widget, attribute):
            setattr(widget, attribute, None)


def _fit_vertical_preview_band_geometry(
    *,
    text_height: int,
    stamp_height: int,
    separator_height: int,
    inner_body_height_px: int,
    detail_hint_height_px: int,
    rendered_line_count: int,
    stamp_visible: bool,
) -> tuple[int, int, int]:
    if inner_body_height_px <= 0:
        return (0, 0, 0)

    # Do not invent extra stamp-band height in the preview. If stacked text
    # needs to claim more of the body, the preview should reflect the actual
    # reservation pressure instead of preserving an arbitrary visible minimum.
    minimum_stamp_height = 0

    # Keep the total preview card geometry fixed, but let the rendered text claim
    # the height it actually needs by borrowing from separator space first and
    # then from the stamp band down to the true reservation floor.
    descender_budget_px = _vertical_preview_descender_budget_px(rendered_line_count)
    target_text_height = max(
        text_height,
        detail_hint_height_px + descender_budget_px,
    )
    max_text_height = max(0, inner_body_height_px - minimum_stamp_height)
    fitted_text_height = min(target_text_height, max_text_height)

    remaining_height = max(0, inner_body_height_px - fitted_text_height)
    fitted_separator_height = min(
        separator_height,
        max(0, remaining_height - minimum_stamp_height),
    )
    fitted_stamp_height = max(0, remaining_height - fitted_separator_height)
    return (fitted_text_height, fitted_stamp_height, fitted_separator_height)


def _vertical_preview_descender_budget_px(rendered_line_count: int) -> int:
    """Reserve a tiny per-line descender budget for stacked preview text.

    Qt's rendered glyph bounds in the compact stacked preview paths are
    consistently a few pixels taller than the raw size hint alone suggests,
    especially once descenders on the last visible line are rasterized. This is
    part of the preview's line-box contract, not a fit-acceptance tolerance.
    """

    line_count = max(1, rendered_line_count)
    return min(4, 1 + line_count)


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


def _format_appearance_summary(appearance: SignatureAppearance) -> str:
    visible_fields = [
        _field_label(field_key)
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


def _hex_to_css_color(value: str, *, fallback: str) -> str:
    candidate = value.strip()
    if len(candidate) == 7 and candidate.startswith("#"):
        return candidate
    return fallback


def _preview_detail_text(preview: SigningDraftPreview) -> str:
    return preview.detail_text or "No visible fields selected"


def _preview_stamp_text(preview: SigningDraftPreview) -> str:
    if preview.stamp_text:
        return preview.stamp_text
    title_text = (preview.signer_label_prefix or preview.title or "").strip()
    detail_text = (preview.detail_text or "").strip()
    if title_text and detail_text:
        return f"{title_text}\n{detail_text}"
    if title_text:
        return title_text
    if detail_text:
        return detail_text
    return "No visible fields selected"


def _preview_box_styles(preview: SigningDraftPreview) -> tuple[str, str]:
    if preview.box_style is None:
        return "", ""
    border_color = _hex_to_css_color(preview.box_style.border_color_hex, fallback="#4a4a4a")
    background = _hex_to_css_color(preview.box_style.background_color_hex, fallback="#ffffff")
    border_width = max(preview.box_style.border_width_pt, 0.5)
    border = (
        f"border: {border_width:.1f}px solid {border_color};"
        if preview.box_style.show_border
        else "border: 1px solid transparent;"
    )
    return border, background


def _preview_card_padding_px(preview: SigningDraftPreview) -> float:
    if preview.signature_rect is None:
        return 6.0
    return _preview_card_padding_pt(preview)


def _preview_inner_body_extent(total_extent_px: int, padding_px: float) -> int:
    return max(1, total_extent_px - int(ceil(padding_px * 2)))


def _preview_text_style(preview: SigningDraftPreview) -> str:
    if preview.text_style is None:
        return "color: #1f1f1f;"
    family = _preview_font_family_css(preview.text_style)
    size = preview.text_style.font_size_pt
    weight = "700" if preview.text_style.bold else "500"
    style = "italic" if preview.text_style.italic else "normal"
    color = _hex_to_css_color(preview.text_style.text_color_hex, fallback="#1f1f1f")
    return (
        f"font-family: {family}; "
        f"font-size: {size:.1f}pt; "
        f"font-weight: {weight}; "
        f"font-style: {style}; "
        f"color: {color};"
    )


def _preview_font_stack(font_family: str) -> str:
    try:
        face = resolve_signature_font_face(font_family, bold=False, italic=False)
        return _quoted_preview_family(face.preview_family_name, font_family)
    except ValueError:
        return "'Noto Sans', sans-serif"


def _preview_font_family_css(text_style: SignatureTextStyle) -> str:
    try:
        face = resolve_signature_font_face(
            text_style.font_family,
            bold=text_style.bold,
            italic=text_style.italic,
        )
    except ValueError:
        face = resolve_signature_font_face(text_style.font_family, bold=False, italic=False)
    return _quoted_preview_family(face.preview_family_name, text_style.font_family)


def _quoted_preview_family(preview_family_name: str, requested_family: str) -> str:
    normalized = requested_family.strip().lower()
    if "mono" in normalized or "courier" in normalized or "code" in normalized:
        return f"'{preview_family_name}', monospace"
    if "serif" in normalized or "times" in normalized or "display" in normalized:
        return f"'{preview_family_name}', serif"
    if "cursive" in normalized or "script" in normalized:
        return f"'{preview_family_name}', cursive"
    if "fantasy" in normalized or "decor" in normalized:
        return f"'{preview_family_name}', fantasy"
    return f"'{preview_family_name}', sans-serif"


def _ensure_preview_fonts_registered() -> None:
    global _PREVIEW_FONTS_REGISTERED
    if _PREVIEW_FONTS_REGISTERED:
        return
    try:
        qt_widgets = importlib.import_module("PySide6.QtWidgets")
        qt_gui = importlib.import_module("PySide6.QtGui")
    except Exception:
        return
    q_application = getattr(qt_widgets, "QApplication", None)
    instance = getattr(q_application, "instance", None)
    if not callable(instance) or instance() is None:
        return
    q_font_database = getattr(qt_gui, "QFontDatabase", None)
    add_application_font = getattr(q_font_database, "addApplicationFont", None)
    if not callable(add_application_font):
        return
    _PREVIEW_FONTS_REGISTERED = True
    for font_path in sorted(bundled_font_root().glob("*.ttf")):
        add_application_font(str(font_path))


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


def _panel_available_width(widget: Any) -> int:
    panel_width = _ancestor_width(widget) or _widget_width(widget)
    if isinstance(panel_width, int) and panel_width > 0:
        return max(1, panel_width - 16)
    return _PREVIEW_MAX_WIDTH_PX


class SignaturePropertiesPanel:
    """Signature editing controls and preview/validation summary."""

    def __init__(
        self,
        *,
        bindings: QtSigningWidgetBindings,
        workflow: SigningDraftWorkflow,
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        on_change: Callable[[], None] | None = None,
        on_page_change: Callable[[int], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        _ensure_preview_fonts_registered()
        self._workflow = workflow
        self._profile_catalog_store = preset_catalog_store
        if preset_catalog is not None:
            self._profile_catalog = preset_catalog
        elif preset_catalog_store is not None:
            self._profile_catalog = preset_catalog_store.load_catalog()
        else:
            self._profile_catalog = SignaturePresetCatalog(
                schema_version=1,
            )
        self._selected_profile_name: str | None = None
        self._on_change = on_change
        self._on_page_change = on_page_change
        self._on_error = on_error
        self._suspend_updates = False
        self._placement_initialized = workflow.signature_rect is not None
        self._control_issue: SigningDraftValidationIssue | None = None
        self._canonical_preview_render_backend = QtPdfRenderBackend()
        self.widget = bindings.q_widget()
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)

        self._profile_controls = self._build_profile_controls()
        self._placement_controls = self._build_placement_controls()
        self._appearance_controls = self._build_appearance_controls()
        self.field_controls = self._build_field_controls()
        self._preview_controls = self._build_preview_controls()
        self.preview_controls = self._preview_controls
        self._validation_label = bindings.q_label("")
        if hasattr(self._validation_label, "setWordWrap"):
            self._validation_label.setWordWrap(True)

        self._layout.addWidget(self._profile_controls.container)
        self._layout.addWidget(self._appearance_controls.container)
        self._layout.addWidget(self._heading("Visible Fields"))
        self._layout.addWidget(self._appearance_controls.show_field_names)
        for controls in self.field_controls.values():
            self._layout.addWidget(controls.container)
        self._layout.addWidget(self._heading("Placement"))
        self._layout.addWidget(self._placement_controls.container)
        self._layout.addWidget(self._heading("Preview"))
        self._layout.addWidget(self._preview_controls.container)
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
        return self._workflow.preview()

    def is_ready_to_sign(self) -> bool:
        preview = self._workflow.preview()
        if not preview.can_submit:
            return False
        if self._control_issue is None:
            return True
        return self._control_issue.severity != SigningDraftValidationSeverity.ERROR

    def validation_text(self) -> str:
        text = _text(self._validation_label)
        return text

    def preview_text(self) -> str:
        preview = self._workflow.preview()
        return _preview_stamp_text(preview).strip()

    def refresh_preview(self) -> SigningDraftPreview:
        preview = self._workflow.preview()
        self._update_preview_controls(preview)
        _set_widget_width_limit(
            self._validation_label,
            _panel_available_width(self.widget),
        )
        self._validation_label.setText(self._format_validation_text(preview))
        return preview

    def load_from_workflow(self) -> None:
        self._suspend_updates = True
        try:
            self._load_profile_controls()
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

    def _build_preview_controls(self) -> PreviewControls:
        bindings = self._bindings
        container = bindings.q_group_box("")
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
        layout.addWidget(card_container)

        return PreviewControls(
            container=container,
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
        self._selected_profile_name = None
        self.load_from_workflow()
        self._notify_change()

    def save_current_profile(self) -> ResolvedSignaturePreset | None:
        name = _text(self._profile_controls.profile_name).strip()
        if not name:
            self._show_profile_error("Profile name is required before saving.")
            return None

        try:
            preset = self._workflow.capture_signature_preset(name)
        except ValueError as exc:
            self._show_profile_error(str(exc))
            return None
        try:
            existing = self._profile_catalog.profile_named(name)
        except KeyError:
            existing = None

        if existing is not None:
            message_box = self._bindings.q_message_box
            yes_value = getattr(message_box, "Yes", None)
            if yes_value is None:
                standard_button = getattr(message_box, "StandardButton", None)
                yes_value = getattr(standard_button, "Yes", None)
            result = message_box.question(
                self.widget,
                "Overwrite profile?",
                f"Profile '{name}' already exists. Overwrite it?",
            )
            if result != yes_value:
                return None

        self._profile_catalog = self._profile_catalog.upsert_profile(preset)
        if self._profile_catalog_store is not None:
            self._profile_catalog_store.save_profile(preset)
        self._selected_profile_name = preset.name
        self._suspend_updates = True
        try:
            self._reload_profile_controls(selected_name=preset.name)
        finally:
            self._suspend_updates = False
        self.load_from_workflow()
        self._notify_change()
        return preset

    def delete_current_profile(self) -> SignaturePresetCatalog | None:
        selected_name = _combo_text(self._profile_controls.profile_combo)
        if selected_name == PROFILE_PLACEHOLDER or not selected_name.strip():
            self._show_profile_error("Select a saved profile before deleting it.")
            return None

        try:
            self._profile_catalog.profile_named(selected_name)
        except KeyError:
            self._show_profile_error(f"Profile '{selected_name}' is not available.")
            return None

        message_box = self._bindings.q_message_box
        yes_value = getattr(message_box, "Yes", None)
        if yes_value is None:
            standard_button = getattr(message_box, "StandardButton", None)
            yes_value = getattr(standard_button, "Yes", None)
        result = message_box.question(
            self.widget,
            "Delete profile?",
            f"Delete profile '{selected_name}'?",
        )
        if result != yes_value:
            return None

        updated_catalog = self._profile_catalog.remove_profile(selected_name)
        self._profile_catalog = updated_catalog
        if self._profile_catalog_store is not None:
            self._profile_catalog_store.delete_profile(selected_name)
        self._selected_profile_name = None
        self._suspend_updates = True
        try:
            self._reload_profile_controls(selected_name=None)
        finally:
            self._suspend_updates = False
        self._notify_change()
        return updated_catalog

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
        layout.addRow("Position", _compose_row(bindings, left_spin, bottom_spin))
        layout.addRow("Size", _compose_row(bindings, width_spin, height_spin))

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

    def _build_profile_controls(self) -> ProfileControls:
        bindings = self._bindings
        container = bindings.q_group_box("Named profiles")
        layout = bindings.q_form_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        profile_combo = bindings.q_combo_box()
        profile_name = bindings.q_line_edit()
        profile_name.setPlaceholderText("Enter a profile name")
        save_button = bindings.q_push_button("Save profile")
        delete_button = bindings.q_push_button("Delete profile")

        layout.addRow("Saved profile", profile_combo)
        layout.addRow("Profile name", profile_name)
        layout.addRow("", _compose_row(bindings, save_button, delete_button))

        profile_combo.currentTextChanged.connect(  # type: ignore[attr-defined]
            lambda _text: self._on_profile_selected()
        )
        index_changed = getattr(profile_combo, "currentIndexChanged", None)
        if hasattr(index_changed, "connect"):
            index_changed.connect(  # type: ignore[attr-defined]
                lambda _index: self._on_profile_selected()
            )
        save_button.clicked.connect(self.save_current_profile)  # type: ignore[attr-defined]
        delete_button.clicked.connect(self.delete_current_profile)  # type: ignore[attr-defined]

        return ProfileControls(
            container=container,
            profile_combo=profile_combo,
            profile_name=profile_name,
            save_button=save_button,
            delete_button=delete_button,
        )

    def _build_appearance_controls(self) -> Any:
        bindings = self._bindings
        container = bindings.q_group_box("Appearance")
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        text_group = bindings.q_group_box("Text and layout")
        text_layout = bindings.q_form_layout(text_group)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        box_group = bindings.q_group_box("Box and stamp")
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

        return type(
            "AppearanceControls",
            (),
            {
                "container": container,
                "signer_label_prefix": signer_label_prefix,
                "layout_template": layout_template,
                "stamp_position": stamp_position,
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
                "show_field_names": show_field_names,
            },
        )()

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

    def _load_placement_controls(self) -> None:
        rect = self._workflow.signature_rect
        if rect is None:
            _set_spin_value(self._placement_controls.page_spin, 1)
            _set_spin_value(self._placement_controls.left_spin, 24.0)
            _set_spin_value(self._placement_controls.bottom_spin, 18.0)
            placement_defaults = self._workflow.signature_placement_defaults
            if placement_defaults is not None:
                _set_spin_value(self._placement_controls.width_spin, placement_defaults.width_pt)
                _set_spin_value(self._placement_controls.height_spin, placement_defaults.height_pt)
            else:
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
        self._sync_font_style_control_availability()

    def _reload_profile_controls(self, *, selected_name: str | None = None) -> None:
        profile_combo = self._profile_controls.profile_combo
        clear = getattr(profile_combo, "clear", None)
        if callable(clear):
            clear()
        elif hasattr(profile_combo, "_items"):
            profile_combo._items = []  # type: ignore[attr-defined]
            profile_combo._current = ""  # type: ignore[attr-defined]

        profile_combo.addItem(PROFILE_PLACEHOLDER)
        profile_combo.addItems(self._profile_catalog.profile_names())
        current_name = (
            selected_name if selected_name in self._profile_catalog.profile_names() else None
        )
        _set_combo_text(profile_combo, current_name or PROFILE_PLACEHOLDER)
        if current_name is None:
            if not _text(self._profile_controls.profile_name).strip():
                _set_text(self._profile_controls.profile_name, "")
        else:
            _set_text(self._profile_controls.profile_name, current_name)

    def _load_profile_controls(self) -> None:
        self._reload_profile_controls(selected_name=self._selected_profile_name)

    def _load_field_controls(self) -> None:
        appearance = self._workflow.signature_appearance or SignatureAppearance()
        for field_key, binding in appearance.iter_field_bindings():
            controls = self.field_controls[field_key]
            _set_combo_text(controls.source_combo, _enum_display_text(binding.source))
            _set_text(controls.override_edit, binding.override_text or "")
            self._sync_field_control_state(field_key)

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

    def _on_profile_selected(self) -> None:
        if self._suspend_updates:
            return
        selected_name = _combo_text(self._profile_controls.profile_combo)
        if selected_name == PROFILE_PLACEHOLDER or not selected_name.strip():
            self._selected_profile_name = None
            self._notify_change()
            return
        try:
            preset = self._profile_catalog.profile_named(selected_name)
        except KeyError:
            self._selected_profile_name = None
            self._notify_change()
            return

        self._selected_profile_name = preset.name
        self._workflow.apply_signature_preset(preset)
        self.load_from_workflow()
        self._notify_change()

    def _mark_profile_dirty(self) -> None:
        if self._selected_profile_name is None:
            return
        self._selected_profile_name = None
        self._suspend_updates = True
        try:
            self._reload_profile_controls(selected_name=None)
        finally:
            self._suspend_updates = False

    def _build_rect_from_controls(self) -> SignatureRect:
        return SignatureRect(
            page_index=int(_spin_value(self._placement_controls.page_spin) - 1),
            left_pt=_spin_value(self._placement_controls.left_spin),
            bottom_pt=_spin_value(self._placement_controls.bottom_spin),
            width_pt=_spin_value(self._placement_controls.width_spin),
            height_pt=_spin_value(self._placement_controls.height_spin),
        )

    def _update_preview_controls(self, preview: SigningDraftPreview) -> None:
        stamp_text = _preview_stamp_text(preview)
        stamp_position = preview.stamp_position or SignatureStampPosition.TOP
        is_vertical = stamp_position in (
            SignatureStampPosition.TOP,
            SignatureStampPosition.BOTTOM,
        )
        available_width_px = _preview_available_width(
            preview,
            container=self._preview_controls.container,
        )
        for widget in (
            self._preview_controls.detail_label,
            self._preview_controls.stamp_label,
            self._preview_controls.multi_detail_label,
            self._preview_controls.multi_stamp_label,
        ):
            _reset_widget_size_constraints(widget)
        card_width, card_height = _preview_body_size(
            preview,
            available_width_px=available_width_px,
        )
        body_width = card_width
        body_height = card_height
        raw_stamp_pixmap = None
        if preview.image_stamp_path:
            raw_pixmap = self._bindings.q_pixmap(preview.image_stamp_path)
            raw_is_null = getattr(raw_pixmap, "isNull", None)
            if not callable(raw_is_null) or not raw_is_null():
                raw_stamp_pixmap = raw_pixmap
        stamp_aspect_ratio = _raw_pixmap_aspect_ratio(raw_stamp_pixmap)
        preview_scale = _preview_display_scale(
            preview,
            available_width_px=available_width_px,
        )
        preview_geometry = _preview_layout_geometry(
            preview,
            stamp_text=stamp_text,
            stamp_aspect_ratio=stamp_aspect_ratio,
        )
        reserved_text_width_px = None
        if preview_geometry is not None:
            reserved_text_width_px = max(
                1,
                int(round(preview_geometry.text_area_width_pt * preview_scale)),
            )
        detail_width = (
            body_width
            if is_vertical
            else (
                reserved_text_width_px
                if reserved_text_width_px is not None
                else _preview_text_width_limit(
                    preview,
                    stamp_text=stamp_text,
                    available_width_px=available_width_px,
                    stamp_aspect_ratio=stamp_aspect_ratio,
                )
            )
        )
        if hasattr(self._preview_controls.card_container, "setFixedSize"):
            self._preview_controls.card_container.setFixedSize(card_width, card_height)
        elif hasattr(self._preview_controls.card_container, "setFixedWidth"):
            self._preview_controls.card_container.setFixedWidth(card_width)
        preview_padding_px = _preview_card_padding_px(preview)
        inner_body_width = _preview_inner_body_extent(body_width, preview_padding_px)
        reserved_text_height_px = None
        reserved_stamp_width_px = None
        reserved_stamp_height_px = None
        if preview_geometry is not None:
            reserved_text_height_px = max(
                1,
                int(round(preview_geometry.text_area_height_pt * preview_scale)),
            )
            reserved_stamp_width_px = max(
                1,
                int(round(preview_geometry.stamp_area_width_pt * preview_scale)),
            )
            reserved_stamp_height_px = max(
                1,
                int(round(preview_geometry.stamp_area_height_pt * preview_scale)),
            )
        for widget in (
            self._preview_controls.title_label,
            self._preview_controls.detail_label,
            self._preview_controls.footer_label,
        ):
            _set_widget_width_limit(widget, card_width)
        for widget in (
            self._preview_controls.multi_content_container,
            self._preview_controls.multi_detail_label,
        ):
            _set_widget_width_limit(widget, detail_width)
        border_css, background_color = _preview_box_styles(preview)
        text_css = _preview_text_style(preview)
        if hasattr(self._preview_controls.card_container, "setStyleSheet"):
            self._preview_controls.card_container.setStyleSheet(
                "QGroupBox {"
                f" {border_css}"
                " border-radius: 6px;"
                f" background: {background_color};"
                f" padding: {preview_padding_px:.1f}px;"
                "}"
            )
        if hasattr(self._preview_controls.title_label, "setStyleSheet"):
            self._preview_controls.title_label.setStyleSheet(
                "font-weight: 700; "
                f"{text_css}"
            )
        if hasattr(self._preview_controls.detail_label, "setStyleSheet"):
            self._preview_controls.detail_label.setStyleSheet(text_css)
        if hasattr(self._preview_controls.multi_detail_label, "setStyleSheet"):
            self._preview_controls.multi_detail_label.setStyleSheet(text_css)
        for label in (
            self._preview_controls.title_label,
            self._preview_controls.detail_label,
            self._preview_controls.multi_detail_label,
        ):
            set_word_wrap = getattr(label, "setWordWrap", None)
            if callable(set_word_wrap):
                set_word_wrap(False)
        self._preview_controls.title_label.setText("")
        _set_widget_visible(self._preview_controls.title_label, False)
        inner_body_height = _preview_inner_body_extent(body_height, preview_padding_px)
        if hasattr(self._preview_controls.single_body_container, "setFixedSize"):
            self._preview_controls.single_body_container.setFixedSize(
                inner_body_width,
                inner_body_height,
            )
        if hasattr(self._preview_controls.multi_body_container, "setFixedSize"):
            self._preview_controls.multi_body_container.setFixedSize(
                inner_body_width,
                inner_body_height,
            )
        if is_vertical:
            self._preview_controls.detail_label.setText(stamp_text)
            self._preview_controls.multi_detail_label.setText("")
        else:
            content_height = (
                reserved_text_height_px
                if (
                    preview.layout_template != SignatureLayoutTemplate.SINGLE_LINE
                    and reserved_text_height_px is not None
                )
                else inner_body_height
            )
            self._preview_controls.detail_label.setText("")
            self._preview_controls.multi_detail_label.setText(stamp_text)
            if hasattr(self._preview_controls.multi_content_container, "setFixedSize"):
                self._preview_controls.multi_content_container.setFixedSize(
                    detail_width,
                    content_height,
                )
            else:
                _set_widget_width_limit(
                    self._preview_controls.multi_content_container,
                    detail_width,
                )
            if hasattr(self._preview_controls.multi_detail_label, "setFixedSize"):
                self._preview_controls.multi_detail_label.setFixedSize(
                    detail_width,
                    content_height,
                )
            else:
                _set_widget_width_limit(
                    self._preview_controls.multi_detail_label,
                    detail_width,
                )
        self._preview_controls.footer_label.setText("")
        _set_widget_visible(self._preview_controls.single_body_container, is_vertical)
        _set_widget_visible(self._preview_controls.multi_body_container, not is_vertical)
        vertical_band_geometry = _preview_vertical_band_geometry(
            preview,
            stamp_text=stamp_text,
            inner_body_height_px=inner_body_height,
            available_width_px=available_width_px,
            stamp_aspect_ratio=stamp_aspect_ratio,
        )
        if is_vertical and vertical_band_geometry is not None:
            text_height, stamp_height, separator_height = vertical_band_geometry
            vertical_band_geometry = _fit_vertical_preview_band_geometry(
                text_height=text_height,
                stamp_height=stamp_height,
                separator_height=separator_height,
                inner_body_height_px=inner_body_height,
                detail_hint_height_px=(
                    _size_hint_height(self._preview_controls.detail_label) or text_height
                ),
                rendered_line_count=max(1, stamp_text.count("\n") + 1),
                stamp_visible=raw_stamp_pixmap is not None,
            )
        stamp_pixmap = None
        if raw_stamp_pixmap is not None:
            if is_vertical and vertical_band_geometry is not None:
                _text_height, stamp_height, _separator_height = vertical_band_geometry
                content_inset = _single_line_stamp_content_inset(
                    stamp_position=preview.stamp_position,
                    box_width=max(1, int(round(preview.signature_rect.width_pt))),
                    box_height=max(1, int(round(preview.signature_rect.height_pt))),
                    reserved_width=max(1, int(round(inner_body_width / preview_scale))),
                    reserved_height=max(1, int(round(stamp_height / preview_scale))),
                )
                inset_px = max(
                    0,
                    int(round(content_inset * preview_scale)),
                )
                border_gap_px = max(
                    0,
                    int(
                        round(
                            _single_line_vertical_stamp_border_gap(
                                box_style=preview.box_style
                            )
                            * preview_scale
                        )
                    ),
                )
                stamp_pixmap = _load_stamp_pixmap(
                    self._bindings,
                    preview.image_stamp_path,
                    max_width=max(1, inner_body_width - inset_px * 2),
                    max_height=max(1, stamp_height - inset_px * 2 - border_gap_px),
                )
            else:
                max_width, max_height = _preview_stamp_max_size(
                    preview,
                    stamp_text=stamp_text,
                    raw_pixmap=raw_stamp_pixmap,
                    available_width_px=available_width_px,
                    stamp_aspect_ratio=stamp_aspect_ratio,
                )
                stamp_pixmap = _load_stamp_pixmap(
                    self._bindings,
                    preview.image_stamp_path,
                    max_width=max_width,
                    max_height=max_height,
                )

        def _apply_stamp(label: Any, *, visible: bool) -> None:
            if visible and stamp_pixmap is not None and hasattr(label, "setPixmap"):
                label.setPixmap(stamp_pixmap)
                _set_widget_visible(label, True)
                if hasattr(label, "setText"):
                    label.setText("")
                if (
                    is_vertical
                    and vertical_band_geometry is not None
                    and hasattr(label, "setFixedSize")
                ):
                    _text_height, stamp_height, _separator_height = vertical_band_geometry
                    label.setFixedSize(inner_body_width, stamp_height)
                elif (
                    is_vertical
                    and reserved_stamp_height_px is not None
                    and hasattr(label, "setFixedSize")
                ):
                    label.setFixedSize(inner_body_width, reserved_stamp_height_px)
                elif (
                    not is_vertical
                    and preview.layout_template != SignatureLayoutTemplate.SINGLE_LINE
                    and reserved_stamp_width_px is not None
                    and reserved_stamp_height_px is not None
                    and hasattr(label, "setFixedSize")
                ):
                    label.setFixedSize(reserved_stamp_width_px, reserved_stamp_height_px)
                elif hasattr(label, "setFixedSize"):
                    size_width = getattr(stamp_pixmap, "width", None)
                    size_height = getattr(stamp_pixmap, "height", None)
                    if callable(size_width):
                        size_width = size_width()
                    if callable(size_height):
                        size_height = size_height()
                    if isinstance(size_width, int) and isinstance(size_height, int):
                        label.setFixedSize(size_width + 4, size_height + 4)
                return
            clear = getattr(label, "clear", None)
            if callable(clear):
                clear()
            elif hasattr(label, "setPixmap"):
                # Test doubles may not expose QLabel.clear().
                label.setPixmap("")
            _set_widget_visible(label, False)
            if hasattr(label, "setText"):
                label.setText("")
            if hasattr(label, "setFixedSize"):
                if is_vertical and vertical_band_geometry is not None:
                    _text_height, stamp_height, _separator_height = vertical_band_geometry
                    label.setFixedSize(inner_body_width, stamp_height)
                elif is_vertical and reserved_stamp_height_px is not None:
                    label.setFixedSize(inner_body_width, reserved_stamp_height_px)
                elif (
                    not is_vertical
                    and preview.layout_template != SignatureLayoutTemplate.SINGLE_LINE
                    and reserved_stamp_width_px is not None
                    and reserved_stamp_height_px is not None
                ):
                    label.setFixedSize(reserved_stamp_width_px, reserved_stamp_height_px)
                else:
                    label.setFixedSize(96, 64)

        align_left = _qt_alignment_flag(self._bindings.qt, "AlignLeft")
        align_center = _qt_alignment_flag(self._bindings.qt, "AlignCenter")
        align_top = _qt_alignment_flag(self._bindings.qt, "AlignTop")
        align_bottom = _qt_alignment_flag(self._bindings.qt, "AlignBottom")
        if is_vertical and align_left is not None:
            stamp_alignment = align_left
            if stamp_position == SignatureStampPosition.TOP and align_bottom is not None:
                stamp_alignment = align_left | align_bottom
            elif stamp_position == SignatureStampPosition.BOTTOM and align_top is not None:
                stamp_alignment = align_left | align_top
            if hasattr(self._preview_controls.stamp_label, "setAlignment"):
                self._preview_controls.stamp_label.setAlignment(stamp_alignment)
            if hasattr(self._preview_controls.detail_label, "setAlignment"):
                self._preview_controls.detail_label.setAlignment(align_left)
        elif (
            align_center is not None
            and hasattr(self._preview_controls.stamp_label, "setAlignment")
        ):
            self._preview_controls.stamp_label.setAlignment(align_center)

        if is_vertical:
            if vertical_band_geometry is not None:
                text_height, _stamp_height, separator_height = vertical_band_geometry
                if hasattr(self._preview_controls.detail_label, "setFixedSize"):
                    self._preview_controls.detail_label.setFixedSize(
                        inner_body_width,
                        text_height,
                    )
                layout = _container_layout(self._preview_controls.single_body_container)
                if layout is not None and hasattr(layout, "setSpacing"):
                    layout.setSpacing(separator_height)
            elif (
                reserved_text_height_px is not None
                and hasattr(self._preview_controls.detail_label, "setFixedSize")
            ):
                self._preview_controls.detail_label.setFixedSize(
                    inner_body_width,
                    reserved_text_height_px,
                )
            stamp_widget: Any = self._preview_controls.stamp_label
            detail_widget: Any = self._preview_controls.detail_label
            if align_left is not None:
                stamp_widget = (self._preview_controls.stamp_label, 0, align_left)
                detail_widget = (self._preview_controls.detail_label, 0, align_left)
            single_widgets: list[Any] = [stamp_widget, detail_widget]
            if stamp_position == SignatureStampPosition.BOTTOM:
                single_widgets = [detail_widget, stamp_widget]
            _set_container_widgets(
                self._preview_controls.single_body_container,
                *single_widgets,
            )
        else:
            stamp_alignment = (
                align_center
                if align_center is not None
                else _qt_alignment_flag(self._bindings.qt, "AlignLeft")
            )
            if hasattr(self._preview_controls.multi_stamp_label, "setAlignment"):
                self._preview_controls.multi_stamp_label.setAlignment(stamp_alignment)
            multi_content_widgets: list[Any] = []
            multi_content_widgets.append(self._preview_controls.multi_detail_label)
            _set_container_widgets(
                self._preview_controls.multi_content_container,
                *multi_content_widgets,
            )
            _set_container_widgets(
                self._preview_controls.multi_body_container,
                (self._preview_controls.multi_stamp_label, 0, stamp_alignment),
                (
                    self._preview_controls.multi_content_container,
                    0,
                    stamp_alignment,
                ),
            )
            if stamp_position == SignatureStampPosition.RIGHT:
                _set_container_widgets(
                    self._preview_controls.multi_body_container,
                    (
                        self._preview_controls.multi_content_container,
                        0,
                        stamp_alignment,
                    ),
                    (self._preview_controls.multi_stamp_label, 0, stamp_alignment),
                )

        _apply_stamp(
            self._preview_controls.stamp_label,
            visible=is_vertical and stamp_pixmap is not None,
        )
        _apply_stamp(
            self._preview_controls.multi_stamp_label,
            visible=not is_vertical and stamp_pixmap is not None,
        )
        self._apply_canonical_preview_render(
            preview=preview,
            preview_scale=preview_scale,
            inner_body_width=inner_body_width,
            inner_body_height=inner_body_height,
            is_vertical=is_vertical,
        )

    def _validation_issues(
        self,
        preview: SigningDraftPreview,
    ) -> tuple[SigningDraftValidationIssue, ...]:
        if self._control_issue is None:
            return preview.issues
        return preview.issues + (self._control_issue,)

    def _apply_canonical_preview_render(
        self,
        *,
        preview: SigningDraftPreview,
        preview_scale: float,
        inner_body_width: int,
        inner_body_height: int,
        is_vertical: bool,
    ) -> None:
        try:
            snapshot = render_canonical_signature_preview(
                preview,
                zoom=max(1.0, preview_scale),
                render_backend=self._canonical_preview_render_backend,
                include_border=True,
                flatten_to_white=False,
            )
        except ValueError:
            snapshot = None
        self._cleanup_canonical_preview_snapshot(
            getattr(self._preview_controls.card_container, "_canonical_preview_snapshot", None)
        )
        self._preview_controls.card_container._canonical_preview_snapshot = snapshot
        if snapshot is None:
            if hasattr(self._preview_controls.card_container, "setStyleSheet"):
                border_css, background_color = _preview_box_styles(preview)
                preview_padding_px = _preview_card_padding_px(preview)
                self._preview_controls.card_container.setStyleSheet(
                    "QGroupBox {"
                    f" {border_css}"
                    " border-radius: 6px;"
                    f" background: {background_color};"
                    f" padding: {preview_padding_px:.1f}px;"
                    "}"
                )
            _set_widget_visible(self._preview_controls.single_render_label, False)
            _set_widget_visible(self._preview_controls.multi_render_label, False)
            return

        if hasattr(self._preview_controls.card_container, "setStyleSheet"):
            self._preview_controls.card_container.setStyleSheet(
                "QGroupBox { border: none; background: transparent; padding: 0px; }"
            )

        render_label = (
            self._preview_controls.single_render_label
            if is_vertical
            else self._preview_controls.multi_render_label
        )
        render_body = (
            self._preview_controls.single_body_container
            if is_vertical
            else self._preview_controls.multi_body_container
        )
        pixmap = self._load_canonical_preview_pixmap(
            snapshot=snapshot,
            max_width=inner_body_width,
            max_height=inner_body_height,
        )
        if pixmap is not None and hasattr(render_label, "setPixmap"):
            render_label.setPixmap(pixmap)
        if hasattr(render_label, "setFixedSize"):
            pixmap_width = getattr(pixmap, "width", None)
            pixmap_height = getattr(pixmap, "height", None)
            if callable(pixmap_width):
                pixmap_width = pixmap_width()
            if callable(pixmap_height):
                pixmap_height = pixmap_height()
            if isinstance(pixmap_width, int) and isinstance(pixmap_height, int):
                render_label.setFixedSize(pixmap_width, pixmap_height)
                if hasattr(render_body, "setFixedSize"):
                    render_body.setFixedSize(pixmap_width, pixmap_height)
            else:
                render_label.setFixedSize(inner_body_width, inner_body_height)
                if hasattr(render_body, "setFixedSize"):
                    render_body.setFixedSize(inner_body_width, inner_body_height)

        _set_widget_visible(self._preview_controls.stamp_label, False)
        _set_widget_visible(self._preview_controls.multi_stamp_label, False)
        _set_widget_visible(self._preview_controls.detail_label, False)
        _set_widget_visible(self._preview_controls.multi_detail_label, False)
        _set_widget_visible(self._preview_controls.single_render_label, is_vertical)
        _set_widget_visible(self._preview_controls.multi_render_label, not is_vertical)
        if is_vertical:
            _set_container_widgets(
                self._preview_controls.single_body_container,
                self._preview_controls.single_render_label,
            )
        else:
            _set_container_widgets(
                self._preview_controls.multi_body_container,
                self._preview_controls.multi_render_label,
            )

    def _cleanup_canonical_preview_snapshot(
        self,
        snapshot: CanonicalSignaturePreviewSnapshot | None,
    ) -> None:
        if snapshot is None:
            return
        image_path = Path(snapshot.image_path)
        temp_dir = image_path.parent
        if not temp_dir.name.startswith("foliaseal-canonical-preview-"):
            return
        shutil.rmtree(temp_dir, ignore_errors=True)

    def _load_canonical_preview_pixmap(
        self,
        *,
        snapshot: CanonicalSignaturePreviewSnapshot,
        max_width: int,
        max_height: int,
    ) -> Any | None:
        pixmap = self._bindings.q_pixmap(snapshot.image_path)
        is_null = getattr(pixmap, "isNull", None)
        if callable(is_null) and is_null():
            return None
        scaled = getattr(pixmap, "scaled", None)
        if callable(scaled):
            keep_aspect = getattr(self._bindings.qt, "KeepAspectRatio", None)
            smooth = getattr(self._bindings.qt, "SmoothTransformation", None)
            if keep_aspect is not None and smooth is not None:
                return scaled(
                    max_width,
                    max_height,
                    keep_aspect,
                    smooth,
                )
        return pixmap

    def _format_validation_text(self, preview: SigningDraftPreview) -> str:
        issues = self._validation_issues(preview)
        blocking_issues = [
            issue
            for issue in issues
            if issue.severity == SigningDraftValidationSeverity.ERROR
        ]
        if (
            len(blocking_issues) == 1
            and self._control_issue is None
            and blocking_issues[0].code == "signature_rect_missing"
        ):
            return "Place a signature on the page to continue."
        if not blocking_issues:
            return "Ready to sign."
        if (
            len(blocking_issues) == 1
            and blocking_issues[0].code == "visible_signature_layout_unavailable"
        ):
            return f"Will fail to sign: {blocking_issues[0].message}"
        return "\n".join(
            f"{issue.severity.value.upper()} {issue.code}: {issue.message}"
            for issue in blocking_issues
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

    def _notify_change(self) -> None:
        self._sync_font_style_control_availability()
        if self._on_change is not None:
            self._on_change()

    def _emit_error(self, message: str) -> None:
        if self._on_error is not None:
            self._on_error(message)

    def _show_profile_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.widget, "Profile error", message)
            return
        self._emit_error(message)

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
        self._mark_profile_dirty()
        self.apply_changes()

    def _on_field_changed(self, field_key: SignatureFieldKey) -> None:
        if self._suspend_updates:
            return
        self._sync_field_control_state(field_key)
        self._mark_profile_dirty()
        self.apply_changes()

    def _on_field_source_changed(self, field_key: SignatureFieldKey) -> None:
        if self._suspend_updates:
            return
        self._sync_field_control_state(field_key)
        self._mark_profile_dirty()
        self.apply_changes()

    def _on_placement_changed(self, *_args: object) -> None:
        if self._suspend_updates:
            return
        self._placement_initialized = True
        self._mark_profile_dirty()
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
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._viewer_workflow = viewer_workflow
        self._draft_workflow = signing_workflow
        self._sign_executor = sign_executor
        self._on_sign_request = on_sign_request
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._last_signing_result: SigningResult | None = None
        self.widget = bindings.q_widget()
        self._layout = bindings.q_vbox_layout(self.widget)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(8)

        self._main_row = bindings.q_hbox_layout()
        self._main_row.setContentsMargins(0, 0, 0, 0)
        self._main_row.setSpacing(8)

        self._viewer_widget = build_qt_pdf_viewer_widget(
            workflow=viewer_workflow,
            on_selection=self._handle_viewer_selection,
            on_error=self._handle_viewer_error,
            on_interaction=self._handle_viewer_interaction,
        )
        self.properties_panel = SignaturePropertiesPanel(
            bindings=bindings,
            workflow=signing_workflow,
            preset_catalog=preset_catalog,
            preset_catalog_store=preset_catalog_store,
            on_change=self._handle_panel_change,
            on_page_change=self._handle_page_change,
            on_error=self._emit_error,
        )
        self._properties_scroll = bindings.q_scroll_area()
        scroll_setter = getattr(self._properties_scroll, "setWidgetResizable", None)
        if callable(scroll_setter):
            scroll_setter(True)
        widget_setter = getattr(self._properties_scroll, "setWidget", None)
        if callable(widget_setter):
            widget_setter(self.properties_panel.container)
        self._sign_button = bindings.q_push_button("Confirm and sign")
        self._sign_button.clicked.connect(self.submit_sign_request)  # type: ignore[attr-defined]
        self._result_label = bindings.q_label("")
        if hasattr(self._result_label, "setWordWrap"):
            self._result_label.setWordWrap(True)
        if hasattr(self._result_label, "setStyleSheet"):
            self._result_label.setStyleSheet("color: #444;")

        self._main_row.addWidget(self._viewer_widget, 3)
        self._main_row.addWidget(self._properties_scroll, 2)
        self._layout.addLayout(self._main_row)
        self._layout.addWidget(self._sign_button)
        self._layout.addWidget(self._result_label)

        self.widget.properties_panel = self.properties_panel  # type: ignore[attr-defined]
        self.widget.viewer_widget = self._viewer_widget  # type: ignore[attr-defined]
        self.widget.properties_scroll = self._properties_scroll  # type: ignore[attr-defined]
        self.widget.sign_result_label = self._result_label  # type: ignore[attr-defined]
        self.widget.last_signing_result = None  # type: ignore[attr-defined]
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
        self._sync_signature_overlay()
        self.properties_panel.refresh_preview()
        self._refresh_sign_button_state()

    def submit_sign_request(self) -> SigningRequest | None:
        self.properties_panel.apply_changes()
        if not self.properties_panel.is_ready_to_sign():
            self._last_signing_result = None
            self._set_sign_result_text("")
            self._emit_error(self.properties_panel.validation_text())
            return None
        request = self._draft_workflow.build_signing_request()
        if self._on_sign_request is not None:
            self._on_sign_request(request)
        if self._sign_executor is not None:
            try:
                result = self._sign_executor.execute(request)
            except Exception as exc:  # pragma: no cover - defensive integration guard
                failure_message = f"Signing failed: {exc}"
                self._last_signing_result = SigningResult(
                    success=False,
                    failure_code=None,
                    message=failure_message,
                )
                self._set_sign_result_text(failure_message, success=False)
                self._emit_error(failure_message)
                self.widget.last_signing_result = self._last_signing_result  # type: ignore[attr-defined]
                return request
            self._last_signing_result = result
            self.widget.last_signing_result = result  # type: ignore[attr-defined]
            if result.success:
                self._set_sign_result_text(
                    f"{result.message} Output: {request.output_pdf_path}",
                    success=True,
                )
                if self._on_status_change is not None:
                    self._on_status_change("sign_success")
            else:
                self._set_sign_result_text(result.message, success=False)
                if self._on_error is not None:
                    self._on_error(result.message)
                if self._on_status_change is not None:
                    self._on_status_change("sign_failure")
            return request
        self._last_signing_result = None
        self.widget.last_signing_result = None  # type: ignore[attr-defined]
        self._set_sign_result_text("")
        return request

    @property
    def last_signing_result(self) -> SigningResult | None:
        """Return the most recent signing result, if a real executor ran."""
        return self._last_signing_result

    def _handle_viewer_selection(self, pdf_rect: PdfRect) -> None:
        snapshot = getattr(self._viewer_workflow, "snapshot", None)
        page_index = (
            snapshot.page_index
            if snapshot is not None
            else self._viewer_workflow.session.current_page
        )
        normalized_rect = pdf_rect.normalized()
        self._sync_placement_context_from_viewer()
        try:
            signature_rect = SignatureRect(
                page_index=page_index,
                left_pt=normalized_rect.x1,
                bottom_pt=normalized_rect.y1,
                width_pt=normalized_rect.x2 - normalized_rect.x1,
                height_pt=normalized_rect.y2 - normalized_rect.y1,
            )
        except ValueError as exc:
            self._emit_error(f"Unable to apply signature placement: {exc}")
            return
        self.properties_panel.set_signature_rect(signature_rect)
        self._sync_signature_overlay()
        self._refresh_sign_button_state()

    def _handle_viewer_error(self, message: str) -> None:
        self._emit_error(message)

    def _handle_viewer_interaction(self, name: str) -> None:
        if self._on_status_change is not None:
            self._on_status_change(name)

    def _handle_panel_change(self) -> None:
        self._sync_placement_context_from_viewer()
        self._sync_signature_overlay()
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
        self._sync_signature_overlay()
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

    def _sync_signature_overlay(self) -> None:
        setter = getattr(self._viewer_widget, "set_signature_overlay", None)
        if callable(setter):
            setter(self._draft_workflow.signature_rect)

    def _refresh_sign_button_state(self) -> None:
        self._sign_button.setEnabled(self.properties_panel.is_ready_to_sign())

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
    """Factory for the Phase 3 Qt signing shell."""

    def __init__(self) -> None:
        self._bindings = self._load_bindings()

    def create(
        self,
        *,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        preset_catalog: SignaturePresetCatalog | None = None,
        preset_catalog_store: SignaturePresetCatalogStore | None = None,
        sign_executor: SigningRequestExecutor | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> Any:
        return SigningWorkspaceWidget(
            bindings=self._bindings,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            preset_catalog=preset_catalog,
            preset_catalog_store=preset_catalog_store,
            sign_executor=sign_executor,
            on_sign_request=on_sign_request,
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
            q_message_box=getattr(qt_widgets, "QMessageBox"),
            q_pixmap=getattr(qt_gui, "QPixmap"),
            q_double_spin_box=getattr(qt_widgets, "QDoubleSpinBox"),
            q_spin_box=getattr(qt_widgets, "QSpinBox"),
            q_push_button=getattr(qt_widgets, "QPushButton"),
            qt=getattr(qt_core, "Qt"),
        )


def build_qt_signing_shell(
    *,
    viewer_workflow: ViewerWorkflow,
    signing_workflow: SigningDraftWorkflow,
    preset_catalog: SignaturePresetCatalog | None = None,
    preset_catalog_store: SignaturePresetCatalogStore | None = None,
    sign_executor: SigningRequestExecutor | None = None,
    on_sign_request: Callable[[SigningRequest], None] | None = None,
    on_error: Callable[[str], None] | None = None,
    on_status_change: Callable[[str], None] | None = None,
) -> Any:
    """Build a QWidget instance for the Phase 3 signing shell."""

    adapter = SigningShellAdapter()
    return adapter.create(
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        preset_catalog=preset_catalog,
        preset_catalog_store=preset_catalog_store,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )
