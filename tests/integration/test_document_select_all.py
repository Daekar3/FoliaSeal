"""Real offscreen Qt coverage for current-page PDF Select All."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.document_review_workspace import DocumentReviewWorkspaceSession
from foliaseal.application.document_text_search import DocumentTextSearchSession
from foliaseal.application.document_text_selection import DocumentTextSelectionSession
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.infra.document_text_selection import QtPdfDocumentTextSelectionEngine
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId
from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspacePort,
    QtSigningWorkspaceSessionPort,
    QtWorkspaceView,
    SigningWorkspaceBootstrap,
    SigningWorkspaceBundle,
)


class _EmptySearchEngine:
    def search(self, input_pdf_path: str, query: str):
        del input_pdf_path, query
        return ()


class _ReviewInspector:
    def inspect(self, input_pdf_path: str) -> DocumentReviewSummary:
        del input_pdf_path
        return DocumentReviewSummary(
            headline="No signatures found",
            detail="This PDF does not currently contain embedded signatures.",
            signature_count=0,
        )


def _write_text_pdf(path: Path) -> None:
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        3: (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        5: (
            b"<< /Length 57 >>\nstream\nBT /F1 18 Tf 72 700 Td "
            b"(Alice Example) Tj ET\nendstream"
        ),
    }
    payload = b"%PDF-1.4\n"
    offsets = [0]
    for object_number in range(1, 6):
        offsets.append(len(payload))
        payload += f"{object_number} 0 obj\n".encode()
        payload += objects[object_number] + b"\nendobj\n"
    xref_offset = len(payload)
    payload += b"xref\n0 6\n0000000000 65535 f \n"
    payload += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    payload += (
        f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    path.write_bytes(payload)


def test_real_offscreen_qt_select_all_returns_current_page_text_and_overlay(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal"])

    source = tmp_path / "text.pdf"
    _write_text_pdf(source)
    review = DocumentReviewWorkspaceSession(
        document_review_inspector=_ReviewInspector(),
        document_text_search_session=DocumentTextSearchSession(
            input_pdf_path=str(source),
            search_engine=_EmptySearchEngine(),
        ),
        document_text_selection_session=DocumentTextSelectionSession(
            input_pdf_path=str(source),
            selection_engine=QtPdfDocumentTextSelectionEngine(),
        ),
        input_pdf_path=str(source),
    )

    review.load()
    transition = review.select_all_text(page_index=0)

    selection = transition.state.document_text.selection_state.selection
    assert selection is not None
    assert selection.page_index == 0
    assert selection.text == "Alice Example"
    assert selection.highlight_rects
    assert transition.effects.highlight_page_index == 0
    assert transition.effects.highlight_rects == selection.highlight_rects
    assert transition.state.document_text.selection_state.can_copy is True

    if created_app:
        app.quit()


def test_real_offscreen_app_frame_select_all_and_copy_use_viewer_fallback(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QWidget

    class SelectAllShell(QWidget):
        def __init__(self, bootstrap: SigningWorkspaceBootstrap) -> None:
            super().__init__()
            self.container = self
            self.status_callback = bootstrap.on_status_change
            source = str(bootstrap.viewer_workflow.document_path)
            self._review = DocumentReviewWorkspaceSession(
                document_review_inspector=_ReviewInspector(),
                document_text_search_session=DocumentTextSearchSession(
                    input_pdf_path=source,
                    search_engine=_EmptySearchEngine(),
                ),
                document_text_selection_session=DocumentTextSelectionSession(
                    input_pdf_path=source,
                    selection_engine=QtPdfDocumentTextSelectionEngine(),
                ),
                input_pdf_path=source,
            )
            self._review.load()
            self.selection_highlights = ()
            self.select_all_calls = 0
            self._page_index = 0

        def has_unsaved_changes(self) -> bool:
            return False

        def discard_draft(self) -> None:
            return None

        def cleanup_recovery_artifact(self) -> None:
            return None

        def clear_session_secrets(self) -> None:
            return None

        def choose_output_pdf_path(self):
            return None

        def has_explicit_output_pdf_path(self) -> bool:
            return False

        def apply_app_settings(self, settings: AppSettings) -> None:
            del settings

        def refresh_certificate_configurations(self) -> CertificateCatalog:
            return CertificateCatalog(schema_version=1)

        def refresh_signature_profiles(self) -> None:
            return None

        def open_reusable_object_editor(self) -> bool:
            return False

        def set_document_text_selection_mode(self, enabled: bool) -> bool:
            transition = self._review.set_text_selection_mode(enabled)
            if callable(self.status_callback):
                self.status_callback("document_text_mode_changed")
            return transition.state.document_text.selection_mode_enabled

        def document_text_selection_mode_enabled(self) -> bool:
            return self._review.current_state().document_text.selection_mode_enabled

        def can_copy_selected_document_text(self) -> bool:
            return self._review.current_state().document_text.selection_state.can_copy

        def copy_selected_document_text(self):
            text = self._review.copy_selected_text()
            if text:
                QApplication.clipboard().setText(text)
            return text

        def can_select_all_document_text(self) -> bool:
            return self._page_index >= 0

        def select_all_document_text(self):
            self.select_all_calls += 1
            transition = self._review.select_all_text(page_index=self._page_index)
            selection = transition.state.document_text.selection_state.selection
            self.selection_highlights = selection.highlight_rects if selection else ()
            if callable(self.status_callback):
                self.status_callback("document_text_selection_changed")
            return transition.state.document_text.selection_state

        def document_review_state(self):
            return self._review.current_state()

        def select_document_review_item(self, signature_id: str):
            return self._review.select_review_item(signature_id).state

        def clear_document_review_highlight(self) -> None:
            return None

        def set_viewer_interaction_mode(self, mode: str) -> str:
            return mode

        def can_place_signature_placement(self) -> bool:
            return False

        def can_adjust_signature_placement(self) -> bool:
            return False

        def can_remove_signature_placement(self) -> bool:
            return False

        def remove_signature_placement(self) -> bool:
            return False

        def can_undo_placement(self) -> bool:
            return False

        def can_redo_placement(self) -> bool:
            return False

        def undo_placement(self):
            return None

        def redo_placement(self):
            return None

        def preview(self):
            return SimpleNamespace(can_submit=False)

        def snapshot(self):
            return SimpleNamespace(last_signing_result=None)

        def submit_sign_request(self):
            return None

        def open_signed_output(self):
            return None

        def go_to_previous_page(self) -> None:
            return None

        def go_to_next_page(self) -> None:
            return None

        def can_go_previous_page(self) -> bool:
            return False

        def can_go_next_page(self) -> bool:
            return False

        def go_back_link(self) -> None:
            return None

        def go_forward_link(self) -> None:
            return None

        def can_go_back_link(self) -> bool:
            return False

        def can_go_forward_link(self) -> bool:
            return False

        def reset_zoom_view(self) -> None:
            return None

        def zoom_in_view(self) -> None:
            return None

        def zoom_out_view(self) -> None:
            return None

        def fit_page_view(self) -> None:
            return None

        def fit_width_view(self) -> None:
            return None

        def focus_document_search(self) -> None:
            return None

        def set_signature_rect(self, **kwargs):
            del kwargs
            return None

        def apply_signature_rect_placement(self, signature_rect) -> None:
            del signature_rect

        def select_signature_field(self, field_name, signature_rect) -> None:
            del field_name, signature_rect

        def focus(self) -> None:
            self.setFocus()

        def close(self) -> bool:
            return super().close()

    class SelectAllFactory:
        def __init__(self) -> None:
            self.shell: SelectAllShell | None = None

        def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
            self.shell = SelectAllShell(bootstrap)
            return SigningWorkspaceBundle(
                maintenance=QtSigningWorkspacePort(self.shell),
                session=QtSigningWorkspaceSessionPort(self.shell),
                testing=object(),
                view=QtWorkspaceView(self.shell),
            )

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal"])
    source = tmp_path / "text.pdf"
    _write_text_pdf(source)
    factory = SelectAllFactory()
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "output"),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        shell_factory=factory,
    )
    frame.window.show()
    app.processEvents()
    assert frame.open_pdf_path(source) is not None
    app.processEvents()
    assert factory.shell is not None
    shell = factory.shell
    select_all_action = frame.command_actions()[AppFrameCommandId.SELECT_ALL]
    copy_action = frame.command_actions()[AppFrameCommandId.COPY]
    assert select_all_action.isEnabled() is True

    select_all_action.trigger()
    assert shell.select_all_calls == 1
    assert shell.selection_highlights
    copy_action.trigger()
    assert QApplication.clipboard().text() == "Alice Example"
    frame.window.activateWindow()
    QTest.keyClick(frame.window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    assert shell.select_all_calls == 2

    frame.window.close()
    app.processEvents()
    if created_app:
        app.quit()
