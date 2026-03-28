from pathlib import Path

import pytest

from pdf_signer.application.runtime_metrics import (
    RuntimeFootprintSnapshot,
    _collect_current_rss_bytes,
    _collect_current_rss_bytes_linux,
    build_runtime_footprint_quick_check,
    collect_idle_memory_mib,
    collect_runtime_footprint_snapshot,
    measure_bundle_size_mib,
    measure_startup_latency_ms,
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


def test_collect_idle_memory_mib_returns_non_negative_or_none() -> None:
    measurement = collect_idle_memory_mib()

    assert measurement is None or measurement >= 0.0


def test_collect_current_rss_bytes_linux_reads_resident_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_open(*args, **kwargs):  # type: ignore[no-untyped-def]
        class _FakeFile:
            def __enter__(self):  # type: ignore[no-untyped-def]
                return self

            def __exit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
                return False

            def read(self) -> str:
                return "12345 10 0 0 0 0 0\n"

        return _FakeFile()

    monkeypatch.setattr("builtins.open", fake_open)
    monkeypatch.setattr("os.sysconf", lambda name: 4096)

    assert _collect_current_rss_bytes_linux() == 40960


def test_collect_current_rss_bytes_returns_none_when_linux_statm_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "pdf_signer.application.runtime_metrics._collect_current_rss_bytes_linux",
        lambda: None,
    )

    assert _collect_current_rss_bytes() is None


def test_measure_bundle_size_mib_sums_directory_files(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "dist"
    bundle_dir.mkdir()
    (bundle_dir / "a.bin").write_bytes(b"a" * 1024 * 1024)
    nested = bundle_dir / "nested"
    nested.mkdir()
    (nested / "b.bin").write_bytes(b"b" * 512 * 1024)

    measured = measure_bundle_size_mib(bundle_dir=str(bundle_dir))

    assert measured == pytest.approx(1.5, abs=0.01)


def test_collect_runtime_footprint_snapshot_reads_bundle_size(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "dist"
    bundle_dir.mkdir()
    (bundle_dir / "payload.bin").write_bytes(b"x" * 2 * 1024 * 1024)

    snapshot = collect_runtime_footprint_snapshot(
        startup_ms=300.0,
        bundle_dir=str(bundle_dir),
    )

    assert snapshot.startup_ms == 300.0
    assert snapshot.bundle_size_mib == pytest.approx(2.0, abs=0.01)
    assert snapshot.idle_memory_mib is None or snapshot.idle_memory_mib >= 0.0


def test_measure_startup_latency_ms_returns_elapsed_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}

    class _Process:
        def __init__(self) -> None:
            self.poll_count = 0

        def poll(self):  # type: ignore[no-untyped-def]
            self.poll_count += 1
            if self.poll_count == 1:
                return None
            return 0

        def terminate(self):  # type: ignore[no-untyped-def]
            raise AssertionError("terminate should not be used for short-lived probe command")

        def wait(self, timeout):  # type: ignore[no-untyped-def]
            calls["wait_timeout"] = timeout
            return 0

        def kill(self):  # type: ignore[no-untyped-def]
            raise AssertionError("kill should not be used for short-lived probe command")

    def fake_popen(*args, **kwargs):  # type: ignore[no-untyped-def]
        calls["command"] = args[0]
        return _Process()

    samples = iter([100.0, 100.10, 100.25])
    monkeypatch.setattr("pdf_signer.application.runtime_metrics.subprocess.Popen", fake_popen)
    monkeypatch.setattr(
        "pdf_signer.application.runtime_metrics.time.perf_counter",
        lambda: next(samples),
    )
    monkeypatch.setattr("pdf_signer.application.runtime_metrics.time.sleep", lambda _: None)

    measured = measure_startup_latency_ms(
        command=["/tmp/foliaseal", "--help"],
        timeout_seconds=15.0,
        ready_after_seconds=0.5,
    )

    assert measured == pytest.approx(250.0, abs=0.001)
    assert calls["command"] == ["/tmp/foliaseal", "--help"]
 

def test_measure_startup_latency_ms_treats_long_running_command_as_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {"terminated": False}

    class _Process:
        def poll(self):  # type: ignore[no-untyped-def]
            return None

        def terminate(self):  # type: ignore[no-untyped-def]
            calls["terminated"] = True

        def wait(self, timeout):  # type: ignore[no-untyped-def]
            calls["wait_timeout"] = timeout
            return 0

        def kill(self):  # type: ignore[no-untyped-def]
            raise AssertionError("kill should not be used when readiness is reached")

    monkeypatch.setattr(
        "pdf_signer.application.runtime_metrics.subprocess.Popen",
        lambda *args, **kwargs: _Process(),
    )
    samples = iter([10.0, 10.2, 10.55])
    monkeypatch.setattr(
        "pdf_signer.application.runtime_metrics.time.perf_counter",
        lambda: next(samples),
    )
    monkeypatch.setattr("pdf_signer.application.runtime_metrics.time.sleep", lambda _: None)

    measured = measure_startup_latency_ms(
        command=["/tmp/foliaseal"],
        timeout_seconds=5.0,
        ready_after_seconds=0.5,
    )

    assert measured == pytest.approx(550.0, abs=0.001)
    assert calls["terminated"] is True
    assert calls["wait_timeout"] == 1.0


def test_measure_startup_latency_ms_rejects_invalid_arguments() -> None:
    with pytest.raises(ValueError, match="at least one argument"):
        measure_startup_latency_ms(command=[])
    with pytest.raises(ValueError, match="greater than zero"):
        measure_startup_latency_ms(command=["python3"], timeout_seconds=0.0)
    with pytest.raises(ValueError, match="greater than zero"):
        measure_startup_latency_ms(command=["python3"], ready_after_seconds=0.0)
    with pytest.raises(ValueError, match="cannot exceed timeout_seconds"):
        measure_startup_latency_ms(
            command=["python3"],
            timeout_seconds=1.0,
            ready_after_seconds=2.0,
        )
