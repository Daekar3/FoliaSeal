from __future__ import annotations

import foliaseal.presentation.qt.phase3_harness as phase3_harness_module


def _snapshotter():
    return phase3_harness_module._build_phase3_appearance_snapshotter()


def test_preview_appearance_snapshotter_restores_border_style_when_missing() -> None:
    preview_snapshot = {
        "box_style": {
            "show_border": True,
            "border_color_hex": "#000000",
            "border_width_pt": 1.0,
            "background_color_hex": "#FFFFFF",
        },
        "render_capture": {
            "analysis_appearance_snapshot": {
                "image_path": "analysis.png",
                "image_size_px": {"width": 320, "height": 42},
                "container_bounds_px": {"x": 0, "y": 0, "width": 320, "height": 42},
                "border_bounds_px": None,
                "border_style": None,
                "text_bounds_px": {"x": 3, "y": 3, "width": 240, "height": 20},
                "stamp_bounds_px": None,
                "text_fragments": [
                    "Digitally signed by",
                    "Morgan Ellery | 2026-04-20 00:55:01 UTC",
                ],
                "line_bounds_px": [
                    {"x": 3, "y": 3, "width": 240, "height": 8},
                    {"x": 3, "y": 15, "width": 240, "height": 8},
                ],
            }
        },
    }

    snapshot = _snapshotter().preview_appearance_snapshot_from_capture(
        preview_snapshot=preview_snapshot
    )

    assert snapshot.border_style is not None
    assert snapshot.border_style["shape"] == "rounded"
    assert snapshot.border_bounds_px == {"x": 0, "y": 0, "width": 320, "height": 42}
    assert snapshot.line_bounds_px == (
        {"x": 3, "y": 3, "width": 240, "height": 8},
        {"x": 3, "y": 15, "width": 240, "height": 8},
    )


def test_signed_output_appearance_snapshotter_derives_structural_line_bounds() -> None:
    snapshot = _snapshotter().signed_output_appearance_snapshot(
        normalized_image_path="signed.png",
        normalized_image_size={"width": 320, "height": 42},
        text_bounds_px={"x": 4, "y": 3, "width": 250, "height": 20},
        line_bounds_px=(
            {"x": 4, "y": 3, "width": 120, "height": 8},
            {"x": 4, "y": 15, "width": 250, "height": 8},
        ),
        visible_appearance_snapshot={
            "appearance_uses_rounded_border": True,
            "text_fragments": ["Digitally signed by", "Morgan Ellery"],
            "image_xobject_count": 0,
        },
        preview_snapshot={
            "text_style": {
                "font_family": "Sans Serif",
                "font_size_pt": 8.5,
                "bold": False,
                "italic": False,
                "text_color_hex": "#000000",
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "render_capture": {},
        },
    )

    assert len(snapshot.line_bounds_px) == 2
    assert snapshot.line_bounds_px[0]["x"] == 4
    assert snapshot.line_bounds_px[0]["y"] == 3
    assert snapshot.line_bounds_px[1]["y"] > snapshot.line_bounds_px[0]["y"]
    assert all(line["width"] > 0 for line in snapshot.line_bounds_px)
