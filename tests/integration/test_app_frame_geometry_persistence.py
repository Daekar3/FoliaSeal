"""Offscreen proof for main-window geometry persistence across frame recreation."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter


def test_main_window_geometry_round_trips_across_frame_recreation(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-frame-geometry-test"])

    store = AppSettingsStore(
        storage_dir=tmp_path / "config",
        default_home_directory=tmp_path / "home",
    )
    adapter = QtAppFrameAdapter()
    first = adapter.create_frame(
        app_settings=store.load_settings(),
        app_settings_store=store,
    )
    first.window.setGeometry(40, 50, 1200, 800)
    first.window.show()
    app.processEvents()

    try:
        first.capture_window_geometry()
        first.persist_captured_window_geometry()
        saved = store.load_settings().ui_settings.main_window_geometry
        assert saved is not None
        assert saved.width == 1200
        assert saved.height == 800
        first.window.showMaximized()
        app.processEvents()
        first.capture_window_geometry()
        first.persist_captured_window_geometry()
        saved = store.load_settings().ui_settings.main_window_geometry
        assert saved is not None
        assert saved.maximized is True
        first.window.close()
        app.processEvents()

        second = adapter.create_frame(
            app_settings=store.load_settings(),
            app_settings_store=store,
        )
        assert second.restore_window_geometry() is True
        restored = second.window.geometry()
        assert restored.width() >= 1100
        assert restored.height() >= 700
        second.window.show()
        second.apply_restored_window_state()
        app.processEvents()
        assert second.window.isMaximized() is True
        second.window.close()
        app.processEvents()
    finally:
        first.window.close()
        app.processEvents()
        if created_app:
            app.quit()
