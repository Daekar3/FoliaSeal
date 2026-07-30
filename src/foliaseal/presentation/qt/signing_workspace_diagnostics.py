"""Neutral diagnostic read models for the live signing workspace."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
    SigningRequest,
    SigningResult,
)


@dataclass(frozen=True)
class SigningWorkspaceSnapshot:
    """Immutable, Qt-free state observed from one live workspace instant."""

    logical_page_index: int
    signature_rect: SignatureRect | None
    signature_appearance: SignatureAppearance | None
    selected_certificate_configuration_id: str | None
    timestamp_required: bool
    current_request: SigningRequest | None
    sign_action_enabled: bool
    last_signing_result: SigningResult | None
