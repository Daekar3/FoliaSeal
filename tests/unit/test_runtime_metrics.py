import pytest

from pdf_signer.application.runtime_metrics import (
    RuntimeFootprintSnapshot,
    build_runtime_footprint_quick_check,
)


def test_runtime_footprint_snapshot_markdown_formats_values() -> None:
    snapshot = RuntimeFootprintSnapshot(
        startup_ms=810.5,
        idle_memory_mib=142.3,
        bundle_size_mib=57.9,
    )

    output = snapshot.to_markdown()

    assert "Startup latency: 810.50 ms" in output
    assert "Idle memory: 142.30 MiB" in output
    assert "Bundle size (one-dir): 57.90 MiB" in output


def test_runtime_footprint_quick_check_warns_on_missing_measurements() -> None:
    snapshot = RuntimeFootprintSnapshot(
        startup_ms=500.0,
        idle_memory_mib=None,
        bundle_size_mib=None,
    )

    output = build_runtime_footprint_quick_check(footprint=snapshot)

    assert "✅ Startup latency recorded" in output
    assert "⚠️ Idle memory recorded" in output
    assert "⚠️ PyInstaller one-dir bundle size recorded" in output


@pytest.mark.parametrize(
    ("startup_ms", "idle_memory_mib", "bundle_size_mib", "field_name"),
    [
        (-1.0, 50.0, 25.0, "startup_ms"),
        (200.0, float("nan"), 25.0, "idle_memory_mib"),
        (200.0, 50.0, float("inf"), "bundle_size_mib"),
    ],
)
def test_runtime_footprint_quick_check_rejects_invalid_measurements(
    startup_ms: float,
    idle_memory_mib: float,
    bundle_size_mib: float,
    field_name: str,
) -> None:
    snapshot = RuntimeFootprintSnapshot(
        startup_ms=startup_ms,
        idle_memory_mib=idle_memory_mib,
        bundle_size_mib=bundle_size_mib,
    )

    with pytest.raises(ValueError, match=field_name):
        build_runtime_footprint_quick_check(footprint=snapshot)
