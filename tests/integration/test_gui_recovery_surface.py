from __future__ import annotations

import os
from pathlib import Path

import pytest


def test_offscreen_frame_can_resolve_verified_startup_candidate(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")

    from PySide6.QtWidgets import QApplication

    from foliaseal.application.signing_transaction_recovery import SigningTransactionRecord
    from foliaseal.infra.config.app_settings_storage import AppSettingsStore
    from foliaseal.infra.config.schemas import AppSettings
    from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal
    from foliaseal.infra.config.signing_transaction_recovery_resolver import (
        FileSigningTransactionRecoveryResolver,
    )
    from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

    class Executor:
        def __init__(self, journal, candidate) -> None:
            self._candidate = candidate
            self._resolver = FileSigningTransactionRecoveryResolver(journal)

        def verified_recovery_candidates(self):
            return (self._candidate,)

        def resolve_recovery_candidate(self, candidate, action, **kwargs):
            return self._resolver.resolve(candidate, action, **kwargs)

    app = QApplication.instance() or QApplication(["foliaseal"])
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    record = SigningTransactionRecord.new(
        transaction_id="transaction-1",
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "signed.pdf"),
    )
    artifact = tmp_path / ".signed.pdf.transaction.tmp"
    artifact.write_bytes(b"signed bytes")
    journal.begin(record)
    journal.mark_staged(record.transaction_id, str(artifact))
    candidate = journal.verified_candidates(lambda _: True)[0]
    frame = QtAppFrameAdapter().create_frame(
        app_settings=AppSettings(
            schema_version=1,
            default_output_directory=str(tmp_path),
            default_open_directory=str(tmp_path),
            linux_packaging_channel="primary",
            ui={},
        ),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        sign_executor=Executor(journal, candidate),
    )
    frame._ask_startup_recovery_action = lambda _candidate: "discard"  # noqa: SLF001

    frame.offer_startup_recovery()
    app.processEvents()

    assert frame.startup_recovery_candidate is None
    assert not artifact.exists()
    assert not candidate.journal_path.exists()
    frame.window.close()
