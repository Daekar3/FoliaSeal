"""Deterministic Qt adapter walkthrough for preview readiness states."""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

import pytest

from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.models import (
    SignatureFieldBinding,
    SignatureFieldSource,
    SignatureRect,
)
from foliaseal.presentation.qt.signing_shell import SigningShellAdapter
from foliaseal.presentation.qt.signing_workspace_properties_panel import SignaturePropertiesPanel
from tests.support.signing_builders import (
    build_reusable_objects_fixture,
    build_signature_appearance,
    build_signature_preset_catalog,
    write_test_pdf,
    write_test_pkcs12,
)


def test_preview_readiness_walkthrough_projects_blockers_and_frozen_request_time(
    tmp_path: Path,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-preview-readiness-walkthrough"])

    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    certificate = tmp_path / "certificate.p12"
    write_test_pkcs12(certificate, passphrase="secret")
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(source),
        output_pdf_path=str(tmp_path / "signed.pdf"),
        certificate_path=str(certificate),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=False,
    )
    workflow.set_signature_appearance(build_signature_appearance())
    reusable_objects = build_reusable_objects_fixture(
        preset_catalog=build_signature_preset_catalog()
    )
    panel = SignaturePropertiesPanel(
        bindings=SigningShellAdapter().bindings,
        workflow=workflow,
        reusable_objects=reusable_objects,
    )

    try:
        placement = panel.readiness()
        assert placement.stage.value == "place_signature"
        assert placement.recommended_action.value == "place_signature"
        assert placement.can_sign is False
        panel.set_signature_rect(
            SignatureRect(
                page_index=0,
                left_pt=24.0,
                bottom_pt=36.0,
                width_pt=260.0,
                height_pt=120.0,
            )
        )

        unsupported = replace(
            build_signature_appearance(),
            common_name=SignatureFieldBinding(
                source=SignatureFieldSource.OVERRIDE,
                override_text="Alice ☃",
            ),
        )
        panel.set_signature_appearance(unsupported)
        glyph_block = panel.readiness()
        assert glyph_block.stage.value == "review_readiness"
        assert glyph_block.can_sign is False
        assert "unsupported character '☃' (U+2603)" in glyph_block.detail
        assert "Common name" in panel.validation_text()

        panel.set_signature_appearance(build_signature_appearance())
        panel.set_signature_rect(
            SignatureRect(
                page_index=0,
                left_pt=35.84,
                bottom_pt=428.48,
                width_pt=261.63,
                height_pt=20.99,
            )
        )
        fit_block = panel.readiness()
        assert fit_block.stage.value == "review_readiness"
        assert fit_block.can_sign is False
        assert "fit" in fit_block.detail.lower()

        panel.set_signature_rect(
            SignatureRect(
                page_index=0,
                left_pt=24.0,
                bottom_pt=36.0,
                width_pt=260.0,
                height_pt=120.0,
            )
        )
        ready = panel.readiness()
        assert ready.stage.value == "ready"
        assert ready.can_sign is True
        preview = panel.preview
        preview_time = workflow.preview_signing_time
        repeated_preview = panel.preview
        assert repeated_preview.can_submit is True
        assert workflow.preview_signing_time == preview_time
        request = workflow.build_signing_request()
        assert preview.can_submit is True
        assert panel.preview_text()
        assert preview_time is not None
        assert request.signing_time == preview_time
    finally:
        panel.dispose()
        panel.container.close()
        app.processEvents()
        if created_app:
            app.quit()
