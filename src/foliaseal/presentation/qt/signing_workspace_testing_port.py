"""Neutral testing contracts for live signing workspace harness consumers."""

from __future__ import annotations

from typing import Any, Protocol

from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
    SigningRequest,
    SigningResult,
)


class SigningWorkspaceTestingPanelPort(Protocol):
    """Narrow harness-facing subset of the signature-properties panel."""

    def set_signature_appearance(self, appearance: SignatureAppearance) -> None: ...
    def set_signature_rect(
        self,
        signature_rect: SignatureRect,
        *,
        notify: bool = True,
    ) -> None: ...
    def refresh_preview(self) -> Any: ...
    def preview_text(self) -> str: ...
    def validation_text(self) -> str: ...
    def capture_preview_render(
        self,
        *,
        preview: Any,
        artifacts_dir: str | None,
        artifact_basename: str,
        build_preview_render_capture_payload: Any,
    ) -> dict[str, Any]: ...


class SigningWorkspaceTestingPort(Protocol):
    """Explicit non-production harness/testing contract for the signing workspace."""

    @property
    def panel(self) -> SigningWorkspaceTestingPanelPort: ...

    def signature_appearance(self) -> SignatureAppearance | None: ...
    def set_timestamp_required(self, required: bool) -> None: ...
    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
    def refresh_viewer(self) -> None: ...
    def current_request(self) -> SigningRequest | None: ...
    def last_signing_result(self) -> SigningResult | None: ...
