"""Real offscreen Qt proof for the signing rail layout contract."""

from __future__ import annotations

import os

import pytest


def test_real_qt_signing_rail_keeps_status_read_only_and_primary_action_visible() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QWidget,
    )

    from foliaseal.presentation.qt.signing_action_coordinator import SigningActionState
    from foliaseal.presentation.qt.signing_shell import SigningShellAdapter
    from foliaseal.presentation.qt.signing_workspace_sidebar import SigningWorkspaceSidebar

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-signing-rail-test"])

    find_calls: list[str] = []
    previous_calls: list[str] = []
    sidebar = SigningWorkspaceSidebar(
        bindings=SigningShellAdapter()._load_bindings(),
        properties_widget=QWidget(),
        on_choose_output=lambda: None,
        on_sign=lambda: None,
        on_open_signed_output=lambda: None,
        on_find_text=lambda: find_calls.append("find"),
        on_previous_text_match=lambda: previous_calls.append("previous"),
        on_next_text_match=lambda: None,
        on_copy_text_match=lambda: None,
        on_review_signature_selected=lambda index: None,
        on_text_selection_mode_changed=lambda enabled: None,
        on_copy_selected_text=lambda: None,
        on_clear_selected_text=lambda: None,
    )
    sidebar.render_signing_action_state(
        SigningActionState(
            can_sign=True,
            stage_text="Step 5 of 6 — Confirm and sign",
            detail_text="Review the output and continue.",
            result_text="",
            result_kind="neutral",
            last_signing_result=None,
            last_successful_output_path=None,
            can_open_signed_output=False,
            recommended_action="sign",
        )
    )

    viewer = QWidget()
    central = QWidget()
    row = QHBoxLayout(central)
    row.addWidget(viewer, 1)
    row.addWidget(sidebar.container)
    window = QMainWindow()
    window.setCentralWidget(central)
    window.resize(1100, 700)
    window.show()
    app.processEvents()

    try:
        assert sidebar.container.width() == SigningWorkspaceSidebar.RAIL_WIDTH
        assert sidebar.status_region.minimumHeight() >= (
            SigningWorkspaceSidebar.STATUS_REGION_MINIMUM_HEIGHT
        )
        assert sidebar.signing_action_controls.container.parentWidget() is sidebar.container
        assert sidebar.signing_action_controls.status_container is sidebar.status_region
        assert sidebar.status_region.parentWidget() is sidebar.container
        assert not sidebar.status_region.findChildren(QPushButton)
        assert len(sidebar.status_region.findChildren(QLabel)) == 4
        assert "border: 2px solid #2563eb" in sidebar.sign_button.styleSheet()
        assert sidebar.sign_button.accessibleName() == (
            "Recommended next action: Confirm and sign"
        )
        assert sidebar.sign_button.toolTip() == "Recommended next action"
        sidebar.render_signing_action_state(
            SigningActionState(
                can_sign=False,
                stage_text="Step 6 of 6 — Verify signed PDF",
                detail_text="Open the signed PDF and review its local verification status.",
                result_text="Signing completed successfully.",
                result_kind="success",
                last_signing_result=None,
                last_successful_output_path="/tmp/signed.pdf",
                can_open_signed_output=True,
                recommended_action="open_signed_output",
            )
        )
        assert "border: 2px solid #2563eb" in sidebar.open_signed_output_button.styleSheet()
        assert sidebar.open_signed_output_button.accessibleName() == (
            "Recommended next action: Open signed PDF"
        )
        assert sidebar.open_signed_output_button.toolTip() == "Recommended next action"
        assert viewer.width() > sidebar.container.width()
        query_input = sidebar.document_text_controls.query_input
        query_input.setFocus()
        QTest.keyClick(query_input, Qt.Key_Return)
        QTest.keyClick(query_input, Qt.Key_Return, Qt.KeyboardModifier.ShiftModifier)
        assert find_calls == ["find"]
        assert previous_calls == ["previous"]
    finally:
        window.close()
        app.processEvents()
        if created_app:
            app.quit()
