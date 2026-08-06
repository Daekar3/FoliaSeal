from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.signing_draft_contracts import SigningDraftValidationIssue
from foliaseal.application.visible_signature_fit_policy import (
    apply_visible_signature_fit_gate,
    decide_visible_signature_fit,
)


def test_fit_policy_applies_one_decision_to_preparation() -> None:
    issue = SigningDraftValidationIssue(
        code="too_small",
        message="Signature box is too small.",
        field_name="signature_rect",
    )
    @dataclass(frozen=True)
    class Preparation:
        fit_gate_passed: bool
        fit_gate_error: str | None

    preparation = Preparation(fit_gate_passed=True, fit_gate_error=None)

    updated = apply_visible_signature_fit_gate(preparation, decide_visible_signature_fit((issue,)))

    assert updated is not preparation
    assert updated.fit_gate_passed is False
    assert updated.fit_gate_error == issue.message
