"""Concrete Phase 3 signing executor wiring."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from asn1crypto import pkcs12
from PIL import Image
from pyhanko.pdf_utils.font.basic import SimpleFontEngineFactory
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.layout import AxisAlignment, SimpleBoxLayoutRule
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.text import TextBoxStyle
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
from foliaseal.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    TsaUnavailableError,
)
from foliaseal.domain.models import (
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
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

        signer = _load_simple_signer(request.certificate_path, request.passphrase)
        signing_time = _current_signing_time(appearance.timezone_display_mode)
        stamp_text = _build_stamp_text(
            appearance=appearance,
            signer=signer,
            signing_time=signing_time,
        )
        stamp_style = _build_stamp_style(
            appearance,
            stamp_text=stamp_text,
            stamp_background=_stamp_background_for_path(appearance.image_stamp_path),
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
) -> TextStampStyle:
    text_style = appearance.text_style
    box_style = appearance.box_style
    font_factory = _font_factory_for_family(text_style.font_family)
    border_width = max(0, int(round(box_style.border_width_pt))) if box_style.show_border else 0
    text_color = _hex_to_rgb(text_style.text_color_hex)
    border_color = _hex_to_rgb(box_style.border_color_hex)
    background = stamp_background or _solid_background_for_color(box_style.background_color_hex)
    return TextStampStyle(
        border_width=border_width,
        border_color=border_color,
        background=background,
        background_opacity=1.0,
        text_box_style=TextBoxStyle(
            font=font_factory,
            font_size=max(1, int(round(text_style.font_size_pt))),
            text_color=text_color,
        ),
        inner_content_layout=SimpleBoxLayoutRule(
            AxisAlignment.ALIGN_MID,
            AxisAlignment.ALIGN_MID,
        ),
        stamp_text=stamp_text,
        timestamp_format=appearance.datetime_format,
    )


def _build_stamp_text(
    *,
    appearance: SigningBackendAppearance,
    signer: SimpleSigner,
    signing_time: datetime,
) -> str:
    lines: list[str] = []
    prefix = appearance.signer_label_prefix.strip()
    if prefix:
        lines.append(prefix)

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
            lines.append(f"{_field_label(field_key)}: {text}")
        else:
            lines.append(text)

    if appearance.layout_template == SignatureLayoutTemplate.SINGLE_LINE:
        return _escape_percent(" | ".join(lines))
    return _escape_percent("\n".join(lines))


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
        return signer.signing_cert.subject.human_friendly
    if field_key == SignatureFieldKey.COMMON_NAME:
        return str(subject.get("common_name") or signer.subject_name)
    if field_key == SignatureFieldKey.EMAIL:
        return str(subject.get("email_address") or signer.subject_name)
    if field_key == SignatureFieldKey.TITLE:
        return str(
            subject.get("organizational_unit_name")
            or binding.display_label
            or signer.subject_name
        )
    if field_key == SignatureFieldKey.COMPANY:
        return str(
            subject.get("organization_name")
            or binding.display_label
            or signer.subject_name
        )
    if field_key == SignatureFieldKey.REASON:
        return str(binding.display_label or signer.subject_name)
    if field_key == SignatureFieldKey.LOCATION:
        location_parts = [
            str(part)
            for part in (
                subject.get("locality_name"),
                subject.get("state_or_province_name"),
                subject.get("country_name"),
            )
            if part
        ]
        if location_parts:
            return ", ".join(location_parts)
        return str(binding.display_label or signer.subject_name)
    return binding.display_label or _field_label(field_key)


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
