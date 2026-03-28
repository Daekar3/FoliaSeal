"""Runtime footprint metric helpers for Phase 2 sign-off evidence."""

from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class RuntimeFootprintSnapshot:
    """Measured runtime footprint metrics for packaged app validation."""

    startup_ms: float | None
    idle_memory_mib: float | None
    bundle_size_mib: float | None

    def to_markdown(self) -> str:
        """Return a compact markdown representation of footprint metrics."""

        startup = (
            f"{self.startup_ms:.2f} ms"
            if self.startup_ms is not None
            else "not recorded"
        )
        idle_memory = (
            f"{self.idle_memory_mib:.2f} MiB"
            if self.idle_memory_mib is not None
            else "not recorded"
        )
        bundle_size = (
            f"{self.bundle_size_mib:.2f} MiB"
            if self.bundle_size_mib is not None
            else "not recorded"
        )
        return "\n".join(
            [
                "### Runtime footprint snapshot",
                f"- Startup latency: {startup}",
                f"- Idle memory: {idle_memory}",
                f"- Bundle size (one-dir): {bundle_size}",
            ]
        )


def collect_idle_memory_mib() -> float | None:
    """Collect current process memory footprint in MiB when available."""

    rss_bytes = _collect_current_rss_bytes()
    if rss_bytes is None:
        return None

    rss_mib = rss_bytes / (1024 * 1024)
    if rss_mib < 0:
        return None

    return rss_mib


def _collect_current_rss_bytes() -> int | None:
    """Collect current resident set size for this process in bytes on Linux."""

    return _collect_current_rss_bytes_linux()


def _collect_current_rss_bytes_linux() -> int | None:
    """Collect current RSS bytes on Linux from /proc/self/statm."""

    try:
        with open("/proc/self/statm", encoding="utf-8") as statm_file:
            statm_fields = statm_file.read().strip().split()
        resident_pages = int(statm_fields[1])
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None

    rss_bytes = resident_pages * page_size
    if rss_bytes < 0:
        return None
    return rss_bytes


def measure_bundle_size_mib(*, bundle_dir: str) -> float:
    """Measure total filesystem size for a PyInstaller one-dir output."""

    root = Path(bundle_dir)
    if not root.exists():
        raise ValueError(f"bundle_dir does not exist: {bundle_dir}")
    if not root.is_dir():
        raise ValueError(f"bundle_dir must be a directory: {bundle_dir}")

    total_bytes = 0
    for path in root.rglob("*"):
        if path.is_file():
            total_bytes += path.stat().st_size
    return total_bytes / (1024 * 1024)


def collect_runtime_footprint_snapshot(
    *,
    startup_ms: float | None = None,
    bundle_dir: str | None = None,
) -> RuntimeFootprintSnapshot:
    """Collect a runtime footprint snapshot from local process and bundle directory."""

    bundle_size_mib = (
        measure_bundle_size_mib(bundle_dir=bundle_dir) if bundle_dir is not None else None
    )
    return RuntimeFootprintSnapshot(
        startup_ms=startup_ms,
        idle_memory_mib=collect_idle_memory_mib(),
        bundle_size_mib=bundle_size_mib,
    )


def measure_startup_latency_ms(
    *,
    command: list[str],
    timeout_seconds: float = 30.0,
    ready_after_seconds: float = 0.5,
) -> float:
    """Measure command launch readiness without requiring normal process exit.

    Short-lived probe commands return their full runtime. Long-running GUI-style
    commands are treated as "started" once they stay alive for the readiness
    window, after which the helper terminates them.
    """

    if not command:
        raise ValueError("command must include at least one argument")
    if not isfinite(timeout_seconds) or timeout_seconds <= 0.0:
        raise ValueError("timeout_seconds must be a finite number greater than zero")
    if not isfinite(ready_after_seconds) or ready_after_seconds <= 0.0:
        raise ValueError("ready_after_seconds must be a finite number greater than zero")
    if ready_after_seconds > timeout_seconds:
        raise ValueError("ready_after_seconds cannot exceed timeout_seconds")

    start = time.perf_counter()
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = start + timeout_seconds
    readiness_deadline = start + ready_after_seconds

    try:
        while True:
            now = time.perf_counter()
            returncode = process.poll()
            if returncode is not None:
                if returncode != 0:
                    raise subprocess.CalledProcessError(returncode, command)
                return (now - start) * 1000.0

            if now >= readiness_deadline:
                process.terminate()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1.0)
                return (now - start) * 1000.0

            if now >= deadline:
                process.kill()
                process.wait(timeout=1.0)
                raise subprocess.TimeoutExpired(command, timeout_seconds)

            time.sleep(0.01)
    except Exception:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=1.0)
        raise


def _format_metric_status(metric: float | None, label: str) -> str:
    icon = "✅" if metric is not None else "⚠️"
    return f"- {icon} {label}"


def _is_valid_runtime_metric(metric: float | None) -> bool:
    return metric is None or (isfinite(metric) and metric >= 0.0)


def validate_runtime_footprint_metrics(*, footprint: RuntimeFootprintSnapshot) -> None:
    invalid_metrics: list[str] = []
    if not _is_valid_runtime_metric(footprint.startup_ms):
        invalid_metrics.append("startup_ms")
    if not _is_valid_runtime_metric(footprint.idle_memory_mib):
        invalid_metrics.append("idle_memory_mib")
    if not _is_valid_runtime_metric(footprint.bundle_size_mib):
        invalid_metrics.append("bundle_size_mib")

    if invalid_metrics:
        metrics = ", ".join(invalid_metrics)
        raise ValueError(
            "Runtime footprint metrics must be finite and greater than or equal to zero. "
            f"Invalid fields: {metrics}."
        )


def build_runtime_footprint_quick_check(
    *,
    footprint: RuntimeFootprintSnapshot,
) -> str:
    """Build quick-check markdown bullets for FR-16 measurement completeness."""

    validate_runtime_footprint_metrics(footprint=footprint)

    return "\n".join(
        [
            "### FR-16 runtime metrics quick-check",
            _format_metric_status(footprint.startup_ms, "Startup latency recorded"),
            _format_metric_status(footprint.idle_memory_mib, "Idle memory recorded"),
            _format_metric_status(
                footprint.bundle_size_mib,
                "PyInstaller one-dir bundle size recorded",
            ),
        ]
    )
