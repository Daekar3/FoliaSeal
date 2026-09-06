"""Real Qt coverage for the final signing confirmation result."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from foliaseal.presentation.qt.signing_action_coordinator import SigningActionState
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)


def test_native_sign_and_save_button_is_semantically_accepted() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication(["foliaseal-native-confirmation-test"])
    bridge = object.__new__(SigningWorkspaceActionBridge)
    bridge._widget = None
    bridge._bindings = SimpleNamespace(q_message_box=QMessageBox)

    def click_affirmative_button() -> None:
        for widget in app.topLevelWidgets():
            if not isinstance(widget, QMessageBox):
                continue
            for button in widget.buttons():
                if button.text() == "Sign and save":
                    button.click()
                    return

    QTimer.singleShot(0, click_affirmative_button)
    try:
        assert bridge._ask_consequence_confirmation(
            title="Confirm signing",
            text="Ready to sign.",
            affirmative_label="Sign and save",
        ) is True
    finally:
        for widget in app.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.close()
        app.processEvents()
        if QApplication.instance() is app:
            app.quit()


def test_native_confirmation_submits_through_public_bridge() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication.instance() or QApplication(["foliaseal-native-submit-test"])
    state = SigningActionState(
        can_sign=True,
        stage_text="Step 5 of 6 — Confirm and sign",
        detail_text="Ready to sign.",
        result_text="",
        result_kind="neutral",
        last_signing_result=None,
        last_successful_output_path=None,
        can_open_signed_output=False,
        recommended_action="sign",
    )

    class Boundary:
        supports_async_transaction = True

        def __init__(self) -> None:
            self.started = False

        def load(self):
            return state

        def begin_transaction(self):
            self.started = True
            return SimpleNamespace(state=state, request=object())

    boundary = Boundary()
    bridge = SigningWorkspaceActionBridge(
        widget=None,
        bindings=SimpleNamespace(q_message_box=QMessageBox),
        sidebar=SimpleNamespace(render_signing_action_state=lambda _state: None),
        setup_port=SimpleNamespace(
            apply_changes=lambda: None,
            load_setup_state=lambda: SimpleNamespace(
                selected_certificate_configuration_name="Test certificate",
                selected_signature_preset_name="Test preset",
            ),
        ),
        signing_action_boundary=boundary,
        draft_workflow=SimpleNamespace(
            input_pdf_path="/tmp/input.pdf",
            output_pdf_path="/tmp/output.pdf",
            preview_signing_time=datetime(2026, 9, 6, 14, 0, tzinfo=UTC),
            preview=lambda: SimpleNamespace(
                title="Approval",
                page_index=0,
                signature_rect=None,
                signer_label_prefix="Signed by",
                layout_template=None,
                stamp_position=None,
                timezone_display_mode=None,
                show_field_names=True,
                datetime_format=None,
                text_style=None,
                box_style=None,
                image_stamp_path=None,
                fields=(),
                detail_text="Ready to sign.",
                issues=(),
                can_submit=True,
            ),
        ),
        app_settings_getter=lambda: SimpleNamespace(default_output_directory="/tmp"),
    )
    bridge._has_explicit_output_pdf_path = True

    def click_affirmative_button() -> None:
        for widget in app.topLevelWidgets():
            if not isinstance(widget, QMessageBox):
                continue
            for button in widget.buttons():
                if button.text() == "Sign and save":
                    button.click()
                    return

    QTimer.singleShot(0, click_affirmative_button)
    try:
        assert bridge.submit_sign_request() is not None
        assert boundary.started is True
    finally:
        for widget in app.topLevelWidgets():
            if isinstance(widget, QMessageBox):
                widget.close()
        app.processEvents()
        if QApplication.instance() is app:
            app.quit()
