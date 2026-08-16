"""Deterministic preview rendering and semantic parity helpers for Acceptance."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from tempfile import mkdtemp
from typing import Any

from PIL import Image
from pyhanko.pdf_utils.content import PdfContent
from pyhanko.pdf_utils.generic import StreamObject
from pyhanko.pdf_utils.layout import BoxConstraints
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter
from pyhanko.stamp import TextStampStyle

from foliaseal.application.horizontal_signature_reservation import (
    measure_horizontal_single_line_rendered_reference,
)
from foliaseal.application.preview_render_boundary import (
    PreviewRasterRenderer,
    PreviewRasterRequest,
    PreviewRasterResult,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signing_draft_contracts import (
    SigningDraftPreview,
    SigningDraftPreviewField,
    SigningDraftValidationIssue,
)
from foliaseal.application.stamp_background import stamp_background_for_path
from foliaseal.application.visible_signature_layout import (
    HorizontalInkMeasurement,
    HorizontalInkMeasurementRequest,
    RectBounds,
    SignatureLayoutPlan,
    VisibleSignatureLayoutOptions,
    VisibleSignatureLayoutRequest,
    VisibleSignatureLayoutService,
    structural_line_bounds,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureRect,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
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
class CanonicalSignaturePreviewSnapshot:
    """Rasterized visible-signature preview from the canonical stamp engine."""

    image_path: str
    width_px: int
    height_px: int
    text_area_bounds_px: dict[str, int] | None
    stamp_area_bounds_px: dict[str, int] | None
    text_bounds_px: dict[str, int] | None
    stamp_bounds_px: dict[str, int] | None
    appearance_snapshot: SignatureAppearanceSnapshot | None = None


@dataclass(frozen=True)
class SignatureAppearanceSnapshot:
    """Normalized structural description of one rendered visible signature."""

    image_path: str | None
    image_size_px: dict[str, int] | None
    container_bounds_px: dict[str, int] | None
    border_bounds_px: dict[str, int] | None
    border_style: dict[str, Any] | None
    text_bounds_px: dict[str, int] | None
    stamp_bounds_px: dict[str, int] | None
    text_fragments: tuple[str, ...]
    line_bounds_px: tuple[dict[str, int], ...] = ()


@dataclass(frozen=True)
class SignatureAppearanceLayerComparison:
    """One structural comparison result for a specific visual layer."""

    layer_name: str
    matches: bool
    reason: str | None = None


@dataclass(frozen=True)
class SignatureAppearanceComparison:
    """Layered comparison between preview and signed-output appearance snapshots."""

    is_consistent: bool
    border: SignatureAppearanceLayerComparison
    text: SignatureAppearanceLayerComparison
    stamp: SignatureAppearanceLayerComparison
    composite: SignatureAppearanceLayerComparison


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
        or preview.stamp_position is None
        or preview.timezone_display_mode is None
    ):
        return "Appearance: missing"
    return (
        "Appearance: "
        f"{preview.signer_label_prefix} | "
        f"{preview.layout_template.value} | "
        f"Stamp position: {preview.stamp_position.value} | "
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


def _metadata_summary(preview: SigningDraftPreview) -> tuple[str, ...]:
    datetime_format = preview.datetime_format if preview.datetime_format is not None else "missing"
    image_stamp_path = preview.image_stamp_path if preview.image_stamp_path is not None else "none"
    return (
        f"Datetime format: {datetime_format}",
        f"Image stamp: {image_stamp_path}",
    )


def _format_field_line(field: SigningDraftPreviewField, *, show_field_names: bool) -> str:
    status = "visible" if field.visible else "hidden"
    if not field.visible:
        return f"[{status}] {field.label}"

    source = field.source.value
    label_text = f"{field.label}: " if show_field_names else ""
    if field.hint is not None:
        return f"[{status}] {label_text}{field.text} ({source}, {field.hint})"
    return f"[{status}] {label_text}{field.text} ({source})"


def _format_issue_line(issue: SigningDraftValidationIssue) -> str:
    field_suffix = f" [{issue.field_name}]" if issue.field_name else ""
    return f"{issue.severity.value.upper()} {issue.code}{field_suffix}: {issue.message}"


def render_signing_preview(preview: SigningDraftPreview) -> SigningPreviewRenderSnapshot:
    """Render the normalized preview into deterministic text lines."""
    lines: list[SigningPreviewLine] = []
    if preview.title.strip():
        lines.append(SigningPreviewLine(SigningPreviewLineKind.TITLE, preview.title))
    lines.extend(
        [
            SigningPreviewLine(
                SigningPreviewLineKind.SUMMARY,
                _rect_summary(preview.signature_rect),
            ),
            SigningPreviewLine(SigningPreviewLineKind.SUMMARY, _appearance_summary(preview)),
        ]
    )

    lines.extend(
        SigningPreviewLine(SigningPreviewLineKind.SUMMARY, summary)
        for summary in _metadata_summary(preview)
    )

    lines.extend(
        SigningPreviewLine(SigningPreviewLineKind.SUMMARY, summary)
        for summary in _style_summary(preview)
    )

    lines.extend(
        SigningPreviewLine(
            SigningPreviewLineKind.FIELD,
            _format_field_line(field, show_field_names=preview.show_field_names),
        )
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


def render_canonical_signature_preview(
    preview: SigningDraftPreview,
    *,
    zoom: float = 2.0,
    render_port: PreviewRasterRenderer | None = None,
    render_backend: Any | None = None,
    include_border: bool = True,
    flatten_to_white: bool = True,
    use_horizontal_ink_reservation: bool = True,
) -> CanonicalSignaturePreviewSnapshot | None:
    """Render the visible signature using the canonical stamp engine."""

    if render_port is not None and render_backend is not None:
        raise ValueError("Provide render_port or render_backend, not both.")
    if render_port is None and render_backend is not None:
        render_port = _LegacyPreviewRasterRenderer(render_backend)

    if (
        preview.signature_rect is None
        or preview.layout_template is None
        or preview.stamp_position is None
        or preview.datetime_format is None
        or preview.text_style is None
        or preview.box_style is None
    ):
        return None

    temp_dir = Path(mkdtemp(prefix="foliaseal-canonical-preview-"))
    full_style = _canonical_preview_stamp_style(
        preview,
        include_text=True,
        include_stamp=True,
        include_border=include_border,
        use_horizontal_ink_reservation=use_horizontal_ink_reservation,
    )
    full_layout = _canonical_preview_layout(
        preview,
        include_text=True,
        include_stamp=True,
        include_border=include_border,
        render_port=render_port,
        use_horizontal_ink_reservation=use_horizontal_ink_reservation,
    )
    full_render = _render_preview_style(
        style=full_style,
        signature_rect=preview.signature_rect,
        zoom=zoom,
        output_path=temp_dir / "full.png",
        render_port=render_port,
        flatten_to_white=flatten_to_white,
    )
    text_bounds = _render_optional_preview_bounds(
        preview=preview,
        layout=full_layout,
        zoom=zoom,
        output_path=temp_dir / "text.png",
        include_text=True,
        include_stamp=False,
        render_port=render_port,
        flatten_to_white=flatten_to_white,
    )
    stamp_bounds = _render_optional_preview_bounds(
        preview=preview,
        layout=full_layout,
        zoom=zoom,
        output_path=temp_dir / "stamp.png",
        include_text=False,
        include_stamp=True,
        render_port=render_port,
        flatten_to_white=flatten_to_white,
    )
    image_size_px = {"width": full_render[1], "height": full_render[2]}
    container_bounds_px = {
        "x": 0,
        "y": 0,
        "width": full_render[1],
        "height": full_render[2],
    }
    text_box_bounds_px = _layout_rule_bounds_px(
        full_layout.layout_plan.text_layout,
        reserved_width_pt=full_layout.layout_plan.text_box.width_pt,
        reserved_height_pt=full_layout.layout_plan.text_box.height_pt,
        width_px=full_render[1],
        height_px=full_render[2],
        container_width_pt=preview.signature_rect.width_pt,
        container_height_pt=preview.signature_rect.height_pt,
        include_when_empty=True,
    )
    border_style = _appearance_border_style(preview=preview, include_border=include_border)
    border_bounds_px = container_bounds_px if border_style is not None else None
    line_bounds_px = _structural_line_bounds_px(
        text=_semantic_preview_stamp_text(preview),
        text_fragments=tuple(_canonical_preview_text_fragments(preview)),
        text_style=preview.text_style,
        text_bounds_px=text_box_bounds_px,
    )
    appearance_snapshot = SignatureAppearanceSnapshot(
        image_path=str(full_render[0]),
        image_size_px=image_size_px,
        container_bounds_px=container_bounds_px,
        border_bounds_px=border_bounds_px,
        border_style=border_style,
        text_bounds_px=_union_rectangles(line_bounds_px) or text_box_bounds_px or text_bounds,
        stamp_bounds_px=stamp_bounds,
        text_fragments=tuple(_canonical_preview_text_fragments(preview)),
        line_bounds_px=line_bounds_px,
    )
    return CanonicalSignaturePreviewSnapshot(
        image_path=str(full_render[0]),
        width_px=full_render[1],
        height_px=full_render[2],
        text_area_bounds_px=_layout_rule_bounds_px(
            full_layout.layout_plan.text_layout,
            reserved_width_pt=full_layout.layout_plan.text_area_width_pt,
            reserved_height_pt=full_layout.layout_plan.text_area_height_pt,
            width_px=full_render[1],
            height_px=full_render[2],
            container_width_pt=preview.signature_rect.width_pt,
            container_height_pt=preview.signature_rect.height_pt,
            include_when_empty=True,
        ),
        stamp_area_bounds_px=(
            None
            if not preview.image_stamp_path
            else _layout_rule_bounds_px(
                full_layout.layout_plan.stamp_layout,
                reserved_width_pt=full_layout.layout_plan.stamp_area_width_pt,
                reserved_height_pt=full_layout.layout_plan.stamp_area_height_pt,
                width_px=full_render[1],
                height_px=full_render[2],
                container_width_pt=preview.signature_rect.width_pt,
                container_height_pt=preview.signature_rect.height_pt,
                include_when_empty=False,
            )
        ),
        text_bounds_px=_union_rectangles(line_bounds_px) or text_box_bounds_px or text_bounds,
        stamp_bounds_px=stamp_bounds,
        appearance_snapshot=appearance_snapshot,
    )


def compare_signature_appearance_snapshots(
    preview_snapshot: SignatureAppearanceSnapshot,
    signed_snapshot: SignatureAppearanceSnapshot,
    *,
    bounds_tolerance_px: int = 6,
) -> SignatureAppearanceComparison:
    """Compare preview and signed appearance snapshots by visual layer."""

    border_reason: str | None = None
    border_matches = True
    if bool(preview_snapshot.border_bounds_px) != bool(signed_snapshot.border_bounds_px):
        border_matches = False
        border_reason = "Border presence differs between preview and signed output."
    elif (
        preview_snapshot.border_bounds_px is not None
        and signed_snapshot.border_bounds_px is not None
    ):
        border_matches = _rectangles_within_tolerance(
            preview_snapshot.border_bounds_px,
            signed_snapshot.border_bounds_px,
            tolerance_px=bounds_tolerance_px,
        )
        if not border_matches:
            border_reason = "Border bounds differ after normalization."
        elif not _border_style_matches(
            preview_snapshot.border_style,
            signed_snapshot.border_style,
        ):
            border_matches = False
            border_reason = "Border style differs between preview and signed output."

    text_reason: str | None = None
    text_matches = True
    if _normalized_text_fragments(preview_snapshot.text_fragments) != _normalized_text_fragments(
        signed_snapshot.text_fragments
    ):
        text_matches = False
        text_reason = "Visible text fragments differ."
    elif preview_snapshot.line_bounds_px or signed_snapshot.line_bounds_px:
        if not _line_bounds_within_tolerance(
            preview_snapshot.line_bounds_px,
            signed_snapshot.line_bounds_px,
            tolerance_px=bounds_tolerance_px,
        ):
            text_matches = False
            text_reason = "Rendered text line bounds differ after normalization."
    elif not _optional_rectangles_within_tolerance(
        preview_snapshot.text_bounds_px,
        signed_snapshot.text_bounds_px,
        tolerance_px=bounds_tolerance_px,
    ):
        text_matches = False
        text_reason = "Rendered text bounds differ after normalization."

    stamp_reason: str | None = None
    stamp_matches = True
    if bool(preview_snapshot.stamp_bounds_px) != bool(signed_snapshot.stamp_bounds_px):
        stamp_matches = False
        stamp_reason = "Stamp presence differs between preview and signed output."
    elif not _optional_rectangles_within_tolerance(
        preview_snapshot.stamp_bounds_px,
        signed_snapshot.stamp_bounds_px,
        tolerance_px=bounds_tolerance_px,
    ):
        stamp_matches = False
        stamp_reason = "Rendered stamp bounds differ after normalization."

    composite_matches = preview_snapshot.image_size_px == signed_snapshot.image_size_px
    composite_reason = (
        None if composite_matches else "Normalized preview and signed image dimensions differ."
    )

    border = SignatureAppearanceLayerComparison(
        layer_name="border",
        matches=border_matches,
        reason=border_reason,
    )
    text = SignatureAppearanceLayerComparison(
        layer_name="text",
        matches=text_matches,
        reason=text_reason,
    )
    stamp = SignatureAppearanceLayerComparison(
        layer_name="stamp",
        matches=stamp_matches,
        reason=stamp_reason,
    )
    composite = SignatureAppearanceLayerComparison(
        layer_name="composite",
        matches=composite_matches,
        reason=composite_reason,
    )
    return SignatureAppearanceComparison(
        is_consistent=(border.matches and text.matches and stamp.matches and composite.matches),
        border=border,
        text=text,
        stamp=stamp,
        composite=composite,
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

    if preview.stamp_position != request_appearance.stamp_position:
        issues.append(
            SigningPreviewParityIssue(
                code="stamp_position_mismatch",
                message="Preview stamp position does not match the final request.",
                field_name="stamp_position",
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

    if preview.show_field_names != request_appearance.show_field_names:
        issues.append(
            SigningPreviewParityIssue(
                code="show_field_names_mismatch",
                message="Preview field-name display mode does not match the final request.",
                field_name="show_field_names",
            )
        )

    if preview.datetime_format != request_appearance.datetime_format:
        issues.append(
            SigningPreviewParityIssue(
                code="datetime_format_mismatch",
                message="Preview datetime format does not match the final request.",
                field_name="datetime_format",
            )
        )

    if preview.image_stamp_path != request_appearance.image_stamp_path:
        issues.append(
            SigningPreviewParityIssue(
                code="image_stamp_path_mismatch",
                message="Preview image stamp path does not match the final request.",
                field_name="image_stamp_path",
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

    issues.extend(_compare_preview_fields_to_appearance(preview.fields, request_appearance))

    return SigningPreviewParityReport(is_consistent=not issues, issues=tuple(issues))


def _canonical_preview_text_fragments(preview: SigningDraftPreview) -> list[str]:
    return _rendered_text_fragments(_semantic_preview_stamp_text(preview))


def _appearance_border_style(
    *,
    preview: SigningDraftPreview,
    include_border: bool,
) -> dict[str, Any] | None:
    if preview.box_style is None or not include_border or not preview.box_style.show_border:
        return None
    return {
        "show_border": True,
        "shape": "rounded",
        "border_color_hex": preview.box_style.border_color_hex,
        "border_width_pt": preview.box_style.border_width_pt,
        "background_color_hex": preview.box_style.background_color_hex,
    }


def _border_style_matches(
    left: dict[str, Any] | None,
    right: dict[str, Any] | None,
) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return left == right


def _rendered_text_fragments(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _normalized_text_fragments(fragments: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_normalize_text_fragment(fragment) for fragment in fragments if fragment.strip())


def _normalize_text_fragment(fragment: str) -> str:
    normalized = re.sub(
        r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?(?:\s+[A-Z]{2,5})?\b",
        "<signing_time>",
        fragment,
    )
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _structural_line_bounds_px(
    *,
    text: str,
    text_fragments: tuple[str, ...],
    text_style: SignatureTextStyle | None,
    text_bounds_px: dict[str, int] | None,
) -> tuple[dict[str, int], ...]:
    if text_style is None or text_bounds_px is None or not text_fragments:
        return ()
    return tuple(
        bounds.as_dict()
        for bounds in structural_line_bounds(
            text=text,
            text_fragments=text_fragments,
            text_style=text_style,
            text_bounds=_rect_bounds_from_mapping(text_bounds_px),
        )
    )


def _union_rectangles(
    rectangles: tuple[dict[str, int], ...],
) -> dict[str, int] | None:
    if not rectangles:
        return None
    min_x = min(rect["x"] for rect in rectangles)
    min_y = min(rect["y"] for rect in rectangles)
    max_x = max(rect["x"] + rect["width"] for rect in rectangles)
    max_y = max(rect["y"] + rect["height"] for rect in rectangles)
    return {
        "x": min_x,
        "y": min_y,
        "width": max_x - min_x,
        "height": max_y - min_y,
    }


def _optional_rectangles_within_tolerance(
    left: dict[str, int] | None,
    right: dict[str, int] | None,
    *,
    tolerance_px: int,
) -> bool:
    if left is None and right is None:
        return True
    if left is None or right is None:
        return False
    return _rectangles_within_tolerance(left, right, tolerance_px=tolerance_px)


def _rectangles_within_tolerance(
    left: dict[str, int],
    right: dict[str, int],
    *,
    tolerance_px: int,
) -> bool:
    for key in ("x", "y", "width", "height"):
        if abs(int(left[key]) - int(right[key])) > tolerance_px:
            return False
    return True


def _line_bounds_within_tolerance(
    left: tuple[dict[str, int], ...],
    right: tuple[dict[str, int], ...],
    *,
    tolerance_px: int,
) -> bool:
    if len(left) != len(right):
        return False
    return all(
        _rectangles_within_tolerance(left_rect, right_rect, tolerance_px=tolerance_px)
        for left_rect, right_rect in zip(left, right, strict=True)
    )


def _semantic_preview_stamp_text(preview: SigningDraftPreview) -> str:
    if preview.stamp_text:
        return preview.stamp_text
    title_text = (preview.signer_label_prefix or preview.title or "").strip()
    detail_text = (preview.detail_text or "").strip()
    if title_text and detail_text:
        return f"{title_text}\n{detail_text}"
    if title_text:
        return title_text
    if detail_text:
        return detail_text
    return "No visible fields selected"


def _canonical_preview_stamp_style(
    preview: SigningDraftPreview,
    *,
    include_text: bool,
    include_stamp: bool,
    include_border: bool,
    use_horizontal_ink_reservation: bool = True,
) -> TextStampStyle:
    layout = _canonical_preview_layout(
        preview,
        include_text=include_text,
        include_stamp=include_stamp,
        include_border=include_border,
        use_horizontal_ink_reservation=use_horizontal_ink_reservation,
    )
    return layout.style


@dataclass(frozen=True)
class _CanonicalPreviewLayout:
    style: TextStampStyle
    background_layout: Any
    inner_content_layout: Any
    layout_plan: SignatureLayoutPlan


def _canonical_preview_layout(
    preview: SigningDraftPreview,
    *,
    include_text: bool,
    include_stamp: bool,
    include_border: bool,
    render_port: PreviewRasterRenderer | None = None,
    use_horizontal_ink_reservation: bool = True,
) -> _CanonicalPreviewLayout:
    assert preview.signature_rect is not None
    assert preview.layout_template is not None
    assert preview.stamp_position is not None
    assert preview.text_style is not None
    assert preview.box_style is not None
    assert preview.datetime_format is not None

    appearance = SigningBackendAppearance(
        signer_label_prefix=preview.signer_label_prefix or preview.title or "",
        layout_template=preview.layout_template,
        stamp_position=preview.stamp_position,
        timezone_display_mode=preview.timezone_display_mode or SignatureTimezoneDisplayMode.LOCAL,
        show_field_names=preview.show_field_names,
        datetime_format=preview.datetime_format,
        field_bindings=(),
        text_style=preview.text_style,
        box_style=preview.box_style,
        image_stamp_path=preview.image_stamp_path if include_stamp else None,
        image_prominence=preview.image_prominence,
        preserve_image_alpha=preview.preserve_image_alpha,
    )
    stamp_text = _semantic_preview_stamp_text(preview) if include_text else " "
    stamp_background = stamp_background_for_path(appearance.image_stamp_path)
    ink_measurer = (
        _PreviewHorizontalInkMeasurer(preview, render_port)
        if use_horizontal_ink_reservation
        else None
    )
    preparation = VisibleSignatureLayoutService.production().prepare(
        VisibleSignatureLayoutRequest(
            appearance=appearance,
            signature_rect=preview.signature_rect,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            options=VisibleSignatureLayoutOptions(
                include_text=include_text,
                include_stamp=include_stamp,
                include_border=include_border,
                include_background=include_stamp,
                allow_fit_issues=True,
                horizontal_ink_policy=(
                    "auto" if use_horizontal_ink_reservation else "disabled"
                ),
            ),
            ink_measurer=ink_measurer,
        )
    )
    service_layout = preparation.preview()
    return _CanonicalPreviewLayout(
        style=service_layout.style,
        background_layout=service_layout.background_layout,
        inner_content_layout=service_layout.content_layout,
        layout_plan=service_layout.layout_plan,
    )


@dataclass(frozen=True)
class _PreviewHorizontalInkMeasurer:
    preview: SigningDraftPreview
    render_port: PreviewRasterRenderer | None = None

    def measure(
        self,
        request: HorizontalInkMeasurementRequest,
    ) -> HorizontalInkMeasurement | None:
        reference = measure_horizontal_single_line_rendered_reference(
            self.preview,
            zoom=1.0,
            render_port=self.render_port,
        )
        if reference is None:
            return None
        return HorizontalInkMeasurement(
            structural_text_bounds_px=_rect_bounds_from_mapping(
                reference.structural_text_bounds_px
            ),
            rendered_ink_bounds_px=_rect_bounds_from_mapping(reference.rendered_ink_bounds_px),
            px_to_pt=reference.px_to_pt,
        )


def _rect_bounds_from_mapping(bounds: dict[str, int]) -> RectBounds:
    return RectBounds(
        x=bounds["x"],
        y=bounds["y"],
        width=bounds["width"],
        height=bounds["height"],
    )


def _stamp_aspect_ratio(stamp_background: PdfContent | None) -> float | None:
    image = getattr(stamp_background, "image", None)
    if image is None or not hasattr(image, "size"):
        return None
    width, height = image.size
    if width <= 0 or height <= 0:
        return None
    return width / height


def _render_optional_preview_bounds(
    *,
    preview: SigningDraftPreview,
    layout: _CanonicalPreviewLayout,
    zoom: float,
    output_path: Path,
    include_text: bool,
    include_stamp: bool,
    flatten_to_white: bool,
    render_port: PreviewRasterRenderer | None = None,
    render_backend: Any | None = None,
) -> dict[str, int] | None:
    if not include_text and not include_stamp:
        return None
    if include_stamp and layout.style.background is None:
        return None
    if render_port is not None and render_backend is not None:
        raise ValueError("Provide render_port or render_backend, not both.")
    if render_port is None and render_backend is not None:
        render_port = _LegacyPreviewRasterRenderer(render_backend)
    style = TextStampStyle(
        border_width=0,
        border_color=layout.style.border_color,
        background=layout.style.background if include_stamp else None,
        background_layout=layout.background_layout,
        background_opacity=layout.style.background_opacity,
        text_box_style=layout.style.text_box_style,
        inner_content_layout=layout.inner_content_layout,
        stamp_text=layout.style.stamp_text if include_text else " ",
        timestamp_format=layout.style.timestamp_format,
    )
    image_path, _width_px, _height_px = _render_preview_style(
        style=style,
        signature_rect=preview.signature_rect,
        zoom=zoom,
        output_path=output_path,
        render_port=render_port,
        flatten_to_white=flatten_to_white,
    )
    with Image.open(image_path) as image:
        rgba_image = image.convert("RGBA")
    return _non_white_bounds(rgba_image)


def _render_preview_style(
    *,
    style: TextStampStyle,
    signature_rect: SignatureRect,
    zoom: float,
    output_path: Path,
    render_port: PreviewRasterRenderer | None,
    flatten_to_white: bool,
) -> tuple[Path, int, int]:
    width_pt = max(1, int(round(signature_rect.width_pt)))
    height_pt = max(1, int(round(signature_rect.height_pt)))
    writer = PdfFileWriter()
    empty_stream = writer.add_object(StreamObject(stream_data=b""))
    page = PageObject(
        contents=empty_stream,
        media_box=(0, 0, width_pt, height_pt),
    )
    writer.insert_page(page)
    stamp = style.create_stamp(
        writer,
        box=BoxConstraints(width=width_pt, height=height_pt),
        text_params={},
    )
    stamp.apply(0, 0, 0)
    pdf_path = output_path.with_suffix(".pdf")
    with pdf_path.open("wb") as handle:
        writer.write(handle)
    renderer = render_port or _default_preview_raster_renderer()
    render = renderer.render_page(
        PreviewRasterRequest(
            document_path=str(pdf_path),
            page_index=0,
            zoom=zoom,
        )
    )
    image = Image.frombytes(
        "RGBA",
        (render.width_px, render.height_px),
        render.rgba_bytes,
    )
    if flatten_to_white:
        flattened = Image.new("RGBA", image.size, (255, 255, 255, 255))
        flattened.alpha_composite(image)
        flattened.save(output_path)
    else:
        image.save(output_path)
    pdf_path.unlink(missing_ok=True)
    return output_path, render.width_px, render.height_px


@dataclass(frozen=True)
class _LegacyPreviewRasterRenderer:
    """Temporary adapter for callers that still pass the old backend object."""

    backend: Any

    def render_page(self, request: PreviewRasterRequest) -> PreviewRasterResult:
        from foliaseal.infra.render.base import RenderPageRequest

        result = self.backend.render_page(
            RenderPageRequest(
                document_path=str(request.document_path),
                page_index=request.page_index,
                zoom=request.zoom,
            )
        )
        return PreviewRasterResult(
            width_px=result.width_px,
            height_px=result.height_px,
            rgba_bytes=result.rgba_bytes,
        )


def _default_preview_raster_renderer() -> PreviewRasterRenderer:
    """Build the legacy direct-call renderer without a module-level Qt import."""

    from foliaseal.infra.render import QtPdfRenderBackend

    return _LegacyPreviewRasterRenderer(QtPdfRenderBackend())


def _layout_rule_bounds_px(
    rule: Any,
    *,
    reserved_width_pt: float,
    reserved_height_pt: float,
    width_px: int,
    height_px: int,
    container_width_pt: float,
    container_height_pt: float,
    include_when_empty: bool,
) -> dict[str, int] | None:
    margins = getattr(rule, "margins", None)
    if margins is None:
        return None
    left = int(round(getattr(margins, "left", 0)))
    top = int(round(getattr(margins, "top", 0)))
    scale_x = width_px / max(container_width_pt, 1.0)
    scale_y = height_px / max(container_height_pt, 1.0)
    x = int(round(left * scale_x))
    y = int(round(top * scale_y))
    width = max(0, int(round(reserved_width_pt * scale_x)))
    height = max(0, int(round(reserved_height_pt * scale_y)))
    if not include_when_empty and (width == 0 or height == 0):
        return None
    return {"x": x, "y": y, "width": width, "height": height}


def _non_white_bounds(image: Image.Image) -> dict[str, int] | None:
    width, height = image.size
    pixels = image.load()
    min_x = width
    min_y = height
    max_x = -1
    max_y = -1
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            if red >= 250 and green >= 250 and blue >= 250:
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        return None
    return {
        "x": min_x,
        "y": min_y,
        "width": (max_x - min_x) + 1,
        "height": (max_y - min_y) + 1,
    }


def _compare_preview_fields_to_appearance(
    preview_fields: tuple[SigningDraftPreviewField, ...],
    appearance: SignatureAppearance,
) -> list[SigningPreviewParityIssue]:
    issues: list[SigningPreviewParityIssue] = []
    expected_bindings = appearance.iter_field_bindings()

    if len(preview_fields) != len(expected_bindings):
        issues.append(
            SigningPreviewParityIssue(
                code="field_count_mismatch",
                message="Preview field count does not match the final request.",
                field_name="signature_appearance",
            )
        )
        return issues

    for preview_field, (field_key, binding) in zip(preview_fields, expected_bindings, strict=True):
        expected_label = _field_label(field_key)
        expected_visible = (
            binding.show_in_visible_appearance and binding.source != SignatureFieldSource.HIDDEN
        )

        if preview_field.field_key != field_key:
            issues.append(
                SigningPreviewParityIssue(
                    code="field_order_mismatch",
                    message="Preview field order does not match the final request.",
                    field_name="signature_appearance",
                )
            )
            continue

        if preview_field.label != expected_label:
            issues.append(
                SigningPreviewParityIssue(
                    code="field_label_mismatch",
                    message="Preview field labels do not match the final request.",
                    field_name=field_key.value,
                )
            )

        if preview_field.visible != expected_visible or preview_field.source != binding.source:
            issues.append(
                SigningPreviewParityIssue(
                    code="field_visibility_mismatch",
                    message="Preview field visibility does not match the final request.",
                    field_name=field_key.value,
                )
            )
            continue

        if binding.source == SignatureFieldSource.OVERRIDE:
            if (
                preview_field.text != (binding.override_text or "")
                or preview_field.hint is not None
            ):
                issues.append(
                    SigningPreviewParityIssue(
                        code="override_field_mismatch",
                        message="Override field rendering does not match the final request.",
                        field_name=field_key.value,
                    )
                )
        elif binding.source == SignatureFieldSource.DERIVED:
            expected_hint = (
                "sign time" if field_key == SignatureFieldKey.SIGNING_TIME else "from certificate"
            )
            if not preview_field.text or preview_field.hint != expected_hint:
                issues.append(
                    SigningPreviewParityIssue(
                        code="derived_field_structure_mismatch",
                        message=(
                            "Derived field parity is structural only; preview must show a "
                            "visible placeholder and the correct derivation hint."
                        ),
                        field_name=field_key.value,
                    )
                )
        else:
            if preview_field.text or preview_field.hint is not None:
                issues.append(
                    SigningPreviewParityIssue(
                        code="hidden_field_mismatch",
                        message="Hidden field rendering does not match the final request.",
                        field_name=field_key.value,
                    )
                )

    return issues
