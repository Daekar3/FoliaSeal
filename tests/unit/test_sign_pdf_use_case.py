from dataclasses import dataclass
from pathlib import Path

from pdf_signer.application.sign_pdf_use_case import SignPdfUseCase
from pdf_signer.domain.errors import FailureCode
from pdf_signer.domain.models import SigningOutput, SigningRequest, VerificationSummary


@dataclass
class StubInspector:
    version: str = "1.7"

    def get_pdf_version(self, input_pdf_path: str) -> str:
        return self.version


@dataclass
class StubCertificateLoader:
    called: bool = False

    def validate(self, certificate_path: str, passphrase: str) -> None:
        self.called = True


@dataclass
class StubSigner:
    output: SigningOutput

    def sign(self, request: SigningRequest) -> SigningOutput:
        return self.output


@dataclass
class StubVerifier:
    summary: VerificationSummary

    def verify(self, output_pdf_path: str) -> VerificationSummary:
        return self.summary


def _request(tmp_path: Path) -> SigningRequest:
    return SigningRequest(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
    )


def test_sign_use_case_success_returns_standards_fields(tmp_path: Path) -> None:
    request = _request(tmp_path)
    output = SigningOutput(
        output_bytes=b"signed-pdf",
        output_pdf_version="1.7",
        signature_subfilter="adbe.pkcs7.detached",
        timestamp_present=True,
    )
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(output=output),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.failure_code is None
    assert result.output_pdf_version == "1.7"
    assert result.signature_subfilter == "adbe.pkcs7.detached"
    assert result.timestamp_present is True
    assert result.standards_summary is not None
    assert (tmp_path / "output.pdf").read_bytes() == b"signed-pdf"


def test_sign_use_case_fails_when_timestamp_required_but_missing(tmp_path: Path) -> None:
    request = _request(tmp_path)
    output = SigningOutput(
        output_bytes=b"signed-pdf",
        output_pdf_version="1.7",
        signature_subfilter="adbe.pkcs7.detached",
        timestamp_present=False,
    )
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(output=output),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=False)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.TIMESTAMP_REQUIRED_BUT_MISSING


def test_sign_use_case_rejects_unsupported_input_version(tmp_path: Path) -> None:
    request = _request(tmp_path)
    output = SigningOutput(
        output_bytes=b"signed-pdf",
        output_pdf_version="1.3",
        signature_subfilter="adbe.pkcs7.detached",
        timestamp_present=True,
    )
    use_case = SignPdfUseCase(
        inspector=StubInspector(version="1.3"),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(output=output),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.INPUT_PDF_INVALID
