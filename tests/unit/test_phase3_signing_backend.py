import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PIL import Image
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.layout import AxisAlignment, InnerScaling
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext

from foliaseal.application.phase3_signing_backend import (
    PyHankoCertificateLoader,
    PyHankoSignatureVerifier,
    _build_stamp_style,
    _build_stamp_text,
    _current_signing_time,
    _layout_reservation_for_template,
    _load_simple_signer,
    _stamp_background_for_path,
    _visible_signature_fit_issues,
    build_phase3_signing_executor,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.domain.errors import CertificateLoadError, FailureCode
from foliaseal.domain.models import (
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureStampPosition,
    SignatureTextStyle,
)
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_field_binding,
    build_signature_rect,
    build_signing_request,
)


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
    request = build_signing_request(tmp_path, passphrase="secret", timestamp_required=True)

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
    assert style.inner_content_layout.x_align == AxisAlignment.ALIGN_MID
    assert style.inner_content_layout.y_align == AxisAlignment.ALIGN_MIN
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


def test_layout_reservation_for_single_line_allocates_right_text_space() -> None:
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.SINGLE_LINE,
        stamp_position=SignatureStampPosition.TOP,
        signature_rect=build_signature_rect(page_index=0, width_pt=240.0, height_pt=72.0),
        text_box_width=110,
        text_box_height=18,
    )

    assert reservation.layout_template == SignatureLayoutTemplate.SINGLE_LINE
    assert reservation.reserved_primary_extent_pt > 0
    assert reservation.stamp_area_width_pt < reservation.container_width_pt
    assert reservation.stamp_area_height_pt < reservation.container_height_pt
    assert reservation.text_area_width_pt < reservation.container_width_pt
    assert reservation.text_area_height_pt < reservation.container_height_pt
    assert reservation.background_layout.x_align == AxisAlignment.ALIGN_MIN
    assert reservation.background_layout.y_align == AxisAlignment.ALIGN_MAX
    assert reservation.inner_content_layout.x_align == AxisAlignment.ALIGN_MID
    assert reservation.inner_content_layout.y_align == AxisAlignment.ALIGN_MIN
    assert reservation.background_layout.inner_content_scaling == InnerScaling.STRETCH_TO_FIT
    assert reservation.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING


def test_layout_reservation_for_multi_line_allocates_right_text_space() -> None:
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.MULTI_LINE,
        stamp_position=SignatureStampPosition.RIGHT,
        signature_rect=build_signature_rect(page_index=0, width_pt=240.0, height_pt=72.0),
        text_box_width=110,
        text_box_height=18,
    )

    assert reservation.layout_template == SignatureLayoutTemplate.MULTI_LINE
    assert reservation.reserved_primary_extent_pt > 0
    assert reservation.stamp_area_width_pt < reservation.container_width_pt
    assert reservation.stamp_area_height_pt == 64
    assert reservation.text_area_width_pt < reservation.container_width_pt
    assert reservation.text_area_height_pt == 64
    assert reservation.background_layout.x_align == AxisAlignment.ALIGN_MAX
    assert reservation.inner_content_layout.x_align == AxisAlignment.ALIGN_MIN
    assert reservation.background_layout.inner_content_scaling == InnerScaling.STRETCH_TO_FIT
    assert reservation.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING


@pytest.mark.parametrize(
    "stamp_position",
    [SignatureStampPosition.LEFT, SignatureStampPosition.RIGHT],
)
def test_layout_reservation_for_horizontal_single_line_frees_more_stamp_space(
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

    assert reservation.text_area_width_pt < text_box_width
    assert reservation.stamp_area_width_pt > old_stamp_area_width
    assert reservation.text_box_width_pt == text_box_width


def test_layout_reservation_for_wrapped_block_allocates_bottom_text_space() -> None:
    reservation = _layout_reservation_for_template(
        SignatureLayoutTemplate.WRAPPED_BLOCK,
        stamp_position=SignatureStampPosition.BOTTOM,
        signature_rect=build_signature_rect(page_index=0, width_pt=240.0, height_pt=72.0),
        text_box_width=110,
        text_box_height=18,
    )

    assert reservation.layout_template == SignatureLayoutTemplate.WRAPPED_BLOCK
    assert reservation.reserved_primary_extent_pt > 0
    assert reservation.stamp_area_width_pt == reservation.text_area_width_pt
    assert reservation.stamp_area_height_pt < reservation.container_height_pt
    assert reservation.background_layout.x_align == AxisAlignment.ALIGN_MID
    assert reservation.inner_content_layout.x_align == AxisAlignment.ALIGN_MID
    assert reservation.background_layout.y_align == AxisAlignment.ALIGN_MIN
    assert reservation.inner_content_layout.y_align == AxisAlignment.ALIGN_MAX


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

    assert style.background_layout.x_align == AxisAlignment.ALIGN_MIN
    assert style.background_layout.y_align == AxisAlignment.ALIGN_MAX
    assert style.background_layout.inner_content_scaling == InnerScaling.SHRINK_TO_FIT
    assert style.background_layout.margins.bottom >= style.inner_content_layout.margins.bottom
    assert style.inner_content_layout.x_align == AxisAlignment.ALIGN_MID
    assert style.inner_content_layout.y_align == AxisAlignment.ALIGN_MIN
    assert style.inner_content_layout.inner_content_scaling == InnerScaling.NO_SCALING
    assert style.text_box_style.box_layout_rule.inner_content_scaling == InnerScaling.NO_SCALING


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


def test_build_stamp_text_wraps_horizontal_single_line_more_aggressively_when_stamp_is_present(
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
    assert "Adam Smith | test@example.com | Board Secretary | FoliaSeal" in stamp_text


def test_visible_signature_fit_issues_accept_compact_vertical_rectangle_with_four_fields_at_nine_point(  # noqa: E501
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

    assert issues == ()


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
def test_visible_signature_fit_issues_accept_compact_vertical_rectangle_with_six_point_text(
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

    assert issues == ()
