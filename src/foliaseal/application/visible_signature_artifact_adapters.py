"""Concrete PyHanko/Pillow materialization for prepared visible-signature plans.

This module is deliberately an infrastructure-facing adapter. Neutral layout policy imports none of
these concrete types; callers use the ``SignatureAppearanceMaterializer`` protocol instead.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import ceil

from PIL import Image
from pyhanko.pdf_utils.font.opentype import GlyphAccumulatorFactory
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.layout import (
    AxisAlignment,
    BoxConstraints,
    InnerScaling,
    Margins,
    SimpleBoxLayoutRule,
)
from pyhanko.pdf_utils.text import TextBox, TextBoxStyle
from pyhanko.pdf_utils.writer import PdfFileWriter
from pyhanko.stamp import TextStamp, TextStampStyle

from foliaseal.application.signature_font_registry import resolve_signature_font_face
from foliaseal.application.signature_text_measurement import PreparedTextBox
from foliaseal.application.visible_signature_layout import (
    TextMetrics,
)
from foliaseal.domain.models import SignatureTextStyle


def _fmt_pdf_number(value: float) -> bytes:
    return f"{value:.4f}".rstrip("0").rstrip(".").encode("ascii")


def _rounded_border_radius_pt(width: float, height: float) -> float:
    shortest_edge = max(1.0, min(width, height))
    return min(6.0, shortest_edge / 4.0)


def _rounded_rect_stroke_command(*, width: float, height: float, border_width: float) -> bytes:
    inset = max(0.0, border_width / 2.0)
    stroke_width = max(0.0, width - border_width)
    stroke_height = max(0.0, height - border_width)
    radius = min(_rounded_border_radius_pt(width, height), stroke_width / 2.0, stroke_height / 2.0)
    if radius <= 0:
        return b"%s w %s %s %s %s re S" % (
            _fmt_pdf_number(border_width),
            _fmt_pdf_number(inset),
            _fmt_pdf_number(inset),
            _fmt_pdf_number(stroke_width),
            _fmt_pdf_number(stroke_height),
        )
    kappa = 0.5522847498
    control = radius * kappa
    left = inset
    bottom = inset
    right = left + stroke_width
    top = bottom + stroke_height
    return b" ".join(
        [
            _fmt_pdf_number(border_width), b"w",
            _fmt_pdf_number(left + radius), _fmt_pdf_number(bottom), b"m",
            _fmt_pdf_number(right - radius), _fmt_pdf_number(bottom), b"l",
            _fmt_pdf_number(right - radius + control), _fmt_pdf_number(bottom),
            _fmt_pdf_number(right), _fmt_pdf_number(bottom + radius - control),
            _fmt_pdf_number(right), _fmt_pdf_number(bottom + radius), b"c",
            _fmt_pdf_number(right), _fmt_pdf_number(top - radius), b"l",
            _fmt_pdf_number(right), _fmt_pdf_number(top - radius + control),
            _fmt_pdf_number(right - radius + control), _fmt_pdf_number(top),
            _fmt_pdf_number(right - radius), _fmt_pdf_number(top), b"c",
            _fmt_pdf_number(left + radius), _fmt_pdf_number(top), b"l",
            _fmt_pdf_number(left + radius - control), _fmt_pdf_number(top),
            _fmt_pdf_number(left), _fmt_pdf_number(top - radius + control),
            _fmt_pdf_number(left), _fmt_pdf_number(top - radius), b"c",
            _fmt_pdf_number(left), _fmt_pdf_number(bottom + radius), b"l",
            _fmt_pdf_number(left), _fmt_pdf_number(bottom + radius - control),
            _fmt_pdf_number(left + radius - control), _fmt_pdf_number(bottom),
            _fmt_pdf_number(left + radius), _fmt_pdf_number(bottom), b"c", b"S",
        ]
    )


class RoundedBorderTextStamp(TextStamp):
    """PyHanko stamp with the product's rounded border stream."""

    def render(self):
        command_stream = [b"q"]
        inner_content = self._render_inner_content()
        if self.style.background:
            command_stream.append(self._render_background())
        if inner_content:
            command_stream.extend(inner_content)
        bbox = self.box
        border_width = self.style.border_width
        border_color = self.style.border_color
        if border_width:
            if border_color:
                command_stream.append(b"%g %g %g RG" % border_color)
            command_stream.append(
                _rounded_rect_stroke_command(
                    width=bbox.width,
                    height=bbox.height,
                    border_width=border_width,
                )
            )
        command_stream.append(b"Q")
        return b" ".join(command_stream)


@dataclass(frozen=True)
class RoundedBorderTextStampStyle(TextStampStyle):
    def create_stamp(
        self,
        writer: PdfFileWriter,
        box: BoxConstraints,
        text_params: dict,
    ) -> RoundedBorderTextStamp:
        return RoundedBorderTextStamp(
            writer=writer,
            style=self,
            box=box,
            text_params=text_params,
        )


def _hex_to_rgb(color_hex: str) -> tuple[float, float, float]:
    normalized = color_hex.strip().lstrip("#")
    return tuple(
        int(normalized[index : index + 2], 16) / 255.0 for index in (0, 2, 4)
    )  # type: ignore[return-value]


def _font_factory_for_family(
    font_family: str,
    *,
    bold: bool = False,
    italic: bool = False,
    font_size: Fraction,
) -> GlyphAccumulatorFactory:
    face = resolve_signature_font_face(font_family, bold=bold, italic=italic)
    return GlyphAccumulatorFactory(font_file=str(face.font_file), font_size=float(font_size))


def _font_factory_for_text_style(
    text_style: SignatureTextStyle,
    *,
    font_size: Fraction,
) -> GlyphAccumulatorFactory:
    return _font_factory_for_family(
        text_style.font_family,
        bold=text_style.bold,
        italic=text_style.italic,
        font_size=font_size,
    )


def build_text_box_style(text_style: SignatureTextStyle) -> TextBoxStyle:
    """Build the exact half-point-aware PyHanko text style used by signing."""

    font_size = max(Fraction(1, 1), Fraction(int(round(text_style.font_size_pt * 2)), 2))
    return TextBoxStyle(
        font=_font_factory_for_text_style(text_style, font_size=font_size),
        font_size=font_size,
        text_color=_hex_to_rgb(text_style.text_color_hex),
        box_layout_rule=SimpleBoxLayoutRule(
            AxisAlignment.ALIGN_MIN,
            AxisAlignment.ALIGN_MAX,
            margins=Margins.uniform(0),
            inner_content_scaling=InnerScaling.NO_SCALING,
        ),
    )


def measure_text_box_dimensions(
    stamp_text: str,
    text_box_style: TextBoxStyle,
) -> tuple[int, int]:
    """Measure text while preserving the backend's multiline descender correction."""

    writer = PdfFileWriter()
    text_box = TextBox(
        text_box_style,
        writer=writer,
        resources=None,
        box=BoxConstraints(),
    )
    text_box.content = stamp_text
    text_box.render()
    measured_width = int(round(text_box.box.width))
    measured_height = int(round(text_box.box.height))
    line_count = max(1, stamp_text.count("\n") + 1)
    minimum_height = int(ceil(line_count * float(text_box_style.font_size)))
    if line_count > 1:
        minimum_height += 1
    return measured_width, max(measured_height, minimum_height)


@dataclass(frozen=True)
class PyHankoSignatureTextBoxEngine:
    """Production text measurer for the concrete materializer boundary."""

    def prepare(self, text: str, text_style: SignatureTextStyle) -> PreparedTextBox:
        text_box_style = build_text_box_style(text_style)
        width_pt, height_pt = measure_text_box_dimensions(text, text_box_style)
        return PreparedTextBox(
            metrics=TextMetrics(
                width_pt=width_pt,
                height_pt=height_pt,
                line_count=max(1, text.count("\n") + 1),
            ),
            render_style=text_box_style,
        )


def solid_background_for_color(color_hex: str) -> PdfImage:
    red, green, blue = (int(component * 255) for component in _hex_to_rgb(color_hex))
    return PdfImage(Image.new("RGB", (16, 16), color=(red, green, blue)), writer=None)


__all__ = [
    "PyHankoSignatureTextBoxEngine",
    "RoundedBorderTextStamp",
    "RoundedBorderTextStampStyle",
    "build_text_box_style",
    "measure_text_box_dimensions",
    "solid_background_for_color",
]
