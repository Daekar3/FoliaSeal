"""Visible-signature field, text, and metadata semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

from foliaseal.application.sign_pdf_use_case import (
    SigningBackendAppearance,
    SigningBackendFieldBinding,
)
from foliaseal.application.signing_draft_contracts import (
    SignaturePlacementContext,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
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


class VisibleSignatureSemanticsMode(str, Enum):  # noqa: UP042
    """Resolution mode for preview-time or final-signing semantics."""

    PREVIEW = "preview"
    FINAL_SIGNING = "final_signing"


@dataclass(frozen=True)
class CertificateFieldValues:
    """Certificate-derived values used for visible signature fields."""

    available: bool
    values: dict[SignatureFieldKey, str]


class CertificateFieldReader(Protocol):
    """Reads certificate-derived field values for visible-signature text."""

    def read_fields(self, certificate_path: str, passphrase: str) -> CertificateFieldValues:
        """Return visible field values for a certificate path/passphrase pair."""


class SigningClock(Protocol):
    """Supplies signing-time timestamps in the requested display mode."""

    def now(self, mode: SignatureTimezoneDisplayMode) -> datetime:
        """Return the current signing timestamp."""


@dataclass(frozen=True)
class VisibleSignatureField:
    """Resolved text for one visible-signature field."""

    field_key: SignatureFieldKey
    label: str
    text: str
    visible: bool
    source: SignatureFieldSource
    hint: str | None = None


@dataclass(frozen=True)
class VisibleSignatureText:
    """Resolved visible-signature text and PDF metadata text."""

    title_text: str
    detail_text: str
    stamp_text: str
    metadata_reason: str | None
    metadata_location: str | None
    metadata_contact_info: str | None


@dataclass(frozen=True)
class VisibleSignatureFitRequest:
    """Input supplied to visible-signature fit validation."""

    signature_rect: SignatureRect
    appearance: SignatureAppearance | SigningBackendAppearance
    stamp_text: str


class VisibleSignatureFitValidator(Protocol):
    """Validates whether resolved visible-signature text fits its rectangle."""

    def validate(
        self,
        request: VisibleSignatureFitRequest,
    ) -> tuple[SigningDraftValidationIssue, ...]:
        """Return fit issues for the resolved visible signature."""


@dataclass(frozen=True)
class VisibleSignatureSemanticsRequest:
    """Inputs needed to resolve visible-signature semantics."""

    certificate_path: str
    passphrase: str
    signature_rect: SignatureRect | None
    appearance: SignatureAppearance | SigningBackendAppearance | None
    placement_context: SignaturePlacementContext | None = None
    mode: VisibleSignatureSemanticsMode = VisibleSignatureSemanticsMode.PREVIEW


@dataclass(frozen=True)
class VisibleSignatureSemantics:
    """Resolved visible-signature fields, text, issues, and readiness."""

    fields: tuple[VisibleSignatureField, ...]
    text: VisibleSignatureText
    issues: tuple[SigningDraftValidationIssue, ...]
    can_submit_visible_signature: bool


class UnavailableCertificateFieldReader:
    """Certificate reader that reports no available certificate values."""

    def read_fields(self, certificate_path: str, passphrase: str) -> CertificateFieldValues:
        del certificate_path, passphrase
        return CertificateFieldValues(available=False, values={})


class SystemSigningClock:
    """Signing clock backed by the local system time."""

    def now(self, mode: SignatureTimezoneDisplayMode) -> datetime:
        timestamp = datetime.now(UTC)
        if mode == SignatureTimezoneDisplayMode.LOCAL:
            return timestamp.astimezone()
        return timestamp


class NoopVisibleSignatureFitValidator:
    """Fit validator that reports no fit issues."""

    def validate(
        self,
        request: VisibleSignatureFitRequest,
    ) -> tuple[SigningDraftValidationIssue, ...]:
        del request
        return ()


class VisibleSignatureSemanticsService:
    """Resolves visible-signature fields, stamp text, metadata, and fit issues."""

    def __init__(
        self,
        *,
        certificate_reader: CertificateFieldReader | None = None,
        clock: SigningClock | None = None,
        fit_validator: VisibleSignatureFitValidator | None = None,
    ) -> None:
        self._certificate_reader = certificate_reader or UnavailableCertificateFieldReader()
        self._clock = clock or SystemSigningClock()
        self._fit_validator = fit_validator or NoopVisibleSignatureFitValidator()

    def resolve(
        self,
        request: VisibleSignatureSemanticsRequest,
    ) -> VisibleSignatureSemantics:
        """Resolve semantic visible-signature state for preview or signing."""
        appearance = request.appearance
        if appearance is None:
            text = VisibleSignatureText(
                title_text="",
                detail_text="",
                stamp_text="",
                metadata_reason=None,
                metadata_location=None,
                metadata_contact_info=None,
            )
            return VisibleSignatureSemantics(
                fields=(),
                text=text,
                issues=(),
                can_submit_visible_signature=True,
            )

        certificate_values = self._certificate_reader.read_fields(
            request.certificate_path,
            request.passphrase,
        )
        fields = tuple(
            self._resolve_field(
                field_key,
                binding,
                appearance=appearance,
                certificate_values=certificate_values,
                mode=request.mode,
            )
            for field_key, binding in _iter_field_bindings(appearance)
        )
        body_fragments = tuple(
            _field_fragment(field, appearance=appearance)
            for field in fields
            if field.visible and field.text
        )
        title_text, detail_text, stamp_text = _compose_visible_signature_text(
            signer_label_prefix=appearance.signer_label_prefix,
            layout_template=appearance.layout_template,
            body_fragments=body_fragments,
        )
        text = VisibleSignatureText(
            title_text=title_text,
            detail_text=detail_text,
            stamp_text=stamp_text,
            metadata_reason=_metadata_value(fields, SignatureFieldKey.REASON),
            metadata_location=_metadata_value(fields, SignatureFieldKey.LOCATION),
            metadata_contact_info=_metadata_value(fields, SignatureFieldKey.EMAIL),
        )

        issues: tuple[SigningDraftValidationIssue, ...] = ()
        if request.signature_rect is not None:
            issues = self._fit_validator.validate(
                VisibleSignatureFitRequest(
                    signature_rect=request.signature_rect,
                    appearance=appearance,
                    stamp_text=text.stamp_text,
                )
            )
        return VisibleSignatureSemantics(
            fields=fields,
            text=text,
            issues=issues,
            can_submit_visible_signature=not any(
                issue.severity == SigningDraftValidationSeverity.ERROR
                for issue in issues
            ),
        )

    def _resolve_field(
        self,
        field_key: SignatureFieldKey,
        binding: SignatureFieldBinding | SigningBackendFieldBinding,
        *,
        appearance: SignatureAppearance | SigningBackendAppearance,
        certificate_values: CertificateFieldValues,
        mode: VisibleSignatureSemanticsMode,
    ) -> VisibleSignatureField:
        label = _field_label(field_key)
        if not _should_render_field(binding):
            return VisibleSignatureField(
                field_key=field_key,
                label=label,
                text="",
                visible=False,
                source=binding.source,
            )

        hint: str | None = None
        if binding.source == SignatureFieldSource.OVERRIDE:
            text = binding.override_text or ""
        elif field_key == SignatureFieldKey.SIGNING_TIME:
            text = self._clock.now(appearance.timezone_display_mode).strftime(
                appearance.datetime_format
            )
            hint = "sign time" if mode == VisibleSignatureSemanticsMode.PREVIEW else None
        else:
            text = certificate_values.values.get(field_key, "")
            if text and mode == VisibleSignatureSemanticsMode.PREVIEW:
                hint = "from certificate"
            elif (
                not certificate_values.available
                and mode == VisibleSignatureSemanticsMode.PREVIEW
            ):
                text = binding.display_label or _derived_preview_text(field_key)
                hint = "from certificate"

        return VisibleSignatureField(
            field_key=field_key,
            label=label,
            text=text,
            visible=bool(text),
            source=binding.source,
            hint=hint,
        )


def _iter_field_bindings(
    appearance: SignatureAppearance | SigningBackendAppearance,
) -> tuple[
    tuple[SignatureFieldKey, SignatureFieldBinding | SigningBackendFieldBinding],
    ...,
]:
    if isinstance(appearance, SigningBackendAppearance):
        return tuple((binding.field_key, binding) for binding in appearance.field_bindings)
    return appearance.iter_field_bindings()


def _should_render_field(
    binding: SignatureFieldBinding | SigningBackendFieldBinding,
) -> bool:
    return binding.show_in_visible_appearance and binding.source != SignatureFieldSource.HIDDEN


def _field_fragment(
    field: VisibleSignatureField,
    *,
    appearance: SignatureAppearance | SigningBackendAppearance,
) -> str:
    if appearance.show_field_names:
        return f"{field.label}: {field.text}"
    return field.text


def _compose_visible_signature_text(
    *,
    signer_label_prefix: str,
    layout_template: SignatureLayoutTemplate,
    body_fragments: tuple[str, ...],
) -> tuple[str, str, str]:
    title_text = signer_label_prefix.strip()
    if layout_template == SignatureLayoutTemplate.SINGLE_LINE:
        detail_text = " | ".join(body_fragments)
    elif layout_template == SignatureLayoutTemplate.WRAPPED_BLOCK:
        if not body_fragments:
            detail_text = ""
        elif len(body_fragments) <= 2:
            detail_text = "\n".join(body_fragments)
        else:
            detail_text = "\n".join(
                [
                    body_fragments[0],
                    body_fragments[1],
                    " ".join(body_fragments[2:]),
                ]
            )
    else:
        detail_text = "\n".join(body_fragments)

    if title_text and detail_text:
        stamp_text = f"{title_text}\n{detail_text}"
    else:
        stamp_text = title_text or detail_text
    return title_text, detail_text, stamp_text.replace("%", "%%")


def _metadata_value(
    fields: tuple[VisibleSignatureField, ...],
    field_key: SignatureFieldKey,
) -> str | None:
    for field in fields:
        if field.field_key == field_key and field.visible and field.text:
            return field.text
    return None


def _derived_preview_text(field_key: SignatureFieldKey) -> str:
    return _field_label(field_key)


def _field_label(field_key: SignatureFieldKey) -> str:
    labels = {
        SignatureFieldKey.DISTINGUISHED_NAME: "Distinguished name",
        SignatureFieldKey.COMMON_NAME: "Common name",
        SignatureFieldKey.EMAIL: "Email",
        SignatureFieldKey.SIGNING_TIME: "Signing time",
        SignatureFieldKey.REASON: "Reason",
        SignatureFieldKey.LOCATION: "Location",
        SignatureFieldKey.TITLE: "Title",
        SignatureFieldKey.COMPANY: "Company",
    }
    return labels[field_key]
