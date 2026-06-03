from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from foliaseal import __main__


def test_main_without_subcommand_prints_default_message(capsys: pytest.CaptureFixture[str]) -> None:
    result = __main__.main([])

    output = capsys.readouterr().out
    assert result == 0
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
        "foliaseal.__main__.measure_startup_latency_ms",
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

    monkeypatch.setattr("foliaseal.__main__.measure_startup_latency_ms", fail_if_called)

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
        "foliaseal.__main__.QtRuntimeReadinessSnapshot.collect",
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


def test_main_phase2_viewer_harness_dispatches_to_qt_harness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def fake_run_phase2_viewer_harness(
        *,
        pdf_path: str,
        summary_json_path: str | None,
        evidence_command_path: str | None,
        checklist_results_path: str,
        checklist_template_path: str,
    ) -> None:
        captured["pdf_path"] = pdf_path
        captured["summary_json_path"] = summary_json_path
        captured["evidence_command_path"] = evidence_command_path
        captured["checklist_results_path"] = checklist_results_path
        captured["checklist_template_path"] = checklist_template_path

    monkeypatch.setattr(
        "foliaseal.__main__.run_phase2_viewer_harness",
        fake_run_phase2_viewer_harness,
    )

    __main__.main(
        [
            "phase2-viewer-harness",
            "--pdf-path",
            "/tmp/sample.pdf",
            "--summary-json-path",
            "/tmp/capture.json",
            "--evidence-command-path",
            "/tmp/evidence-command.sh",
        ]
    )

    assert captured == {
        "pdf_path": "/tmp/sample.pdf",
        "summary_json_path": "/tmp/capture.json",
        "evidence_command_path": "/tmp/evidence-command.sh",
        "checklist_results_path": "artifacts/phase2_manual_qa_results.md",
        "checklist_template_path": "docs/ExecPlans/phase2_manual_qa_checklist.md",
    }


def test_main_gui_dispatches_to_qt_app_launcher(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_launch_qt_app_frame(
        *,
        argv,
        initial_pdf_path,
    ) -> int:
        captured["argv"] = list(argv) if argv is not None else None
        captured["initial_pdf_path"] = initial_pdf_path
        return 0

    monkeypatch.setattr("foliaseal.__main__.launch_qt_app_frame", fake_launch_qt_app_frame)

    result = __main__.main(
        [
            "gui",
            "--pdf-path",
            "/tmp/sample.pdf",
        ]
    )

    assert result == 0
    assert captured == {
        "argv": ["gui", "--pdf-path", "/tmp/sample.pdf"],
        "initial_pdf_path": "/tmp/sample.pdf",
    }


def test_main_gui_uses_process_argv_when_called_without_explicit_argv(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    def fake_launch_qt_app_frame(
        *,
        argv,
        initial_pdf_path,
    ) -> int:
        captured["argv"] = list(argv) if argv is not None else None
        captured["initial_pdf_path"] = initial_pdf_path
        return 9

    monkeypatch.setattr("foliaseal.__main__.launch_qt_app_frame", fake_launch_qt_app_frame)
    monkeypatch.setattr(__main__.sys, "argv", ["foliaseal", "gui", "--pdf-path", "/tmp/live.pdf"])

    result = __main__.main()

    assert result == 9
    assert captured == {
        "argv": ["foliaseal", "gui", "--pdf-path", "/tmp/live.pdf"],
        "initial_pdf_path": "/tmp/live.pdf",
    }


def test_main_phase3_signing_preview_matrix_dispatches_to_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    class _FakeService:
        def run_preview_matrix(self, request):
            captured["pdf_path"] = request.pdf_path
            captured["certificate_path"] = request.certificate_path
            captured["passphrase"] = request.passphrase
            captured["scenario_manifest_path"] = request.scenario_manifest_path
            captured["artifacts_dir"] = request.artifacts_dir
            return {
                "artifacts_dir": request.artifacts_dir,
                "scenario_count": 1,
                "successful_scenario_count": 1,
            }

    monkeypatch.setattr(
        "foliaseal.__main__._build_phase3_evidence_service",
        lambda: _FakeService(),
    )

    __main__.main(
        [
            "phase3-signing-preview-matrix",
            "--pdf-path",
            "/tmp/sample.pdf",
            "--certificate-path",
            "/tmp/cert.p12",
            "--passphrase",
            "secret",
            "--scenario-manifest-path",
            "/tmp/manifest.json",
            "--artifacts-dir",
            "/tmp/artifacts",
        ]
    )

    assert captured == {
        "pdf_path": "/tmp/sample.pdf",
        "certificate_path": "/tmp/cert.p12",
        "passphrase": "secret",
        "scenario_manifest_path": "/tmp/manifest.json",
        "artifacts_dir": "/tmp/artifacts",
    }


def test_main_phase3_signing_acceptance_matrix_dispatches_to_runner(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured = {}

    class _FakeService:
        def run_signed_acceptance_matrix(self, request):
            captured["pdf_path"] = request.pdf_path
            captured["certificate_path"] = request.certificate_path
            captured["passphrase"] = request.passphrase
            captured["scenario_manifest_path"] = request.scenario_manifest_path
            captured["artifacts_dir"] = request.artifacts_dir
            return {
                "artifacts_dir": request.artifacts_dir,
                "scenario_count": 3,
                "successful_signing_run_count": 2,
            }

    monkeypatch.setattr(
        "foliaseal.__main__._build_phase3_evidence_service",
        lambda: _FakeService(),
    )

    __main__.main(
        [
            "phase3-signing-acceptance-matrix",
            "--pdf-path",
            "/tmp/sample.pdf",
            "--certificate-path",
            "/tmp/cert.p12",
            "--passphrase",
            "secret",
            "--scenario-manifest-path",
            "/tmp/manifest.json",
            "--artifacts-dir",
            "/tmp/artifacts",
        ]
    )

    assert captured == {
        "pdf_path": "/tmp/sample.pdf",
        "certificate_path": "/tmp/cert.p12",
        "passphrase": "secret",
        "scenario_manifest_path": "/tmp/manifest.json",
        "artifacts_dir": "/tmp/artifacts",
    }
    output = capsys.readouterr().out
    assert "Phase 3 signed acceptance matrix" in output
    assert "- scenarios executed: 3" in output
    assert "- successful signings: 2" in output


def test_main_phase3_signing_harness_dispatches_through_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}

    class _FakeService:
        def capture_harness(self, request):
            captured["pdf_path"] = request.pdf_path
            captured["certificate_path"] = request.certificate_path
            captured["passphrase"] = request.passphrase
            captured["summary_json_path"] = request.summary_json_path
            captured["checklist_results_path"] = request.checklist_results_path
            captured["checklist_template_path"] = request.checklist_template_path
            captured["artifacts_dir"] = request.artifacts_dir
            return object()

    monkeypatch.setattr(
        "foliaseal.__main__._build_phase3_evidence_service",
        lambda: _FakeService(),
    )

    __main__.main(
        [
            "phase3-signing-harness",
            "--pdf-path",
            "/tmp/sample.pdf",
            "--certificate-path",
            "/tmp/cert.p12",
            "--passphrase",
            "secret",
            "--summary-json-path",
            "/tmp/summary.json",
            "--checklist-results-path",
            "/tmp/results.md",
            "--checklist-template-path",
            "/tmp/template.md",
            "--artifacts-dir",
            "/tmp/artifacts",
        ]
    )

    assert captured == {
        "pdf_path": "/tmp/sample.pdf",
        "certificate_path": "/tmp/cert.p12",
        "passphrase": "secret",
        "summary_json_path": "/tmp/summary.json",
        "checklist_results_path": "/tmp/results.md",
        "checklist_template_path": "/tmp/template.md",
        "artifacts_dir": "/tmp/artifacts",
    }


def test_main_phase3_signed_acceptance_evidence_dispatches_to_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured = {}

    class _FakeCounters:
        scenario_count = 10
        successful_signing_run_count = 7

    class _FakeMatrixResult:
        name = "signed_acceptance_matrix"
        counters = _FakeCounters()

    class _FakeEvidence:
        summary_markdown_path = "/tmp/foliaseal-evidence/summary.md"
        matrix_results = (_FakeMatrixResult(),)

    class _FakeService:
        def run_signed_acceptance_evidence(self, request):
            captured["artifacts_root"] = str(request.artifacts_root)
            captured["summary_markdown_path"] = request.summary_markdown_path
            return _FakeEvidence()

    monkeypatch.setattr(
        "foliaseal.__main__._build_phase3_evidence_service",
        lambda: _FakeService(),
    )

    __main__.main(
        [
            "phase3-signing-acceptance-evidence",
            "--artifacts-root",
            "/tmp/foliaseal-evidence",
            "--summary-markdown-path",
            "/tmp/foliaseal-evidence/summary.md",
        ]
    )

    assert captured == {
        "artifacts_root": "/tmp/foliaseal-evidence",
        "summary_markdown_path": "/tmp/foliaseal-evidence/summary.md",
    }
    output = capsys.readouterr().out
    assert "Phase 3 signed acceptance evidence" in output
    assert "signed_acceptance_matrix: PASS (10 scenarios, 7 successful signings)" in output


def test_main_phase3_signing_harness_validate_dispatches_to_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured = {}

    class _FakeService:
        def validate_harness_capture(self, request):
            captured["summary_json_path"] = str(request.summary_json_path)
            return SimpleNamespace(
                acceptance_tier="full",
                gate_verdict="pass",
                passed=True,
                contract_version="phase3.v1",
                errors=(),
                warnings=(),
            )

    monkeypatch.setattr(
        "foliaseal.__main__._build_phase3_evidence_service",
        lambda: _FakeService(),
    )

    __main__.main(
        [
            "phase3-signing-harness-validate",
            "--summary-json-path",
            str(tmp_path / "summary.json"),
        ]
    )

    output = capsys.readouterr().out
    assert captured == {"summary_json_path": str(tmp_path / "summary.json")}
    assert "Phase 3 evidence contract" in output
    assert "- validation passed: yes" in output


def test_main_phase3_signing_harness_validate_raises_on_failed_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeService:
        def validate_harness_capture(self, request):
            return SimpleNamespace(
                acceptance_tier="partial",
                gate_verdict="fail",
                passed=False,
                contract_version="phase3.v1",
                errors=("missing required field",),
                warnings=(),
            )

    monkeypatch.setattr(
        "foliaseal.__main__._build_phase3_evidence_service",
        lambda: _FakeService(),
    )

    with pytest.raises(ValueError, match="failed evidence contract validation"):
        __main__.main(
            [
                "phase3-signing-harness-validate",
                "--summary-json-path",
                str(tmp_path / "summary.json"),
            ]
        )

    output = capsys.readouterr().out
    assert "- validation passed: no" in output
    assert "- errors: ['missing required field']" in output
