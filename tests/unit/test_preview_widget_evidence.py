from __future__ import annotations

from types import SimpleNamespace

from foliaseal.presentation.qt.preview_widget_evidence import (
    label_alignment_snapshot,
    preview_text_color_rgba,
    project_pixmap_bounds_within_label,
    widget_rect_snapshot,
)


def test_widget_evidence_reads_geometry_and_text_color_without_qt_imports() -> None:
    rect = SimpleNamespace(x=lambda: 2, y=lambda: 3, width=lambda: 40, height=lambda: 20)
    widget = SimpleNamespace(geometry=lambda: rect)
    preview = SimpleNamespace(text_style=SimpleNamespace(text_color_hex="#123456"))

    assert widget_rect_snapshot(widget) == {"x": 2, "y": 3, "width": 40, "height": 20}
    assert preview_text_color_rgba(preview) == (18, 52, 86, 255)


def test_widget_evidence_projects_aligned_pixmap_bounds() -> None:
    label = SimpleNamespace(alignment=lambda: 4)

    result = project_pixmap_bounds_within_label(
        label_bounds={"x": 10, "y": 20, "width": 100, "height": 60},
        pixmap_size={"width": 40, "height": 20},
        alignment=label_alignment_snapshot(label),
        alignment_flag=lambda name: {
            "AlignLeft": 1,
            "AlignRight": 2,
            "AlignTop": 4,
            "AlignBottom": 8,
        }[name],
    )

    assert result == {"x": 40, "y": 20, "width": 40, "height": 20}
