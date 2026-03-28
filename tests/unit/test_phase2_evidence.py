import pytest

from pdf_signer.application.performance_timing import ViewerTimingSnapshot
from pdf_signer.application.phase2_evidence import (
    RuntimeEnvironmentSnapshot,
    build_phase2_timing_evidence,
)


def test_build_phase2_timing_evidence_includes_environment_and_statuses() -> None:
    snapshot = ViewerTimingSnapshot(
        first_render_ms=123.0,
        average_navigation_ms=22.0,
        min_navigation_ms=20.0,
        max_navigation_ms=25.0,
        sample_count=12,
    )
    environment = RuntimeEnvironmentSnapshot(
        os_name="Linux",
        os_version="6.8.0",
        machine="x86_64",
        processor="ExampleCPU",
        python_version="3.12.3",
    )

    report = build_phase2_timing_evidence(timing=snapshot, environment=environment)

    assert "## Phase 2 runtime evidence" in report
    assert "First render: 123.00 ms" in report
    assert "Navigation samples: 12" in report
    assert "- OS: Linux (6.8.0)" in report
    assert "- ✅ First-render timing recorded" in report
    assert "- ✅ Navigation sample count (12/10)" in report


def test_build_phase2_timing_evidence_warns_on_missing_metrics() -> None:
    snapshot = ViewerTimingSnapshot(
        first_render_ms=None,
        average_navigation_ms=None,
        min_navigation_ms=None,
        max_navigation_ms=None,
        sample_count=3,
    )
    environment = RuntimeEnvironmentSnapshot(
        os_name="Linux",
        os_version="6.8.0",
        machine="x86_64",
        processor="ExampleCPU",
        python_version="3.12.3",
    )

    report = build_phase2_timing_evidence(
        timing=snapshot,
        environment=environment,
        minimum_navigation_samples=5,
    )

    assert "- ⚠️ First-render timing recorded" in report
    assert "- ⚠️ Navigation sample count (3/5)" in report


def test_build_phase2_timing_evidence_rejects_invalid_threshold() -> None:
    snapshot = ViewerTimingSnapshot(
        first_render_ms=1.0,
        average_navigation_ms=1.0,
        min_navigation_ms=1.0,
        max_navigation_ms=1.0,
        sample_count=1,
    )
    environment = RuntimeEnvironmentSnapshot(
        os_name="Linux",
        os_version="6.8.0",
        machine="x86_64",
        processor="ExampleCPU",
        python_version="3.12.3",
    )

    with pytest.raises(ValueError, match="at least 1"):
        build_phase2_timing_evidence(
            timing=snapshot,
            environment=environment,
            minimum_navigation_samples=0,
        )


def test_runtime_environment_collect_returns_non_empty_fields() -> None:
    collected = RuntimeEnvironmentSnapshot.collect()

    assert collected.os_name
    assert collected.os_version
    assert collected.machine
    assert collected.processor
    assert collected.python_version
