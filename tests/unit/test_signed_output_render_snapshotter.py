from __future__ import annotations

from pathlib import Path

from PIL import Image

import foliaseal.presentation.qt.interactive_harness as interactive_harness_module
from foliaseal.presentation.qt.preview_image_comparison import PreviewImageComparisonAnalyzer
from foliaseal.presentation.qt.preview_text_geometry import PreviewTextGeometryAnalyzer
from foliaseal.presentation.qt.signed_output_render_snapshotter import (
    AcceptanceSignedOutputRenderSnapshotter,
)


def _snapshotter() -> AcceptanceSignedOutputRenderSnapshotter:
    return interactive_harness_module._build_signed_output_render_snapshotter()


def test_signed_output_render_snapshotter_captures_output_parity(
    monkeypatch, tmp_path: Path
) -> None:
    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 48), color=(255, 255, 255, 255)).save(preview_path)
    analysis_preview_path = tmp_path / "preview_analysis.png"
    Image.new("RGBA", (120, 48), color=(255, 255, 255, 255)).save(analysis_preview_path)
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")

    class _FakeBackend:
        def diagnostics(self):
            return type("_Diag", (), {"available": True, "message": "ok"})()

        def render_page(self, request):
            image = Image.new("RGBA", (300, 400), color=(255, 255, 255, 255))
            return type(
                "_Render",
                (),
                {
                    "width_px": image.width,
                    "height_px": image.height,
                    "rgba_bytes": image.tobytes(),
                },
            )()

        def get_page_geometry(self, document_path: str, page_index: int):
            return type(
                "_Geom",
                (),
                {"crop_box": (0.0, 0.0, 300.0, 400.0), "rotation": 0},
            )()

    monkeypatch.setattr(interactive_harness_module, "QtPdfRenderBackend", _FakeBackend)
    detect_calls: list[dict[str, object]] = []

    def _fake_detect(self, **kwargs):
        detect_calls.append(kwargs)
        return ({"x": 14, "y": 12, "width": 64, "height": 18}, None)

    monkeypatch.setattr(
        PreviewTextGeometryAnalyzer,
        "detect_text_content_bounds_in_preview",
        _fake_detect,
    )
    monkeypatch.setattr(
        PreviewImageComparisonAnalyzer,
        "normalized_image_crop_change_ratio",
        lambda self, **kwargs: 0.1,
    )

    snapshot = _snapshotter().run(
        output_pdf_path=str(output_pdf),
        page_index=0,
        preview_snapshot={
            "image_stamp_path": "/tmp/stamp.png",
            "signature_rect": {
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 120.0,
                "height_pt": 48.0,
            },
            "text_style": {"text_color_hex": "#000000"},
            "fields": [
                {"visible": True, "text": "Morgan Ellery"},
                {"visible": True, "text": "Northwind Ledger Holdings"},
                {"visible": True, "text": "2026-04-11 09:00"},
            ],
            "render_capture": {
                "preview_image_path": str(preview_path),
                "analysis_preview_image_path": str(analysis_preview_path),
                "card_bounds_px": {"x": 0, "y": 0, "width": 120, "height": 48},
                "text_rendered_content_bounds_px": {"x": 14, "y": 12, "width": 64, "height": 18},
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        preview_text="Morgan Ellery | Northwind Ledger Holdings | 2026-04-11 09:00",
        output_visible_appearance_snapshot={
            "annotation_rect": [10.0, 20.0, 130.0, 68.0],
            "image_xobject_count": 1,
            "appearance_has_visible_text": True,
            "appearance_uses_rounded_border": True,
            "text_fragments": [
                "Morgan Ellery",
                "Northwind Ledger Holdings",
                "2026-04-11 09:00",
            ],
        },
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_case",
    )

    assert snapshot is not None
    assert snapshot["signature_crop_path"] is not None
    assert snapshot["normalized_signature_crop_path"] is not None
    assert snapshot["comparison_path"] is not None
    assert snapshot["annotation_rect_matches_request"] is True
    assert snapshot["output_image_presence_matches_preview"] is True
    assert snapshot["output_text_bounds_match_preview"] is True
    assert snapshot["normalized_signed_crop_dimensions_px"] == {"width": 120, "height": 48}
    assert snapshot["preview_appearance_snapshot"] is not None
    assert snapshot["signed_output_appearance_snapshot"] is not None
    assert snapshot["appearance_layer_comparison"] is not None
    assert snapshot["appearance_layer_comparison"]["border"]["matches"] is True
    assert snapshot["appearance_layer_comparison"]["text"]["matches"] is True
    assert snapshot["appearance_layer_comparison"]["stamp"]["matches"] is True
    assert detect_calls[-1]["preview_image_path"] == snapshot["normalized_signature_crop_path"]
    assert detect_calls[-1]["text_widget_bounds"] == {"x": 0, "y": 0, "width": 120, "height": 48}
    assert detect_calls[-1]["reference_text_content_bounds"] == {
        "x": 14,
        "y": 12,
        "width": 64,
        "height": 18,
    }


def test_signed_output_render_snapshotter_normalizes_to_analysis_surface(
    monkeypatch, tmp_path: Path
) -> None:
    pdf_path = tmp_path / "signed.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n%%EOF\n")
    preview_path = tmp_path / "preview.png"
    analysis_preview_path = tmp_path / "preview_analysis.png"
    Image.new("RGBA", (427, 56), (255, 255, 255, 255)).save(preview_path)
    Image.new("RGBA", (320, 42), (255, 255, 255, 255)).save(analysis_preview_path)

    class _FakeBackend:
        def diagnostics(self):
            return type("_Diag", (), {"available": True, "message": "ok"})()

        def render_page(self, request):
            image = Image.new("RGBA", (900, 900), color=(255, 255, 255, 255))
            return type(
                "_Render",
                (),
                {
                    "width_px": image.width,
                    "height_px": image.height,
                    "rgba_bytes": image.tobytes(),
                },
            )()

        def get_page_geometry(self, document_path: str, page_index: int):
            return type(
                "_Geom",
                (),
                {"crop_box": (0.0, 0.0, 300.0, 300.0), "rotation": 0},
            )()

    monkeypatch.setattr(interactive_harness_module, "QtPdfRenderBackend", _FakeBackend)
    monkeypatch.setattr(
        interactive_harness_module,
        "_render_signed_annotation_appearance_direct",
        lambda **_: {
            "image_path": str(tmp_path / "direct.png"),
            "error": None,
        },
    )
    Image.new("RGBA", (320, 42), (255, 255, 255, 255)).save(tmp_path / "direct.png")
    monkeypatch.setattr(
        PreviewTextGeometryAnalyzer,
        "detect_text_content_bounds_in_preview",
        lambda self, **_: ({"x": 3, "y": 0, "width": 280, "height": 18}, None),
    )
    monkeypatch.setattr(
        PreviewTextGeometryAnalyzer,
        "detect_text_line_bounds_in_preview",
        lambda self, **_: (({"x": 3, "y": 0, "width": 280, "height": 9},), None),
    )

    snapshot = _snapshotter().run(
        output_pdf_path=str(pdf_path),
        page_index=0,
        preview_snapshot={
            "signature_rect": {
                "page_index": 0,
                "left_pt": 10,
                "bottom_pt": 20,
                "width_pt": 120,
                "height_pt": 48,
            },
            "render_capture": {
                "preview_image_path": str(preview_path),
                "analysis_preview_image_path": str(analysis_preview_path),
                "card_bounds_px": {"x": 0, "y": 0, "width": 427, "height": 56},
                "analysis_appearance_snapshot": {
                    "image_path": str(analysis_preview_path),
                    "image_size_px": {"width": 320, "height": 42},
                    "container_bounds_px": {"x": 0, "y": 0, "width": 320, "height": 42},
                    "text_bounds_px": {"x": 3, "y": 0, "width": 280, "height": 18},
                    "line_bounds_px": (
                        {"x": 3, "y": 0, "width": 280, "height": 9},
                    ),
                    "stamp_bounds_px": {"x": 6, "y": 8, "width": 54, "height": 13},
                    "text_fragments": ("Morgan Ellery",),
                },
                "stamp_rendered_content_bounds_px": {
                    "x": 8,
                    "y": 10,
                    "width": 74,
                    "height": 18,
                },
                "text_rendered_content_bounds_px": {"x": 3, "y": 0, "width": 280, "height": 18},
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        preview_text="Morgan Ellery",
        output_visible_appearance_snapshot={
            "annotation_rect": [10.0, 20.0, 130.0, 68.0],
            "appearance_has_visible_text": True,
            "appearance_uses_rounded_border": True,
            "image_xobject_count": 1,
            "text_fragments": ["Morgan Ellery"],
        },
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_case",
    )

    assert snapshot is not None
    assert snapshot["preview_crop_bounds_px"] == {"x": 0, "y": 0, "width": 320, "height": 42}
    assert snapshot["normalized_signed_crop_dimensions_px"] == {"width": 320, "height": 42}
    assert snapshot["signed_output_appearance_snapshot"].stamp_bounds_px == {
        "x": 6,
        "y": 8,
        "width": 54,
        "height": 13,
    }
    assert snapshot["appearance_layer_comparison"]["composite"]["matches"] is True
    assert snapshot["appearance_layer_comparison"]["stamp"]["matches"] is True


def test_signed_output_render_snapshotter_composites_transparent_page_over_white(
    monkeypatch, tmp_path: Path
) -> None:
    preview_path = tmp_path / "preview.png"
    Image.new("RGBA", (120, 48), color=(255, 255, 255, 255)).save(preview_path)
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")

    class _FakeBackend:
        def diagnostics(self):
            return type("_Diag", (), {"available": True, "message": "ok"})()

        def render_page(self, request):
            image = Image.new("RGBA", (300, 400), color=(0, 0, 0, 0))
            return type(
                "_Render",
                (),
                {
                    "width_px": image.width,
                    "height_px": image.height,
                    "rgba_bytes": image.tobytes(),
                },
            )()

        def get_page_geometry(self, document_path: str, page_index: int):
            return type(
                "_Geom",
                (),
                {"crop_box": (0.0, 0.0, 300.0, 400.0), "rotation": 0},
            )()

    monkeypatch.setattr(interactive_harness_module, "QtPdfRenderBackend", _FakeBackend)
    monkeypatch.setattr(
        PreviewTextGeometryAnalyzer,
        "detect_text_content_bounds_in_preview",
        lambda self, **kwargs: ({"x": 14, "y": 12, "width": 64, "height": 18}, None),
    )
    monkeypatch.setattr(
        PreviewImageComparisonAnalyzer,
        "normalized_image_crop_change_ratio",
        lambda self, **kwargs: 0.0,
    )

    snapshot = _snapshotter().run(
        output_pdf_path=str(output_pdf),
        page_index=0,
        preview_snapshot={
            "image_stamp_path": None,
            "signature_rect": {
                "left_pt": 10.0,
                "bottom_pt": 20.0,
                "width_pt": 120.0,
                "height_pt": 48.0,
            },
            "text_style": {"text_color_hex": "#000000"},
            "render_capture": {
                "preview_image_path": str(preview_path),
                "card_bounds_px": {"x": 0, "y": 0, "width": 120, "height": 48},
                "text_rendered_content_bounds_px": {"x": 14, "y": 12, "width": 64, "height": 18},
            },
            "box_style": {
                "show_border": True,
                "border_color_hex": "#000000",
                "border_width_pt": 1.0,
                "background_color_hex": "#FFFFFF",
            },
            "layout_template": "single_line",
            "stamp_position": "top",
        },
        preview_text="Morgan Ellery | Northwind Ledger Holdings | 2026-04-11 09:00",
        output_visible_appearance_snapshot={
            "annotation_rect": [10.0, 20.0, 130.0, 68.0],
            "text_fragments": [
                "Morgan Ellery",
                "Northwind Ledger Holdings",
                "2026-04-11 09:00",
            ],
        },
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_white_bg",
    )

    assert snapshot is not None
    page_image = Image.open(snapshot["page_render_path"]).convert("RGBA")
    assert page_image.getpixel((0, 0)) == (255, 255, 255, 255)
