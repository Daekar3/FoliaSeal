"""Viewer interaction state helpers for Phase 2 usability requirements."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ViewerZoomLimits:
    """Clamp configuration for interactive zoom controls."""

    minimum: float = 0.10
    maximum: float = 8.0
    step: float = 1.25

    def validate(self) -> None:
        if self.minimum <= 0:
            raise ValueError("Zoom minimum must be greater than zero.")
        if self.maximum < self.minimum:
            raise ValueError("Zoom maximum must be greater than or equal to minimum.")
        if self.step <= 1.0:
            raise ValueError("Zoom step must be greater than 1.0.")


class ViewerSession:
    """Mutable viewer state for page navigation and zoom behavior."""

    def __init__(
        self,
        *,
        page_count: int,
        zoom_limits: ViewerZoomLimits | None = None,
    ) -> None:
        if page_count <= 0:
            raise ValueError("page_count must be greater than zero.")

        self._page_count = page_count
        self._current_page = 0
        self._zoom_limits = zoom_limits or ViewerZoomLimits()
        self._zoom_limits.validate()
        self._zoom = self._default_zoom()
        self._zoom_mode = "fit_page"

    @property
    def page_count(self) -> int:
        return self._page_count

    @property
    def current_page(self) -> int:
        return self._current_page

    @property
    def zoom(self) -> float:
        return self._zoom

    @property
    def zoom_limits(self) -> ViewerZoomLimits:
        return self._zoom_limits

    @property
    def zoom_mode(self) -> str:
        """Return ``fit_page``, ``fit_width``, or ``custom`` for the current view."""

        return self._zoom_mode

    def can_go_previous(self) -> bool:
        return self._current_page > 0

    def can_go_next(self) -> bool:
        return self._current_page < (self._page_count - 1)

    def go_previous(self) -> int:
        if self.can_go_previous():
            self._current_page -= 1
        return self._current_page

    def go_next(self) -> int:
        if self.can_go_next():
            self._current_page += 1
        return self._current_page

    def jump_to_page(self, page_index: int) -> int:
        if page_index < 0 or page_index >= self._page_count:
            raise ValueError("page_index is out of range.")
        self._current_page = page_index
        return self._current_page

    def zoom_in(self) -> float:
        self._zoom = min(self._zoom * self._zoom_limits.step, self._zoom_limits.maximum)
        self._zoom_mode = "custom"
        return self._zoom

    def zoom_out(self) -> float:
        self._zoom = max(self._zoom / self._zoom_limits.step, self._zoom_limits.minimum)
        self._zoom_mode = "custom"
        return self._zoom

    def reset_zoom(self) -> float:
        self._zoom = self._default_zoom()
        self._zoom_mode = "custom"
        return self._zoom

    def fit_to_width(self, viewport_width_px: float, page_width_px: float) -> float:
        self._zoom = self._fit_zoom(viewport_extent=viewport_width_px, page_extent=page_width_px)
        self._zoom_mode = "fit_width"
        return self._zoom

    def fit_to_page(self, viewport_height_px: float, page_height_px: float) -> float:
        self._zoom = self._fit_zoom(viewport_extent=viewport_height_px, page_extent=page_height_px)
        self._zoom_mode = "fit_page"
        return self._zoom

    def _fit_zoom(self, *, viewport_extent: float, page_extent: float) -> float:
        if viewport_extent <= 0:
            raise ValueError("viewport extent must be greater than zero.")
        if page_extent <= 0:
            raise ValueError("page extent must be greater than zero.")
        computed = viewport_extent / page_extent
        return min(max(computed, self._zoom_limits.minimum), self._zoom_limits.maximum)

    def _default_zoom(self) -> float:
        return min(max(1.0, self._zoom_limits.minimum), self._zoom_limits.maximum)
