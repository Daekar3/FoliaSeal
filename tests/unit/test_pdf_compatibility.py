import pytest

from pdf_signer.application.pdf_compatibility import PdfCompatibilityError, PdfCompatibilityProfile


def test_accepts_versions_in_supported_open_range() -> None:
    profile = PdfCompatibilityProfile()

    profile.ensure_open_version_supported("1.4")
    profile.ensure_open_version_supported("1.7")
    profile.ensure_open_version_supported("2.0")


def test_rejects_versions_outside_supported_open_range() -> None:
    profile = PdfCompatibilityProfile()

    with pytest.raises(PdfCompatibilityError):
        profile.ensure_open_version_supported("1.3")

    with pytest.raises(PdfCompatibilityError):
        profile.ensure_open_version_supported("2.1")


def test_rejects_non_finite_or_non_numeric_versions() -> None:
    profile = PdfCompatibilityProfile()

    with pytest.raises(PdfCompatibilityError):
        profile.ensure_open_version_supported("nan")

    with pytest.raises(PdfCompatibilityError):
        profile.ensure_open_version_supported("not-a-version")


def test_rejects_output_version_change_when_preservation_enabled() -> None:
    profile = PdfCompatibilityProfile(preserve_input_version=True)

    with pytest.raises(PdfCompatibilityError):
        profile.ensure_output_version_policy("1.7", "2.0")


def test_build_standards_summary_contains_required_fields() -> None:
    profile = PdfCompatibilityProfile()

    summary = profile.build_standards_summary(
        input_pdf_version="1.7",
        output_pdf_version="1.7",
        signature_subfilter="adbe.pkcs7.detached",
        timestamp_present=True,
    )

    assert "Opened as PDF 1.7" in summary
    assert "saved incrementally as PDF 1.7" in summary
    assert "subfilter=adbe.pkcs7.detached" in summary
    assert "timestamped" in summary
