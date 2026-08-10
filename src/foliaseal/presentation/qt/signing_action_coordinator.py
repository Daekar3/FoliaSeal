"""State coordinator for the signing action and confirmation workflow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from foliaseal.application import format_signing_completion_message
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from foliaseal.domain.models import SigningRequest, SigningResult

SigningRequestExecutor = object
ResultKind = Literal["neutral", "success", "error"]
RecommendedAction = Literal[
    "sign",
    "open_signed_output",
    "verify_again",
    "return_to_draft",
    "open_preserved_copy",
]


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
    recommended_action: RecommendedAction | None = None
    can_verify_again: bool = False
    can_return_to_draft: bool = False
    can_open_preserved_copy: bool = False


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
        is_ready_to_sign: Callable[[], bool],
        validation_text: Callable[[], str],
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
        self._is_ready_to_sign = is_ready_to_sign
        self._validation_text = validation_text
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

    def submit(self) -> SigningActionTransition:
        self._apply_changes()
        if not self._is_ready_to_sign():
            self._clear_previous_signing_result()
            return SigningActionTransition(
                request=None,
                state=self._build_state(),
                error_message=self._validation_text(),
                error_via_emit=True,
            )

        request = self._workflow.build_signing_request()
        if self._on_sign_request is not None:
            self._on_sign_request(request)

        if self._sign_executor is None:
            self._clear_previous_signing_result()
            return SigningActionTransition(request=request, state=self._build_state())

        try:
            execute = getattr(self._sign_executor, "execute")
            result = execute(request)
        except Exception as exc:  # pragma: no cover - defensive integration guard
            failure_message = f"Signing failed: {exc}"
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
            )

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
        can_sign = self._is_ready_to_sign() and (
            not self._untrusted_recovery
            or (self._preserved_artifact_verified and self._recovery_permission_allows)
        )
        has_successful_output = (
            self._last_signing_result is not None
            and self._last_signing_result.success
            and self._last_successful_output_path is not None
        )
        preserved_artifact_path = self._preserved_artifact_path()
        has_recovery_artifact = preserved_artifact_path is not None
        if has_successful_output:
            stage_text = "Step 6 of 6 — Verify signed PDF"
            detail_text = (
                "Open the signed PDF, review its local verification status, and keep any "
                "trust caveats in mind. Add another approval signature only if document "
                "permissions permit it."
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
        elif not self._has_signing_setup():
            stage_text = "Step 2 of 6 — Choose signing setup"
            detail_text = (
                "Choose or create a certificate and signing setup in the sidebar before "
                "placing the visible signature."
            )
        elif self._workflow.signature_rect is None:
            stage_text = "Step 3 of 6 — Place visible signature"
            detail_text = (
                "Placement mode is active — Drag on the page to place the visible "
                "signature, or enter placement values."
            )
        else:
            stage_text = "Step 4 of 6 — Review readiness"
            validation_text = self._validation_text().strip()
            if validation_text:
                detail_text = validation_text
            else:
                detail_text = "Review the on-page preview and resolve any readiness warnings."

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
            can_verify_again=(
                has_recovery_artifact and self._verify_preserved_artifact is not None
            ),
            can_return_to_draft=has_recovery_artifact,
            can_open_preserved_copy=(has_recovery_artifact and self._can_open_preserved_copy),
            recommended_action=(
                "open_signed_output"
                if has_successful_output and self._can_open_signed_output
                else "verify_again"
                if (
                    has_recovery_artifact
                    and not self._preserved_artifact_verified
                    and self._verify_preserved_artifact is not None
                )
                else "open_preserved_copy"
                if has_recovery_artifact and self._can_open_preserved_copy
                else "sign"
                if can_sign
                and (
                    self._last_signing_result is None
                    or not self._last_signing_result.success
                )
                else "return_to_draft"
                if has_recovery_artifact
                else "sign"
                if can_sign
                and (
                    self._last_signing_result is None
                    or not self._last_signing_result.success
                )
                else None
            ),
        )

    def _has_signing_setup(self) -> bool:
        """Return whether the draft has the minimum material needed for signing."""

        return bool(self._workflow.certificate_path and self._workflow.passphrase)
