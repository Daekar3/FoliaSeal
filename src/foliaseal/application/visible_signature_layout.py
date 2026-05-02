"""Visible-signature layout planning boundary.

This module is the public application-layer seam for visible-signature geometry.
The first implementation preserves current behavior by delegating to the
existing backend layout helpers; later slices can move the policy here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from PIL import Image

from foliaseal.application.horizontal_signature_reservation import (
    build_horizontal_single_line_ink_reservation,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signing_draft_workflow import SigningDraftValidationSeverity
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
)


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
    backend_reservation: object
    stamp_image: ImageMetrics | None


@dataclass(frozen=True)
class PyHankoVisibleSignatureStyle:
    """pyHanko style bundle built from the visible-signature layout service."""

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


class PyHankoTextMeasurer:
    """Production text measurer backed by the current pyHanko text engine."""

    def measure(self, text: str, text_style: SignatureTextStyle) -> TextMetrics:
        from foliaseal.application.phase3_signing_backend import (
            _build_text_box_style,
            _measure_text_box_dimensions,
        )

        text_box_style = _build_text_box_style(text_style)
        width_pt, height_pt = _measure_text_box_dimensions(text, text_box_style)
        return TextMetrics(
            width_pt=width_pt,
            height_pt=height_pt,
            line_count=max(1, len(text.splitlines()) or 1),
        )


class PillowStampImageProbe:
    """Production stamp image probe backed by Pillow."""

    def inspect(self, image_stamp_path: str | None) -> ImageMetrics | None:
        if image_stamp_path is None:
            return None
        try:
            with Image.open(image_stamp_path) as image:
                width_px, height_px = image.size
        except FileNotFoundError as exc:
            raise ValueError(f"Image stamp path not found: {image_stamp_path}") from exc
        except OSError as exc:
            raise ValueError(
                f"Image stamp path is not a readable image: {image_stamp_path}"
            ) from exc
        if width_px <= 0 or height_px <= 0:
            return None
        return ImageMetrics(
            width_px=width_px,
            height_px=height_px,
            aspect_ratio=width_px / height_px,
        )


@dataclass
class VisibleSignatureLayoutEngine:
    """Plan visible-signature layout through one application boundary."""

    text_measurer: TextMeasurer | None = None
    image_probe: StampImageProbe | None = None
    ink_measurer: HorizontalInkMeasurer | None = None

    def plan(self, request: LayoutRequest) -> SignatureLayoutPlan:
        """Return the visible-signature layout plan for one request."""

        text_measurer = self.text_measurer or PyHankoTextMeasurer()
        image_probe = self.image_probe or PillowStampImageProbe()
        text_box = text_measurer.measure(request.stamp_text, request.text_style)
        stamp_image = image_probe.inspect(request.image_stamp_path)
        has_visible_stamp_image = stamp_image is not None

        from foliaseal.application.phase3_signing_backend import (
            _apply_horizontal_single_line_ink_text_alignment,
            _effective_layout_edge_margin,
            _ensure_layout_can_fit,
            _horizontal_single_line_background_text_width,
            _horizontal_single_line_ink_validation_reservation,
            _layout_reservation_for_template,
        )

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
            text_layout=_layout_rule_spec(placement_reservation.inner_content_layout),
            stamp_layout=_layout_rule_spec(placement_reservation.background_layout),
            background_text_box_width_pt=background_text_box_width,
            ink_reservation=_public_ink_reservation(ink_reservation),
            fit_issues=fit_issues,
            backend_reservation=placement_reservation,
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


@dataclass
class VisibleSignatureLayoutService:
    """Facade for visible-signature layout policy and pyHanko adapters."""

    text_measurer: TextMeasurer | None = None
    image_probe: StampImageProbe | None = None
    ink_measurer: HorizontalInkMeasurer | None = None

    @classmethod
    def production(cls) -> VisibleSignatureLayoutService:
        """Return the production layout service with default local adapters."""

        return cls()

    def plan(self, request: VisibleSignatureLayoutInput) -> SignatureLayoutPlan:
        """Return the canonical visible-signature layout plan."""

        return VisibleSignatureLayoutEngine(
            text_measurer=self.text_measurer,
            image_probe=self.image_probe,
            ink_measurer=self.ink_measurer,
        ).plan(
            LayoutRequest(
                signature_rect=request.signature_rect,
                layout_template=request.layout_template,
                stamp_position=request.stamp_position,
                text_style=request.text_style,
                box_style=request.box_style,
                stamp_text=request.stamp_text,
                image_stamp_path=request.image_stamp_path,
                use_horizontal_ink_reservation=request.use_horizontal_ink_reservation,
            )
        )

    def pyhanko_style_for_signing(
        self,
        *,
        appearance: SigningBackendAppearance,
        stamp_text: str,
        stamp_background: object | None,
        signature_rect: SignatureRect,
        options: VisibleSignatureLayoutOptions | None = None,
        ink_measurer: HorizontalInkMeasurer | None = None,
    ) -> PyHankoVisibleSignatureStyle:
        """Build a pyHanko signing style through the layout service boundary."""

        options = options or VisibleSignatureLayoutOptions()
        effective_stamp_text = stamp_text if options.include_text else " "
        layout_plan = VisibleSignatureLayoutEngine(
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
                stamp_text=effective_stamp_text,
                image_stamp_path=appearance.image_stamp_path if options.include_stamp else None,
                use_horizontal_ink_reservation=options.horizontal_ink_policy != "disabled",
            )
        )
        stamp_style = PyHankoSignatureAppearanceAdapter().build_stamp_style(
            appearance=appearance,
            stamp_text=effective_stamp_text,
            stamp_background=stamp_background if options.include_background else None,
            signature_rect=signature_rect,
            layout_plan=layout_plan,
            allow_fit_issues=options.allow_fit_issues,
            include_border=options.include_border,
            include_background=options.include_background,
        )
        return PyHankoVisibleSignatureStyle(
            stamp_style=stamp_style,
            content_layout=stamp_style.inner_content_layout,
            background_layout=stamp_style.background_layout,
            layout_plan=layout_plan,
            fit_issues=layout_plan.fit_issues,
        )

    def pyhanko_style_for_canonical_preview(
        self,
        *,
        appearance: SigningBackendAppearance,
        stamp_text: str,
        stamp_background: object | None,
        signature_rect: SignatureRect,
        options: VisibleSignatureLayoutOptions | None = None,
        ink_measurer: HorizontalInkMeasurer | None = None,
    ) -> CanonicalPreviewLayout:
        """Build a canonical preview style through the layout service boundary."""

        options = options or VisibleSignatureLayoutOptions(allow_fit_issues=True)
        layout_plan = self._plan_for_appearance(
            appearance=appearance,
            stamp_text=stamp_text if options.include_text else " ",
            signature_rect=signature_rect,
            include_stamp=options.include_stamp,
            use_horizontal_ink_reservation=options.horizontal_ink_policy != "disabled",
            ink_measurer=ink_measurer,
        )
        stamp_suppressed = False
        if (
            options.include_stamp
            and appearance.layout_template == SignatureLayoutTemplate.SINGLE_LINE
            and appearance.stamp_position
            in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
            and layout_plan.text_area_width_pt * 2 < layout_plan.text_box.width_pt
        ):
            stamp_suppressed = True
            layout_plan = self._plan_for_appearance(
                appearance=appearance,
                stamp_text=stamp_text if options.include_text else " ",
                signature_rect=signature_rect,
                include_stamp=False,
                use_horizontal_ink_reservation=False,
                ink_measurer=ink_measurer,
            )

        style = PyHankoSignatureAppearanceAdapter().build_stamp_style(
            appearance=appearance,
            stamp_text=stamp_text if options.include_text else " ",
            stamp_background=(
                stamp_background
                if options.include_stamp
                and options.include_background
                and not stamp_suppressed
                else None
            ),
            signature_rect=signature_rect,
            layout_plan=layout_plan,
            allow_fit_issues=options.allow_fit_issues,
            include_border=options.include_text and options.include_border,
            include_background=(
                options.include_stamp and options.include_background and not stamp_suppressed
            ),
        )
        return CanonicalPreviewLayout(
            style=style,
            background_layout=style.background_layout,
            content_layout=style.inner_content_layout,
            layout_plan=layout_plan,
            stamp_suppressed=stamp_suppressed,
            fit_issues=layout_plan.fit_issues,
        )

    def _plan_for_appearance(
        self,
        *,
        appearance: SigningBackendAppearance,
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


class PyHankoSignatureAppearanceAdapter:
    """Build pyHanko stamp styles from a visible-signature layout plan."""

    def build_stamp_style(
        self,
        *,
        appearance: SigningBackendAppearance,
        stamp_text: str,
        stamp_background: object | None,
        signature_rect: SignatureRect,
        layout_plan: SignatureLayoutPlan,
        allow_fit_issues: bool = False,
        include_border: bool = True,
        include_background: bool = True,
    ) -> object:
        """Return the pyHanko stamp style represented by ``layout_plan``."""

        if layout_plan.fit_issues and not allow_fit_issues:
            raise ValueError("; ".join(issue.message for issue in layout_plan.fit_issues))

        from foliaseal.application.phase3_signing_backend import (
            RoundedBorderTextStampStyle,
            _background_layout_for_stamp,
            _build_text_box_style,
            _hex_to_rgb,
            _solid_background_for_color,
        )

        box_style = appearance.box_style
        border_width = (
            max(0, int(round(box_style.border_width_pt)))
            if box_style.show_border and include_border
            else 0
        )
        background = (
            stamp_background or _solid_background_for_color(box_style.background_color_hex)
            if include_background
            else None
        )
        text_box_style = _build_text_box_style(appearance.text_style)
        background_layout = _background_layout_for_stamp(
            appearance.layout_template,
            stamp_position=appearance.stamp_position,
            stamp_background=stamp_background,
            signature_rect=signature_rect,
            text_box_width=layout_plan.background_text_box_width_pt,
            text_box_height=layout_plan.text_box.height_pt,
            box_style=appearance.box_style,
        )
        return RoundedBorderTextStampStyle(
            border_width=border_width,
            border_color=_hex_to_rgb(box_style.border_color_hex),
            background=background,
            background_layout=background_layout,
            background_opacity=1.0,
            text_box_style=text_box_style,
            inner_content_layout=layout_plan.backend_reservation.inner_content_layout,
            stamp_text=stamp_text,
            timestamp_format=appearance.datetime_format,
        )


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


def _layout_rule_spec(rule: object) -> LayoutRuleSpec:
    margins = getattr(rule, "margins")
    return LayoutRuleSpec(
        x_align=_enum_name(getattr(rule, "x_align")),
        y_align=_enum_name(getattr(rule, "y_align")),
        margins=LayoutMargins(
            left=int(round(getattr(margins, "left", 0))),
            right=int(round(getattr(margins, "right", 0))),
            top=int(round(getattr(margins, "top", 0))),
            bottom=int(round(getattr(margins, "bottom", 0))),
        ),
        scaling=_enum_name(getattr(rule, "inner_content_scaling")),
    )


def _enum_name(value: object) -> str:
    name = getattr(value, "name", None)
    if isinstance(name, str):
        return name
    return str(value)
