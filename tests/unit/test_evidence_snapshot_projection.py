from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from foliaseal.presentation.qt.evidence_snapshot_projection import (
    project_snapshot,
    project_visible_appearance,
)


def test_projection_prefers_modern_schema_and_nested_render_capture() -> None:
    snapshot = {
        "signature_appearance": {
            "layout_template": "modern-template",
            "stamp_position": "modern-position",
            "show_field_names": True,
            "fields": [{"field_key": "reason"}, {"field_key": "location"}],
        },
        "stamp_text": "hello",
        "stamp_art_enabled": True,
        "stamp_background_present": False,
        "layout_plan": {
            "background_scaling": "modern-background",
            "content_scaling": "modern-content",
            "content_bottom_margin_pt": 4.5,
        },
        "background_layout": {"inner_content_scaling": "legacy-background"},
        "content_layout": {"inner_content_scaling": "legacy-content", "margins": {"bottom": 9}},
        "edge_distances_px": {"content_top_to_border_px": 99},
        "render_capture": {"edge_distances_px": {"content_top_to_border_px": 3.5}},
    }

    projection = project_snapshot(snapshot)

    assert projection.layout_template == "modern-template"
    assert projection.stamp_position == "modern-position"
    assert projection.show_field_names is True
    assert projection.request_field_count == 2
    assert projection.preview_edge_distance("content_top_to_border_px") == 3.5
    assert projection.reservation.stamp_text_length == 5
    assert projection.reservation.stamp_background_present is True
    assert projection.reservation.layout.source == "layout_plan"
    assert projection.reservation.layout.background_scaling == "modern-background"
    assert projection.reservation.layout.content_scaling == "modern-content"
    assert projection.reservation.layout.content_bottom_margin_pt == 4.5


def test_projection_falls_back_to_legacy_and_is_idempotent() -> None:
    snapshot = {
        "signature_appearance": {"layout_template": "legacy", "fields": []},
        "stamp_text": "legacy text",
        "stamp_background_present": True,
        "background_layout": {"inner_content_scaling": "legacy-background"},
        "content_layout": {"inner_content_scaling": "legacy-content", "margins": {"bottom": 7}},
        "edge_distances_px": {"content_bottom_to_border_px": 8},
    }

    first = project_snapshot(snapshot)
    second = project_snapshot(snapshot)

    assert first == second
    assert first.preview_edge_distance("content_bottom_to_border_px") == 8
    assert first.reservation.layout.source == "legacy"
    assert first.reservation.layout.content_bottom_margin_pt == 7
    assert first.reservation.stamp_background_present is True


def test_projection_handles_missing_malformed_and_visible_aliases() -> None:
    assert project_snapshot(None).reservation.stamp_text_length == 0
    malformed = project_snapshot(
        {
            "layout_plan": {"content_bottom_margin_pt": True},
            "render_capture": {"edge_distances_px": {"top": True}},
            "stamp_text": 42,
        }
    )
    assert malformed.preview_edge_distance("top") is None
    assert malformed.reservation.layout.content_bottom_margin_pt is None
    appearance = project_visible_appearance(
        {
            "field_name": "Sig1",
            "text_fragments": ["a", "b"],
            "image_xobjects": [{"name": "Im1", "subtype": "Image", "width": 2, "height": 3}],
            "visible_text_present": True,
        }
    )
    assert appearance.field_name == "Sig1"
    assert appearance.visible_text == "yes"
    assert appearance.text_fragments_summary() == "['a', 'b']"
    assert appearance.image_xobjects_summary() == "[Im1:Image 2x3]"


def test_projection_import_is_free_of_gui_and_render_dependencies() -> None:
    script = """
import sys
import foliaseal.presentation.qt.evidence_snapshot_projection
blocked = ('PyQt', 'PySide6', 'PIL', 'pyhanko', 'foliaseal.presentation.qt.phase3_harness')
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
)
assert not loaded, loaded
"""
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        (source_root, environment.get("PYTHONPATH", ""))
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
