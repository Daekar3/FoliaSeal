from pathlib import Path

from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
from foliaseal.domain.errors import FailureCode
from tests.support.phase3_builders import build_signing_request


def test_phase3_signing_executor_writes_output_pdf(tmp_path: Path) -> None:
    input_pdf = tmp_path / "input.pdf"
    input_pdf.write_bytes(b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n")
    (tmp_path / "output.pdf").write_bytes(b"")
    request = build_signing_request(tmp_path)

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is True
    assert result.failure_code is None
    assert (tmp_path / "output.pdf").read_bytes() == input_pdf.read_bytes()
    assert result.output_pdf_version == "1.7"
    assert result.timestamp_present is True


def test_phase3_signing_executor_fails_for_missing_input_pdf(tmp_path: Path) -> None:
    request = build_signing_request(tmp_path)

    executor = build_phase3_signing_executor()
    result = executor.execute(request)

    assert result.success is False
    assert result.failure_code == FailureCode.INPUT_PDF_INVALID
