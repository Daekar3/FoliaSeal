"""Viewer performance timing helpers for Phase 2 exit criteria."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewerTimingSnapshot:
    """Computed viewer timing summary in milliseconds."""

    first_render_ms: float | None
    average_navigation_ms: float | None
    sample_count: int


class ViewerPerformanceTracker:
    """Collect first-render and navigation timing measurements."""

    def __init__(self) -> None:
        self._first_render_ms: float | None = None
        self._navigation_samples_ms: list[float] = []

    def record_first_render(self, elapsed_ms: float) -> None:
        if elapsed_ms < 0:
            raise ValueError("elapsed_ms must be greater than or equal to zero.")
        if self._first_render_ms is None:
            self._first_render_ms = elapsed_ms

    def record_navigation(self, elapsed_ms: float) -> None:
        if elapsed_ms < 0:
            raise ValueError("elapsed_ms must be greater than or equal to zero.")
        self._navigation_samples_ms.append(elapsed_ms)

    def snapshot(self) -> ViewerTimingSnapshot:
        avg = None
        if self._navigation_samples_ms:
            avg = sum(self._navigation_samples_ms) / len(self._navigation_samples_ms)
        return ViewerTimingSnapshot(
            first_render_ms=self._first_render_ms,
            average_navigation_ms=avg,
            sample_count=len(self._navigation_samples_ms),
        )

    def reset(self) -> None:
        self._first_render_ms = None
        self._navigation_samples_ms.clear()
