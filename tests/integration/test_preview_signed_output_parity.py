"""Rendered preview and signed-appearance parity evidence."""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
from foliaseal.application.signature_image_import import ManagedSignatureImageStore
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from foliaseal.application.signing_preview_renderer import render_canonical_signature_preview
from foliaseal.domain.models import SignatureRect
from foliaseal.presentation.qt.phase3_harness import _render_signed_annotation_appearance_direct
from tests.support.signing_builders import (
    build_signature_appearance,
    write_test_pdf,
    write_test_pkcs12,
)


def _qt_app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(["foliaseal-preview-parity-test"])
    return app


def _render_and_sign(
    tmp_path: Path,
    *,
    appearance,
):
    input_pdf = tmp_path / "input.pdf"
    output_pdf = tmp_path / "output.pdf"
    certificate = tmp_path / "cert.p12"
    write_test_pdf(input_pdf)
    write_test_pkcs12(certificate, passphrase="secret", common_name="Test User")

    workflow = SigningDraftWorkflow(
        input_pdf_path=str(input_pdf),
        output_pdf_path=str(output_pdf),
        certificate_path=str(certificate),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=False,
        certificate_alias="signing-cert",
    )
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(
        SignatureRect(
            page_index=0,
            left_pt=24.0,
            bottom_pt=36.0,
            width_pt=620.0,
            height_pt=180.0,
        )
    )
    preview = workflow.preview()
    assert preview.can_submit is True, preview.issues
    request = workflow.build_signing_request()
    canonical = render_canonical_signature_preview(
        preview,
        zoom=2.0,
        flatten_to_white=False,
    )
    assert canonical is not None

    result = build_phase3_signing_executor().execute(request)
    assert result.success is True, result
    signed = _render_signed_annotation_appearance_direct(
        output_pdf_path=str(output_pdf),
        artifacts_dir=str(tmp_path),
        artifact_basename="preview-parity",
        zoom=2.0,
    )
    assert signed["error"] is None, signed
    assert signed["image_path"] is not None
    return canonical, Path(signed["image_path"])


def test_canonical_preview_matches_actual_signed_annotation_raster(tmp_path: Path) -> None:
    """The final signed appearance must be pixel-identical to the frozen preview."""
    _qt_app()
    canonical, signed_path = _render_and_sign(
        tmp_path,
        appearance=build_signature_appearance(show_field_names=True),
    )
    preview_path = Path(canonical.image_path)
    try:
        with Image.open(preview_path) as preview_image, Image.open(signed_path) as signed_image:
            preview_rgba = preview_image.convert("RGBA")
            signed_rgba = signed_image.convert("RGBA")
            assert preview_rgba.size == signed_rgba.size
            assert ImageChops.difference(preview_rgba, signed_rgba).getbbox() is None
    finally:
        shutil.rmtree(preview_path.parent, ignore_errors=True)


@pytest.mark.parametrize("preserve_alpha", [True, False])
def test_managed_image_alpha_mode_matches_signed_annotation_raster(
    tmp_path: Path,
    preserve_alpha: bool,
) -> None:
    """Both managed image alpha policies are represented by the signed appearance."""
    _qt_app()
    stamp = tmp_path / "stamp.png"
    Image.new("RGBA", (96, 48), (0, 80, 160, 190)).save(stamp)
    managed_stamp = ManagedSignatureImageStore(tmp_path / "catalog").import_image(
        stamp,
        preserve_alpha=preserve_alpha,
    )
    with Image.open(managed_stamp) as managed_image:
        managed_alpha = managed_image.convert("RGBA").getchannel("A")
        if preserve_alpha:
            assert managed_alpha.getextrema()[0] < 255
        else:
            assert managed_alpha.getextrema() == (255, 255)
    appearance = replace(
        build_signature_appearance(
            image_stamp_path=str(managed_stamp),
            show_field_names=True,
        ),
        preserve_image_alpha=preserve_alpha,
    )
    canonical, signed_path = _render_and_sign(tmp_path, appearance=appearance)
    preview_path = Path(canonical.image_path)
    try:
        with Image.open(preview_path) as preview_image, Image.open(signed_path) as signed_image:
            preview_rgba = preview_image.convert("RGBA")
            signed_rgba = signed_image.convert("RGBA")
            assert preview_rgba.size == signed_rgba.size
            assert ImageChops.difference(preview_rgba, signed_rgba).getbbox() is None
    finally:
        shutil.rmtree(preview_path.parent, ignore_errors=True)
