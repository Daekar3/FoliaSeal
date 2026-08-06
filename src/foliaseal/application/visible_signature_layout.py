"""Visible-signature layout planning boundary.

This module is the application-layer seam for visible-signature geometry.
It owns the shared reservation, placement, and fit-policy helpers used by the
signing and preview adapters. Callers prepare one neutral plan and materialize
target-specific outputs from that preparation.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field, replace
from math import ceil
from pathlib import Path
from typing import Literal, Protocol

from foliaseal.application.horizontal_signature_reservation import (
    HorizontalSingleLineInkReservation,
    build_horizontal_single_line_ink_reservation,
)
from foliaseal.application.signing_draft_workflow import SigningDraftValidationSeverity
from foliaseal.application.visible_signature_color import text_style_color_rgba
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
)

_SINGLE_LINE_RENDERED_INK_FIT_CACHE: dict[tuple[object, ...], bool] = {}


@dataclass(frozen=True)
class TextMetrics:
    """Measured visible-signature text box dimensions in PDF points."""

    width_pt: int
    height_pt: int
    line_count: int


@dataclass(frozen=True)
class ImageMetrics:
    """Stamp image dimensions used by layout policy."""

    width_px: int
    height_px: int
    aspect_ratio: float


@dataclass(frozen=True)
class RectBounds:
    """Integer rectangle bounds, usually from raster measurements."""

    x: int
    y: int
    width: int
    height: int

    def as_dict(self) -> dict[str, int]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True)
class HorizontalInkMeasurementRequest:
    """Inputs needed to measure horizontal single-line rendered ink."""

    signature_rect: SignatureRect
    layout_template: SignatureLayoutTemplate
    stamp_position: SignatureStampPosition
    text_style: SignatureTextStyle
    box_style: SignatureBoxStyle
    stamp_text: str
    image_stamp_path: str
    structural_text_box_width_pt: int
    structural_text_box_height_pt: int


@dataclass(frozen=True)
class HorizontalInkMeasurement:
    """Rendered ink bounds measured from a local preview render."""

    structural_text_bounds_px: RectBounds
    rendered_ink_bounds_px: RectBounds
    px_to_pt: float


@dataclass(frozen=True)
class HorizontalInkReservation:
    """Point-space text lane reservation derived from rendered ink."""

    lane_width_pt: int
    ink_width_pt: int
    ink_height_pt: int
    ink_left_offset_pt: int
    ink_right_slack_pt: int
    border_facing_padding_pt: int
    stamp_facing_padding_pt: int


@dataclass(frozen=True)
class LayoutMargins:
    """Margins for a layout rule in PDF points."""

    left: int
    right: int
    top: int
    bottom: int


@dataclass(frozen=True)
class LayoutRuleSpec:
    """Plain-data view of a pyHanko layout rule."""

    x_align: str
    y_align: str
    margins: LayoutMargins
    scaling: str


class VisibleSignatureAppearancePort(Protocol):
    """Structural appearance view required by neutral layout policy."""

    layout_template: SignatureLayoutTemplate
    stamp_position: SignatureStampPosition
    datetime_format: str
    text_style: SignatureTextStyle
    box_style: SignatureBoxStyle
    image_stamp_path: str | None


def _layout_rule_spec_from_parts(
    *,
    x_align: str,
    y_align: str,
    margins: LayoutMargins,
    scaling: str,
) -> LayoutRuleSpec:
    return LayoutRuleSpec(
        x_align=x_align,
        y_align=y_align,
        margins=margins,
        scaling=scaling,
    )


def _layout_margins(*, left: int, right: int, top: int, bottom: int) -> LayoutMargins:
    return LayoutMargins(left=left, right=right, top=top, bottom=bottom)


def _layout_rule(
    *,
    x_align: str,
    y_align: str,
    margins: LayoutMargins,
    scaling: str,
) -> LayoutRuleSpec:
    return _layout_rule_spec_from_parts(
        x_align=x_align,
        y_align=y_align,
        margins=margins,
        scaling=scaling,
    )


@dataclass(frozen=True)
class _SignatureLayoutReservation:
    """Explicit split of reserved stamp and text space inside the rectangle."""

    layout_template: SignatureLayoutTemplate
    stamp_position: SignatureStampPosition
    container_width_pt: int
    container_height_pt: int
    text_box_width_pt: int
    text_box_height_pt: int
    reserved_primary_extent_pt: int
    stamp_area_width_pt: int
    stamp_area_height_pt: int
    text_area_width_pt: int
    text_area_height_pt: int
    background_layout: LayoutRuleSpec
    inner_content_layout: LayoutRuleSpec


def _base_layout_spacing(
    *,
    stamp_position: SignatureStampPosition,
    box_height: int,
) -> tuple[int, int]:
    if stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}:
        edge_margin = max(2, min(4, int(round(box_height * 0.08))))
        gap = max(1, min(6, int(round(box_height * 0.14)) - 2))
        return edge_margin, gap
    return 4, 6


def _effective_layout_edge_margin(
    *,
    stamp_position: SignatureStampPosition,
    box_height: int,
    box_style: SignatureBoxStyle | None,
) -> int:
    base_edge_margin, _gap = _base_layout_spacing(
        stamp_position=stamp_position,
        box_height=box_height,
    )
    return max(base_edge_margin, _border_safe_inset(box_style))


def _single_line_vertical_outer_margin(
    *,
    box_height: int,
    box_style: SignatureBoxStyle | None,
) -> int:
    return _effective_layout_edge_margin(
        stamp_position=SignatureStampPosition.TOP,
        box_height=box_height,
        box_style=box_style,
    )


def _single_line_no_stamp_vertical_optical_shift(
    *,
    available_height: int,
    text_box_height: int,
    outer_margin: int,
) -> int:
    free_height = max(0, available_height - text_box_height)
    return min(free_height, max(0, outer_margin))


def _effective_horizontal_text_reservation_width(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    text_box_width: int,
) -> int:
    if layout_template == SignatureLayoutTemplate.SINGLE_LINE and stamp_position in {
        SignatureStampPosition.LEFT,
        SignatureStampPosition.RIGHT,
    }:
        return text_box_width
    return max(text_box_width, int(round(text_box_width * 0.95)))


def _layout_reservation_for_template(
    layout_template: SignatureLayoutTemplate,
    *,
    stamp_position: SignatureStampPosition,
    signature_rect: SignatureRect,
    text_box_width: int,
    text_box_height: int,
    box_style: SignatureBoxStyle | None = None,
    has_visible_stamp_image: bool = True,
    stamp_aspect_ratio: float | None = None,
) -> _SignatureLayoutReservation:
    box_width = max(1, int(round(signature_rect.width_pt)))
    box_height = max(1, int(round(signature_rect.height_pt)))
    base_edge_margin, gap = _base_layout_spacing(
        stamp_position=stamp_position,
        box_height=box_height,
    )
    edge_margin = max(base_edge_margin, _border_safe_inset(box_style))
    available_width = max(box_width - edge_margin * 2, 0)
    available_height = max(box_height - edge_margin * 2, 0)

    if layout_template == SignatureLayoutTemplate.SINGLE_LINE and not has_visible_stamp_image:
        vertical_margin = edge_margin
        if stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}:
            vertical_margin = _single_line_vertical_outer_margin(
                box_height=box_height,
                box_style=box_style,
            )
            available_height = max(box_height - vertical_margin * 2, 0)
        optical_shift = _single_line_no_stamp_vertical_optical_shift(
            available_height=available_height,
            text_box_height=text_box_height,
            outer_margin=vertical_margin,
        )
        full_margins = _layout_margins(
            left=edge_margin,
            right=edge_margin,
            top=max(0, vertical_margin - optical_shift),
            bottom=vertical_margin + optical_shift,
        )
        return _SignatureLayoutReservation(
            layout_template=layout_template,
            stamp_position=stamp_position,
            container_width_pt=box_width,
            container_height_pt=box_height,
            text_box_width_pt=text_box_width,
            text_box_height_pt=text_box_height,
            reserved_primary_extent_pt=0,
            stamp_area_width_pt=0,
            stamp_area_height_pt=0,
            text_area_width_pt=available_width,
            text_area_height_pt=available_height,
            background_layout=_layout_rule(
                x_align="ALIGN_MID",
                y_align="ALIGN_MID",
                margins=full_margins,
                scaling="STRETCH_TO_FIT",
            ),
            inner_content_layout=_layout_rule(
                x_align=(
                    "ALIGN_MIN"
                    if stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.LEFT}
                    else "ALIGN_MID"
                ),
                y_align="ALIGN_MAX",
                margins=full_margins,
                scaling="NO_SCALING",
            ),
        )

    if stamp_position in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}:
        text_area_width = min(
            _effective_horizontal_text_reservation_width(
                layout_template=layout_template,
                stamp_position=stamp_position,
                text_box_width=text_box_width,
            ),
            available_width,
        )
        remaining_width = max(available_width - text_area_width, 0)
        separator_width = min(gap, remaining_width)
        stamp_area_width = max(remaining_width - separator_width, 0)
        reserved_primary_extent = stamp_area_width
        stamp_area_height = available_height
        text_area_height = available_height

        if stamp_position == SignatureStampPosition.LEFT:
            background_margins = _layout_margins(
                left=edge_margin,
                right=text_area_width + separator_width + edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            text_margins = _layout_margins(
                left=stamp_area_width + separator_width + edge_margin,
                right=edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            background_alignment = "ALIGN_MIN"
            text_alignment = "ALIGN_MAX"
        else:
            background_margins = _layout_margins(
                left=text_area_width + separator_width + edge_margin,
                right=edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            text_margins = _layout_margins(
                left=edge_margin,
                right=stamp_area_width + separator_width + edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            background_alignment = "ALIGN_MAX"
            text_alignment = "ALIGN_MIN"

        return _SignatureLayoutReservation(
            layout_template=layout_template,
            stamp_position=stamp_position,
            container_width_pt=box_width,
            container_height_pt=box_height,
            text_box_width_pt=text_box_width,
            text_box_height_pt=text_box_height,
            reserved_primary_extent_pt=reserved_primary_extent,
            stamp_area_width_pt=stamp_area_width,
            stamp_area_height_pt=stamp_area_height,
            text_area_width_pt=text_area_width,
            text_area_height_pt=text_area_height,
            background_layout=_layout_rule(
                x_align=background_alignment,
                y_align="ALIGN_MID",
                margins=background_margins,
                scaling="STRETCH_TO_FIT",
            ),
            inner_content_layout=_layout_rule(
                x_align=text_alignment,
                y_align="ALIGN_MID",
                margins=text_margins,
                scaling="NO_SCALING",
            ),
        )

    vertical_top_margin = edge_margin
    vertical_bottom_margin = edge_margin
    if stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}:
        vertical_top_margin = _single_line_vertical_outer_margin(
            box_height=box_height,
            box_style=box_style,
        )
        vertical_bottom_margin = vertical_top_margin
        available_width = max(box_width - edge_margin * 2, 0)
        available_height = max(box_height - vertical_top_margin - vertical_bottom_margin, 0)
    text_area_height = min(text_box_height, available_height)
    remaining_height = max(available_height - text_area_height, 0)
    separator_height = min(gap, remaining_height)
    text_area_width = available_width
    stamp_area_width = available_width
    stamp_area_height = max(remaining_height - separator_height, 0)
    reserved_primary_extent = stamp_area_height

    if stamp_position == SignatureStampPosition.TOP:
        background_margins = _layout_margins(
            left=edge_margin,
            right=edge_margin,
            top=vertical_top_margin,
            bottom=text_area_height + separator_height + vertical_bottom_margin,
        )
        text_margins = _layout_margins(
            left=edge_margin,
            right=edge_margin,
            top=stamp_area_height + separator_height + vertical_top_margin,
            bottom=vertical_bottom_margin,
        )
        background_alignment = "ALIGN_MID"
        text_alignment = (
            "ALIGN_MIN"
            if layout_template == SignatureLayoutTemplate.SINGLE_LINE
            and has_visible_stamp_image
            and stamp_aspect_ratio is not None
            else "ALIGN_MID"
        )
        background_y_alignment = "ALIGN_MAX"
        text_y_alignment = "ALIGN_MIN"
    else:
        background_margins = _layout_margins(
            left=edge_margin,
            right=edge_margin,
            top=text_area_height + separator_height + vertical_top_margin,
            bottom=vertical_bottom_margin,
        )
        text_margins = _layout_margins(
            left=edge_margin,
            right=edge_margin,
            top=vertical_top_margin,
            bottom=stamp_area_height + separator_height + vertical_bottom_margin,
        )
        background_alignment = "ALIGN_MID"
        text_alignment = (
            "ALIGN_MIN"
            if layout_template == SignatureLayoutTemplate.SINGLE_LINE
            and has_visible_stamp_image
            and stamp_aspect_ratio is not None
            else "ALIGN_MID"
        )
        if layout_template == SignatureLayoutTemplate.SINGLE_LINE:
            background_y_alignment = "ALIGN_MID"
            text_y_alignment = "ALIGN_MID"
        else:
            background_y_alignment = "ALIGN_MIN"
            text_y_alignment = "ALIGN_MAX"

    return _SignatureLayoutReservation(
        layout_template=layout_template,
        stamp_position=stamp_position,
        container_width_pt=box_width,
        container_height_pt=box_height,
        text_box_width_pt=text_box_width,
        text_box_height_pt=text_box_height,
        reserved_primary_extent_pt=reserved_primary_extent,
        stamp_area_width_pt=stamp_area_width,
        stamp_area_height_pt=stamp_area_height,
        text_area_width_pt=text_area_width,
        text_area_height_pt=text_area_height,
        background_layout=_layout_rule(
            x_align=background_alignment,
            y_align=background_y_alignment,
            margins=background_margins,
            scaling="STRETCH_TO_FIT",
        ),
        inner_content_layout=_layout_rule(
            x_align=text_alignment,
            y_align=text_y_alignment,
            margins=text_margins,
            scaling="NO_SCALING",
        ),
    )


@dataclass(frozen=True)
class VisibleSignatureFitIssue:
    """Typed layout fit issue returned by the planning boundary."""

    code: str
    message: str
    severity: SigningDraftValidationSeverity = SigningDraftValidationSeverity.ERROR
    field_name: str = "signature_appearance"


@dataclass(frozen=True)
class VisibleSignatureLayoutInput:
    """Public inputs for visible-signature layout planning."""

    signature_rect: SignatureRect
    layout_template: SignatureLayoutTemplate
    stamp_position: SignatureStampPosition
    text_style: SignatureTextStyle
    box_style: SignatureBoxStyle
    stamp_text: str
    image_stamp_path: str | None
    use_horizontal_ink_reservation: bool = True


@dataclass(frozen=True)
class LayoutRequest(VisibleSignatureLayoutInput):
    """Compatibility name for visible-signature layout planning inputs."""


@dataclass(frozen=True)
class VisibleSignatureLayoutOptions:
    """Optional layout facade switches for signing and preview adapters."""

    include_text: bool = True
    include_stamp: bool = True
    include_border: bool = True
    include_background: bool = True
    allow_fit_issues: bool = False
    horizontal_ink_policy: Literal["auto", "disabled"] = "auto"


@dataclass(frozen=True)
class VisibleSignatureLayoutRequest:
    """Complete input for one prepare-once layout operation."""

    appearance: VisibleSignatureAppearancePort
    signature_rect: SignatureRect
    stamp_text: str
    stamp_background: object | None = None
    options: VisibleSignatureLayoutOptions = field(default_factory=VisibleSignatureLayoutOptions)
    ink_measurer: HorizontalInkMeasurer | None = None


@dataclass(frozen=True)
class SignatureLayoutPlan:
    """Canonical visible-signature layout result for callers and adapters."""

    container_width_pt: int
    container_height_pt: int
    text_box: TextMetrics
    has_visible_stamp_image: bool
    text_area_width_pt: int
    text_area_height_pt: int
    stamp_area_width_pt: int
    stamp_area_height_pt: int
    reserved_primary_extent_pt: int
    text_layout: LayoutRuleSpec
    stamp_layout: LayoutRuleSpec
    background_text_box_width_pt: int
    ink_reservation: HorizontalInkReservation | None
    fit_issues: tuple[VisibleSignatureFitIssue, ...]
    stamp_image: ImageMetrics | None


@dataclass(frozen=True)
class SigningVisibleSignatureStyle:
    """Opaque signing style bundle produced from a prepared layout."""

    stamp_style: object
    content_layout: object
    background_layout: object
    layout_plan: SignatureLayoutPlan
    fit_issues: tuple[VisibleSignatureFitIssue, ...]


@dataclass(frozen=True)
class CanonicalPreviewLayout:
    """Canonical preview style bundle built by the layout service."""

    style: object
    background_layout: object
    content_layout: object
    layout_plan: SignatureLayoutPlan
    stamp_suppressed: bool
    fit_issues: tuple[VisibleSignatureFitIssue, ...]


class VisibleSignatureLayoutPort(Protocol):
    """Application-owned prepare-once boundary for visible-signature layout."""

    def prepare(self, request: VisibleSignatureLayoutRequest) -> VisibleSignaturePreparation:
        """Prepare one neutral plan for target-specific materializers."""


class SignatureAppearanceMaterializer(Protocol):
    """Port for materializing a prepared plan for a concrete target."""

    def build_stamp_style(
        self,
        *,
        appearance: VisibleSignatureAppearancePort,
        stamp_text: str,
        stamp_background: object | None,
        signature_rect: SignatureRect,
        layout_plan: SignatureLayoutPlan,
        allow_fit_issues: bool = False,
        include_border: bool = True,
        include_background: bool = True,
    ) -> object:
        """Materialize a concrete signing or preview style."""


@dataclass(frozen=True)
class VisibleSignaturePreparation:
    """One immutable neutral plan with lazy target-specific materialization."""

    layout_plan: SignatureLayoutPlan
    reservation_snapshot: dict[str, object]
    fit_issues: tuple[VisibleSignatureFitIssue, ...]
    plan_fingerprint: tuple[object, ...]
    _service: VisibleSignatureLayoutService
    _request: VisibleSignatureLayoutRequest
    _preview_plan: SignatureLayoutPlan
    _preview_stamp_suppressed: bool
    _appearance_materializer: SignatureAppearanceMaterializer | None = None
    fit_gate_passed: bool = True
    fit_gate_error: str | None = None
    _signing_result: SigningVisibleSignatureStyle | None = None
    _preview_result: CanonicalPreviewLayout | None = None

    def signing(self) -> SigningVisibleSignatureStyle:
        """Materialize signing output from the prepared plan exactly once."""

        if self._signing_result is None:
            options = self._request.options
            effective_stamp_text = self._request.stamp_text if options.include_text else " "
            stamp_style = _appearance_materializer(self._appearance_materializer).build_stamp_style(
                appearance=self._request.appearance,
                stamp_text=effective_stamp_text,
                stamp_background=(
                    self._request.stamp_background
                    if options.include_stamp and options.include_background
                    else None
                ),
                signature_rect=self._request.signature_rect,
                layout_plan=self.layout_plan,
                allow_fit_issues=options.allow_fit_issues,
                include_border=options.include_border,
                include_background=options.include_background,
            )
            object.__setattr__(
                self,
                "_signing_result",
                SigningVisibleSignatureStyle(
                    stamp_style=stamp_style,
                    content_layout=stamp_style.inner_content_layout,
                    background_layout=stamp_style.background_layout,
                    layout_plan=self.layout_plan,
                    fit_issues=self.fit_issues,
                ),
            )
        return self._signing_result

    def preview(self) -> CanonicalPreviewLayout:
        """Materialize canonical preview output, explicitly deriving suppression when needed."""

        if self._preview_result is None:
            options = self._request.options
            layout_plan = self._preview_plan
            stamp_suppressed = self._preview_stamp_suppressed
            effective_stamp_text = self._request.stamp_text if options.include_text else " "
            stamp_style = _appearance_materializer(self._appearance_materializer).build_stamp_style(
                appearance=self._request.appearance,
                stamp_text=effective_stamp_text,
                stamp_background=(
                    self._request.stamp_background
                    if options.include_stamp and options.include_background and not stamp_suppressed
                    else None
                ),
                signature_rect=self._request.signature_rect,
                layout_plan=layout_plan,
                allow_fit_issues=options.allow_fit_issues,
                include_border=options.include_text and options.include_border,
                include_background=(
                    options.include_stamp and options.include_background and not stamp_suppressed
                ),
            )
            object.__setattr__(
                self,
                "_preview_result",
                CanonicalPreviewLayout(
                    style=stamp_style,
                    background_layout=stamp_style.background_layout,
                    content_layout=stamp_style.inner_content_layout,
                    layout_plan=layout_plan,
                    stamp_suppressed=stamp_suppressed,
                    fit_issues=layout_plan.fit_issues,
                ),
            )
        return self._preview_result


class TextMeasurer(Protocol):
    """Port for measuring visible-signature text."""

    def measure(self, text: str, text_style: SignatureTextStyle) -> TextMetrics:
        """Return point-space dimensions for the rendered text box."""


class StampImageProbe(Protocol):
    """Port for inspecting optional stamp image metadata."""

    def inspect(self, image_stamp_path: str | None) -> ImageMetrics | None:
        """Return image metrics or None when there is no visible stamp image."""


class HorizontalInkMeasurer(Protocol):
    """Port for local rendered-ink measurement."""

    def measure(
        self,
        request: HorizontalInkMeasurementRequest,
    ) -> HorizontalInkMeasurement | None:
        """Return rendered ink bounds for horizontal single-line layout."""


def _text_measurer_or_default(measurer: TextMeasurer | None) -> TextMeasurer:
    if measurer is not None:
        return measurer
    from foliaseal.application.visible_signature_layout_adapters import PyHankoTextMeasurer

    return PyHankoTextMeasurer()


def _image_probe_or_default(probe: StampImageProbe | None) -> StampImageProbe:
    if probe is not None:
        return probe
    from foliaseal.application.visible_signature_layout_adapters import PillowStampImageProbe

    return PillowStampImageProbe()


def _appearance_materializer(
    materializer: SignatureAppearanceMaterializer | None,
) -> SignatureAppearanceMaterializer:
    if materializer is not None:
        return materializer
    from foliaseal.application.visible_signature_layout_adapters import (
        PyHankoSignatureAppearanceAdapter,
    )

    return PyHankoSignatureAppearanceAdapter()


def structural_line_bounds(
    *,
    text: str,
    text_fragments: tuple[str, ...],
    text_style: SignatureTextStyle,
    text_bounds: RectBounds,
    text_measurer: TextMeasurer | None = None,
) -> tuple[RectBounds, ...]:
    """Return structural line boxes using the shared pyHanko text-height contract."""

    visible_fragments = tuple(fragment for fragment in text_fragments if fragment.strip())
    if not visible_fragments or text_bounds.width <= 0 or text_bounds.height <= 0:
        return ()

    measurer = _text_measurer_or_default(text_measurer)
    full_metrics = measurer.measure(text, text_style)
    if full_metrics.width_pt <= 0 or full_metrics.height_pt <= 0:
        return ()

    fragment_metrics = tuple(
        measurer.measure(fragment, text_style) for fragment in visible_fragments
    )
    max_fragment_width = max((metrics.width_pt for metrics in fragment_metrics), default=0)
    if max_fragment_width <= 0:
        return ()

    structural_height = max(text_bounds.height, int(round(full_metrics.height_pt)))
    base_line_height, extra_px = divmod(structural_height, len(visible_fragments))
    remaining_height = structural_height
    current_y = text_bounds.y
    line_bounds: list[RectBounds] = []
    for index, metrics in enumerate(fragment_metrics):
        remaining_line_count = len(fragment_metrics) - index
        if index == len(fragment_metrics) - 1:
            line_height = max(1, remaining_height)
        else:
            desired_height = max(1, base_line_height + (1 if index < extra_px else 0))
            available_for_this_line = max(1, remaining_height - (remaining_line_count - 1))
            line_height = min(desired_height, available_for_this_line)
        line_width = max(
            1,
            min(
                text_bounds.width,
                int(round(text_bounds.width * (metrics.width_pt / max_fragment_width))),
            ),
        )
        line_bounds.append(
            RectBounds(
                x=text_bounds.x,
                y=current_y,
                width=line_width,
                height=line_height,
            )
        )
        current_y += line_height
        remaining_height -= line_height
    return tuple(line_bounds)


@dataclass
class VisibleSignatureLayoutEngine:
    """Plan visible-signature layout through one application boundary."""

    text_measurer: TextMeasurer | None = None
    image_probe: StampImageProbe | None = None
    ink_measurer: HorizontalInkMeasurer | None = None

    def plan(self, request: LayoutRequest) -> SignatureLayoutPlan:
        """Return the visible-signature layout plan for one request."""

        text_measurer = _text_measurer_or_default(self.text_measurer)
        image_probe = _image_probe_or_default(self.image_probe)
        text_box = text_measurer.measure(request.stamp_text, request.text_style)
        stamp_image = image_probe.inspect(request.image_stamp_path)
        has_visible_stamp_image = stamp_image is not None

        structural_reservation = _layout_reservation_for_template(
            request.layout_template,
            stamp_position=request.stamp_position,
            signature_rect=request.signature_rect,
            text_box_width=text_box.width_pt,
            text_box_height=text_box.height_pt,
            box_style=request.box_style,
            has_visible_stamp_image=has_visible_stamp_image,
            stamp_aspect_ratio=None if stamp_image is None else stamp_image.aspect_ratio,
        )
        ink_reservation = self._horizontal_ink_reservation(
            request=request,
            text_box=text_box,
            has_visible_stamp_image=has_visible_stamp_image,
            edge_margin=_effective_layout_edge_margin(
                stamp_position=request.stamp_position,
                box_height=structural_reservation.container_height_pt,
                box_style=request.box_style,
            ),
        )
        placement_reservation = _horizontal_single_line_ink_validation_reservation(
            structural_reservation,
            ink_reservation=ink_reservation,
            signature_rect=request.signature_rect,
            box_style=request.box_style,
            has_visible_stamp_image=has_visible_stamp_image,
            stamp_aspect_ratio=None if stamp_image is None else stamp_image.aspect_ratio,
        )
        placement_reservation = _apply_horizontal_single_line_ink_text_alignment(
            placement_reservation,
            ink_reservation=ink_reservation,
        )
        fit_issues = self._fit_issues(
            placement_reservation,
            has_visible_stamp_image=has_visible_stamp_image,
            fit_checker=_ensure_layout_can_fit,
        )
        background_text_box_width = _horizontal_single_line_background_text_width(
            layout_template=request.layout_template,
            stamp_position=request.stamp_position,
            box_height=placement_reservation.container_height_pt,
            fallback_text_box_width=placement_reservation.text_box_width_pt,
            ink_reservation=ink_reservation,
        )

        return SignatureLayoutPlan(
            container_width_pt=placement_reservation.container_width_pt,
            container_height_pt=placement_reservation.container_height_pt,
            text_box=text_box,
            has_visible_stamp_image=has_visible_stamp_image,
            text_area_width_pt=placement_reservation.text_area_width_pt,
            text_area_height_pt=placement_reservation.text_area_height_pt,
            stamp_area_width_pt=placement_reservation.stamp_area_width_pt,
            stamp_area_height_pt=placement_reservation.stamp_area_height_pt,
            reserved_primary_extent_pt=placement_reservation.reserved_primary_extent_pt,
            text_layout=placement_reservation.inner_content_layout,
            stamp_layout=placement_reservation.background_layout,
            background_text_box_width_pt=background_text_box_width,
            ink_reservation=_public_ink_reservation(ink_reservation),
            fit_issues=fit_issues,
            stamp_image=stamp_image,
        )

    def validate(self, request: LayoutRequest) -> tuple[VisibleSignatureFitIssue, ...]:
        """Return only visible-signature layout fit issues."""

        return self.plan(request).fit_issues

    def _horizontal_ink_reservation(
        self,
        *,
        request: LayoutRequest,
        text_box: TextMetrics,
        has_visible_stamp_image: bool,
        edge_margin: int,
    ) -> object | None:
        if (
            self.ink_measurer is None
            or not request.use_horizontal_ink_reservation
            or not has_visible_stamp_image
            or request.image_stamp_path is None
            or request.layout_template != SignatureLayoutTemplate.SINGLE_LINE
            or request.stamp_position
            not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
        ):
            return None

        measurement = self.ink_measurer.measure(
            HorizontalInkMeasurementRequest(
                signature_rect=request.signature_rect,
                layout_template=request.layout_template,
                stamp_position=request.stamp_position,
                text_style=request.text_style,
                box_style=request.box_style,
                stamp_text=request.stamp_text,
                image_stamp_path=request.image_stamp_path,
                structural_text_box_width_pt=text_box.width_pt,
                structural_text_box_height_pt=text_box.height_pt,
            )
        )
        if measurement is None:
            return None

        return build_horizontal_single_line_ink_reservation(
            layout_template=request.layout_template,
            stamp_position=request.stamp_position,
            has_visible_stamp_image=has_visible_stamp_image,
            structural_text_box_width_pt=text_box.width_pt,
            structural_text_box_height_pt=text_box.height_pt,
            structural_text_bounds_px=measurement.structural_text_bounds_px.as_dict(),
            rendered_ink_bounds_px=measurement.rendered_ink_bounds_px.as_dict(),
            px_to_pt=measurement.px_to_pt,
            border_facing_padding_pt=edge_margin,
            stamp_facing_padding_pt=edge_margin,
        )

    @staticmethod
    def _fit_issues(
        reservation: object,
        *,
        has_visible_stamp_image: bool,
        fit_checker: object,
    ) -> tuple[VisibleSignatureFitIssue, ...]:
        try:
            fit_checker(reservation, has_visible_stamp_image=has_visible_stamp_image)
        except Exception as exc:
            return (
                VisibleSignatureFitIssue(
                    code="visible_signature_layout_unavailable",
                    message=str(exc),
                ),
            )
        return ()


def _reservation_snapshot(layout_plan: SignatureLayoutPlan) -> dict[str, object]:
    """Return JSON-ready neutral evidence for a resolved layout plan."""

    return {
        "container_width_pt": layout_plan.container_width_pt,
        "container_height_pt": layout_plan.container_height_pt,
        "text_box": {
            "width_pt": layout_plan.text_box.width_pt,
            "height_pt": layout_plan.text_box.height_pt,
            "line_count": layout_plan.text_box.line_count,
        },
        "text_area_width_pt": layout_plan.text_area_width_pt,
        "text_area_height_pt": layout_plan.text_area_height_pt,
        "stamp_area_width_pt": layout_plan.stamp_area_width_pt,
        "stamp_area_height_pt": layout_plan.stamp_area_height_pt,
        "reserved_primary_extent_pt": layout_plan.reserved_primary_extent_pt,
        "has_visible_stamp_image": layout_plan.has_visible_stamp_image,
        "fit_issue_codes": [issue.code for issue in layout_plan.fit_issues],
    }


def _layout_plan_fingerprint(layout_plan: SignatureLayoutPlan) -> tuple[object, ...]:
    """Return a stable value fingerprint for prepared-plan identity checks."""

    return (
        layout_plan.container_width_pt,
        layout_plan.container_height_pt,
        layout_plan.text_box,
        layout_plan.text_area_width_pt,
        layout_plan.text_area_height_pt,
        layout_plan.stamp_area_width_pt,
        layout_plan.stamp_area_height_pt,
        layout_plan.reserved_primary_extent_pt,
        layout_plan.text_layout,
        layout_plan.stamp_layout,
        layout_plan.fit_issues,
    )


def _horizontal_single_line_ink_validation_reservation(
    structural_reservation: _SignatureLayoutReservation,
    *,
    ink_reservation: HorizontalSingleLineInkReservation | None,
    signature_rect: SignatureRect,
    box_style: SignatureBoxStyle | None,
    has_visible_stamp_image: bool,
    stamp_aspect_ratio: float | None,
) -> _SignatureLayoutReservation:
    """Return an ink-informed reservation for validation without changing placement."""

    if (
        ink_reservation is None
        or not has_visible_stamp_image
        or structural_reservation.layout_template != SignatureLayoutTemplate.SINGLE_LINE
        or structural_reservation.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return structural_reservation
    if ink_reservation.lane_width_pt >= structural_reservation.text_area_width_pt:
        return structural_reservation

    return _layout_reservation_for_template(
        structural_reservation.layout_template,
        stamp_position=structural_reservation.stamp_position,
        signature_rect=signature_rect,
        text_box_width=ink_reservation.lane_width_pt,
        text_box_height=structural_reservation.text_box_height_pt,
        box_style=box_style,
        has_visible_stamp_image=has_visible_stamp_image,
        stamp_aspect_ratio=stamp_aspect_ratio,
    )


def _apply_horizontal_single_line_ink_text_alignment(
    reservation: _SignatureLayoutReservation,
    *,
    ink_reservation: HorizontalSingleLineInkReservation | None,
) -> _SignatureLayoutReservation:
    """Optically align horizontal single-line text ink without changing fit policy."""

    if (
        ink_reservation is None
        or reservation.layout_template != SignatureLayoutTemplate.SINGLE_LINE
        or reservation.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return reservation

    layout_rule = reservation.inner_content_layout
    margins = layout_rule.margins
    if reservation.stamp_position == SignatureStampPosition.LEFT:
        if ink_reservation.ink_right_slack_pt <= 0:
            return reservation
        adjusted_margins = _layout_margins(
            left=margins.left,
            right=margins.right - ink_reservation.ink_right_slack_pt,
            top=margins.top,
            bottom=margins.bottom,
        )
    else:
        if ink_reservation.ink_left_offset_pt <= 0:
            return reservation
        adjusted_margins = _layout_margins(
            left=margins.left - ink_reservation.ink_left_offset_pt,
            right=margins.right,
            top=margins.top,
            bottom=margins.bottom,
        )
    return replace(
        reservation,
        inner_content_layout=_layout_rule(
            x_align=layout_rule.x_align,
            y_align=layout_rule.y_align,
            margins=adjusted_margins,
            scaling=layout_rule.scaling,
        ),
    )


def _horizontal_single_line_background_text_width(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    box_height: int,
    fallback_text_box_width: int,
    ink_reservation: HorizontalSingleLineInkReservation | None,
) -> int:
    """Return the text width reserved when sizing a single-line stamp image."""

    if (
        ink_reservation is None
        or layout_template != SignatureLayoutTemplate.SINGLE_LINE
        or stamp_position not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return fallback_text_box_width

    _edge_margin, separator_width = _base_layout_spacing(
        stamp_position=stamp_position,
        box_height=box_height,
    )
    return max(
        1,
        ink_reservation.ink_width_pt + ink_reservation.stamp_facing_padding_pt - separator_width,
    )


def _ensure_layout_can_fit(
    layout_reservation: _SignatureLayoutReservation,
    *,
    has_visible_stamp_image: bool = False,
) -> None:
    """Validate fit after reservation with only a tiny numeric seam correction."""

    max_text_width = layout_reservation.text_area_width_pt + 1
    if (
        has_visible_stamp_image
        and (
            layout_reservation.layout_template != SignatureLayoutTemplate.SINGLE_LINE
            or layout_reservation.stamp_position
            in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
        )
        and (
            layout_reservation.stamp_area_width_pt <= 0
            or layout_reservation.stamp_area_height_pt <= 0
        )
    ):
        raise ValueError(
            "Visible signature content does not fit inside the selected rectangle for the "
            f"{layout_reservation.layout_template.value} template. "
            "Enlarge the signature box or choose a more compact appearance."
        )
    if (
        layout_reservation.text_box_width_pt > max_text_width
        or layout_reservation.text_box_height_pt > layout_reservation.text_area_height_pt
    ):
        raise ValueError(
            "Visible signature content does not fit inside the selected rectangle for the "
            f"{layout_reservation.layout_template.value} template. "
            "Enlarge the signature box or choose a more compact appearance."
        )


@dataclass(frozen=True)
class _LayoutAppearance:
    """Minimal neutral appearance view needed by layout policy."""

    layout_template: SignatureLayoutTemplate
    stamp_position: SignatureStampPosition
    datetime_format: str
    text_style: SignatureTextStyle
    box_style: SignatureBoxStyle
    image_stamp_path: str | None


@dataclass
class VisibleSignatureLayoutService:
    """Facade for neutral visible-signature layout policy."""

    text_measurer: TextMeasurer | None = None
    image_probe: StampImageProbe | None = None
    ink_measurer: HorizontalInkMeasurer | None = None
    appearance_materializer: SignatureAppearanceMaterializer | None = None

    @classmethod
    def production(cls) -> VisibleSignatureLayoutService:
        """Return the production layout service with default local adapters."""

        return cls()

    def prepare(self, request: VisibleSignatureLayoutRequest) -> VisibleSignaturePreparation:
        """Prepare one neutral plan for all target-specific layout materializers."""

        layout_plan = self._plan_for_request(request)
        preview_plan = layout_plan
        preview_stamp_suppressed = False
        if (
            request.options.include_stamp
            and request.appearance.layout_template == SignatureLayoutTemplate.SINGLE_LINE
            and request.appearance.stamp_position
            in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
            and layout_plan.text_area_width_pt * 2 < layout_plan.text_box.width_pt
        ):
            preview_stamp_suppressed = True
            preview_plan = self._plan_for_request(
                request,
                include_stamp=False,
                use_horizontal_ink_reservation=False,
            )
        return VisibleSignaturePreparation(
            layout_plan=layout_plan,
            reservation_snapshot=_reservation_snapshot(layout_plan),
            fit_issues=layout_plan.fit_issues,
            plan_fingerprint=_layout_plan_fingerprint(layout_plan),
            _service=self,
            _request=request,
            _preview_plan=preview_plan,
            _preview_stamp_suppressed=preview_stamp_suppressed,
            _appearance_materializer=self.appearance_materializer,
        )

    def plan(self, request: VisibleSignatureLayoutInput) -> SignatureLayoutPlan:
        """Return the canonical visible-signature layout plan."""

        appearance = _LayoutAppearance(
            layout_template=request.layout_template,
            stamp_position=request.stamp_position,
            datetime_format="%Y-%m-%d %H:%M",
            text_style=request.text_style,
            box_style=request.box_style,
            image_stamp_path=request.image_stamp_path,
        )
        return self._plan_for_appearance(
            appearance=appearance,
            stamp_text=request.stamp_text,
            signature_rect=request.signature_rect,
            include_stamp=request.image_stamp_path is not None,
            use_horizontal_ink_reservation=request.use_horizontal_ink_reservation,
            ink_measurer=self.ink_measurer,
        )

    def _plan_for_appearance(
        self,
        *,
        appearance: VisibleSignatureAppearancePort,
        stamp_text: str,
        signature_rect: SignatureRect,
        include_stamp: bool,
        use_horizontal_ink_reservation: bool,
        ink_measurer: HorizontalInkMeasurer | None,
    ) -> SignatureLayoutPlan:
        return VisibleSignatureLayoutEngine(
            text_measurer=self.text_measurer,
            image_probe=self.image_probe,
            ink_measurer=ink_measurer or self.ink_measurer,
        ).plan(
            LayoutRequest(
                signature_rect=signature_rect,
                layout_template=appearance.layout_template,
                stamp_position=appearance.stamp_position,
                text_style=appearance.text_style,
                box_style=appearance.box_style,
                stamp_text=stamp_text,
                image_stamp_path=appearance.image_stamp_path if include_stamp else None,
                use_horizontal_ink_reservation=use_horizontal_ink_reservation,
            )
        )

    def _plan_for_request(
        self,
        request: VisibleSignatureLayoutRequest,
        *,
        include_stamp: bool | None = None,
        use_horizontal_ink_reservation: bool | None = None,
    ) -> SignatureLayoutPlan:
        options = request.options
        return self._plan_for_appearance(
            appearance=request.appearance,
            stamp_text=request.stamp_text if options.include_text else " ",
            signature_rect=request.signature_rect,
            include_stamp=options.include_stamp if include_stamp is None else include_stamp,
            use_horizontal_ink_reservation=(
                options.horizontal_ink_policy != "disabled"
                if use_horizontal_ink_reservation is None
                else use_horizontal_ink_reservation
            ),
            ink_measurer=request.ink_measurer or self.ink_measurer,
        )


def _background_layout_spec_for_stamp(
    layout_template: SignatureLayoutTemplate,
    *,
    stamp_position: SignatureStampPosition,
    stamp_background: object | None,
    signature_rect: SignatureRect,
    text_box_width: int,
    text_box_height: int,
    box_style: SignatureBoxStyle | None = None,
    stamp_aspect_ratio: float | None = None,
) -> LayoutRuleSpec:
    if stamp_aspect_ratio is None:
        image = getattr(stamp_background, "image", None)
        size = getattr(image, "size", None)
        if size is not None and size[0] > 0 and size[1] > 0:
            stamp_aspect_ratio = size[0] / size[1]
    reservation = _layout_reservation_for_template(
        layout_template,
        stamp_position=stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=box_style,
        has_visible_stamp_image=stamp_background is not None,
        stamp_aspect_ratio=stamp_aspect_ratio,
    )
    if stamp_background is None:
        return reservation.background_layout

    background_layout = replace(reservation.background_layout, scaling="SHRINK_TO_FIT")
    if stamp_aspect_ratio is None or stamp_aspect_ratio <= 0:
        return background_layout

    area_width = max(1, reservation.stamp_area_width_pt)
    area_height = max(1, reservation.stamp_area_height_pt)
    content_inset = 0
    if layout_template == SignatureLayoutTemplate.SINGLE_LINE:
        content_inset = _single_line_stamp_content_inset(
            stamp_position=stamp_position,
            box_width=max(1, int(round(signature_rect.width_pt))),
            box_height=max(1, int(round(signature_rect.height_pt))),
            reserved_width=area_width,
            reserved_height=area_height,
        )
    horizontal_single_line_vertical_inset = content_inset
    if layout_template == SignatureLayoutTemplate.SINGLE_LINE and stamp_position in {
        SignatureStampPosition.LEFT,
        SignatureStampPosition.RIGHT,
    }:
        horizontal_single_line_vertical_inset = _single_line_horizontal_stamp_vertical_inset(
            box_style=box_style,
            content_inset=content_inset,
        )
    fit_width = max(1, area_width - content_inset * 2)
    fit_height = max(1, area_height - horizontal_single_line_vertical_inset * 2)
    border_gap = _border_facing_stamp_inset(
        layout_template=layout_template,
        stamp_position=stamp_position,
        box_style=box_style,
    )
    if layout_template == SignatureLayoutTemplate.SINGLE_LINE and stamp_position in {
        SignatureStampPosition.TOP,
        SignatureStampPosition.BOTTOM,
    }:
        border_gap = _single_line_vertical_stamp_border_gap(box_style=box_style)
        fit_height = max(1, fit_height - border_gap)
    elif stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}:
        border_gap = _top_stamp_border_facing_inset(box_style=box_style)
        fit_height = max(1, fit_height - border_gap)
    elif stamp_position == SignatureStampPosition.RIGHT:
        fit_width = max(1, fit_width - border_gap)
    target_width = fit_width
    target_height = max(1, int(round(target_width / stamp_aspect_ratio)))
    if target_height > fit_height:
        target_height = fit_height
        target_width = max(1, int(round(target_height * stamp_aspect_ratio)))

    if layout_template == SignatureLayoutTemplate.SINGLE_LINE and stamp_position in {
        SignatureStampPosition.TOP,
        SignatureStampPosition.BOTTOM,
    }:
        remaining_y = max(0, area_height - target_height)
        centered_extra_y = max(0, remaining_y - border_gap) // 2
        extra_x_left = 0
        extra_x_right = max(0, area_width - target_width)
        if stamp_position == SignatureStampPosition.TOP:
            extra_y_top = min(border_gap, remaining_y) + centered_extra_y
            extra_y_bottom = centered_extra_y
        else:
            extra_y_top = centered_extra_y
            extra_y_bottom = min(border_gap, remaining_y) + centered_extra_y
    elif (
        stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}
        and border_gap > 0
    ):
        remaining_y = max(0, area_height - target_height)
        centered_extra_y = max(0, remaining_y - border_gap) // 2
        centered_extra_x = max(0, area_width - target_width) // 2
        extra_x_left = centered_extra_x
        extra_x_right = centered_extra_x
        if stamp_position == SignatureStampPosition.TOP:
            extra_y_top = min(border_gap, remaining_y) + centered_extra_y
            extra_y_bottom = centered_extra_y
        else:
            extra_y_top = centered_extra_y
            extra_y_bottom = min(border_gap, remaining_y) + centered_extra_y
    elif stamp_position == SignatureStampPosition.RIGHT and border_gap > 0:
        remaining_x = max(0, area_width - target_width)
        centered_extra_x = max(0, remaining_x - border_gap) // 2
        extra_x_left = centered_extra_x
        extra_x_right = min(border_gap, remaining_x) + centered_extra_x
        extra_y_top = max(0, area_height - target_height) // 2
        extra_y_bottom = extra_y_top
    elif stamp_position == SignatureStampPosition.LEFT and border_gap > 0:
        max_content_width = max(1, fit_width - border_gap)
        if target_width > max_content_width:
            target_width = max_content_width
            target_height = max(1, int(round(target_width / stamp_aspect_ratio)))
        remaining_x = max(0, area_width - target_width)
        centered_extra_x = max(0, remaining_x - border_gap) // 2
        extra_x_left = min(border_gap, remaining_x) + centered_extra_x
        extra_x_right = centered_extra_x
        extra_y_top = max(0, area_height - target_height) // 2
        extra_y_bottom = extra_y_top
    elif (
        layout_template == SignatureLayoutTemplate.SINGLE_LINE
        and stamp_position == SignatureStampPosition.LEFT
    ):
        extra_x_left = max(0, area_width - target_width)
        extra_x_right = 0
        extra_y_top = max(0, area_height - target_height) // 2
        extra_y_bottom = extra_y_top
    else:
        centered_extra_x = max(0, area_width - target_width) // 2
        extra_x_left = centered_extra_x
        extra_x_right = centered_extra_x
        extra_y_top = max(0, area_height - target_height) // 2
        extra_y_bottom = extra_y_top
    margins = background_layout.margins
    return replace(
        background_layout,
        margins=LayoutMargins(
            left=margins.left + extra_x_left,
            right=margins.right + extra_x_right,
            top=margins.top + extra_y_top,
            bottom=margins.bottom + extra_y_bottom,
        ),
    )


def _border_safe_inset(box_style: SignatureBoxStyle | None) -> int:
    if box_style is None or not box_style.show_border:
        return 0
    return max(0, int(ceil(box_style.border_width_pt / 2.0)) + 1)


def _single_line_stamp_content_inset(
    *,
    stamp_position: SignatureStampPosition,
    box_width: int,
    box_height: int,
    reserved_width: int | None = None,
    reserved_height: int | None = None,
) -> int:
    effective_width = (
        reserved_width if isinstance(reserved_width, int) and reserved_width > 0 else box_width
    )
    effective_height = (
        reserved_height if isinstance(reserved_height, int) and reserved_height > 0 else box_height
    )
    shortest_edge = max(1, min(effective_width, effective_height))
    if stamp_position in {
        SignatureStampPosition.TOP,
        SignatureStampPosition.BOTTOM,
    }:
        return max(0, min(2, int(shortest_edge * 0.08)))
    if stamp_position in {
        SignatureStampPosition.LEFT,
        SignatureStampPosition.RIGHT,
    }:
        return max(0, min(1, int(round(shortest_edge * 0.03))))
    return 0


def _single_line_vertical_stamp_border_gap(
    *,
    box_style: SignatureBoxStyle | None,
) -> int:
    if box_style is None or not box_style.show_border:
        return 0
    return max(1, min(2, int(round(max(box_style.border_width_pt, 1.0) / 2.0))))


def _single_line_horizontal_stamp_vertical_inset(
    *,
    box_style: SignatureBoxStyle | None,
    content_inset: int,
) -> int:
    return max(content_inset, _border_safe_inset(box_style))


def single_line_stamp_content_inset(
    *,
    stamp_position: SignatureStampPosition,
    box_width: int,
    box_height: int,
    reserved_width: int | None = None,
    reserved_height: int | None = None,
) -> int:
    """Return the public content inset used by Qt and backend adapters."""

    return _single_line_stamp_content_inset(
        stamp_position=stamp_position,
        box_width=box_width,
        box_height=box_height,
        reserved_width=reserved_width,
        reserved_height=reserved_height,
    )


def single_line_vertical_stamp_border_gap(*, box_style: SignatureBoxStyle | None) -> int:
    """Return the public border gap used by Qt and backend adapters."""

    return _single_line_vertical_stamp_border_gap(box_style=box_style)


def single_line_horizontal_stamp_vertical_inset(
    *,
    box_style: SignatureBoxStyle | None,
    content_inset: int,
) -> int:
    """Return the public horizontal-stamp vertical inset."""

    return _single_line_horizontal_stamp_vertical_inset(
        box_style=box_style,
        content_inset=content_inset,
    )


def _top_stamp_border_facing_inset(
    *,
    box_style: SignatureBoxStyle | None,
) -> int:
    if box_style is None or not box_style.show_border:
        return 1
    return max(1, min(2, int(round(max(box_style.border_width_pt, 1.0) / 2.0))))


def _border_facing_stamp_inset(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    box_style: SignatureBoxStyle | None,
) -> int:
    if layout_template == SignatureLayoutTemplate.SINGLE_LINE:
        return 0
    if stamp_position in {
        SignatureStampPosition.LEFT,
        SignatureStampPosition.TOP,
        SignatureStampPosition.BOTTOM,
        SignatureStampPosition.RIGHT,
    }:
        return _top_stamp_border_facing_inset(box_style=box_style)
    return 0


def _public_ink_reservation(reservation: object | None) -> HorizontalInkReservation | None:
    if reservation is None:
        return None
    return HorizontalInkReservation(
        lane_width_pt=reservation.lane_width_pt,
        ink_width_pt=reservation.ink_width_pt,
        ink_height_pt=reservation.ink_height_pt,
        ink_left_offset_pt=reservation.ink_left_offset_pt,
        ink_right_slack_pt=reservation.ink_right_slack_pt,
        border_facing_padding_pt=reservation.border_facing_padding_pt,
        stamp_facing_padding_pt=reservation.stamp_facing_padding_pt,
    )


def _single_line_text_only_ink_bounds(
    *,
    preview: object,
    output_path: Path,
) -> dict[str, int] | None:
    from foliaseal.application.signing_preview_renderer import (
        _canonical_preview_layout,
        _render_optional_preview_bounds,
    )

    layout = _canonical_preview_layout(
        preview,
        include_text=True,
        include_stamp=True,
        include_border=True,
    )
    return _render_optional_preview_bounds(
        preview=preview,
        layout=layout,
        zoom=1.0,
        output_path=output_path,
        include_text=True,
        include_stamp=False,
        render_backend=None,
        flatten_to_white=True,
    )


def _single_line_rendered_ink_fits_reservation(
    *,
    signature_rect: SignatureRect,
    signature_appearance: object,
    stamp_text: str,
) -> bool:
    if signature_appearance.layout_template != SignatureLayoutTemplate.SINGLE_LINE:
        return False
    cache_key = _single_line_rendered_ink_fit_cache_key(
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
        stamp_text=stamp_text,
    )
    cached = _SINGLE_LINE_RENDERED_INK_FIT_CACHE.get(cache_key)
    if cached is not None:
        return cached
    snapshot = None
    reference_snapshot = None
    try:
        from foliaseal.application.phase3_signing_backend import (
            _signing_draft_preview_for_stamp_text,
        )
        from foliaseal.application.signing_preview_renderer import (
            render_canonical_signature_preview,
        )

        preview = _signing_draft_preview_for_stamp_text(
            signature_rect=signature_rect,
            signature_appearance=signature_appearance,
            stamp_text=stamp_text,
        )
        snapshot = render_canonical_signature_preview(
            preview,
            zoom=1.0,
            include_border=True,
            flatten_to_white=True,
        )
        if snapshot is None or snapshot.text_area_bounds_px is None:
            return False
        if (
            signature_appearance.image_stamp_path is not None
            and signature_appearance.stamp_position
            in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
            and (snapshot.stamp_area_bounds_px is None or snapshot.stamp_bounds_px is None)
        ):
            return False
        nominal_width_overflow = (
            (snapshot.text_bounds_px["width"] - snapshot.text_area_bounds_px["width"])
            if snapshot.text_bounds_px is not None
            else 0
        )
        if nominal_width_overflow > 16:
            return False
        text_bounds = _single_line_text_only_ink_bounds(
            preview=preview,
            output_path=Path(snapshot.image_path).parent / "fit-text-only.png",
        )
        if text_bounds is None:
            return False
        if not _horizontal_single_line_text_ink_inside_border(
            text_bounds=text_bounds,
            preview_width_px=snapshot.width_px,
            preview_height_px=snapshot.height_px,
            signature_appearance=signature_appearance,
        ):
            return False
        enforce_reference_ink_preservation = (
            signature_appearance.image_stamp_path is not None
            and signature_appearance.stamp_position
            in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
        )
        if enforce_reference_ink_preservation:
            reference_rect = replace(
                signature_rect,
                width_pt=max(
                    signature_rect.width_pt,
                    signature_rect.width_pt
                    + float((snapshot.text_bounds_px or {}).get("width", 0))
                    + 64.0,
                ),
                height_pt=max(
                    signature_rect.height_pt,
                    float((snapshot.text_bounds_px or {}).get("height", 0)) + 64.0,
                ),
            )
            reference_preview = _signing_draft_preview_for_stamp_text(
                signature_rect=reference_rect,
                signature_appearance=signature_appearance,
                stamp_text=stamp_text,
            )
            reference_snapshot = render_canonical_signature_preview(
                reference_preview,
                zoom=1.0,
                include_border=True,
                flatten_to_white=True,
            )
            if reference_snapshot is None or reference_snapshot.text_area_bounds_px is None:
                return False
            reference_text_bounds = _single_line_text_only_ink_bounds(
                preview=reference_preview,
                output_path=Path(reference_snapshot.image_path).parent
                / "fit-reference-text-only.png",
            )
            if reference_text_bounds is None:
                return False
            reference_width_loss = max(
                0,
                reference_text_bounds["width"] - text_bounds["width"],
            )
            reference_height_loss = max(
                0,
                reference_text_bounds["height"] - text_bounds["height"],
            )
            if reference_width_loss > 3 or reference_height_loss > 3:
                return False
        result = (
            text_bounds["width"] <= snapshot.text_area_bounds_px["width"]
            and text_bounds["height"] <= snapshot.text_area_bounds_px["height"] + 1
        )
        if len(_SINGLE_LINE_RENDERED_INK_FIT_CACHE) >= 256:
            _SINGLE_LINE_RENDERED_INK_FIT_CACHE.clear()
        _SINGLE_LINE_RENDERED_INK_FIT_CACHE[cache_key] = result
        return result
    except Exception:
        return False
    finally:
        if snapshot is not None:
            _cleanup_canonical_preview_snapshot(snapshot)
        if reference_snapshot is not None:
            _cleanup_canonical_preview_snapshot(reference_snapshot)


def _horizontal_multi_line_rendered_layout_fits_reservation(
    *,
    signature_rect: SignatureRect,
    signature_appearance: object,
    stamp_text: str,
    layout_plan: SignatureLayoutPlan,
) -> bool:
    if (
        signature_appearance.layout_template != SignatureLayoutTemplate.MULTI_LINE
        or signature_appearance.image_stamp_path is None
        or signature_appearance.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return False

    width_overflow = layout_plan.text_box.width_pt - (layout_plan.text_area_width_pt + 1)
    height_overflow = layout_plan.text_box.height_pt - layout_plan.text_area_height_pt
    if width_overflow > 0 or height_overflow <= 0 or height_overflow > 6:
        return False

    snapshot = None
    try:
        from foliaseal.application.phase3_signing_backend import (
            _signing_draft_preview_for_stamp_text,
        )
        from foliaseal.application.phase3_signing_backend import (
            detect_text_content_bounds_in_image as _detect_text_content_bounds_in_image,
        )
        from foliaseal.application.signing_preview_renderer import (
            render_canonical_signature_preview,
        )

        preview = _signing_draft_preview_for_stamp_text(
            signature_rect=signature_rect,
            signature_appearance=signature_appearance,
            stamp_text=stamp_text,
        )
        snapshot = render_canonical_signature_preview(
            preview,
            zoom=1.0,
            include_border=True,
            flatten_to_white=True,
        )
        if snapshot.text_area_bounds_px is None:
            return False
        rendered_text_bounds, _error = _detect_text_content_bounds_in_image(
            preview_image_path=snapshot.image_path,
            text_widget_bounds=snapshot.text_area_bounds_px,
            text_color_rgba=_text_style_color_rgba(signature_appearance.text_style),
            reference_text_content_bounds=snapshot.text_bounds_px,
        )
        text_bounds = rendered_text_bounds
        stamp_bounds = getattr(snapshot, "stamp_bounds_px", None)
        if text_bounds is None or stamp_bounds is None:
            return False
        if stamp_bounds["width"] <= 0 or stamp_bounds["height"] <= 0:
            return False
        container = {"x": 0, "y": 0, "width": snapshot.width_px, "height": snapshot.height_px}
        return (
            _rect_inside_container(text_bounds, container)
            and _rect_inside_container(stamp_bounds, container)
            and not _rectangles_overlap(text_bounds, stamp_bounds)
        )
    except Exception:
        return False
    finally:
        if snapshot is not None:
            _cleanup_canonical_preview_snapshot(snapshot)


def _rect_inside_container(
    rect: dict[str, int],
    container: dict[str, int],
) -> bool:
    return (
        rect["x"] >= container["x"]
        and rect["y"] >= container["y"]
        and rect["x"] + rect["width"] <= container["x"] + container["width"]
        and rect["y"] + rect["height"] <= container["y"] + container["height"]
    )


def _rectangles_overlap(first: dict[str, int], second: dict[str, int]) -> bool:
    return (
        first["x"] < second["x"] + second["width"]
        and second["x"] < first["x"] + first["width"]
        and first["y"] < second["y"] + second["height"]
        and second["y"] < first["y"] + first["height"]
    )


def _horizontal_single_line_text_ink_inside_border(
    *,
    text_bounds: dict[str, int],
    preview_width_px: int,
    preview_height_px: int,
    signature_appearance: object,
) -> bool:
    if (
        signature_appearance.layout_template != SignatureLayoutTemplate.SINGLE_LINE
        or signature_appearance.image_stamp_path is None
        or signature_appearance.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return True
    guard_px = _border_safe_inset(signature_appearance.box_style)
    if guard_px <= 0:
        return True
    container = {
        "x": guard_px,
        "y": guard_px,
        "width": max(0, preview_width_px - guard_px * 2),
        "height": max(0, preview_height_px - guard_px * 2),
    }
    return _rect_inside_container(text_bounds, container)


def _single_line_rendered_ink_fit_cache_key(
    *,
    signature_rect: SignatureRect,
    signature_appearance: object,
    stamp_text: str,
) -> tuple[object, ...]:
    box_style = signature_appearance.box_style
    text_style = signature_appearance.text_style
    image_identity: tuple[object, ...] = (signature_appearance.image_stamp_path,)
    if signature_appearance.image_stamp_path:
        try:
            image_stat = Path(signature_appearance.image_stamp_path).stat()
        except OSError:
            image_stat = None
        if image_stat is not None:
            image_identity = (
                signature_appearance.image_stamp_path,
                image_stat.st_size,
                image_stat.st_mtime_ns,
            )
    return (
        signature_rect.page_index,
        round(signature_rect.left_pt, 3),
        round(signature_rect.bottom_pt, 3),
        round(signature_rect.width_pt, 3),
        round(signature_rect.height_pt, 3),
        stamp_text,
        signature_appearance.layout_template,
        signature_appearance.stamp_position,
        image_identity,
        signature_appearance.signer_label_prefix,
        signature_appearance.datetime_format,
        signature_appearance.show_field_names,
        text_style.font_family,
        round(text_style.font_size_pt, 3),
        text_style.bold,
        text_style.italic,
        text_style.text_color_hex,
        box_style.show_border,
        box_style.border_color_hex,
        round(box_style.border_width_pt, 3),
        box_style.background_color_hex,
    )


def _text_style_color_rgba(text_style: SignatureTextStyle) -> tuple[int, int, int, int] | None:
    return text_style_color_rgba(text_style)


def _cleanup_canonical_preview_snapshot(snapshot: object) -> None:
    image_path = getattr(snapshot, "image_path", None)
    if not isinstance(image_path, str):
        return
    temp_dir = Path(image_path).parent
    if temp_dir.name.startswith("foliaseal-canonical-preview-"):
        shutil.rmtree(temp_dir, ignore_errors=True)
