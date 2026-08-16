from __future__ import annotations

from pathlib import Path

from foliaseal.presentation.qt.signed_output_snapshotter import (
    AcceptanceSignedOutputSnapshotter,
    signed_output_preview_comparison_snapshot,
)


def test_signed_output_preview_comparison_snapshot_projects_expected_fields() -> None:
    snapshot = signed_output_preview_comparison_snapshot(
        {
            "page_render_path": "page.png",
            "signature_crop_path": "crop.png",
            "normalized_signature_crop_path": "crop-normalized.png",
            "comparison_path": "cmp.png",
            "preview_crop_bounds_px": {"x": 1},
            "signed_crop_bounds_px": {"x": 2},
            "preview_vs_signed_output_change_ratio": 0.15,
            "preview_vs_signed_output_aspect_ratio_delta": 0.01,
            "preview_text_fragments_match_output": True,
            "annotation_rect_matches_request": True,
            "output_text_bounds_match_preview": True,
            "output_image_presence_matches_preview": False,
            "preview_vs_signed_output_passed": False,
            "comparison_error": "",
            "signature_crop_error": "",
            "page_render_error": "render failed",
            "appearance_layer_comparison": {"text": {"matches": True}},
        }
    )

    assert snapshot == {
        "page_render_path": "page.png",
        "signature_crop_path": "crop.png",
        "normalized_signature_crop_path": "crop-normalized.png",
        "comparison_path": "cmp.png",
        "preview_crop_bounds_px": {"x": 1},
        "signed_crop_bounds_px": {"x": 2},
        "preview_vs_signed_output_change_ratio": 0.15,
        "preview_vs_signed_output_aspect_ratio_delta": 0.01,
        "preview_text_fragments_match_output": True,
        "annotation_rect_matches_request": True,
        "output_text_bounds_match_preview": True,
        "output_image_presence_matches_preview": False,
        "preview_vs_signed_output_passed": False,
        "preview_vs_signed_output_error": "render failed",
        "appearance_layer_comparison": {"text": {"matches": True}},
    }


def test_signed_output_snapshotter_builds_successful_output_bundle(tmp_path: Path) -> None:
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")
    render_calls: list[dict[str, object]] = []

    snapshotter = AcceptanceSignedOutputSnapshotter(
        count_embedded_signatures=lambda path: 2 if path == output_pdf else 0,
        snapshot_output_signature=lambda path: {"field_name": "Signature1", "path": str(path)},
        snapshot_output_verification=lambda path, trust_policy: {
            "cryptographic_validation_passed": True,
            "path": str(path),
            "trust_policy": trust_policy,
        },
        snapshot_visible_signature_appearance=lambda path: {
            "annotation_rect": [1, 2, 3, 4],
            "path": str(path),
        },
        snapshot_signed_output_render=lambda **kwargs: render_calls.append(kwargs)
        or {
            "page_render_path": "page.png",
            "preview_vs_signed_output_passed": True,
        },
    )

    bundle = snapshotter.snapshot_successful_signed_output(
        output_file=output_pdf,
        page_index=3,
        preview_snapshot={"title": "Preview"},
        preview_text="Preview text",
        trust_policy=None,
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_case",
    )

    assert bundle["output_file_exists"] is True
    assert bundle["output_file_size_bytes"] == output_pdf.stat().st_size
    assert bundle["output_signature_count"] == 2
    assert bundle["output_signature_snapshot"]["field_name"] == "Signature1"
    assert bundle["output_verification_snapshot"]["cryptographic_validation_passed"] is True
    assert bundle["output_visible_appearance_snapshot"]["annotation_rect"] == [1, 2, 3, 4]
    assert bundle["signed_output_render_snapshot"] == {
        "page_render_path": "page.png",
        "preview_vs_signed_output_passed": True,
    }
    assert bundle["signed_output_preview_comparison"] == {
        "page_render_path": "page.png",
        "signature_crop_path": None,
        "normalized_signature_crop_path": None,
        "comparison_path": None,
        "preview_crop_bounds_px": None,
        "signed_crop_bounds_px": None,
        "preview_vs_signed_output_change_ratio": None,
        "preview_vs_signed_output_aspect_ratio_delta": None,
        "preview_text_fragments_match_output": None,
        "annotation_rect_matches_request": None,
        "output_text_bounds_match_preview": None,
        "output_image_presence_matches_preview": None,
        "preview_vs_signed_output_passed": True,
        "preview_vs_signed_output_error": None,
        "appearance_layer_comparison": None,
    }
    assert render_calls[0]["output_pdf_path"] == str(output_pdf)
    assert render_calls[0]["page_index"] == 3
    assert render_calls[0]["preview_snapshot"] == {"title": "Preview"}
    assert render_calls[0]["preview_text"] == "Preview text"
    assert render_calls[0]["artifacts_dir"] == str(tmp_path)
    assert render_calls[0]["artifact_basename"] == "signed_case"


def test_signed_output_snapshotter_handles_missing_render_snapshot(tmp_path: Path) -> None:
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")

    snapshotter = AcceptanceSignedOutputSnapshotter(
        count_embedded_signatures=lambda _path: 1,
        snapshot_output_signature=lambda _path: {"field_name": "Signature1"},
        snapshot_output_verification=lambda _path, _trust_policy: {"ok": True},
        snapshot_visible_signature_appearance=lambda _path: {"annotation_rect": [1, 2, 3, 4]},
        snapshot_signed_output_render=lambda **_kwargs: None,
    )

    bundle = snapshotter.snapshot_successful_signed_output(
        output_file=output_pdf,
        page_index=0,
        preview_snapshot={},
        preview_text="Preview text",
        trust_policy=None,
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_case",
    )

    assert bundle["signed_output_render_snapshot"] is None
    assert bundle["signed_output_preview_comparison"] is None
