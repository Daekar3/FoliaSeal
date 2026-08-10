"""Real offscreen Qt proof for safe external-link confirmation."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from foliaseal.application.document_safety import LinkDecision, LinkDecisionKind
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame
from foliaseal.presentation.qt.external_link_confirmation import ExternalLinkOutcome


def _decision(destination: str) -> LinkDecision:
    return LinkDecision(
        kind=LinkDecisionKind.CONFIRM_EXTERNAL,
        destination=destination,
        reason="External destinations require confirmation before opening.",
    )


def _frame(window, launcher):
    frame = object.__new__(FoliaSealAppFrame)
    frame.window = window
    frame._bindings = SimpleNamespace(q_message_box=None)  # noqa: SLF001
    frame._external_link_launcher = launcher  # noqa: SLF001
    frame._on_error = lambda _message: None  # noqa: SLF001
    frame._pending_external_link = None  # noqa: SLF001
    frame._signing_transaction_active = False  # noqa: SLF001
    return frame


def test_real_offscreen_external_link_dialog_requires_explicit_open(monkeypatch) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

    app = QApplication.instance() or QApplication(["foliaseal-safe-links-external-test"])
    window = QWidget()
    opened: list[str] = []
    frame = _frame(window, lambda destination: opened.append(destination) or True)
    frame._bindings.q_message_box = QMessageBox  # noqa: SLF001

    def click_open() -> None:
        for widget in app.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                button = next(
                    button for button in widget.buttons() if button.text() == "Open link"
                )
                button.click()
                return
        QTimer.singleShot(1, click_open)

    QTimer.singleShot(0, click_open)
    result = frame._handle_external_link_confirmation(_decision("https://example.test/review"))  # noqa: SLF001

    assert result.outcome is ExternalLinkOutcome.OPENED
    assert opened == ["https://example.test/review"]
    window.close()
    app.processEvents()
