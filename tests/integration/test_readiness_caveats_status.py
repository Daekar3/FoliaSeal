"""Offscreen Qt proof that changed source identity blocks signing readiness first."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from foliaseal.application.document_source_monitor import DocumentSourceMonitor
from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
)
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from foliaseal.domain.models import SignatureAppearance
from foliaseal.presentation.qt.signing_shell import SigningShellAdapter
from foliaseal.presentation.qt.signing_workspace_properties_panel import SignaturePropertiesPanel
from tests.support.signing_builders import write_test_pdf


def test_real_qt_properties_panel_prioritizes_changed_source_safety(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-readiness-caveats-test"])

    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(source),
        output_pdf_path=str(tmp_path / "signed.pdf"),
        certificate_path="",
        passphrase="",
        tsa_url="",
        timestamp_required=False,
        signature_appearance=SignatureAppearance(),
        document_source_monitor=DocumentSourceMonitor.for_path(source),
    )
    panel = SignaturePropertiesPanel(
        bindings=SigningShellAdapter()._load_bindings(),
        workflow=workflow,
        reusable_objects=ReusableSigningObjects(
            InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
        ),
    )
    try:
        source.write_bytes(source.read_bytes() + b"changed")
        readiness = panel.readiness()
        assert readiness.stage.value == "document_safety"
        assert readiness.recommended_action.value == "review_document_safety"
        assert readiness.can_sign is False
        assert "changed on disk" in readiness.detail
    finally:
        panel.dispose()
        app.processEvents()
        if created_app:
            app.quit()
