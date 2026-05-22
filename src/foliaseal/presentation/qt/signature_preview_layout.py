"""Qt-facing preview layout planning and widget handoff for signing previews."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from math import ceil
from typing import Any

from foliaseal.application.phase3_signing_backend import (
    _single_line_horizontal_stamp_vertical_inset,
    _single_line_stamp_content_inset,
    _single_line_vertical_stamp_border_gap,
)
from foliaseal.application.signature_font_registry import (
    bundled_font_root,
    resolve_signature_font_face,
)
from foliaseal.application.signing_draft_workflow import SigningDraftPreview
from foliaseal.application.visible_signature_layout import (
    ImageMetrics,
    LayoutRequest,
    SignatureLayoutPlan,
    VisibleSignatureLayoutEngine,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
)
from foliaseal.presentation.qt.signature_preview_lifecycle import (
    CanonicalPreviewRenderState,
)

_PREVIEW_FONTS_REGISTERED = False
_PREVIEW_MAX_WIDTH_PX = 520
_PREVIEW_MAX_HEIGHT_PX = 180
_PREVIEW_DEFAULT_WIDTH_PX = 320
_PREVIEW_DEFAULT_HEIGHT_PX = 120
_PREVIEW_SCREEN_PX_PER_PT = 96.0 / 72.0
_PREVIEW_HORIZONTAL_PADDING_PX = 24
_PREVIEW_GROUP_OVERHEAD_PX = 28


def _load_stamp_pixmap(
    bindings: Any,
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
    del stamp_visible
    if inner_body_height_px <= 0:
        return (0, 0, 0)

    minimum_stamp_height = 0
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
    line_count = max(1, rendered_line_count)
    return min(4, 1 + line_count)


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


def _hex_to_css_color(value: str, *, fallback: str) -> str:
    candidate = value.strip()
    if len(candidate) == 7 and candidate.startswith("#"):
        return candidate
    return fallback


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


def _set_widget_width_limit(widget: Any, width: int) -> None:
    fixed_width = getattr(widget, "setFixedWidth", None)
    if callable(fixed_width):
        fixed_width(width)
        return
    max_width = getattr(widget, "setMaximumWidth", None)
    if callable(max_width):
        max_width(width)


def _set_widget_visible(widget: Any, visible: bool) -> None:
    setter = getattr(widget, "setVisible", None)
    if callable(setter):
        setter(visible)


@dataclass(frozen=True)
class PreviewLayoutState:
    stamp_text: str
    stamp_position: SignatureStampPosition
    is_vertical: bool
    available_width_px: int
    card_size: tuple[int, int]
    detail_width: int
    preview_scale: float
    preview_padding_px: float
    inner_body_size: tuple[int, int]
    reserved_text_height_px: int | None
    reserved_stamp_width_px: int | None
    reserved_stamp_height_px: int | None
    stamp_aspect_ratio: float | None
    raw_stamp_pixmap: Any | None
    fallback_card_style: str
    text_css: str


class QtSignaturePreviewLayout:
    """Plan and apply preview geometry and widget layout for the signing shell."""

    def __init__(self, *, bindings: Any) -> None:
        self._bindings = bindings

    def plan(
        self,
        *,
        preview: SigningDraftPreview,
        controls: Any,
    ) -> PreviewLayoutState:
        stamp_text = _preview_stamp_text(preview)
        stamp_position = preview.stamp_position or SignatureStampPosition.TOP
        is_vertical = stamp_position in (
            SignatureStampPosition.TOP,
            SignatureStampPosition.BOTTOM,
        )
        available_width_px = _preview_available_width(
            preview,
            container=controls.container,
        )
        card_width, card_height = _preview_body_size(
            preview,
            available_width_px=available_width_px,
        )
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
            card_width
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
        preview_padding_px = _preview_card_padding_px(preview)
        inner_body_width = _preview_inner_body_extent(card_width, preview_padding_px)
        inner_body_height = _preview_inner_body_extent(card_height, preview_padding_px)
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
        border_css, background_color = _preview_box_styles(preview)
        fallback_card_style = (
            "QGroupBox {"
            f" {border_css}"
            " border-radius: 6px;"
            f" background: {background_color};"
            f" padding: {preview_padding_px:.1f}px;"
            "}"
        )
        return PreviewLayoutState(
            stamp_text=stamp_text,
            stamp_position=stamp_position,
            is_vertical=is_vertical,
            available_width_px=available_width_px,
            card_size=(card_width, card_height),
            detail_width=detail_width,
            preview_scale=preview_scale,
            preview_padding_px=preview_padding_px,
            inner_body_size=(inner_body_width, inner_body_height),
            reserved_text_height_px=reserved_text_height_px,
            reserved_stamp_width_px=reserved_stamp_width_px,
            reserved_stamp_height_px=reserved_stamp_height_px,
            stamp_aspect_ratio=stamp_aspect_ratio,
            raw_stamp_pixmap=raw_stamp_pixmap,
            fallback_card_style=fallback_card_style,
            text_css=_preview_text_style(preview),
        )

    def apply(
        self,
        *,
        preview: SigningDraftPreview,
        controls: Any,
        state: PreviewLayoutState,
        canonical_render_state: CanonicalPreviewRenderState,
    ) -> None:
        is_vertical = state.is_vertical
        inner_body_width, inner_body_height = state.inner_body_size
        for widget in (
            controls.detail_label,
            controls.stamp_label,
            controls.multi_detail_label,
            controls.multi_stamp_label,
        ):
            _reset_widget_size_constraints(widget)

        card_width, card_height = state.card_size
        if hasattr(controls.card_container, "setFixedSize"):
            controls.card_container.setFixedSize(card_width, card_height)
        elif hasattr(controls.card_container, "setFixedWidth"):
            controls.card_container.setFixedWidth(card_width)

        for widget in (
            controls.title_label,
            controls.detail_label,
            controls.footer_label,
        ):
            _set_widget_width_limit(widget, card_width)
        for widget in (
            controls.multi_content_container,
            controls.multi_detail_label,
        ):
            _set_widget_width_limit(widget, state.detail_width)

        if hasattr(controls.card_container, "setStyleSheet"):
            controls.card_container.setStyleSheet(state.fallback_card_style)
        if hasattr(controls.title_label, "setStyleSheet"):
            controls.title_label.setStyleSheet(
                "font-weight: 700; "
                f"{state.text_css}"
            )
        if hasattr(controls.detail_label, "setStyleSheet"):
            controls.detail_label.setStyleSheet(state.text_css)
        if hasattr(controls.multi_detail_label, "setStyleSheet"):
            controls.multi_detail_label.setStyleSheet(state.text_css)
        for label in (
            controls.title_label,
            controls.detail_label,
            controls.multi_detail_label,
        ):
            set_word_wrap = getattr(label, "setWordWrap", None)
            if callable(set_word_wrap):
                set_word_wrap(False)
        controls.title_label.setText("")
        _set_widget_visible(controls.title_label, False)

        if hasattr(controls.single_body_container, "setFixedSize"):
            controls.single_body_container.setFixedSize(inner_body_width, inner_body_height)
        if hasattr(controls.multi_body_container, "setFixedSize"):
            controls.multi_body_container.setFixedSize(inner_body_width, inner_body_height)

        if is_vertical:
            controls.detail_label.setText(state.stamp_text)
            controls.multi_detail_label.setText("")
        else:
            content_height = (
                state.reserved_text_height_px
                if (
                    preview.layout_template != SignatureLayoutTemplate.SINGLE_LINE
                    and state.reserved_text_height_px is not None
                )
                else inner_body_height
            )
            controls.detail_label.setText("")
            controls.multi_detail_label.setText(state.stamp_text)
            if hasattr(controls.multi_content_container, "setFixedSize"):
                controls.multi_content_container.setFixedSize(state.detail_width, content_height)
            else:
                _set_widget_width_limit(controls.multi_content_container, state.detail_width)
            if hasattr(controls.multi_detail_label, "setFixedSize"):
                controls.multi_detail_label.setFixedSize(state.detail_width, content_height)
            else:
                _set_widget_width_limit(controls.multi_detail_label, state.detail_width)

        controls.footer_label.setText("")
        _set_widget_visible(controls.single_body_container, is_vertical)
        _set_widget_visible(controls.multi_body_container, not is_vertical)

        vertical_band_geometry = _preview_vertical_band_geometry(
            preview,
            stamp_text=state.stamp_text,
            inner_body_height_px=inner_body_height,
            available_width_px=state.available_width_px,
            stamp_aspect_ratio=state.stamp_aspect_ratio,
        )
        if is_vertical and vertical_band_geometry is not None:
            text_height, stamp_height, separator_height = vertical_band_geometry
            vertical_band_geometry = _fit_vertical_preview_band_geometry(
                text_height=text_height,
                stamp_height=stamp_height,
                separator_height=separator_height,
                inner_body_height_px=inner_body_height,
                detail_hint_height_px=_size_hint_height(controls.detail_label) or text_height,
                rendered_line_count=max(1, state.stamp_text.count("\n") + 1),
                stamp_visible=state.raw_stamp_pixmap is not None,
            )

        stamp_pixmap = None
        if state.raw_stamp_pixmap is not None:
            if is_vertical and vertical_band_geometry is not None:
                _text_height, stamp_height, _separator_height = vertical_band_geometry
                content_inset = _single_line_stamp_content_inset(
                    stamp_position=preview.stamp_position,
                    box_width=max(1, int(round(preview.signature_rect.width_pt))),
                    box_height=max(1, int(round(preview.signature_rect.height_pt))),
                    reserved_width=max(1, int(round(inner_body_width / state.preview_scale))),
                    reserved_height=max(1, int(round(stamp_height / state.preview_scale))),
                )
                inset_px = max(0, int(round(content_inset * state.preview_scale)))
                border_gap_px = max(
                    0,
                    int(
                        round(
                            _single_line_vertical_stamp_border_gap(box_style=preview.box_style)
                            * state.preview_scale
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
                    stamp_text=state.stamp_text,
                    raw_pixmap=state.raw_stamp_pixmap,
                    available_width_px=state.available_width_px,
                    stamp_aspect_ratio=state.stamp_aspect_ratio,
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
                    and state.reserved_stamp_height_px is not None
                    and hasattr(label, "setFixedSize")
                ):
                    label.setFixedSize(inner_body_width, state.reserved_stamp_height_px)
                elif (
                    not is_vertical
                    and preview.layout_template != SignatureLayoutTemplate.SINGLE_LINE
                    and state.reserved_stamp_width_px is not None
                    and state.reserved_stamp_height_px is not None
                    and hasattr(label, "setFixedSize")
                ):
                    label.setFixedSize(
                        state.reserved_stamp_width_px,
                        state.reserved_stamp_height_px,
                    )
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
                label.setPixmap("")
            _set_widget_visible(label, False)
            if hasattr(label, "setText"):
                label.setText("")
            if hasattr(label, "setFixedSize"):
                if is_vertical and vertical_band_geometry is not None:
                    _text_height, stamp_height, _separator_height = vertical_band_geometry
                    label.setFixedSize(inner_body_width, stamp_height)
                elif is_vertical and state.reserved_stamp_height_px is not None:
                    label.setFixedSize(inner_body_width, state.reserved_stamp_height_px)
                elif (
                    not is_vertical
                    and preview.layout_template != SignatureLayoutTemplate.SINGLE_LINE
                    and state.reserved_stamp_width_px is not None
                    and state.reserved_stamp_height_px is not None
                ):
                    label.setFixedSize(
                        state.reserved_stamp_width_px,
                        state.reserved_stamp_height_px,
                    )
                else:
                    label.setFixedSize(96, 64)

        align_left = _qt_alignment_flag(self._bindings.qt, "AlignLeft")
        align_center = _qt_alignment_flag(self._bindings.qt, "AlignCenter")
        align_top = _qt_alignment_flag(self._bindings.qt, "AlignTop")
        align_bottom = _qt_alignment_flag(self._bindings.qt, "AlignBottom")
        if is_vertical and align_left is not None:
            stamp_alignment = align_left
            if state.stamp_position == SignatureStampPosition.TOP and align_bottom is not None:
                stamp_alignment = align_left | align_bottom
            elif (
                state.stamp_position == SignatureStampPosition.BOTTOM
                and align_top is not None
            ):
                stamp_alignment = align_left | align_top
            if hasattr(controls.stamp_label, "setAlignment"):
                controls.stamp_label.setAlignment(stamp_alignment)
            if hasattr(controls.detail_label, "setAlignment"):
                controls.detail_label.setAlignment(align_left)
        elif align_center is not None and hasattr(controls.stamp_label, "setAlignment"):
            controls.stamp_label.setAlignment(align_center)

        if is_vertical:
            if vertical_band_geometry is not None:
                text_height, _stamp_height, separator_height = vertical_band_geometry
                if hasattr(controls.detail_label, "setFixedSize"):
                    controls.detail_label.setFixedSize(inner_body_width, text_height)
                layout = _container_layout(controls.single_body_container)
                if layout is not None and hasattr(layout, "setSpacing"):
                    layout.setSpacing(separator_height)
            elif state.reserved_text_height_px is not None and hasattr(
                controls.detail_label,
                "setFixedSize",
            ):
                controls.detail_label.setFixedSize(inner_body_width, state.reserved_text_height_px)
            stamp_widget: Any = controls.stamp_label
            detail_widget: Any = controls.detail_label
            if align_left is not None:
                stamp_widget = (controls.stamp_label, 0, align_left)
                detail_widget = (controls.detail_label, 0, align_left)
            single_widgets: list[Any] = [stamp_widget, detail_widget]
            if state.stamp_position == SignatureStampPosition.BOTTOM:
                single_widgets = [detail_widget, stamp_widget]
            _set_container_widgets(controls.single_body_container, *single_widgets)
        else:
            stamp_alignment = (
                align_center
                if align_center is not None
                else _qt_alignment_flag(self._bindings.qt, "AlignLeft")
            )
            if hasattr(controls.multi_stamp_label, "setAlignment"):
                controls.multi_stamp_label.setAlignment(stamp_alignment)
            _set_container_widgets(
                controls.multi_content_container,
                controls.multi_detail_label,
            )
            _set_container_widgets(
                controls.multi_body_container,
                (controls.multi_stamp_label, 0, stamp_alignment),
                (controls.multi_content_container, 0, stamp_alignment),
            )
            if state.stamp_position == SignatureStampPosition.RIGHT:
                _set_container_widgets(
                    controls.multi_body_container,
                    (controls.multi_content_container, 0, stamp_alignment),
                    (controls.multi_stamp_label, 0, stamp_alignment),
                )

        _apply_stamp(controls.stamp_label, visible=is_vertical and stamp_pixmap is not None)
        _apply_stamp(
            controls.multi_stamp_label,
            visible=(not is_vertical) and stamp_pixmap is not None,
        )

        controls.card_container._canonical_preview_snapshot = canonical_render_state.snapshot
        if hasattr(controls.card_container, "setStyleSheet"):
            controls.card_container.setStyleSheet(canonical_render_state.card_style)
        if canonical_render_state.snapshot is None:
            _set_widget_visible(controls.single_render_label, False)
            _set_widget_visible(controls.multi_render_label, False)
            return

        render_label = (
            controls.single_render_label if is_vertical else controls.multi_render_label
        )
        render_body = (
            controls.single_body_container if is_vertical else controls.multi_body_container
        )
        if canonical_render_state.pixmap is not None and hasattr(render_label, "setPixmap"):
            render_label.setPixmap(canonical_render_state.pixmap)
        if hasattr(render_label, "setFixedSize"):
            render_width, render_height = canonical_render_state.render_body_size
            render_label.setFixedSize(render_width, render_height)
            if hasattr(render_body, "setFixedSize"):
                render_body.setFixedSize(render_width, render_height)

        _set_widget_visible(controls.stamp_label, False)
        _set_widget_visible(controls.multi_stamp_label, False)
        _set_widget_visible(controls.detail_label, False)
        _set_widget_visible(controls.multi_detail_label, False)
        _set_widget_visible(
            controls.single_render_label,
            is_vertical and canonical_render_state.render_label_visible,
        )
        _set_widget_visible(
            controls.multi_render_label,
            (not is_vertical) and canonical_render_state.render_label_visible,
        )
        if is_vertical:
            _set_container_widgets(controls.single_body_container, controls.single_render_label)
        else:
            _set_container_widgets(controls.multi_body_container, controls.multi_render_label)
