"""Real offscreen Qt proof for native close draft decisions."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter


class _QuestionBox:
    Discard = 1
    Cancel = 2
    Save = 3
    Yes = Discard
    No = Cancel

    result = Cancel

    @classmethod
    def question(cls, parent, title, text):
        del parent, title, text
        return cls.result


class _Maintenance:
    def __init__(self) -> None:
        self.dirty = True
        self.discard_calls = 0
        self.clear_secret_calls = 0

    def has_unsaved_changes(self) -> bool:
        return self.dirty

    def discard_draft(self) -> None:
        self.discard_calls += 1
        self.dirty = False

    def clear_session_secrets(self) -> None:
        self.clear_secret_calls += 1


class _Session:
    def preview(self):
        raise RuntimeError("not ready in this lifecycle test")


class _Host:
    def __init__(self, maintenance: _Maintenance) -> None:
        self.handle = SimpleNamespace(maintenance=maintenance, session=_Session())
        self.close_calls = 0

    def active(self):
        return self.handle

    def close(self) -> None:
        self.close_calls += 1
        self.handle = None


def test_real_qt_native_close_cancel_then_discard(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    created_app = app is None
    if app is None:
        app = QApplication(["foliaseal-dirty-lifecycle-test"])

    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path / "signed"),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        certificate_catalog_store=CertificateCatalogStore(storage_dir=tmp_path / "certificates"),
        preset_catalog_store=SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
    )
    maintenance = _Maintenance()
    host = _Host(maintenance)
    frame._workspace_host = host  # type: ignore[assignment]
    frame._bindings = frame._bindings.__class__(
        **{
            **frame._bindings.__dict__,
            "q_message_box": _QuestionBox,
        }
    )
    frame.window.show()
    app.processEvents()

    try:
        _QuestionBox.result = _QuestionBox.Cancel
        frame.window.close()
        app.processEvents()
        assert frame.window.isVisible() is True
        assert host.close_calls == 0
        assert maintenance.discard_calls == 0

        _QuestionBox.result = _QuestionBox.Discard
        frame.window.close()
        app.processEvents()
        assert host.close_calls == 1
        assert maintenance.discard_calls == 1
        assert frame.window.isVisible() is False
    finally:
        frame.window.close()
        app.processEvents()
        if created_app:
            app.quit()
