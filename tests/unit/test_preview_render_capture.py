from __future__ import annotations

from foliaseal.presentation.qt.preview_render_capture import (
    HeadlessPreviewRenderCaptureAdapter,
    PreviewRenderCaptureRequest,
    QtPreviewRenderCaptureAdapter,
)


def test_headless_capture_adapter_projects_mapping_and_artifact_paths() -> None:
    calls: list[dict[str, object]] = []

    def capture(**kwargs):
        calls.append(kwargs)
        return {
            "preview_image_path": "/tmp/preview.png",
            "text_debug_image_path": "/tmp/text.png",
            "preview_image_error": None,
        }

    result = HeadlessPreviewRenderCaptureAdapter(callback=capture).capture(
        PreviewRenderCaptureRequest(
            preview="preview",
            artifacts_dir="/tmp",
            artifact_basename="scenario",
        )
    )

    assert result is not None
    assert calls == [
        {"preview": "preview", "artifacts_dir": "/tmp", "artifact_basename": "scenario"}
    ]
    assert result.as_mapping()["preview_image_path"] == "/tmp/preview.png"
    assert result.artifact_paths == ("/tmp/preview.png", "/tmp/text.png")
    assert result.errors == ()


def test_qt_capture_adapter_forwards_workspace_without_changing_payload() -> None:
    workspace = object()
    result = QtPreviewRenderCaptureAdapter(
        callback=lambda **kwargs: {
            "preview_image_error": "capture failed",
            "stamp_debug_image_path": "/tmp/stamp.png",
            "workspace_seen": kwargs["workspace"] is workspace,
        }
    ).capture(
        PreviewRenderCaptureRequest(
            preview="preview",
            artifacts_dir=None,
            artifact_basename="scenario",
            workspace=workspace,
        )
    )

    assert result is not None
    assert result.as_mapping()["workspace_seen"] is True
    assert result.errors == ("capture failed",)
    assert result.artifact_paths == ("/tmp/stamp.png",)
