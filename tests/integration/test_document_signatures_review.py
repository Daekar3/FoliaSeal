"""Offscreen proof for the AppFrame-owned Document Signatures window."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review import (
    DocumentReviewSummary,
    DocumentSignatureReviewItem,
)
from foliaseal.application.document_review_workspace import DocumentReviewWorkspaceSession
from foliaseal.application.document_text_search import DocumentTextSearchSession
from foliaseal.application.document_text_selection import DocumentTextSelectionSession
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId
from foliaseal.presentation.qt.signing_workspace_review_bridge import SigningWorkspaceReviewBridge


def test_document_signatures_window_is_modeless_and_cleans_up(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-document-signatures-test"])

    items = (
        DocumentSignatureReviewItem(
            label="Approval",
            signer_subject="CN=Alice Example",
            cryptographic_validation_passed=True,
            detail="Integrity verified locally.",
            drill_in_detail="Claimed signing time: 2026-08-10 12:00 UTC.",
            signature_id="Approval:signed",
            kind="signed_visible",
            page_index=0,
            highlight_rect=PdfRect(x1=10, y1=20, x2=120, y2=70),
        ),
        DocumentSignatureReviewItem(
            label="Countersignature",
            signer_subject=None,
            cryptographic_validation_passed=None,
            detail="This signature field is empty.",
            drill_in_detail="No signer or integrity result exists.",
            signature_id="Countersignature:unsigned",
            kind="unsigned_field",
            field_name="Countersignature",
        ),
    )
    summary = DocumentReviewSummary(
        headline="Signature review",
        detail="Found one embedded signature and one empty field.",
        signature_count=1,
        signature_items=items,
    )
    class _SearchEngine:
        def search(self, _input_pdf_path: str, _query: str):
            return ()

    class _SelectionEngine:
        def select(self, _input_pdf_path: str, *, page_index: int, selection_rect: PdfRect):
            del page_index, selection_rect
            return None

    review_session = DocumentReviewWorkspaceSession(
        document_review_inspector=SimpleNamespace(inspect=lambda _path: summary),
        document_text_search_session=DocumentTextSearchSession(
            input_pdf_path="/tmp/review.pdf",
            search_engine=_SearchEngine(),
        ),
        document_text_selection_session=DocumentTextSelectionSession(
            input_pdf_path="/tmp/review.pdf",
            selection_engine=_SelectionEngine(),
        ),
        input_pdf_path="/tmp/review.pdf",
    )
    review_session.load()

    class _Sidebar:
        def apply_document_review_workspace_state(self, _state, *, can_copy_text: bool) -> None:
            del can_copy_text

    class _Viewer:
        def __init__(self) -> None:
            self.review_overlay = None

        def set_review_highlight_overlay(self, *, page_index: int, highlight_rect: PdfRect) -> None:
            self.review_overlay = (page_index, highlight_rect)

        def clear_review_highlight_overlay(self) -> None:
            self.review_overlay = None

    viewer = _Viewer()
    jumped_pages: list[int] = []
    bridge = SigningWorkspaceReviewBridge(
        sidebar=_Sidebar(),
        viewer_widget=viewer,
        document_review_workspace=review_session,
        on_jump_to_page_index=jumped_pages.append,
        can_copy_text=False,
    )

    class _Session:
        def __init__(self) -> None:
            self.selected: list[str] = []
            self.cleared = 0
            self.focused = 0

        def document_review_state(self):
            return review_session.current_state()

        def select_document_review_item(self, signature_id: str):
            self.selected.append(signature_id)
            bridge.select_review_item(signature_id)
            return review_session.current_state()

        def clear_document_review_highlight(self) -> None:
            self.cleared += 1
            bridge.clear_review_highlight()

        def focus(self) -> None:
            self.focused += 1

    session = _Session()
    frame = QtAppFrameAdapter().create_frame(
        app_settings_store=None,
        certificate_catalog_store=None,
        preset_catalog_store=None,
    )
    frame._workspace_host = SimpleNamespace(  # type: ignore[assignment]
        active=lambda: SimpleNamespace(session=session),
    )
    frame.window.show()
    app.processEvents()

    action = frame.command_actions()[AppFrameCommandId.DOCUMENT_SIGNATURES]
    action.setEnabled(True)
    action.trigger()
    app.processEvents()

    dialog = frame.document_signatures_dialog
    assert dialog is not None
    assert dialog.controls.dialog.isVisible()
    assert not dialog.controls.dialog.isModal()
    assert dialog.controls.item_list.count() == 2
    assert dialog.controls.item_list.item(1).text().endswith("— unsigned")

    dialog.controls.item_list.setCurrentRow(1)
    app.processEvents()
    dialog.controls.item_list.setCurrentRow(0)
    app.processEvents()
    assert session.selected == [
        "Countersignature:unsigned",
        "Approval:signed",
    ]
    assert session.focused == 2
    assert jumped_pages == [0]
    assert viewer.review_overlay == (0, PdfRect(x1=10, y1=20, x2=120, y2=70))
    dialog.controls.item_list.setCurrentRow(1)
    app.processEvents()
    assert viewer.review_overlay is None
    dialog.controls.item_list.setCurrentRow(0)
    app.processEvents()
    assert session.selected == [
        "Countersignature:unsigned",
        "Approval:signed",
        "Countersignature:unsigned",
        "Approval:signed",
    ]
    assert session.focused == 4
    assert viewer.review_overlay == (0, PdfRect(x1=10, y1=20, x2=120, y2=70))
    assert "Integrity verified locally." in dialog.controls.detail_text.toPlainText()

    dialog.controls.dialog.close()
    app.processEvents()
    assert frame.document_signatures_dialog is None
    assert session.cleared == 1
    assert viewer.review_overlay is None

    replacement_dialog = frame.show_document_signatures()
    assert replacement_dialog is not None
    app.processEvents()
    frame._close_document_signatures()
    app.processEvents()
    assert frame.document_signatures_dialog is None
    assert session.cleared == 2
    assert viewer.review_overlay is None

    frame._close_document_signatures()
    frame.window.hide()
    app.processEvents()
    if created_app:
        app.quit()
