import pytest

from foliaseal.domain.models import SigningRequest


def _request(*, tsa_url: str, timestamp_required: bool) -> SigningRequest:
    return SigningRequest(
        input_pdf_path="/tmp/input.pdf",
        output_pdf_path="/tmp/output.pdf",
        certificate_path="/tmp/certificate.p12",
        passphrase="secret",
        tsa_url=tsa_url,
        timestamp_required=timestamp_required,
    )


def test_signing_request_allows_empty_tsa_url_for_offline_signing() -> None:
    request = _request(tsa_url="", timestamp_required=False)

    assert request.tsa_url == ""
    assert request.timestamp_required is False


def test_signing_request_requires_tsa_url_when_timestamping_is_required() -> None:
    with pytest.raises(ValueError, match="tsa_url must be a non-empty string"):
        _request(tsa_url="", timestamp_required=True)
