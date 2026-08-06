"""Neutral fit-gate policy shared by visible-signature preparation paths."""

from __future__ import annotations

from dataclasses import dataclass, replace

from foliaseal.application.signing_draft_workflow import SigningDraftValidationIssue
from foliaseal.application.visible_signature_layout import VisibleSignaturePreparation


@dataclass(frozen=True)
class VisibleSignatureFitDecision:
    """Immutable result of applying rendered-ink fit issues to a preparation."""

    issues: tuple[SigningDraftValidationIssue, ...]

    @property
    def accepted(self) -> bool:
        return not self.issues


def decide_visible_signature_fit(
    issues: tuple[SigningDraftValidationIssue, ...],
) -> VisibleSignatureFitDecision:
    return VisibleSignatureFitDecision(issues=tuple(issues))


def apply_visible_signature_fit_gate(
    preparation: VisibleSignaturePreparation,
    decision: VisibleSignatureFitDecision,
) -> VisibleSignaturePreparation:
    """Apply one decision consistently to signing, preview, and evidence consumers."""
    return replace(
        preparation,
        fit_gate_passed=decision.accepted,
        fit_gate_error=decision.issues[0].message if decision.issues else None,
    )


__all__ = [
    "VisibleSignatureFitDecision",
    "apply_visible_signature_fit_gate",
    "decide_visible_signature_fit",
]
