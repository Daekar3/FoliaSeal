from pathlib import Path

from foliaseal.application import SigningDraftWorkflow
from foliaseal.domain.errors import FailureCode
from foliaseal.domain.models import SigningResult
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
        is_ready_to_sign=lambda: False,
        validation_text=lambda: "",
    )

    state = coordinator.load()

    assert state.can_sign is False
    assert state.stage_text == "Step 3 of 6 — Place visible signature"
    assert "Drag on the page to place the visible signature" in state.detail_text
    assert state.last_signing_result is None
    assert state.can_open_signed_output is False


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
        is_ready_to_sign=lambda: False,
        validation_text=lambda: "Choose a certificate before signing.",
    )

    state = coordinator.load()

    assert state.stage_text == "Step 2 of 6 — Choose signing setup"
    assert "choose or create a certificate" in state.detail_text.lower()


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
        is_ready_to_sign=lambda: True,
        validation_text=lambda: "",
        sign_executor=executor,
        can_open_signed_output=True,
    )

    transition = coordinator.submit()
    request = transition.request
    assert request is not None

    updated = coordinator.accept_output_path(str(tmp_path / "other.pdf"))

    assert workflow.output_pdf_path == str(tmp_path / "other.pdf")
    assert updated.last_signing_result is None
    assert updated.result_text == f"Output will be saved to: {tmp_path / 'other.pdf'}"
    assert updated.can_open_signed_output is False
    assert updated.stage_text == "Step 5 of 6 — Confirm and sign"


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
        is_ready_to_sign=lambda: True,
        validation_text=lambda: "",
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


def test_signing_action_coordinator_returns_validation_failure_without_request(
    tmp_path: Path,
) -> None:
    workflow = _workflow(tmp_path)
    applied = []
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: applied.append(True),
        is_ready_to_sign=lambda: False,
        validation_text=lambda: "Selection is incomplete.",
    )

    transition = coordinator.submit()

    assert applied == [True]
    assert transition.request is None
    assert transition.error_message == "Selection is incomplete."
    assert transition.error_via_emit is True
    assert transition.state.last_signing_result is None
    assert transition.state.stage_text == "Step 4 of 6 — Review readiness"


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
        is_ready_to_sign=lambda: True,
        validation_text=lambda: "",
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
    assert coordinator.open_signed_output() == workflow.output_pdf_path


def test_signing_action_coordinator_failure_tracks_error_state(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    executor = _FakeSigningExecutor(
        SigningResult(
            success=False,
            failure_code=FailureCode.POST_VERIFY_FAILED,
            message="Post-sign verification failed.",
        )
    )
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        is_ready_to_sign=lambda: True,
        validation_text=lambda: "",
        sign_executor=executor,
        can_open_signed_output=True,
    )

    transition = coordinator.submit()

    assert transition.request is not None
    assert transition.status_event == "sign_failure"
    assert transition.error_message == "Post-sign verification failed."
    assert transition.error_via_emit is False
    assert transition.state.last_signing_result is not None
    assert transition.state.last_signing_result.success is False
    assert transition.state.result_text == "Post-sign verification failed."
    assert transition.state.can_open_signed_output is False
    assert coordinator.open_signed_output() is None


def test_signing_action_coordinator_exception_uses_emit_error_path(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    coordinator = SigningActionCoordinator(
        workflow=workflow,
        apply_changes=lambda: None,
        is_ready_to_sign=lambda: True,
        validation_text=lambda: "",
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
