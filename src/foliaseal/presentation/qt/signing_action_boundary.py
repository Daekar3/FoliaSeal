"""Shell-facing boundary for the signing action flow."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from foliaseal.domain.models import SigningRequest
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionCoordinator,
    SigningActionState,
)


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
    ) -> None:
        self._coordinator = coordinator
        self._emit_error = emit_error
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._on_open_signed_output = on_open_signed_output

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
        transition = self._coordinator.submit()
        if transition.status_event is not None and self._on_status_change is not None:
            self._on_status_change(transition.status_event)
        if transition.error_message is not None:
            if transition.error_via_emit:
                if self._emit_error is not None:
                    self._emit_error(transition.error_message)
            elif self._on_error is not None:
                self._on_error(transition.error_message)
        return SigningActionBoundaryResult(
            state=transition.state,
            request=transition.request,
            status_event=transition.status_event,
            error_message=transition.error_message,
            error_via_emit=transition.error_via_emit,
        )

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
        return SigningActionBoundaryResult(state=self._coordinator.return_to_draft())

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
