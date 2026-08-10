"""Offscreen proof for the transactional fixed-page placement editor."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from foliaseal.application.placement_editor import PlacementEditorState
from foliaseal.application.reusable_signing_models import (
    PlacementProfileRect,
    PlacementProfileSourcePage,
)
from foliaseal.presentation.qt.placement_profile_editor_dialog import (
    PlacementProfileEditorDialog,
)


def _bindings() -> SimpleNamespace:
    from PySide6 import QtCore, QtWidgets

    return SimpleNamespace(
        q_widget=QtWidgets.QWidget,
        q_vbox_layout=QtWidgets.QVBoxLayout,
        q_hbox_layout=QtWidgets.QHBoxLayout,
        q_label=QtWidgets.QLabel,
        q_line_edit=QtWidgets.QLineEdit,
        q_check_box=QtWidgets.QCheckBox,
        q_dialog=QtWidgets.QDialog,
        q_double_spin_box=QtWidgets.QDoubleSpinBox,
        q_spin_box=QtWidgets.QSpinBox,
        q_push_button=QtWidgets.QPushButton,
        qt=QtCore.Qt,
    )


def _state() -> PlacementEditorState:
    return PlacementEditorState(
        display_name="Approval",
        page_number=3,
        source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
        rect=PlacementProfileRect(left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0),
    )


def test_editor_save_and_cancel_are_observable_offscreen() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(["foliaseal-placement-editor-test"])
    del app
    bindings = _bindings()
    saved = []
    editor = PlacementProfileEditorDialog(
        bindings=bindings,
        parent=None,
        initial=_state(),
        on_save=saved.append,
    )
    editor.controls.name_input.setText("Board approval")
    editor.controls.page_spin.setValue(4)
    editor.controls.top_spin.setValue(700.0)
    editor.controls.pinned_check.setChecked(True)
    editor.controls.save_button.click()

    assert len(saved) == 1
    assert saved[0].display_name == "Board approval"
    assert saved[0].page_number == 4
    assert saved[0].rect.top_pt == 700.0
    assert saved[0].pinned is True
    assert editor.controls.dialog.result() == bindings.q_dialog.Accepted

    cancelled = []
    second = PlacementProfileEditorDialog(
        bindings=bindings,
        parent=None,
        initial=_state(),
        on_save=cancelled.append,
    )
    second.controls.name_input.setText("Discarded")
    second.controls.cancel_button.click()

    assert cancelled == []
    assert second.controls.dialog.result() == bindings.q_dialog.Rejected
