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
