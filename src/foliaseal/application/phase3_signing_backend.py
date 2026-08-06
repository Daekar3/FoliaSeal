"""Concrete Phase 3 signing executor wiring."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from fractions import Fraction
from io import BytesIO
from math import ceil
from pathlib import Path
from typing import Any

from asn1crypto import pkcs12
from PIL import Image
from pyhanko.pdf_utils.font.opentype import GlyphAccumulatorFactory
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
from pyhanko.sign.fields import InvisSigSettings
from pyhanko.sign.signers import PdfSignatureMetadata, PdfSigner, SimpleSigner
from pyhanko.sign.timestamps.common_utils import TimestampRequestError
from pyhanko.stamp import TextStamp, TextStampStyle
from pyhanko_certvalidator import ValidationContext

from foliaseal.application import text_raster_analysis as _text_raster_analysis
from foliaseal.application.horizontal_signature_reservation import (
    HorizontalSingleLineInkReservation,
    build_horizontal_single_line_ink_reservation,
    measure_horizontal_single_line_rendered_reference,
)
from foliaseal.application.preview_render_boundary import PreviewRasterRenderer
from foliaseal.application.sign_pdf_use_case import (
    SigningBackendAppearance,
    SigningBackendRequest,
    SignPdfUseCase,
)
from foliaseal.application.signature_font_registry import resolve_signature_font_face
from foliaseal.application.signature_text_measurement import (
    PreparedTextBox,
    SignatureTextBoxEngine,
)
from foliaseal.application.signing_draft_workflow import (
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
)
from foliaseal.application.stamp_background import (
    stamp_background_for_path as _neutral_stamp_background_for_path,
)
from foliaseal.application.stamp_preview_builder import (
    signing_draft_preview_for_stamp_text,
    stamp_text_preview_parts,
)
from foliaseal.application.visible_signature_color import text_style_color_rgba
from foliaseal.application.visible_signature_fit_policy import (
    apply_visible_signature_fit_gate,
    decide_visible_signature_fit,
)
from foliaseal.application.visible_signature_layout import (
    HorizontalInkMeasurement,
    HorizontalInkMeasurementRequest,
    RectBounds,
    SignatureLayoutPlan,
    TextMetrics,
    VisibleSignatureLayoutOptions,
    VisibleSignatureLayoutRequest,
    VisibleSignatureLayoutService,
    VisibleSignaturePreparation,
    _ensure_layout_can_fit,
    _horizontal_multi_line_rendered_layout_fits_reservation,
    _layout_reservation_for_template,
    _SignatureLayoutReservation,
    _single_line_rendered_ink_fits_reservation,
)
from foliaseal.application.visible_signature_semantics import (
    CertificateFieldValues,
    VisibleSignatureSemantics,
    VisibleSignatureSemanticsMode,
    VisibleSignatureSemanticsRequest,
    VisibleSignatureSemanticsService,
)
from foliaseal.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    TsaUnavailableError,
)
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureFieldKey,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningOutput,
    SigningRequest,
    SigningResult,
    TimestampTrustPolicy,
    VerificationSummary,
)
from foliaseal.infra.certification import inspect_pdf_certification_reader
from foliaseal.infra.tsa import build_http_timestamper, build_timestamp_validation_context

_PDF_VERSION_PATTERN = re.compile(rb"%PDF-(\d+\.\d+)")
detect_text_content_bounds_in_image = _text_raster_analysis.detect_text_content_bounds_in_image


def _next_signature_field_name(input_path: Path) -> str:
    """Choose the first unused ``SignatureN`` field for an incremental append."""
    with input_path.open("rb") as input_stream:
        reader = PdfFileReader(input_stream)
        existing_names = {
            str(field_name)
            for field_name, _field_value, _field_ref in fields.enumerate_sig_fields(reader)
        }
    index = 1
    while f"Signature{index}" in existing_names:
        index += 1
    return f"Signature{index}"


@dataclass(frozen=True)
class BackendReservationEvidence:
    """JSON-ready backend reservation evidence for a signing request."""

    snapshot: dict[str, Any] | None
    error: str | None


@dataclass(frozen=True)
class PreparedSigningPlan:
    """Application-owned preparation shared by signing and layout adapters."""

    backend_request: SigningBackendRequest
    visible_semantics: VisibleSignatureSemantics | None
    layout_plan: SignatureLayoutPlan | None
    layout_preparation: VisibleSignaturePreparation | None
    fit_issues: tuple[SigningDraftValidationIssue, ...]
    stamp_text: str
    visible: bool


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
            _fmt_pdf_number(border_width),
            b"w",
            _fmt_pdf_number(left + radius),
            _fmt_pdf_number(bottom),
            b"m",
            _fmt_pdf_number(right - radius),
            _fmt_pdf_number(bottom),
            b"l",
            _fmt_pdf_number(right - radius + control),
            _fmt_pdf_number(bottom),
            _fmt_pdf_number(right),
            _fmt_pdf_number(bottom + radius - control),
            _fmt_pdf_number(right),
            _fmt_pdf_number(bottom + radius),
            b"c",
            _fmt_pdf_number(right),
            _fmt_pdf_number(top - radius),
            b"l",
            _fmt_pdf_number(right),
            _fmt_pdf_number(top - radius + control),
            _fmt_pdf_number(right - radius + control),
            _fmt_pdf_number(top),
            _fmt_pdf_number(right - radius),
            _fmt_pdf_number(top),
            b"c",
            _fmt_pdf_number(left + radius),
            _fmt_pdf_number(top),
            b"l",
            _fmt_pdf_number(left + radius - control),
            _fmt_pdf_number(top),
            _fmt_pdf_number(left),
            _fmt_pdf_number(top - radius + control),
            _fmt_pdf_number(left),
            _fmt_pdf_number(top - radius),
            b"c",
            _fmt_pdf_number(left),
            _fmt_pdf_number(bottom + radius),
            b"l",
            _fmt_pdf_number(left),
            _fmt_pdf_number(bottom + radius - control),
            _fmt_pdf_number(left + radius - control),
            _fmt_pdf_number(bottom),
            _fmt_pdf_number(left + radius),
            _fmt_pdf_number(bottom),
            b"c",
            b"S",
        ]
    )


class RoundedBorderTextStamp(TextStamp):
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


@dataclass(frozen=True)
class _PyHankoSignerCertificateFieldReader:
    signer: SimpleSigner

    def read_fields(self, certificate_path: str, passphrase: str) -> CertificateFieldValues:
        del certificate_path, passphrase
        subject = self.signer.signing_cert.subject.native
        common_name = _subject_value(subject, "common_name")
        email = _subject_value(subject, "email_address")
        title = _subject_value(subject, "title") or _subject_value(
            subject, "organizational_unit_name"
        )
        company = _subject_value(subject, "organization_name")
        location = _derived_location(subject)
        distinguished_name = ", ".join(
            value
            for value in (
                common_name,
                email,
                title,
                company,
                location,
            )
            if value
        )
        return CertificateFieldValues(
            available=True,
            values={
                SignatureFieldKey.DISTINGUISHED_NAME: distinguished_name,
                SignatureFieldKey.COMMON_NAME: common_name or self.signer.subject_name,
                SignatureFieldKey.EMAIL: email or "",
                SignatureFieldKey.TITLE: title or "",
                SignatureFieldKey.COMPANY: company or "",
                SignatureFieldKey.REASON: "",
                SignatureFieldKey.LOCATION: location,
            },
        )


@dataclass(frozen=True)
class _FixedSigningClock:
    signing_time: datetime

    def now(self, mode: SignatureTimezoneDisplayMode) -> datetime:
        del mode
        return self.signing_time


@dataclass
class PyHankoPdfSigner:
    """Produce a genuinely signed PDF using pyHanko."""

    timestamper_factory: Callable[[str], object] | None = None

    def sign(
        self,
        request: SigningBackendRequest,
        *,
        prepared: PreparedSigningPlan | None = None,
    ) -> SigningOutput:
        input_path = Path(request.input_pdf_path)
        if not input_path.exists():
            raise FileNotFoundError(request.input_pdf_path)
        prepared = prepared or prepare_phase3_signing_plan(request)
        signature_field_name = _next_signature_field_name(input_path)
        signer = _load_simple_signer(request.certificate_path, request.passphrase)
        if any(
            issue.severity == SigningDraftValidationSeverity.ERROR for issue in prepared.fit_issues
        ):
            raise ValueError("; ".join(issue.message for issue in prepared.fit_issues))

        timestamper = None
        if request.timestamp_required:
            timestamper = self._build_timestamper(request.tsa_url)
        semantics = prepared.visible_semantics
        stamp_style = None
        field_spec: fields.SigFieldSpec
        if prepared.visible:
            appearance = request.signature_appearance
            signature_rect = request.signature_rect
            if appearance is None or signature_rect is None or semantics is None:
                raise ValueError("A visible signature rectangle and appearance are required.")
            stamp_style = _build_stamp_style(
                appearance,
                stamp_text=prepared.stamp_text,
                stamp_background=stamp_background_for_path(appearance.image_stamp_path),
                signature_rect=signature_rect,
                layout_plan=prepared.layout_plan,
                preparation=prepared.layout_preparation,
            )
            field_spec = fields.SigFieldSpec(
                sig_field_name=signature_field_name,
                on_page=signature_rect.page_index,
                box=_rect_to_box(signature_rect),
                readable_field_name="Visible signature",
            )
        else:
            field_spec = fields.SigFieldSpec(
                sig_field_name=signature_field_name,
                box=None,
                readable_field_name="Invisible signature",
                invis_sig_settings=InvisSigSettings(
                    set_print_flag=False,
                    set_hidden_flag=True,
                ),
            )

        metadata = PdfSignatureMetadata(
            field_name=signature_field_name,
            md_algorithm="sha256",
            name=_signature_name_for_metadata(request, signer),
            reason=None if semantics is None else semantics.text.metadata_reason,
            location=None if semantics is None else semantics.text.metadata_location,
            contact_info=None if semantics is None else semantics.text.metadata_contact_info,
            subfilter=fields.SigSeedSubFilter.ADOBE_PKCS7_DETACHED,
        )

        with input_path.open("rb") as input_stream:
            writer = IncrementalPdfFileWriter(input_stream)
            signed_output = BytesIO()
            signer_engine = PdfSigner(
                metadata,
                signer,
                timestamper=timestamper,
                stamp_style=stamp_style,
                new_field_spec=field_spec,
            )
            try:
                signer_engine.sign_pdf(writer, output=signed_output)
            except TimestampRequestError as exc:
                raise TsaUnavailableError(str(exc)) from exc
        output_bytes = signed_output.getvalue()

        return SigningOutput(
            output_bytes=output_bytes,
            output_pdf_version=_read_pdf_version_from_bytes(output_bytes)
            or self._fallback_pdf_version(input_path),
            signature_subfilter="adbe.pkcs7.detached",
            timestamp_present=_signature_has_timestamp(output_bytes),
        )

    def _build_timestamper(self, tsa_url: str) -> object:
        factory = self.timestamper_factory
        timestamper = factory(tsa_url) if factory is not None else build_http_timestamper(tsa_url)
        if timestamper is None:
            raise TsaUnavailableError("Timestamping is required but no TSA timestamper was built.")
        return timestamper

    @staticmethod
    def _fallback_pdf_version(input_path: Path) -> str:
        with input_path.open("rb") as handle:
            header = handle.read(16)
        match = _PDF_VERSION_PATTERN.search(header)
        return match.group(1).decode("ascii") if match else "1.7"


class PyHankoSignatureVerifier:
    """Cryptographically validate the signed output PDF."""

    def verify(
        self,
        output_pdf_path: str,
        *,
        trust_policy: TimestampTrustPolicy | None = None,
    ) -> VerificationSummary:
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
            timestamp_validation_context = build_timestamp_validation_context(trust_policy)
            status = validation.validate_pdf_signature(
                signature,
                signer_validation_context=validation_context,
                ts_validation_context=timestamp_validation_context,
            )
            certification = inspect_pdf_certification_reader(reader)

        if not status.intact or not status.valid:
            raise ValueError("The signed PDF failed cryptographic validation.")

        timestamp_validity = getattr(status, "timestamp_validity", None)
        timestamp_cryptographically_valid = None
        tsa_chain_trusted = None
        timestamp_validation_error = None
        if trust_policy is not None and timestamp_validity is not None:
            timestamp_cryptographically_valid = bool(
                getattr(timestamp_validity, "intact", True)
                and getattr(timestamp_validity, "valid", True)
            )
            tsa_chain_trusted = bool(getattr(timestamp_validity, "trusted", False))
            if not tsa_chain_trusted:
                describe_timestamp_trust = getattr(
                    timestamp_validity,
                    "describe_timestamp_trust",
                    None,
                )
                if callable(describe_timestamp_trust):
                    try:
                        timestamp_validation_error = describe_timestamp_trust()
                    except Exception:
                        timestamp_validation_error = None
                if timestamp_validation_error is None:
                    timestamp_validation_error = (
                        "The timestamp token is not trusted under the configured anchors."
                    )

        return VerificationSummary(
            signature_count=len(embedded_signatures),
            timestamp_present=_status_has_timestamp(status),
            timestamp_cryptographically_valid=timestamp_cryptographically_valid,
            tsa_chain_trusted=tsa_chain_trusted,
            timestamp_validation_error=timestamp_validation_error,
            docmdp_permission=certification.docmdp_permission,
            certification_restricted=certification.certification_restricted,
            restriction_reason=certification.restriction_reason,
        )


@dataclass(frozen=True)
class Phase3SigningExecutor:
    """Concrete executor used by the Phase 3 shell and harness."""

    use_case: SignPdfUseCase

    def execute(self, request: SigningRequest) -> SigningResult:
        return self.use_case.execute(request)


def build_phase3_signing_executor(
    *,
    timestamper_factory: Callable[[str], object] | None = None,
    render_port: PreviewRasterRenderer | None = None,
) -> Phase3SigningExecutor:
    """Build the concrete signing executor used by the Phase 3 shell."""
    use_case = SignPdfUseCase(
        inspector=PyHankoPdfInspector(),
        certificate_loader=PyHankoCertificateLoader(),
        signer=PyHankoPdfSigner(timestamper_factory=timestamper_factory),
        verifier=PyHankoSignatureVerifier(),
        preview_render_port=render_port,
    )
    return Phase3SigningExecutor(use_case=use_case)


@dataclass(frozen=True)
class _BackendLayoutPreparation:
    preparation: VisibleSignaturePreparation
    fit_issues: tuple[SigningDraftValidationIssue, ...]


def _prepare_backend_layout(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
    stamp_background: PdfImage | None,
    render_port: PreviewRasterRenderer | None = None,
) -> _BackendLayoutPreparation:
    """Prepare and fit-gate one canonical backend layout for all visible callers."""

    preparation = VisibleSignatureLayoutService.production().prepare(
        VisibleSignatureLayoutRequest(
            appearance=signature_appearance,
            signature_rect=signature_rect,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
            ink_measurer=_BackendHorizontalInkMeasurer(signature_appearance, render_port),
        )
    )
    fit_issues = _layout_fit_issues(
        layout_plan=preparation.layout_plan,
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
        stamp_text=stamp_text,
        render_port=render_port,
    )
    return _BackendLayoutPreparation(
        preparation=apply_visible_signature_fit_gate(
            preparation,
            decide_visible_signature_fit(fit_issues),
        ),
        fit_issues=fit_issues,
    )


def prepare_phase3_signing_plan(
    request: SigningBackendRequest,
) -> PreparedSigningPlan:
    """Resolve visible semantics and layout once for the signing adapters."""

    if request.signature_rect is None and request.signature_appearance is None:
        return PreparedSigningPlan(
            backend_request=request,
            visible_semantics=None,
            layout_plan=None,
            layout_preparation=None,
            fit_issues=(),
            stamp_text="",
            visible=False,
        )
    appearance = request.signature_appearance
    signature_rect = request.signature_rect
    if appearance is None or signature_rect is None:
        raise ValueError("A visible signature rectangle and appearance are required.")

    signer = _load_simple_signer(request.certificate_path, request.passphrase)
    signing_time = request.signing_time or _current_signing_time(appearance.timezone_display_mode)
    semantics = _resolve_visible_signature_semantics(
        certificate_path=request.certificate_path,
        passphrase=request.passphrase,
        appearance=appearance,
        signer=signer,
        signing_time=signing_time,
        signature_rect=signature_rect,
    )
    stamp_text = semantics.text.stamp_text
    layout_result = _prepare_backend_layout(
        signature_rect=signature_rect,
        signature_appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=stamp_background_for_path(appearance.image_stamp_path),
        render_port=request.render_port,
    )
    return PreparedSigningPlan(
        backend_request=request,
        visible_semantics=semantics,
        layout_plan=layout_result.preparation.layout_plan,
        layout_preparation=layout_result.preparation,
        fit_issues=layout_result.fit_issues,
        stamp_text=stamp_text,
        visible=True,
    )


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
    layout_plan: SignatureLayoutPlan,
    preparation: VisibleSignaturePreparation,
) -> TextStampStyle:
    if preparation.layout_plan is not layout_plan:
        raise ValueError("The stamp style must consume the prepared layout plan.")
    if not preparation.fit_gate_passed:
        raise ValueError(preparation.fit_gate_error or "Visible signature layout does not fit.")

    return preparation.signing().stamp_style


def _layout_fit_issues(
    *,
    layout_plan: SignatureLayoutPlan,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
    render_port: PreviewRasterRenderer | None = None,
) -> tuple[SigningDraftValidationIssue, ...]:
    """Apply the existing rendered-ink fallback ladder to one prepared plan."""

    if not layout_plan.fit_issues:
        return ()
    if _single_line_rendered_ink_fits_reservation(
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
        stamp_text=stamp_text,
        render_port=render_port,
    ) or _horizontal_multi_line_rendered_layout_fits_reservation(
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
        stamp_text=stamp_text,
        layout_plan=layout_plan,
        render_port=render_port,
    ):
        return ()
    return tuple(
        SigningDraftValidationIssue(
            code=issue.code,
            message=issue.message,
            field_name=issue.field_name,
            severity=issue.severity,
        )
        for issue in layout_plan.fit_issues
    )


@dataclass(frozen=True)
class _BackendHorizontalInkMeasurer:
    """Adapter from backend stamp text inputs to the layout engine ink port."""

    signature_appearance: SigningBackendAppearance
    render_port: PreviewRasterRenderer | None = None

    def measure(
        self,
        request: HorizontalInkMeasurementRequest,
    ) -> HorizontalInkMeasurement | None:
        reference = measure_horizontal_single_line_rendered_reference(
            _signing_draft_preview_for_stamp_text(
                signature_rect=request.signature_rect,
                signature_appearance=self.signature_appearance,
                stamp_text=request.stamp_text,
            ),
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


def _build_text_box_style_impl(text_style: SignatureTextStyle) -> TextBoxStyle:
    # Preserve the user's selected half-point font sizes in backend measurement.
    # Rounding 8.5pt up to 9pt creates avoidable preview/backend drift in narrow
    # layouts because the Qt preview renders the actual selected size.
    font_size = max(Fraction(1, 1), Fraction(int(round(text_style.font_size_pt * 2)), 2))
    font_factory = _font_factory_for_text_style(text_style, font_size=font_size)
    return TextBoxStyle(
        font=font_factory,
        font_size=font_size,
        text_color=_hex_to_rgb(text_style.text_color_hex),
        box_layout_rule=SimpleBoxLayoutRule(
            AxisAlignment.ALIGN_MIN,
            AxisAlignment.ALIGN_MAX,
            margins=Margins.uniform(0),
            inner_content_scaling=InnerScaling.NO_SCALING,
        ),
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


def _single_line_no_stamp_vertical_optical_shift(
    *,
    available_height: int,
    text_box_height: int,
    outer_margin: int,
) -> int:
    """Shift no-stamp single-line text upward within the reserved box.

    The full signature box already belongs to text in this path, but the
    rendered glyph ink sits low relative to the nominal text-box metrics.
    Bound the correction by the existing outer inset so we improve visual
    centering without inventing a new tolerance regime.
    """

    free_height = max(0, available_height - text_box_height)
    return min(free_height, max(0, outer_margin))


def _top_stamp_border_facing_inset(
    *,
    box_style: SignatureBoxStyle | None,
) -> int:
    """Reserve real top clearance for non-single-line top stamp content."""

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


def _horizontal_single_line_ink_reservation_for_stamp_text(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
    structural_reservation: _SignatureLayoutReservation,
    has_visible_stamp_image: bool,
) -> HorizontalSingleLineInkReservation | None:
    if (
        not has_visible_stamp_image
        or signature_appearance.layout_template != SignatureLayoutTemplate.SINGLE_LINE
        or signature_appearance.stamp_position
        not in {SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT}
    ):
        return None

    reference = measure_horizontal_single_line_rendered_reference(
        _signing_draft_preview_for_stamp_text(
            signature_rect=signature_rect,
            signature_appearance=signature_appearance,
            stamp_text=stamp_text,
        ),
        zoom=1.0,
    )
    if reference is None:
        return None

    edge_margin = _effective_layout_edge_margin(
        stamp_position=signature_appearance.stamp_position,
        box_height=structural_reservation.container_height_pt,
        box_style=signature_appearance.box_style,
    )
    return build_horizontal_single_line_ink_reservation(
        layout_template=signature_appearance.layout_template,
        stamp_position=signature_appearance.stamp_position,
        has_visible_stamp_image=has_visible_stamp_image,
        structural_text_box_width_pt=structural_reservation.text_box_width_pt,
        structural_text_box_height_pt=structural_reservation.text_box_height_pt,
        structural_text_bounds_px=reference.structural_text_bounds_px,
        rendered_ink_bounds_px=reference.rendered_ink_bounds_px,
        px_to_pt=reference.px_to_pt,
        border_facing_padding_pt=edge_margin,
        stamp_facing_padding_pt=edge_margin,
    )


def _visible_signature_fit_issues(
    *,
    certificate_path: str,
    passphrase: str,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    signer: SimpleSigner | None = None,
    signing_time: datetime | None = None,
    semantics: VisibleSignatureSemantics | None = None,
) -> tuple[SigningDraftValidationIssue, ...]:
    """Return backend-side layout fit issues for the requested visible signature."""
    try:
        resolved_signer = signer or _load_simple_signer(certificate_path, passphrase)
        resolved_signing_time = signing_time or _current_signing_time(
            signature_appearance.timezone_display_mode
        )
        resolved_semantics = semantics or _resolve_visible_signature_semantics(
            certificate_path=certificate_path,
            passphrase=passphrase,
            appearance=signature_appearance,
            signer=resolved_signer,
            signing_time=resolved_signing_time,
            signature_rect=signature_rect,
        )
        stamp_background = stamp_background_for_path(signature_appearance.image_stamp_path)
        return _visible_signature_fit_issues_for_stamp_text(
            signature_rect=signature_rect,
            signature_appearance=signature_appearance,
            stamp_text=resolved_semantics.text.stamp_text,
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
    """Compatibility wrapper for public visible-signature fit validation."""

    return validate_visible_signature_fit(
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
        stamp_text=stamp_text,
        stamp_background=stamp_background,
    )


def validate_visible_signature_fit(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
    stamp_background: PdfImage | None,
    render_port: PreviewRasterRenderer | None = None,
) -> tuple[SigningDraftValidationIssue, ...]:
    try:
        layout_result = _prepare_backend_layout(
            signature_rect=signature_rect,
            signature_appearance=signature_appearance,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            render_port=render_port,
        )
        _build_stamp_style(
            signature_appearance,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            signature_rect=signature_rect,
            preparation=layout_result.preparation,
            layout_plan=layout_result.preparation.layout_plan,
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


def _signing_draft_preview_for_stamp_text(
    *,
    signature_rect: SignatureRect,
    signature_appearance: SigningBackendAppearance,
    stamp_text: str,
) -> SigningDraftPreview:
    return signing_draft_preview_for_stamp_text(
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
        stamp_text=stamp_text,
    )


def _stamp_text_preview_parts(
    stamp_text: str,
    *,
    signature_appearance: SigningBackendAppearance,
) -> tuple[str, str]:
    return stamp_text_preview_parts(
        stamp_text,
        signature_appearance=signature_appearance,
    )


def _text_style_color_rgba(text_style: SignatureTextStyle) -> tuple[int, int, int, int] | None:
    return text_style_color_rgba(text_style)


def _build_stamp_text(
    *,
    appearance: SigningBackendAppearance,
    signer: SimpleSigner,
    signing_time: datetime,
    signature_rect: SignatureRect | None = None,
) -> str:
    semantics = _resolve_visible_signature_semantics(
        certificate_path="",
        passphrase="",
        appearance=appearance,
        signer=signer,
        signing_time=signing_time,
        signature_rect=signature_rect,
    )
    return semantics.text.stamp_text


def _resolve_visible_signature_semantics(
    *,
    certificate_path: str,
    passphrase: str,
    appearance: SigningBackendAppearance,
    signer: SimpleSigner,
    signing_time: datetime,
    signature_rect: SignatureRect | None = None,
) -> VisibleSignatureSemantics:
    service = VisibleSignatureSemanticsService(
        certificate_reader=_PyHankoSignerCertificateFieldReader(signer),
        clock=_FixedSigningClock(signing_time),
    )
    return service.resolve(
        VisibleSignatureSemanticsRequest(
            certificate_path=certificate_path,
            passphrase=passphrase,
            signature_rect=signature_rect,
            appearance=appearance,
            mode=VisibleSignatureSemanticsMode.FINAL_SIGNING,
        )
    )


def _single_line_text_fits_reservation(
    *,
    appearance: SigningBackendAppearance,
    signature_rect: SignatureRect,
    text: str,
    text_box_engine: SignatureTextBoxEngine | None = None,
) -> bool:
    prepared_text = (text_box_engine or PyHankoSignatureTextBoxEngine()).prepare(
        text,
        appearance.text_style,
    )
    text_box_width = prepared_text.metrics.width_pt
    text_box_height = prepared_text.metrics.height_pt
    reservation = _layout_reservation_for_template(
        appearance.layout_template,
        stamp_position=appearance.stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=appearance.box_style,
        has_visible_stamp_image=appearance.image_stamp_path is not None,
        stamp_aspect_ratio=_stamp_image_aspect_ratio(
            stamp_background_for_path(appearance.image_stamp_path)
            if appearance.image_stamp_path is not None
            else None
        ),
    )
    try:
        _ensure_layout_can_fit(
            reservation,
            has_visible_stamp_image=appearance.image_stamp_path is not None,
        )
    except ValueError:
        return False
    return True


def _effective_horizontal_text_reservation_width(
    *,
    layout_template: SignatureLayoutTemplate,
    stamp_position: SignatureStampPosition,
    text_box_width: int,
) -> int:
    del stamp_position
    if layout_template != SignatureLayoutTemplate.SINGLE_LINE:
        return text_box_width
    return text_box_width


@dataclass(frozen=True)
class PyHankoSignatureTextBoxEngine:
    """Production adapter for atomic PyHanko text style and metric preparation."""

    def prepare(self, text: str, text_style: SignatureTextStyle) -> PreparedTextBox:
        text_box_style = _build_text_box_style_impl(text_style)
        width_pt, height_pt = _measure_text_box_dimensions_impl(text, text_box_style)
        return PreparedTextBox(
            metrics=TextMetrics(
                width_pt=width_pt,
                height_pt=height_pt,
                line_count=max(1, text.count("\n") + 1),
            ),
            render_style=text_box_style,
        )


def stamp_background_for_path(image_stamp_path: str | None) -> PdfImage | None:
    """Load one optional image stamp for a concrete rendering adapter."""
    return _neutral_stamp_background_for_path(image_stamp_path)


def _solid_background_for_color(color_hex: str) -> PdfImage:
    red, green, blue = (int(component * 255) for component in _hex_to_rgb(color_hex))
    image = Image.new("RGB", (16, 16), color=(red, green, blue))
    return PdfImage(image, writer=None)


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
    from foliaseal.application.visible_signature_layout_adapters import (
        pyhanko_layout_rule_from_spec,
    )

    return pyhanko_layout_rule_from_spec(
        _layout_reservation_for_template(
            layout_template,
            stamp_position=stamp_position,
            signature_rect=signature_rect,
            text_box_width=text_box_width,
            text_box_height=text_box_height,
            box_style=box_style,
            has_visible_stamp_image=stamp_background is not None,
            stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
        ).inner_content_layout
    )


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
    from foliaseal.application.visible_signature_layout_adapters import (
        pyhanko_layout_rule_from_spec,
    )

    return pyhanko_layout_rule_from_spec(
        _layout_reservation_for_template(
            layout_template,
            stamp_position=stamp_position,
            signature_rect=signature_rect,
            text_box_width=text_box_width,
            text_box_height=text_box_height,
            box_style=box_style,
            has_visible_stamp_image=stamp_background is not None,
            stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
        ).background_layout
    )


def _measure_text_box_dimensions_impl(
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
    measured_width = int(round(text_box.box.width))
    measured_height = int(round(text_box.box.height))
    line_count = max(1, stamp_text.count("\n") + 1)
    nominal_line_height = float(text_box_style.font_size)
    minimum_height = int(ceil(line_count * nominal_line_height))
    if line_count > 1:
        # Reserve one extra point for stacked-text descenders. This is a
        # measurement correction for the backend's line-box model, not a fit
        # tolerance: Qt/PDF rasterization consistently needs a touch more
        # vertical room than the nominal per-line font size alone captures.
        minimum_height += 1
    return measured_width, max(measured_height, minimum_height)


def _build_text_box_style(text_style: SignatureTextStyle) -> TextBoxStyle:
    """Compatibility wrapper for the public text-box engine."""

    return _build_text_box_style_impl(text_style)


def _measure_text_box_dimensions(
    stamp_text: str,
    text_box_style: TextBoxStyle,
) -> tuple[int, int]:
    """Compatibility wrapper for the public text-box engine."""

    return _measure_text_box_dimensions_impl(stamp_text, text_box_style)


def _reserved_space(container_length: int, content_length: int, gap: int) -> int:
    desired = content_length + gap + 4
    upper_bound = max(container_length - 4, 0)
    return max(0, min(desired, upper_bound))


def _signature_name_for_metadata(
    request: SigningBackendRequest,
    signer: SimpleSigner,
) -> str:
    if request.certificate_alias:
        return request.certificate_alias
    return signer.subject_name


def _current_signing_time(timezone_mode: SignatureTimezoneDisplayMode) -> datetime:
    timestamp = datetime.now(UTC)
    if timezone_mode is SignatureTimezoneDisplayMode.LOCAL:
        timestamp = timestamp.astimezone()
    return timestamp


def _layout_value_name(value: object) -> str | None:
    if value is None:
        return None
    return str(getattr(value, "name", value)).lower()


def _snapshot_layout_rule(layout_rule: object | None) -> dict[str, Any] | None:
    if layout_rule is None:
        return None
    margins = getattr(layout_rule, "margins", None)
    return {
        "x_align": _layout_value_name(getattr(layout_rule, "x_align", None)),
        "y_align": _layout_value_name(getattr(layout_rule, "y_align", None)),
        "inner_content_scaling": _layout_value_name(
            getattr(
                layout_rule,
                "inner_content_scaling",
                getattr(layout_rule, "scaling", None),
            )
        ),
        "margins": None
        if margins is None
        else {
            "left": margins.left,
            "right": margins.right,
            "top": margins.top,
            "bottom": margins.bottom,
        },
    }


def build_backend_reservation_evidence(
    request: SigningRequest | None,
) -> BackendReservationEvidence | None:
    """Build backend reservation snapshot/error evidence for UI and harness callers."""

    if request is None or request.signature_rect is None or request.signature_appearance is None:
        return None

    appearance = SigningBackendAppearance.from_signature_appearance(request.signature_appearance)
    snapshot: dict[str, Any] = {
        "layout_template": appearance.layout_template.value,
        "stamp_position": appearance.stamp_position.value,
        "signature_rect": {
            "page_index": request.signature_rect.page_index,
            "page_number": request.signature_rect.page_index + 1,
            "left_pt": request.signature_rect.left_pt,
            "bottom_pt": request.signature_rect.bottom_pt,
            "width_pt": request.signature_rect.width_pt,
            "height_pt": request.signature_rect.height_pt,
        },
        "error": None,
    }

    try:
        prepared = prepare_phase3_signing_plan(SigningBackendRequest.from_signing_request(request))
        layout_preparation = prepared.layout_preparation
        if layout_preparation is None:
            raise ValueError("Visible signature preparation is unavailable.")
        stamp_text = prepared.stamp_text
        stamp_background = stamp_background_for_path(appearance.image_stamp_path)
        layout_plan = layout_preparation.layout_plan
        text_box_width = layout_plan.text_box.width_pt
        text_box_height = layout_plan.text_box.height_pt
        fit_gate_width_limit = layout_plan.text_area_width_pt + 1
        fit_gate_height_limit = layout_plan.text_area_height_pt
        fit_gate_passed = layout_preparation.fit_gate_passed
        if not fit_gate_passed:
            snapshot["error"] = layout_preparation.fit_gate_error
        from foliaseal.application.visible_signature_layout_adapters import (
            materialize_background_layout,
        )

        background_layout = materialize_background_layout(
            layout_template=appearance.layout_template,
            stamp_position=appearance.stamp_position,
            stamp_background=stamp_background,
            signature_rect=request.signature_rect,
            text_box_width=layout_plan.background_text_box_width_pt,
            text_box_height=layout_plan.text_box.height_pt,
            box_style=appearance.box_style,
            stamp_aspect_ratio=(
                None if layout_plan.stamp_image is None else layout_plan.stamp_image.aspect_ratio
            ),
        )
        snapshot.update(
            {
                "stamp_text": stamp_text,
                "stamp_text_length": len(stamp_text),
                "stamp_text_line_count": len(stamp_text.splitlines()) if stamp_text else 0,
                "stamp_background_present": stamp_background is not None,
                "measured_text_box_width_pt": text_box_width,
                "measured_text_box_height_pt": text_box_height,
                "reserved_primary_extent_pt": layout_plan.reserved_primary_extent_pt,
                "stamp_area_width_pt": layout_plan.stamp_area_width_pt,
                "stamp_area_height_pt": layout_plan.stamp_area_height_pt,
                "text_area_width_pt": layout_plan.text_area_width_pt,
                "text_area_height_pt": layout_plan.text_area_height_pt,
                "fit_gate_width_limit_pt": fit_gate_width_limit,
                "fit_gate_height_limit_pt": fit_gate_height_limit,
                "fit_gate_passed": fit_gate_passed,
                "text_style": {
                    "font_family": appearance.text_style.font_family,
                    "font_size_pt": appearance.text_style.font_size_pt,
                    "bold": appearance.text_style.bold,
                    "italic": appearance.text_style.italic,
                    "text_color_hex": appearance.text_style.text_color_hex,
                },
                "box_style": {
                    "border_color_hex": appearance.box_style.border_color_hex,
                    "border_width_pt": appearance.box_style.border_width_pt,
                    "background_color_hex": appearance.box_style.background_color_hex,
                }
                if appearance.box_style is not None
                else None,
                "background_layout": _snapshot_layout_rule(background_layout),
                "content_layout": _snapshot_layout_rule(layout_plan.text_layout),
                "neutral_plan": layout_preparation.reservation_snapshot,
            }
        )
    except Exception as exc:
        snapshot["error"] = str(exc)
        return BackendReservationEvidence(snapshot=snapshot, error=str(exc))

    if not layout_preparation.fit_gate_passed:
        return BackendReservationEvidence(
            snapshot=snapshot,
            error=layout_preparation.fit_gate_error,
        )
    return BackendReservationEvidence(snapshot=snapshot, error=None)


def _rect_to_box(signature_rect) -> tuple[int, int, int, int]:
    left = int(round(signature_rect.left_pt))
    bottom = int(round(signature_rect.bottom_pt))
    right = int(round(signature_rect.left_pt + signature_rect.width_pt))
    top = int(round(signature_rect.bottom_pt + signature_rect.height_pt))
    return (left, bottom, right, top)


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


def _font_factory_for_family(
    font_family: str,
    *,
    bold: bool = False,
    italic: bool = False,
    font_size: Fraction,
) -> GlyphAccumulatorFactory:
    face = resolve_signature_font_face(font_family, bold=bold, italic=italic)
    return GlyphAccumulatorFactory(
        font_file=str(face.font_file),
        font_size=float(font_size),
    )


def _hex_to_rgb(color_hex: str) -> tuple[float, float, float]:
    normalized = color_hex.strip().lstrip("#")
    return tuple(int(normalized[index : index + 2], 16) / 255.0 for index in (0, 2, 4))  # type: ignore[return-value]


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
        getattr(timestamp_validity, "intact", True) and getattr(timestamp_validity, "valid", True)
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
