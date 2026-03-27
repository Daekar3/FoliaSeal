from dataclasses import dataclass
from pathlib import Path

import pytest

from pdf_signer.application.sign_pdf_use_case import SignPdfUseCase
from pdf_signer.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    FailureCode,
    TsaUnavailableError,
)
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


@dataclass
class RaisingSigner:
    error: Exception

    def sign(self, request: SigningRequest) -> SigningOutput:
        raise self.error


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


def test_sign_use_case_rejects_equal_input_and_output_paths(tmp_path: Path) -> None:
    request = SigningRequest(
        input_pdf_path=str(tmp_path / "same.pdf"),
        output_pdf_path=str(tmp_path / "same.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
    )
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"signed-pdf",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.OUTPUT_PATH_INVALID


def test_sign_use_case_rejects_paths_pointing_to_same_file_via_relative_path(
    tmp_path: Path,
) -> None:
    request = SigningRequest(
        input_pdf_path=str(tmp_path / "same.pdf"),
        output_pdf_path=str(tmp_path / "nested" / ".." / "same.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
    )
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"signed-pdf",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.OUTPUT_PATH_INVALID


def test_sign_use_case_maps_path_normalization_errors_to_stable_failure_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"signed-pdf",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    def _raise_runtime_error(_input: str, _output: str) -> bool:
        raise RuntimeError("Could not determine home directory")

    monkeypatch.setattr(use_case, "_paths_conflict", _raise_runtime_error)

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.UNEXPECTED_INTERNAL_ERROR


def test_sign_use_case_returns_post_verify_failed_when_timestamp_not_found(tmp_path: Path) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"signed-pdf",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=False)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.POST_VERIFY_FAILED


def test_sign_use_case_allows_missing_timestamp_when_optional(tmp_path: Path) -> None:
    request = SigningRequest(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=False,
    )
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"signed-pdf",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=False,
            )
        ),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=False)
        ),
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.timestamp_present is False


def test_sign_use_case_maps_value_error_to_pdf_signing_failed(tmp_path: Path) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=RaisingSigner(error=ValueError("signing failed")),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PDF_SIGNING_FAILED


def test_sign_use_case_maps_wrong_pkcs12_password(tmp_path: Path) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=RaisingSigner(error=CertificateWrongPasswordError("bad passphrase")),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PKCS12_WRONG_PASSWORD


def test_sign_use_case_maps_pkcs12_load_failures(tmp_path: Path) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=RaisingSigner(error=CertificateLoadError("broken pkcs12")),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PKCS12_LOAD_FAILED


def test_sign_use_case_maps_tsa_unreachable(tmp_path: Path) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=RaisingSigner(error=TsaUnavailableError("tsa timeout")),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.TSA_UNREACHABLE


def test_sign_use_case_maps_unexpected_errors_to_unexpected_internal_error(tmp_path: Path) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=RaisingSigner(error=RuntimeError("boom")),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.UNEXPECTED_INTERNAL_ERROR


def test_sign_use_case_maps_oserror_during_atomic_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = _request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"signed-pdf",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=StubVerifier(
            summary=VerificationSummary(signature_count=1, timestamp_present=True)
        ),
    )
    def _raise_oserror(_output_path: str, _output_bytes: bytes) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(SignPdfUseCase, "_write_atomically", staticmethod(_raise_oserror))

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.ATOMIC_WRITE_FAILED
