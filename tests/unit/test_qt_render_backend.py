import pytest

from pdf_signer.infra.render import QtPdfRenderBackend, RenderPageRequest


def test_qt_backend_reports_unavailable_when_qt_bindings_missing() -> None:
    backend = QtPdfRenderBackend()

    diagnostic = backend.diagnostics()

    assert diagnostic.backend_name == "qtpdf-render-backend"
    assert diagnostic.available is False
    assert "unavailable" in diagnostic.message


def test_qt_backend_raises_file_not_found_before_binding_usage(tmp_path) -> None:
    backend = QtPdfRenderBackend()
    missing = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError, match="Document does not exist"):
        backend.get_page_geometry(str(missing), page_index=0)


def test_qt_backend_rejects_non_positive_zoom(tmp_path) -> None:
    backend = QtPdfRenderBackend()
    fake_pdf = tmp_path / "sample.pdf"
    fake_pdf.write_bytes(b"%PDF-1.7\n")

    with pytest.raises(ValueError, match="zoom"):
        backend.render_page(
            RenderPageRequest(document_path=str(fake_pdf), page_index=0, zoom=0.0)
        )
