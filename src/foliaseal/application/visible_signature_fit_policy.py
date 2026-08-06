"""Neutral fit-gate and rendered-fallback policies for visible signatures."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol

from foliaseal.application.preview_render_boundary import PreviewRasterRenderer
from foliaseal.application.signing_draft_contracts import SigningDraftValidationIssue
from foliaseal.application.visible_signature_layout import (
    SignatureLayoutPlan,
    VisibleSignatureAppearancePort,
    VisibleSignaturePreparation,
)
from foliaseal.domain.models import (
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
)


@dataclass(frozen=True)
class VisibleSignatureRenderedFitRequest:
    """Inputs for one rendered fallback decision."""

    signature_rect: SignatureRect
    appearance: VisibleSignatureAppearancePort
    stamp_text: str
    layout_plan: SignatureLayoutPlan
    render_port: PreviewRasterRenderer | None = None


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


@dataclass(frozen=True)
class VisibleSignatureRenderedFitDecision:
    """Typed result of the rendered fallback probe."""

    accepted: bool


class VisibleSignatureRenderedFitProbe(Protocol):
    """Concrete renderer/raster adapter used by the neutral policy."""

    def single_line_fits(self, request: VisibleSignatureRenderedFitRequest) -> bool: ...

    def horizontal_multi_line_fits(self, request: VisibleSignatureRenderedFitRequest) -> bool: ...


class VisibleSignatureRenderedFitPolicy:
    """Own structural fallback dispatch without owning rendering or validation DTOs."""

    @staticmethod
    def decide(
        request: VisibleSignatureRenderedFitRequest,
        *,
        probe: VisibleSignatureRenderedFitProbe,
    ) -> VisibleSignatureRenderedFitDecision:
        if not request.layout_plan.fit_issues:
            return VisibleSignatureRenderedFitDecision(accepted=True)
        if request.appearance.layout_template == SignatureLayoutTemplate.SINGLE_LINE:
            accepted = probe.single_line_fits(request)
        elif (
            request.appearance.layout_template == SignatureLayoutTemplate.MULTI_LINE
            and request.appearance.image_stamp_path is not None
            and request.appearance.stamp_position
            in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
        ):
            accepted = probe.horizontal_multi_line_fits(request)
        else:
            accepted = False
        return VisibleSignatureRenderedFitDecision(accepted=bool(accepted))


__all__ = [
    "VisibleSignatureFitDecision",
    "VisibleSignatureRenderedFitDecision",
    "VisibleSignatureRenderedFitPolicy",
    "VisibleSignatureRenderedFitProbe",
    "VisibleSignatureRenderedFitRequest",
    "apply_visible_signature_fit_gate",
    "decide_visible_signature_fit",
]
