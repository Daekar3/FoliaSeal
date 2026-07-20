from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from foliaseal.infra.render import (
    PdfPageGeometry,
    PopplerPdfRenderBackend,
    RenderBackendDiagnostic,
    RenderPageRequest,
)


class _GeometryBackend:
    def diagnostics(self) -> RenderBackendDiagnostic:
        return RenderBackendDiagnostic("geometry", True, "available")

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        return PdfPageGeometry((0.0, 0.0, 612.0, 792.0), (0.0, 0.0, 612.0, 792.0), 0)

    def render_page(self, request: RenderPageRequest):  # pragma: no cover - protocol helper
        raise AssertionError("Poppler owns page rasterisation")


class _UnavailableGeometryBackend(_GeometryBackend):
    def diagnostics(self) -> RenderBackendDiagnostic:
        return RenderBackendDiagnostic("geometry", False, "Qt geometry unavailable")


def test_poppler_backend_delegates_geometry_to_qt_compatible_backend() -> None:
    backend = PopplerPdfRenderBackend(geometry_backend=_GeometryBackend())

    geometry = backend.get_page_geometry("example.pdf", 0)

    assert geometry.crop_box == (0.0, 0.0, 612.0, 792.0)


def test_poppler_backend_rejects_invalid_zoom_before_running_command(tmp_path: Path) -> None:
    document = tmp_path / "sample.pdf"
    document.write_bytes(b"%PDF-1.7\n")
    backend = PopplerPdfRenderBackend(geometry_backend=_GeometryBackend())

    with pytest.raises(ValueError, match="zoom"):
        backend.render_page(RenderPageRequest(str(document), 0, 0.0))


def test_poppler_backend_reports_missing_executable(monkeypatch) -> None:
    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.shutil.which",
        lambda _: None,
    )

    diagnostic = PopplerPdfRenderBackend(geometry_backend=_GeometryBackend()).diagnostics()

    assert not diagnostic.available
    assert "pdftoppm" in diagnostic.message


def test_poppler_backend_reports_unavailable_geometry(monkeypatch) -> None:
    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.shutil.which",
        lambda _: "/usr/bin/pdftoppm",
    )

    diagnostic = PopplerPdfRenderBackend(
        geometry_backend=_UnavailableGeometryBackend()
    ).diagnostics()

    assert not diagnostic.available
    assert "Qt geometry unavailable" in diagnostic.message


def test_poppler_backend_returns_opaque_rgba_raster(monkeypatch, tmp_path: Path) -> None:
    document = tmp_path / "sample.pdf"
    document.write_bytes(b"%PDF-1.7\n")
    backend = PopplerPdfRenderBackend(geometry_backend=_GeometryBackend())

    def fake_run(command, **kwargs):
        assert command[0] == "/usr/bin/pdftoppm"
        assert command[command.index("-f") + 1] == "2"
        assert command[command.index("-r") + 1] == "144.0"
        output_prefix = Path(command[-1])
        Image.new("RGB", (3, 2), color=(12, 34, 56)).save(output_prefix.with_suffix(".png"))
        return type("Completed", (), {"returncode": 0, "stderr": "", "stdout": ""})()

    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.shutil.which",
        lambda _: "/usr/bin/pdftoppm",
    )
    monkeypatch.setattr("foliaseal.infra.render.poppler_backend.subprocess.run", fake_run)

    result = backend.render_page(RenderPageRequest(str(document), 1, 2.0))

    assert (result.width_px, result.height_px) == (3, 2)
    assert result.rgba_bytes == bytes((12, 34, 56, 255)) * 6


def test_poppler_backend_surfaces_command_failure(monkeypatch, tmp_path: Path) -> None:
    document = tmp_path / "sample.pdf"
    document.write_bytes(b"%PDF-1.7\n")
    backend = PopplerPdfRenderBackend(geometry_backend=_GeometryBackend())
    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.shutil.which",
        lambda _: "/usr/bin/pdftoppm",
    )
    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"returncode": 1, "stderr": "bad PDF", "stdout": ""}
        )(),
    )

    with pytest.raises(RuntimeError, match="bad PDF"):
        backend.render_page(RenderPageRequest(str(document), 0, 1.0))


def test_poppler_backend_rejects_missing_output_image(monkeypatch, tmp_path: Path) -> None:
    document = tmp_path / "sample.pdf"
    document.write_bytes(b"%PDF-1.7\n")
    backend = PopplerPdfRenderBackend(geometry_backend=_GeometryBackend())
    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.shutil.which",
        lambda _: "/usr/bin/pdftoppm",
    )
    monkeypatch.setattr(
        "foliaseal.infra.render.poppler_backend.subprocess.run",
        lambda *args, **kwargs: type(
            "Completed", (), {"returncode": 0, "stderr": "", "stdout": ""}
        )(),
    )

    with pytest.raises(RuntimeError, match="without producing"):
        backend.render_page(RenderPageRequest(str(document), 0, 1.0))
