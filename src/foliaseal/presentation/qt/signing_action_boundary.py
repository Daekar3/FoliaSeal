"""Shell-facing boundary for the signing action flow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from foliaseal.domain.models import SigningRequest
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionCoordinator,
    SigningActionState,
    SigningActionTransition,
)
from foliaseal.presentation.qt.signing_transaction_runner import SigningTransactionRunner


class ErrorEmitter(Protocol):
    def __call__(self, message: str) -> None: ...


@dataclass(frozen=True)
class SigningActionBoundaryResult:
    """Result of driving a shell-facing signing action."""

    state: SigningActionState
    request: SigningRequest | None = None
    opened_output_path: str | None = None
    status_event: str | None = None
    error_message: str | None = None
    error_via_emit: bool = False


class SigningActionBoundary:
    """Own shell-facing signing-action orchestration over the coordinator."""

    def __init__(
        self,
        *,
        coordinator: SigningActionCoordinator,
        emit_error: ErrorEmitter | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
        on_open_signed_output: Callable[[str], None] | None = None,
        transaction_runner: SigningTransactionRunner | None = None,
    ) -> None:
        self._coordinator = coordinator
        self._emit_error = emit_error
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._on_open_signed_output = on_open_signed_output
        self._transaction_runner = transaction_runner

    @property
    def supports_async_transaction(self) -> bool:
        """Whether the boundary has an owned worker for the production Qt path."""
        return self._transaction_runner is not None

    def load(self) -> SigningActionState:
        return self._coordinator.load()

    def accept_output_path(
        self,
        selected_path: str,
        *,
        allow_source_overwrite: bool = False,
    ) -> SigningActionBoundaryResult:
        if allow_source_overwrite:
            state = self._coordinator.accept_output_path(
                selected_path,
                allow_source_overwrite=True,
            )
        else:
            # Keep the narrow pre-authorization call shape for existing test and
            # harness coordinators; ordinary output selection remains unchanged.
            state = self._coordinator.accept_output_path(selected_path)
        return SigningActionBoundaryResult(
            state=state
        )

    def submit(self) -> SigningActionBoundaryResult:
        if self._on_status_change is not None:
            self._on_status_change("sign_started")
        transition = self._coordinator.submit()
        if transition.status_event is not None and self._on_status_change is not None:
            self._on_status_change(transition.status_event)
        self._emit_transition_error(transition)
        return SigningActionBoundaryResult(
            state=transition.state,
            request=transition.request,
            status_event=transition.status_event,
            error_message=transition.error_message,
            error_via_emit=transition.error_via_emit,
        )

    def begin_transaction(self) -> SigningActionBoundaryResult:
        """Begin the production non-blocking signing transaction."""
        transition = self._coordinator.begin()
        worker_started = False
        if transition.request is not None and self._transaction_runner is not None:
            try:
                self._transaction_runner.start(transition.request)
                worker_started = True
            except Exception as exc:
                transition = self._coordinator.complete(error=exc)
        if self._on_status_change is not None and worker_started:
            self._on_status_change("sign_started")
        if transition.status_event is not None and self._on_status_change is not None:
            self._on_status_change(transition.status_event)
        if transition.error_message is not None:
            self._emit_transition_error(transition)
        return SigningActionBoundaryResult(
            state=transition.state,
            request=transition.request,
            error_message=transition.error_message,
            error_via_emit=transition.error_via_emit,
        )

    def poll_transaction(self) -> SigningActionBoundaryResult | None:
        """Deliver one worker terminal result on the caller's thread."""
        runner = self._transaction_runner
        if runner is None:
            return None
        completion = runner.poll_completion()
        if completion is None:
            return None
        if isinstance(completion, BaseException):
            transition = self._coordinator.complete(error=completion)
        else:
            transition = self._coordinator.complete(result=completion)
        if transition.status_event is not None and self._on_status_change is not None:
            self._on_status_change(transition.status_event)
        self._emit_transition_error(transition)
        return SigningActionBoundaryResult(
            state=transition.state,
            request=transition.request,
            status_event=transition.status_event,
            error_message=transition.error_message,
            error_via_emit=transition.error_via_emit,
        )

    def close_transaction(self) -> None:
        """Join and release the owned worker, if any."""
        if self._transaction_runner is not None:
            self._transaction_runner.close()

    def _emit_transition_error(self, transition: SigningActionTransition) -> None:
        if transition.error_message is None:
            return
        if transition.error_via_emit:
            if self._emit_error is not None:
                self._emit_error(transition.error_message)
        elif self._on_error is not None:
            self._on_error(transition.error_message)

    def open_signed_output(self) -> SigningActionBoundaryResult:
        output_path = self._coordinator.open_signed_output()
        if output_path is not None and self._on_open_signed_output is not None:
            self._on_open_signed_output(output_path)
        return SigningActionBoundaryResult(
            state=self._coordinator.load(),
            opened_output_path=output_path,
        )

    def verify_again(self) -> SigningActionBoundaryResult:
        transition = self._coordinator.verify_again()
        if transition.status_event is not None and self._on_status_change is not None:
            self._on_status_change(transition.status_event)
        return SigningActionBoundaryResult(
            state=transition.state,
            status_event=transition.status_event,
            error_message=transition.error_message,
        )

    def return_to_draft(self) -> SigningActionBoundaryResult:
        result = SigningActionBoundaryResult(state=self._coordinator.return_to_draft())
        if self._on_status_change is not None:
            self._on_status_change("recovery_return_to_draft")
        return result

    def cleanup_recovery_artifact(self) -> None:
        self._coordinator.cleanup_recovery_artifact()

    def open_preserved_copy(self) -> SigningActionBoundaryResult:
        output_path = self._coordinator.open_preserved_copy()
        if output_path is not None and self._on_open_signed_output is not None:
            self._on_open_signed_output(output_path)
        return SigningActionBoundaryResult(
            state=self._coordinator.load(),
            opened_output_path=output_path,
        )

    def invalidate(self, reason: str) -> SigningActionBoundaryResult:
        return SigningActionBoundaryResult(state=self._coordinator.invalidate(reason))
