"""Real Qt checks for the Appearance editor's live preview and sticky layout."""

from __future__ import annotations

import os
from hashlib import sha256
from types import SimpleNamespace

import pytest

from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
    SaveAppearance,
)
from foliaseal.application.signature_image_import import ManagedSignatureImageStore
from foliaseal.presentation.qt.appearance_profile_editor_widget import (
    AppearanceProfileEditorWidget,
)
from tests.support.signing_builders import build_signature_appearance


def _bindings() -> SimpleNamespace:
    from PySide6 import QtCore, QtGui, QtWidgets

    return SimpleNamespace(
        q_widget=QtWidgets.QWidget,
        q_vbox_layout=QtWidgets.QVBoxLayout,
        q_hbox_layout=QtWidgets.QHBoxLayout,
        q_form_layout=QtWidgets.QFormLayout,
        q_scroll_area=QtWidgets.QScrollArea,
        q_group_box=QtWidgets.QGroupBox,
        q_label=QtWidgets.QLabel,
        q_line_edit=QtWidgets.QLineEdit,
        q_check_box=QtWidgets.QCheckBox,
        q_combo_box=QtWidgets.QComboBox,
        q_file_dialog=QtWidgets.QFileDialog,
        q_input_dialog=QtWidgets.QInputDialog,
        q_message_box=QtWidgets.QMessageBox,
        q_dialog=QtWidgets.QDialog,
        q_icon=QtGui.QIcon,
        q_pixmap=QtGui.QPixmap,
        q_double_spin_box=QtWidgets.QDoubleSpinBox,
        q_spin_box=QtWidgets.QSpinBox,
        q_push_button=QtWidgets.QPushButton,
        q_object=QtCore.QObject,
        q_event=QtCore.QEvent,
        q_timer=QtCore.QTimer,
        qt=QtCore.Qt,
    )


def test_live_preview_is_composed_and_stays_visible_when_form_scrolls(tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication, QCheckBox

    app = QApplication.instance() or QApplication(["foliaseal-appearance-preview-test"])
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Preview", build_signature_appearance()))
    image_store = ManagedSignatureImageStore(tmp_path / "managed-images")
    editor = AppearanceProfileEditorWidget(
        bindings=_bindings(),
        parent=None,
        library=service,
        initial_ref=service.view().appearances[0].ref,
        image_store=image_store,
    )
    editor.controls.container.resize(1000, 650)
    editor.controls.container.show()
    app.processEvents()

    preview = editor.controls.sample_preview_label
    assert preview.isVisible()
    assert preview.text()
    # These fixture values are rendered by the composed preview, rather than only as settings
    # summaries.  The assertions intentionally avoid exact pixels.
    assert "ada@example.test" in preview.text()
    assert "Approval" in preview.text()
    assert preview.width() > 160
    assert preview.height() > 40

    rendered_preview = editor.controls.sample_preview_image.pixmap()
    assert rendered_preview is not None
    preview_scroll = editor.controls.sample_preview_scroll_area
    assert preview_scroll is not None
    assert rendered_preview.width() >= 900
    assert preview_scroll.horizontalScrollBar().maximum() > 0
    preview_scroll.setFocus()
    QTest.keyClick(preview_scroll, Qt.Key.Key_Right)
    app.processEvents()
    assert preview_scroll.horizontalScrollBar().value() > 0

    rendered_image = rendered_preview.toImage()
    before_pixels = sha256(rendered_image.constBits().tobytes()).digest()
    for x, y in (
        (0, 0),
        (rendered_image.width() - 1, 0),
        (0, rendered_image.height() - 1),
        (rendered_image.width() - 1, rendered_image.height() - 1),
    ):
        assert rendered_image.pixelColor(x, y).alpha() == 255
    editor.controls.setup_form.appearance_controls.move_field_down.click()
    app.processEvents()
    reordered_preview = editor.controls.sample_preview_image.pixmap()
    assert reordered_preview is not None
    after_pixels = sha256(reordered_preview.toImage().constBits().tobytes()).digest()
    assert after_pixels != before_pixels
    assert "1. Common name" in preview.text()
    assert "2. Distinguished name" in preview.text()
    preview_scroll.horizontalScrollBar().setValue(
        preview_scroll.horizontalScrollBar().maximum()
    )
    app.processEvents()
    assert preview_scroll.horizontalScrollBar().value() > 0

    # The managed image path uses a long digest/UUID basename. It must wrap in
    # the form without forcing a horizontal scrollbar or clipping image actions.
    from PySide6.QtGui import QImage

    source = tmp_path / "synthetic-source.png"
    image = QImage(360, 72, QImage.Format.Format_ARGB32)
    image.fill(0xFF202020)
    assert image.save(str(source), "PNG")
    managed = image_store.import_asset(source)
    assert len(managed.path.name) >= 40
    editor.controls.setup_form.set_image_asset(str(managed.path), managed.asset)
    controls = editor.controls.setup_form.appearance_controls
    controls.stamp_position.setCurrentText("Left")
    checks = editor.controls.setup_form.visible_text_controls.field_checks_container.findChildren(
        QCheckBox
    )
    for check in checks:
        check.setChecked(check.text() in {"Common name", "Signing time"})
    app.processEvents()
    form_scroll = editor.controls.form_scroll_area
    assert form_scroll.horizontalScrollBar().maximum() == 0
    assert controls.browse_image_button.isVisible()
    assert controls.remove_image_button.isVisible()
    browse_right = controls.browse_image_button.mapTo(
        form_scroll.viewport(), controls.browse_image_button.rect().bottomRight()
    ).x()
    remove_right = controls.remove_image_button.mapTo(
        form_scroll.viewport(), controls.remove_image_button.rect().bottomRight()
    ).x()
    assert browse_right < form_scroll.viewport().width()
    assert remove_right < form_scroll.viewport().width()
    assert "Common name" in preview.text()
    assert "Signing time" in preview.text()
    assert "Email" not in preview.text()

    app.processEvents()
    image_pixmap = editor.controls.sample_preview_image.pixmap()
    assert image_pixmap is not None
    assert editor.controls.sample_preview_hint.text().startswith("Complete image preview")
    assert image_pixmap.width() <= preview_scroll.viewport().width()
    assert image_pixmap.height() <= 132
    assert preview_scroll.horizontalScrollBar().maximum() == 0
    previous_width = image_pixmap.width()
    editor.controls.container.resize(760, 650)
    QTest.qWait(120)
    resized_pixmap = editor.controls.sample_preview_image.pixmap()
    assert resized_pixmap is not None
    assert resized_pixmap.width() <= preview_scroll.viewport().width()
    assert resized_pixmap.width() < previous_width
    editor.controls.container.resize(1000, 650)
    QTest.qWait(120)

    footer_geometry = editor.controls.action_row.geometry()
    preview_geometry = preview.geometry()
    scroll_area = editor.controls.form_scroll_area
    assert scroll_area is not None
    assert not scroll_area.horizontalScrollBar().isVisible()
    assert scroll_area.verticalScrollBar().isVisible()

    scroll_area.verticalScrollBar().setValue(scroll_area.verticalScrollBar().maximum())
    app.processEvents()
    assert preview.geometry() == preview_geometry
    assert editor.controls.action_row.geometry() == footer_geometry
    assert preview.isVisible()
    editor.controls.container.close()
