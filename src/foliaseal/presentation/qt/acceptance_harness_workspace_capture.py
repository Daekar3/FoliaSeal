"""Qt-free snapshot assembly for the Acceptance harness workspace boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from foliaseal.domain.models import SigningRequest, SigningResult


@dataclass(frozen=True)
class AcceptanceHarnessWorkspaceSnapshot:
    """Stable workspace capture shared by live-shell and headless harness paths."""

    current_request: SigningRequest | None
    last_signing_result: SigningResult | None
    capture_index: int
    capture_kind: str
    capture_label: str | None
    preview_snapshot: dict[str, Any]
    preview_text: str
    validation_text: str
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    backend_reservation_error: str | None

    def as_mapping(self) -> dict[str, Any]:
        payload = {
            "capture_index": self.capture_index,
            "capture_kind": self.capture_kind,
            "preview_snapshot": self.preview_snapshot,
            "preview_text": self.preview_text,
            "validation_text": self.validation_text,
            "sign_request_snapshot": self.sign_request_snapshot,
            "backend_reservation_snapshot": self.backend_reservation_snapshot,
            "backend_reservation_error": self.backend_reservation_error,
        }
        if self.capture_label is not None:
            payload["capture_label"] = self.capture_label
        return payload


@dataclass(frozen=True)
class AcceptanceHarnessWorkspaceCaptureInput:
    """Already-collected values for one workspace snapshot."""

    current_request: SigningRequest | None
    last_signing_result: SigningResult | None
    capture_index: int
    capture_kind: str
    capture_label: str | None
    preview_snapshot: dict[str, Any]
    preview_text: str
    validation_text: str
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    backend_reservation_error: str | None


class AcceptanceHarnessWorkspaceCaptureService:
    """Build the stable workspace snapshot without owning any runtime effects."""

    def build_snapshot(
        self, data: AcceptanceHarnessWorkspaceCaptureInput
    ) -> AcceptanceHarnessWorkspaceSnapshot:
        return AcceptanceHarnessWorkspaceSnapshot(
            current_request=data.current_request,
            last_signing_result=data.last_signing_result,
            capture_index=data.capture_index,
            capture_kind=data.capture_kind,
            capture_label=data.capture_label,
            preview_snapshot=data.preview_snapshot,
            preview_text=data.preview_text,
            validation_text=data.validation_text,
            sign_request_snapshot=data.sign_request_snapshot,
            backend_reservation_snapshot=data.backend_reservation_snapshot,
            backend_reservation_error=data.backend_reservation_error,
        )
