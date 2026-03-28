import pytest

from foliaseal.application.performance_timing import ViewerPerformanceTracker


def test_tracker_records_first_render_once_and_navigation_average() -> None:
    tracker = ViewerPerformanceTracker()

    tracker.record_first_render(80.0)
    tracker.record_first_render(120.0)
    tracker.record_navigation(40.0)
    tracker.record_navigation(60.0)

    snapshot = tracker.snapshot()

    assert snapshot.first_render_ms == 80.0
    assert snapshot.average_navigation_ms == pytest.approx(50.0)
    assert snapshot.min_navigation_ms == pytest.approx(40.0)
    assert snapshot.max_navigation_ms == pytest.approx(60.0)
    assert snapshot.sample_count == 2


def test_tracker_rejects_negative_timings() -> None:
    tracker = ViewerPerformanceTracker()

    with pytest.raises(ValueError, match="greater than or equal to zero"):
        tracker.record_first_render(-1.0)

    with pytest.raises(ValueError, match="greater than or equal to zero"):
        tracker.record_navigation(-1.0)


def test_tracker_reset_clears_measurements() -> None:
    tracker = ViewerPerformanceTracker()
    tracker.record_first_render(20.0)
    tracker.record_navigation(10.0)

    tracker.reset()
    snapshot = tracker.snapshot()

    assert snapshot.first_render_ms is None
    assert snapshot.average_navigation_ms is None
    assert snapshot.min_navigation_ms is None
    assert snapshot.max_navigation_ms is None
    assert snapshot.sample_count == 0


def test_snapshot_to_markdown_formats_recorded_values() -> None:
    tracker = ViewerPerformanceTracker()
    tracker.record_first_render(20.0)
    tracker.record_navigation(10.0)
    tracker.record_navigation(15.0)

    markdown = tracker.snapshot().to_markdown()

    assert "First render: 20.00 ms" in markdown
    assert "Navigation average: 12.50 ms" in markdown
    assert "Navigation min/max: 10.00 ms / 15.00 ms" in markdown
    assert "Navigation samples: 2" in markdown
