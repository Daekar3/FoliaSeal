"""Typed fit-validation adapter for visible-signature semantics."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from foliaseal.application.signing_draft_contracts import (
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
)

if TYPE_CHECKING:
    from foliaseal.application.visible_signature_semantics import VisibleSignatureFitRequest


class BackendVisibleSignatureFitValidator:
    """Adapt the backend fit gate to the neutral semantics validator protocol.

    The backend remains the authority for rendered-ink measurement and PyHanko style
    materialization. Those imports stay inside ``validate`` so importing this adapter
    does not pull infrastructure into the application boundary.
    """

    def __init__(self, *, certificate_path: str) -> None:
        self._certificate_path = certificate_path

    def validate(
        self,
        request: VisibleSignatureFitRequest,
    ) -> tuple[SigningDraftValidationIssue, ...]:
        if not Path(self._certificate_path).exists():
            return ()

        from foliaseal.application.phase3_signing_backend import (
            validate_visible_signature_fit,
        )
        from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
        from foliaseal.application.stamp_background import stamp_background_for_path

        try:
            stamp_background = stamp_background_for_path(request.appearance.image_stamp_path)
            appearance = request.appearance
            if not isinstance(appearance, SigningBackendAppearance):
                appearance = SigningBackendAppearance.from_signature_appearance(appearance)
            return validate_visible_signature_fit(
                signature_rect=request.signature_rect,
                signature_appearance=appearance,
                stamp_text=request.stamp_text,
                stamp_background=stamp_background,
            )
        except Exception as exc:
            return (
                SigningDraftValidationIssue(
                    code="visible_signature_layout_unavailable",
                    message=str(exc),
                    field_name="signature_appearance",
                    severity=SigningDraftValidationSeverity.ERROR,
                ),
            )


__all__ = ["BackendVisibleSignatureFitValidator"]
