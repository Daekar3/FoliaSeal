"""Reusable Phase 3 test builders for signature appearance and signing data."""

from __future__ import annotations

from pathlib import Path

from foliaseal.domain.models import (
    SignatureAnchor,
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignaturePlacementDefaults,
    SignatureRect,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningRequest,
)
from foliaseal.infra.config.schemas import SignaturePreset


def build_signature_rect(
    *,
    page_index: int = 1,
    left_pt: float = 24.0,
    bottom_pt: float = 18.0,
    width_pt: float = 220.0,
    height_pt: float = 80.0,
) -> SignatureRect:
    """Build a valid PDF-space signature rectangle."""
    return SignatureRect(
        page_index=page_index,
        left_pt=left_pt,
        bottom_pt=bottom_pt,
        width_pt=width_pt,
        height_pt=height_pt,
    )


def build_signature_field_binding(
    *,
    source: SignatureFieldSource = SignatureFieldSource.DERIVED,
    show_in_visible_appearance: bool = True,
    override_text: str | None = None,
    display_label: str | None = None,
) -> SignatureFieldBinding:
    """Build a valid field binding for one appearance field."""
    return SignatureFieldBinding(
        source=source,
        show_in_visible_appearance=show_in_visible_appearance,
        override_text=override_text,
        display_label=display_label,
    )


def build_signature_appearance(
    *,
    signer_label_prefix: str = "Digitally signed by",
    layout_template: SignatureLayoutTemplate = SignatureLayoutTemplate.MULTI_LINE,
    timezone_display_mode: SignatureTimezoneDisplayMode = SignatureTimezoneDisplayMode.UTC,
    datetime_format: str = "%Y-%m-%d %H:%M",
    field_order: tuple[SignatureFieldKey, ...] | None = None,
    distinguished_name: SignatureFieldBinding | None = None,
    common_name: SignatureFieldBinding | None = None,
    email: SignatureFieldBinding | None = None,
    signing_time: SignatureFieldBinding | None = None,
    reason: SignatureFieldBinding | None = None,
    location: SignatureFieldBinding | None = None,
    title: SignatureFieldBinding | None = None,
    company: SignatureFieldBinding | None = None,
    text_style: SignatureTextStyle | None = None,
    box_style: SignatureBoxStyle | None = None,
    image_stamp_path: str | None = None,
) -> SignatureAppearance:
    """Build a representative valid signature appearance."""
    default_field_order = (
        SignatureFieldKey.DISTINGUISHED_NAME,
        SignatureFieldKey.COMMON_NAME,
        SignatureFieldKey.EMAIL,
        SignatureFieldKey.SIGNING_TIME,
        SignatureFieldKey.REASON,
        SignatureFieldKey.LOCATION,
        SignatureFieldKey.TITLE,
        SignatureFieldKey.COMPANY,
    )
    return SignatureAppearance(
        signer_label_prefix=signer_label_prefix,
        layout_template=layout_template,
        timezone_display_mode=timezone_display_mode,
        datetime_format=datetime_format,
        field_order=field_order or default_field_order,
        distinguished_name=distinguished_name or build_signature_field_binding(),
        common_name=common_name or build_signature_field_binding(),
        email=email
        or build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="alice@example.com",
        ),
        signing_time=signing_time or build_signature_field_binding(),
        reason=reason
        or build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Approved",
        ),
        location=location
        or build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        title=title
        or build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Director",
        ),
        company=company
        or build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="FoliaSeal",
        ),
        text_style=text_style
        or SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=9.5,
            bold=True,
            italic=False,
            text_color_hex="#123456",
        ),
        box_style=box_style
        or SignatureBoxStyle(
            show_border=True,
            border_color_hex="#333333",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=image_stamp_path,
    )


def build_signature_preset(
    *,
    schema_version: int = 1,
    name: str = "default",
    appearance: SignatureAppearance | None = None,
    placement_defaults: SignaturePlacementDefaults | None = None,
) -> SignaturePreset:
    """Build a representative signature preset with nested appearance data."""
    return SignaturePreset(
        schema_version=schema_version,
        name=name,
        appearance=appearance or build_signature_appearance(),
        placement_defaults=placement_defaults
        or SignaturePlacementDefaults(
            width_pt=220.0,
            height_pt=80.0,
            anchor=SignatureAnchor.BOTTOM_RIGHT,
        ),
    )


def build_signing_request(
    base_path: Path,
    *,
    input_name: str = "input.pdf",
    output_name: str = "output.pdf",
    certificate_name: str = "cert.p12",
    passphrase: str = "secret",
    tsa_url: str = "https://tsa.example.com",
    timestamp_required: bool = True,
    certificate_alias: str | None = "signing-cert",
    signature_rect: SignatureRect | None = None,
    signature_appearance: SignatureAppearance | None = None,
) -> SigningRequest:
    """Build a signing request using stable defaults for unit tests."""
    return SigningRequest(
        input_pdf_path=str(base_path / input_name),
        output_pdf_path=str(base_path / output_name),
        certificate_path=str(base_path / certificate_name),
        passphrase=passphrase,
        tsa_url=tsa_url,
        timestamp_required=timestamp_required,
        certificate_alias=certificate_alias,
        signature_rect=signature_rect or build_signature_rect(),
        signature_appearance=signature_appearance or build_signature_appearance(),
    )


def invalid_signature_field_binding_override_without_text_kwargs() -> dict[str, object]:
    """Return kwargs that intentionally violate the override-text rule."""
    return {
        "source": SignatureFieldSource.OVERRIDE,
        "show_in_visible_appearance": True,
        "override_text": None,
    }


def invalid_signature_field_binding_hidden_visible_kwargs() -> dict[str, object]:
    """Return kwargs that intentionally violate the hidden-field rule."""
    return {
        "source": SignatureFieldSource.HIDDEN,
        "show_in_visible_appearance": True,
    }


def invalid_signature_appearance_duplicate_field_order_kwargs() -> dict[str, object]:
    """Return kwargs that intentionally violate the field-order uniqueness rule."""
    return {
        "field_order": (
            SignatureFieldKey.COMMON_NAME,
            SignatureFieldKey.COMMON_NAME,
            SignatureFieldKey.EMAIL,
            SignatureFieldKey.SIGNING_TIME,
            SignatureFieldKey.REASON,
            SignatureFieldKey.LOCATION,
            SignatureFieldKey.TITLE,
            SignatureFieldKey.COMPANY,
        ),
    }


def invalid_signature_rect_zero_width_kwargs() -> dict[str, object]:
    """Return kwargs that intentionally violate the rectangle size rule."""
    return {
        "page_index": 0,
        "left_pt": 0.0,
        "bottom_pt": 0.0,
        "width_pt": 0.0,
        "height_pt": 10.0,
    }
