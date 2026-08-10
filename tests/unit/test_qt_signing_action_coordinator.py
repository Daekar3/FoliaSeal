from pathlib import Path

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.signing_readiness import (
    SigningReadinessInputs,
    project_signing_readiness,
)
from foliaseal.domain.errors import FailureCode
from foliaseal.domain.models import SigningResult, VerificationSummary
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionCoordinator,
)
from tests.support.signing_builders import build_signature_appearance, build_signature_rect


class _FakeSigningExecutor:
    def __init__(self, result=None, *, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls = []

    def execute(self, request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.result


class _FakeRecoveryExecutor(_FakeSigningExecutor):
    def __init__(self, result=None, *, verify_error: Exception | None = None) -> None:
        super().__init__(result)
        self.verify_error = verify_error
        self.verify_calls: list[str] = []

    def verify_preserved_artifact(self, artifact_path: str):
        self.verify_calls.append(artifact_path)
        if self.verify_error is not None:
            raise self.verify_error
        return VerificationSummary(
            signature_count=1,
            timestamp_present=True,
            signatures_cryptographically_valid=True,
        )


class _InvalidVerificationSummary:
    signatures_cryptographically_valid = False


class _MissingTimestampVerificationSummary:
    signatures_cryptographically_valid = True
    timestamp_present = False


class _RestrictedVerificationSummary:
    signatures_cryptographically_valid = True
    timestamp_present = True
    certification_restricted = True
    restriction_reason = "Certification forbids changes."
    docmdp_permission = "no_changes"


def _workflow(tmp_path: Path) -> SigningDraftWorkflow:
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )
    workflow.signature_rect = build_signature_rect(page_index=0, width_pt=120.0, height_pt=40.0)
    workflow.signature_appearance = build_signature_appearance()
    return workflow


def _readiness(workflow: SigningDraftWorkflow, *, ready: bool, text: str):
    return lambda: project_signing_readiness(
        SigningReadinessInputs(
            selected_preset_name="Approval",
            has_saved_presets=True,
            certificate_selected=bool(workflow.certificate_path),
            certificate_blocking=False,
            certificate_detail="",
            certificate_warning=False,
            placement_present=workflow.signature_rect is not None,
            validation_text=text,
            ready_to_sign=ready,
        )
    )


def test_signing_action_coordinator_load_reports_place_signature_when_draft_is_empty(
    tmp_path: Path,
) -> None:
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=False, text=""),
    )

    state = coordinator.load()

    assert state.can_sign is False
    assert state.stage_text == "Step 3 of 6 — Place visible signature"
    assert "Place the visible signature on the page" in state.detail_text
    assert state.last_signing_result is None
    assert state.can_open_signed_output is False
    assert state.recommended_action == "place_signature"


def test_signing_action_coordinator_prioritizes_missing_signing_setup(
    tmp_path: Path,
) -> None:
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path="",
        passphrase="",
        tsa_url="",
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(
            workflow, ready=False, text="Choose a certificate before signing."
        ),
    )

    state = coordinator.load()

    assert state.stage_text == "Step 2 of 6 — Setup required"
    assert "choose a certificate" in state.detail_text.lower()
    assert state.recommended_action == "complete_setup"


def test_signing_action_coordinator_accept_output_path_clears_previous_success(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
        can_open_signed_output=True,
    )

    transition = coordinator.submit()
    request = transition.request
    assert request is not None

    updated = coordinator.accept_output_path(str(tmp_path / "other.pdf"))

    assert workflow.output_pdf_path == str(tmp_path / "other.pdf")
    assert workflow.output_path_confirmed is True
    assert updated.last_signing_result is None
    assert updated.result_text == f"Output will be saved to: {tmp_path / 'other.pdf'}"
    assert updated.can_open_signed_output is False
    assert updated.stage_text == "Step 5 of 6 — Confirm and sign"
    assert updated.recommended_action == "sign"


def test_signing_action_coordinator_invalidate_clears_signed_state(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            timestamp_present=False,
        )
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
        can_open_signed_output=True,
    )
    transition = coordinator.submit()
    assert transition.request is not None

    state = coordinator.invalidate("placement")

    assert state.last_signing_result is None
    assert state.last_successful_output_path is None
    assert state.result_text == ""
    assert state.can_open_signed_output is False
    assert state.stage_text == "Step 5 of 6 — Confirm and sign"
    assert state.recommended_action == "sign"


def test_signing_action_coordinator_returns_validation_failure_without_request(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    applied = []
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: applied.append(True),
        readiness=_readiness(workflow, ready=False, text="Selection is incomplete."),
    )

    transition = coordinator.submit()

    assert applied == [True]
    assert transition.request is None
    assert transition.error_message == "Selection is incomplete."
    assert transition.error_via_emit is True
    assert transition.state.last_signing_result is None
    assert transition.state.stage_text == "Step 4 of 6 — Review readiness"
    assert transition.state.recommended_action == "review_readiness"


def test_signing_action_coordinator_success_tracks_signed_state(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    requested = []
    executor = _FakeSigningExecutor(
        SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
            standards_summary="PDF 1.7, detached signature, no timestamp.",
            timestamp_present=False,
        )
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
        on_sign_request=requested.append,
        can_open_signed_output=True,
    )

    transition = coordinator.submit()

    assert transition.request is not None
    assert executor.calls == [transition.request]
    assert requested == [transition.request]
    assert transition.status_event == "sign_success"
    assert transition.error_message is None
    assert transition.state.last_signing_result is not None
    assert transition.state.last_signing_result.success is True
    assert transition.state.stage_text == "Step 6 of 6 — Verify signed PDF"
    assert transition.state.can_open_signed_output is True
    assert transition.state.recommended_action == "open_signed_output"
    assert workflow.has_unsaved_changes is False
    assert workflow.passphrase == ""
    assert coordinator.open_signed_output() == workflow.output_pdf_path


def test_signing_action_coordinator_begin_and_complete_preserve_non_cancellable_state(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    executor = _FakeSigningExecutor()
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
    )

    started = coordinator.begin()

    assert started.request is not None
    assert started.state.transaction_active is True
    assert started.state.can_sign is False
    assert started.state.stage_text == "Step 5 of 6 — Confirm and sign"
    assert "Signing is starting" not in started.state.detail_text
    duplicate = coordinator.begin()
    assert duplicate.error_message == "Signing is already in progress."

    result = SigningResult(
        success=True,
        failure_code=None,
        message="Signing completed successfully.",
    )
    completed = coordinator.complete(result=result)

    assert completed.status_event == "sign_success"
    assert completed.state.transaction_active is False
    assert completed.state.last_signing_result == result


def test_signing_action_coordinator_success_without_reopen_capability_has_no_recommended_action(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=_FakeSigningExecutor(
            SigningResult(
                success=True,
                failure_code=None,
                message="Signing completed successfully.",
                timestamp_present=False,
            )
        ),
        can_open_signed_output=False,
    )

    transition = coordinator.submit()

    assert transition.state.can_open_signed_output is False
    assert transition.state.recommended_action is None


def test_signing_action_coordinator_failure_tracks_error_state(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    executor = _FakeSigningExecutor(
        SigningResult(
            success=False,
            failure_code=FailureCode.PDF_SIGNING_FAILED,
            message="Signing failed before an output was preserved.",
        )
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
        can_open_signed_output=True,
    )

    transition = coordinator.submit()

    assert transition.request is not None
    assert transition.status_event == "sign_failure"
    assert transition.error_message == "Signing failed before an output was preserved."
    assert transition.error_via_emit is False
    assert transition.state.last_signing_result is not None
    assert transition.state.last_signing_result.success is False
    assert transition.state.status == "signing_failed"
    assert transition.state.stage_text == "Signing failed"
    assert transition.state.result_text == "Signing failed before an output was preserved."
    assert transition.state.can_open_signed_output is False
    assert transition.state.recommended_action == "sign"
    assert coordinator.open_signed_output() is None


def test_signing_action_coordinator_exposes_preserved_artifact_recovery_actions(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    preserved = str(tmp_path / "preserved.tmp")
    executor = _FakeRecoveryExecutor(
        SigningResult(
            success=False,
            failure_code=FailureCode.POST_VERIFY_FAILED,
            message="Post-sign verification failed; preserved artifact is untrusted.",
            preserved_artifact_path=preserved,
        )
    )
    cleaned: list[str] = []
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
        verify_preserved_artifact=executor.verify_preserved_artifact,
        can_open_preserved_copy=True,
        cleanup_preserved_artifact=cleaned.append,
    )

    transition = coordinator.submit()

    assert transition.state.stage_text == "Saved but not verified"
    assert "must not yet be relied upon" in transition.state.detail_text
    assert transition.state.can_sign is False
    assert transition.state.status == "saved_but_not_verified"
    assert transition.state.can_verify_again is True
    assert transition.state.can_return_to_draft is True
    assert transition.state.can_open_preserved_copy is True
    assert transition.state.recommended_action == "verify_again"
    assert coordinator.open_preserved_copy() == preserved

    verified = coordinator.verify_again()
    assert verified.status_event == "verify_success"
    assert executor.verify_calls == [preserved]
    assert "verified locally" in verified.state.result_text
    assert verified.state.recommended_action == "open_preserved_copy"

    returned = coordinator.return_to_draft()
    assert returned.last_signing_result is None
    assert returned.can_verify_again is False
    assert returned.recommended_action == "sign"
    assert cleaned == [preserved]


def test_signing_action_coordinator_keeps_invalid_retry_in_recovery_state(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    preserved = str(tmp_path / "preserved.tmp")
    executor = _FakeRecoveryExecutor(
        SigningResult(
            success=False,
            failure_code=FailureCode.POST_VERIFY_FAILED,
            message="untrusted",
            preserved_artifact_path=preserved,
        )
    )
    executor.verify_preserved_artifact = lambda _path: _InvalidVerificationSummary()
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=executor,
        verify_preserved_artifact=executor.verify_preserved_artifact,
        can_open_preserved_copy=True,
    )

    coordinator.submit()
    retry = coordinator.verify_again()

    assert retry.status_event == "verify_failure"
    assert retry.state.can_verify_again is True
    assert retry.state.recommended_action == "verify_again"


def test_signing_action_coordinator_rejects_missing_required_timestamp_on_retry(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    preserved = str(tmp_path / "preserved.tmp")
    result = SigningResult(
        success=False,
        failure_code=FailureCode.POST_VERIFY_FAILED,
        message="timestamp missing",
        preserved_artifact_path=preserved,
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=_FakeSigningExecutor(result),
        verify_preserved_artifact=lambda _path: _MissingTimestampVerificationSummary(),
        can_open_preserved_copy=True,
    )

    coordinator.submit()
    retry = coordinator.verify_again()

    assert retry.status_event == "verify_failure"
    assert "trusted preserved artifact" in retry.state.result_text


def test_untrusted_recovery_workspace_blocks_signing_until_verified(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    executor = _FakeRecoveryExecutor()
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        verify_preserved_artifact=executor.verify_preserved_artifact,
        can_open_preserved_copy=False,
        untrusted_recovery=True,
    )

    state = coordinator.load()

    assert state.can_sign is False
    assert state.can_verify_again is True
    assert state.can_return_to_draft is True
    assert state.recommended_action == "verify_again"

    retry = coordinator.verify_again()

    assert retry.state.can_sign is True
    assert retry.state.recommended_action == "sign"


def test_untrusted_recovery_workspace_blocks_restricted_later_approval(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        verify_preserved_artifact=lambda _path: _RestrictedVerificationSummary(),
        untrusted_recovery=True,
    )

    coordinator.load()
    retry = coordinator.verify_again()

    assert retry.state.can_sign is False
    assert retry.state.recommended_action == "return_to_draft"


def test_recovery_cleanup_hook_releases_preserved_workspace_artifact(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    cleaned: list[str] = []
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        verify_preserved_artifact=lambda _path: _MissingTimestampVerificationSummary(),
        cleanup_preserved_artifact=cleaned.append,
        untrusted_recovery=True,
    )

    coordinator.load()
    coordinator.cleanup_recovery_artifact()

    assert cleaned == [workflow.input_pdf_path]
    assert coordinator.load().can_return_to_draft is False


def test_signing_action_coordinator_exception_uses_emit_error_path(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        readiness=_readiness(workflow, ready=True, text=""),
        sign_executor=_FakeSigningExecutor(error=RuntimeError("boom")),
        can_open_signed_output=True,
    )

    transition = coordinator.submit()

    assert transition.request is not None
    assert transition.error_via_emit is True
    assert transition.error_message == "Signing failed: boom"
    assert transition.state.last_signing_result is not None
    assert transition.state.last_signing_result.success is False
    assert transition.state.result_text == "Signing failed: boom"
    assert transition.state.recommended_action == "sign"
