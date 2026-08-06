"""Phase 3 signing draft workflow and preview normalization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Self

from foliaseal.application.certificate_preview import (
    CertificatePreviewReader,
    Pkcs12CertificatePreviewReader,
)
from foliaseal.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewRect,
    ViewTransform,
    validate_pdf_rect_within_page,
    view_rect_to_pdf_rect,
)
from foliaseal.application.reusable_signing_models import ResolvedSignaturePreset
from foliaseal.application.signing_material_resolver import SigningMaterial
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
from foliaseal.infra.config.schemas import CertificateConfiguration


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
    stamp_text: str | None = None


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
    selected_certificate_configuration_id: str | None = None
    selected_appearance_profile_id: str | None = None
    selected_placement_profile_id: str | None = None
    selected_signature_preset_id: str | None = None
    signature_rect: SignatureRect | None = None
    signature_appearance: SignatureAppearance | None = None
    signature_placement_defaults: SignaturePlacementDefaults | None = None
    placement_context: SignaturePlacementContext | None = None
    certificate_preview_reader: CertificatePreviewReader = field(
        default_factory=Pkcs12CertificatePreviewReader,
        repr=False,
    )
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
        self.selected_placement_profile_id = None
        self.selected_signature_preset_id = None

    def clear_signature_rect(self) -> None:
        """Remove the current signature rectangle."""
        self.signature_rect = None
        self.selected_placement_profile_id = None
        self.selected_signature_preset_id = None

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
        self.selected_appearance_profile_id = None
        self.selected_signature_preset_id = None

    def clear_signature_appearance(self) -> None:
        """Remove the current visible-signature appearance draft."""
        self.signature_appearance = None
        self.selected_appearance_profile_id = None

    def capture_current_signature_setup(
        self,
        name: str,
        *,
        schema_version: int = 1,
        placement_defaults: SignaturePlacementDefaults | None = None,
    ) -> ResolvedSignaturePreset:
        """Capture the current setup as a resolved reusable signature preset."""
        if self.signature_appearance is None:
            raise ValueError(
                "A signature appearance must exist before saving a signature preset."
            )

        effective_placement_defaults = placement_defaults
        if effective_placement_defaults is None:
            effective_placement_defaults = self.signature_placement_defaults
        if effective_placement_defaults is None and self.signature_rect is not None:
            effective_placement_defaults = SignaturePlacementDefaults(
                width_pt=self.signature_rect.width_pt,
                height_pt=self.signature_rect.height_pt,
            )

        return ResolvedSignaturePreset.from_parts(
            schema_version=schema_version,
            name=name,
            appearance=self.signature_appearance,
            placement_defaults=effective_placement_defaults,
            certificate_configuration_id=self.selected_certificate_configuration_id,
        )

    def apply_resolved_signature_preset(self, preset: ResolvedSignaturePreset) -> None:
        """Apply a resolved reusable signature preset to the current draft."""
        self.apply_signature_preset_values(
            appearance=preset.appearance,
            placement_defaults=preset.placement_defaults,
            signature_preset_id=preset.preset.signature_preset_id,
            appearance_profile_id=preset.preset.appearance_profile_id,
            placement_profile_id=preset.preset.placement_profile_id,
            certificate_configuration_id=preset.preset.certificate_configuration_id,
        )

    def apply_signature_preset_values(
        self,
        *,
        appearance: SignatureAppearance,
        placement_defaults: SignaturePlacementDefaults | None,
        signature_preset_id: str | None,
        appearance_profile_id: str | None,
        placement_profile_id: str | None,
        certificate_configuration_id: str | None,
    ) -> None:
        """Apply draft-facing signature preset values without requiring a schema DTO."""
        self.signature_appearance = appearance
        self.signature_placement_defaults = placement_defaults
        self.selected_signature_preset_id = signature_preset_id
        if certificate_configuration_id is not None:
            self.selected_certificate_configuration_id = certificate_configuration_id
        self.selected_appearance_profile_id = appearance_profile_id
        self.selected_placement_profile_id = placement_profile_id

    def apply_certificate_configuration(
        self,
        configuration: CertificateConfiguration,
        signing_material: SigningMaterial,
    ) -> None:
        """Apply a resolved certificate configuration to the current draft."""
        self.selected_certificate_configuration_id = (
            configuration.certificate_configuration_id
        )
        self.certificate_path = signing_material.certificate_path
        self.passphrase = signing_material.passphrase
        self.certificate_alias = signing_material.certificate_alias
        self._certificate_preview_values = None
        self._certificate_preview_available = False

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
        semantics = self._resolve_visible_signature_semantics()
        fields = tuple(
            SigningDraftPreviewField(
                field_key=field.field_key,
                label=field.label,
                text=field.text,
                visible=field.visible,
                source=field.source,
                hint=field.hint,
            )
            for field in semantics.fields
        )
        detail_text = ""
        if appearance is not None:
            detail_text = semantics.text.detail_text
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
            stamp_text=semantics.text.stamp_text,
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

    def _certificate_values_for_preview(self) -> dict[SignatureFieldKey, str]:
        if self._certificate_preview_values is not None:
            return self._certificate_preview_values

        preview_values = self.certificate_preview_reader.read_preview_values(
            self.certificate_path,
            self.passphrase,
        )
        self._certificate_preview_values = preview_values.values
        self._certificate_preview_available = preview_values.available
        return self._certificate_preview_values

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
        return self._resolve_visible_signature_semantics().issues

    def _resolve_visible_signature_semantics(self):
        from foliaseal.application.visible_signature_semantics import (
            CertificateFieldValues,
            VisibleSignatureFitRequest,
            VisibleSignatureSemanticsRequest,
            VisibleSignatureSemanticsService,
        )

        workflow = self

        class _WorkflowCertificateFieldReader:
            def read_fields(
                self,
                certificate_path: str,
                passphrase: str,
            ) -> CertificateFieldValues:
                del certificate_path, passphrase
                values = workflow._certificate_values_for_preview()
                return CertificateFieldValues(
                    available=workflow._certificate_preview_available,
                    values=values,
                )

        class _WorkflowVisibleSignatureFitValidator:
            def validate(
                self,
                request: VisibleSignatureFitRequest,
            ) -> tuple[SigningDraftValidationIssue, ...]:
                if not Path(workflow.certificate_path).exists():
                    return ()
                from foliaseal.application.phase3_signing_backend import (
                    stamp_background_for_path,
                    validate_visible_signature_fit,
                )
                from foliaseal.application.sign_pdf_use_case import (
                    SigningBackendAppearance,
                )

                if workflow.signature_appearance is None:
                    return ()
                try:
                    stamp_background = stamp_background_for_path(
                        workflow.signature_appearance.image_stamp_path
                    )
                except ValueError as exc:
                    return (
                        _issue(
                            "visible_signature_layout_unavailable",
                            str(exc),
                            field_name="signature_appearance",
                        ),
                    )
                return validate_visible_signature_fit(
                    signature_rect=request.signature_rect,
                    signature_appearance=SigningBackendAppearance.from_signature_appearance(
                        workflow.signature_appearance
                    ),
                    stamp_text=request.stamp_text,
                    stamp_background=stamp_background,
                )

        return VisibleSignatureSemanticsService(
            certificate_reader=_WorkflowCertificateFieldReader(),
            fit_validator=_WorkflowVisibleSignatureFitValidator(),
        ).resolve(
            VisibleSignatureSemanticsRequest(
                certificate_path=self.certificate_path,
                passphrase=self.passphrase,
                signature_rect=self.signature_rect,
                appearance=self.signature_appearance,
                placement_context=self.placement_context,
            )
        )
