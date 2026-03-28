"""Viewer performance timing helpers for Phase 2 exit criteria."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewerTimingSnapshot:
    """Computed viewer timing summary in milliseconds."""

    first_render_ms: float | None
    average_navigation_ms: float | None
    min_navigation_ms: float | None
    max_navigation_ms: float | None
    sample_count: int

    def to_markdown(self) -> str:
        """Return a compact markdown block useful for Phase 2 evidence notes."""

        first_render = (
            f"{self.first_render_ms:.2f} ms"
            if self.first_render_ms is not None
            else "not recorded"
        )
        avg_nav = (
            f"{self.average_navigation_ms:.2f} ms"
            if self.average_navigation_ms is not None
            else "not recorded"
        )
        min_nav = (
            f"{self.min_navigation_ms:.2f} ms"
            if self.min_navigation_ms is not None
            else "not recorded"
        )
        max_nav = (
            f"{self.max_navigation_ms:.2f} ms"
            if self.max_navigation_ms is not None
            else "not recorded"
        )
        return "\n".join(
            [
                "### Viewer timing snapshot",
                f"- First render: {first_render}",
                f"- Navigation average: {avg_nav}",
                f"- Navigation min/max: {min_nav} / {max_nav}",
                f"- Navigation samples: {self.sample_count}",
            ]
        )


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
        min_sample = None
        max_sample = None
        if self._navigation_samples_ms:
            avg = sum(self._navigation_samples_ms) / len(self._navigation_samples_ms)
            min_sample = min(self._navigation_samples_ms)
            max_sample = max(self._navigation_samples_ms)
        return ViewerTimingSnapshot(
            first_render_ms=self._first_render_ms,
            average_navigation_ms=avg,
            min_navigation_ms=min_sample,
            max_navigation_ms=max_sample,
            sample_count=len(self._navigation_samples_ms),
        )

    def reset(self) -> None:
        self._first_render_ms = None
        self._navigation_samples_ms.clear()
