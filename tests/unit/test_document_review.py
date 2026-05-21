from foliaseal.application.document_review import (
    PyHankoDocumentReviewInspector,
    summarize_document_review,
)
from foliaseal.infra.certification import CertificationPolicyResult


def test_summarize_document_review_for_unsigned_pdf() -> None:
    summary = summarize_document_review(signature_count=0)

    assert summary.headline == "No signatures found"
    assert "does not currently contain embedded signatures" in summary.detail
    assert "place and sign a new visible approval signature" in summary.detail
    assert summary.certification_restricted is False


def test_summarize_document_review_for_verified_signed_pdf() -> None:
    summary = summarize_document_review(
        signature_count=2,
        signer_subject="CN=Alice Example",
        cryptographic_validation_passed=True,
        docmdp_permission="fill_forms",
    )

    assert summary.headline == "Signature review"
    assert "Found 2 embedded signatures." in summary.detail
    assert "Latest signer: CN=Alice Example." in summary.detail
    assert "Latest signature verified locally." in summary.detail
    assert "Certification permits form filling and additional signing changes." in summary.detail


def test_summarize_document_review_for_certification_restricted_pdf() -> None:
    summary = summarize_document_review(
        signature_count=1,
        signer_subject="CN=Alice Example",
        cryptographic_validation_passed=False,
        certification_restricted=True,
        restriction_reason="Certification-restricted PDF: DocMDP NO_CHANGES forbids signing.",
        docmdp_permission="no_changes",
    )

    assert summary.headline == "Signature review: restricted"
    assert "Latest signature needs attention: local verification failed." in summary.detail
    assert "Further changes may be blocked" in summary.detail
    assert "DocMDP NO_CHANGES forbids signing" in summary.detail
    assert summary.certification_restricted is True


def test_document_review_inspector_reports_missing_file_as_unavailable(tmp_path) -> None:
    summary = PyHankoDocumentReviewInspector().inspect(str(tmp_path / "missing.pdf"))

    assert summary.headline == "Review unavailable"
    assert "file not found" in summary.detail
    assert summary.signature_count is None


def test_document_review_inspector_reports_unsigned_pdf(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "unsigned.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n")

    class _FakeReader:
        def __init__(self, _handle) -> None:
            self.embedded_signatures = []

    monkeypatch.setattr(
        "foliaseal.application.document_review.PdfFileReader",
        _FakeReader,
    )
    monkeypatch.setattr(
        "foliaseal.application.document_review.inspect_pdf_certification_reader",
        lambda _reader: CertificationPolicyResult(
            docmdp_permission=None,
            certification_restricted=False,
            restriction_reason=None,
        ),
    )

    summary = PyHankoDocumentReviewInspector().inspect(str(pdf_path))

    assert summary.headline == "No signatures found"
    assert summary.signature_count == 0
    assert "place and sign a new visible approval signature" in summary.detail


def test_document_review_inspector_reports_signed_restricted_pdf(monkeypatch, tmp_path) -> None:
    pdf_path = tmp_path / "signed.pdf"
    pdf_path.write_bytes(b"%PDF-1.7\n")

    class _FakeSubject:
        human_friendly = "CN=Alice Example"

    class _FakeSignerCert:
        subject = _FakeSubject()

    class _FakeSignature:
        signer_cert = _FakeSignerCert()

    class _FakeReader:
        def __init__(self, _handle) -> None:
            self.embedded_signatures = [_FakeSignature()]

    class _FakeStatus:
        intact = True
        valid = True

    monkeypatch.setattr(
        "foliaseal.application.document_review.PdfFileReader",
        _FakeReader,
    )
    monkeypatch.setattr(
        "foliaseal.application.document_review.inspect_pdf_certification_reader",
        lambda _reader: CertificationPolicyResult(
            docmdp_permission="no_changes",
            certification_restricted=True,
            restriction_reason="Certification-restricted PDF: DocMDP NO_CHANGES forbids signing.",
        ),
    )
    monkeypatch.setattr(
        "foliaseal.application.document_review.validation.validate_pdf_signature",
        lambda signature, signer_validation_context: _FakeStatus(),
    )
    monkeypatch.setattr(
        "foliaseal.application.document_review.ValidationContext",
        lambda trust_roots: object(),
    )

    summary = PyHankoDocumentReviewInspector().inspect(str(pdf_path))

    assert summary.headline == "Signature review: restricted"
    assert summary.signature_count == 1
    assert summary.signer_subject == "CN=Alice Example"
    assert "Latest signature verified locally." in summary.detail
    assert "DocMDP NO_CHANGES forbids signing" in summary.detail
