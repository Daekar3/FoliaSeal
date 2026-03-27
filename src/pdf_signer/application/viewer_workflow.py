"""Workflow helper to wire render backend, view transforms, and timing metrics."""

from __future__ import annotations

from dataclasses import dataclass

from pdf_signer.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewRect,
    ViewTransform,
    validate_pdf_rect_within_page,
    view_rect_to_pdf_rect,
)
from pdf_signer.application.performance_timing import ViewerPerformanceTracker
from pdf_signer.application.viewer_session import ViewerSession
from pdf_signer.infra.render import PdfRenderBackend, RenderPageRequest, RenderPageResult


@dataclass(frozen=True)
class ViewerRenderSnapshot:
    """Current render/frame state required by placement interactions."""

    page_index: int
    zoom: float
    pan_x: float
    pan_y: float
    page_box: PageBox
    rotation: int
    image_width_px: int
    image_height_px: int


class ViewerWorkflow:
    """Coordinate viewer rendering and placement conversion logic."""

    def __init__(
        self,
        *,
        document_path: str,
        render_backend: PdfRenderBackend,
        session: ViewerSession,
        performance_tracker: ViewerPerformanceTracker | None = None,
    ) -> None:
        self._document_path = document_path
        self._render_backend = render_backend
        self._session = session
        self._performance_tracker = performance_tracker or ViewerPerformanceTracker()
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._last_snapshot: ViewerRenderSnapshot | None = None

    @property
    def snapshot(self) -> ViewerRenderSnapshot | None:
        return self._last_snapshot

    @property
    def timing_tracker(self) -> ViewerPerformanceTracker:
        return self._performance_tracker

    def set_pan(self, *, pan_x: float, pan_y: float) -> None:
        self._pan_x = pan_x
        self._pan_y = pan_y

    def render_current_page(
        self,
        *,
        elapsed_ms: float | None = None,
        navigation: bool = False,
    ) -> RenderPageResult:
        request = RenderPageRequest(
            document_path=self._document_path,
            page_index=self._session.current_page,
            zoom=self._session.zoom,
        )
        render = self._render_backend.render_page(request)
        geometry = self._render_backend.get_page_geometry(
            self._document_path,
            self._session.current_page,
        )

        page_box = PageBox(*geometry.crop_box)
        page_box.validate()
        self._last_snapshot = ViewerRenderSnapshot(
            page_index=self._session.current_page,
            zoom=self._session.zoom,
            pan_x=self._pan_x,
            pan_y=self._pan_y,
            page_box=page_box,
            rotation=geometry.rotation,
            image_width_px=render.width_px,
            image_height_px=render.height_px,
        )

        if elapsed_ms is not None:
            if navigation:
                self._performance_tracker.record_navigation(elapsed_ms)
            else:
                self._performance_tracker.record_first_render(elapsed_ms)

        return render

    def go_next_page(self, *, elapsed_ms: float | None = None) -> RenderPageResult:
        previous = self._session.current_page
        current = self._session.go_next()
        return self.render_current_page(elapsed_ms=elapsed_ms, navigation=current != previous)

    def go_previous_page(self, *, elapsed_ms: float | None = None) -> RenderPageResult:
        previous = self._session.current_page
        current = self._session.go_previous()
        return self.render_current_page(elapsed_ms=elapsed_ms, navigation=current != previous)

    def jump_to_page(self, page_index: int, *, elapsed_ms: float | None = None) -> RenderPageResult:
        previous = self._session.current_page
        current = self._session.jump_to_page(page_index)
        return self.render_current_page(elapsed_ms=elapsed_ms, navigation=current != previous)

    def selection_to_pdf_rect(self, *, selection: ViewRect) -> PdfRect:
        snapshot = self._require_snapshot()
        pdf_rect = view_rect_to_pdf_rect(
            view_rect=selection,
            transform=ViewTransform(zoom=snapshot.zoom, pan_x=self._pan_x, pan_y=self._pan_y),
            page_box=snapshot.page_box,
            rotation=snapshot.rotation,
        )
        if not validate_pdf_rect_within_page(pdf_rect, page_box=snapshot.page_box):
            raise ValueError("Selection is out of page bounds.")
        return pdf_rect

    def _require_snapshot(self) -> ViewerRenderSnapshot:
        if self._last_snapshot is None:
            raise RuntimeError("No rendered page is available yet.")
        return self._last_snapshot
