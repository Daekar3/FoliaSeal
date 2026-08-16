from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

import foliaseal.presentation.qt.preview_render_evidence_adapters as adapters
from foliaseal.presentation.qt.preview_render_evidence_projection import (
    PreviewEvidenceFrame,
    assemble_preview_evidence,
    build_preview_analysis_request,
)


def test_qt_adapter_forwards_the_typed_dependency_bundle(monkeypatch) -> None:
    dependencies = object()
    expected = {"preview_image_path": "capture.png"}
    observed = {}

    def fake_capture(**kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(adapters, "build_qt_preview_render_capture_payload", fake_capture)

    result = adapters.QtPreviewRenderEvidenceAdapter(dependencies).capture_payload(
        preview_controls="controls",
        canonical_preview_render_backend="backend",
        preview="preview",
        artifacts_dir="artifacts",
        artifact_basename="example",
    )

    assert result is expected
    assert observed == {
        "dependencies": dependencies,
        "preview_controls": "controls",
        "canonical_preview_render_backend": "backend",
        "preview": "preview",
        "artifacts_dir": "artifacts",
        "artifact_basename": "example",
    }


def test_headless_adapter_forwards_the_typed_dependency_bundle(monkeypatch) -> None:
    dependencies = object()
    expected = {"preview_image_path": "capture.png"}
    observed = {}

    def fake_capture(**kwargs):
        observed.update(kwargs)
        return expected

    monkeypatch.setattr(adapters, "capture_headless_preview_render", fake_capture)

    result = adapters.HeadlessPreviewRenderEvidenceAdapter(dependencies).capture_payload(
        preview="preview",
        artifacts_dir="artifacts",
        artifact_basename="example",
    )

    assert result is expected
    assert observed == {
        "dependencies": dependencies,
        "preview": "preview",
        "artifacts_dir": "artifacts",
        "artifact_basename": "example",
    }


def test_qt_capture_cleans_analysis_snapshot_when_payload_raises(monkeypatch) -> None:
    snapshot = object()
    cleaned: list[object] = []

    def fake_build(**kwargs):
        kwargs["register_analysis_snapshot"](snapshot)
        raise RuntimeError("analysis failed")

    monkeypatch.setattr(adapters, "_build_qt_preview_render_capture_payload", fake_build)
    dependencies = SimpleNamespace(
        cleanup_canonical_preview_tempdir=cleaned.append,
    )

    with pytest.raises(RuntimeError, match="analysis failed"):
        adapters.build_qt_preview_render_capture_payload(
            dependencies=dependencies,
            preview_controls=None,
            canonical_preview_render_backend=None,
            preview=None,
            artifacts_dir=None,
            artifact_basename="example",
        )

    assert cleaned == [snapshot]


def test_qt_capture_cleans_analysis_snapshot_on_success(monkeypatch) -> None:
    snapshot = object()
    cleaned: list[object] = []

    def fake_build(**kwargs):
        kwargs["register_analysis_snapshot"](snapshot)
        return {"analysis_preview_image_path": "artifacts/example_analysis.png"}

    monkeypatch.setattr(adapters, "_build_qt_preview_render_capture_payload", fake_build)
    dependencies = SimpleNamespace(
        cleanup_canonical_preview_tempdir=cleaned.append,
    )

    result = adapters.build_qt_preview_render_capture_payload(
        dependencies=dependencies,
        preview_controls=None,
        canonical_preview_render_backend=None,
        preview=None,
        artifacts_dir="artifacts",
        artifact_basename="example",
    )

    assert result["analysis_preview_image_path"].endswith("example_analysis.png")
    assert cleaned == [snapshot]


def test_headless_capture_cleans_snapshot_when_payload_raises(monkeypatch) -> None:
    snapshot = object()
    cleaned: list[object] = []

    def fake_build(**kwargs):
        kwargs["register_snapshot"](snapshot)
        raise RuntimeError("payload failed")

    monkeypatch.setattr(adapters, "_capture_headless_preview_render", fake_build)
    dependencies = SimpleNamespace(
        cleanup_canonical_preview_tempdir=cleaned.append,
    )

    with pytest.raises(RuntimeError, match="payload failed"):
        adapters.capture_headless_preview_render(
            dependencies=dependencies,
            preview=None,
            artifacts_dir=None,
            artifact_basename="example",
        )

    assert cleaned == [snapshot]


def test_headless_capture_cleans_snapshot_on_success(monkeypatch) -> None:
    snapshot = object()
    cleaned: list[object] = []

    def fake_build(**kwargs):
        kwargs["register_snapshot"](snapshot)
        return {"preview_image_path": "artifacts/example.png"}

    monkeypatch.setattr(adapters, "_capture_headless_preview_render", fake_build)
    dependencies = SimpleNamespace(
        cleanup_canonical_preview_tempdir=cleaned.append,
    )

    result = adapters.capture_headless_preview_render(
        dependencies=dependencies,
        preview=None,
        artifacts_dir="artifacts",
        artifact_basename="example",
    )

    assert result["preview_image_path"].endswith("example.png")
    assert cleaned == [snapshot]


def test_headless_capture_preserves_copied_image_after_snapshot_cleanup(
    monkeypatch, tmp_path
) -> None:
    canonical_root = Path(tempfile.mkdtemp(prefix="foliaseal-canonical-preview-"))
    source_path = canonical_root / "preview.png"
    Image.new("RGB", (2, 2), (12, 34, 56)).save(source_path)
    snapshot = SimpleNamespace(
        image_path=str(source_path),
        width_px=2,
        height_px=2,
        text_area_bounds_px={"x": 0, "y": 0, "width": 2, "height": 1},
        stamp_area_bounds_px={"x": 0, "y": 1, "width": 2, "height": 1},
        text_bounds_px={"x": 0, "y": 0, "width": 2, "height": 1},
        stamp_bounds_px={"x": 0, "y": 1, "width": 2, "height": 1},
        appearance_snapshot=None,
    )

    monkeypatch.setattr(
        adapters,
        "build_preview_analysis_request",
        lambda **_: object(),
    )
    monkeypatch.setattr(
        adapters,
        "assemble_preview_evidence",
        lambda *, frame, **_: {"preview_image_path": frame.preview_image_path},
    )
    dependencies = SimpleNamespace(
        render_canonical_signature_preview=lambda _preview: snapshot,
        build_preview_analysis_engine=lambda: SimpleNamespace(
            analyze=lambda _request: SimpleNamespace(as_mapping=lambda: {})
        ),
        preview_text_color_rgba=lambda _preview: (0, 0, 0, 255),
        preview_padding_for_capture=lambda _preview: 0,
        cleanup_canonical_preview_tempdir=lambda value: shutil.rmtree(
            Path(value.image_path).parent, ignore_errors=True
        ),
    )
    output_dir = tmp_path / "artifacts"

    result = adapters.capture_headless_preview_render(
        dependencies=dependencies,
        preview=object(),
        artifacts_dir=str(output_dir),
        artifact_basename="example",
    )

    copied_path = Path(result["preview_image_path"])
    assert copied_path.exists()
    with Image.open(copied_path) as copied_image:
        assert copied_image.size == (2, 2)
    assert not canonical_root.exists()


def test_adapter_module_imports_without_loading_qt() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    import_statement = (
        "import sys; import foliaseal.presentation.qt.preview_render_evidence_adapters; "
        "print('PySide6' in sys.modules)"
    )
    result = subprocess.run(
        [sys.executable, "-c", import_statement],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "False"


def _projection_frame() -> PreviewEvidenceFrame:
    return PreviewEvidenceFrame(
        preview=SimpleNamespace(box_style=None),
        artifacts_dir="artifacts",
        artifact_basename="example",
        preview_image_path="preview.png",
        analysis_image_path="analysis.png",
        analysis_request_image_path="analysis.png",
        image_error=None,
        card_bounds={"x": 0, "y": 0, "width": 80, "height": 40},
        body_bounds={"x": 0, "y": 0, "width": 80, "height": 40},
        detail_bounds={"x": 1, "y": 2, "width": 70, "height": 20},
        stamp_bounds={"x": 1, "y": 24, "width": 70, "height": 8},
        text_widget_bounds={"x": 1, "y": 2, "width": 70, "height": 20},
        analysis_detection_bounds={"x": 1, "y": 2, "width": 70, "height": 20},
        stamp_band_bounds={"x": 1, "y": 24, "width": 70, "height": 8},
        stamp_pixmap_bounds={"x": 2, "y": 25, "width": 68, "height": 6},
        stamp_pixmap_size={"width": 68, "height": 6},
        stamp_content_bounds_override=None,
        structural_text_content_bounds=None,
        structural_line_bounds=(),
        reference_text_content_bounds=None,
        reference_text_detection_error=None,
        text_color_rgba=(0, 0, 0, 255),
        active_label=None,
        preview_padding_px=6,
        layout_spacing_px=0,
        stamp_alignment="center",
        single_body_bounds={"x": 0, "y": 0, "width": 80, "height": 40},
        multi_body_bounds={"x": 0, "y": 0, "width": 80, "height": 40},
        detail_label_bounds={"x": 1, "y": 2, "width": 70, "height": 20},
        stamp_label_bounds={"x": 1, "y": 24, "width": 70, "height": 8},
        multi_detail_bounds={"x": 1, "y": 2, "width": 70, "height": 20},
        multi_stamp_bounds={"x": 1, "y": 24, "width": 70, "height": 8},
        detail_text_size_hint=None,
        canonical_snapshot=None,
        analysis_snapshot=None,
        prefer_analysis_snapshot=False,
        fallback_snapshot_image_path_to_base=False,
    )


def _projection_analysis_values() -> dict[str, object]:
    return {
        "stamp_source_image_size_px": {"width": 68, "height": 6},
        "stamp_source_content_bounds_px": {"x": 2, "y": 25, "width": 68, "height": 6},
        "stamp_source_content_error": None,
        "stamp_rendered_content_bounds_px": {"x": 3, "y": 26, "width": 64, "height": 4},
        "stamp_band_bounds_px": {"x": 1, "y": 24, "width": 70, "height": 8},
        "stamp_rendered_pixmap_bounds_px": {"x": 2, "y": 25, "width": 68, "height": 6},
        "text_rendered_content_bounds_px": {"x": 4, "y": 5, "width": 60, "height": 12},
        "text_rendered_line_bounds_px": ({"x": 4, "y": 5, "width": 60, "height": 5},),
        "text_content_detection_error": None,
        "text_line_detection_error": None,
        "edge_distances_px": {"top": 1, "right": 2, "bottom": 3, "left": 4},
        "text_widget_image_sha256": "abc123",
        "requested_text_font_family": "Sans Serif",
        "stamp_warning": "kept",
    }


def test_projection_boundary_builds_request_and_preserves_mapping_policy() -> None:
    frame = _projection_frame()
    request_type = type(
        "Request",
        (),
        {"__init__": lambda self, **kwargs: self.__dict__.update(kwargs)},
    )
    dependencies = SimpleNamespace(
        preview_analysis_request_type=request_type,
        appearance_snapshot_type=object,
        jsonable_capture=lambda value: value,
        write_stamp_debug_overlay=lambda **kwargs: None,
        write_text_debug_overlay=lambda **kwargs: None,
    )

    request = build_preview_analysis_request(frame=frame, dependencies=dependencies)
    assert request.analysis_image_path == "analysis.png"
    assert request.analysis_detection_bounds == frame.analysis_detection_bounds
    payload = assemble_preview_evidence(
        frame=frame,
        analysis_values=_projection_analysis_values(),
        dependencies=dependencies,
    )

    assert payload["preview_image_path"] == "preview.png"
    assert payload["analysis_preview_image_path"] == "analysis.png"
    assert payload["stamp_warning"] == "kept"
    assert payload["text_widget_image_sha256"] == "abc123"
    assert payload["stamp_debug_image_path"] == "artifacts/example_stamp_debug.png"
    assert payload["text_debug_image_path"] == "artifacts/example_text_debug.png"


def test_projection_module_imports_without_loading_qt() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import foliaseal.presentation.qt.preview_render_evidence_projection; "
            "print('PySide6' in sys.modules)",
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "False"
