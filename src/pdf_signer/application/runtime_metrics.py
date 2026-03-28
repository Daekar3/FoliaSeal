"""Runtime footprint metric helpers for Phase 2 sign-off evidence."""

from __future__ import annotations

from dataclasses import dataclass


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


def _format_metric_status(metric: float | None, label: str) -> str:
    icon = "✅" if metric is not None else "⚠️"
    return f"- {icon} {label}"


def build_runtime_footprint_quick_check(
    *,
    footprint: RuntimeFootprintSnapshot,
) -> str:
    """Build quick-check markdown bullets for FR-16 measurement completeness."""

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
