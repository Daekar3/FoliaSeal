import json
import subprocess
import sys

import pytest

from foliaseal.application.evidence_service import EvidenceMatrixRequest
from foliaseal.presentation.qt import evidence_runner_factories


def _request() -> EvidenceMatrixRequest:
    return EvidenceMatrixRequest(
        pdf_path="fixture.pdf",
        certificate_path="identity.p12",
        passphrase="secret",
        scenario_manifest_path="manifest.json",
        artifacts_dir="artifacts",
    )


def test_matrix_operation_builder_is_lazy_and_forwards_typed_requests() -> None:
    calls: list[str] = []
    request = _request()

    def build_preview():
        calls.append("preview_factory")

        def preview(received):
            calls.append(f"preview:{received.pdf_path}")
            assert received == request
            return {"scenario_count": 8}

        return preview

    def build_signed():
        calls.append("signed_factory")
        return lambda _received: {"scenario_count": 8}

    operation = evidence_runner_factories._build_matrix_operation(build_preview)

    assert calls == []
    assert operation(request) == {"scenario_count": 8}
    assert calls == ["preview_factory", "preview:fixture.pdf"]


def test_matrix_operation_constructs_its_runner_once() -> None:
    factory_count = 0

    def preview_factory():
        nonlocal factory_count
        factory_count += 1
        return lambda _request: {"kind": "preview"}

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
    operation = evidence_runner_factories._build_matrix_operation(
        lambda: lambda _request: expected
    )

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
