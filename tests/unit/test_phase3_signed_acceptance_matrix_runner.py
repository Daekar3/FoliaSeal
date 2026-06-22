from __future__ import annotations

import json
from pathlib import Path

import foliaseal.presentation.qt.phase3_signed_acceptance_matrix_runner as runner_module
from foliaseal.presentation.qt.phase3_signed_acceptance_matrix_runner import (
    Phase3SignedAcceptanceMatrixRunner,
)


class _FakeApplication:
    _instance = None

    def __init__(self, *_args) -> None:
        type(self)._instance = self
        self.process_events_calls = 0

    @classmethod
    def instance(cls):
        return cls._instance

    def processEvents(self) -> None:
        self.process_events_calls += 1


class _FakeWindow:
    def __init__(self) -> None:
        self.title = None
        self.size = None
        self.central_widget = None
        self.shown = False
        self.closed = False

    def setWindowTitle(self, title: str) -> None:
        self.title = title

    def resize(self, width: int, height: int) -> None:
        self.size = (width, height)

    def setCentralWidget(self, widget) -> None:
        self.central_widget = widget

    def show(self) -> None:
        self.shown = True

    def close(self) -> None:
        self.closed = True


class _FakeBindings:
    q_application = _FakeApplication
    q_main_window = _FakeWindow


class _FakeShell:
    pass


class _FakeWorkspace:
    def __init__(self) -> None:
        self.refresh_calls = 0

    def refresh_viewer(self) -> None:
        self.refresh_calls += 1


class _FakeBackend:
    class _Diagnostic:
        available = True
        message = ""

    def diagnostics(self):
        return self._Diagnostic()


def _runner(
    *,
    manifest: dict[str, object],
    scenario_executor,
    expectation_result: tuple[bool, list[str]] = (True, []),
    build_dummy_timestamper=None,
    build_signing_executor=None,
    build_workspace=None,
) -> Phase3SignedAcceptanceMatrixRunner:
    return Phase3SignedAcceptanceMatrixRunner(
        load_qt_harness_bindings=lambda: _FakeBindings(),
        load_preview_matrix_manifest=lambda _path: manifest,
        build_phase3_signing_executor=build_signing_executor
        or (lambda **kwargs: {"executor": kwargs}),
        build_dummy_timestamper=build_dummy_timestamper or (lambda: object()),
        load_page_count=lambda **_kwargs: 1,
        build_qt_signing_shell=lambda **_kwargs: _FakeShell(),
        build_workspace=build_workspace or (lambda **_kwargs: _FakeWorkspace()),
        execute_signed_acceptance_scenario=scenario_executor,
        preview_matrix_error_result=lambda **kwargs: {
            "name": kwargs["scenario"]["name"],
            "error": str(kwargs["error"]),
            "error_type": type(kwargs["error"]).__name__,
        },
        signed_matrix_diagnostic_summary=lambda results: {
            "successful_signing_run_count": sum(
                1
                for item in results
                if isinstance(item.get("signing_result"), dict)
                and item["signing_result"].get("success") is True
            ),
            "matched_expected_intentional_rejection_count": 0,
            "expected_outcome_mismatch_count": 0,
            "cryptographic_validation_failure_count": 0,
            "preview_output_comparison_failure_count": 0,
            "annotation_rect_mismatch_count": 0,
        },
        evaluate_signed_matrix_acceptance_expectations=lambda **_kwargs: expectation_result,
        jsonable_capture=lambda payload: payload,
    )


def test_signed_acceptance_matrix_runner_writes_summary_and_expectation_fields(
    tmp_path: Path, monkeypatch
) -> None:
    source_pdf = tmp_path / "fixture.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% fixture\n")
    artifacts_dir = tmp_path / "artifacts"
    dummy_calls: list[str] = []
    executor_calls: list[dict[str, object]] = []
    workspace_calls: list[dict[str, object]] = []
    workspace = _FakeWorkspace()

    monkeypatch.setattr(runner_module, "QtPdfRenderBackend", _FakeBackend)

    runner = _runner(
        manifest={
            "timestamping_mode": "dummy",
            "acceptance_expectations": {"scenario_count": 2},
            "scenarios": [{"name": "Scenario A"}, {"name": "Scenario B"}],
        },
        scenario_executor=lambda **kwargs: {
            "name": kwargs["scenario"]["name"],
            "signing_result": {"success": kwargs["scenario"]["name"] == "Scenario A"},
        },
        expectation_result=(False, ["expected mismatch"]),
        build_dummy_timestamper=lambda: dummy_calls.append("dummy") or object(),
        build_signing_executor=lambda **kwargs: executor_calls.append(kwargs) or {"executor": True},
        build_workspace=lambda **kwargs: workspace_calls.append(kwargs) or workspace,
    )

    summary = runner.run(
        pdf_path=str(source_pdf),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        scenario_manifest_path=str(tmp_path / "manifest.json"),
        artifacts_dir=str(artifacts_dir),
    )

    summary_path = artifacts_dir / "summary.json"
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["timestamping_mode"] == "dummy"
    assert payload["acceptance_expectations"] == {"scenario_count": 2}
    assert payload["acceptance_expectations_passed"] is False
    assert payload["acceptance_expectation_errors"] == ["expected mismatch"]
    assert payload["successful_scenario_count"] == 1
    assert payload["successful_signing_run_count"] == 1
    assert [item["name"] for item in payload["results"]] == ["Scenario A", "Scenario B"]
    assert callable(executor_calls[0]["timestamper_factory"])
    executor_calls[0]["timestamper_factory"]("ignored")
    assert dummy_calls == ["dummy"]
    assert summary["acceptance_expectations_passed"] is False
    assert workspace.refresh_calls == 1
    assert workspace_calls[0]["shell"] is not None
    assert workspace_calls[0]["profile_store"] is not None


def test_signed_acceptance_matrix_runner_records_error_results(
    tmp_path: Path, monkeypatch
) -> None:
    source_pdf = tmp_path / "fixture.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% fixture\n")
    artifacts_dir = tmp_path / "artifacts"

    monkeypatch.setattr(runner_module, "QtPdfRenderBackend", _FakeBackend)

    def execute(**kwargs):
        if kwargs["scenario"]["name"] == "Scenario B":
            raise RuntimeError("boom")
        return {"name": kwargs["scenario"]["name"], "signing_result": {"success": True}}

    runner = _runner(
        manifest={"scenarios": [{"name": "Scenario A"}, {"name": "Scenario B"}]},
        scenario_executor=execute,
    )

    summary = runner.run(
        pdf_path=str(source_pdf),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        scenario_manifest_path=str(tmp_path / "manifest.json"),
        artifacts_dir=str(artifacts_dir),
    )

    assert summary["successful_scenario_count"] == 1
    assert summary["error_scenario_count"] == 1
    assert summary["results"][1]["error"] == "boom"
    assert summary["results"][1]["error_type"] == "RuntimeError"


def test_signed_acceptance_matrix_runner_rejects_unknown_timestamping_mode(
    tmp_path: Path,
) -> None:
    source_pdf = tmp_path / "fixture.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% fixture\n")

    runner = _runner(
        manifest={"timestamping_mode": "bogus", "scenarios": []},
        scenario_executor=lambda **_kwargs: {},
    )

    try:
        runner.run(
            pdf_path=str(source_pdf),
            certificate_path=str(tmp_path / "cert.p12"),
            passphrase="secret",
            scenario_manifest_path=str(tmp_path / "manifest.json"),
            artifacts_dir=str(tmp_path / "artifacts"),
        )
    except ValueError as exc:
        assert "'timestamping_mode' must be one of 'real' or 'dummy'." in str(exc)
    else:
        raise AssertionError("expected ValueError for unsupported timestamping_mode")
