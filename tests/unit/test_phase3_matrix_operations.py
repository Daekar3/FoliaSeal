import json
import subprocess
import sys

import pytest

from foliaseal.application.phase3_evidence_service import Phase3MatrixRequest
from foliaseal.presentation.qt import evidence_runner_factories
from foliaseal.presentation.qt.phase3_matrix_operations import (
    build_evidence_matrix_operations,
)


def _request() -> Phase3MatrixRequest:
    return Phase3MatrixRequest(
        pdf_path="fixture.pdf",
        certificate_path="identity.p12",
        passphrase="secret",
        scenario_manifest_path="manifest.json",
        artifacts_dir="artifacts",
    )


def test_matrix_operations_are_lazy_and_forward_typed_requests() -> None:
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

    operations = build_evidence_matrix_operations(
        preview_factory=build_preview,
        signed_acceptance_factory=build_signed,
    )

    assert calls == []
    assert operations.preview(request) == {"scenario_count": 8}
    assert calls == ["preview_factory", "preview:fixture.pdf"]


def test_each_matrix_operation_constructs_its_runner_once() -> None:
    factory_counts = {"preview": 0, "signed": 0}

    def preview_factory():
        factory_counts["preview"] += 1
        return lambda _request: {"kind": "preview"}

    def signed_factory():
        factory_counts["signed"] += 1
        return lambda _request: {"kind": "signed"}

    operations = build_evidence_matrix_operations(
        preview_factory=preview_factory,
        signed_acceptance_factory=signed_factory,
    )

    assert operations.preview(_request()) == {"kind": "preview"}
    assert operations.preview(_request()) == {"kind": "preview"}
    assert operations.signed_acceptance(_request()) == {"kind": "signed"}
    assert factory_counts == {"preview": 1, "signed": 1}


def test_evidence_matrix_operations_are_lazy_and_forward_requests() -> None:
    request = _request()
    calls: list[str] = []

    def preview_factory():
        calls.append("preview_factory")
        return lambda received: calls.append(received.pdf_path) or {"kind": "preview"}

    def signed_factory():
        calls.append("signed_factory")
        return lambda received: calls.append(received.pdf_path) or {"kind": "signed"}

    operations = build_evidence_matrix_operations(
        preview_factory=preview_factory,
        signed_acceptance_factory=signed_factory,
    )
    assert calls == []
    assert operations.preview(request) == {"kind": "preview"}
    assert operations.preview(request) == {"kind": "preview"}
    assert operations.signed_acceptance(request) == {"kind": "signed"}
    assert calls == [
        "preview_factory",
        "fixture.pdf",
        "fixture.pdf",
        "signed_factory",
        "fixture.pdf",
    ]


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


def test_matrix_operations_preserve_raw_mapping_results() -> None:
    expected = {"scenario_count": 8, "results": [{"name": "baseline"}]}
    operations = build_evidence_matrix_operations(
        preview_factory=lambda: lambda _request: expected,
        signed_acceptance_factory=lambda: lambda _request: expected,
    )

    assert operations.preview(_request()) is expected
    assert operations.signed_acceptance(_request()) is expected


def test_matrix_operations_module_does_not_import_gui_or_pdf_libraries() -> None:
    script = """
import json
import sys
import foliaseal.presentation.qt.phase3_matrix_operations
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


def test_default_evidence_module_does_not_import_gui_or_pdf_libraries() -> None:
    script = """
import json
import sys
import foliaseal.presentation.qt.phase3_signed_acceptance_evidence
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
