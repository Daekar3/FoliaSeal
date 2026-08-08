"""Focused testing adapters for the signing workspace runtime and properties panel."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
    SigningRequest,
    SigningResult,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import (
    SigningWorkspaceSnapshot,
)
from foliaseal.presentation.qt.signing_workspace_properties_panel import (
    SignaturePropertiesPanel,
)
from foliaseal.presentation.qt.signing_workspace_runtime import (
    SigningWorkspaceRuntime,
)
from foliaseal.presentation.qt.signing_workspace_testing_port import (
    SigningWorkspaceTestingPanelPort,
)

__all__ = ["SigningWorkspaceTestingAdapter", "SigningWorkspaceTestingPanelAdapter"]


class SigningWorkspaceTestingAdapter:
    """Dedicated harness/testing adapter over the live runtime/controller seam."""

    def __init__(
        self,
        *,
        runtime: SigningWorkspaceRuntime,
        properties_panel: SignaturePropertiesPanel,
        last_signing_result: Callable[[], SigningResult | None],
    ) -> None:
        self._runtime = runtime
        self._last_signing_result = last_signing_result
        self._panel = SigningWorkspaceTestingPanelAdapter(properties_panel)

    @property
    def panel(self) -> SigningWorkspaceTestingPanelPort:
        return self._panel

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._runtime.signature_appearance()

    def set_timestamp_required(self, required: bool) -> None:
        self._runtime.set_timestamp_required(required)

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self._runtime.apply_signature_rect_placement(signature_rect)

    def refresh_viewer(self) -> None:
        self._runtime.refresh_viewer()

    def current_request(self) -> SigningRequest | None:
        return self._runtime.current_request()

    def last_signing_result(self) -> SigningResult | None:
        signing_result = self._last_signing_result()
        return signing_result if isinstance(signing_result, SigningResult) else None

    def snapshot(self) -> SigningWorkspaceSnapshot:
        return self._runtime.snapshot(last_signing_result=self.last_signing_result())


class SigningWorkspaceTestingPanelAdapter:
    """Wrap the live properties panel behind a smaller testing-oriented port."""

    def __init__(self, properties_panel: SignaturePropertiesPanel) -> None:
        self._properties_panel = properties_panel

    def set_signature_appearance(self, appearance: SignatureAppearance) -> None:
        self._properties_panel.set_signature_appearance(appearance)

    def set_signature_rect(
        self,
        signature_rect: SignatureRect,
        *,
        notify: bool = True,
    ) -> None:
        self._properties_panel.set_signature_rect(signature_rect, notify=notify)

    def refresh_preview(self) -> Any:
        return self._properties_panel.refresh_preview()

    def preview_text(self) -> str:
        return self._properties_panel.preview_text()

    def validation_text(self) -> str:
        return self._properties_panel.validation_text()

    def capture_preview_render(
        self,
        *,
        preview: Any,
        artifacts_dir: str | None,
        artifact_basename: str,
        build_preview_render_capture_payload: Any,
    ) -> dict[str, Any]:
        return build_preview_render_capture_payload(
            preview_controls=self._properties_panel.preview_controls,
            canonical_preview_render_backend=getattr(
                self._properties_panel,
                "_canonical_preview_render_backend",
                None,
            ),
            preview=preview,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
        )
