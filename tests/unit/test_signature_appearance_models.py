from pathlib import Path

import pytest

from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureRect,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_rect,
    build_signing_request,
    invalid_signature_appearance_duplicate_field_order_kwargs,
    invalid_signature_field_binding_hidden_visible_kwargs,
    invalid_signature_field_binding_override_without_text_kwargs,
    invalid_signature_rect_zero_width_kwargs,
)


def test_signing_request_accepts_richer_visible_signature_contract(
    tmp_path: Path,
) -> None:
    rect = build_signature_rect(page_index=2)
    appearance = build_signature_appearance()
    request = build_signing_request(
        tmp_path,
        signature_rect=rect,
        signature_appearance=appearance,
    )

    assert request.signature_rect == rect
    assert request.signature_appearance == appearance
    assert request.has_visible_signature_settings() is True
    assert request.certificate_alias == "signing-cert"


def test_signature_field_binding_rejects_override_without_text() -> None:
    with pytest.raises(ValueError, match="override_text is required"):
        SignatureFieldBinding(
            **invalid_signature_field_binding_override_without_text_kwargs(),
        )


def test_signature_field_binding_rejects_hidden_fields_that_are_visible() -> None:
    with pytest.raises(ValueError, match="Hidden fields cannot be shown"):
        SignatureFieldBinding(
            **invalid_signature_field_binding_hidden_visible_kwargs(),
        )


def test_signature_appearance_rejects_duplicate_field_order() -> None:
    with pytest.raises(
        ValueError,
        match="field_order must contain each signature field key exactly once",
    ):
        build_signature_appearance(
            **invalid_signature_appearance_duplicate_field_order_kwargs(),
        )


def test_signature_appearance_defaults_to_signer_first_field_order() -> None:
    appearance = SignatureAppearance()

    assert appearance.field_order == (
        SignatureFieldKey.DISTINGUISHED_NAME,
        SignatureFieldKey.COMMON_NAME,
        SignatureFieldKey.EMAIL,
        SignatureFieldKey.TITLE,
        SignatureFieldKey.COMPANY,
        SignatureFieldKey.SIGNING_TIME,
        SignatureFieldKey.REASON,
        SignatureFieldKey.LOCATION,
    )


def test_signature_rect_requires_positive_size() -> None:
    with pytest.raises(ValueError, match="width_pt must be a positive finite number"):
        SignatureRect(**invalid_signature_rect_zero_width_kwargs())
