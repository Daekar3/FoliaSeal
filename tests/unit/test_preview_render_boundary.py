from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
from foliaseal.application.preview_render_boundary import (
    PreviewRasterRequest,
    PreviewRasterResult,
    RenderedInkMeasurementRequest,
    RenderedInkMeasurementResult,
)
from foliaseal.application.signing_preview_renderer import (
    _render_preview_style,
)


def test_preview_raster_result_validates_rgba_payload() -> None:
    assert PreviewRasterResult(2, 1, b"\x00" * 8).width_px == 2
    with pytest.raises(ValueError, match="byte length"):
        PreviewRasterResult(2, 1, b"\x00" * 7)
    with pytest.raises(ValueError, match="dimensions"):
        PreviewRasterResult(0, 1, b"")


def test_rendered_ink_measurement_request_keeps_neutral_data_only(tmp_path: Path) -> None:
    request = RenderedInkMeasurementRequest(
        preview_image_path=tmp_path / "preview.png",
        text_widget_bounds={"x": 1, "y": 2, "width": 30, "height": 10},
        text_color_rgba=(12, 13, 14, 255),
        reference_text_content_bounds={"x": 3, "y": 4, "width": 5, "height": 6},
    )
    result = RenderedInkMeasurementResult(bounds_px={"x": 4, "y": 5, "width": 2, "height": 3})
    assert request.preview_image_path == tmp_path / "preview.png"
    assert result.error is None


def test_canonical_renderer_accepts_neutral_raster_port(monkeypatch, tmp_path: Path) -> None:
    requests: list[PreviewRasterRequest] = []

    class _FakeRenderer:
        def render_page(self, request: PreviewRasterRequest) -> PreviewRasterResult:
            requests.append(request)
            return PreviewRasterResult(4, 3, b"\x00" * 48)

    from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
    from foliaseal.domain.models import SignatureRect
    from tests.support.signing_builders import build_signature_appearance

    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )
    workflow.set_signature_appearance(build_signature_appearance())
    workflow.set_signature_rect(SignatureRect(0, 24.0, 18.0, 180.0, 48.0))

    # Exercise the low-level port call without depending on a Qt installation.
    from foliaseal.application.signing_preview_renderer import _canonical_preview_stamp_style

    style = _canonical_preview_stamp_style(
        workflow.preview(),
        include_text=True,
        include_stamp=True,
        include_border=True,
        use_horizontal_ink_reservation=False,
    )
    _render_preview_style(
        style=style,
        signature_rect=workflow.preview().signature_rect,
        zoom=1.0,
        output_path=tmp_path / "preview.png",
        render_port=_FakeRenderer(),
        flatten_to_white=True,
    )
    assert requests and requests[0].page_index == 0
    assert requests[0].zoom == 1.0


def test_application_preview_modules_do_not_import_infra_at_import_time() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = """
import sys
import foliaseal.application.preview_render_boundary
import foliaseal.application.signing_preview_renderer
import foliaseal.application.horizontal_signature_reservation
import foliaseal.application.visible_signature_layout
assert not any(
    name == 'foliaseal.infra.render' or name.startswith('foliaseal.infra.render.')
    for name in sys.modules
)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_signing_executor_carries_composed_preview_port() -> None:
    fake_port = object()
    executor = build_phase3_signing_executor(render_port=fake_port)
    assert executor.use_case.preview_render_port is fake_port
