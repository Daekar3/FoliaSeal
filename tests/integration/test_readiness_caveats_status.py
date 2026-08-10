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
    from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-readiness-caveats-test"])

    source = tmp_path / "source.pdf"
    write_test_pdf(source)
    canvas = QWidget()
    rail = QWidget()
    central = QWidget()
    row = QHBoxLayout(central)
    row.setContentsMargins(0, 0, 0, 0)
    row.addWidget(canvas, 1)
    row.addWidget(rail)
    rail_layout = QVBoxLayout(rail)
    rail_layout.setContentsMargins(0, 0, 0, 0)
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
        bindings=SigningShellAdapter().bindings,
        workflow=workflow,
        reusable_objects=ReusableSigningObjects(
            InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
        ),
        source_safety_overlay_parent=canvas,
        )
    rail_layout.addWidget(panel.container)
    central.resize(1000, 600)
    central.show()
    app.processEvents()
    canvas_geometry = canvas.geometry()
    rail_geometry = rail.geometry()
    panel_geometry = panel.container.geometry()
    panel._on_source_ignore = lambda: (  # noqa: SLF001
        workflow.document_source_monitor.acknowledge_current_source(),
        panel.refresh_source_safety(),
    )
    panel._source_ignore_button.clicked.connect(panel._on_source_ignore)  # noqa: SLF001
    try:
        source.write_bytes(source.read_bytes() + b"changed")
        readiness = panel.readiness()
        assert readiness.stage.value == "document_safety"
        assert readiness.recommended_action.value == "review_document_safety"
        assert readiness.can_sign is False
        assert "changed on disk" in readiness.detail
        panel.refresh_source_safety()
        assert not panel._source_safety_container.isHidden()  # noqa: SLF001
        assert panel._source_safety_container.parentWidget() is canvas  # noqa: SLF001
        assert panel._source_safety_container.geometry().x() == 12  # noqa: SLF001
        assert panel._source_safety_container.geometry().y() == 12  # noqa: SLF001
        assert panel._source_safety_container.geometry().width() == canvas.width() - 24  # noqa: SLF001
        assert panel.container.layout().count() == 4  # noqa: SLF001
        assert canvas.geometry() == canvas_geometry
        assert rail.geometry() == rail_geometry
        assert panel.container.geometry() == panel_geometry
        central.resize(1120, 640)
        app.processEvents()
        assert panel._source_safety_container.parentWidget() is canvas  # noqa: SLF001
        assert panel._source_safety_container.geometry().width() == canvas.width() - 24  # noqa: SLF001
        assert panel._source_safety_container.geometry().height() <= canvas.height() - 24  # noqa: SLF001
        assert not panel._source_reload_button.isHidden()  # noqa: SLF001
        assert not panel._source_ignore_button.isHidden()  # noqa: SLF001
        assert panel._source_locate_button.isHidden()  # noqa: SLF001
        panel._source_ignore_button.click()  # noqa: SLF001
        assert panel._source_safety_container.isHidden()  # noqa: SLF001
    finally:
        panel.dispose()
        central.close()
        app.processEvents()
        if created_app:
            app.quit()
