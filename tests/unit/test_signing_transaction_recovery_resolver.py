from pathlib import Path

from foliaseal.application.signing_transaction_recovery import (
    SigningTransactionRecord,
)
from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal
from foliaseal.infra.config.signing_transaction_recovery_resolver import (
    FileSigningTransactionRecoveryResolver,
)


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


def test_open_resolution_is_non_destructive(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    result = FileSigningTransactionRecoveryResolver(journal).resolve(candidate, "open")

    assert result.success
    assert result.artifact_path == str(candidate.artifact_path)
    assert candidate.artifact_path.exists()
    assert candidate.journal_path.exists()


def test_copy_resolution_preserves_candidate_and_unrelated_file(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    unrelated = tmp_path / "unrelated.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    destination = tmp_path / "copies" / "signed-copy.pdf"

    result = FileSigningTransactionRecoveryResolver(journal).resolve(
        candidate,
        "copy",
        destination_path=str(destination),
    )

    assert result.success
    assert destination.read_bytes() == b"signed bytes"
    assert candidate.artifact_path.exists()
    assert candidate.journal_path.exists()
    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_copy_resolution_requires_overwrite_authorization(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    destination = tmp_path / "existing.pdf"
    destination.write_bytes(b"keep")
    resolver = FileSigningTransactionRecoveryResolver(journal)

    denied = resolver.resolve(candidate, "copy", destination_path=str(destination))

    assert not denied.success
    assert destination.read_bytes() == b"keep"
    accepted = resolver.resolve(
        candidate,
        "copy",
        destination_path=str(destination),
        overwrite_authorized=True,
    )
    assert accepted.success
    assert destination.read_bytes() == b"signed bytes"


def test_resolution_rejects_artifact_changed_after_discovery(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    candidate.artifact_path.write_bytes(b"tampered")

    result = FileSigningTransactionRecoveryResolver(journal).resolve(candidate, "open")

    assert not result.success
    assert "no longer owned" in (result.error or "")
    assert candidate.journal_path.exists()


def test_replace_requires_authorization_and_consumes_owned_candidate(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    resolver = FileSigningTransactionRecoveryResolver(journal)

    denied = resolver.resolve(candidate, "replace")
    assert not denied.success
    assert candidate.artifact_path.exists()

    accepted = resolver.resolve(candidate, "replace", replace_authorized=True)
    assert accepted.success
    assert (tmp_path / "signed.pdf").read_bytes() == b"signed bytes"
    assert not candidate.artifact_path.exists()
    assert not candidate.journal_path.exists()


def test_discard_removes_only_owned_candidate(tmp_path: Path) -> None:
    journal, candidate = _candidate(tmp_path)
    unrelated = tmp_path / "unrelated.tmp"
    unrelated.write_text("keep", encoding="utf-8")

    result = FileSigningTransactionRecoveryResolver(journal).resolve(candidate, "discard")

    assert result.success
    assert not candidate.artifact_path.exists()
    assert not candidate.journal_path.exists()
    assert unrelated.exists()
