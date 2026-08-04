from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from foliaseal.presentation.qt.preview_analysis import (
    PreviewAnalysisRequest,
    analyze_capture_state_transitions,
    build_preview_analysis_engine,
)


def _request(image_path: Path) -> PreviewAnalysisRequest:
    bounds = {"x": 0, "y": 0, "width": 80, "height": 40}
    return PreviewAnalysisRequest(
        preview=SimpleNamespace(image_stamp_path=None, layout_template=None, stamp_position=None),
        preview_image_path=str(image_path),
        analysis_image_path=str(image_path),
        image_error=None,
        card_bounds=bounds,
        body_bounds=bounds,
        detail_bounds=bounds,
        stamp_bounds=None,
        text_widget_bounds=bounds,
        analysis_detection_bounds=bounds,
        stamp_band_bounds=None,
        stamp_pixmap_bounds=None,
        stamp_content_bounds_override=None,
        structural_text_content_bounds=None,
        structural_line_bounds=(),
        reference_text_content_bounds=None,
        reference_text_detection_error=None,
        text_color_rgba=(0, 0, 0, 255),
        active_label=None,
        preview_padding_px=6,
        layout_spacing_px=0,
    )


def test_analysis_engine_returns_neutral_payload_for_rendered_preview(tmp_path: Path) -> None:
    image_path = tmp_path / "preview.png"
    image = Image.new("RGBA", (80, 40), (255, 255, 255, 255))
    for x in range(18, 46):
        for y in range(12, 21):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(image_path)

    values = build_preview_analysis_engine().analyze(_request(image_path)).as_mapping()

    assert values["text_rendered_content_bounds_px"] == {
        "x": 18,
        "y": 12,
        "width": 28,
        "height": 9,
    }
    assert values["text_widget_image_sha256"]
    assert "edge_distances_px" in values
    assert values["stamp_source_image_size_px"] is None


def test_neutral_analysis_import_does_not_load_qt_bindings() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[2] / "src")
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import foliaseal.presentation.qt.preview_analysis; "
                "print(any(name == 'PySide6' or name.startswith('PySide6.') "
                "for name in sys.modules))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.stdout.strip() == "False"


def test_transition_analysis_is_neutral_and_skips_malformed_states(tmp_path: Path) -> None:
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    Image.new("RGBA", (20, 10), (255, 255, 255, 255)).save(image_a)
    Image.new("RGBA", (20, 10), (255, 255, 255, 255)).save(image_b)
    states = (
        None,
        {
            "capture_label": "one",
            "preview_text": "Alice 2026-08-04 10:00",
            "preview_snapshot": {
                "layout_template": "single_line",
                "stamp_position": "top",
                "signature_rect": {"width_pt": 200.0, "height_pt": 30.0},
                "text_style": {"font_family": "Serif", "font_size_pt": 8.0},
                "render_capture": {
                    "preview_image_path": str(image_a),
                    "text_widget_bounds_px": {"x": 0, "y": 0, "width": 20, "height": 10},
                    "text_rendered_content_bounds_px": {"x": 2, "y": 2, "width": 8, "height": 3},
                    "effective_text_font_category": "serif",
                },
            },
        },
    )

    assert build_preview_analysis_engine().analyze_capture_transitions(states) == ()


def test_neutral_transition_analysis_skips_malformed_states_and_flags_font_size_change(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGBA", (20, 10), (255, 255, 255, 255)).save(first)
    Image.new("RGBA", (20, 10), (255, 255, 255, 255)).save(second)
    states = (
        {"preview_snapshot": None},
        {
            "capture_label": "before",
            "preview_text": "Ada\n2026-04-11 09:00",
            "preview_snapshot": {
                "layout_template": "multi_line",
                "stamp_position": "top",
                "signature_rect": {"width_pt": 100},
                "text_style": {"font_family": "Serif", "font_size_pt": 8.0},
                "render_capture": {
                    "preview_image_path": str(first),
                    "text_widget_bounds_px": {"x": 0, "y": 0, "width": 20, "height": 10},
                    "text_rendered_content_bounds_px": {"x": 2, "y": 2, "width": 8, "height": 4},
                    "effective_text_font_category": "serif",
                },
            },
        },
        {
            "capture_label": "after",
            "preview_text": "Ada\n2026-04-11 09:00",
            "preview_snapshot": {
                "layout_template": "multi_line",
                "stamp_position": "top",
                "signature_rect": {"width_pt": 100},
                "text_style": {"font_family": "Serif", "font_size_pt": 7.5},
                "render_capture": {
                    "preview_image_path": str(second),
                    "text_widget_bounds_px": {"x": 0, "y": 0, "width": 20, "height": 10},
                    "text_rendered_content_bounds_px": {"x": 2, "y": 2, "width": 8, "height": 4},
                    "effective_text_font_category": "serif",
                },
            },
        },
    )

    diagnostics = analyze_capture_state_transitions(states)

    assert len(diagnostics) == 1
    assert diagnostics[0]["issue_code"] == "font_size_change_had_negligible_visual_effect"
