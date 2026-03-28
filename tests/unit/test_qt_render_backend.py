import pytest

from foliaseal.infra.render import QtPdfRenderBackend, RenderPageRequest
from foliaseal.infra.render.qt_backend import (
    PdfPageGeometryUnavailableError,
    _load_pdf_page_metadata,
    _QtBindings,
)


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
    class _Document:
        def pageCount(self):
            return 1

    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=object,
        qsize=object,
        qpdf_document_render_options=object,
    )
    monkeypatch.setattr(backend, "_open_document", lambda _: _Document())
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._document_signature",
        lambda path: (123, 456),
    )
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._load_pdf_page_metadata",
        lambda **_: type(
            "_Metadata",
            (),
            {
                "media_box": (0.0, 0.0, 612.0, 792.0),
                "crop_box": (18.0, 36.0, 594.0, 756.0),
                "rotation": 90,
            },
        )(),
    )

    geometry = backend.get_page_geometry("any.pdf", page_index=0)

    assert geometry.media_box == (0.0, 0.0, 612.0, 792.0)
    assert geometry.crop_box == (18.0, 36.0, 594.0, 756.0)
    assert geometry.rotation == 90


def test_qt_backend_geometry_caches_metadata_for_repeated_requests(monkeypatch) -> None:
    class _Document:
        def pageCount(self):
            return 2

    calls: list[int] = []

    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=object,
        qsize=object,
        qpdf_document_render_options=object,
    )
    backend._metadata_cache = {}
    monkeypatch.setattr(backend, "_open_document", lambda _: _Document())
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._document_signature",
        lambda path: (123, 456),
    )

    def fake_load_pdf_page_metadata(*, document_path, page_index):
        calls.append(page_index)
        return type(
            "_Metadata",
            (),
            {
                "media_box": (0.0, 0.0, 612.0, 792.0),
                "crop_box": (0.0, 0.0, 612.0, 792.0),
                "rotation": 0,
            },
        )()

    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._load_pdf_page_metadata",
        fake_load_pdf_page_metadata,
    )

    first = backend.get_page_geometry("any.pdf", page_index=0)
    second = backend.get_page_geometry("any.pdf", page_index=0)

    assert first == second
    assert calls == [0]


def test_qt_backend_geometry_invalidates_metadata_cache_when_file_signature_changes(
    monkeypatch,
) -> None:
    class _Document:
        def pageCount(self):
            return 1

    signatures = iter([(123, 456), (124, 456)])
    rotations = iter([0, 90])

    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=object,
        qsize=object,
        qpdf_document_render_options=object,
    )
    backend._metadata_cache = {}
    monkeypatch.setattr(backend, "_open_document", lambda _: _Document())
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._document_signature",
        lambda path: next(signatures),
    )
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._load_pdf_page_metadata",
        lambda **_: type(
            "_Metadata",
            (),
            {
                "media_box": (0.0, 0.0, 612.0, 792.0),
                "crop_box": (0.0, 0.0, 612.0, 792.0),
                "rotation": next(rotations),
            },
        )(),
    )

    first = backend.get_page_geometry("any.pdf", page_index=0)
    second = backend.get_page_geometry("any.pdf", page_index=0)

    assert first.rotation == 0
    assert second.rotation == 90


def test_qt_backend_geometry_raises_when_parser_fails(
    monkeypatch,
) -> None:
    class _Document:
        def pageCount(self):
            return 1

    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=object,
        qsize=object,
        qpdf_document_render_options=object,
    )
    backend._metadata_cache = {}
    monkeypatch.setattr(backend, "_open_document", lambda _: _Document())
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._document_signature",
        lambda path: (123, 456),
    )
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._load_pdf_page_metadata",
        lambda **_: (_ for _ in ()).throw(ValueError("object stream unsupported")),
    )

    with pytest.raises(PdfPageGeometryUnavailableError, match="object stream unsupported"):
        backend.get_page_geometry("any.pdf", page_index=0)


def test_qt_backend_geometry_retries_after_parser_failure_without_caching_guesswork(
    monkeypatch,
) -> None:
    class _Document:
        def pageCount(self):
            return 1

    backend = QtPdfRenderBackend.__new__(QtPdfRenderBackend)
    backend._bindings_error = None
    backend._bindings = _QtBindings(
        qpdf_document=object,
        qimage=object,
        qsize=object,
        qpdf_document_render_options=object,
    )
    backend._metadata_cache = {}
    monkeypatch.setattr(backend, "_open_document", lambda _: _Document())
    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._document_signature",
        lambda path: (123, 456),
    )

    calls = {"count": 0}

    def fail_parser(**kwargs):
        calls["count"] += 1
        raise ValueError("compressed xref stream unsupported")

    monkeypatch.setattr(
        "foliaseal.infra.render.qt_backend._load_pdf_page_metadata",
        fail_parser,
    )

    with pytest.raises(PdfPageGeometryUnavailableError):
        backend.get_page_geometry("any.pdf", page_index=0)
    with pytest.raises(PdfPageGeometryUnavailableError):
        backend.get_page_geometry("any.pdf", page_index=0)

    assert calls["count"] == 2


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


def test_load_pdf_page_metadata_resolves_inherited_boxes_and_rotation(tmp_path) -> None:
    pdf_path = tmp_path / "metadata.pdf"
    pdf_path.write_bytes(
        b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
"""
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 612 792]"
        b" /CropBox [18 36 594 756] /Rotate 90 >>\n"
        b"""endobj
3 0 obj
<< /Type /Page /Parent 2 0 R >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
"""
    )

    metadata = _load_pdf_page_metadata(document_path=str(pdf_path), page_index=0)

    assert metadata.media_box == (0.0, 0.0, 612.0, 792.0)
    assert metadata.crop_box == (18.0, 36.0, 594.0, 756.0)
    assert metadata.rotation == 90


def test_load_pdf_page_metadata_falls_back_to_media_box_when_crop_missing(tmp_path) -> None:
    pdf_path = tmp_path / "metadata_no_crop.pdf"
    pdf_path.write_bytes(
        b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [10 20 410 620] >>
endobj
trailer
<< /Root 1 0 R >>
%%EOF
"""
    )

    metadata = _load_pdf_page_metadata(document_path=str(pdf_path), page_index=0)

    assert metadata.media_box == (10.0, 20.0, 410.0, 620.0)
    assert metadata.crop_box == (10.0, 20.0, 410.0, 620.0)
    assert metadata.rotation == 0
