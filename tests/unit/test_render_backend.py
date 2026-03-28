import pytest

from foliaseal.infra.render import NullPdfRenderBackend, RenderPageRequest


def test_null_render_backend_reports_unavailable_diagnostic() -> None:
    backend = NullPdfRenderBackend()

    diagnostic = backend.diagnostics()

    assert diagnostic.available is False
    assert "No render backend configured" in diagnostic.message


def test_null_render_backend_raises_actionable_error_when_used() -> None:
    backend = NullPdfRenderBackend()

    with pytest.raises(RuntimeError, match="No render backend configured"):
        backend.render_page(
            RenderPageRequest(document_path="example.pdf", page_index=0, zoom=1.0)
        )
