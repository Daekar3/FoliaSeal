import pytest

from pdf_signer.infra.render import QtPdfRenderBackend, RenderPageRequest
from pdf_signer.infra.render.qt_backend import _QtBindings


def test_qt_backend_reports_unavailable_when_qt_bindings_missing(monkeypatch) -> None:
    def _missing_bindings(self):
        self._bindings_error = "PySide6 import failed"
        return None

    monkeypatch.setattr(QtPdfRenderBackend, "_load_bindings", _missing_bindings)
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


def test_qt_backend_geometry_uses_qpdfdocument_page_apis(monkeypatch) -> None:
    class _Size:
        def toTuple(self):
            return (612.0, 792.0)

    class _Document:
        def pageCount(self):
            return 1

        def pagePointSize(self, page_index):
            assert page_index == 0
            return _Size()

    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=object,
        qsize=object,
        qpdf_document_render_options=object,
    )
    monkeypatch.setattr(backend, "_open_document", lambda _: _Document())

    geometry = backend.get_page_geometry("any.pdf", page_index=0)

    assert geometry.media_box == (0.0, 0.0, 612.0, 792.0)
    assert geometry.crop_box == (0.0, 0.0, 612.0, 792.0)
    assert geometry.rotation == 0


def test_qt_backend_render_uses_qpdfdocument_render(monkeypatch) -> None:
    class _Bits:
        def tobytes(self, _size):
            return b"\x00" * 16

    class _RenderedImage:
        def convertToFormat(self, _format):
            return self

        def bits(self):
            return _Bits()

    class _SizePoints:
        def toTuple(self):
            return (2.0, 2.0)

    class _Document:
        def __init__(self):
            self.calls = []

        def pageCount(self):
            return 1

        def pagePointSize(self, page_index):
            assert page_index == 0
            return _SizePoints()

        def render(self, page_index, image_size, render_opts):
            self.calls.append((page_index, image_size, render_opts))
            return _RenderedImage()

    class _QSize:
        def __init__(self, width, height):
            self.width = width
            self.height = height

    class _QImage:
        Format_RGBA8888 = 1

        def __init__(self, width, height, _fmt):
            self.width = width
            self.height = height

        def fill(self, _value):
            return None

    class _RenderOptions:
        pass

    document = _Document()
    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=_QImage,
        qsize=_QSize,
        qpdf_document_render_options=_RenderOptions,
    )
    monkeypatch.setattr(backend, "_open_document", lambda _: document)

    result = backend.render_page(
        RenderPageRequest(document_path="any.pdf", page_index=0, zoom=1.0)
    )

    assert result.width_px == 2
    assert result.height_px == 2
    assert len(result.rgba_bytes) == 16
    assert len(document.calls) == 1
    page_index, image_size, render_opts = document.calls[0]
    assert page_index == 0
    assert image_size.width == 2
    assert image_size.height == 2
    assert isinstance(render_opts, _RenderOptions)
