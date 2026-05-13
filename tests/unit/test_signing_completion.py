from pathlib import Path

from foliaseal.application.signing_completion import format_signing_completion_message
from foliaseal.domain.models import SigningResult


def test_format_signing_completion_includes_saved_path_and_standards_summary(
    tmp_path: Path,
) -> None:
    message = format_signing_completion_message(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            output_pdf_version="1.7",
            signature_subfilter="adbe.pkcs7.detached",
            timestamp_present=False,
            standards_summary="PDF 1.7, detached signature, no timestamp.",
        ),
        tmp_path / "signed" / "contract-signed.pdf",
    )

    assert "Signing completed successfully." in message
    assert f"Saved to: {tmp_path / 'signed' / 'contract-signed.pdf'}" in message
    assert "Verified locally: PDF 1.7, detached signature, no timestamp." in message
    assert "No timestamp token was found" in message


def test_format_signing_completion_does_not_overstate_unknown_trust(
    tmp_path: Path,
) -> None:
    message = format_signing_completion_message(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=True,
            timestamp_cryptographically_valid=None,
            tsa_chain_trusted=None,
        ),
        tmp_path / "signed.pdf",
    )

    assert "Timestamp token is present." in message
    assert "Timestamp trust was not evaluated locally." in message
    assert "trusted" not in message.lower()


def test_format_signing_completion_surfaces_timestamp_trust_failure(
    tmp_path: Path,
) -> None:
    message = format_signing_completion_message(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=True,
            timestamp_cryptographically_valid=False,
            tsa_chain_trusted=False,
            timestamp_validation_error="TSA certificate is not trusted.",
        ),
        tmp_path / "signed.pdf",
    )

    assert "Timestamp trust needs attention: TSA certificate is not trusted." in message


def test_format_signing_completion_warns_when_future_signatures_may_be_blocked(
    tmp_path: Path,
) -> None:
    message = format_signing_completion_message(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            certification_restricted=True,
            restriction_reason="Document certification allows no changes.",
        ),
        tmp_path / "signed.pdf",
    )

    assert "Adding another signature may be blocked" in message
    assert "Document certification allows no changes." in message
