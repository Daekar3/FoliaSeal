import json
import re
from datetime import UTC, datetime, timedelta
from fractions import Fraction
from pathlib import Path

import pytest
from asn1crypto import keys as asn1_keys
from asn1crypto import x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from PIL import Image
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.font.opentype import GlyphAccumulatorFactory
from pyhanko.pdf_utils.layout import AxisAlignment, BoxConstraints, InnerScaling
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter
from pyhanko.sign import validation
from pyhanko.sign.timestamps.dummy_client import DummyTimeStamper
from pyhanko_certvalidator import ValidationContext
from pyhanko_certvalidator.registry import SimpleCertificateStore

from foliaseal.application import signing_preview_renderer as signing_preview_renderer_module
from foliaseal.application.horizontal_signature_reservation import (
    HorizontalSingleLineInkReservation,
    HorizontalSingleLineRenderedReference,
)
from foliaseal.application.phase3_signing_backend import (
    _SINGLE_LINE_RENDERED_INK_FIT_CACHE,
    PyHankoCertificateLoader,
    PyHankoPdfInspector,
    PyHankoPdfSigner,
    PyHankoSignatureVerifier,
    _background_layout_for_stamp,
    _build_stamp_style,
    _build_stamp_text,
    _build_text_box_style,
    _current_signing_time,
    _effective_horizontal_text_reservation_width,
    _horizontal_single_line_ink_validation_reservation,
    _layout_reservation_for_template,
    _load_simple_signer,
    _measure_text_box_dimensions,
    _resolve_visible_signature_semantics,
    _single_line_horizontal_stamp_vertical_inset,
    _single_line_rendered_ink_fits_reservation,
    _single_line_stamp_content_inset,
    _single_line_vertical_stamp_border_gap,
    _stamp_background_for_path,
    _visible_signature_fit_issues,
    _visible_signature_fit_issues_for_stamp_text,
    build_phase3_signing_executor,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance, SignPdfUseCase
from foliaseal.application.signing_draft_workflow import SigningDraftPreview
from foliaseal.domain.errors import CertificateLoadError, FailureCode
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    TimestampTrustPolicy,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_field_binding,
    build_signature_rect,
    build_signing_request,
)

_MANUAL_HORIZONTAL_SINGLE_LINE_REPLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "phase3_horizontal_single_line_manual_replay.json"
)


def _load_manual_horizontal_single_line_replay() -> dict:
    return json.loads(_MANUAL_HORIZONTAL_SINGLE_LINE_REPLAY_PATH.read_text())


def _replay_stamp_position(case: dict) -> SignatureStampPosition:
    if case.get("stamp_position") == "right":
        return SignatureStampPosition.RIGHT
    return SignatureStampPosition.LEFT


def _write_test_pdf(path: Path) -> None:
    writer = PdfFileWriter()
    empty_stream = writer.add_object(generic.StreamObject(stream_data=b""))
    writer.insert_page(PageObject(contents=empty_stream, media_box=(0, 0, 612, 792)))
    with path.open("wb") as handle:
        writer.write(handle)


def _write_test_pkcs12(
    path: Path,
    *,
    passphrase: str,
    common_name: str = "Test User",
) -> x509.Certificate:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.TITLE, "Board Secretary"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QA"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "test@example.com"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Wytheville"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Virginia"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    pfx = pkcs12.serialize_key_and_certificates(
        name=common_name.encode("utf-8"),
        key=key,
        cert=cert,
        cas=None,
        encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode("utf-8")),
    )
    path.write_bytes(pfx)
    return cert


def _write_test_stamp_image(path: Path) -> None:
    image = Image.new("RGB", (96, 48), color=(215, 235, 255))
    image.save(path, format="PNG")


def _build_dummy_timestamper() -> DummyTimeStamper:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "FoliaSeal TSA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    tsa_cert = asn1_x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))
    tsa_key = asn1_keys.PrivateKeyInfo.load(
        key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return DummyTimeStamper(
        tsa_cert=tsa_cert,
        tsa_key=tsa_key,
        fixed_dt=datetime(2024, 1, 1, tzinfo=UTC),
    )


def _build_ca_signed_dummy_timestamper(
    *,
    root_common_name: str = "FoliaSeal TSA Root",
    tsa_common_name: str = "FoliaSeal TSA",
) -> tuple[DummyTimeStamper, x509.Certificate]:
    root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    root_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, root_common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
    root_cert = (
        x509.CertificateBuilder()
        .subject_name(root_subject)
        .issuer_name(root_subject)
        .public_key(root_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(root_key, hashes.SHA256())
    )
    tsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    tsa_subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, tsa_common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
    tsa_cert = (
        x509.CertificateBuilder()
        .subject_name(tsa_subject)
        .issuer_name(root_subject)
        .public_key(tsa_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.TIME_STAMPING]),
            critical=False,
        )
        .sign(root_key, hashes.SHA256())
    )
    tsa_cert_asn1 = asn1_x509.Certificate.load(tsa_cert.public_bytes(serialization.Encoding.DER))
    tsa_key_asn1 = asn1_keys.PrivateKeyInfo.load(
        tsa_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    root_cert_asn1 = asn1_x509.Certificate.load(root_cert.public_bytes(serialization.Encoding.DER))
    return (
        DummyTimeStamper(
            tsa_cert=tsa_cert_asn1,
            tsa_key=tsa_key_asn1,
            certs_to_embed=SimpleCertificateStore.from_certs([root_cert_asn1]),
            fixed_dt=datetime(2024, 1, 1, tzinfo=UTC),
        ),
        root_cert,
    )


def _signature_appearance_stream_text(pdf_path: Path) -> str:
    with pdf_path.open("rb") as handle:
        reader = PdfFileReader(handle)
        embedded_signatures = list(reader.embedded_signatures)
        assert embedded_signatures
        appearance_stream = embedded_signatures[-1].sig_field["/AP"]["/N"].get_object()
        return appearance_stream.data.decode("latin1", errors="replace")


def _signature_background_scale(pdf_path: Path) -> tuple[float, float]:
    stream_text = _signature_appearance_stream_text(pdf_path)
    match = re.search(
        r"/BackgroundGS gs\s+([-\d.]+)\s+0\s+0\s+([-\d.]+)\s+[-\d.]+\s+[-\d.]+\s+cm",
        stream_text,
    )
    assert match is not None, stream_text
    return float(match.group(1)), float(match.group(2))


def test_phase3_signing_executor_produces_signed_pdf_and_validates(tmp_path: Path) -> None:
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        show_field_names=True,
    )

    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=0, width_pt=620.0, height_pt=180.0),
        signature_appearance=appearance,
    )

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is True
    assert result.failure_code is None
    assert output_pdf.exists()
    assert output_pdf.read_bytes() != input_pdf.read_bytes()
    assert result.output_pdf_version == "1.7"
    assert result.signature_subfilter == "adbe.pkcs7.detached"
    assert result.timestamp_present is False

    appearance_text = _signature_appearance_stream_text(output_pdf)
    assert "Test User" in appearance_text
    assert "Board Secretary" in appearance_text
    assert "FoliaSeal" in appearance_text
    assert "Visible signature" not in appearance_text

    with output_pdf.open("rb") as handle:
        reader = PdfFileReader(handle)
        embedded_signatures = list(reader.embedded_signatures)
        assert len(embedded_signatures) == 1
        status = validation.validate_pdf_signature(
            embedded_signatures[0],
            signer_validation_context=ValidationContext(
                trust_roots=[embedded_signatures[0].signer_cert]
            ),
        )
        assert status.intact is True
        assert status.valid is True
        assert getattr(status, "timestamp_validity", None) is None
        assert embedded_signatures[0].signer_cert.subject.native["common_name"] == "Test User"

    verifier = PyHankoSignatureVerifier()
    summary = verifier.verify(str(output_pdf))
    assert summary.signature_count == 1
    assert summary.timestamp_present is False


def test_phase3_signing_executor_produces_visible_signature_without_image_stamp(
    tmp_path: Path,
) -> None:
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    cert_path = tmp_path / "cert.p12"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")
    appearance = build_signature_appearance(
        image_stamp_path=None,
        show_field_names=True,
        signer_label_prefix="",
    )

    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
        signature_appearance=appearance,
    )

    result = build_phase3_signing_executor().execute(request)

    assert result.success is True
    assert result.failure_code is None
    assert output_pdf.exists()
    appearance_text = _signature_appearance_stream_text(output_pdf)
    assert "Test User" in appearance_text
    assert "Board Secretary" in appearance_text
    assert "FoliaSeal" in appearance_text
    assert appearance_text.strip()


def test_phase3_signing_executor_adds_timestamp_when_required_with_tsa(
    tmp_path: Path,
) -> None:
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    cert_path = tmp_path / "cert.p12"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")

    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=True,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
        signature_appearance=build_signature_appearance(
            image_stamp_path=None,
            show_field_names=True,
            signer_label_prefix="",
        ),
    )

    signer = PyHankoPdfSigner(timestamper_factory=lambda _request: _build_dummy_timestamper())
    use_case = SignPdfUseCase(
        inspector=PyHankoPdfInspector(),
        certificate_loader=PyHankoCertificateLoader(),
        signer=signer,
        verifier=PyHankoSignatureVerifier(),
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.failure_code is None
    assert output_pdf.exists()
    assert result.timestamp_present is True
    assert signer is not None
    with output_pdf.open("rb") as handle:
        reader = PdfFileReader(handle)
        embedded_signatures = list(reader.embedded_signatures)
        assert len(embedded_signatures) == 1
        status = validation.validate_pdf_signature(
            embedded_signatures[0],
            signer_validation_context=ValidationContext(
                trust_roots=[embedded_signatures[0].signer_cert]
            ),
        )
        assert getattr(status, "timestamp_validity", None) is not None


def test_phase3_signing_executor_reports_trusted_timestamp_when_anchors_are_configured(
    tmp_path: Path,
) -> None:
    _write_test_pdf(tmp_path / "input.pdf")
    _write_test_pkcs12(tmp_path / "cert.p12", passphrase="secret")
    timestamper, root_cert = _build_ca_signed_dummy_timestamper()
    root_bundle = tmp_path / "tsa-root.pem"
    root_bundle.write_bytes(root_cert.public_bytes(serialization.Encoding.PEM))

    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=True,
        trust_policy=TimestampTrustPolicy(
            use_system_store=False,
            extra_ca_bundle_path=str(root_bundle),
            revocation_mode="soft-fail",
        ),
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
        signature_appearance=build_signature_appearance(
            image_stamp_path=None,
            show_field_names=True,
            signer_label_prefix="",
        ),
    )

    use_case = SignPdfUseCase(
        inspector=PyHankoPdfInspector(),
        certificate_loader=PyHankoCertificateLoader(),
        signer=PyHankoPdfSigner(timestamper_factory=lambda _request: timestamper),
        verifier=PyHankoSignatureVerifier(),
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.timestamp_present is True
    assert result.timestamp_cryptographically_valid is True
    assert result.tsa_chain_trusted is True
    assert result.timestamp_validation_error is None


def test_single_line_stamp_content_inset_is_orientation_aware() -> None:
    assert (
        _single_line_stamp_content_inset(
            stamp_position=SignatureStampPosition.TOP,
            box_width=260,
            box_height=24,
        )
        == 1
    )
    assert (
        _single_line_stamp_content_inset(
            stamp_position=SignatureStampPosition.LEFT,
            box_width=300,
            box_height=26,
        )
        == 1
    )
    assert (
        _single_line_stamp_content_inset(
            stamp_position=SignatureStampPosition.RIGHT,
            box_width=210,
            box_height=42,
        )
        == 1
    )


def test_single_line_stamp_content_inset_scales_to_reserved_band() -> None:
    assert (
        _single_line_stamp_content_inset(
            stamp_position=SignatureStampPosition.TOP,
            box_width=260,
            box_height=23,
            reserved_width=257,
            reserved_height=8,
        )
        == 0
    )


def test_single_line_vertical_stamp_border_gap_tracks_border_visibility() -> None:
    assert (
        _single_line_vertical_stamp_border_gap(
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            )
        )
        == 1
    )
    assert (
        _single_line_vertical_stamp_border_gap(
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=3.5,
                background_color_hex="#FFFFFF",
            )
        )
        == 2
    )
    assert _single_line_vertical_stamp_border_gap(box_style=None) == 0


def test_single_line_horizontal_stamp_vertical_inset_uses_border_safe_spacing() -> None:
    assert (
        _single_line_horizontal_stamp_vertical_inset(
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
            content_inset=1,
        )
        == 2
    )
    assert (
        _single_line_horizontal_stamp_vertical_inset(
            box_style=SignatureBoxStyle(
                show_border=False,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
            content_inset=1,
        )
        == 1
    )


def test_background_layout_for_top_multi_line_stamp_adds_border_facing_inset(
) -> None:
    stamp_path = Path("/tmp/test-top-stamp-inset.png")
    Image.new("RGBA", (40, 12), color=(0, 0, 0, 255)).save(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))
    signature_rect = build_signature_rect(page_index=0, width_pt=260.0, height_pt=46.0)
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.TOP,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=24,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        has_visible_stamp_image=True,
        stamp_aspect_ratio=40 / 12,
    )

    background_layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.TOP,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=24,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )

    assert background_layout.margins.top > reservation.background_layout.margins.top


def test_background_layout_for_bottom_wrapped_block_stamp_adds_border_facing_inset(
) -> None:
    stamp_path = Path("/tmp/test-bottom-stamp-inset.png")
    Image.new("RGBA", (12, 40), color=(0, 0, 0, 255)).save(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))
    signature_rect = build_signature_rect(page_index=0, width_pt=260.0, height_pt=54.0)
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.BOTTOM,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=24,
        box_style=box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=12 / 40,
    )

    background_layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.BOTTOM,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=24,
        box_style=box_style,
    )

    assert background_layout.margins.bottom > reservation.background_layout.margins.bottom


def test_background_layout_for_right_wrapped_block_stamp_adds_border_facing_inset(
) -> None:
    stamp_path = Path("/tmp/test-right-stamp-inset.png")
    Image.new("RGBA", (40, 12), color=(0, 0, 0, 255)).save(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))
    signature_rect = build_signature_rect(page_index=0, width_pt=220.0, height_pt=62.0)
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.RIGHT,
        signature_rect=signature_rect,
        text_box_width=120,
        text_box_height=36,
        box_style=box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=40 / 12,
    )

    background_layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.RIGHT,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=120,
        text_box_height=36,
        box_style=box_style,
    )

    assert background_layout.margins.right > reservation.background_layout.margins.right


def test_background_layout_for_left_wrapped_block_stamp_adds_border_facing_inset(
) -> None:
    stamp_path = Path("/tmp/test-left-stamp-inset.png")
    Image.new("RGBA", (40, 12), color=(0, 0, 0, 255)).save(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))
    signature_rect = build_signature_rect(page_index=0, width_pt=220.0, height_pt=62.0)
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.LEFT,
        signature_rect=signature_rect,
        text_box_width=120,
        text_box_height=36,
        box_style=box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=40 / 12,
    )

    background_layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.LEFT,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=120,
        text_box_height=36,
        box_style=box_style,
    )

    assert background_layout.margins.left > reservation.background_layout.margins.left


def test_single_line_horizontal_text_reservation_width_is_strict_for_left_right() -> None:
    assert (
        _effective_horizontal_text_reservation_width(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.RIGHT,
            text_box_width=115,
        )
        == 115
    )


def test_single_line_horizontal_text_reservation_width_matches_strict_preview_contract(
) -> None:
    assert (
        _effective_horizontal_text_reservation_width(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.RIGHT,
            text_box_width=380,
        )
        == 380
    )


def test_build_text_box_style_preserves_half_point_font_size_in_stamp_style() -> None:
    style = _build_stamp_style(
        SigningBackendAppearance.from_signature_appearance(
            build_signature_appearance(
                text_style=SignatureTextStyle(
                    font_family="Serif",
                    font_size_pt=8.5,
                    bold=False,
                    italic=True,
                    text_color_hex="#000000",
                )
            )
        ),
        stamp_text="Test",
        stamp_background=None,
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.text_box_style.font_size == Fraction(17, 2)


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
def test_horizontal_single_line_ink_validation_reservation_grows_stamp_lane(
    stamp_position: SignatureStampPosition,
) -> None:
    structural_reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=stamp_position,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=373.25,
            height_pt=36.86,
        ),
        text_box_width=254,
        text_box_height=18,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.1,
    )

    ink_reservation = HorizontalSingleLineInkReservation(
        lane_width_pt=218,
        ink_width_pt=210,
        ink_height_pt=12,
        ink_left_offset_pt=12,
        ink_right_slack_pt=32,
        border_facing_padding_pt=4,
        stamp_facing_padding_pt=4,
    )
    validation_reservation = _horizontal_single_line_ink_validation_reservation(
        structural_reservation,
        ink_reservation=ink_reservation,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=373.25,
            height_pt=36.86,
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.1,
    )

    assert validation_reservation.text_area_width_pt == 218
    assert validation_reservation.text_box_width_pt == 218
    assert validation_reservation.stamp_area_width_pt > structural_reservation.stamp_area_width_pt
    assert validation_reservation.stamp_area_width_pt == 141
    assert validation_reservation.inner_content_layout.margins.left >= 0
    assert validation_reservation.inner_content_layout.margins.right >= 0


def test_horizontal_single_line_ink_validation_reservation_falls_back_to_structural() -> None:
    structural_reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=373.25,
            height_pt=36.86,
        ),
        text_box_width=254,
        text_box_height=18,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.1,
    )

    assert (
        _horizontal_single_line_ink_validation_reservation(
            structural_reservation,
            ink_reservation=None,
            signature_rect=build_signature_rect(page_index=0),
            box_style=None,
            has_visible_stamp_image=True,
            stamp_aspect_ratio=4.1,
        )
        is structural_reservation
    )


def test_horizontal_single_line_backend_validation_uses_ink_reference_for_compact_stamp_lane(
    monkeypatch,
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "manual-replay-signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "_single_line_rendered_ink_fits_reservation",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "measure_horizontal_single_line_rendered_reference",
        lambda *_args, **_kwargs: HorizontalSingleLineRenderedReference(
            preview_size_px={"width": 640, "height": 90},
            structural_text_bounds_px={"x": 40, "y": 28, "width": 254, "height": 18},
            rendered_ink_bounds_px={"x": 52, "y": 31, "width": 210, "height": 12},
            structural_text_bounds_pt={"x": 40, "y": 28, "width": 254, "height": 18},
            rendered_ink_bounds_pt={"x": 52, "y": 31, "width": 210, "height": 12},
            px_to_pt=1.0,
        ),
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=36.7,
            bottom_pt=428.6,
            width_pt=261.328,
            height_pt=44.65,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert issues == ()


def test_horizontal_single_line_backend_validation_falls_back_without_ink_reference(
    monkeypatch,
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "manual-replay-signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "_single_line_rendered_ink_fits_reservation",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "measure_horizontal_single_line_rendered_reference",
        lambda *_args, **_kwargs: None,
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=36.7,
            bottom_pt=428.6,
            width_pt=261.328,
            height_pt=44.65,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert len(issues) == 1


def test_horizontal_single_line_cap10_geometry_passes_after_text_first_reservation(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.RIGHT,
            timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=373.25,
            height_pt=36.86,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 15:26"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert issues == ()


def test_horizontal_single_line_still_rejects_when_text_cannot_fit(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.RIGHT,
            timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=34.82,
            bottom_pt=428.48,
            width_pt=248.0,
            height_pt=36.86,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 15:26"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert issues
    assert issues[0].code == "visible_signature_layout_unavailable"


def test_horizontal_single_line_short_height_accepts_preserved_rendered_ink(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=34.3,
            bottom_pt=428.99,
            width_pt=423.43,
            height_pt=24.068,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 17:27"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert issues == ()


def test_manual_caps_4_to_8_replay_backend_validation_ladder(
    tmp_path: Path,
) -> None:
    replay = _load_manual_horizontal_single_line_replay()
    stamp_path = tmp_path / "manual-replay-signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance_config = replay["appearance"]
    stamp_background = _stamp_background_for_path(str(stamp_path))

    for case in replay["cases"]:
        stamp_position = _replay_stamp_position(case)
        appearance = SigningBackendAppearance.from_signature_appearance(
            build_signature_appearance(
                signer_label_prefix=appearance_config["signer_label_prefix"],
                layout_template=SignatureLayoutTemplate.SINGLE_LINE,
                stamp_position=stamp_position,
                timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
                show_field_names=False,
                datetime_format=appearance_config["datetime_format"],
                image_stamp_path=str(stamp_path),
                text_style=SignatureTextStyle(
                    font_family=appearance_config["font_family"],
                    font_size_pt=appearance_config["font_size_pt"],
                    bold=False,
                    italic=False,
                    text_color_hex="#000000",
                ),
            )
        )
        issues = _visible_signature_fit_issues_for_stamp_text(
            signature_rect=build_signature_rect(
                page_index=3,
                left_pt=36.7,
                bottom_pt=428.6,
                width_pt=case["width_pt"],
                height_pt=case["height_pt"],
            ),
            signature_appearance=appearance,
            stamp_text=appearance_config["stamp_text"],
            stamp_background=stamp_background,
        )

        assert (issues == ()) is case["expected_backend_ready"], case["label"]


def test_background_layout_for_stamp_left_aligns_vertical_single_line_image(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "tall_stamp.png"
    Image.new("RGBA", (40, 120), color=(32, 48, 96, 255)).save(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))

    layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        stamp_background=stamp_background,
        signature_rect=build_signature_rect(page_index=0, width_pt=260.0, height_pt=24.0),
        text_box_width=176,
        text_box_height=8,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=3.5,
            background_color_hex="#FFFFFF",
        ),
    )

    assert layout.margins.left <= 3
    assert layout.margins.right > 3
    assert layout.margins.right > layout.margins.left
    assert layout.margins.top >= 3
    assert layout.margins.bottom >= 12


def test_phase3_signing_executor_signs_compact_single_line_rectangle(
    tmp_path: Path,
) -> None:
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        show_field_names=False,
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        text_style=SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=6.0,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
    )

    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="output.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=261.63,
            height_pt=20.99,
        ),
        signature_appearance=appearance,
    )

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is True
    assert result.failure_code is None
    assert output_pdf.exists()
    assert output_pdf.read_bytes() != input_pdf.read_bytes()


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM],
)
def test_phase3_signing_executor_keeps_compact_vertical_stamp_visible(
    tmp_path: Path,
    stamp_position: SignatureStampPosition,
) -> None:
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / f"output-{stamp_position.value}.pdf"
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pdf(input_pdf)
    _write_test_pkcs12(cert_path, passphrase="secret")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=stamp_position,
        show_field_names=False,
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=4.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )

    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name=output_pdf.name,
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=261.63,
            height_pt=22.12,
        ),
        signature_appearance=appearance,
    )

    result = build_phase3_signing_executor().execute(request)

    assert result.success is True
    assert output_pdf.exists()

    scale_x, scale_y = _signature_background_scale(output_pdf)
    assert scale_x > 0.02
    assert scale_y > 0.02

    appearance_text = _signature_appearance_stream_text(output_pdf)
    assert "Inkslapped by" in appearance_text
    assert "Test User" in appearance_text


def test_phase3_signing_executor_maps_wrong_password_to_stable_failure(
    tmp_path: Path,
) -> None:
    _write_test_pdf(tmp_path / "input.pdf")
    _write_test_pkcs12(tmp_path / "cert.p12", passphrase="secret")
    request = build_signing_request(tmp_path, passphrase="wrong-pass")

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PKCS12_WRONG_PASSWORD


def test_phase3_signing_executor_fails_honestly_when_timestamp_is_required(
    tmp_path: Path,
) -> None:
    _write_test_pdf(tmp_path / "input.pdf")
    _write_test_pkcs12(tmp_path / "cert.p12", passphrase="secret")
    request = build_signing_request(
        tmp_path,
        passphrase="secret",
        tsa_url="not-a-valid-tsa-url",
        timestamp_required=True,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
        signature_appearance=build_signature_appearance(
            image_stamp_path=None,
            show_field_names=True,
            signer_label_prefix="",
        ),
    )

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.TSA_UNREACHABLE


def test_phase3_certificate_loader_accepts_valid_pkcs12(tmp_path: Path) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")

    loader = PyHankoCertificateLoader()

    loader.validate(str(cert_path), "secret")


def test_phase3_certificate_loader_rejects_malformed_pkcs12(tmp_path: Path) -> None:
    cert_path = tmp_path / "broken.p12"
    cert_path.write_bytes(b"not a pkcs12 payload")

    loader = PyHankoCertificateLoader()

    with pytest.raises(CertificateLoadError):
        loader.validate(str(cert_path), "secret")


def test_build_stamp_style_uses_solid_background_when_no_image_stamp() -> None:
    appearance = build_signature_appearance(
        image_stamp_path=None,
        stamp_position=SignatureStampPosition.TOP,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=None,
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.background is not None
    assert style.background_layout.inner_content_scaling == InnerScaling.STRETCH_TO_FIT
    assert style.background_layout.x_align == AxisAlignment.ALIGN_MID
    assert style.background_layout.y_align == AxisAlignment.ALIGN_MAX


def test_build_stamp_style_uses_rounded_border_path_for_visible_stamp() -> None:
    appearance = SigningBackendAppearance(
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        field_bindings=(),
        text_style=SignatureTextStyle(
            font_family="Sans Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        image_stamp_path=None,
    )
    style = _build_stamp_style(
        appearance,
        stamp_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-19 15:52",
        stamp_background=None,
        signature_rect=build_signature_rect(page_index=0, width_pt=260.6, height_pt=22.0),
    )
    writer = PdfFileWriter()
    stamp = style.create_stamp(writer, box=BoxConstraints(width=261, height=22), text_params={})
    rendered = stamp.render()

    assert b" re S" not in rendered
    assert b" c " in rendered
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
def test_backend_horizontal_multi_line_fit_gate_can_fail_from_height_not_width(
    stamp_position: SignatureStampPosition,
) -> None:
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=stamp_position,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=34.3,
            bottom_pt=428.99,
            width_pt=260.61,
            height_pt=22.12,
        ),
        text_box_width=62,
        text_box_height=25,
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.0,
    )

    assert reservation.text_box_width_pt == reservation.text_area_width_pt
    assert reservation.text_box_height_pt > reservation.text_area_height_pt


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
def test_backend_horizontal_single_line_structural_reservation_keeps_separator(
    stamp_position: SignatureStampPosition,
) -> None:
    signature_rect = build_signature_rect(
        page_index=0,
        left_pt=35.23,
        bottom_pt=428.68,
        width_pt=259.28,
        height_pt=22.12,
    )
    text_box_width = 180
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=18,
    )

    available_width = max(1, int(round(signature_rect.width_pt)) - 8)
    old_remaining_width = max(available_width - min(text_box_width, available_width), 0)
    old_stamp_area_width = max(old_remaining_width - min(6, old_remaining_width), 0)

    assert reservation.text_area_width_pt == text_box_width
    assert reservation.stamp_area_width_pt == old_stamp_area_width
    assert reservation.text_box_width_pt == text_box_width


def test_multi_line_bottom_allows_one_point_width_rounding_overflow(tmp_path: Path) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.BOTTOM,
        signer_label_prefix="",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="2026-04-06 18:11",
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )
    signature_rect = build_signature_rect(
        page_index=0,
        left_pt=37.376,
        bottom_pt=420.8,
        width_pt=83.456,
        height_pt=78.336,
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=signature_rect,
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
        stamp_text="Adam Smith\nLawson Heirs Inc.\n2026-04-06 18:11",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert issues == ()


def test_multi_line_bottom_rejects_zero_height_stamp_band(tmp_path: Path) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.BOTTOM,
        signer_label_prefix="",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="2026-04-06 18:11",
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )
    signature_rect = build_signature_rect(
        page_index=0,
        left_pt=37.376,
        bottom_pt=420.8,
        width_pt=81.92,
        height_pt=32.768,
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=signature_rect,
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
        stamp_text="Adam Smith\nLawson Heirs Inc.\n2026-04-06 18:11",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert len(issues) == 1
    assert "does not fit" in issues[0].message


@pytest.mark.parametrize(
    ("stamp_position", "width_pt", "height_pt", "expected_pass"),
    [
        (SignatureStampPosition.LEFT, 237.28, 48.45, True),
        (SignatureStampPosition.LEFT, 237.28, 47.45, True),
        (SignatureStampPosition.LEFT, 245.28, 47.45, True),
        (SignatureStampPosition.LEFT, 245.28, 48.45, True),
        (SignatureStampPosition.RIGHT, 245.28, 48.45, True),
        (SignatureStampPosition.RIGHT, 238.28, 48.45, True),
        (SignatureStampPosition.RIGHT, 211.2464, 29.6084, False),
        (SignatureStampPosition.LEFT, 296.956, 50.684, True),
        (SignatureStampPosition.LEFT, 293.884, 49.66, True),
        (SignatureStampPosition.RIGHT, 293.88, 49.66, True),
    ],
)
def test_multi_line_horizontal_accepts_small_structural_height_overflow_when_rendered_layout_fits(  # noqa: E501
    tmp_path: Path,
    stamp_position: SignatureStampPosition,
    width_pt: float,
    height_pt: float,
    expected_pass: bool,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=stamp_position,
        signer_label_prefix="Digitally signed by",
        image_stamp_path=str(stamp_path),
        show_field_names=False,
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=3,
            left_pt=36.86,
            bottom_pt=428.99,
            width_pt=width_pt,
            height_pt=height_pt,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery\n"
            "Board Secretary\n"
            "FoliaSeal\n"
            "2026-04-28 23:56"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    if expected_pass:
        assert issues == ()
    else:
        assert len(issues) == 1
        assert "does not fit" in issues[0].message


def test_build_text_box_style_preserves_half_point_font_size() -> None:
    style = _build_text_box_style(
        SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        )
    )

    assert style.font_size == Fraction(17, 2)


def test_build_text_box_style_uses_italic_font_variant_for_serif() -> None:
    style = _build_text_box_style(
        SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        )
    )

    assert isinstance(style.font, GlyphAccumulatorFactory)
    assert style.font.font_file.endswith("NotoSerif-Italic.ttf")


def test_build_text_box_style_rejects_removed_cursive_family() -> None:
    with pytest.raises(ValueError, match="Unsupported signature font family 'Cursive'"):
        _build_text_box_style(
            SignatureTextStyle(
                font_family="Cursive",
                font_size_pt=8.0,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            )
        )


def test_stamp_background_for_gif_preserves_transparency(tmp_path: Path) -> None:
    stamp_path = tmp_path / "stamp.gif"
    image = Image.new("RGBA", (12, 12), color=(0, 0, 0, 0))
    for x in range(3, 9):
        for y in range(3, 9):
            image.putpixel((x, y), (0, 0, 0, 255))
    image.save(stamp_path, format="GIF", transparency=0)

    background = _stamp_background_for_path(str(stamp_path))

    assert background is not None
    assert getattr(background.image, "mode", None) == "RGBA"
    assert background.image.getchannel("A").getbbox() is not None


def test_measure_text_box_dimensions_reserves_nominal_height_per_line() -> None:
    style = _build_text_box_style(
        SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        )
    )

    width, height = _measure_text_box_dimensions("Line 1\nLine 2\nLine 3", style)

    assert width > 0
    assert height == 27


def test_multi_line_top_accepts_real_world_half_point_width_case(tmp_path: Path) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.TOP,
        signer_label_prefix="",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="2026-04-09 21:17",
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )
    signature_rect = build_signature_rect(
        page_index=0,
        left_pt=187.904,
        bottom_pt=396.736,
        width_pt=120.0,
        height_pt=90.112,
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=signature_rect,
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
        stamp_text=(
            "Adam Smith\nSecretary.LHI@Outlook.com\nBoard Secretary\n"
            "Lawson Heirs Inc.\n2026-04-09 21:17"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert issues == ()


def test_single_line_top_rejects_large_horizontal_overflow_even_with_vertical_compaction(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        signer_label_prefix="",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            override_text="2026-04-12 11:28",
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
        box_style=SignatureBoxStyle(
            show_border=True,
            border_color_hex="#000000",
            border_width_pt=1.0,
            background_color_hex="#FFFFFF",
        ),
    )
    signature_rect = build_signature_rect(
        page_index=3,
        left_pt=35.84,
        bottom_pt=428.48,
        width_pt=259.07,
        height_pt=24.06,
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=signature_rect,
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
        stamp_text=(
            "Adam Smith | Secretary.LHI@Outlook.com | Board Secretary | "
            "Lawson Heirs Inc. | 2026-04-12 11:28"
        ),
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    assert len(issues) == 1
    assert "does not fit" in issues[0].message


def test_background_layout_for_single_line_bottom_preserves_border_facing_gap(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    signature_rect = build_signature_rect(page_index=0, width_pt=260.0, height_pt=24.0)
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.BOTTOM,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=8,
        box_style=box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=2.0,
    )

    layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.BOTTOM,
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=8,
        box_style=box_style,
    )

    assert layout.margins.bottom > reservation.background_layout.margins.bottom


def test_single_line_top_and_bottom_use_distinct_vertical_layout_paths(tmp_path: Path) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))
    signature_rect = build_signature_rect(page_index=0, width_pt=260.0, height_pt=40.0)
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )

    top_layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=10,
        box_style=box_style,
    )
    bottom_layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.BOTTOM,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=180,
        text_box_height=10,
        box_style=box_style,
    )

    assert top_layout.y_align != bottom_layout.y_align
    assert top_layout.margins.top < top_layout.margins.bottom
    assert bottom_layout.margins.bottom < bottom_layout.margins.top


def test_build_stamp_style_uses_template_specific_layout_for_single_line(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.background_layout.x_align == AxisAlignment.ALIGN_MID
    assert style.background_layout.y_align == AxisAlignment.ALIGN_MAX
    assert style.background_layout.inner_content_scaling == InnerScaling.SHRINK_TO_FIT
    assert style.background_layout.margins.bottom >= style.inner_content_layout.margins.bottom
    assert style.inner_content_layout.x_align == AxisAlignment.ALIGN_MIN
    assert style.inner_content_layout.y_align == AxisAlignment.ALIGN_MIN
    assert style.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


def test_build_stamp_style_uses_ink_reservation_for_horizontal_single_line_pdf_layout(
    monkeypatch,
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )
    signature_rect = build_signature_rect(
        page_index=3,
        left_pt=34.82,
        bottom_pt=428.48,
        width_pt=373.25,
        height_pt=36.86,
    )
    stamp_text = (
        "Digitally signed by\n"
        "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
    )
    structural_reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        signature_rect=signature_rect,
        text_box_width=254,
        text_box_height=18,
        box_style=appearance.box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.1,
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "measure_horizontal_single_line_rendered_reference",
        lambda *_args, **_kwargs: HorizontalSingleLineRenderedReference(
            preview_size_px={"width": 640, "height": 90},
            structural_text_bounds_px={"x": 40, "y": 4, "width": 254, "height": 18},
            rendered_ink_bounds_px={"x": 52, "y": 45, "width": 210, "height": 12},
            structural_text_bounds_pt={"x": 40, "y": 4, "width": 254, "height": 18},
            rendered_ink_bounds_pt={"x": 52, "y": 45, "width": 210, "height": 12},
            px_to_pt=1.0,
        ),
    )

    style = _build_stamp_style(
        appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=signature_rect,
    )

    assert (
        style.inner_content_layout.margins.left
        > structural_reservation.inner_content_layout.margins.left
    )
    assert style.inner_content_layout.margins.right == (
        structural_reservation.inner_content_layout.margins.right - 32
    )
    assert (
        style.background_layout.margins.right
        < structural_reservation.background_layout.margins.right
    )


def test_build_stamp_style_falls_back_to_structural_horizontal_layout_without_ink_reference(
    monkeypatch,
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )
    signature_rect = build_signature_rect(
        page_index=3,
        left_pt=34.82,
        bottom_pt=428.48,
        width_pt=373.25,
        height_pt=36.86,
    )
    stamp_text = (
        "Digitally signed by\n"
        "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
    )
    structural_reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        signature_rect=signature_rect,
        text_box_width=254,
        text_box_height=18,
        box_style=appearance.box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=4.1,
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "measure_horizontal_single_line_rendered_reference",
        lambda *_args, **_kwargs: None,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=signature_rect,
    )

    assert style.inner_content_layout.margins.left == (
        structural_reservation.inner_content_layout.margins.left
    )
    assert style.inner_content_layout.margins.right == (
        structural_reservation.inner_content_layout.margins.right
    )


def test_build_stamp_style_matches_canonical_preview_ink_reservation_margins(
    monkeypatch,
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    signature_rect = build_signature_rect(
        page_index=3,
        left_pt=34.82,
        bottom_pt=428.48,
        width_pt=373.25,
        height_pt=36.86,
    )
    text_style = SignatureTextStyle(
        font_family="Serif",
        font_size_pt=8.5,
        bold=False,
        italic=False,
        text_color_hex="#000000",
    )
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )
    rendered_reference = HorizontalSingleLineRenderedReference(
        preview_size_px={"width": 640, "height": 90},
        structural_text_bounds_px={"x": 40, "y": 4, "width": 254, "height": 18},
        rendered_ink_bounds_px={"x": 52, "y": 45, "width": 210, "height": 12},
        structural_text_bounds_pt={"x": 40, "y": 4, "width": 254, "height": 18},
        rendered_ink_bounds_pt={"x": 52, "y": 45, "width": 210, "height": 12},
        px_to_pt=1.0,
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "measure_horizontal_single_line_rendered_reference",
        lambda *_args, **_kwargs: rendered_reference,
    )
    monkeypatch.setattr(
        signing_preview_renderer_module,
        "measure_horizontal_single_line_rendered_reference",
        lambda *_args, **_kwargs: rendered_reference,
    )
    stamp_text = (
        "Digitally signed by\n"
        "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
    )
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=text_style,
            box_style=box_style,
        )
    )
    preview = SigningDraftPreview(
        title="Digitally signed by",
        page_index=3,
        signature_rect=signature_rect,
        signer_label_prefix="Digitally signed by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        text_style=text_style,
        box_style=box_style,
        image_stamp_path=str(stamp_path),
        fields=(),
        detail_text="Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19",
        issues=(),
        can_submit=True,
    )

    pdf_style = _build_stamp_style(
        appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=signature_rect,
    )
    preview_layout = signing_preview_renderer_module._canonical_preview_layout(
        preview,
        include_text=True,
        include_stamp=True,
        include_border=True,
    )

    assert pdf_style.inner_content_layout.margins == (
        preview_layout.inner_content_layout.margins
    )
    assert pdf_style.background_layout.margins == preview_layout.background_layout.margins


def test_build_stamp_style_uses_template_specific_layout_for_multi_line(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.background_layout.x_align == AxisAlignment.ALIGN_MAX
    assert style.background_layout.y_align == AxisAlignment.ALIGN_MID
    assert style.background_layout.inner_content_scaling == InnerScaling.SHRINK_TO_FIT
    assert style.inner_content_layout.x_align == AxisAlignment.ALIGN_MIN
    assert style.inner_content_layout.y_align == AxisAlignment.ALIGN_MID
    assert style.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


def test_background_layout_for_horizontal_single_line_keeps_stamp_vertically_inside_lane(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "wide_signature.png"
    Image.new("RGBA", (1400, 334), color=(0, 0, 0, 160)).save(stamp_path)
    stamp_background = _stamp_background_for_path(str(stamp_path))
    signature_rect = build_signature_rect(
        page_index=3,
        left_pt=36.86,
        bottom_pt=429.5,
        width_pt=384.506,
        height_pt=28.678,
    )
    box_style = SignatureBoxStyle(
        show_border=True,
        border_color_hex="#000000",
        border_width_pt=1.0,
        background_color_hex="#FFFFFF",
    )
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        signature_rect=signature_rect,
        text_box_width=254,
        text_box_height=18,
        box_style=box_style,
        has_visible_stamp_image=True,
        stamp_aspect_ratio=1400 / 334,
    )

    layout = _background_layout_for_stamp(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.LEFT,
        stamp_background=stamp_background,
        signature_rect=signature_rect,
        text_box_width=254,
        text_box_height=18,
        box_style=box_style,
    )

    fitted_height = (
        reservation.container_height_pt
        - layout.margins.top
        - layout.margins.bottom
    )
    assert fitted_height <= reservation.stamp_area_height_pt - 4


def test_build_stamp_style_uses_template_specific_layout_for_left_position(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.LEFT,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.background_layout.x_align == AxisAlignment.ALIGN_MIN
    assert style.background_layout.y_align == AxisAlignment.ALIGN_MID
    assert style.background_layout.inner_content_scaling == InnerScaling.SHRINK_TO_FIT
    assert style.inner_content_layout.x_align == AxisAlignment.ALIGN_MAX
    assert style.inner_content_layout.y_align == AxisAlignment.ALIGN_MID
    assert style.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


def test_build_stamp_style_uses_template_specific_layout_for_wrapped_block(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        layout_template=SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.BOTTOM,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.background_layout.x_align == AxisAlignment.ALIGN_MID
    assert style.background_layout.y_align == AxisAlignment.ALIGN_MIN
    assert style.background_layout.inner_content_scaling == InnerScaling.SHRINK_TO_FIT
    assert style.inner_content_layout.x_align == AxisAlignment.ALIGN_MID
    assert style.inner_content_layout.y_align == AxisAlignment.ALIGN_MAX
    assert style.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


def test_build_stamp_style_uses_shrink_to_fit_for_image_background(
    tmp_path: Path,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        image_stamp_path=str(stamp_path),
        layout_template=SignatureLayoutTemplate.MULTI_LINE,
    )

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=_stamp_background_for_path(str(stamp_path)),
        signature_rect=build_signature_rect(page_index=0),
    )

    assert style.background_layout.inner_content_scaling == InnerScaling.SHRINK_TO_FIT


def test_build_stamp_text_uses_real_derived_values_without_placeholder_labels(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    signer = _load_simple_signer(str(cert_path), "secret")
    appearance = SigningBackendAppearance.from_signature_appearance(build_signature_appearance())

    stamp_text = _build_stamp_text(
        appearance=appearance,
        signer=signer,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
    )

    assert "Test User" in stamp_text
    assert "Board Secretary" in stamp_text
    assert "FoliaSeal" in stamp_text
    assert "Wytheville, Virginia, US" in stamp_text
    assert "Reason" not in stamp_text
    assert "Location" not in stamp_text


def test_backend_visible_semantics_resolve_stamp_text_and_metadata(tmp_path: Path) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    signer = _load_simple_signer(str(cert_path), "secret")
    signing_time = datetime(2026, 5, 1, 14, 30, tzinfo=UTC)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
            show_field_names=False,
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            email=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            title=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            company=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            signing_time=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.OVERRIDE,
                override_text="Approved for release",
            ),
            location=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
        )
    )

    semantics = _resolve_visible_signature_semantics(
        certificate_path=str(cert_path),
        passphrase="secret",
        appearance=appearance,
        signer=signer,
        signing_time=signing_time,
        signature_rect=build_signature_rect(page_index=0),
    )

    assert semantics.text.stamp_text == (
        "Digitally signed by\n"
        "Test User\n"
        "test@example.com\n"
        "Board Secretary\n"
        "FoliaSeal\n"
        "2026-05-01 14:30\n"
        "Approved for release\n"
        "Wytheville, Virginia, US"
    )
    assert semantics.text.metadata_reason == "Approved for release"
    assert semantics.text.metadata_location == "Wytheville, Virginia, US"
    assert semantics.text.metadata_contact_info == "test@example.com"
    assert (
        _build_stamp_text(
            appearance=appearance,
            signer=signer,
            signing_time=signing_time,
            signature_rect=build_signature_rect(page_index=0),
        )
        == semantics.text.stamp_text
    )


def test_visible_signature_fit_issues_use_semantics_stamp_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    signer = _load_simple_signer(str(cert_path), "secret")
    signing_time = datetime(2026, 5, 1, 14, 30, tzinfo=UTC)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            show_field_names=False,
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            email=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            title=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            company=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            signing_time=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(source=SignatureFieldSource.DERIVED),
        )
    )
    captured: dict[str, str] = {}

    def _capture_fit_issues(**kwargs):
        captured["stamp_text"] = kwargs["stamp_text"]
        return ()

    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend."
        "_visible_signature_fit_issues_for_stamp_text",
        _capture_fit_issues,
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(page_index=0),
        signature_appearance=appearance,
        signer=signer,
        signing_time=signing_time,
    )

    assert issues == ()
    assert captured["stamp_text"] == (
        "Digitally signed by\n"
        "Test User | test@example.com | Board Secretary | FoliaSeal | "
        "2026-05-01 14:30 | Wytheville, Virginia, US"
    )


def test_build_stamp_text_wraps_single_line_content_for_compact_rectangle(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    signer = _load_simple_signer(str(cert_path), "secret")
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Inkslapped by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            show_field_names=False,
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            text_style=SignatureTextStyle(
                font_family="Source Sans 3",
                font_size_pt=6.0,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    stamp_text = _build_stamp_text(
        appearance=appearance,
        signer=signer,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=180.0,
            height_pt=20.99,
        ),
    )

    assert "\n" in stamp_text
    assert "Inkslapped by" in stamp_text
    assert "Test User" in stamp_text
    assert "test@example.com" in stamp_text
    assert "FoliaSeal" in stamp_text


def test_build_stamp_text_prefers_fewer_body_lines_for_compact_vertical_single_line(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    signer = _load_simple_signer(str(cert_path), "secret")
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Inkslapped by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            show_field_names=False,
            image_stamp_path="dummy.png",
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=6.0,
                bold=False,
                italic=True,
                text_color_hex="#000000",
            ),
        )
    )

    stamp_text = _build_stamp_text(
        appearance=appearance,
        signer=signer,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=36.48,
            bottom_pt=429.76,
            width_pt=263.04,
            height_pt=20.48,
        ),
    )

    assert stamp_text.count("\n") == 1
    assert "Inkslapped by" in stamp_text
    assert "Adam Smith" in stamp_text
    assert "Wytheville, Virginia, US" in stamp_text


def test_build_stamp_text_wraps_horizontal_single_line_when_stamp_is_present(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    signer = _load_simple_signer(str(cert_path), "secret")
    signature_rect = build_signature_rect(
        page_index=0,
        left_pt=35.23,
        bottom_pt=428.68,
        width_pt=259.28,
        height_pt=22.12,
    )

    def _appearance(image_stamp_path: str | None) -> SigningBackendAppearance:
        return SigningBackendAppearance.from_signature_appearance(
            build_signature_appearance(
                signer_label_prefix="Inkslapped by",
                layout_template=SignatureLayoutTemplate.SINGLE_LINE,
                stamp_position=SignatureStampPosition.LEFT,
                show_field_names=False,
                image_stamp_path=image_stamp_path,
                distinguished_name=build_signature_field_binding(
                    source=SignatureFieldSource.HIDDEN,
                    show_in_visible_appearance=False,
                ),
                common_name=build_signature_field_binding(
                    source=SignatureFieldSource.DERIVED,
                    show_in_visible_appearance=True,
                ),
                email=build_signature_field_binding(
                    source=SignatureFieldSource.DERIVED,
                    show_in_visible_appearance=True,
                ),
                title=build_signature_field_binding(
                    source=SignatureFieldSource.DERIVED,
                    show_in_visible_appearance=True,
                ),
                company=build_signature_field_binding(
                    source=SignatureFieldSource.DERIVED,
                    show_in_visible_appearance=True,
                ),
                signing_time=build_signature_field_binding(
                    source=SignatureFieldSource.DERIVED,
                    show_in_visible_appearance=True,
                ),
                reason=build_signature_field_binding(
                    source=SignatureFieldSource.HIDDEN,
                    show_in_visible_appearance=False,
                ),
                location=build_signature_field_binding(
                    source=SignatureFieldSource.DERIVED,
                    show_in_visible_appearance=True,
                ),
                text_style=SignatureTextStyle(
                    font_family="Serif",
                    font_size_pt=6.0,
                    bold=False,
                    italic=True,
                    text_color_hex="#000000",
                ),
            )
        )

    appearance_without_stamp = _appearance(None)
    without_stamp = _build_stamp_text(
        appearance=appearance_without_stamp,
        signer=signer,
        signing_time=_current_signing_time(appearance_without_stamp.timezone_display_mode),
        signature_rect=signature_rect,
    )
    appearance_with_stamp = _appearance("dummy.png")
    with_stamp = _build_stamp_text(
        appearance=appearance_with_stamp,
        signer=signer,
        signing_time=_current_signing_time(appearance_with_stamp.timezone_display_mode),
        signature_rect=signature_rect,
    )

    assert with_stamp.count("\n") >= without_stamp.count("\n")
    assert "Adam Smith" in with_stamp
    assert "Wytheville, Virginia, US" in with_stamp



@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
def test_visible_signature_fit_issues_accept_compact_horizontal_rectangle_with_realistic_text(
    tmp_path: Path,
    stamp_position: SignatureStampPosition,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    _write_test_stamp_image(stamp_path)
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Inkslapped by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=stamp_position,
            show_field_names=False,
            image_stamp_path=str(stamp_path),
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=4.5,
                bold=False,
                italic=True,
                text_color_hex="#000000",
            ),
        )
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.23,
            bottom_pt=428.68,
            width_pt=259.28,
            height_pt=22.12,
        ),
        signature_appearance=appearance,
    )

    assert issues == ()


def test_build_stamp_text_keeps_single_line_body_single_when_roomy(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    signer = _load_simple_signer(str(cert_path), "secret")
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Inkslapped by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            show_field_names=False,
            image_stamp_path=None,
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            text_style=SignatureTextStyle(
                font_family="Source Sans 3",
                font_size_pt=6.0,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    stamp_text = _build_stamp_text(
        appearance=appearance,
        signer=signer,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
    )

    lines = stamp_text.splitlines()

    assert lines[0] == "Inkslapped by"
    assert len(lines) == 2
    assert "Test User" in lines[1]
    assert "test@example.com" in lines[1]
    assert "FoliaSeal" in lines[1]


def test_build_stamp_text_without_prefix_keeps_roomy_single_line_on_one_line(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    signer = _load_simple_signer(str(cert_path), "secret")
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            show_field_names=False,
            image_stamp_path=None,
            distinguished_name=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            common_name=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            email=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            signing_time=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            reason=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            location=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            title=build_signature_field_binding(
                source=SignatureFieldSource.HIDDEN,
                show_in_visible_appearance=False,
            ),
            company=build_signature_field_binding(
                source=SignatureFieldSource.DERIVED,
                show_in_visible_appearance=True,
            ),
            text_style=SignatureTextStyle(
                font_family="Source Sans 3",
                font_size_pt=6.0,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    stamp_text = _build_stamp_text(
        appearance=appearance,
        signer=signer,
        signing_time=_current_signing_time(appearance.timezone_display_mode),
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=620.0,
            height_pt=180.0,
        ),
    )

    assert "\n" not in stamp_text
    assert "Test User" in stamp_text
    assert "test@example.com" in stamp_text
    assert "FoliaSeal" in stamp_text


def test_phase3_signing_executor_rejects_visible_signature_that_does_not_fit(
    tmp_path: Path,
) -> None:
    _write_test_pdf(tmp_path / "input.pdf")
    _write_test_pkcs12(tmp_path / "cert.p12", passphrase="secret")
    request = build_signing_request(
        tmp_path,
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(
            page_index=0,
            width_pt=42.0,
            height_pt=12.0,
        ),
        signature_appearance=build_signature_appearance(
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        ),
    )

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PDF_SIGNING_FAILED
    assert "does not fit" in result.message.lower()


def test_visible_signature_fit_issues_accept_compact_real_world_rectangle(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret")
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        show_field_names=False,
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        text_style=SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=6.0,
            bold=False,
            italic=False,
            text_color_hex="#000000",
        ),
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.84,
            bottom_pt=428.48,
            width_pt=261.63,
            height_pt=20.99,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert issues == ()


def test_build_stamp_text_accepts_compact_vertical_single_line_with_modest_width_overflow(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        show_field_names=False,
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=10.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )
    backend_appearance = SigningBackendAppearance.from_signature_appearance(appearance)
    signer = _load_simple_signer(str(cert_path), "secret")
    signing_time = _current_signing_time(backend_appearance.timezone_display_mode)

    stamp_text = _build_stamp_text(
        appearance=backend_appearance,
        signer=signer,
        signing_time=signing_time,
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=429.0,
            width_pt=260.0,
            height_pt=22.0,
        ),
    )

    assert "Inkslapped by" in stamp_text
    assert (
        "Adam Smith | Secretary.LHI@Outlook.com | Board Secretary | Lawson Heirs Inc."
        in stamp_text
    )


def test_visible_signature_fit_issues_reject_compact_vertical_rectangle_with_four_fields_at_nine_point(  # noqa: E501
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        show_field_names=False,
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=9.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=429.0,
            width_pt=260.0,
            height_pt=22.0,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert len(issues) == 1
    assert "does not fit" in issues[0].message


def test_visible_signature_fit_issues_reject_compact_vertical_rectangle_with_five_fields_at_eight_point_five(  # noqa: E501
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.gif"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=34.0,
            bottom_pt=430.0,
            width_pt=260.0,
            height_pt=22.0,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert len(issues) == 1
    assert "does not fit" in issues[0].message


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM],
)
def test_visible_signature_fit_issues_reject_real_world_vertical_single_line_text(
    tmp_path: Path,
    stamp_position: SignatureStampPosition,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.gif"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=stamp_position,
        timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.5,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=260.0,
            height_pt=24.0,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert len(issues) == 1
    assert "does not fit" in issues[0].message


@pytest.mark.parametrize(
    ("width_pt", "expected_pass"),
    [
        (244.0, False),
        (247.294, True),
        (256.29, True),
        (261.29, True),
    ],
)
def test_visible_signature_fit_issues_use_rendered_ink_fallback_for_manual_single_line_top_stamp_ladder(  # noqa: E501
    tmp_path: Path,
    width_pt: float,
    expected_pass: bool,
) -> None:
    stamp_path = tmp_path / "stamp.png"
    Image.new("RGBA", (640, 160), color=(255, 255, 255, 0)).save(stamp_path, format="PNG")
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )
    stamp_text = (
        "Digitally signed by\n"
        "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-24 21:26"
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=width_pt,
            height_pt=61.44,
        ),
        signature_appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background_for_path(str(stamp_path)),
    )

    if expected_pass:
        assert issues == ()
    else:
        assert len(issues) == 1
        assert "does not fit" in issues[0].message


@pytest.mark.parametrize(
    ("width_pt", "stamp_position", "stamp_path", "font_family", "stamp_text"),
    [
        (
            241.664,
            SignatureStampPosition.TOP,
            None,
            "Sans Serif",
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:34",
        ),
        (
            248.66,
            SignatureStampPosition.TOP,
            None,
            "Sans Serif",
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:35",
        ),
        (
            250.106,
            SignatureStampPosition.BOTTOM,
            "stamp.png",
            "Serif",
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:37",
        ),
        (
            258.56,
            SignatureStampPosition.LEFT,
            None,
            "Sans Serif",
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:50",
        ),
        (
            258.56,
            SignatureStampPosition.RIGHT,
            None,
            "Sans Serif",
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-25 02:51",
        ),
    ],
)
def test_visible_signature_fit_issues_use_rendered_ink_for_manual_vertical_single_line_false_negatives(  # noqa: E501
    tmp_path: Path,
    width_pt: float,
    stamp_position: SignatureStampPosition,
    stamp_path: str | None,
    font_family: str,
    stamp_text: str,
) -> None:
    image_stamp_path = None
    if stamp_path is not None:
        image_stamp_path = str(tmp_path / stamp_path)
        Image.new("RGBA", (640, 160), color=(0, 0, 0, 160)).save(
            image_stamp_path,
            format="PNG",
        )
    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=stamp_position,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=image_stamp_path,
            text_style=SignatureTextStyle(
                font_family=font_family,
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    issues = _visible_signature_fit_issues_for_stamp_text(
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=width_pt,
            height_pt=87.562 if stamp_position == SignatureStampPosition.BOTTOM else 24.58,
        ),
        signature_appearance=appearance,
        stamp_text=stamp_text,
        stamp_background=_stamp_background_for_path(image_stamp_path),
    )

    assert issues == ()


def test_single_line_rendered_ink_fallback_caches_identical_checks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _SINGLE_LINE_RENDERED_INK_FIT_CACHE.clear()
    stamp_path = tmp_path / "stamp.png"
    current_png = tmp_path / "current.png"
    Image.new("RGBA", (320, 80), color=(255, 255, 255, 255)).save(stamp_path, format="PNG")
    Image.new("RGBA", (300, 90), color=(255, 255, 255, 255)).save(current_png, format="PNG")

    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.TOP,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )
    render_calls: list[float] = []

    def _fake_render(preview, **_kwargs):
        render_calls.append(preview.signature_rect.width_pt)
        path = current_png
        bounds = {"x": 4, "y": 28, "width": 240, "height": 16}
        image_width = 250
        return type(
            "_Snapshot",
            (),
            {
                "image_path": str(path),
                "width_px": image_width,
                "height_px": 90,
                "text_area_bounds_px": {"x": 0, "y": 24, "width": image_width, "height": 20},
                "stamp_area_bounds_px": {"x": 0, "y": 0, "width": image_width, "height": 24},
                "text_bounds_px": bounds,
                "stamp_bounds_px": None,
            },
        )()

    monkeypatch.setattr(
        "foliaseal.application.signing_preview_renderer.render_canonical_signature_preview",
        _fake_render,
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend.detect_text_content_bounds_in_image",
        lambda **kwargs: ({"x": 4, "y": 28, "width": 240, "height": 16}, None),
    )

    signature_rect = build_signature_rect(
        page_index=0,
        left_pt=35.0,
        bottom_pt=428.0,
        width_pt=247.294,
        height_pt=61.44,
    )
    stamp_text = (
        "Digitally signed by\n"
        "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-24 21:26"
    )

    assert _single_line_rendered_ink_fits_reservation(
        signature_rect=signature_rect,
        signature_appearance=appearance,
        stamp_text=stamp_text,
    )
    assert _single_line_rendered_ink_fits_reservation(
        signature_rect=signature_rect,
        signature_appearance=appearance,
        stamp_text=stamp_text,
    )
    assert render_calls == [247.294]


def test_single_line_rendered_ink_fallback_rejects_border_flush_text(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _SINGLE_LINE_RENDERED_INK_FIT_CACHE.clear()
    stamp_path = tmp_path / "stamp.png"
    current_png = tmp_path / "current.png"
    Image.new("RGBA", (320, 80), color=(255, 255, 255, 255)).save(stamp_path, format="PNG")
    Image.new("RGBA", (300, 90), color=(255, 255, 255, 255)).save(current_png, format="PNG")

    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
            box_style=SignatureBoxStyle(
                show_border=True,
                border_color_hex="#000000",
                border_width_pt=1.0,
                background_color_hex="#FFFFFF",
            ),
        )
    )

    def _fake_render(preview, **_kwargs):
        return type(
            "_Snapshot",
            (),
            {
                "image_path": str(current_png),
                "width_px": 300,
                "height_px": 90,
                "text_area_bounds_px": {"x": 40, "y": 24, "width": 254, "height": 20},
                "stamp_area_bounds_px": {"x": 4, "y": 4, "width": 30, "height": 82},
                "text_bounds_px": {"x": 40, "y": 28, "width": 254, "height": 18},
                "stamp_bounds_px": {"x": 4, "y": 35, "width": 28, "height": 7},
            },
        )()

    monkeypatch.setattr(
        "foliaseal.application.signing_preview_renderer.render_canonical_signature_preview",
        _fake_render,
    )
    text_only_bounds = iter(
        (
            {"x": 0, "y": 28, "width": 220, "height": 17},
            {"x": 50, "y": 28, "width": 220, "height": 17},
        )
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend._single_line_text_only_ink_bounds",
        lambda **kwargs: next(text_only_bounds),
    )

    assert not _single_line_rendered_ink_fits_reservation(
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=273.61,
            height_pt=42.60,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
        ),
    )


def test_single_line_rendered_ink_fallback_rejects_reference_text_loss(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _SINGLE_LINE_RENDERED_INK_FIT_CACHE.clear()
    stamp_path = tmp_path / "stamp.png"
    current_png = tmp_path / "current.png"
    Image.new("RGBA", (320, 80), color=(255, 255, 255, 255)).save(stamp_path, format="PNG")
    Image.new("RGBA", (300, 90), color=(255, 255, 255, 255)).save(current_png, format="PNG")

    appearance = SigningBackendAppearance.from_signature_appearance(
        build_signature_appearance(
            signer_label_prefix="Digitally signed by",
            layout_template=SignatureLayoutTemplate.SINGLE_LINE,
            stamp_position=SignatureStampPosition.LEFT,
            timezone_display_mode=SignatureTimezoneDisplayMode.UTC,
            show_field_names=False,
            datetime_format="%Y-%m-%d %H:%M",
            image_stamp_path=str(stamp_path),
            text_style=SignatureTextStyle(
                font_family="Serif",
                font_size_pt=8.5,
                bold=False,
                italic=False,
                text_color_hex="#000000",
            ),
        )
    )

    def _fake_render(preview, **_kwargs):
        return type(
            "_Snapshot",
            (),
            {
                "image_path": str(current_png),
                "width_px": 300,
                "height_px": 90,
                "text_area_bounds_px": {"x": 40, "y": 24, "width": 254, "height": 20},
                "stamp_area_bounds_px": {"x": 4, "y": 4, "width": 30, "height": 82},
                "text_bounds_px": {"x": 40, "y": 28, "width": 254, "height": 18},
                "stamp_bounds_px": {"x": 4, "y": 35, "width": 28, "height": 7},
            },
        )()

    monkeypatch.setattr(
        "foliaseal.application.signing_preview_renderer.render_canonical_signature_preview",
        _fake_render,
    )
    text_only_bounds = iter(
        (
            {"x": 75, "y": 28, "width": 217, "height": 17},
            {"x": 40, "y": 28, "width": 254, "height": 18},
        )
    )
    monkeypatch.setattr(
        "foliaseal.application.phase3_signing_backend._single_line_text_only_ink_bounds",
        lambda **kwargs: next(text_only_bounds),
    )

    assert not _single_line_rendered_ink_fits_reservation(
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=273.61,
            height_pt=42.60,
        ),
        signature_appearance=appearance,
        stamp_text=(
            "Digitally signed by\n"
            "Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-26 21:19"
        ),
    )


def test_visible_signature_fit_issues_reject_compact_horizontal_rectangle_with_real_signature_gif(
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    Image.new("RGB", (1400, 334), color=(215, 235, 255)).save(stamp_path, format="PNG")
    appearance = build_signature_appearance(
        signer_label_prefix="",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        timezone_display_mode=SignatureTimezoneDisplayMode.LOCAL,
        show_field_names=False,
        datetime_format="%Y-%m-%d %H:%M",
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Adam Smith",
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Secretary.LHI@Outlook.com",
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Board Secretary",
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text="Lawson Heirs Inc.",
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=8.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=428.0,
            width_pt=260.0,
            height_pt=24.0,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert issues
    assert issues[0].code == "visible_signature_layout_unavailable"


def test_visible_signature_fit_issues_reject_compact_vertical_rectangle_when_combined_text_is_too_tall(  # noqa: E501
    tmp_path: Path,
) -> None:
    cert_path = tmp_path / "cert.p12"
    stamp_path = tmp_path / "stamp.png"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    _write_test_stamp_image(stamp_path)
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        show_field_names=False,
        image_stamp_path=str(stamp_path),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=10.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=35.0,
            bottom_pt=429.0,
            width_pt=260.0,
            height_pt=22.0,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert len(issues) == 1
    assert issues[0].code == "visible_signature_layout_unavailable"


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM],
)
def test_visible_signature_fit_issues_reject_compact_vertical_rectangle_with_six_point_text(
    tmp_path: Path,
    stamp_position: SignatureStampPosition,
) -> None:
    cert_path = tmp_path / "cert.p12"
    _write_test_pkcs12(cert_path, passphrase="secret", common_name="Adam Smith")
    appearance = build_signature_appearance(
        signer_label_prefix="Inkslapped by",
        layout_template=SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=stamp_position,
        show_field_names=False,
        image_stamp_path=str(tmp_path / "stamp.png"),
        distinguished_name=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        common_name=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        email=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        title=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        company=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        signing_time=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        reason=build_signature_field_binding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
        ),
        location=build_signature_field_binding(
            source=SignatureFieldSource.DERIVED,
            show_in_visible_appearance=True,
        ),
        text_style=SignatureTextStyle(
            font_family="Serif",
            font_size_pt=6.0,
            bold=False,
            italic=True,
            text_color_hex="#000000",
        ),
    )
    _write_test_stamp_image(tmp_path / "stamp.png")

    issues = _visible_signature_fit_issues(
        certificate_path=str(cert_path),
        passphrase="secret",
        signature_rect=build_signature_rect(
            page_index=0,
            left_pt=36.48,
            bottom_pt=429.76,
            width_pt=263.04,
            height_pt=20.48,
        ),
        signature_appearance=SigningBackendAppearance.from_signature_appearance(appearance),
    )

    assert len(issues) == 1
    assert "does not fit" in issues[0].message
