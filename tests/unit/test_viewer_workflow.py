import pytest

from pdf_signer.application.coordinate_transform import ViewRect
from pdf_signer.application.viewer_session import ViewerSession
from pdf_signer.application.viewer_workflow import ViewerWorkflow
from pdf_signer.infra.render import PdfPageGeometry, RenderPageRequest, RenderPageResult


class _FakeRenderBackend:
    def __init__(self) -> None:
        self.requests: list[RenderPageRequest] = []

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        self.requests.append(request)
        return RenderPageResult(width_px=200, height_px=100, rgba_bytes=b"\x00" * (200 * 100 * 4))

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        assert document_path.endswith("sample.pdf")
        return PdfPageGeometry(
            media_box=(0.0, 0.0, 100.0, 50.0),
            crop_box=(0.0, 0.0, 100.0, 50.0),
            rotation=0,
        )

    def diagnostics(self):  # pragma: no cover - not needed for this unit test
        raise NotImplementedError


def test_render_current_page_tracks_first_render_and_snapshot() -> None:
    backend = _FakeRenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=3),
    )

    result = workflow.render_current_page(elapsed_ms=40.0)
    snapshot = workflow.snapshot

    assert result.width_px == 200
    assert snapshot is not None
    assert snapshot.page_index == 0
    assert snapshot.zoom == 1.0
    assert workflow.timing_tracker.snapshot().first_render_ms == 40.0
    assert workflow.timing_tracker.snapshot().sample_count == 0


def test_page_navigation_records_navigation_timing() -> None:
    backend = _FakeRenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=3),
    )

    workflow.render_current_page(elapsed_ms=30.0)
    workflow.go_next_page(elapsed_ms=22.0)

    timings = workflow.timing_tracker.snapshot()
    assert timings.first_render_ms == 30.0
    assert timings.sample_count == 1
    assert timings.average_navigation_ms == pytest.approx(22.0)


def test_selection_to_pdf_rect_uses_snapshot_transform_and_bounds() -> None:
    backend = _FakeRenderBackend()
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=backend,
        session=ViewerSession(page_count=1),
    )
    workflow.set_pan(pan_x=0.0, pan_y=0.0)
    workflow.render_current_page()

    rect = workflow.selection_to_pdf_rect(selection=ViewRect(x1=10, y1=10, x2=30, y2=20))

    assert rect.x1 == pytest.approx(10.0)
    assert rect.x2 == pytest.approx(30.0)
    assert rect.y1 == pytest.approx(30.0)
    assert rect.y2 == pytest.approx(40.0)


def test_selection_requires_rendered_snapshot() -> None:
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_FakeRenderBackend(),
        session=ViewerSession(page_count=1),
    )

    with pytest.raises(RuntimeError, match="No rendered page"):
        workflow.selection_to_pdf_rect(selection=ViewRect(x1=0, y1=0, x2=10, y2=10))


def test_selection_rejects_out_of_page_bounds() -> None:
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_FakeRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    workflow.render_current_page()

    with pytest.raises(ValueError, match="out of page bounds"):
        workflow.selection_to_pdf_rect(selection=ViewRect(x1=-20, y1=10, x2=10, y2=20))


def test_selection_uses_live_pan_state_after_render() -> None:
    workflow = ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_FakeRenderBackend(),
        session=ViewerSession(page_count=1),
    )
    workflow.render_current_page()
    workflow.set_pan(pan_x=5.0, pan_y=3.0)

    rect = workflow.selection_to_pdf_rect(selection=ViewRect(x1=10, y1=10, x2=30, y2=20))

    assert rect.x1 == pytest.approx(5.0)
    assert rect.x2 == pytest.approx(25.0)
    assert rect.y1 == pytest.approx(33.0)
    assert rect.y2 == pytest.approx(43.0)
