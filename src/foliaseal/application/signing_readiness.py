"""Pure readiness projection for the active signing workspace."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SigningReadinessStage(StrEnum):
    """Ordered user-facing stages before a signing request can be submitted."""

    SELECT_PRESET = "select_preset"
    SETUP_REQUIRED = "setup_required"
    PLACE_SIGNATURE = "place_signature"
    REVIEW_READINESS = "review_readiness"
    READY = "ready"


class SigningReadinessAction(StrEnum):
    """At most one recommended next action for a readiness state."""

    CHOOSE_SETUP = "choose_setup"
    COMPLETE_SETUP = "complete_setup"
    PLACE_SIGNATURE = "place_signature"
    REVIEW_READINESS = "review_readiness"
    SIGN = "sign"


@dataclass(frozen=True)
class SigningReadinessInputs:
    """Existing setup facts needed by the pure readiness projection."""

    selected_preset_name: str | None
    certificate_selected: bool
    certificate_blocking: bool
    certificate_detail: str
    certificate_warning: bool
    placement_present: bool
    validation_text: str
    ready_to_sign: bool
    has_saved_presets: bool = False


@dataclass(frozen=True)
class SigningReadiness:
    """One immutable state, explanation, and recommended action."""

    stage: SigningReadinessStage
    heading: str
    detail: str
    can_sign: bool
    recommended_action: SigningReadinessAction | None
    caveat: str | None = None


def project_signing_readiness(inputs: SigningReadinessInputs) -> SigningReadiness:
    """Project setup facts into the ordered UI_SPEC readiness vocabulary."""
    if not inputs.selected_preset_name and not inputs.has_saved_presets:
        return SigningReadiness(
            stage=SigningReadinessStage.SELECT_PRESET,
            heading="Select a signature preset",
            detail="Choose or create a signature preset before signing this PDF.",
            can_sign=False,
            recommended_action=SigningReadinessAction.CHOOSE_SETUP,
        )

    if not inputs.certificate_selected or inputs.certificate_blocking:
        detail = inputs.certificate_detail.strip() or inputs.validation_text.strip() or (
            "Select or configure a certificate before signing this PDF."
        )
        return SigningReadiness(
            stage=SigningReadinessStage.SETUP_REQUIRED,
            heading="Setup required",
            detail=detail,
            can_sign=False,
            recommended_action=SigningReadinessAction.COMPLETE_SETUP,
        )

    if not inputs.placement_present:
        return SigningReadiness(
            stage=SigningReadinessStage.PLACE_SIGNATURE,
            heading="Place a visible signature",
            detail=(
                "Place the visible signature on the page before signing. Drag on the page or "
                "enter placement values."
            ),
            can_sign=False,
            recommended_action=SigningReadinessAction.PLACE_SIGNATURE,
        )

    validation_text = inputs.validation_text.strip()
    if not inputs.ready_to_sign:
        return SigningReadiness(
            stage=SigningReadinessStage.REVIEW_READINESS,
            heading="Review readiness",
            detail=validation_text or "Resolve the readiness issue before signing.",
            can_sign=False,
            recommended_action=SigningReadinessAction.REVIEW_READINESS,
        )

    caveat = inputs.certificate_detail.strip() if inputs.certificate_warning else None
    detail = validation_text or "Ready to sign."
    ready_marker = "Ready to sign."
    if ready_marker in detail:
        detail = detail[detail.index(ready_marker) :]
    if caveat and caveat not in detail:
        detail = f"{detail}\n{caveat}"
    return SigningReadiness(
        stage=SigningReadinessStage.READY,
        heading="Ready to sign",
        detail=detail,
        can_sign=True,
        recommended_action=SigningReadinessAction.SIGN,
        caveat=caveat,
    )


__all__ = [
    "SigningReadiness",
    "SigningReadinessAction",
    "SigningReadinessInputs",
    "SigningReadinessStage",
    "project_signing_readiness",
]
