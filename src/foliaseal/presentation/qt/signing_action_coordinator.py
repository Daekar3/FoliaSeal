"""State coordinator for the signing action and confirmation workflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Literal

from foliaseal.application import format_signing_completion_message
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from foliaseal.application.signing_readiness import (
    SigningReadiness,
    SigningReadinessAction,
    SigningReadinessStage,
)
from foliaseal.domain.errors import FailureCode
from foliaseal.domain.models import SigningRequest, SigningResult

SigningRequestExecutor = object
ResultKind = Literal["neutral", "success", "error"]
SigningActionStatus = Literal[
    "readiness",
    "signing",
    "signed_and_verified",
    "saved_but_not_verified",
    "signing_failed",
]
RecommendedAction = Literal[
    "sign",
    "open_signed_output",
    "verify_again",
    "return_to_draft",
    "open_preserved_copy",
] | SigningReadinessAction


@dataclass(frozen=True)
class SigningActionState:
    """UI-facing state for the signing action panel and reopen actions."""

    can_sign: bool
    stage_text: str
    detail_text: str
    result_text: str
    result_kind: ResultKind
    last_signing_result: SigningResult | None
    last_successful_output_path: str | None
    can_open_signed_output: bool
    transaction_active: bool = False
    transaction_elapsed_seconds: float = 0.0
    recommended_action: RecommendedAction | None = None
    can_verify_again: bool = False
    can_return_to_draft: bool = False
    can_open_preserved_copy: bool = False
    status: SigningActionStatus = "readiness"


@dataclass(frozen=True)
class SigningActionTransition:
    """Result of driving the signing action state machine."""

    request: SigningRequest | None
    state: SigningActionState
    error_message: str | None = None
    error_via_emit: bool = False
    status_event: str | None = None


class SigningActionCoordinator:
    """Own signing action state transitions while leaving Qt rendering outside."""

    def __init__(
        self,
        *,
        workflow: SigningDraftWorkflow,
        apply_changes: Callable[[], None],
        readiness: Callable[[], SigningReadiness],
        sign_executor: object | None = None,
        on_sign_request: Callable[[SigningRequest], None] | None = None,
        can_open_signed_output: bool = False,
        verify_preserved_artifact: Callable[[str], object] | None = None,
        can_open_preserved_copy: bool = False,
        cleanup_preserved_artifact: Callable[[str], None] | None = None,
        untrusted_recovery: bool = False,
    ) -> None:
        self._workflow = workflow
        self._apply_changes = apply_changes
        self._readiness = readiness
        self._sign_executor = sign_executor
        self._on_sign_request = on_sign_request
        self._can_open_signed_output = can_open_signed_output
        self._verify_preserved_artifact = verify_preserved_artifact
        self._can_open_preserved_copy = can_open_preserved_copy
        self._cleanup_preserved_artifact = cleanup_preserved_artifact
        self._untrusted_recovery = untrusted_recovery
        self._recovery_dismissed = False
        self._preserved_artifact_verified = False
        self._recovery_permission_allows = False
        self._last_signing_result: SigningResult | None = None
        self._last_successful_output_path: str | None = None
        self._result_text = ""
        self._result_kind: ResultKind = "neutral"
        self._recovery_timestamp_required = False
        self._recovery_trust_required = False
        self._transaction_active = False
        self._transaction_request: SigningRequest | None = None
        self._transaction_started_at: float | None = None

    @property
    def last_signing_result(self) -> SigningResult | None:
        return self._last_signing_result

    def load(self) -> SigningActionState:
        return self._build_state()

    def accept_output_path(
        self,
        selected_path: str,
        *,
        allow_source_overwrite: bool = False,
    ) -> SigningActionState:
        self._workflow.confirm_output_pdf_path(selected_path)
        if allow_source_overwrite:
            self._workflow.authorize_source_overwrite()
        self._clear_previous_signing_result()
        self._result_text = f"Output will be saved to: {selected_path}"
        self._result_kind = "neutral"
        return self._build_state()

    def invalidate(self, reason: str) -> SigningActionState:
        del reason
        self._clear_previous_signing_result()
        return self._build_state()

    def begin(self) -> SigningActionTransition:
        """Prepare one confirmed request and mark its non-cancellable transaction active."""
        if self._transaction_active:
            return SigningActionTransition(
                request=self._transaction_request,
                state=self._build_state(),
                error_message="Signing is already in progress.",
                error_via_emit=True,
            )
        self._apply_changes()
        readiness = self._readiness()
        if not readiness.can_sign:
            self._clear_previous_signing_result()
            return SigningActionTransition(
                request=None,
                state=self._build_state(),
                error_message=readiness.detail,
                error_via_emit=True,
            )

        request = self._workflow.build_signing_request()
        if self._on_sign_request is not None:
            self._on_sign_request(request)
        if self._sign_executor is None:
            self._clear_previous_signing_result()
            return SigningActionTransition(request=request, state=self._build_state())
        self._transaction_active = True
        self._transaction_request = request
        self._transaction_started_at = monotonic()
        self._result_text = ""
        self._result_kind = "neutral"
        return SigningActionTransition(request=request, state=self._build_state())

    def complete(
        self,
        result: SigningResult | None = None,
        error: BaseException | None = None,
    ) -> SigningActionTransition:
        """Apply one worker terminal result on the caller's (Qt) thread."""
        request = self._transaction_request
        if not self._transaction_active or request is None:
            raise RuntimeError("No signing transaction is active.")
        self._transaction_active = False
        self._transaction_request = None
        self._transaction_started_at = None
        if error is not None:
            failure_message = f"Signing failed: {error}"
            self._last_signing_result = SigningResult(
                success=False,
                failure_code=None,
                message=failure_message,
            )
            self._last_successful_output_path = None
            self._result_text = failure_message
            self._result_kind = "error"
            return SigningActionTransition(
                request=request,
                state=self._build_state(),
                error_message=failure_message,
                error_via_emit=True,
                status_event="sign_failure",
            )
        if result is None:
            raise ValueError("A signing result or error is required.")
        return self._apply_result(request, result)

    def submit(self) -> SigningActionTransition:
        transition = self.begin()
        request = transition.request
        if request is None or not self._transaction_active:
            return transition
        try:
            execute = getattr(self._sign_executor, "execute")
            result = execute(request)
        except Exception as exc:  # pragma: no cover - defensive integration guard
            return self.complete(error=exc)
        return self.complete(result=result)

    def _apply_result(
        self,
        request: SigningRequest,
        result: SigningResult,
    ) -> SigningActionTransition:
        self._last_signing_result = result
        if result.success:
            self._workflow.mark_clean()
            self._workflow.clear_session_secrets()
            self._last_successful_output_path = request.output_pdf_path
            self._result_text = format_signing_completion_message(
                result, request.output_pdf_path
            )
            self._result_kind = "success"
            return SigningActionTransition(
                request=request,
                state=self._build_state(),
                status_event="sign_success",
            )

        self._last_successful_output_path = None
        self._recovery_timestamp_required = request.timestamp_required
        self._recovery_trust_required = request.trust_policy is not None
        self._result_text = result.message
        self._result_kind = "error"
        return SigningActionTransition(
            request=request,
            state=self._build_state(),
            error_message=result.message,
            status_event="sign_failure",
        )

    def verify_again(self) -> SigningActionTransition:
        """Retry local verification of the preserved, untrusted artifact."""

        artifact_path = self._preserved_artifact_path()
        if artifact_path is None or self._verify_preserved_artifact is None:
            return SigningActionTransition(request=None, state=self._build_state())
        try:
            summary = self._verify_preserved_artifact(artifact_path)
            if (
                getattr(summary, "signatures_cryptographically_valid", None) is not True
                or (
                    self._recovery_timestamp_required
                    and getattr(summary, "timestamp_present", None) is not True
                )
                or (
                    self._recovery_trust_required
                    and (
                        getattr(summary, "timestamp_cryptographically_valid", None) is not True
                        or getattr(summary, "tsa_chain_trusted", None) is not True
                    )
                )
                or getattr(summary, "timestamp_cryptographically_valid", None) is False
                or getattr(summary, "tsa_chain_trusted", None) is False
            ):
                self._preserved_artifact_verified = False
                self._result_kind = "error"
                self._result_text = (
                    "Verification did not establish a trusted preserved artifact; keep it "
                    "separate from the requested output."
                )
                return SigningActionTransition(
                    request=None,
                    state=self._build_state(),
                    error_message=self._result_text,
                    status_event="verify_failure",
                )
            self._recovery_permission_allows = (
                not bool(getattr(summary, "certification_restricted", False))
                and getattr(summary, "restriction_reason", None) is None
                and getattr(summary, "docmdp_permission", None)
                in {None, "fill_forms", "annotate"}
            )
        except Exception as exc:  # pragma: no cover - defensive integration guard
            self._preserved_artifact_verified = False
            self._result_kind = "error"
            self._result_text = f"Verification failed again: {exc}"
            return SigningActionTransition(
                request=None,
                state=self._build_state(),
                error_message=self._result_text,
                status_event="verify_failure",
            )
        self._preserved_artifact_verified = True
        self._result_kind = "success"
        self._result_text = (
            "Preserved artifact verified locally; it remains separate from the requested output "
            "until you choose how to recover."
        )
        return SigningActionTransition(
            request=None,
            state=self._build_state(),
            status_event="verify_success",
        )

    def return_to_draft(self) -> SigningActionState:
        """Dismiss recovery state without changing the authored draft."""

        artifact_path = self._preserved_artifact_path()
        if artifact_path is not None and self._cleanup_preserved_artifact is not None:
            self._cleanup_preserved_artifact(artifact_path)
        self._last_signing_result = None
        self._recovery_dismissed = True
        self._result_text = "Returned to the signing draft."
        self._result_kind = "neutral"
        self._preserved_artifact_verified = False
        self._recovery_permission_allows = False
        self._recovery_timestamp_required = False
        self._recovery_trust_required = False
        return self._build_state()

    def cleanup_recovery_artifact(self) -> None:
        """Release a preserved artifact when its workspace is being disposed."""

        artifact_path = self._preserved_artifact_path()
        if artifact_path is not None and self._cleanup_preserved_artifact is not None:
            self._cleanup_preserved_artifact(artifact_path)
        self._last_signing_result = None
        self._recovery_dismissed = True

    def open_preserved_copy(self) -> str | None:
        """Return the preserved artifact only after explicit user choice."""

        if not self._can_open_preserved_copy:
            return None
        return self._preserved_artifact_path()

    def open_signed_output(self) -> str | None:
        if not self._can_open_signed_output:
            return None
        return self._last_successful_output_path

    def _clear_previous_signing_result(self) -> None:
        self._last_signing_result = None
        self._last_successful_output_path = None
        self._result_text = ""
        self._result_kind = "neutral"
        self._preserved_artifact_verified = False

    def _preserved_artifact_path(self) -> str | None:
        if self._last_signing_result is None:
            if self._untrusted_recovery and not self._recovery_dismissed:
                return self._workflow.input_pdf_path
            return None
        return self._last_signing_result.preserved_artifact_path

    def _build_state(self) -> SigningActionState:
        readiness = self._readiness()
        transaction_elapsed = (
            max(0.0, monotonic() - self._transaction_started_at)
            if self._transaction_active and self._transaction_started_at is not None
            else 0.0
        )
        has_successful_output = (
            self._last_signing_result is not None
            and self._last_signing_result.success
            and self._last_successful_output_path is not None
        )
        preserved_artifact_path = self._preserved_artifact_path()
        has_recovery_artifact = preserved_artifact_path is not None
        saved_but_not_verified = (
            self._last_signing_result is not None
            and not self._last_signing_result.success
            and self._last_signing_result.failure_code == FailureCode.POST_VERIFY_FAILED
            and has_recovery_artifact
            and not self._preserved_artifact_verified
        )
        can_sign = readiness.can_sign and (
            not self._untrusted_recovery
            or (self._preserved_artifact_verified and self._recovery_permission_allows)
        ) and not saved_but_not_verified
        status: SigningActionStatus = "readiness"
        if self._transaction_active:
            status = "signing"
            can_sign = False
            if transaction_elapsed < 1.0:
                stage_text = "Step 5 of 6 — Confirm and sign"
                detail_text = readiness.detail
            elif transaction_elapsed < 10.0:
                stage_text = "Signing — preparing, writing, and verifying"
                detail_text = "FoliaSeal is signing and verifying the PDF."
            else:
                stage_text = "Signing — still working"
                detail_text = (
                    "Signing is taking longer than expected; FoliaSeal is still working."
                )
        elif has_successful_output:
            status = "signed_and_verified"
            stage_text = "Step 6 of 6 — Verify signed PDF"
            detail_text = (
                "Open the signed PDF, review its local verification status, and keep any "
                "trust caveats in mind. Add another approval signature only if document "
                "permissions permit it."
            )
        elif saved_but_not_verified:
            status = "saved_but_not_verified"
            stage_text = "Saved but not verified"
            detail_text = (
                "The signed PDF was saved, but local verification did not complete. It must not "
                "yet be relied upon; verify again, return to the draft, or open the preserved copy."
            )
        elif self._last_signing_result is not None and not self._last_signing_result.success:
            status = "signing_failed"
            stage_text = "Signing failed"
            detail_text = (
                "The signing attempt did not produce a trusted output. Correct the reported "
                "problem and try again."
            )
        elif has_recovery_artifact and not can_sign:
            stage_text = "Step 6 of 6 — Recover verification result"
            detail_text = (
                "The signed artifact was preserved but is not trusted yet. Verify again, return "
                "to the draft, or open the preserved copy for technical inspection."
            )
        elif can_sign:
            stage_text = "Step 5 of 6 — Confirm and sign"
            detail_text = (
                "Confirm the output path and review the on-page preview, then use Confirm and sign "
                "to review the final signing summary."
            )
        else:
            stage_text = _readiness_stage_text(readiness.stage)
            detail_text = readiness.detail

        return SigningActionState(
            can_sign=can_sign,
            stage_text=stage_text,
            detail_text=detail_text,
            result_text=self._result_text,
            result_kind=self._result_kind,
            last_signing_result=self._last_signing_result,
            last_successful_output_path=self._last_successful_output_path,
            can_open_signed_output=(
                self._last_successful_output_path is not None
                and self._can_open_signed_output
            ),
            transaction_active=self._transaction_active,
            transaction_elapsed_seconds=transaction_elapsed,
            can_verify_again=(
                has_recovery_artifact and self._verify_preserved_artifact is not None
            ),
            can_return_to_draft=has_recovery_artifact,
            can_open_preserved_copy=(has_recovery_artifact and self._can_open_preserved_copy),
            status=status,
            recommended_action=_recommended_action(
                readiness=readiness,
                can_sign=can_sign,
                has_successful_output=has_successful_output,
                has_recovery_artifact=has_recovery_artifact,
                preserved_artifact_verified=self._preserved_artifact_verified,
                can_open_signed_output=self._can_open_signed_output,
                can_open_preserved_copy=self._can_open_preserved_copy,
                can_verify_again=self._verify_preserved_artifact is not None,
            ),
        )


def _readiness_stage_text(stage: SigningReadinessStage) -> str:
    labels = {
        SigningReadinessStage.SELECT_PRESET: "Step 2 of 6 — Select a signature preset",
        SigningReadinessStage.SETUP_REQUIRED: "Step 2 of 6 — Setup required",
        SigningReadinessStage.PLACE_SIGNATURE: "Step 3 of 6 — Place visible signature",
        SigningReadinessStage.REVIEW_READINESS: "Step 4 of 6 — Review readiness",
        SigningReadinessStage.READY: "Step 5 of 6 — Confirm and sign",
    }
    return labels[stage]


def _recommended_action(
    *,
    readiness: SigningReadiness,
    can_sign: bool,
    has_successful_output: bool,
    has_recovery_artifact: bool,
    preserved_artifact_verified: bool,
    can_open_signed_output: bool,
    can_open_preserved_copy: bool,
    can_verify_again: bool,
) -> RecommendedAction | None:
    if has_successful_output:
        return "open_signed_output" if can_open_signed_output else None
    if has_recovery_artifact and not preserved_artifact_verified and can_verify_again:
        return "verify_again"
    if has_recovery_artifact and can_open_preserved_copy:
        return "open_preserved_copy"
    if has_recovery_artifact and can_sign:
        return readiness.recommended_action
    if has_recovery_artifact:
        return "return_to_draft"
    if can_sign or readiness.recommended_action is not None:
        return readiness.recommended_action
    return None
