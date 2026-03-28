import pytest

from foliaseal.application.viewer_session import ViewerSession, ViewerZoomLimits


def test_navigation_boundaries_and_jump() -> None:
    session = ViewerSession(page_count=3)

    assert session.current_page == 0
    assert session.can_go_previous() is False
    assert session.can_go_next() is True

    assert session.go_previous() == 0
    assert session.go_next() == 1
    assert session.go_next() == 2
    assert session.can_go_next() is False
    assert session.go_next() == 2

    assert session.jump_to_page(1) == 1

    with pytest.raises(ValueError, match="out of range"):
        session.jump_to_page(3)


def test_zoom_controls_and_limits_are_applied() -> None:
    session = ViewerSession(
        page_count=1,
        zoom_limits=ViewerZoomLimits(minimum=0.5, maximum=2.0, step=2.0),
    )

    assert session.zoom == 1.0
    assert session.zoom_in() == 2.0
    assert session.zoom_in() == 2.0

    assert session.zoom_out() == 1.0
    assert session.zoom_out() == 0.5
    assert session.zoom_out() == 0.5

    assert session.reset_zoom() == 1.0


def test_fit_to_width_and_page_clamp_to_limits() -> None:
    session = ViewerSession(
        page_count=1,
        zoom_limits=ViewerZoomLimits(minimum=0.25, maximum=3.0, step=1.25),
    )

    assert session.fit_to_width(viewport_width_px=1200, page_width_px=600) == 2.0
    assert session.fit_to_page(viewport_height_px=2000, page_height_px=500) == 3.0
    assert session.fit_to_page(viewport_height_px=50, page_height_px=1000) == 0.25


def test_initial_and_reset_zoom_are_clamped_to_configured_limits() -> None:
    above_one = ViewerSession(
        page_count=1,
        zoom_limits=ViewerZoomLimits(minimum=1.5, maximum=4.0, step=1.25),
    )
    assert above_one.zoom == 1.5
    assert above_one.reset_zoom() == 1.5

    below_one = ViewerSession(
        page_count=1,
        zoom_limits=ViewerZoomLimits(minimum=0.25, maximum=0.8, step=1.25),
    )
    assert below_one.zoom == 0.8
    assert below_one.reset_zoom() == 0.8


@pytest.mark.parametrize(
    ("page_count", "limits"),
    [
        (0, ViewerZoomLimits()),
        (1, ViewerZoomLimits(minimum=0.0, maximum=4.0, step=1.2)),
        (1, ViewerZoomLimits(minimum=2.0, maximum=1.0, step=1.2)),
        (1, ViewerZoomLimits(minimum=0.5, maximum=2.0, step=1.0)),
    ],
)
def test_rejects_invalid_constructor_values(page_count: int, limits: ViewerZoomLimits) -> None:
    with pytest.raises(ValueError):
        ViewerSession(page_count=page_count, zoom_limits=limits)


def test_fit_rejects_non_positive_extents() -> None:
    session = ViewerSession(page_count=1)

    with pytest.raises(ValueError, match="viewport"):
        session.fit_to_width(viewport_width_px=0, page_width_px=100)

    with pytest.raises(ValueError, match="page"):
        session.fit_to_page(viewport_height_px=100, page_height_px=0)
