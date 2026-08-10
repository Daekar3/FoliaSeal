from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.application.sign_pdf_use_case import (
    SigningBackendRequest,
    SignPdfUseCase,
)
from foliaseal.domain.errors import (
    CertificateLoadError,
    CertificateWrongPasswordError,
    FailureCode,
    TimestampTrustMaterialError,
    TsaUnavailableError,
)
from foliaseal.domain.models import (
    DocumentOperationType,
    RevisionStrategy,
    SignatureFieldKey,
    SignatureStampPosition,
    SigningOutput,
    SigningRequest,
    TimestampTrustPolicy,
    VerificationSummary,
)
from foliaseal.infra.certification import CertificationPolicyResult
from tests.support.signing_builders import (
    build_signature_appearance,
    build_signing_request,
)


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
    called: bool = False
    last_request: object | None = None

    def sign(self, request) -> SigningOutput:
        self.called = True
        self.last_request = request
        return self.output


@dataclass
class StubVerifier:
    summary: VerificationSummary
    last_trust_policy: TimestampTrustPolicy | None = None
    verified_paths: list[str] = field(default_factory=list)

    def verify(
        self,
        output_pdf_path: str,
        *,
        trust_policy: TimestampTrustPolicy | None = None,
    ) -> VerificationSummary:
        self.last_trust_policy = trust_policy
        self.verified_paths.append(output_pdf_path)
        return self.summary


@dataclass
class StubCertificationInspector:
    result: CertificationPolicyResult
    called: bool = False
    last_input_pdf_path: str | None = None

    def inspect(self, input_pdf_path: str) -> CertificationPolicyResult:
        self.called = True
        self.last_input_pdf_path = input_pdf_path
        return self.result


@dataclass
class RaisingSigner:
    error: Exception

    def sign(self, request: SigningRequest) -> SigningOutput:
        raise self.error


@dataclass
class RaisingVerifier:
    error: Exception

    def verify(
        self,
        output_pdf_path: str,
        *,
        trust_policy: TimestampTrustPolicy | None = None,
    ) -> VerificationSummary:
        raise self.error


def _request(tmp_path: Path) -> SigningRequest:
    return build_signing_request(tmp_path)


def _write_test_pdf(path: Path) -> None:
    writer = PdfFileWriter()
    empty_stream = writer.add_object(generic.StreamObject(stream_data=b""))
    writer.insert_page(PageObject(contents=empty_stream, media_box=(0, 0, 612, 792)))
    with path.open("wb") as handle:
        writer.write(handle)


def test_sign_use_case_success_returns_standards_fields(tmp_path: Path) -> None:
    request = build_signing_request(
        tmp_path,
        signature_appearance=build_signature_appearance(
            image_stamp_path="/tmp/stamp.png",
        ),
    )
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
    assert result.docmdp_permission is None
    assert result.certification_restricted is False
    assert result.operation_type == DocumentOperationType.SIGN
    assert result.revision_strategy == RevisionStrategy.INCREMENTAL
    assert result.standards_summary is not None
    assert (tmp_path / "output.pdf").read_bytes() == b"signed-pdf"
    assert use_case.verifier.verified_paths
    assert Path(use_case.verifier.verified_paths[0]) != tmp_path / "output.pdf"
    assert not list(tmp_path.glob(".output.pdf.*.tmp"))
    assert use_case.signer.called is True
    assert isinstance(use_case.signer.last_request, SigningBackendRequest)
    assert use_case.signer.last_request.signature_appearance is not None
    assert use_case.signer.last_request.signature_appearance.datetime_format == "%Y-%m-%d %H:%M"
    assert use_case.signer.last_request.signature_appearance.show_field_names is False
    assert (
        use_case.signer.last_request.signature_appearance.stamp_position
        == SignatureStampPosition.LEFT
    )
    assert (
        use_case.signer.last_request.signature_appearance.image_stamp_path
        == "/tmp/stamp.png"
    )
    assert len(use_case.signer.last_request.signature_appearance.field_bindings) == 8
    assert (
        use_case.signer.last_request.signature_appearance.field_bindings[0].field_key
        == SignatureFieldKey.DISTINGUISHED_NAME
    )


def test_sign_use_case_blocks_certification_restricted_inputs_before_signing(
    tmp_path: Path,
) -> None:
    _write_test_pdf(tmp_path / "input.pdf")
    request = build_signing_request(tmp_path)
    request = replace(request, timestamp_required=False)
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
        certification_inspector=StubCertificationInspector(
            result=CertificationPolicyResult(
                docmdp_permission="no_changes",
                certification_restricted=True,
                restriction_reason=(
                    "Certification-restricted PDF: DocMDP NO_CHANGES forbids signing."
                ),
            )
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PDF_CERTIFICATION_RESTRICTS_SIGNING
    assert result.docmdp_permission == "no_changes"
    assert result.certification_restricted is True
    assert result.restriction_reason == (
        "Certification-restricted PDF: DocMDP NO_CHANGES forbids signing."
    )
    assert "forbids signing" in result.message
    assert use_case.signer.called is False
    assert use_case.certificate_loader.called is False


def test_sign_use_case_allows_certified_documents_when_policy_permits(
    tmp_path: Path,
) -> None:
    _write_test_pdf(tmp_path / "input.pdf")
    request = build_signing_request(tmp_path)
    request = replace(request, timestamp_required=False)
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
        certification_inspector=StubCertificationInspector(
            result=CertificationPolicyResult(
                docmdp_permission="fill_forms",
                certification_restricted=False,
                restriction_reason=None,
            )
        ),
    )

    result = use_case.execute(request)

    assert result.success is True
    assert result.docmdp_permission == "fill_forms"
    assert result.certification_restricted is False
    assert use_case.signer.called is True
    assert use_case.certificate_loader.called is True


def test_sign_use_case_passes_timestamp_trust_policy_to_verifier(
    tmp_path: Path,
) -> None:
    trust_policy = TimestampTrustPolicy(
        use_system_store=False,
        extra_ca_bundle_path="/tmp/tsa-root.pem",
        revocation_mode="soft-fail",
    )
    request = build_signing_request(tmp_path, trust_policy=trust_policy)
    verifier = StubVerifier(
        summary=VerificationSummary(
            signature_count=1,
            timestamp_present=True,
            timestamp_cryptographically_valid=True,
            tsa_chain_trusted=True,
        )
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
        verifier=verifier,
    )

    result = use_case.execute(request)

    assert result.success is True
    assert verifier.last_trust_policy == trust_policy
    assert result.timestamp_cryptographically_valid is True
    assert result.tsa_chain_trusted is True


def test_sign_use_case_fails_when_timestamp_trust_chain_is_untrusted(
    tmp_path: Path,
) -> None:
    trust_policy = TimestampTrustPolicy(
        use_system_store=False,
        extra_ca_bundle_path="/tmp/tsa-root.pem",
        revocation_mode="soft-fail",
    )
    request = build_signing_request(tmp_path, trust_policy=trust_policy)
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
            summary=VerificationSummary(
                signature_count=1,
                timestamp_present=True,
                timestamp_cryptographically_valid=True,
                tsa_chain_trusted=False,
                timestamp_validation_error="The TSA certificate is untrusted.",
            )
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.TIMESTAMP_TRUST_FAILED
    assert result.timestamp_present is True
    assert result.timestamp_cryptographically_valid is True
    assert result.tsa_chain_trusted is False
    assert result.timestamp_validation_error == "The TSA certificate is untrusted."


def test_sign_use_case_maps_timestamp_trust_material_errors(
    tmp_path: Path,
) -> None:
    request = build_signing_request(
        tmp_path,
        trust_policy=TimestampTrustPolicy(
            use_system_store=False,
            extra_ca_bundle_path="/tmp/missing-tsa-root.pem",
            revocation_mode="soft-fail",
        ),
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
        verifier=RaisingVerifier(
            error=TimestampTrustMaterialError("Timestamp trust bundle not found.")
        ),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.TIMESTAMP_TRUST_MATERIAL_INVALID


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
    request = build_signing_request(
        tmp_path,
        input_name="same.pdf",
        output_name="same.pdf",
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


def test_sign_use_case_allows_explicitly_authorized_source_replacement(tmp_path: Path) -> None:
    request = replace(
        build_signing_request(
            tmp_path,
            input_name="same.pdf",
            output_name="same.pdf",
        ),
        allow_source_overwrite=True,
    )
    source = Path(request.input_pdf_path)
    _write_test_pdf(source)
    verifier = StubVerifier(summary=VerificationSummary(signature_count=1, timestamp_present=True))
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"verified-replacement",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=verifier,
    )

    result = use_case.execute(request)

    assert result.success is True
    assert source.read_bytes() == b"verified-replacement"
    assert len(verifier.verified_paths) == 1
    assert Path(verifier.verified_paths[0]).name.startswith(".same.pdf.")


def test_sign_use_case_rejects_paths_pointing_to_same_file_via_relative_path(
    tmp_path: Path,
) -> None:
    request = build_signing_request(
        tmp_path,
        input_name="same.pdf",
        output_name="nested/../same.pdf",
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


def test_sign_use_case_allows_invisible_signing_requests(tmp_path: Path) -> None:
    request = SigningRequest(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
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

    assert result.success is True
    assert isinstance(use_case.signer.last_request, SigningBackendRequest)
    assert use_case.signer.last_request.signature_appearance is None


def test_sign_use_case_rejects_partial_visible_signature_settings(
    tmp_path: Path,
) -> None:
    request = SigningRequest(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        signature_rect=build_signing_request(tmp_path).signature_rect,
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
    assert result.failure_code == FailureCode.SIGNATURE_RECT_INVALID
    assert use_case.signer.called is False


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


def test_sign_use_case_preserves_existing_destination_when_verification_fails(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    destination = Path(request.output_pdf_path)
    destination.write_bytes(b"previous-output")
    use_case = SignPdfUseCase(
        inspector=StubInspector(),
        certificate_loader=StubCertificateLoader(),
        signer=StubSigner(
            output=SigningOutput(
                output_bytes=b"unverified-output",
                output_pdf_version="1.7",
                signature_subfilter="adbe.pkcs7.detached",
                timestamp_present=True,
            )
        ),
        verifier=RaisingVerifier(error=ValueError("verification failed")),
    )

    result = use_case.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.PDF_SIGNING_FAILED
    assert destination.read_bytes() == b"previous-output"
    assert not list(tmp_path.glob(".output.pdf.*.tmp"))
