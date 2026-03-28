from __future__ import annotations

import pytest

from pdf_signer import __main__


def test_main_without_subcommand_prints_default_message(capsys: pytest.CaptureFixture[str]) -> None:
    __main__.main([])

    output = capsys.readouterr().out
    assert "pdf-signer phase 0 skeleton ready" in output


def test_main_phase2_evidence_prints_markdown(capsys: pytest.CaptureFixture[str]) -> None:
    __main__.main(
        [
            "phase2-evidence",
            "--first-render-ms",
            "42.5",
            "--navigation-ms",
            "21.0",
            "--navigation-ms",
            "23.0",
            "--minimum-navigation-samples",
            "2",
        ]
    )

    output = capsys.readouterr().out
    assert "## Phase 2 runtime evidence" in output
    assert "- First render: 42.50 ms" in output
    assert "- Navigation samples: 2" in output
    assert "- ✅ Navigation sample count (2/2)" in output


def test_main_phase2_evidence_rejects_negative_timing_values() -> None:
    with pytest.raises(ValueError, match="greater than or equal to zero"):
        __main__.main(["phase2-evidence", "--navigation-ms", "-1"])


def test_main_phase2_evidence_rejects_invalid_runtime_footprint_values() -> None:
    with pytest.raises(ValueError, match="idle_memory_mib"):
        __main__.main(["phase2-evidence", "--idle-memory-mib", "nan"])
