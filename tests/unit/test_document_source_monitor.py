from pathlib import Path

import pytest

from foliaseal.application.document_safety import (
    SourceChangeAction,
    SourceChangeStatus,
)
from foliaseal.application.document_source_monitor import (
    DocumentSourceMonitor,
    fingerprint_source,
)
from foliaseal.application.signing_draft_contracts import SigningDraftValidationError
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from tests.support.signing_builders import build_signature_appearance, build_signature_rect


def test_monitor_projects_unchanged_and_changed_source(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-1.7\n")
    monitor = DocumentSourceMonitor.for_path(source)

    unchanged = monitor.decision()
    assert unchanged.status is SourceChangeStatus.UNCHANGED
    assert unchanged.action is SourceChangeAction.NONE

    source.write_bytes(b"%PDF-1.7\nchanged\n")
    changed = monitor.decision()
    assert changed.status is SourceChangeStatus.CHANGED
    assert changed.action is SourceChangeAction.RELOAD_OR_IGNORE


def test_monitor_projects_missing_source_and_acknowledges_new_identity(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-1.7\n")
    monitor = DocumentSourceMonitor.for_path(source)
    source.unlink()

    missing = monitor.decision()
    assert missing.status is SourceChangeStatus.MISSING
    assert missing.action is SourceChangeAction.LOCATE_OR_CLOSE

    source.write_bytes(b"%PDF-1.7\nreplacement\n")
    assert monitor.acknowledge_current_source().status is SourceChangeStatus.UNCHANGED


def test_fingerprint_source_returns_none_for_missing_path(tmp_path: Path) -> None:
    assert fingerprint_source(tmp_path / "missing.pdf") is None


def test_changed_source_blocks_direct_workflow_request_construction(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"%PDF-1.7\n")
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(source),
        output_pdf_path=str(tmp_path / "signed.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="",
        timestamp_required=False,
        signature_appearance=build_signature_appearance(),
        signature_rect=build_signature_rect(page_index=0),
        document_source_monitor=DocumentSourceMonitor.for_path(source),
    )
    source.write_bytes(b"%PDF-1.7\nchanged\n")

    assert workflow.can_build_request() is False
    with pytest.raises(SigningDraftValidationError, match="changed on disk"):
        workflow.build_signing_request()
