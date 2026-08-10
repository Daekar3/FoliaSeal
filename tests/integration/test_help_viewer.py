"""Offscreen Qt acceptance for the modeless offline Help surface."""

from __future__ import annotations

import os

import pytest


def test_help_viewer_search_history_and_f1_work_without_a_document() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QLineEdit

    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
    from foliaseal.presentation.qt.app_frame_command_model import AppFrameCommandId

    app = QApplication.instance() or QApplication(["foliaseal"])
    frame = QtAppFrameAdapter().create_frame()
    frame.window.show()
    app.processEvents()

    frame.window.activateWindow()
    frame.window.setFocus()
    QTest.keyClick(frame.window, Qt.Key_F1)
    app.processEvents()
    viewer = frame.help_viewer
    assert viewer is not None
    assert viewer.current_topic_id == "getting-started"
    assert viewer.dialog.isModal() is False
    assert viewer.search_input.hasFocus()

    viewer.search_input.setText("certificate")
    app.processEvents()
    assert viewer.topic_list.count() == 1
    viewer.topic_list.setCurrentRow(0)
    app.processEvents()
    assert viewer.current_topic_id == "certificates"
    assert "certificate" in viewer.content_browser.toPlainText().lower()

    viewer.content_browser.anchorClicked.emit(QUrl("help:privacy"))
    assert viewer.current_topic_id == "privacy"
    viewer.content_browser.anchorClicked.emit(QUrl("https://example.invalid/remote"))
    assert viewer.current_topic_id == "privacy"

    viewer.go_back()
    assert viewer.current_topic_id == "certificates"
    viewer.go_forward()
    assert viewer.current_topic_id == "privacy"

    frame._command_actions[AppFrameCommandId.HELP].trigger()  # noqa: SLF001
    app.processEvents()
    assert frame.help_viewer is viewer

    editor = QLineEdit(frame.window)
    editor.show()
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key_F1)
    app.processEvents()
    assert frame.help_viewer is viewer

    viewer.close()
    app.processEvents()
    assert frame.help_viewer is None
    frame.window.close()
