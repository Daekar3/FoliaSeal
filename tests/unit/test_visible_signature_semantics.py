from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from foliaseal.application.signing_draft_workflow import (
    SigningDraftValidationIssue,
)
from foliaseal.application.visible_signature_semantics import (
    CertificateFieldValues,
    VisibleSignatureFitRequest,
    VisibleSignatureSemanticsMode,
    VisibleSignatureSemanticsRequest,
    VisibleSignatureSemanticsService,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureTimezoneDisplayMode,
)


@dataclass(frozen=True)
class _FakeCertificateReader:
    values: CertificateFieldValues

    def read_fields(self, certificate_path: str, passphrase: str) -> CertificateFieldValues:
        assert certificate_path == "/tmp/cert.p12"
        assert passphrase == "secret"
        return self.values


@dataclass(frozen=True)
class _FixedClock:
    timestamp: datetime

    def now(self, mode: SignatureTimezoneDisplayMode) -> datetime:
        assert mode == SignatureTimezoneDisplayMode.UTC
        return self.timestamp


@dataclass
class _RecordingFitValidator:
    issues: tuple[SigningDraftValidationIssue, ...] = ()
    requests: list[VisibleSignatureFitRequest] = field(default_factory=list)

    def validate(
        self,
        request: VisibleSignatureFitRequest,
    ) -> tuple[SigningDraftValidationIssue, ...]:
        self.requests.append(request)
        return self.issues


def _request(
    *,
    appearance: SignatureAppearance,
    mode: VisibleSignatureSemanticsMode = VisibleSignatureSemanticsMode.PREVIEW,
    signature_rect: SignatureRect | None = None,
) -> VisibleSignatureSemanticsRequest:
    return VisibleSignatureSemanticsRequest(
        certificate_path="/tmp/cert.p12",
        passphrase="secret",
        signature_rect=signature_rect,
        appearance=appearance,
        mode=mode,
    )


def test_semantics_resolves_preview_fields_and_wrapped_block_text() -> None:
    service = VisibleSignatureSemanticsService(
        certificate_reader=_FakeCertificateReader(
            CertificateFieldValues(
                available=True,
                values={
                    SignatureFieldKey.DISTINGUISHED_NAME: (
                        "Alice Example, alice@example.com, Board Secretary, "
                        "FoliaSeal, Wytheville, Virginia, US"
                    ),
                    SignatureFieldKey.COMMON_NAME: "Alice Example",
                    SignatureFieldKey.EMAIL: "alice@example.com",
                    SignatureFieldKey.TITLE: "Board Secretary",
                    SignatureFieldKey.COMPANY: "FoliaSeal",
                    SignatureFieldKey.LOCATION: "Wytheville, Virginia, US",
                },
            )
        ),
        clock=_FixedClock(datetime(2026, 5, 1, 14, 30, tzinfo=UTC)),
    )
    appearance = SignatureAppearance(
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
        timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
        datetime_format="%Y-%m-%d %H:%M",
        common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        email=SignatureFieldBinding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="override@example.com",
        ),
        title=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        company=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        signing_time=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        reason=SignatureFieldBinding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Approved for release",
        ),
        location=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
    )

    semantics = service.resolve(_request(appearance=appearance))

    assert [field.field_key for field in semantics.fields] == list(appearance.field_order)
    assert semantics.fields[1].text == "Alice Example"
    assert semantics.fields[1].hint == "from certificate"
    assert semantics.fields[2].text == "override@example.com"
    assert semantics.fields[3].text == "Board Secretary"
    assert semantics.fields[4].text == "FoliaSeal"
    assert semantics.fields[5].text == "2026-05-01 14:30"
    assert semantics.fields[5].hint == "sign time"
    assert semantics.fields[7].visible is False
    assert semantics.text.title_text == "Digitally signed by"
    assert semantics.text.detail_text == (
        "Alice Example, alice@example.com, Board Secretary, FoliaSeal, "
        "Wytheville, Virginia, US\n"
        "Alice Example\n"
        "override@example.com Board Secretary FoliaSeal 2026-05-01 14:30 "
        "Approved for release"
    )
    assert semantics.text.stamp_text == (
        "Digitally signed by\n"
        "Alice Example, alice@example.com, Board Secretary, FoliaSeal, "
        "Wytheville, Virginia, US\n"
        "Alice Example\n"
        "override@example.com Board Secretary FoliaSeal 2026-05-01 14:30 "
        "Approved for release"
    )
    assert semantics.text.metadata_reason == "Approved for release"
    assert semantics.text.metadata_location is None
    assert semantics.text.metadata_contact_info == "override@example.com"
    assert semantics.can_submit_visible_signature is True


def test_semantics_uses_fallback_preview_labels_when_certificate_is_unavailable() -> None:
    service = VisibleSignatureSemanticsService(
        certificate_reader=_FakeCertificateReader(
            CertificateFieldValues(available=False, values={})
        ),
        clock=_FixedClock(datetime(2026, 5, 1, 14, 30, tzinfo=UTC)),
    )
    appearance = SignatureAppearance(
        signer_label_prefix="",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        common_name=SignatureFieldBinding(
            source=SignatureFieldSource.DERIVED,
            display_label="Certificate common name",
        ),
        email=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        signing_time=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
    )

    semantics = service.resolve(_request(appearance=appearance))

    assert semantics.fields[1].text == "Certificate common name"
    assert semantics.fields[1].hint == "from certificate"
    assert semantics.fields[2].text == "Email"
    assert semantics.fields[5].visible is False
    assert semantics.text.detail_text == (
        "Distinguished name | Certificate common name | Email | Title | Company | "
        "Reason | Location"
    )
    assert semantics.text.stamp_text == semantics.text.detail_text


def test_semantics_composes_multiline_text_with_field_names_and_escapes_percent() -> None:
    service = VisibleSignatureSemanticsService(
        certificate_reader=_FakeCertificateReader(
            CertificateFieldValues(
                available=True,
                values={
                    SignatureFieldKey.COMMON_NAME: "Alice 100%",
                    SignatureFieldKey.LOCATION: "Richmond",
                },
            )
        ),
        clock=_FixedClock(datetime(2026, 5, 1, 14, 30, tzinfo=UTC)),
    )
    appearance = SignatureAppearance(
        signer_label_prefix="Signed 50%",
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        show_field_names=True,
        common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        location=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        email=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        title=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        company=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        signing_time=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        reason=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
    )

    semantics = service.resolve(_request(appearance=appearance))

    assert semantics.text.detail_text == "Common name: Alice 100%\nLocation: Richmond"
    assert semantics.text.stamp_text == (
        "Signed 50%%\n"
        "Common name: Alice 100%%\n"
        "Location: Richmond"
    )


def test_final_signing_mode_does_not_invent_preview_fallback_fields() -> None:
    service = VisibleSignatureSemanticsService(
        certificate_reader=_FakeCertificateReader(
            CertificateFieldValues(available=False, values={})
        ),
        clock=_FixedClock(datetime(2026, 5, 1, 14, 30, tzinfo=UTC)),
    )
    appearance = SignatureAppearance(
        signer_label_prefix="Digitally signed by",
        common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        signing_time=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        reason=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
    )

    semantics = service.resolve(
        _request(appearance=appearance, mode=VisibleSignatureSemanticsMode.FINAL_SIGNING)
    )

    assert all(not field.visible for field in semantics.fields if field.text == "")
    assert semantics.text.detail_text == ""
    assert semantics.text.stamp_text == "Digitally signed by"
    assert semantics.text.metadata_reason is None


def test_semantics_passes_resolved_stamp_text_to_fit_validator() -> None:
    issue = SigningDraftValidationIssue(
        code="visible_signature_layout_unavailable",
        message="too small",
    )
    fit_validator = _RecordingFitValidator(issues=(issue,))
    service = VisibleSignatureSemanticsService(
        certificate_reader=_FakeCertificateReader(
            CertificateFieldValues(
                available=True,
                values={SignatureFieldKey.COMMON_NAME: "Alice"},
            )
        ),
        clock=_FixedClock(datetime(2026, 5, 1, 14, 30, tzinfo=UTC)),
        fit_validator=fit_validator,
    )
    appearance = SignatureAppearance(
        signer_label_prefix="Digitally signed by",
        common_name=SignatureFieldBinding(source=SignatureFieldSource.DERIVED),
        signing_time=SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
    )
    rect = SignatureRect(
        page_index=0,
        left_pt=10,
        bottom_pt=20,
        width_pt=100,
        height_pt=30,
    )

    semantics = service.resolve(_request(appearance=appearance, signature_rect=rect))

    assert semantics.issues == (issue,)
    assert semantics.can_submit_visible_signature is False
    assert len(fit_validator.requests) == 1
    assert fit_validator.requests[0].signature_rect == rect
    assert fit_validator.requests[0].appearance == appearance
    assert fit_validator.requests[0].stamp_text == "Digitally signed by\nAlice"
