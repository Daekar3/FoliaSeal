"""Concrete Phase 3 signing executor wiring."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from io import BytesIO
from math import ceil
from pathlib import Path

from asn1crypto import pkcs12
from PIL import Image
from pyhanko.pdf_utils.font.basic import SimpleFontEngineFactory
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.layout import (
    AxisAlignment,
    BoxConstraints,
    InnerScaling,
    Margins,
    SimpleBoxLayoutRule,
)
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.text import TextBox, TextBoxStyle
from pyhanko.pdf_utils.writer import PdfFileWriter
from pyhanko.sign import fields, validation
from pyhanko.sign.signers import PdfSignatureMetadata, PdfSigner, SimpleSigner
from pyhanko.stamp import TextStampStyle
from pyhanko_certvalidator import ValidationContext

from foliaseal.application.sign_pdf_use_case import (
    SigningBackendAppearance,
    SigningBackendFieldBinding,
    SigningBackendRequest,
    SignPdfUseCase,
)
from foliaseal.application.signing_draft_workflow import (
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
)
from foliaseal.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    TsaUnavailableError,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningOutput,
    SigningRequest,
    SigningResult,
    VerificationSummary,
)

_PDF_VERSION_PATTERN = re.compile(rb"%PDF-(\d+\.\d+)")
_SIG_FIELD_NAME = "Signature1"


class PyHankoPdfInspector:
    """Read the PDF version from the source file header."""

    def get_pdf_version(self, input_pdf_path: str) -> str:
        path = Path(input_pdf_path)
        if not path.exists():
            raise FileNotFoundError(input_pdf_path)
        with path.open("rb") as handle:
            header = handle.read(16)
        match = _PDF_VERSION_PATTERN.search(header)
        if match is None:
            raise ValueError(f"Could not read PDF version from '{input_pdf_path}'.")
        return match.group(1).decode("ascii")


class PyHankoCertificateLoader:
    """Validate PKCS#12 signing material using pyHanko's signer loader."""

    def validate(self, certificate_path: str, passphrase: str) -> None:
        _load_simple_signer(certificate_path, passphrase)


class PyHankoPdfSigner:
    """Produce a genuinely signed PDF using pyHanko."""

    def sign(self, request: SigningBackendRequest) -> SigningOutput:
        input_path = Path(request.input_pdf_path)
        if not input_path.exists():
            raise FileNotFoundError(request.input_pdf_path)
        appearance = request.signature_appearance
        if request.signature_rect is None or appearance is None:
            raise ValueError("A visible signature rectangle and appearance are required.")
        if request.timestamp_required:
            raise TsaUnavailableError(
                "Timestamping is not configured for the concrete signing backend yet."
            )

        fit_issues = _visible_signature_fit_issues(
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            signature_rect=request.signature_rect,
            signature_appearance=appearance,
        )
        if any(issue.severity == SigningDraftValidationSeverity.ERROR for issue in fit_issues):
            raise ValueError("; ".join(issue.message for issue in fit_issues))

        signer = _load_simple_signer(request.certificate_path, request.passphrase)
        signing_time = _current_signing_time(appearance.timezone_display_mode)
        stamp_text = _build_stamp_text(
            appearance=appearance,
            signer=signer,
            signing_time=signing_time,
            signature_rect=request.signature_rect,
        )
        stamp_style = _build_stamp_style(
            appearance,
            stamp_text=stamp_text,
            stamp_background=_stamp_background_for_path(appearance.image_stamp_path),
            signature_rect=request.signature_rect,
        )
        metadata = PdfSignatureMetadata(
            field_name=_SIG_FIELD_NAME,
            md_algorithm="sha256",
            name=_signature_name_for_metadata(request, signer),
            reason=_visible_reason(appearance, signer),
            location=_visible_location(appearance, signer),
            contact_info=_visible_email(appearance, signer),
            subfilter=fields.SigSeedSubFilter.ADOBE_PKCS7_DETACHED,
        )
        field_spec = fields.SigFieldSpec(
            sig_field_name=_SIG_FIELD_NAME,
            on_page=request.signature_rect.page_index,
            box=_rect_to_box(request.signature_rect),
            readable_field_name="Visible signature",
        )

        with input_path.open("rb") as input_stream:
            writer = IncrementalPdfFileWriter(input_stream)
            signed_output = BytesIO()
            signer_engine = PdfSigner(
                metadata,
                signer,
                stamp_style=stamp_style,
                new_field_spec=field_spec,
            )
            signer_engine.sign_pdf(writer, output=signed_output)
        output_bytes = signed_output.getvalue()

        return SigningOutput(
            output_bytes=output_bytes,
            output_pdf_version=_read_pdf_version_from_bytes(output_bytes)
            or self._fallback_pdf_version(input_path),
            signature_subfilter="adbe.pkcs7.detached",
            timestamp_present=_signature_has_timestamp(output_bytes),
        )

    @staticmethod
    def _fallback_pdf_version(input_path: Path) -> str:
        with input_path.open("rb") as handle:
            header = handle.read(16)
        match = _PDF_VERSION_PATTERN.search(header)
        return match.group(1).decode("ascii") if match else "1.7"


class PyHankoSignatureVerifier:
    """Cryptographically validate the signed output PDF."""

    def verify(self, output_pdf_path: str) -> VerificationSummary:
        path = Path(output_pdf_path)
        if not path.exists():
            raise FileNotFoundError(output_pdf_path)

        with path.open("rb") as handle:
            reader = PdfFileReader(handle)
            embedded_signatures = list(reader.embedded_signatures)
            if not embedded_signatures:
                raise ValueError("No embedded signature fields were found in the output PDF.")

            signature = embedded_signatures[-1]
            validation_context = ValidationContext(trust_roots=[signature.signer_cert])
            status = validation.validate_pdf_signature(
                signature,
                signer_validation_context=validation_context,
            )

        if not status.intact or not status.valid:
            raise ValueError("The signed PDF failed cryptographic validation.")

        return VerificationSummary(
            signature_count=len(embedded_signatures),
            timestamp_present=_status_has_timestamp(status),
        )


@dataclass(frozen=True)
class Phase3SigningExecutor:
    """Concrete executor used by the Phase 3 shell and harness."""

    use_case: SignPdfUseCase

    def execute(self, request: SigningRequest) -> SigningResult:
        return self.use_case.execute(request)


def build_phase3_signing_executor() -> Phase3SigningExecutor:
    """Build the concrete signing executor used by the Phase 3 shell."""
    use_case = SignPdfUseCase(
        inspector=PyHankoPdfInspector(),
        certificate_loader=PyHankoCertificateLoader(),
        signer=PyHankoPdfSigner(),
        verifier=PyHankoSignatureVerifier(),
    )
    return Phase3SigningExecutor(use_case=use_case)


def _load_simple_signer(certificate_path: str, passphrase: str) -> SimpleSigner:
    path = Path(certificate_path)
    if not path.exists():
        raise FileNotFoundError(certificate_path)

    try:
        signer = SimpleSigner.load_pkcs12(
            str(path),
            passphrase=passphrase.encode("utf-8"),
        )
    except FileNotFoundError:
        raise
    except ValueError as exc:
        message = str(exc)
        if _looks_like_wrong_password(path, message):
            raise CertificateWrongPasswordError(message) from exc
        raise CertificateLoadError(message) from exc
    except Exception as exc:  # pragma: no cover - defensive mapping for stable contracts.
        raise CertificateLoadError(str(exc)) from exc
    if signer is None:
        message = "Could not load key material from PKCS#12 data"
        if _is_pkcs12_container(path):
            raise CertificateWrongPasswordError(message)
        raise CertificateLoadError(message)
    return signer


def _build_stamp_style(
    appearance: SigningBackendAppearance,
    *,
    stamp_text: str,
    stamp_background: PdfImage | None,
    signature_rect: SignatureRect,
) -> TextStampStyle:
    text_style = appearance.text_style
    box_style = appearance.box_style
    border_width = max(0, int(round(box_style.border_width_pt))) if box_style.show_border else 0
    border_color = _hex_to_rgb(box_style.border_color_hex)
    background = stamp_background or _solid_background_for_color(box_style.background_color_hex)
    text_box_style = _build_text_box_style(text_style)
    text_box_width, text_box_height = _measure_text_box_dimensions(
        stamp_text,
        text_box_style,
    )
    layout_reservation = _layout_reservation_for_template(
        appearance.layout_template,
        stamp_position=appearance.stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=appearance.box_style,
        has_visible_stamp_image=stamp_background is not None,
    )
    _ensure_layout_can_fit(layout_reservation)
    background_layout = _background_layout_for_stamp(
        appearance.layout_template,
        stamp_position=appearance.stamp_position,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=appearance.box_style,
    )
    return TextStampStyle(
        border_width=border_width,
        border_color=border_color,
        background=background,
        background_layout=background_layout,
        background_opacity=1.0,
        text_box_style=text_box_style,
        inner_content_layout=layout_reservation.inner_content_layout,
        stamp_text=stamp_text,
        timestamp_format=appearance.datetime_format,
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
    background_layout: SimpleBoxLayoutRule
    inner_content_layout: SimpleBoxLayoutRule


@dataclass(frozen=True)
class VisibleSignatureTextLayout:
    """Composed visible-signature text shared by preview and backend fit checks."""

    title_text: str
    detail_text: str
    stamp_text: str


def _build_text_box_style(text_style: SignatureTextStyle) -> TextBoxStyle:
    font_factory = _font_factory_for_family(text_style.font_family)
    return TextBoxStyle(
        font=font_factory,
        font_size=max(1, int(round(text_style.font_size_pt))),
        text_color=_hex_to_rgb(text_style.text_color_hex),
        box_layout_rule=SimpleBoxLayoutRule(
            AxisAlignment.ALIGN_MIN,
            AxisAlignment.ALIGN_MAX,
            margins=Margins.uniform(0),
            inner_content_scaling=InnerScaling.NO_SCALING,
        ),
    )


def _compose_visible_signature_text_layout(
    *,
    signer_label_prefix: str,
    layout_template: SignatureLayoutTemplate,
    body_fragments: list[str],
) -> VisibleSignatureTextLayout:
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
    return VisibleSignatureTextLayout(
        title_text=title_text,
        detail_text=detail_text,
        stamp_text=_escape_percent(stamp_text),
    )


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


def _border_safe_inset(box_style: SignatureBoxStyle | None) -> int:
    if box_style is None or not box_style.show_border:
        return 0
    return max(0, int(ceil(box_style.border_width_pt / 2.0)) + 1)


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
    """Use the same border-aware outer inset for all vertical single-line content."""

    return _effective_layout_edge_margin(
        stamp_position=SignatureStampPosition.TOP,
        box_height=box_height,
        box_style=box_style,
    )


def _single_line_stamp_content_inset(
    *,
    stamp_position: SignatureStampPosition,
    box_width: int,
    box_height: int,
    reserved_width: int | None = None,
    reserved_height: int | None = None,
) -> int:
    """Reserve a small internal gutter so fitted stamp content is not flush to the band edge."""

    effective_width = (
        reserved_width
        if isinstance(reserved_width, int) and reserved_width > 0
        else box_width
    )
    effective_height = (
        reserved_height if isinstance(reserved_height, int) and reserved_height > 0 else box_height
    )
    shortest_edge = max(1, min(effective_width, effective_height))
    if stamp_position in {
        SignatureStampPosition.TOP,
        SignatureStampPosition.BOTTOM,
    }:
        return max(1, min(2, int(round(shortest_edge * 0.08))))
    if stamp_position in {
        SignatureStampPosition.LEFT,
        SignatureStampPosition.RIGHT,
    }:
        return max(1, min(2, int(round(shortest_edge * 0.04))))
    return 0


def _stamp_image_aspect_ratio(stamp_background: PdfImage | None) -> float | None:
    if stamp_background is None:
        return None
    image = getattr(stamp_background, "image", None)
    if image is None or not hasattr(image, "size"):
        return None
    image_width, image_height = image.size
    if image_width <= 0 or image_height <= 0:
        return None
    return image_width / image_height


def _single_line_horizontal_minimum_stamp_width(
    *,
    available_height: int,
    box_width: int,
    box_height: int,
    stamp_aspect_ratio: float | None,
) -> int:
    if available_height <= 0:
        return 0
    content_inset = _single_line_stamp_content_inset(
        stamp_position=SignatureStampPosition.RIGHT,
        box_width=box_width,
        box_height=box_height,
        reserved_width=box_width,
        reserved_height=available_height,
    )
    fit_height = max(1, available_height - content_inset * 2)
    if stamp_aspect_ratio is None:
        content_width = max(6, int(round(fit_height * 1.5)))
    else:
        content_width = max(1, int(round(fit_height * min(stamp_aspect_ratio, 6.0))))
    return max(1, content_width + content_inset * 2)


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
    """Compute the actual reserved-space split for the requested rectangle."""
    box_width = max(1, int(round(signature_rect.width_pt)))
    box_height = max(1, int(round(signature_rect.height_pt)))
    edge_margin, gap = _base_layout_spacing(
        stamp_position=stamp_position,
        box_height=box_height,
    )
    edge_margin = max(edge_margin, _border_safe_inset(box_style))
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
        full_margins = Margins(
            left=edge_margin,
            right=edge_margin,
            top=vertical_margin,
            bottom=vertical_margin,
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
            background_layout=SimpleBoxLayoutRule(
                AxisAlignment.ALIGN_MID,
                AxisAlignment.ALIGN_MID,
                margins=full_margins,
                inner_content_scaling=InnerScaling.STRETCH_TO_FIT,
            ),
            inner_content_layout=SimpleBoxLayoutRule(
                AxisAlignment.ALIGN_MIN
                if stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.LEFT}
                else AxisAlignment.ALIGN_MID,
                AxisAlignment.ALIGN_MID,
                margins=full_margins,
                inner_content_scaling=InnerScaling.NO_SCALING,
            ),
        )

    if stamp_position in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}:
        minimum_stamp_width = 0
        if layout_template == SignatureLayoutTemplate.SINGLE_LINE and has_visible_stamp_image:
            minimum_stamp_width = _single_line_horizontal_minimum_stamp_width(
                available_height=available_height,
                box_width=box_width,
                box_height=box_height,
                stamp_aspect_ratio=stamp_aspect_ratio,
            )
        text_area_width = min(
            _effective_horizontal_text_reservation_width(
                layout_template=layout_template,
                stamp_position=stamp_position,
                text_box_width=text_box_width,
            ),
            max(available_width - minimum_stamp_width, 0),
        )
        remaining_width = max(available_width - text_area_width, 0)
        separator_width = min(gap, max(remaining_width - minimum_stamp_width, 0))
        stamp_area_width = max(remaining_width - separator_width, 0)
        reserved_primary_extent = stamp_area_width
        stamp_area_height = available_height
        text_area_height = available_height

        if stamp_position == SignatureStampPosition.LEFT:
            background_margins = Margins(
                left=edge_margin,
                right=text_area_width + separator_width + edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            text_margins = Margins(
                left=stamp_area_width + separator_width + edge_margin,
                right=edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            background_alignment = AxisAlignment.ALIGN_MIN
            text_alignment = AxisAlignment.ALIGN_MAX
        else:
            background_margins = Margins(
                left=text_area_width + separator_width + edge_margin,
                right=edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            text_margins = Margins(
                left=edge_margin,
                right=stamp_area_width + separator_width + edge_margin,
                top=edge_margin,
                bottom=edge_margin,
            )
            background_alignment = AxisAlignment.ALIGN_MAX
            text_alignment = AxisAlignment.ALIGN_MIN

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
            background_layout=SimpleBoxLayoutRule(
                background_alignment,
                AxisAlignment.ALIGN_MID,
                margins=background_margins,
                inner_content_scaling=InnerScaling.STRETCH_TO_FIT,
            ),
            inner_content_layout=SimpleBoxLayoutRule(
                text_alignment,
                AxisAlignment.ALIGN_MID,
                margins=text_margins,
                inner_content_scaling=InnerScaling.NO_SCALING,
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
        background_margins = Margins(
            left=edge_margin,
            right=edge_margin,
            top=vertical_top_margin,
            bottom=text_area_height + separator_height + vertical_bottom_margin,
        )
        text_margins = Margins(
            left=edge_margin,
            right=edge_margin,
            top=stamp_area_height + separator_height + vertical_top_margin,
            bottom=vertical_bottom_margin,
        )
        background_alignment = (
            AxisAlignment.ALIGN_MID
            if layout_template == SignatureLayoutTemplate.SINGLE_LINE
            else AxisAlignment.ALIGN_MID
        )
        text_alignment = AxisAlignment.ALIGN_MID
        background_y_alignment = AxisAlignment.ALIGN_MAX
        text_y_alignment = AxisAlignment.ALIGN_MIN
    else:
        background_margins = Margins(
            left=edge_margin,
            right=edge_margin,
            top=text_area_height + separator_height + vertical_top_margin,
            bottom=vertical_bottom_margin,
        )
        text_margins = Margins(
            left=edge_margin,
            right=edge_margin,
            top=vertical_top_margin,
            bottom=stamp_area_height + separator_height + vertical_bottom_margin,
        )
        background_alignment = (
            AxisAlignment.ALIGN_MID
            if layout_template == SignatureLayoutTemplate.SINGLE_LINE
            else AxisAlignment.ALIGN_MID
        )
        text_alignment = AxisAlignment.ALIGN_MID
        if layout_template == SignatureLayoutTemplate.SINGLE_LINE:
            background_y_alignment = AxisAlignment.ALIGN_MID
            text_y_alignment = AxisAlignment.ALIGN_MID
        else:
            background_y_alignment = AxisAlignment.ALIGN_MIN
            text_y_alignment = AxisAlignment.ALIGN_MAX

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
        background_layout=SimpleBoxLayoutRule(
            background_alignment,
            background_y_alignment,
            margins=background_margins,
            inner_content_scaling=InnerScaling.STRETCH_TO_FIT,
        ),
        inner_content_layout=SimpleBoxLayoutRule(
            text_alignment,
            text_y_alignment,
            margins=text_margins,
            inner_content_scaling=InnerScaling.NO_SCALING,
        ),
    )


def _background_layout_for_stamp(
    layout_template: SignatureLayoutTemplate,
    *,
    stamp_position: SignatureStampPosition,
    stamp_background: PdfImage | None,
    signature_rect: SignatureRect,
    text_box_width: int,
    text_box_height: int,
    box_style: SignatureBoxStyle | None = None,
) -> SimpleBoxLayoutRule:
    reservation = _layout_reservation_for_template(
        layout_template,
        stamp_position=stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=box_style,
        has_visible_stamp_image=stamp_background is not None,
        stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
    )
    if stamp_background is None:
        return reservation.background_layout
    background_layout = replace(
        reservation.background_layout,
        inner_content_scaling=InnerScaling.SHRINK_TO_FIT,
    )
    image = getattr(stamp_background, "image", None)
    if image is None or not hasattr(image, "size"):
        return background_layout

    image_width, image_height = image.size
    if image_height <= 0:
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
    fit_width = max(1, area_width - content_inset * 2)
    fit_height = max(1, area_height - content_inset * 2)
    aspect_ratio = image_width / image_height
    target_width = fit_width
    target_height = max(1, int(round(target_width / aspect_ratio)))
    if target_height > fit_height:
        target_height = fit_height
        target_width = max(1, int(round(target_height * aspect_ratio)))

    if (
        layout_template == SignatureLayoutTemplate.SINGLE_LINE
        and stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}
    ):
        extra_x_left = 0
        extra_x_right = max(0, area_width - target_width)
    else:
        centered_extra_x = max(0, area_width - target_width) // 2
        extra_x_left = centered_extra_x
        extra_x_right = centered_extra_x
    extra_y = max(0, area_height - target_height) // 2
    margins = background_layout.margins
    return replace(
        background_layout,
        margins=Margins(
            left=margins.left + extra_x_left,
            right=margins.right + extra_x_right,
            top=margins.top + extra_y,
            bottom=margins.bottom + extra_y,
        ),
    )


def _visible_signature_fit_issues(
    *,
    certificate_path: str,
    passphrase: str,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
) -> tuple[SigningDraftValidationIssue, ...]:
    """Return backend-side layout fit issues for the requested visible signature."""
    try:
        signer = _load_simple_signer(certificate_path, passphrase)
        signing_time = _current_signing_time(signature_appearance.timezone_display_mode)
        stamp_text = _build_stamp_text(
            appearance=signature_appearance,
            signer=signer,
            signing_time=signing_time,
            signature_rect=signature_rect,
        )
        stamp_background = _stamp_background_for_path(signature_appearance.image_stamp_path)
        return _visible_signature_fit_issues_for_stamp_text(
            signature_rect=signature_rect,
            signature_appearance=signature_appearance,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
        )
    except Exception as exc:
        return (
            SigningDraftValidationIssue(
                code="visible_signature_layout_unavailable",
                message=str(exc),
                field_name="signature_appearance",
                severity=SigningDraftValidationSeverity.ERROR,
            ),
        )


def _visible_signature_fit_issues_for_stamp_text(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
    stamp_background: PdfImage | None,
) -> tuple[SigningDraftValidationIssue, ...]:
    try:
        _build_stamp_style(
            signature_appearance,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            signature_rect=signature_rect,
        )
    except Exception as exc:
        return (
            SigningDraftValidationIssue(
                code="visible_signature_layout_unavailable",
                message=str(exc),
                field_name="signature_appearance",
                severity=SigningDraftValidationSeverity.ERROR,
            ),
        )
    return ()


def _ensure_layout_can_fit(layout_reservation: _SignatureLayoutReservation) -> None:
    max_text_width = layout_reservation.text_area_width_pt
    if (
        layout_reservation.layout_template == SignatureLayoutTemplate.SINGLE_LINE
    ):
        max_text_width = int(
            round(
                layout_reservation.text_area_width_pt
                * _single_line_width_overflow_tolerance(
                    stamp_position=layout_reservation.stamp_position
                )
            )
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


def _build_stamp_text(
    *,
    appearance: SigningBackendAppearance,
    signer: SimpleSigner,
    signing_time: datetime,
    signature_rect: SignatureRect | None = None,
) -> str:
    body_fragments: list[str] = []
    prefix = appearance.signer_label_prefix.strip()

    for binding in appearance.field_bindings:
        field_key = binding.field_key
        if not _should_render_field(binding):
            continue
        text = _resolve_visible_field_text(
            field_key,
            binding,
            signer=signer,
            appearance=appearance,
            signing_time=signing_time,
        )
        if not text:
            continue
        if appearance.show_field_names:
            body_fragments.append(f"{_field_label(field_key)}: {text}")
        else:
            body_fragments.append(text)
    return _compose_visible_signature_text_layout(
        signer_label_prefix=prefix,
        layout_template=appearance.layout_template,
        body_fragments=body_fragments,
    ).stamp_text


def _single_line_width_overflow_tolerance(
    *,
    stamp_position: SignatureStampPosition,
) -> float:
    """Allow modest horizontal text overflow to free more room for the stamp.

    Left/right single-line layouts need more flexibility because text and stamp
    share the same width. Top/bottom layouts still benefit from a smaller bounded
    tolerance so fit decisions do not change at arbitrary box-height cutoffs.
    """

    if stamp_position in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}:
        return 1.65
    return 1.5


def _single_line_text_fits_reservation(
    *,
    appearance: SigningBackendAppearance,
    signature_rect: SignatureRect,
    text: str,
) -> bool:
    text_box_style = _build_text_box_style(appearance.text_style)
    text_box_width, text_box_height = _measure_text_box_dimensions(text, text_box_style)
    reservation = _layout_reservation_for_template(
        appearance.layout_template,
        stamp_position=appearance.stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=appearance.box_style,
        has_visible_stamp_image=appearance.image_stamp_path is not None,
        stamp_aspect_ratio=_stamp_image_aspect_ratio(
            _stamp_background_for_path(appearance.image_stamp_path)
            if appearance.image_stamp_path is not None
            else None
        ),
    )
    try:
        _ensure_layout_can_fit(reservation)
    except ValueError:
        return False
    return True


def _effective_horizontal_text_reservation_width(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    text_box_width: int,
) -> int:
    if layout_template != SignatureLayoutTemplate.SINGLE_LINE:
        return text_box_width
    return max(
        1,
        int(
            ceil(
                text_box_width
                / _single_line_width_overflow_tolerance(
                    stamp_position=stamp_position
                )
            )
        ),
    )


def _stamp_background_for_path(image_stamp_path: str | None) -> PdfImage | None:
    if image_stamp_path is None:
        return None
    try:
        with Image.open(image_stamp_path) as image:
            return PdfImage(image.copy(), writer=None)
    except FileNotFoundError as exc:
        raise ValueError(f"Image stamp path not found: {image_stamp_path}") from exc
    except OSError as exc:
        raise ValueError(f"Image stamp path is not a readable image: {image_stamp_path}") from exc


def _solid_background_for_color(color_hex: str) -> PdfImage:
    red, green, blue = (
        int(component * 255) for component in _hex_to_rgb(color_hex)
    )
    image = Image.new("RGB", (16, 16), color=(red, green, blue))
    return PdfImage(image, writer=None)


def _resolve_visible_field_text(
    field_key: SignatureFieldKey,
    binding: SigningBackendFieldBinding,
    *,
    signer: SimpleSigner,
    appearance: SigningBackendAppearance,
    signing_time: datetime,
) -> str:
    if binding.source == SignatureFieldSource.OVERRIDE:
        return binding.override_text or ""
    if binding.source == SignatureFieldSource.HIDDEN:
        return ""
    if field_key == SignatureFieldKey.SIGNING_TIME:
        return _format_signing_time(signing_time, appearance.datetime_format)

    subject = signer.signing_cert.subject.native
    if field_key == SignatureFieldKey.DISTINGUISHED_NAME:
        dn_parts = [
            value
            for value in (
                _subject_value(subject, "common_name"),
                _subject_value(subject, "email_address"),
                (
                    _subject_value(subject, "title")
                    or _subject_value(subject, "organizational_unit_name")
                ),
                _subject_value(subject, "organization_name"),
                _derived_location(subject),
            )
            if value
        ]
        return ", ".join(dn_parts)
    if field_key == SignatureFieldKey.COMMON_NAME:
        return _subject_value(subject, "common_name") or signer.subject_name
    if field_key == SignatureFieldKey.EMAIL:
        return _subject_value(subject, "email_address") or ""
    if field_key == SignatureFieldKey.TITLE:
        return str(
            _subject_value(subject, "title")
            or _subject_value(subject, "organizational_unit_name")
            or ""
        )
    if field_key == SignatureFieldKey.COMPANY:
        return _subject_value(subject, "organization_name") or ""
    if field_key == SignatureFieldKey.REASON:
        return ""
    if field_key == SignatureFieldKey.LOCATION:
        return _derived_location(subject)
    return binding.display_label or _field_label(field_key)


def _subject_value(subject: dict[str, object], key: str) -> str | None:
    value = subject.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _derived_location(subject: dict[str, object]) -> str:
    location_parts = [
        part
        for part in (
            _subject_value(subject, "locality_name"),
            _subject_value(subject, "state_or_province_name"),
            _subject_value(subject, "country_name"),
        )
        if part
    ]
    return ", ".join(location_parts)


def _content_layout_for_template(
    layout_template: SignatureLayoutTemplate,
    *,
    stamp_position: SignatureStampPosition,
    signature_rect: SignatureRect,
    stamp_background: PdfImage | None,
    text_box_width: int,
    text_box_height: int,
    box_style: SignatureBoxStyle | None = None,
) -> SimpleBoxLayoutRule:
    return _layout_reservation_for_template(
        layout_template,
        stamp_position=stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=box_style,
        has_visible_stamp_image=stamp_background is not None,
        stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
    ).inner_content_layout


def _background_layout_for_template(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    signature_rect: SignatureRect,
    stamp_background: PdfImage | None,
    text_box_width: int,
    text_box_height: int,
    box_style: SignatureBoxStyle | None = None,
) -> SimpleBoxLayoutRule:
    return _layout_reservation_for_template(
        layout_template,
        stamp_position=stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=box_style,
        has_visible_stamp_image=stamp_background is not None,
        stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
    ).background_layout


def _measure_text_box_dimensions(
    stamp_text: str,
    text_box_style: TextBoxStyle,
) -> tuple[int, int]:
    writer = PdfFileWriter()
    text_box = TextBox(
        text_box_style,
        writer=writer,
        resources=None,
        box=BoxConstraints(),
    )
    text_box.content = stamp_text
    text_box.render()
    return int(round(text_box.box.width)), int(round(text_box.box.height))


def _reserved_space(container_length: int, content_length: int, gap: int) -> int:
    desired = content_length + gap + 4
    upper_bound = max(container_length - 4, 0)
    return max(0, min(desired, upper_bound))


def _should_render_field(binding: SigningBackendFieldBinding) -> bool:
    return binding.show_in_visible_appearance and binding.source != SignatureFieldSource.HIDDEN


def _signature_name_for_metadata(
    request: SigningBackendRequest,
    signer: SimpleSigner,
) -> str:
    if request.certificate_alias:
        return request.certificate_alias
    return signer.subject_name


def _visible_reason(appearance: SigningBackendAppearance, signer: SimpleSigner) -> str | None:
    binding = _binding_for_field(appearance, SignatureFieldKey.REASON)
    if binding is None or not _should_render_field(binding):
        return None
    return _resolve_visible_field_text(
        SignatureFieldKey.REASON,
        binding,
        signer=signer,
        appearance=appearance,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
    )


def _visible_location(appearance: SigningBackendAppearance, signer: SimpleSigner) -> str | None:
    binding = _binding_for_field(appearance, SignatureFieldKey.LOCATION)
    if binding is None or not _should_render_field(binding):
        return None
    return _resolve_visible_field_text(
        SignatureFieldKey.LOCATION,
        binding,
        signer=signer,
        appearance=appearance,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
    )


def _visible_email(appearance: SigningBackendAppearance, signer: SimpleSigner) -> str | None:
    binding = _binding_for_field(appearance, SignatureFieldKey.EMAIL)
    if binding is None or not _should_render_field(binding):
        return None
    return _resolve_visible_field_text(
        SignatureFieldKey.EMAIL,
        binding,
        signer=signer,
        appearance=appearance,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
    )


def _current_signing_time(timezone_mode: SignatureTimezoneDisplayMode) -> datetime:
    timestamp = datetime.now(UTC)
    if timezone_mode is SignatureTimezoneDisplayMode.LOCAL:
        timestamp = timestamp.astimezone()
    return timestamp


def _format_signing_time(signing_time: datetime, datetime_format: str) -> str:
    return signing_time.strftime(datetime_format)


def _rect_to_box(signature_rect) -> tuple[int, int, int, int]:
    left = int(round(signature_rect.left_pt))
    bottom = int(round(signature_rect.bottom_pt))
    right = int(round(signature_rect.left_pt + signature_rect.width_pt))
    top = int(round(signature_rect.bottom_pt + signature_rect.height_pt))
    return (left, bottom, right, top)


def _font_factory_for_family(font_family: str) -> SimpleFontEngineFactory:
    normalized = font_family.strip().lower()
    if "courier" in normalized or "mono" in normalized or "code" in normalized:
        return SimpleFontEngineFactory("Courier", 0.6)
    if "times" in normalized or "serif" in normalized:
        return SimpleFontEngineFactory("Times-Roman", 0.5)
    return SimpleFontEngineFactory("Helvetica", 0.5)


def _hex_to_rgb(color_hex: str) -> tuple[float, float, float]:
    normalized = color_hex.strip().lstrip("#")
    return tuple(int(normalized[index : index + 2], 16) / 255.0 for index in (0, 2, 4))  # type: ignore[return-value]


def _escape_percent(value: str) -> str:
    return value.replace("%", "%%")


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


def _read_pdf_version_from_bytes(output_bytes: bytes) -> str | None:
    version_match = _PDF_VERSION_PATTERN.search(output_bytes[:16])
    if version_match is None:
        return None
    return version_match.group(1).decode("ascii")


def _signature_has_timestamp(output_bytes: bytes) -> bool:
    with BytesIO(output_bytes) as handle:
        reader = PdfFileReader(handle)
        embedded_signatures = list(reader.embedded_signatures)
        if not embedded_signatures:
            return False
        return _status_has_timestamp(
            validation.validate_pdf_signature(
                embedded_signatures[-1],
                signer_validation_context=ValidationContext(
                    trust_roots=[embedded_signatures[-1].signer_cert]
                ),
            )
        )


def _status_has_timestamp(status) -> bool:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return False
    return bool(
        getattr(timestamp_validity, "intact", True)
        and getattr(timestamp_validity, "valid", True)
    )


def _looks_like_wrong_password(path: Path, message: str) -> bool:
    normalized = message.lower()
    mentions_password = (
        "invalid password" in normalized
        or "password" in normalized
        or "pkcs12 data" in normalized
        or "pkcs#12 data" in normalized
    )
    if not mentions_password:
        return False
    return _is_pkcs12_container(path)


def _is_pkcs12_container(path: Path) -> bool:
    try:
        pkcs12.Pfx.load(path.read_bytes()).native
    except Exception:
        return False
    return True


def _binding_for_field(
    appearance: SigningBackendAppearance,
    field_key: SignatureFieldKey,
) -> SigningBackendFieldBinding | None:
    for binding in appearance.field_bindings:
        if binding.field_key == field_key:
            return binding
    return None
