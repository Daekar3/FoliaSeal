"""Pillow and PyHanko materializers for visible-signature layout plans.

The application layout module owns only neutral geometry and fit evidence.  This
module is the composition edge for concrete rendering and signing artifacts.
"""

from __future__ import annotations

from PIL import Image
from pyhanko.pdf_utils.layout import AxisAlignment, InnerScaling, Margins, SimpleBoxLayoutRule

from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signature_text_measurement import SignatureTextBoxEngine
from foliaseal.application.visible_signature_layout import (
    ImageMetrics,
    LayoutRuleSpec,
    SignatureLayoutPlan,
    TextMetrics,
    _background_layout_spec_for_stamp,
)
from foliaseal.domain.models import SignatureRect


class PyHankoTextMeasurer:
    """Production text measurer backed by the current pyHanko text engine."""

    def __init__(self, engine: SignatureTextBoxEngine | None = None) -> None:
        self.engine = engine

    def measure(self, text: str, text_style) -> TextMetrics:
        from foliaseal.application.phase3_signing_backend import PyHankoSignatureTextBoxEngine

        engine = self.engine or PyHankoSignatureTextBoxEngine()
        return engine.prepare(text, text_style).metrics


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
            PyHankoSignatureTextBoxEngine,
            RoundedBorderTextStampStyle,
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
        text_box_style = (
            PyHankoSignatureTextBoxEngine()
            .prepare(
                stamp_text,
                appearance.text_style,
            )
            .render_style
        )
        background_layout = self.build_background_layout(
            appearance=appearance,
            stamp_background=stamp_background,
            signature_rect=signature_rect,
            layout_plan=layout_plan,
        )
        return RoundedBorderTextStampStyle(
            border_width=border_width,
            border_color=_hex_to_rgb(box_style.border_color_hex),
            background=background,
            background_layout=background_layout,
            background_opacity=1.0,
            text_box_style=text_box_style,
            inner_content_layout=pyhanko_layout_rule_from_spec(layout_plan.text_layout),
            stamp_text=stamp_text,
            timestamp_format=appearance.datetime_format,
        )

    def build_background_layout(
        self,
        *,
        appearance: SigningBackendAppearance,
        stamp_background: object | None,
        signature_rect: SignatureRect,
        layout_plan: SignatureLayoutPlan,
    ) -> object:
        """Return the fitted pyHanko background layout for one stamp style."""

        return materialize_background_layout(
            layout_template=appearance.layout_template,
            stamp_position=appearance.stamp_position,
            stamp_background=stamp_background,
            signature_rect=signature_rect,
            text_box_width=layout_plan.background_text_box_width_pt,
            text_box_height=layout_plan.text_box.height_pt,
            box_style=appearance.box_style,
            stamp_aspect_ratio=(
                None if layout_plan.stamp_image is None else layout_plan.stamp_image.aspect_ratio
            ),
        )


def materialize_background_layout(*args, **kwargs) -> object:
    """Materialize the neutral background rule for PyHanko callers."""

    return pyhanko_layout_rule_from_spec(_background_layout_spec_for_stamp(*args, **kwargs))


def pyhanko_layout_rule_from_spec(spec: LayoutRuleSpec) -> object:
    """Materialize a neutral layout rule at the PyHanko composition edge."""
    return SimpleBoxLayoutRule(
        x_align=AxisAlignment[spec.x_align],
        y_align=AxisAlignment[spec.y_align],
        margins=Margins(
            left=spec.margins.left,
            right=spec.margins.right,
            top=spec.margins.top,
            bottom=spec.margins.bottom,
        ),
        inner_content_scaling=InnerScaling[spec.scaling],
    )


__all__ = [
    "PillowStampImageProbe",
    "PyHankoSignatureAppearanceAdapter",
    "PyHankoTextMeasurer",
    "materialize_background_layout",
    "pyhanko_layout_rule_from_spec",
]
