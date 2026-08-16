from pathlib import Path

import pytest

from foliaseal.application.sign_pdf_use_case import SignPdfUseCase
from foliaseal.application.signing_transaction_recovery import (
    SigningTransactionJournalError,
    SigningTransactionRecord,
    is_owned_staged_artifact,
)
from foliaseal.domain.models import SigningOutput, VerificationSummary
from tests.support.signing_builders import build_signing_request


class _Inspector:
    def get_pdf_version(self, _path: str) -> str:
        return "1.7"


class _Loader:
    def validate(self, _path: str, _passphrase: str) -> None:
        return None


class _Signer:
    def sign(self, _request) -> SigningOutput:
        return SigningOutput(b"signed", "1.7", "adbe.pkcs7.detached", True)


class _Verifier:
    def __init__(self, summary: VerificationSummary) -> None:
        self.summary = summary

    def verify(self, _path: str, *, trust_policy=None) -> VerificationSummary:
        del trust_policy
        return self.summary


class _RaisingVerifier:
    def verify(self, _path: str, *, trust_policy=None) -> VerificationSummary:
        del trust_policy
        raise ValueError("verification failed")


class _FailingJournal:
    def __init__(self, operation: str) -> None:
        self.operation = operation

    def _maybe_fail(self, operation: str) -> None:
        if self.operation == operation:
            raise OSError(f"journal {operation} failed")

    def begin(self, _record) -> None:
        self._maybe_fail("begin")

    def mark_staged(self, _transaction_id: str, _path: str) -> None:
        self._maybe_fail("mark_staged")

    def mark_preserved(self, _transaction_id: str) -> None:
        self._maybe_fail("mark_preserved")

    def mark_committing(self, _transaction_id: str) -> None:
        self._maybe_fail("mark_committing")

    def complete(self, _transaction_id: str) -> None:
        self._maybe_fail("complete")

    def discard(self, _transaction_id: str) -> None:
        return None

    def verified_candidates(self, _verifier):
        return ()

    def discard_candidate(self, _candidate) -> None:
        return None


def _record(tmp_path: Path) -> SigningTransactionRecord:
    output = tmp_path / "signed.pdf"
    return SigningTransactionRecord.new(
        transaction_id="transaction-1",
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(output),
    ).with_stage(str(tmp_path / ".signed.pdf.abc.tmp"))


def test_record_round_trips_only_secret_free_fields(tmp_path: Path) -> None:
    record = _record(tmp_path)

    assert SigningTransactionRecord.from_dict(record.to_dict()) == record
    assert "passphrase" not in record.to_dict()
    assert "certificate" not in record.to_dict()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update(password="secret"),
        lambda payload: payload.update(staged_pdf_path="relative.tmp"),
        lambda payload: payload.update(state="complete"),
        lambda payload: payload.pop("created_at"),
    ],
)
def test_record_decoder_rejects_unsafe_or_malformed_payloads(
    tmp_path: Path,
    mutator,
) -> None:
    payload = _record(tmp_path).to_dict()
    mutator(payload)

    with pytest.raises(SigningTransactionJournalError):
        SigningTransactionRecord.from_dict(payload)


def test_owned_artifact_requires_exact_staged_sibling_shape(tmp_path: Path) -> None:
    record = _record(tmp_path)
    owned = Path(record.staged_pdf_path)

    assert is_owned_staged_artifact(record, owned)
    assert not is_owned_staged_artifact(record, tmp_path / "unrelated.tmp")
    assert not is_owned_staged_artifact(
        record,
        tmp_path / "nested" / owned.name,
    )


def test_preserved_requires_a_staged_artifact(tmp_path: Path) -> None:
    record = SigningTransactionRecord.new(
        transaction_id="transaction-1",
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "signed.pdf"),
    )

    with pytest.raises(SigningTransactionJournalError):
        record.preserved()


def test_use_case_clears_journal_after_successful_replacement(tmp_path: Path) -> None:
    from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal

    request = build_signing_request(tmp_path)
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    use_case = SignPdfUseCase(
        inspector=_Inspector(),
        certificate_loader=_Loader(),
        signer=_Signer(),
        verifier=_Verifier(VerificationSummary(signature_count=1, timestamp_present=True)),
        transaction_journal=journal,
    )

    result = use_case.execute(request)

    assert result.success
    assert tuple((tmp_path / "journal").glob("*.json")) == ()


def test_use_case_leaves_preserved_artifact_journal_for_restart_recovery(tmp_path: Path) -> None:
    from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal

    request = build_signing_request(tmp_path)
    journal = FileSigningTransactionJournal(tmp_path / "journal")
    use_case = SignPdfUseCase(
        inspector=_Inspector(),
        certificate_loader=_Loader(),
        signer=_Signer(),
        verifier=_RaisingVerifier(),
        transaction_journal=journal,
    )

    result = use_case.execute(request)

    assert not result.success
    assert result.preserved_artifact_path is not None
    assert tuple((tmp_path / "journal").glob("*.json"))


@pytest.mark.parametrize("operation", ["begin", "mark_staged", "mark_committing", "complete"])
def test_journal_write_failures_fail_closed(tmp_path: Path, operation: str) -> None:
    request = build_signing_request(tmp_path)
    use_case = SignPdfUseCase(
        inspector=_Inspector(),
        certificate_loader=_Loader(),
        signer=_Signer(),
        verifier=_Verifier(VerificationSummary(signature_count=1, timestamp_present=True)),
        transaction_journal=_FailingJournal(operation),
    )

    result = use_case.execute(request)

    assert not result.success
    assert result.failure_code.value == "atomic_write_failed"
