import json
import subprocess
import sys
from pathlib import Path

import pytest

from foliaseal.application.evidence_service import EvidenceMatrixRequest
from foliaseal.presentation.qt import evidence_runner_factories
from foliaseal.presentation.qt.evidence_harness_runtime import EvidenceHarnessRuntime
from foliaseal.presentation.qt.evidence_runner_providers import (
    EvidenceRunnerProviders,
    InteractiveEvidenceProviders,
    PreviewMatrixEvidenceProviders,
    SignedAcceptanceEvidenceProviders,
)


def _request() -> EvidenceMatrixRequest:
    return EvidenceMatrixRequest(
        pdf_path="fixture.pdf",
        certificate_path="identity.p12",
        passphrase="secret",
        scenario_manifest_path="manifest.json",
        artifacts_dir="artifacts",
    )


def _fake_providers() -> EvidenceRunnerProviders:
    def callback(*_args, **_kwargs):
        return None

    return EvidenceRunnerProviders(
        interactive=InteractiveEvidenceProviders(
            load_qt_harness_bindings=callback,
            load_page_count=callback,
            render_backend_factory=callback,
            profile_store_factory=callback,
            build_phase3_signing_executor=callback,
            session_runner=object(),
            capture_assembler=object(),
            contract_evaluator=callback,
            capture_factory=callback,
            checklist_renderer=callback,
            report_finalizer=callback,
            artifact_policy=object(),
        ),
        preview=PreviewMatrixEvidenceProviders(
            load_preview_matrix_manifest=callback,
            execute_headless_preview_matrix_scenario=callback,
            preview_matrix_error_result=callback,
            preview_matrix_diagnostic_summary=callback,
            jsonable_capture=callback,
            profile_store_factory=callback,
        ),
        signed=SignedAcceptanceEvidenceProviders(
            load_qt_harness_bindings=callback,
            load_preview_matrix_manifest=callback,
            build_phase3_signing_executor=callback,
            build_dummy_timestamper=callback,
            load_page_count=callback,
            build_qt_signing_shell=callback,
            build_workspace=callback,
            execute_signed_acceptance_scenario=callback,
            preview_matrix_error_result=callback,
            signed_matrix_diagnostic_summary=callback,
            evaluate_signed_matrix_acceptance_expectations=callback,
            jsonable_capture=callback,
            render_backend_factory=callback,
            profile_store_factory=callback,
        ),
    )


def test_evidence_harness_runtime_exposes_only_explicit_lazy_operations() -> None:
    runtime = EvidenceHarnessRuntime(
        capture_operation=lambda request: ("capture", request),
        preview_matrix_operation=lambda request: {"kind": "preview", "request": request},
        signed_acceptance_matrix_operation=lambda request: {
            "kind": "signed",
            "request": request,
        },
    )
    request = _request()

    assert runtime.capture("capture-request") == ("capture", "capture-request")
    assert runtime.preview_matrix(request) == {"kind": "preview", "request": request}
    assert runtime.signed_acceptance_matrix(request) == {
        "kind": "signed",
        "request": request,
    }


def test_matrix_operation_builder_is_lazy_and_forwards_typed_requests() -> None:
    calls: list[str] = []
    request = _request()

    def build_preview():
        calls.append("preview_factory")

        class PreviewRunner:
            def run(self, **kwargs):
                calls.append(f"preview:{kwargs['pdf_path']}")
                assert kwargs["pdf_path"] == request.pdf_path
                return {"scenario_count": 8}

        return PreviewRunner()

    def build_signed():
        calls.append("signed_factory")

        class SignedRunner:
            def run(self, **_kwargs):
                return {"scenario_count": 8}

        return SignedRunner()

    operation = evidence_runner_factories._build_matrix_operation(build_preview)

    assert calls == []
    assert operation(request) == {"scenario_count": 8}
    assert calls == ["preview_factory", "preview:fixture.pdf"]


def test_preview_factory_consumes_injected_provider_record() -> None:
    providers = _fake_providers()

    runner = evidence_runner_factories.build_preview_evidence_runner(
        providers=providers,
    )

    assert runner.deps.load_preview_matrix_manifest is (
        providers.preview.load_preview_matrix_manifest
    )
    assert runner.deps.execute_headless_preview_matrix_scenario is (
        providers.preview.execute_headless_preview_matrix_scenario
    )
    assert runner.deps.preview_matrix_error_result is (
        providers.preview.preview_matrix_error_result
    )
    assert runner.deps.preview_matrix_diagnostic_summary is (
        providers.preview.preview_matrix_diagnostic_summary
    )
    assert runner.deps.jsonable_capture is providers.preview.jsonable_capture
    assert runner.deps.profile_store_factory is providers.preview.profile_store_factory


def test_interactive_factory_consumes_injected_provider_record() -> None:
    providers = _fake_providers()

    engine = evidence_runner_factories.build_interactive_capture_engine(
        providers=providers,
    )

    assert engine.load_qt_harness_bindings is (
        providers.interactive.load_qt_harness_bindings
    )
    assert engine.load_page_count is providers.interactive.load_page_count
    assert engine.render_backend_factory is providers.interactive.render_backend_factory
    assert engine.profile_store_factory is providers.interactive.profile_store_factory
    assert engine.session_runner is providers.interactive.session_runner
    assert engine.capture_assembler is providers.interactive.capture_assembler
    assert engine.artifact_policy is providers.interactive.artifact_policy


def test_signed_factory_consumes_injected_provider_record() -> None:
    providers = _fake_providers()

    runner = evidence_runner_factories.build_signed_acceptance_evidence_runner(
        providers=providers,
    )

    assert runner.deps.load_qt_harness_bindings is (
        providers.signed.load_qt_harness_bindings
    )
    assert runner.deps.load_preview_matrix_manifest is (
        providers.signed.load_preview_matrix_manifest
    )
    assert runner.deps.build_workspace is providers.signed.build_workspace
    assert runner.deps.execute_signed_acceptance_scenario is (
        providers.signed.execute_signed_acceptance_scenario
    )
    assert runner.deps.render_backend_factory is providers.signed.render_backend_factory
    assert runner.deps.profile_store_factory is providers.signed.profile_store_factory


def test_provider_module_stays_headless_until_harness_builder_is_requested() -> None:
    script = """
import json
import sys
import foliaseal.presentation.qt.evidence_runner_providers
import foliaseal.presentation.qt.evidence_runner_factories
heavy = ("PySide6", "PIL", "pyhanko", "foliaseal.presentation.qt.phase3_harness")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)
print(json.dumps(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []


def test_factory_has_no_private_harness_reach_through() -> None:
    source = evidence_runner_factories.__file__
    assert source is not None
    assert "harness._" not in Path(source).read_text(encoding="utf-8")


def test_matrix_operation_constructs_its_runner_once() -> None:
    factory_count = 0

    def preview_factory():
        nonlocal factory_count
        factory_count += 1
        class PreviewRunner:
            def run(self, **_kwargs):
                return {"kind": "preview"}

        return PreviewRunner()

    operation = evidence_runner_factories._build_matrix_operation(preview_factory)

    assert operation(_request()) == {"kind": "preview"}
    assert operation(_request()) == {"kind": "preview"}
    assert factory_count == 1


@pytest.mark.parametrize(
    ("operation_factory", "runner_factory", "result"),
    [
        (
            evidence_runner_factories.build_preview_evidence_operation,
            "build_preview_evidence_runner",
            {"kind": "preview"},
        ),
        (
            evidence_runner_factories.build_signed_acceptance_evidence_operation,
            "build_signed_acceptance_evidence_runner",
            {"kind": "signed"},
        ),
    ],
)
def test_concrete_evidence_operations_forward_every_request_field(
    monkeypatch: pytest.MonkeyPatch,
    operation_factory,
    runner_factory: str,
    result: dict[str, str],
) -> None:
    captured: dict[str, object] = {}

    class _FakeRunner:
        def run(self, **kwargs):
            captured.update(kwargs)
            return result

    monkeypatch.setattr(evidence_runner_factories, runner_factory, lambda: _FakeRunner())
    request = _request()

    assert operation_factory()(request) == result
    assert captured == {
        "pdf_path": request.pdf_path,
        "certificate_path": request.certificate_path,
        "passphrase": request.passphrase,
        "scenario_manifest_path": request.scenario_manifest_path,
        "artifacts_dir": request.artifacts_dir,
    }


def test_evidence_runner_factories_do_not_import_gui_or_pdf_libraries() -> None:
    script = """
import json
import sys
import foliaseal.presentation.qt.evidence_runner_factories
heavy = ("PySide6", "PIL", "pyhanko")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)
print(json.dumps(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []


def test_interactive_capture_engine_import_and_construction_stay_lazy() -> None:
    script = """
import json
import sys
from foliaseal.presentation.qt.evidence_interactive_capture import (
    InteractiveCaptureEngine,
    InteractiveEvidenceArtifactPolicy,
)
InteractiveCaptureEngine(
    load_qt_harness_bindings=lambda: None,
    load_page_count=lambda **_: 1,
    render_backend_factory=lambda: None,
    profile_store_factory=lambda: None,
    build_phase3_signing_executor=lambda: None,
    session_runner=None,
    capture_assembler=None,
    contract_evaluator=lambda **_: None,
    capture_factory=lambda **_: None,
    checklist_renderer=lambda **_: "",
    report_finalizer=lambda **_: None,
    artifact_policy=InteractiveEvidenceArtifactPolicy(
        default_artifacts_dir=lambda **_: None,
        output_pdf_path=lambda **_: "output.pdf",
        write_text=lambda **_: None,
    ),
)
heavy = ("PySide6", "PIL", "pyhanko")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)
print(json.dumps(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []


def test_matrix_operation_preserves_raw_mapping_results() -> None:
    expected = {"scenario_count": 8, "results": [{"name": "baseline"}]}
    class PreviewRunner:
        def run(self, **_kwargs):
            return expected

    operation = evidence_runner_factories._build_matrix_operation(lambda: PreviewRunner())

    assert operation(_request()) is expected


def test_default_evidence_module_does_not_import_gui_or_pdf_libraries() -> None:
    script = """
import json
import sys
import foliaseal.presentation.qt.signed_acceptance_evidence
heavy = ("PySide6", "PIL", "pyhanko")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)
print(json.dumps(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []


def test_default_evidence_program_construction_stays_headless() -> None:
    script = """
import json
import sys
from foliaseal.__main__ import _build_evidence_program
_build_evidence_program()
heavy = ("PySide6", "PIL", "pyhanko", "cryptography")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)
print(json.dumps(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []


def test_cli_module_does_not_import_gui_or_pdf_libraries() -> None:
    script = """
import json
import sys
import foliaseal.__main__
heavy = ("PySide6", "PIL", "pyhanko")
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in heavy)
)
print(json.dumps(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout) == []
