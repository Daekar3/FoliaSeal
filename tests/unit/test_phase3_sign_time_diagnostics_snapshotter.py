from __future__ import annotations

import foliaseal.presentation.qt.phase3_harness as phase3_harness_module


def _snapshotter():
    return phase3_harness_module._build_sign_time_diagnostics_snapshotter()


def test_sign_time_diagnostics_snapshotter_combines_backend_and_canonical_geometry() -> None:
    diagnostics = _snapshotter().snapshot(
        preview_render_capture={
            "analysis_preview_image_path": "artifacts/preview.png",
            "text_rendered_content_bounds_px": {"x": 7, "y": 86, "width": 316, "height": 19},
            "text_rendered_line_bounds_px": (
                {"x": 7, "y": 86, "width": 92, "height": 9},
                {"x": 7, "y": 96, "width": 316, "height": 9},
            ),
            "card_bounds_px": {"x": 0, "y": 0, "width": 343, "height": 115},
            "analysis_appearance_snapshot": {
                "image_path": "artifacts/preview_analysis.png",
                "image_size_px": {"width": 257, "height": 86},
                "container_bounds_px": {"x": 0, "y": 0, "width": 257, "height": 86},
                "text_bounds_px": {"x": 5, "y": 85, "width": 333, "height": 24},
                "line_bounds_px": (
                    {"x": 5, "y": 85, "width": 97, "height": 12},
                    {"x": 5, "y": 97, "width": 333, "height": 12},
                ),
                "stamp_bounds_px": {"x": 6, "y": 11, "width": 273, "height": 64},
            },
        },
        backend_reservation_snapshot={
            "measured_text_box_width_pt": 250,
            "measured_text_box_height_pt": 18,
            "text_area_width_pt": 249,
            "text_area_height_pt": 18,
            "stamp_area_width_pt": 249,
            "stamp_area_height_pt": 54,
            "reserved_primary_extent_pt": 54,
            "fit_gate_width_limit_pt": 250,
            "fit_gate_height_limit_pt": 18,
            "fit_gate_passed": True,
            "error": None,
        },
    )

    assert diagnostics is not None
    assert diagnostics["backend_fit"]["coordinate_space"] == "pdf_points"
    assert diagnostics["backend_fit"]["measured_text_box_width_pt"] == 250
    assert diagnostics["backend_fit"]["fit_gate_passed"] is True
    assert diagnostics["canonical_preview_geometry"]["coordinate_space"] == (
        "canonical_preview_pixels"
    )
    assert diagnostics["canonical_preview_geometry"]["image_path"] == (
        "artifacts/preview_analysis.png"
    )
    assert diagnostics["canonical_preview_geometry"]["image_size_px"] == {
        "width": 257,
        "height": 86,
    }
    assert diagnostics["canonical_preview_geometry"]["text_bounds_px"] == {
        "x": 7,
        "y": 86,
        "width": 316,
        "height": 19,
    }
    assert diagnostics["canonical_preview_geometry"]["line_bounds_px"] == (
        {"x": 7, "y": 86, "width": 92, "height": 9},
        {"x": 7, "y": 96, "width": 316, "height": 9},
    )
    assert diagnostics["canonical_preview_geometry"]["structural_text_bounds_px"] == {
        "x": 5,
        "y": 85,
        "width": 333,
        "height": 24,
    }
    assert diagnostics["canonical_preview_geometry"]["glyph_ink_text_bounds_px"] == {
        "x": 7,
        "y": 86,
        "width": 316,
        "height": 19,
    }
