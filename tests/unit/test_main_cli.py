from __future__ import annotations

from pathlib import Path

import pytest

from pdf_signer import __main__


def test_main_without_subcommand_prints_default_message(capsys: pytest.CaptureFixture[str]) -> None:
    __main__.main([])

    output = capsys.readouterr().out
    assert "FoliaSeal phase 0 skeleton ready" in output


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
        lambda command, timeout_seconds, ready_after_seconds: 432.1,
    )

    __main__.main(
        [
            "phase2-evidence",
            "--measure-startup-command",
            "python3",
            "--startup-ready-after-seconds",
            "0.75",
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


def test_main_phase2_evidence_derives_runtime_validation_from_checklist_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checklist_path = tmp_path / "checklist.md"
    checklist_path.write_text(
        "\n".join(
            [
                "- [x] Initial render succeeds on page 1.",
                "- [ ] Keyboard page navigation works.",
            ]
        ),
        encoding="utf-8",
    )

    __main__.main(
        [
            "phase2-evidence",
            "--qa-checklist-file",
            str(checklist_path),
        ]
    )

    output = capsys.readouterr().out
    assert "### Runtime validation sweep" in output
    assert "Checklist status: 1/2 checks passed" in output
    assert "Keyboard page navigation works." in output


def test_main_phase2_evidence_merges_extra_issue_notes_with_checklist_derived_summary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checklist_path = tmp_path / "checklist.md"
    checklist_path.write_text("- [x] Initial render succeeds on page 1.", encoding="utf-8")

    __main__.main(
        [
            "phase2-evidence",
            "--qa-checklist-file",
            str(checklist_path),
            "--qa-issue",
            "Observed transient zoom jitter at 300%.",
        ]
    )

    output = capsys.readouterr().out
    assert "Checklist status: 1/1 checks passed" in output
    assert "Observed transient zoom jitter at 300%." in output


def test_main_phase2_evidence_writes_markdown_file_when_requested(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output_file = tmp_path / "evidence" / "phase2_runtime.md"

    __main__.main(
        [
            "phase2-evidence",
            "--first-render-ms",
            "44.0",
            "--write-markdown-file",
            str(output_file),
        ]
    )

    output = capsys.readouterr().out
    assert "## Phase 2 runtime evidence" in output
    assert output_file.exists()
    written = output_file.read_text(encoding="utf-8")
    assert written.endswith("\n")
    assert "## Phase 2 runtime evidence" in written


def test_main_phase2_evidence_appends_qt_runtime_diagnostics_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "pdf_signer.__main__.QtRuntimeReadinessSnapshot.collect",
        lambda: __main__.QtRuntimeReadinessSnapshot(
            pyside6_available=True,
            qtpdf_available=False,
        ),
    )

    __main__.main(
        [
            "phase2-evidence",
            "--check-qt-runtime",
        ]
    )

    output = capsys.readouterr().out
    assert "### Qt runtime readiness" in output
    assert "- ✅ PySide6 import available" in output
    assert "- ⚠️ PySide6.QtPdf import available" in output
