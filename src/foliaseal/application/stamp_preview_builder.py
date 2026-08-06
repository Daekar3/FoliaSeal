"""Neutral construction of a signing-draft preview from canonical stamp text."""

from __future__ import annotations

from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signing_draft_workflow import SigningDraftPreview
from foliaseal.domain.models import SignatureRect


def signing_draft_preview_for_stamp_text(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
) -> SigningDraftPreview:
    """Build the neutral preview payload used by rendered-ink fit checks."""

    title_text, detail_text = stamp_text_preview_parts(
        stamp_text,
        signature_appearance=signature_appearance,
    )
    return SigningDraftPreview(
        title=title_text,
        page_index=signature_rect.page_index,
        signature_rect=signature_rect,
        signer_label_prefix=title_text,
        layout_template=signature_appearance.layout_template,
        stamp_position=signature_appearance.stamp_position,
        timezone_display_mode=signature_appearance.timezone_display_mode,
        show_field_names=signature_appearance.show_field_names,
        datetime_format=signature_appearance.datetime_format,
        text_style=signature_appearance.text_style,
        box_style=signature_appearance.box_style,
        image_stamp_path=signature_appearance.image_stamp_path,
        fields=(),
        detail_text=detail_text,
        issues=(),
        can_submit=True,
    )


def stamp_text_preview_parts(
    stamp_text: str,
    *,
    signature_appearance: SigningBackendAppearance,
) -> tuple[str, str]:
    """Split canonical stamp text into the preview title and detail lines."""

    lines = stamp_text.splitlines()
    if not lines:
        return signature_appearance.signer_label_prefix, ""
    if len(lines) == 1:
        prefix = (signature_appearance.signer_label_prefix or "").strip()
        if prefix and lines[0].startswith(prefix):
            return prefix, lines[0][len(prefix) :].lstrip(" \n|")
        return "", lines[0]
    return lines[0], "\n".join(lines[1:])
