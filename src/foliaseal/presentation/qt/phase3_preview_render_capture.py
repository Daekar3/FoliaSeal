"""Typed preview-render capture seam for live and headless harness workspaces."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PreviewRenderCaptureRequest:
    """Inputs shared by live Qt and headless preview capture adapters."""

    preview: Any
    artifacts_dir: str | None
    artifact_basename: str
    workspace: Any | None = None


@dataclass(frozen=True)
class PreviewRenderCaptureResult:
    """Stable render-capture mapping plus artifact/error projections."""

    mapping: Mapping[str, Any]

    @property
    def artifact_paths(self) -> tuple[str, ...]:
        return tuple(
            value
            for key, value in self.mapping.items()
            if key.endswith("_path") and isinstance(value, str)
        )

    @property
    def errors(self) -> tuple[str, ...]:
        return tuple(
            value
            for key, value in self.mapping.items()
            if key.endswith("_error") and isinstance(value, str) and value
        )

    def as_mapping(self) -> dict[str, Any]:
        return dict(self.mapping)


class PreviewRenderCapturePort(Protocol):
    """One typed capture operation used by both workspace adapters."""

    def capture(self, request: PreviewRenderCaptureRequest) -> PreviewRenderCaptureResult | None:
        """Capture one preview and return the existing JSON-ready evidence mapping."""


@dataclass(frozen=True)
class QtPreviewRenderCaptureAdapter:
    """Adapter that keeps Qt workspace anatomy behind the capture seam."""

    callback: Callable[..., Mapping[str, Any] | None]

    def capture(self, request: PreviewRenderCaptureRequest) -> PreviewRenderCaptureResult | None:
        mapping = self.callback(
            workspace=request.workspace,
            preview=request.preview,
            artifacts_dir=request.artifacts_dir,
            artifact_basename=request.artifact_basename,
        )
        return None if mapping is None else PreviewRenderCaptureResult(mapping)


@dataclass(frozen=True)
class HeadlessPreviewRenderCaptureAdapter:
    """Adapter that keeps canonical headless rendering behind the capture seam."""

    callback: Callable[..., Mapping[str, Any] | None]

    def capture(self, request: PreviewRenderCaptureRequest) -> PreviewRenderCaptureResult | None:
        mapping = self.callback(
            preview=request.preview,
            artifacts_dir=request.artifacts_dir,
            artifact_basename=request.artifact_basename,
        )
        return None if mapping is None else PreviewRenderCaptureResult(mapping)


__all__ = [
    "HeadlessPreviewRenderCaptureAdapter",
    "PreviewRenderCapturePort",
    "PreviewRenderCaptureRequest",
    "PreviewRenderCaptureResult",
    "QtPreviewRenderCaptureAdapter",
]
