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
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningRequest,
    TimestampTrustPolicy,
)
from foliaseal.infra.config.schemas import (
    AppearanceProfile,
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
    PlacementProfile,
    ResolvedSignaturePreset,
    SignaturePreset,
    SignaturePresetCatalog,
)


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
    signer_label_prefix: str | None = "Digitally signed by",
    layout_template: SignatureLayoutTemplate = SignatureLayoutTemplate.MULTI_LINE,
    stamp_position: SignatureStampPosition | None = None,
    timezone_display_mode: SignatureTimezoneDisplayMode = SignatureTimezoneDisplayMode.UTC,
    show_field_names: bool = False,
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
        SignatureFieldKey.TITLE,
        SignatureFieldKey.COMPANY,
        SignatureFieldKey.SIGNING_TIME,
        SignatureFieldKey.REASON,
        SignatureFieldKey.LOCATION,
    )
    effective_stamp_position = stamp_position
    if effective_stamp_position is None:
        effective_stamp_position = (
            SignatureStampPosition.TOP
            if layout_template == SignatureLayoutTemplate.SINGLE_LINE
            else SignatureStampPosition.LEFT
        )
    return SignatureAppearance(
        signer_label_prefix=signer_label_prefix or "",
        layout_template=layout_template,
        stamp_position=effective_stamp_position,
        timezone_display_mode=timezone_display_mode,
        show_field_names=show_field_names,
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
) -> ResolvedSignaturePreset:
    """Build a representative resolved signature preset for shell tests."""
    return ResolvedSignaturePreset.from_parts(
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


def build_signature_preset_catalog(
    *,
    schema_version: int = 1,
    profiles: tuple[ResolvedSignaturePreset, ...] | None = None,
) -> SignaturePresetCatalog:
    """Build a representative named profile catalog."""
    catalog = SignaturePresetCatalog(schema_version=schema_version)
    for profile in profiles or (
        build_signature_preset(name="Default"),
        build_signature_preset(
            name="Compact",
            appearance=build_signature_appearance(
                signer_label_prefix="Signed by",
                show_field_names=False,
            ),
        ),
    ):
        catalog = catalog.upsert_profile(profile)
    return catalog


def build_reference_signature_preset(
    *,
    schema_version: int = 1,
    signature_preset_id: str = "preset-default",
    display_name: str = "Default",
    certificate_configuration_id: str | None = None,
    appearance_profile_id: str | None = "appearance-default",
    placement_profile_id: str | None = "placement-default",
) -> SignaturePreset:
    """Build a canonical reference-only signature preset."""
    return SignaturePreset(
        schema_version=schema_version,
        signature_preset_id=signature_preset_id,
        display_name=display_name,
        certificate_configuration_id=certificate_configuration_id,
        appearance_profile_id=appearance_profile_id,
        placement_profile_id=placement_profile_id,
    )


def build_appearance_profile(
    *,
    schema_version: int = 1,
    appearance_profile_id: str = "appearance-default",
    display_name: str = "Default",
    appearance: SignatureAppearance | None = None,
) -> AppearanceProfile:
    """Build a canonical appearance profile."""
    return AppearanceProfile(
        schema_version=schema_version,
        appearance_profile_id=appearance_profile_id,
        display_name=display_name,
        appearance=appearance or build_signature_appearance(),
    )


def build_placement_profile(
    *,
    schema_version: int = 1,
    placement_profile_id: str = "placement-default",
    display_name: str = "Default",
    placement_defaults: SignaturePlacementDefaults | None = None,
) -> PlacementProfile:
    """Build a canonical placement profile from width/height defaults."""
    return PlacementProfile.from_defaults(
        schema_version=schema_version,
        placement_profile_id=placement_profile_id,
        display_name=display_name,
        placement_defaults=placement_defaults
        or SignaturePlacementDefaults(
            width_pt=220.0,
            height_pt=80.0,
            anchor=SignatureAnchor.BOTTOM_RIGHT,
        ),
    )


def build_managed_certificate(
    *,
    schema_version: int = 1,
    managed_certificate_id: str = "managed-cert-default",
    display_name: str = "Board Secretary 2026",
    storage_filename: str = "cert_default.p12",
    source_kind: str = "created",
    created_at: str = "2026-05-06T00:00:00Z",
    subject_summary: ManagedCertificateSubjectSummary | None = None,
) -> ManagedCertificate:
    """Build a canonical managed certificate record."""
    return ManagedCertificate(
        schema_version=schema_version,
        managed_certificate_id=managed_certificate_id,
        display_name=display_name,
        storage_filename=storage_filename,
        source_kind=source_kind,
        created_at=created_at,
        subject_summary=subject_summary
        or ManagedCertificateSubjectSummary(
            common_name="Morgan Ellery",
            email="morgan@example.com",
            title="Board Secretary",
            company="Northwind Ledger Holdings",
        ),
    )


def build_certificate_configuration(
    *,
    schema_version: int = 1,
    certificate_configuration_id: str = "cert-config-default",
    display_name: str = "Corporate Records Signing",
    managed_certificate_id: str = "managed-cert-default",
    save_password: bool = False,
    password_secret_ref: str | None = None,
    notes: str | None = "Default signing identity",
) -> CertificateConfiguration:
    """Build a canonical certificate configuration."""
    return CertificateConfiguration(
        schema_version=schema_version,
        certificate_configuration_id=certificate_configuration_id,
        display_name=display_name,
        managed_certificate_id=managed_certificate_id,
        save_password=save_password,
        password_secret_ref=password_secret_ref,
        notes=notes,
    )


def build_certificate_catalog(
    *,
    schema_version: int = 1,
    managed_certificates: tuple[ManagedCertificate, ...] | None = None,
    certificate_configurations: tuple[CertificateConfiguration, ...] | None = None,
) -> CertificateCatalog:
    """Build a canonical certificate catalog."""
    managed_certificate = build_managed_certificate()
    return CertificateCatalog(
        schema_version=schema_version,
        managed_certificates=managed_certificates or (managed_certificate,),
        certificate_configurations=certificate_configurations
        or (
            build_certificate_configuration(
                managed_certificate_id=managed_certificate.managed_certificate_id,
            ),
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
    trust_policy: TimestampTrustPolicy | None = None,
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
        trust_policy=trust_policy,
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
