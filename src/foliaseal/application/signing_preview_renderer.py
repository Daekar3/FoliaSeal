"""Deterministic preview rendering and semantic parity helpers for Phase 3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from foliaseal.application.signing_draft_workflow import (
    SigningDraftPreview,
    SigningDraftPreviewField,
    SigningDraftValidationIssue,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureRect,
    SigningRequest,
)


class SigningPreviewLineKind(str, Enum):  # noqa: UP042
    """Stable line categories for preview rendering."""

    TITLE = "title"
    SUMMARY = "summary"
    FIELD = "field"
    ISSUE = "issue"
    STATUS = "status"


@dataclass(frozen=True)
class SigningPreviewLine:
    """One deterministic line in the rendered preview."""

    kind: SigningPreviewLineKind
    text: str


@dataclass(frozen=True)
class SigningPreviewRenderSnapshot:
    """Normalized preview output that a UI can render directly."""

    title: str
    lines: tuple[SigningPreviewLine, ...]
    field_count: int
    visible_field_count: int
    hidden_field_count: int
    issue_count: int
    can_submit: bool


@dataclass(frozen=True)
class SigningPreviewParityIssue:
    """Mismatch between a draft preview and the request it should represent."""

    code: str
    message: str
    field_name: str | None = None


@dataclass(frozen=True)
class SigningPreviewParityReport:
    """Result of comparing preview semantics to the final signing request."""

    is_consistent: bool
    issues: tuple[SigningPreviewParityIssue, ...]


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


def _rect_summary(signature_rect: SignatureRect | None) -> str:
    if signature_rect is None:
        return "Placement: missing"
    return (
        "Placement: "
        f"page={signature_rect.page_index} "
        f"left={signature_rect.left_pt:g} "
        f"bottom={signature_rect.bottom_pt:g} "
        f"width={signature_rect.width_pt:g} "
        f"height={signature_rect.height_pt:g}"
    )


def _appearance_summary(preview: SigningDraftPreview) -> str:
    if (
        preview.signer_label_prefix is None
        or preview.layout_template is None
        or preview.timezone_display_mode is None
    ):
        return "Appearance: missing"
    return (
        "Appearance: "
        f"{preview.signer_label_prefix} | "
        f"{preview.layout_template.value} | "
        f"{preview.timezone_display_mode.value}"
    )


def _style_summary(preview: SigningDraftPreview) -> tuple[str, ...]:
    if preview.text_style is None or preview.box_style is None:
        return ()
    return (
        (
            "Text style: "
            f"{preview.text_style.font_family} "
            f"{preview.text_style.font_size_pt:g}pt "
            f"{'bold' if preview.text_style.bold else 'regular'} "
            f"{'italic' if preview.text_style.italic else 'upright'} "
            f"{preview.text_style.text_color_hex}"
        ),
        (
            "Box style: "
            f"{'border' if preview.box_style.show_border else 'no-border'} "
            f"{preview.box_style.border_color_hex} "
            f"{preview.box_style.border_width_pt:g}pt "
            f"{preview.box_style.background_color_hex}"
        ),
    )


def _format_field_line(field: SigningDraftPreviewField) -> str:
    status = "visible" if field.visible else "hidden"
    if not field.visible:
        return f"[{status}] {field.label}"

    source = field.source.value
    if field.hint is not None:
        return f"[{status}] {field.label}: {field.text} ({source}, {field.hint})"
    return f"[{status}] {field.label}: {field.text} ({source})"


def _format_issue_line(issue: SigningDraftValidationIssue) -> str:
    field_suffix = f" [{issue.field_name}]" if issue.field_name else ""
    return f"{issue.severity.value.upper()} {issue.code}{field_suffix}: {issue.message}"


def _render_fields_from_appearance(
    appearance: SignatureAppearance,
) -> tuple[SigningDraftPreviewField, ...]:
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
        else:
            text = binding.display_label or label
            hint = "from certificate"

        fields.append(
            SigningDraftPreviewField(
                field_key=field_key,
                label=label,
                text=text,
                visible=True,
                source=binding.source,
                hint=hint,
            )
        )
    return tuple(fields)


def render_signing_preview(preview: SigningDraftPreview) -> SigningPreviewRenderSnapshot:
    """Render the normalized preview into deterministic text lines."""
    lines: list[SigningPreviewLine] = [
        SigningPreviewLine(SigningPreviewLineKind.TITLE, preview.title),
        SigningPreviewLine(SigningPreviewLineKind.SUMMARY, _rect_summary(preview.signature_rect)),
        SigningPreviewLine(SigningPreviewLineKind.SUMMARY, _appearance_summary(preview)),
    ]

    lines.extend(
        SigningPreviewLine(SigningPreviewLineKind.SUMMARY, summary)
        for summary in _style_summary(preview)
    )

    lines.extend(
        SigningPreviewLine(SigningPreviewLineKind.FIELD, _format_field_line(field))
        for field in preview.fields
    )
    lines.extend(
        SigningPreviewLine(SigningPreviewLineKind.ISSUE, _format_issue_line(issue))
        for issue in preview.issues
    )
    lines.append(
        SigningPreviewLine(
            SigningPreviewLineKind.STATUS,
            "Ready to sign" if preview.can_submit else "Signing blocked",
        )
    )

    visible_field_count = sum(1 for field in preview.fields if field.visible)
    hidden_field_count = len(preview.fields) - visible_field_count
    return SigningPreviewRenderSnapshot(
        title=preview.title,
        lines=tuple(lines),
        field_count=len(preview.fields),
        visible_field_count=visible_field_count,
        hidden_field_count=hidden_field_count,
        issue_count=len(preview.issues),
        can_submit=preview.can_submit,
    )


def compare_preview_to_request(
    preview: SigningDraftPreview,
    request: SigningRequest,
) -> SigningPreviewParityReport:
    """Compare preview semantics to the request it should represent."""
    issues: list[SigningPreviewParityIssue] = []

    if preview.signature_rect != request.signature_rect:
        issues.append(
            SigningPreviewParityIssue(
                code="signature_rect_mismatch",
                message="Preview placement does not match the final signing request.",
                field_name="signature_rect",
            )
        )

    if request.signature_appearance is None:
        if preview.fields:
            issues.append(
                SigningPreviewParityIssue(
                    code="appearance_missing_in_request",
                    message="Preview contains appearance fields but the request does not.",
                    field_name="signature_appearance",
                )
            )
        return SigningPreviewParityReport(is_consistent=not issues, issues=tuple(issues))

    request_appearance = request.signature_appearance
    if preview.signer_label_prefix != request_appearance.signer_label_prefix:
        issues.append(
            SigningPreviewParityIssue(
                code="signer_label_prefix_mismatch",
                message="Preview label prefix does not match the final request.",
                field_name="signer_label_prefix",
            )
        )

    if preview.layout_template != request_appearance.layout_template:
        issues.append(
            SigningPreviewParityIssue(
                code="layout_template_mismatch",
                message="Preview layout template does not match the final request.",
                field_name="layout_template",
            )
        )

    if preview.timezone_display_mode != request_appearance.timezone_display_mode:
        issues.append(
            SigningPreviewParityIssue(
                code="timezone_display_mode_mismatch",
                message="Preview timezone mode does not match the final request.",
                field_name="timezone_display_mode",
            )
        )

    if preview.text_style != request_appearance.text_style:
        issues.append(
            SigningPreviewParityIssue(
                code="text_style_mismatch",
                message="Preview text style does not match the final request.",
                field_name="text_style",
            )
        )

    if preview.box_style != request_appearance.box_style:
        issues.append(
            SigningPreviewParityIssue(
                code="box_style_mismatch",
                message="Preview box style does not match the final request.",
                field_name="box_style",
            )
        )

    expected_fields = _render_fields_from_appearance(request_appearance)
    if preview.fields != expected_fields:
        issues.append(
            SigningPreviewParityIssue(
                code="field_render_mismatch",
                message="Preview field rendering does not match the final request.",
                field_name="signature_appearance",
            )
        )

    return SigningPreviewParityReport(is_consistent=not issues, issues=tuple(issues))

