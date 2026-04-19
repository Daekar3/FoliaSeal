"""Phase 3 signing draft workflow and preview normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Self

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewRect,
    ViewTransform,
    validate_pdf_rect_within_page,
    view_rect_to_pdf_rect,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
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
from foliaseal.infra.config.schemas import SignaturePreset


class SigningDraftValidationError(ValueError):
    """Raised when the signing draft cannot be converted into a final request."""

    def __init__(self, issues: tuple[SigningDraftValidationIssue, ...]) -> None:
        self.issues = issues
        message = "; ".join(issue.message for issue in issues) if issues else "Invalid draft."
        super().__init__(message)


class SigningDraftValidationSeverity(str, Enum):  # noqa: UP042
    """Severity levels for signing draft validation."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class SigningDraftValidationIssue:
    """A single validation problem surfaced to the UI."""

    code: str
    message: str
    field_name: str | None = None
    severity: SigningDraftValidationSeverity = SigningDraftValidationSeverity.ERROR


@dataclass(frozen=True)
class SignaturePlacementContext:
    """Page geometry and rotation used for placement validation."""

    page_index: int
    page_box: PageBox
    rotation: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be zero or greater.")
        if self.rotation % 90 != 0:
            raise ValueError("rotation must be a multiple of 90 degrees.")
        self.page_box.validate()


@dataclass(frozen=True)
class SigningDraftPreviewField:
    """Normalized preview line for one visible signature field."""

    field_key: SignatureFieldKey
    label: str
    text: str
    visible: bool
    source: SignatureFieldSource
    hint: str | None = None


@dataclass(frozen=True)
class SigningDraftPreview:
    """Normalized preview payload for the UI layer."""

    title: str
    page_index: int | None
    signature_rect: SignatureRect | None
    signer_label_prefix: str | None
    layout_template: SignatureLayoutTemplate | None
    stamp_position: SignatureStampPosition | None
    timezone_display_mode: SignatureTimezoneDisplayMode | None
    show_field_names: bool
    datetime_format: str | None
    text_style: SignatureTextStyle | None
    box_style: SignatureBoxStyle | None
    image_stamp_path: str | None
    fields: tuple[SigningDraftPreviewField, ...]
    detail_text: str
    issues: tuple[SigningDraftValidationIssue, ...]
    can_submit: bool


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


def _derived_preview_text(field_key: SignatureFieldKey) -> str:
    return _field_label(field_key)


def _preview_signing_time(
    *,
    datetime_format: str,
    timezone_mode: SignatureTimezoneDisplayMode,
) -> str:
    timestamp = datetime.now(UTC)
    if timezone_mode == SignatureTimezoneDisplayMode.LOCAL:
        timestamp = timestamp.astimezone()
    return timestamp.strftime(datetime_format)


def _issue(
    code: str,
    message: str,
    field_name: str | None = None,
    severity: SigningDraftValidationSeverity = SigningDraftValidationSeverity.ERROR,
) -> SigningDraftValidationIssue:
    return SigningDraftValidationIssue(
        code=code,
        message=message,
        field_name=field_name,
        severity=severity,
    )


@dataclass
class SigningDraftWorkflow:
    """Application-layer state machine for visible-signature signing drafts."""

    input_pdf_path: str
    output_pdf_path: str
    certificate_path: str
    passphrase: str
    tsa_url: str
    timestamp_required: bool = True
    trust_policy: TimestampTrustPolicy | None = None
    certificate_alias: str | None = None
    signature_rect: SignatureRect | None = None
    signature_appearance: SignatureAppearance | None = None
    signature_placement_defaults: SignaturePlacementDefaults | None = None
    placement_context: SignaturePlacementContext | None = None
    _certificate_preview_values: dict[SignatureFieldKey, str] | None = field(
        default=None,
        init=False,
        repr=False,
    )
    _certificate_preview_available: bool = field(default=False, init=False, repr=False)

    @classmethod
    def from_signing_request(
        cls,
        request: SigningRequest,
        *,
        placement_context: SignaturePlacementContext | None = None,
    ) -> Self:
        """Create a draft workflow seeded from an existing signing request."""
        return cls(
            input_pdf_path=request.input_pdf_path,
            output_pdf_path=request.output_pdf_path,
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            tsa_url=request.tsa_url,
            timestamp_required=request.timestamp_required,
            trust_policy=request.trust_policy,
            certificate_alias=request.certificate_alias,
            signature_rect=request.signature_rect,
            signature_appearance=request.signature_appearance,
            signature_placement_defaults=None,
            placement_context=placement_context,
        )

    @property
    def current_signature_rect(self) -> SignatureRect | None:
        """Return the current signed-rectangle draft value."""
        return self.signature_rect

    @property
    def current_signature_appearance(self) -> SignatureAppearance | None:
        """Return the current visible-signature appearance draft value."""
        return self.signature_appearance

    def set_placement_context(self, context: SignaturePlacementContext | None) -> None:
        """Store the current page geometry used for placement validation."""
        self.placement_context = context

    def clear_placement_context(self) -> None:
        """Forget the current page geometry."""
        self.placement_context = None

    def set_signature_rect(self, signature_rect: SignatureRect | None) -> None:
        """Set the PDF-space rectangle used for the visible signature."""
        self.signature_rect = signature_rect

    def clear_signature_rect(self) -> None:
        """Remove the current signature rectangle."""
        self.signature_rect = None

    def update_signature_rect(
        self,
        *,
        page_index: int | None = None,
        left_pt: float | None = None,
        bottom_pt: float | None = None,
        width_pt: float | None = None,
        height_pt: float | None = None,
    ) -> SignatureRect:
        """Apply numeric fine-tuning to the current signature rectangle."""
        if self.signature_rect is None and (
            page_index is None
            or left_pt is None
            or bottom_pt is None
            or width_pt is None
            or height_pt is None
        ):
            raise ValueError(
                "A signature rectangle must exist before fine-tuning partial values."
            )

        current = self.signature_rect
        if current is None:
            new_rect = SignatureRect(
                page_index=page_index if page_index is not None else 0,
                left_pt=left_pt if left_pt is not None else 0.0,
                bottom_pt=bottom_pt if bottom_pt is not None else 0.0,
                width_pt=width_pt if width_pt is not None else 1.0,
                height_pt=height_pt if height_pt is not None else 1.0,
            )
        else:
            new_rect = SignatureRect(
                page_index=page_index if page_index is not None else current.page_index,
                left_pt=left_pt if left_pt is not None else current.left_pt,
                bottom_pt=bottom_pt if bottom_pt is not None else current.bottom_pt,
                width_pt=width_pt if width_pt is not None else current.width_pt,
                height_pt=height_pt if height_pt is not None else current.height_pt,
            )
        self.signature_rect = new_rect
        return new_rect

    def set_signature_rect_from_view_selection(
        self,
        view_rect: ViewRect,
        *,
        transform: ViewTransform,
    ) -> SignatureRect:
        """Convert a viewer drag selection into a PDF-space rectangle."""
        context = self._require_placement_context()
        pdf_rect = view_rect_to_pdf_rect(
            view_rect=view_rect,
            transform=transform,
            page_box=context.page_box,
            rotation=context.rotation,
        )
        if not validate_pdf_rect_within_page(pdf_rect, page_box=context.page_box):
            raise ValueError("Selection is out of page bounds.")

        rect = SignatureRect(
            page_index=context.page_index,
            left_pt=pdf_rect.x1,
            bottom_pt=pdf_rect.y1,
            width_pt=pdf_rect.x2 - pdf_rect.x1,
            height_pt=pdf_rect.y2 - pdf_rect.y1,
        )
        self.signature_rect = rect
        return rect

    def set_signature_appearance(
        self,
        signature_appearance: SignatureAppearance | None,
    ) -> None:
        """Set the normalized visible-signature appearance."""
        self.signature_appearance = signature_appearance

    def clear_signature_appearance(self) -> None:
        """Remove the current visible-signature appearance draft."""
        self.signature_appearance = None

    def capture_signature_preset(
        self,
        name: str,
        *,
        schema_version: int = 1,
        placement_defaults: SignaturePlacementDefaults | None = None,
    ) -> SignaturePreset:
        """Capture the current appearance draft as a named reusable profile."""
        if self.signature_appearance is None:
            raise ValueError("A signature appearance must exist before saving a profile.")

        effective_placement_defaults = placement_defaults
        if effective_placement_defaults is None:
            effective_placement_defaults = self.signature_placement_defaults
        if effective_placement_defaults is None and self.signature_rect is not None:
            effective_placement_defaults = SignaturePlacementDefaults(
                width_pt=self.signature_rect.width_pt,
                height_pt=self.signature_rect.height_pt,
            )

        return SignaturePreset(
            schema_version=schema_version,
            name=name,
            appearance=self.signature_appearance,
            placement_defaults=effective_placement_defaults,
        )

    def apply_signature_preset(self, preset: SignaturePreset) -> None:
        """Load a named reusable profile into the current draft."""
        self.signature_appearance = preset.appearance
        self.signature_placement_defaults = preset.placement_defaults

    def validation_issues(self) -> tuple[SigningDraftValidationIssue, ...]:
        """Return blocking and non-blocking problems for the current draft."""
        issues: list[SigningDraftValidationIssue] = []
        if self.signature_rect is None:
            issues.append(
                _issue(
                    "signature_rect_missing",
                    "Signature placement is required before signing.",
                    field_name="signature_rect",
                )
            )
        else:
            issues.extend(self._validate_signature_rect())

        if self.signature_appearance is None:
            issues.append(
                _issue(
                    "signature_appearance_missing",
                    "Visible signature appearance is required before signing.",
                    field_name="signature_appearance",
                )
            )
        elif self.signature_rect is not None:
            issues.extend(self._validate_visible_signature_fit())

        return tuple(issues)

    def can_build_request(self) -> bool:
        """Return whether the current draft is ready for signing."""
        return not any(
            issue.severity == SigningDraftValidationSeverity.ERROR
            for issue in self.validation_issues()
        )

    def preview(self) -> SigningDraftPreview:
        """Return a normalized, UI-friendly preview payload."""
        appearance = self.signature_appearance
        issues = self.validation_issues()
        fields = self._build_preview_fields(appearance) if appearance is not None else ()
        detail_text = ""
        if appearance is not None:
            detail_text = self._build_preview_detail_text(appearance, fields)
        return SigningDraftPreview(
            title=appearance.signer_label_prefix if appearance else "Signature draft",
            page_index=self.signature_rect.page_index if self.signature_rect else None,
            signature_rect=self.signature_rect,
            signer_label_prefix=appearance.signer_label_prefix if appearance else None,
            layout_template=appearance.layout_template if appearance else None,
            stamp_position=appearance.stamp_position if appearance else None,
            timezone_display_mode=appearance.timezone_display_mode if appearance else None,
            show_field_names=appearance.show_field_names if appearance else False,
            datetime_format=appearance.datetime_format if appearance else None,
            text_style=appearance.text_style if appearance else None,
            box_style=appearance.box_style if appearance else None,
            image_stamp_path=appearance.image_stamp_path if appearance else None,
            fields=fields,
            detail_text=detail_text,
            issues=issues,
            can_submit=self.can_build_request(),
        )

    def build_signing_request(self) -> SigningRequest:
        """Build the final signing request or raise with validation issues."""
        issues = self.validation_issues()
        if any(
            issue.severity == SigningDraftValidationSeverity.ERROR
            for issue in issues
        ):
            raise SigningDraftValidationError(issues)

        return SigningRequest(
            input_pdf_path=self.input_pdf_path,
            output_pdf_path=self.output_pdf_path,
            certificate_path=self.certificate_path,
            passphrase=self.passphrase,
            tsa_url=self.tsa_url,
            timestamp_required=self.timestamp_required,
            trust_policy=self.trust_policy,
            certificate_alias=self.certificate_alias,
            signature_rect=self.signature_rect,
            signature_appearance=self.signature_appearance,
        )

    def _build_preview_fields(
        self,
        appearance: SignatureAppearance,
    ) -> tuple[SigningDraftPreviewField, ...]:
        certificate_values = self._certificate_values_for_preview()
        certificate_available = self._certificate_preview_available
        fields: list[SigningDraftPreviewField] = []
        for field_key, binding in appearance.iter_field_bindings():
            label = _field_label(field_key)
            if (
                not binding.show_in_visible_appearance
                or binding.source == SignatureFieldSource.HIDDEN
            ):
                fields.append(
                    SigningDraftPreviewField(
                        field_key=field_key,
                        label=label,
                        text="",
                        visible=False,
                        source=binding.source,
                    )
                )
                continue

            if binding.source == SignatureFieldSource.OVERRIDE:
                text = binding.override_text or ""
                hint = None
            elif field_key == SignatureFieldKey.SIGNING_TIME:
                text = _preview_signing_time(
                    datetime_format=appearance.datetime_format,
                    timezone_mode=appearance.timezone_display_mode,
                )
                hint = "sign time"
            else:
                if certificate_available:
                    text = certificate_values.get(field_key, "")
                    hint = "from certificate" if text else None
                else:
                    text = binding.display_label or _derived_preview_text(field_key)
                    hint = "from certificate"

            fields.append(
                SigningDraftPreviewField(
                    field_key=field_key,
                    label=label,
                    text=text,
                    visible=bool(text),
                    source=binding.source,
                    hint=hint,
                )
            )

        return tuple(fields)

    def _build_preview_detail_text(
        self,
        appearance: SignatureAppearance,
        fields: tuple[SigningDraftPreviewField, ...],
    ) -> str:
        from foliaseal.application.phase3_signing_backend import (
            _compose_visible_signature_text_layout,
        )

        visible_fragments = self._visible_preview_fragments(appearance, fields)
        return _compose_visible_signature_text_layout(
            signer_label_prefix=appearance.signer_label_prefix,
            layout_template=appearance.layout_template,
            body_fragments=visible_fragments,
        ).detail_text

    def _visible_preview_fragments(
        self,
        appearance: SignatureAppearance,
        fields: tuple[SigningDraftPreviewField, ...],
    ) -> list[str]:
        fragments: list[str] = []
        for preview_field in fields:
            if not preview_field.visible or not preview_field.text:
                continue
            if appearance.show_field_names:
                fragments.append(f"{preview_field.label}: {preview_field.text}")
            else:
                fragments.append(preview_field.text)
        return fragments

    def _certificate_values_for_preview(self) -> dict[SignatureFieldKey, str]:
        if self._certificate_preview_values is not None:
            return self._certificate_preview_values

        try:
            key, certificate, _extra = pkcs12.load_key_and_certificates(
                Path(self.certificate_path).read_bytes(),
                self.passphrase.encode("utf-8"),
            )
        except Exception:
            self._certificate_preview_values = {}
            self._certificate_preview_available = False
            return self._certificate_preview_values

        if key is None or certificate is None:
            self._certificate_preview_values = {}
            self._certificate_preview_available = False
            return self._certificate_preview_values

        subject = certificate.subject
        def _first_attr(oid: NameOID) -> str | None:
            attributes = subject.get_attributes_for_oid(oid)
            if not attributes:
                return None
            value = attributes[0].value.strip()
            return value or None

        common_name = _first_attr(NameOID.COMMON_NAME)
        email = _first_attr(NameOID.EMAIL_ADDRESS)
        title = _first_attr(NameOID.TITLE) or _first_attr(NameOID.ORGANIZATIONAL_UNIT_NAME)
        company = _first_attr(NameOID.ORGANIZATION_NAME)
        location_parts = tuple(
            value
            for value in (
                _first_attr(NameOID.LOCALITY_NAME),
                _first_attr(NameOID.STATE_OR_PROVINCE_NAME),
                _first_attr(NameOID.COUNTRY_NAME),
            )
            if value
        )
        distinguished_name_parts = tuple(
            value
            for value in (
                common_name,
                email,
                title,
                company,
                *location_parts,
            )
            if value
        )

        values: dict[SignatureFieldKey, str] = {}
        if distinguished_name_parts:
            values[SignatureFieldKey.DISTINGUISHED_NAME] = ", ".join(distinguished_name_parts)

        if common_name:
            values[SignatureFieldKey.COMMON_NAME] = common_name
        if email:
            values[SignatureFieldKey.EMAIL] = email
        if title:
            values[SignatureFieldKey.TITLE] = title
        if company:
            values[SignatureFieldKey.COMPANY] = company
        if location_parts:
            values[SignatureFieldKey.LOCATION] = ", ".join(location_parts)

        self._certificate_preview_values = values
        self._certificate_preview_available = True
        return values

    def _validate_signature_rect(self) -> tuple[SigningDraftValidationIssue, ...]:
        rect = self.signature_rect
        if rect is None:
            return ()

        issues: list[SigningDraftValidationIssue] = []
        context = self.placement_context
        if context is None:
            issues.append(
                _issue(
                    "signature_rect_geometry_unavailable",
                    "Signature placement geometry is unavailable; bounds cannot be verified yet.",
                    field_name="signature_rect",
                    severity=SigningDraftValidationSeverity.WARNING,
                )
            )
            return tuple(issues)

        if rect.page_index != context.page_index:
            issues.append(
                _issue(
                    "signature_rect_page_mismatch",
                    "Signature rectangle page does not match the active placement page.",
                    field_name="signature_rect",
                )
            )
            return tuple(issues)

        pdf_rect = PdfRect(
            x1=rect.left_pt,
            y1=rect.bottom_pt,
            x2=rect.left_pt + rect.width_pt,
            y2=rect.bottom_pt + rect.height_pt,
        )
        if not validate_pdf_rect_within_page(pdf_rect, page_box=context.page_box):
            issues.append(
                _issue(
                    "signature_rect_out_of_bounds",
                    "Signature rectangle must stay within the current page bounds.",
                    field_name="signature_rect",
                )
            )

        return tuple(issues)

    def _require_placement_context(self) -> SignaturePlacementContext:
        if self.placement_context is None:
            raise ValueError("A placement context is required before converting selections.")
        return self.placement_context

    def _validate_visible_signature_fit(self) -> tuple[SigningDraftValidationIssue, ...]:
        if self.signature_rect is None or self.signature_appearance is None:
            return ()
        if not Path(self.certificate_path).exists():
            return ()

        from foliaseal.application.phase3_signing_backend import (
            _compose_visible_signature_text_layout,
            _stamp_background_for_path,
            _visible_signature_fit_issues_for_stamp_text,
        )
        from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance

        fields = self._build_preview_fields(self.signature_appearance)
        visible_fragments = self._visible_preview_fragments(
            self.signature_appearance,
            fields,
        )
        stamp_text = _compose_visible_signature_text_layout(
            signer_label_prefix=self.signature_appearance.signer_label_prefix,
            layout_template=self.signature_appearance.layout_template,
            body_fragments=visible_fragments,
        ).stamp_text
        try:
            stamp_background = _stamp_background_for_path(
                self.signature_appearance.image_stamp_path
            )
        except ValueError as exc:
            return (
                _issue(
                    "visible_signature_layout_unavailable",
                    str(exc),
                    field_name="signature_appearance",
                ),
            )
        return _visible_signature_fit_issues_for_stamp_text(
            signature_rect=self.signature_rect,
            signature_appearance=SigningBackendAppearance.from_signature_appearance(
                self.signature_appearance
            ),
            stamp_text=stamp_text,
            stamp_background=stamp_background,
        )
