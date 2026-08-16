from pathlib import Path

from foliaseal.application.signing_transaction_recovery import (
    SigningTransactionRecord,
)
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal
from foliaseal.infra.config.signing_transaction_recovery_resolver import (
    FileSigningTransactionRecoveryResolver,
)
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame
from tests.unit.test_qt_app_frame import (
    _fake_bindings,
    _FakeMessageBox,
    _FakeShell,
    _FakeShellFactory,
    _settings,
)


class _RecoveryExecutor:
    def __init__(self, journal: FileSigningTransactionJournal, candidate) -> None:
        self.candidate = candidate
        self.resolver = FileSigningTransactionRecoveryResolver(journal)

    def verified_recovery_candidates(self):
        return (self.candidate,)

    def resolve_recovery_candidate(self, candidate, action, **kwargs):
        return self.resolver.resolve(candidate, action, **kwargs)


def _candidate(tmp_path: Path):
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
    return journal, journal.verified_candidates(lambda _: True)[0]


def _frame(tmp_path: Path, executor: _RecoveryExecutor) -> FoliaSealAppFrame:
    return FoliaSealAppFrame(
        bindings=_fake_bindings(),
        app_settings=_settings(tmp_path),
        app_settings_store=AppSettingsStore(storage_dir=tmp_path / "config"),
        shell_factory=_FakeShellFactory(_FakeShell()),
        render_backend_factory=lambda: object(),
        sign_executor=executor,
    )


def test_startup_recovery_dismissal_preserves_candidate(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    executor = _RecoveryExecutor(journal, candidate)
    frame = _frame(tmp_path, executor)
    frame._bindings.q_message_box.next_question_result = _FakeMessageBox.No  # noqa: SLF001

    offered = frame.offer_startup_recovery()

    assert offered == candidate
    assert frame.startup_recovery_candidate == candidate
    assert candidate.artifact_path.exists()
    assert candidate.journal_path.exists()


def test_startup_recovery_discard_uses_explicit_safe_resolution(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    executor = _RecoveryExecutor(journal, candidate)
    frame = _frame(tmp_path, executor)
    frame._startup_recovery_candidate = candidate  # noqa: SLF001
    frame._resolve_startup_recovery(candidate, "discard")  # noqa: SLF001

    assert frame.startup_recovery_candidate is None
    assert not candidate.artifact_path.exists()
    assert not candidate.journal_path.exists()


def test_replace_requires_consequence_confirmation(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    frame = _frame(tmp_path, _RecoveryExecutor(journal, candidate))
    frame._bindings.q_message_box.next_question_result = _FakeMessageBox.No  # noqa: SLF001

    assert not frame._confirm_startup_recovery_replace(candidate)  # noqa: SLF001


def test_copy_overwrite_requires_consequence_confirmation(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    frame = _frame(tmp_path, _RecoveryExecutor(journal, candidate))
    destination = tmp_path / "existing.pdf"
    destination.write_text("keep", encoding="utf-8")
    frame._bindings.q_message_box.next_question_result = _FakeMessageBox.No  # noqa: SLF001

    assert not frame._confirm_startup_recovery_copy_overwrite(destination)  # noqa: SLF001
    assert destination.read_text(encoding="utf-8") == "keep"
