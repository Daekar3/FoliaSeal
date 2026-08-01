from pathlib import Path

from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.presentation.qt.phase3_pdf_signature_snapshotter import (
    Phase3PdfSignatureSnapshotter,
)


def test_missing_signed_pdf_returns_safe_evidence_results(tmp_path: Path) -> None:
    snapshotter = Phase3PdfSignatureSnapshotter()
    missing_pdf = tmp_path / "missing.pdf"

    assert snapshotter.count_embedded_signatures(missing_pdf) is None
    assert snapshotter.snapshot_output_signature(missing_pdf) is None
    assert snapshotter.snapshot_visible_signature_appearance(missing_pdf) == {
        "error": "[Errno 2] No such file or directory: "
        f"'{missing_pdf}'"
    }
    verification = snapshotter.snapshot_output_verification(missing_pdf)
    assert verification is not None
    assert verification["cryptographic_validation_passed"] is False
    assert verification["signature_count"] is None
    assert "No such file or directory" in verification["error"]


def test_unsigned_pdf_reports_an_explicit_verification_failure(tmp_path: Path) -> None:
    unsigned_pdf = tmp_path / "unsigned.pdf"
    writer = PdfFileWriter()
    empty_stream = writer.add_object(generic.StreamObject(stream_data=b""))
    writer.insert_page(
        PageObject(
            contents=empty_stream,
            media_box=(0, 0, 100, 100),
        )
    )
    with unsigned_pdf.open("wb") as handle:
        writer.write(handle)

    snapshot = Phase3PdfSignatureSnapshotter().snapshot_output_verification(unsigned_pdf)

    assert snapshot == {
        "cryptographic_validation_passed": False,
        "signature_count": 0,
        "docmdp_permission": None,
        "certification_restricted": False,
        "restriction_reason": None,
        "error": "No embedded signature fields were found in the output PDF.",
    }


def test_malformed_pdf_appearance_is_reported_without_raising(tmp_path: Path) -> None:
    malformed_pdf = tmp_path / "malformed.pdf"
    malformed_pdf.write_bytes(b"not a PDF")

    snapshot = Phase3PdfSignatureSnapshotter().snapshot_visible_signature_appearance(
        malformed_pdf
    )

    assert snapshot is not None
    assert "error" in snapshot
