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
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext

from foliaseal.application.phase3_signing_backend import (
    PyHankoCertificateLoader,
    PyHankoSignatureVerifier,
    _build_stamp_style,
    build_phase3_signing_executor,
)
from foliaseal.domain.errors import CertificateLoadError, FailureCode
from tests.support.phase3_builders import (
    build_signature_appearance,
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
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QA"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "test@example.com"),
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
        signature_rect=build_signature_rect(page_index=0),
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
    appearance = build_signature_appearance(image_stamp_path=None)

    style = _build_stamp_style(
        appearance,
        stamp_text="Visible signature",
        stamp_background=None,
    )

    assert style.background is not None
