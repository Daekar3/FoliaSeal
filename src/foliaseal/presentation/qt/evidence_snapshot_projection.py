"""Pure semantic views over harness evidence snapshots.

The harness owns capture and JSON construction; this module owns the small, messy
compatibility policy needed to read modern and legacy snapshot shapes consistently.
It deliberately has no Qt, PDF, image, filesystem, or report dependencies.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

SnapshotMapping = Mapping[str, Any] | None
Number = int | float


def _mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _number(value: Any) -> Number | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _first_string(mapping: Mapping[str, Any] | None, *keys: str) -> str | None:
    if mapping is None:
        return None
    for key in keys:
        value = _string(mapping.get(key))
        if value is not None:
            return value
    return None


def _freeze_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class RenderCaptureView:
    """Normalized render-capture diagnostics used by reports and harness adapters."""

    preview_image_path: str | None = None
    analysis_preview_image_path: str | None = None
    edge_distances_px: Mapping[str, Number] = field(default_factory=lambda: MappingProxyType({}))

    def edge_distance(self, key: str) -> Number | None:
        return self.edge_distances_px.get(key)


@dataclass(frozen=True)
class LayoutView:
    """Modern-or-legacy layout reservation values."""

    source: str = "none"
    background_scaling: str | None = None
    content_scaling: str | None = None
    content_bottom_margin_pt: Number | None = None


@dataclass(frozen=True)
class ReservationView:
    """Visible-signature reservation values used in acceptance readouts."""

    stamp_text_length: int = 0
    stamp_background_present: bool = False
    layout: LayoutView = field(default_factory=LayoutView)


@dataclass(frozen=True)
class VisibleAppearanceView:
    """Stable scalar and summary projections for a signed appearance snapshot."""

    field_name: str = "not captured"
    annotation_rect: str = "not captured"
    appearance_bbox: str = "not captured"
    appearance_stream_length: int = 0
    visible_text: str = "not captured"
    text_fragments: tuple[str, ...] = ()
    image_xobjects: tuple[Mapping[str, Any], ...] = ()
    captured: bool = False
    error: str = "not captured"

    def text_fragments_summary(self) -> str:
        if not self.captured:
            return "not captured"
        if not self.text_fragments:
            return "[]"
        preview = ", ".join(repr(fragment) for fragment in self.text_fragments[:6])
        suffix = ", ..." if len(self.text_fragments) > 6 else ""
        return f"[{preview}{suffix}]"

    def image_xobjects_summary(self) -> str:
        if not self.captured:
            return "not captured"
        if not self.image_xobjects:
            return "[]"
        entries: list[str] = []
        for item in self.image_xobjects[:6]:
            name = item.get("name")
            subtype = item.get("subtype")
            width = item.get("width")
            height = item.get("height")
            size = f" {width}x{height}" if width is not None and height is not None else ""
            entries.append(f"{name}:{subtype}{size}")
        suffix = ", ..." if len(self.image_xobjects) > 6 else ""
        return f"[{', '.join(entries)}{suffix}]"


@dataclass(frozen=True)
class SnapshotView:
    """Immutable semantic projection of one evidence snapshot."""

    signature_appearance: Mapping[str, Any] | None = None
    layout_template: str | None = None
    stamp_position: str | None = None
    show_field_names: bool = False
    request_field_count: int = 0
    render_capture: RenderCaptureView = field(default_factory=RenderCaptureView)
    reservation: ReservationView = field(default_factory=ReservationView)

    def preview_edge_distance(self, key: str) -> Number | None:
        return self.render_capture.edge_distance(key)


def _project_render_capture(snapshot: Mapping[str, Any] | None) -> RenderCaptureView:
    if snapshot is None:
        return RenderCaptureView()
    nested = _mapping(snapshot.get("render_capture"))
    source = nested or snapshot
    distances_value = source.get("edge_distances_px") if source is not None else None
    distances_mapping = _mapping(distances_value) or {}
    distances = {
        str(key): numeric
        for key, value in distances_mapping.items()
        if (numeric := _number(value)) is not None
    }
    preview_path = _string(source.get("preview_image_path")) if source else None
    analysis_path = _string(source.get("analysis_preview_image_path")) if source else None
    if analysis_path is None:
        analysis_path = preview_path
    return RenderCaptureView(
        preview_image_path=preview_path,
        analysis_preview_image_path=analysis_path,
        edge_distances_px=MappingProxyType(distances),
    )


def _project_layout(snapshot: Mapping[str, Any] | None) -> LayoutView:
    if snapshot is None:
        return LayoutView()
    modern = _mapping(snapshot.get("layout_plan"))
    background = _mapping(snapshot.get("background_layout"))
    content = _mapping(snapshot.get("content_layout"))
    background_scaling = _first_string(modern, "background_scaling")
    if background_scaling is None:
        background_scaling = _first_string(background, "inner_content_scaling")
    content_scaling = _first_string(modern, "content_scaling")
    if content_scaling is None:
        content_scaling = _first_string(content, "inner_content_scaling")
    margin = _number(modern.get("content_bottom_margin_pt")) if modern else None
    if margin is None and content is not None:
        margins = _mapping(content.get("margins"))
        margin = _number(margins.get("bottom")) if margins else None
    source = "layout_plan" if modern is not None else "legacy" if background or content else "none"
    return LayoutView(
        source=source,
        background_scaling=background_scaling,
        content_scaling=content_scaling,
        content_bottom_margin_pt=margin,
    )


def _project_reservation(snapshot: Mapping[str, Any] | None, layout: LayoutView) -> ReservationView:
    if snapshot is None:
        return ReservationView(layout=layout)
    text = snapshot.get("stamp_text")
    modern_art = snapshot.get("stamp_art_enabled")
    background = bool(modern_art) if modern_art is not None else bool(
        snapshot.get("stamp_background_present")
    )
    return ReservationView(
        stamp_text_length=len(text) if isinstance(text, str) else 0,
        stamp_background_present=background,
        layout=layout,
    )


def project_snapshot(snapshot: SnapshotMapping) -> SnapshotView:
    """Project a raw snapshot without raising on missing or malformed fields."""

    if snapshot is None:
        return SnapshotView()
    appearance = _mapping(snapshot.get("signature_appearance"))
    layout_template = _first_string(snapshot, "layout_template") or _first_string(
        appearance, "layout_template"
    )
    stamp_position = _first_string(snapshot, "stamp_position") or _first_string(
        appearance, "stamp_position"
    )
    show_field_names = bool(
        appearance.get("show_field_names")
        if appearance is not None and "show_field_names" in appearance
        else snapshot.get("show_field_names")
    )
    fields = appearance.get("fields") if appearance is not None else None
    field_count = len(fields) if isinstance(fields, list) else 0
    render_capture = _project_render_capture(snapshot)
    layout = _project_layout(snapshot)
    return SnapshotView(
        signature_appearance=(_freeze_mapping(appearance) if appearance is not None else None),
        layout_template=layout_template,
        stamp_position=stamp_position,
        show_field_names=show_field_names,
        request_field_count=field_count,
        render_capture=render_capture,
        reservation=_project_reservation(snapshot, layout),
    )


def project_visible_appearance(snapshot: SnapshotMapping) -> VisibleAppearanceView:
    """Normalize signed-appearance scalar fields and legacy aliases."""

    if snapshot is None:
        return VisibleAppearanceView()
    fragments_value = snapshot.get("text_fragments", snapshot.get("appearance_text_fragments"))
    fragments = (
        tuple(value for value in fragments_value if isinstance(value, str))
        if isinstance(fragments_value, list)
        else ()
    )
    xobjects_value = snapshot.get("image_xobjects", snapshot.get("appearance_xobjects"))
    xobjects = (
        tuple(_freeze_mapping(value) for value in xobjects_value if isinstance(value, Mapping))
        if isinstance(xobjects_value, list)
        else ()
    )
    has_text = snapshot.get("visible_text_present", snapshot.get("appearance_has_visible_text"))
    visible_text = "yes" if isinstance(has_text, bool) and has_text else (
        "no" if isinstance(has_text, bool) else "not captured"
    )
    stream_length = snapshot.get("appearance_stream_length")
    field_name = (
        str(snapshot.get("field_name"))
        if snapshot.get("field_name") is not None
        else "not captured"
    )
    return VisibleAppearanceView(
        field_name=field_name,
        annotation_rect=(
            str(snapshot.get("annotation_rect"))
            if snapshot.get("annotation_rect") is not None
            else "not captured"
        ),
        appearance_bbox=(
            str(snapshot.get("appearance_bbox"))
            if snapshot.get("appearance_bbox") is not None
            else "not captured"
        ),
        appearance_stream_length=(
            int(stream_length)
            if isinstance(stream_length, int) and not isinstance(stream_length, bool)
            else 0
        ),
        visible_text=visible_text,
        text_fragments=fragments,
        image_xobjects=xobjects,
        captured=True,
        error=str(snapshot.get("error")) if snapshot.get("error") is not None else "none",
    )


# Transitional function adapters keep existing provider signatures stable while callers migrate.
def snapshot_sign_request_appearance(snapshot: SnapshotMapping) -> Mapping[str, Any] | None:
    return project_snapshot(snapshot).signature_appearance


def snapshot_layout_template(snapshot: SnapshotMapping) -> str | None:
    return project_snapshot(snapshot).layout_template


def snapshot_stamp_position(snapshot: SnapshotMapping) -> str | None:
    return project_snapshot(snapshot).stamp_position


def snapshot_show_field_names(snapshot: SnapshotMapping) -> bool:
    return project_snapshot(snapshot).show_field_names


def snapshot_request_field_count(snapshot: SnapshotMapping) -> int:
    return project_snapshot(snapshot).request_field_count


def snapshot_preview_edge_distance(snapshot: SnapshotMapping, key: str) -> Number | None:
    return project_snapshot(snapshot).preview_edge_distance(key)


def snapshot_reservation_text_length(snapshot: SnapshotMapping) -> int:
    return project_snapshot(snapshot).reservation.stamp_text_length


def snapshot_reservation_stamp_background(snapshot: SnapshotMapping) -> bool:
    return project_snapshot(snapshot).reservation.stamp_background_present


def snapshot_layout_scaling(snapshot: SnapshotMapping, key: str) -> str | None:
    layout = project_snapshot(snapshot).reservation.layout
    return layout.background_scaling if key == "background" else layout.content_scaling


def snapshot_reservation_margin_bottom(snapshot: SnapshotMapping) -> Number | None:
    return project_snapshot(snapshot).reservation.layout.content_bottom_margin_pt


def snapshot_visible_appearance_field_name(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).field_name


def snapshot_visible_appearance_annotation_rect(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).annotation_rect


def snapshot_visible_appearance_bbox(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).appearance_bbox


def snapshot_visible_appearance_stream_length(snapshot: SnapshotMapping) -> int:
    return project_visible_appearance(snapshot).appearance_stream_length


def snapshot_visible_appearance_has_text(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).visible_text


def snapshot_visible_appearance_text_fragments(snapshot: SnapshotMapping) -> list[str]:
    return list(project_visible_appearance(snapshot).text_fragments)


def snapshot_visible_appearance_text_fragments_summary(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).text_fragments_summary()


def snapshot_visible_appearance_image_xobjects(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).image_xobjects_summary()


def snapshot_visible_appearance_error(snapshot: SnapshotMapping) -> str:
    return project_visible_appearance(snapshot).error


__all__ = [
    "LayoutView",
    "RenderCaptureView",
    "ReservationView",
    "SnapshotView",
    "VisibleAppearanceView",
    "project_snapshot",
    "project_visible_appearance",
    "snapshot_layout_scaling",
    "snapshot_layout_template",
    "snapshot_preview_edge_distance",
    "snapshot_request_field_count",
    "snapshot_reservation_margin_bottom",
    "snapshot_reservation_stamp_background",
    "snapshot_reservation_text_length",
    "snapshot_sign_request_appearance",
    "snapshot_show_field_names",
    "snapshot_stamp_position",
    "snapshot_visible_appearance_annotation_rect",
    "snapshot_visible_appearance_bbox",
    "snapshot_visible_appearance_error",
    "snapshot_visible_appearance_field_name",
    "snapshot_visible_appearance_has_text",
    "snapshot_visible_appearance_image_xobjects",
    "snapshot_visible_appearance_stream_length",
    "snapshot_visible_appearance_text_fragments",
    "snapshot_visible_appearance_text_fragments_summary",
]
