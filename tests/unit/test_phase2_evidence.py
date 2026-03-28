import pytest

from pdf_signer.application.performance_timing import ViewerTimingSnapshot
from pdf_signer.application.phase2_evidence import (
    RuntimeEnvironmentSnapshot,
    RuntimeValidationSnapshot,
    build_phase2_timing_evidence,
)
from pdf_signer.application.runtime_metrics import RuntimeFootprintSnapshot


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


def test_build_phase2_timing_evidence_includes_runtime_footprint_block() -> None:
    snapshot = ViewerTimingSnapshot(
        first_render_ms=20.0,
        average_navigation_ms=12.0,
        min_navigation_ms=10.0,
        max_navigation_ms=14.0,
        sample_count=10,
    )
    environment = RuntimeEnvironmentSnapshot(
        os_name="Linux",
        os_version="6.8.0",
        machine="x86_64",
        processor="ExampleCPU",
        python_version="3.12.3",
    )
    runtime = RuntimeFootprintSnapshot(
        startup_ms=650.0,
        idle_memory_mib=180.0,
        bundle_size_mib=60.0,
    )

    report = build_phase2_timing_evidence(
        timing=snapshot,
        environment=environment,
        runtime_footprint=runtime,
    )

    assert "### Runtime footprint snapshot" in report
    assert "- Startup latency: 650.00 ms" in report
    assert "### FR-16 runtime metrics quick-check" in report
    assert "- ✅ PyInstaller one-dir bundle size recorded" in report


def test_runtime_environment_collect_returns_non_empty_fields() -> None:
    collected = RuntimeEnvironmentSnapshot.collect()

    assert collected.os_name
    assert collected.os_version
    assert collected.machine
    assert collected.processor
    assert collected.python_version


def test_build_phase2_timing_evidence_includes_runtime_validation_block() -> None:
    snapshot = ViewerTimingSnapshot(
        first_render_ms=20.0,
        average_navigation_ms=12.0,
        min_navigation_ms=10.0,
        max_navigation_ms=14.0,
        sample_count=10,
    )
    environment = RuntimeEnvironmentSnapshot(
        os_name="Linux",
        os_version="6.8.0",
        machine="x86_64",
        processor="ExampleCPU",
        python_version="3.12.3",
    )
    validation = RuntimeValidationSnapshot(
        passed_checks=8,
        total_checks=9,
        issues=("Selection callback failed on rotated page sample.",),
    )

    report = build_phase2_timing_evidence(
        timing=snapshot,
        environment=environment,
        runtime_validation=validation,
    )

    assert "### Runtime validation sweep" in report
    assert "Checklist status: 8/9 checks passed" in report
    assert "Selection callback failed on rotated page sample." in report


def test_runtime_validation_snapshot_rejects_invalid_counts() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        RuntimeValidationSnapshot(passed_checks=0, total_checks=0)

    with pytest.raises(ValueError, match="greater than or equal to zero"):
        RuntimeValidationSnapshot(passed_checks=-1, total_checks=5)

    with pytest.raises(ValueError, match="cannot exceed total_checks"):
        RuntimeValidationSnapshot(passed_checks=6, total_checks=5)
