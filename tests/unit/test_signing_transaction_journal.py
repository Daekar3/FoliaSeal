import json
from pathlib import Path

from foliaseal.application.signing_transaction_recovery import SigningTransactionRecord
from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal


def _record(tmp_path: Path) -> SigningTransactionRecord:
    return SigningTransactionRecord.new(
        transaction_id="transaction-1",
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "signed.pdf"),
    )


def test_journal_survives_restart_and_verifies_only_owned_artifact(tmp_path: Path) -> None:
    journal_root = tmp_path / "config" / "signing-transactions"
    journal = FileSigningTransactionJournal(journal_root)
    record = _record(tmp_path)
    artifact = tmp_path / ".signed.pdf.transaction.tmp"
    artifact.write_bytes(b"signed")
    journal.begin(record)
    journal.mark_staged(record.transaction_id, str(artifact))

    restarted = FileSigningTransactionJournal(journal_root)
    assert restarted.verified_candidates(lambda _path: False) == ()
    candidates = restarted.verified_candidates(
        lambda path: path == str(artifact) and Path(path).read_bytes() == b"signed"
    )
    assert len(candidates) == 1
    assert candidates[0].artifact_path == artifact


def test_malformed_or_secret_bearing_records_are_ignored_without_neighbor_cleanup(
    tmp_path: Path,
) -> None:
    journal_root = tmp_path / "journal"
    journal_root.mkdir(parents=True)
    unrelated = tmp_path / "unrelated.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    (journal_root / "malformed.json").write_text("{not-json", encoding="utf-8")
    (journal_root / "secret.json").write_text(
        json.dumps({"password": "do-not-store"}),
        encoding="utf-8",
    )

    assert FileSigningTransactionJournal(journal_root).verified_candidates(lambda _: True) == ()
    assert unrelated.read_text(encoding="utf-8") == "keep"


def test_candidate_discard_removes_only_proven_owned_artifact(tmp_path: Path) -> None:
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    record = _record(tmp_path)
    artifact = tmp_path / ".signed.pdf.transaction.tmp"
    artifact.write_bytes(b"signed")
    journal.begin(record)
    journal.mark_staged(record.transaction_id, str(artifact))
    candidate = journal.verified_candidates(lambda _: True)[0]
    unrelated = tmp_path / "unrelated.tmp"
    unrelated.write_text("keep", encoding="utf-8")

    journal.discard_candidate(candidate)

    assert not artifact.exists()
    assert unrelated.exists()
    assert not candidate.journal_path.exists()


def test_post_replace_crash_recovers_final_output_by_digest(tmp_path: Path) -> None:
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    record = _record(tmp_path)
    artifact = tmp_path / ".signed.pdf.transaction.tmp"
    artifact.write_bytes(b"signed")
    journal.begin(record)
    journal.mark_staged(record.transaction_id, str(artifact))
    output = tmp_path / "signed.pdf"
    artifact.replace(output)
    journal.mark_committing(record.transaction_id)

    candidates = journal.verified_candidates(lambda path: Path(path).read_bytes() == b"signed")

    assert len(candidates) == 1
    assert candidates[0].artifact_path == output


def test_verifier_exception_rejects_only_that_candidate(tmp_path: Path) -> None:
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    record = _record(tmp_path)
    artifact = tmp_path / ".signed.pdf.transaction.tmp"
    artifact.write_bytes(b"signed")
    journal.begin(record)
    journal.mark_staged(record.transaction_id, str(artifact))

    def verifier(_path: str) -> bool:
        raise RuntimeError("backend unavailable")

    assert journal.verified_candidates(verifier) == ()


def test_complete_and_discard_are_idempotent(tmp_path: Path) -> None:
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    record = _record(tmp_path)
    journal.begin(record)

    journal.complete(record.transaction_id)
    journal.complete(record.transaction_id)
    journal.begin(record)
    journal.discard(record.transaction_id)
    journal.discard(record.transaction_id)

    assert not (tmp_path / "journal" / "transaction-1.json").exists()
