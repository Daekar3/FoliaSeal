from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import foliaseal.presentation.qt.preview_render_evidence_adapters as adapters


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
