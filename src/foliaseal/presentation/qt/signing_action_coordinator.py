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
    ) -> None:
        self._workflow = workflow
        self._apply_changes = apply_changes
        self._is_ready_to_sign = is_ready_to_sign
        self._validation_text = validation_text
        self._sign_executor = sign_executor
        self._on_sign_request = on_sign_request
        self._can_open_signed_output = can_open_signed_output
        self._last_signing_result: SigningResult | None = None
        self._last_successful_output_path: str | None = None
        self._result_text = ""
        self._result_kind: ResultKind = "neutral"

    @property
    def last_signing_result(self) -> SigningResult | None:
        return self._last_signing_result

    def load(self) -> SigningActionState:
        return self._build_state()

    def accept_output_path(self, selected_path: str) -> SigningActionState:
        self._workflow.output_pdf_path = selected_path
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
        self._result_text = result.message
        self._result_kind = "error"
        return SigningActionTransition(
            request=request,
            state=self._build_state(),
            error_message=result.message,
            status_event="sign_failure",
        )

    def open_signed_output(self) -> str | None:
        if not self._can_open_signed_output:
            return None
        return self._last_successful_output_path

    def _clear_previous_signing_result(self) -> None:
        self._last_signing_result = None
        self._last_successful_output_path = None
        self._result_text = ""
        self._result_kind = "neutral"

    def _build_state(self) -> SigningActionState:
        can_sign = self._is_ready_to_sign()
        if (
            self._last_signing_result is not None
            and self._last_signing_result.success
            and self._last_successful_output_path is not None
        ):
            stage_text = "Signed"
            detail_text = (
                "Open or verify the signed PDF, then add another approval signature "
                "later if the document permits it."
            )
        elif can_sign:
            stage_text = "Confirm/sign"
            detail_text = "Confirm the output path, review readiness, then sign the PDF."
        elif self._workflow.signature_rect is None:
            stage_text = "Place signature"
            detail_text = (
                "Drag on the page to place the visible signature, or enter placement values."
            )
        else:
            stage_text = "Review preview"
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
        )
