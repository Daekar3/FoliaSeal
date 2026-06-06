"""Sign-time fit diagnostics shaping helpers for Phase 3 QA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Mapping = Callable[[Any], dict[str, Any]]


@dataclass(frozen=True)
class Phase3SignTimeDiagnosticsSnapshotter:
    """Own the merged backend-fit and canonical-preview diagnostics payload."""

    mapping: Mapping

    def snapshot(
        self,
        *,
        preview_render_capture: dict[str, Any] | None,
        backend_reservation_snapshot: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        backend = self.mapping(backend_reservation_snapshot)
        render_capture = self.mapping(preview_render_capture)
        if not backend and not render_capture:
            return None
        analysis_snapshot = self.mapping(render_capture.get("analysis_appearance_snapshot"))
        structural_line_bounds = tuple(
            analysis_snapshot.get("line_bounds_px")
            or render_capture.get("text_structural_line_bounds_px")
            or ()
        )
        structural_text_bounds = self.mapping(
            analysis_snapshot.get("text_bounds_px")
        ) or self.mapping(render_capture.get("text_structural_content_bounds_px"))
        glyph_ink_line_bounds = tuple(render_capture.get("text_rendered_line_bounds_px") or ())
        glyph_ink_text_bounds = self.mapping(render_capture.get("text_rendered_content_bounds_px"))
        canonical_stamp_bounds = self.mapping(
            analysis_snapshot.get("stamp_bounds_px")
        ) or self.mapping(render_capture.get("stamp_rendered_content_bounds_px"))
        canonical_image_size = self.mapping(analysis_snapshot.get("image_size_px")) or {
            "width": self.mapping(render_capture.get("card_bounds_px")).get("width"),
            "height": self.mapping(render_capture.get("card_bounds_px")).get("height"),
        }
        if canonical_image_size == {"width": None, "height": None}:
            canonical_image_size = None
        return {
            "backend_fit": {
                "coordinate_space": "pdf_points",
                "measured_text_box_width_pt": backend.get("measured_text_box_width_pt"),
                "measured_text_box_height_pt": backend.get("measured_text_box_height_pt"),
                "text_area_width_pt": backend.get("text_area_width_pt"),
                "text_area_height_pt": backend.get("text_area_height_pt"),
                "stamp_area_width_pt": backend.get("stamp_area_width_pt"),
                "stamp_area_height_pt": backend.get("stamp_area_height_pt"),
                "reserved_primary_extent_pt": backend.get("reserved_primary_extent_pt"),
                "fit_gate_width_limit_pt": backend.get("fit_gate_width_limit_pt"),
                "fit_gate_height_limit_pt": backend.get("fit_gate_height_limit_pt"),
                "fit_gate_passed": backend.get("fit_gate_passed"),
                "error": backend.get("error"),
            },
            "canonical_preview_geometry": {
                "coordinate_space": "canonical_preview_pixels",
                "image_path": analysis_snapshot.get("image_path")
                or render_capture.get("analysis_preview_image_path")
                or render_capture.get("preview_image_path"),
                "image_size_px": canonical_image_size,
                "container_bounds_px": self.mapping(analysis_snapshot.get("container_bounds_px"))
                or self.mapping(render_capture.get("card_bounds_px")),
                "text_bounds_px": glyph_ink_text_bounds or structural_text_bounds,
                "line_bounds_px": glyph_ink_line_bounds or structural_line_bounds,
                "structural_text_bounds_px": structural_text_bounds,
                "structural_line_bounds_px": structural_line_bounds,
                "glyph_ink_text_bounds_px": glyph_ink_text_bounds,
                "glyph_ink_line_bounds_px": glyph_ink_line_bounds,
                "stamp_bounds_px": canonical_stamp_bounds,
            },
        }

