"""Appearance snapshot shaping helpers for Acceptance QA parity checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.signing_preview_renderer import SignatureAppearanceSnapshot

Mapping = Callable[[Any], dict[str, Any]]
SignatureTextStyleFromSnapshot = Callable[[object], Any]
StructuralLineBounds = Callable[..., tuple[dict[str, Any], ...]]
VisibleAppearanceImageXObjects = Callable[[dict[str, Any]], list[str]]
VisibleAppearanceTextFragments = Callable[[dict[str, Any]], list[str]]
ReconstructTextBoxBounds = Callable[..., dict[str, Any] | None]
UnionRectangles = Callable[[tuple[dict[str, Any], ...]], dict[str, Any] | None]


@dataclass(frozen=True)
class AcceptanceAppearanceSnapshotter:
    """Own both sides of the Acceptance appearance parity model."""

    mapping: Mapping
    signature_text_style_from_snapshot: SignatureTextStyleFromSnapshot
    structural_line_bounds: StructuralLineBounds
    visible_appearance_image_xobjects: VisibleAppearanceImageXObjects
    visible_appearance_text_fragments: VisibleAppearanceTextFragments
    reconstruct_text_box_bounds: ReconstructTextBoxBounds
    union_rectangles: UnionRectangles

    def preview_appearance_snapshot_from_capture(
        self,
        *,
        preview_snapshot: dict[str, Any],
    ) -> SignatureAppearanceSnapshot:
        render_capture = self.mapping(preview_snapshot.get("render_capture"))
        analysis_snapshot = self.mapping(render_capture.get("analysis_appearance_snapshot"))
        box_style = self.mapping(preview_snapshot.get("box_style"))
        if analysis_snapshot:
            border_style = self.mapping(analysis_snapshot.get("border_style")) or None
            border_bounds = self.mapping(analysis_snapshot.get("border_bounds_px")) or None
            if border_style is None and box_style.get("show_border") is True:
                border_style = {
                    "show_border": True,
                    "shape": "rounded",
                    "border_color_hex": box_style.get("border_color_hex"),
                    "border_width_pt": box_style.get("border_width_pt"),
                    "background_color_hex": box_style.get("background_color_hex"),
                }
                border_bounds = self.mapping(
                    analysis_snapshot.get("container_bounds_px")
                ) or None
            return SignatureAppearanceSnapshot(
                image_path=analysis_snapshot.get("image_path"),
                image_size_px=self.mapping(analysis_snapshot.get("image_size_px")) or None,
                container_bounds_px=self.mapping(analysis_snapshot.get("container_bounds_px"))
                or None,
                border_bounds_px=border_bounds,
                border_style=border_style,
                text_bounds_px=self.mapping(analysis_snapshot.get("text_bounds_px")) or None,
                stamp_bounds_px=self.mapping(analysis_snapshot.get("stamp_bounds_px")) or None,
                text_fragments=tuple(analysis_snapshot.get("text_fragments", ())),
                line_bounds_px=tuple(analysis_snapshot.get("line_bounds_px", ())),
            )
        card_bounds = self.mapping(render_capture.get("card_bounds_px"))
        image_size = None
        if card_bounds:
            image_size = {"width": card_bounds["width"], "height": card_bounds["height"]}
        border_style = None
        if box_style.get("show_border") is True:
            border_style = {
                "show_border": True,
                "shape": "rounded",
                "border_color_hex": box_style.get("border_color_hex"),
                "border_width_pt": box_style.get("border_width_pt"),
                "background_color_hex": box_style.get("background_color_hex"),
            }
        text_fragments = tuple(
            field.get("text", "").strip()
            for field in preview_snapshot.get("fields", ())
            if (
                isinstance(field, dict)
                and field.get("visible") is True
                and field.get("text", "").strip()
            )
        )
        text_style = self.signature_text_style_from_snapshot(
            preview_snapshot.get("text_style")
        )
        text_bounds = self.mapping(render_capture.get("text_rendered_content_bounds_px")) or None
        line_bounds = tuple(render_capture.get("text_rendered_line_bounds_px", ()))
        if not line_bounds:
            line_bounds = self.structural_line_bounds(
                text="\n".join(text_fragments),
                text_fragments=text_fragments,
                text_style=text_style,
                text_bounds_px=text_bounds,
            )
        return SignatureAppearanceSnapshot(
            image_path=render_capture.get("analysis_preview_image_path")
            or render_capture.get("preview_image_path"),
            image_size_px=image_size,
            container_bounds_px=card_bounds or None,
            border_bounds_px=(card_bounds or None) if border_style is not None else None,
            border_style=border_style,
            text_bounds_px=text_bounds,
            stamp_bounds_px=self.mapping(render_capture.get("stamp_rendered_content_bounds_px"))
            or None,
            text_fragments=text_fragments,
            line_bounds_px=line_bounds,
        )

    def signed_output_appearance_snapshot(
        self,
        *,
        normalized_image_path: str,
        normalized_image_size: dict[str, int],
        text_bounds_px: dict[str, int] | None,
        line_bounds_px: tuple[dict[str, int], ...] = (),
        visible_appearance_snapshot: dict[str, Any],
        preview_snapshot: dict[str, Any],
    ) -> SignatureAppearanceSnapshot:
        preview_box_style = self.mapping(preview_snapshot.get("box_style"))
        border_shape = "rounded"
        if visible_appearance_snapshot.get("appearance_uses_rounded_border") is False:
            border_shape = "square"
        elif visible_appearance_snapshot.get("appearance_uses_rounded_border") is None:
            border_shape = "unknown"
        border_style = None
        if preview_box_style.get("show_border") is True:
            border_style = {
                "show_border": True,
                "shape": border_shape,
                "border_color_hex": preview_box_style.get("border_color_hex"),
                "border_width_pt": preview_box_style.get("border_width_pt"),
                "background_color_hex": preview_box_style.get("background_color_hex"),
            }
        container_bounds = {
            "x": 0,
            "y": 0,
            "width": normalized_image_size["width"],
            "height": normalized_image_size["height"],
        }
        stamp_bounds = None
        if self.visible_appearance_image_xobjects(visible_appearance_snapshot):
            preview_render_capture = self.mapping(preview_snapshot.get("render_capture"))
            analysis_snapshot = self.mapping(
                preview_render_capture.get("analysis_appearance_snapshot")
            )
            stamp_bounds = (
                self.mapping(analysis_snapshot.get("stamp_bounds_px"))
                or self.mapping(preview_render_capture.get("stamp_rendered_content_bounds_px"))
                or None
            )
        text_fragments = tuple(
            self.visible_appearance_text_fragments(visible_appearance_snapshot)
        )
        text_style = self.signature_text_style_from_snapshot(
            preview_snapshot.get("text_style")
        )
        reconstructed_text_box_bounds = self.reconstruct_text_box_bounds(
            preview_snapshot=preview_snapshot,
            text_fragments=text_fragments,
            container_bounds_px=container_bounds,
        )
        structural_line_bounds = self.structural_line_bounds(
            text="\n".join(text_fragments),
            text_fragments=text_fragments,
            text_style=text_style,
            text_bounds_px=reconstructed_text_box_bounds or text_bounds_px,
        )
        return SignatureAppearanceSnapshot(
            image_path=normalized_image_path,
            image_size_px=normalized_image_size,
            container_bounds_px=container_bounds,
            border_bounds_px=container_bounds if border_style is not None else None,
            border_style=border_style,
            text_bounds_px=(
                self.union_rectangles(structural_line_bounds)
                or reconstructed_text_box_bounds
                or text_bounds_px
            ),
            stamp_bounds_px=stamp_bounds,
            text_fragments=text_fragments,
            line_bounds_px=structural_line_bounds or line_bounds_px,
        )
