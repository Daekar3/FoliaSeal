from __future__ import annotations

from pathlib import Path

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


def test_main_phase2_evidence_collects_bundle_size_when_requested(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bundle_dir = tmp_path / "dist"
    bundle_dir.mkdir()
    (bundle_dir / "artifact.bin").write_bytes(b"z" * 1024 * 1024)

    __main__.main(
        [
            "phase2-evidence",
            "--collect-runtime-footprint",
            "--bundle-dir",
            str(bundle_dir),
        ]
    )

    output = capsys.readouterr().out
    assert "### Runtime footprint snapshot" in output
    assert "- Bundle size (one-dir): 1.00 MiB" in output


def test_main_phase2_evidence_measures_startup_command_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "pdf_signer.__main__.measure_startup_latency_ms",
        lambda command, timeout_seconds: 432.1,
    )

    __main__.main(
        [
            "phase2-evidence",
            "--measure-startup-command",
            "python3",
        ]
    )

    output = capsys.readouterr().out
    assert "- Startup latency: 432.10 ms" in output


def test_main_phase2_evidence_prefers_explicit_startup_ms_over_measured_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_if_called(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("measure_startup_latency_ms should not be called")

    monkeypatch.setattr("pdf_signer.__main__.measure_startup_latency_ms", fail_if_called)

    __main__.main(
        [
            "phase2-evidence",
            "--startup-ms",
            "111.0",
            "--measure-startup-command",
            "python3",
        ]
    )

    output = capsys.readouterr().out
    assert "- Startup latency: 111.00 ms" in output


def test_main_phase2_evidence_includes_runtime_validation_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    __main__.main(
        [
            "phase2-evidence",
            "--qa-passed-checks",
            "8",
            "--qa-total-checks",
            "9",
            "--qa-issue",
            "Selection mapping failed on one rotated sample.",
        ]
    )

    output = capsys.readouterr().out
    assert "### Runtime validation sweep" in output
    assert "Checklist status: 8/9 checks passed" in output
    assert "Selection mapping failed on one rotated sample." in output


def test_main_phase2_evidence_rejects_partial_runtime_validation_args() -> None:
    with pytest.raises(ValueError, match="must be provided together"):
        __main__.main(["phase2-evidence", "--qa-total-checks", "9"])
