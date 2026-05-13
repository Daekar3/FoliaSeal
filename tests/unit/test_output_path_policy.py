from pathlib import Path

from foliaseal.application.output_path_policy import suggest_signed_output_path


def test_suggest_signed_output_path_uses_input_pdf_stem_for_new_draft(
    tmp_path: Path,
) -> None:
    assert suggest_signed_output_path(
        input_pdf_path=tmp_path / "source" / "contract.pdf",
        default_output_directory=tmp_path / "signed",
    ) == tmp_path / "signed" / "contract-signed.pdf"


def test_suggest_signed_output_path_reuses_current_output_filename(
    tmp_path: Path,
) -> None:
    assert suggest_signed_output_path(
        input_pdf_path=tmp_path / "source" / "contract.pdf",
        default_output_directory=tmp_path / "signed",
        current_output_path=tmp_path / "other" / "custom-name.pdf",
    ) == tmp_path / "signed" / "custom-name.pdf"


def test_suggest_signed_output_path_falls_back_when_input_has_no_stem(
    tmp_path: Path,
) -> None:
    assert suggest_signed_output_path(
        input_pdf_path="",
        default_output_directory=tmp_path / "signed",
    ) == tmp_path / "signed" / "signed-signed.pdf"
