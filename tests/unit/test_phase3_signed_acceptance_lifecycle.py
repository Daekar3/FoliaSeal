from __future__ import annotations

from pathlib import Path

from foliaseal.presentation.qt.phase3_matrix_artifacts import (
    MemoryPhase3MatrixArtifactPort,
)
from foliaseal.presentation.qt.phase3_signed_acceptance_lifecycle import (
    FakePhase3SignedAcceptanceLifecycle,
)


def test_fake_signed_acceptance_lifecycle_records_open_process_and_close() -> None:
    lifecycle = FakePhase3SignedAcceptanceLifecycle()

    lifecycle.start(title="Matrix")
    lifecycle.attach_shell(object())
    lifecycle.process_events()
    lifecycle.close()

    assert lifecycle.calls == [
        ("start", "Matrix"),
        ("attach_shell", None),
        ("process_events", None),
        ("close", None),
    ]


def test_memory_matrix_artifact_port_records_summary_without_filesystem_io() -> None:
    artifacts = MemoryPhase3MatrixArtifactPort()

    root = artifacts.prepare("memory/run")
    summary_path = artifacts.write_summary(root, {"scenario_count": 2})

    assert root == Path("memory/run")
    assert summary_path == "memory/run/summary.json"
    assert artifacts.summaries[summary_path] == {"scenario_count": 2}
