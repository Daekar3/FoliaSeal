from pathlib import Path

from foliaseal.domain.models import SigningResult
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionState,
    SigningActionTransition,
)
from tests.support.signing_builders import build_signing_request


def _state(
    *,
    result_text: str = "",
    can_open_signed_output: bool = False,
) -> SigningActionState:
    return SigningActionState(
        can_sign=True,
        stage_text="Confirm/sign",
        detail_text="Confirm the output path, review readiness, then sign the PDF.",
        result_text=result_text,
        result_kind="neutral",
        last_signing_result=None,
        last_successful_output_path=None,
        can_open_signed_output=can_open_signed_output,
    )


class _FakeCoordinator:
    def __init__(self, *, state: SigningActionState | None = None) -> None:
        self.state = state or _state()
        self.accepted_paths: list[str] = []
        self.submitted_transition = SigningActionTransition(
            request=None,
            state=self.state,
        )
        self.open_result: str | None = None
        self.invalidate_calls: list[str] = []
        self.load_calls = 0

    def load(self) -> SigningActionState:
        self.load_calls += 1
        return self.state

    def accept_output_path(self, selected_path: str) -> SigningActionState:
        self.accepted_paths.append(selected_path)
        self.state = _state(result_text=f"Output will be saved to: {selected_path}")
        return self.state

    def submit(self) -> SigningActionTransition:
        return self.submitted_transition

    def open_signed_output(self) -> str | None:
        return self.open_result

    def invalidate(self, reason: str) -> SigningActionState:
        self.invalidate_calls.append(reason)
        self.state = _state()
        return self.state


class _FakeTransactionRunner:
    def __init__(self, completion=None, *, start_error: Exception | None = None) -> None:
        self.completion = completion
        self.start_error = start_error
        self.started = []
        self.closed = False

    def start(self, request) -> None:
        if self.start_error is not None:
            raise self.start_error
        self.started.append(request)

    def is_running(self) -> bool:
        return self.completion is not None

    def poll_completion(self):
        completion, self.completion = self.completion, None
        return completion

    def close(self) -> None:
        self.closed = True


def test_signing_action_boundary_accept_output_path_returns_updated_state(tmp_path: Path) -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    coordinator = _FakeCoordinator()
    boundary = SigningActionBoundary(coordinator=coordinator)

    result = boundary.accept_output_path(str(tmp_path / "signed.pdf"))

    assert coordinator.accepted_paths == [str(tmp_path / "signed.pdf")]
    assert result.request is None
    assert result.state.result_text == f"Output will be saved to: {tmp_path / 'signed.pdf'}"


def test_signing_action_boundary_submit_emits_status_event(tmp_path: Path) -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    request = build_signing_request(tmp_path)
    coordinator = _FakeCoordinator()
    coordinator.submitted_transition = SigningActionTransition(
        request=request,
        state=_state(result_text="Signing completed successfully.", can_open_signed_output=True),
        status_event="sign_success",
    )
    status_events: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=coordinator,
        on_status_change=status_events.append,
    )

    result = boundary.submit()

    assert result.request == request
    assert result.status_event == "sign_success"
    assert status_events == ["sign_started", "sign_success"]
    assert result.state.can_open_signed_output is True


def test_signing_action_boundary_submit_uses_emit_error_path(tmp_path: Path) -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    request = build_signing_request(tmp_path)
    coordinator = _FakeCoordinator()
    coordinator.submitted_transition = SigningActionTransition(
        request=request,
        state=_state(result_text="Signing failed: boom"),
        error_message="Signing failed: boom",
        error_via_emit=True,
    )
    emitted: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=coordinator,
        emit_error=emitted.append,
    )

    result = boundary.submit()

    assert result.error_message == "Signing failed: boom"
    assert emitted == ["Signing failed: boom"]


def test_signing_action_boundary_submit_uses_on_error_path_when_not_emit(tmp_path: Path) -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    request = build_signing_request(tmp_path)
    coordinator = _FakeCoordinator()
    coordinator.submitted_transition = SigningActionTransition(
        request=request,
        state=_state(result_text="Post-sign verification failed."),
        error_message="Post-sign verification failed.",
        error_via_emit=False,
    )
    errors: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=coordinator,
        on_error=errors.append,
    )

    result = boundary.submit()

    assert result.error_message == "Post-sign verification failed."
    assert errors == ["Post-sign verification failed."]


def test_signing_action_boundary_open_signed_output_forwards_callback() -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    coordinator = _FakeCoordinator(
        state=_state(
            result_text="Signing completed successfully.",
            can_open_signed_output=True,
        )
    )
    coordinator.open_result = "/tmp/signed.pdf"
    opened: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=coordinator,
        on_open_signed_output=opened.append,
    )

    result = boundary.open_signed_output()

    assert result.opened_output_path == "/tmp/signed.pdf"
    assert opened == ["/tmp/signed.pdf"]


def test_signing_action_boundary_open_signed_output_is_guarded_when_disabled() -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    coordinator = _FakeCoordinator(state=_state(can_open_signed_output=False))
    opened: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=coordinator,
        on_open_signed_output=opened.append,
    )

    result = boundary.open_signed_output()

    assert result.opened_output_path is None
    assert result.state.can_open_signed_output is False
    assert opened == []


def test_signing_action_boundary_invalidate_returns_reset_state() -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    prior_state = SigningActionState(
        can_sign=True,
        stage_text="Signed",
        detail_text="Open or verify the signed PDF.",
        result_text="Signing completed successfully.",
        result_kind="success",
        last_signing_result=SigningResult(
            success=True,
            failure_code=None,
            message="Signing completed successfully.",
        ),
        last_successful_output_path="/tmp/signed.pdf",
        can_open_signed_output=True,
    )
    coordinator = _FakeCoordinator(state=prior_state)
    boundary = SigningActionBoundary(coordinator=coordinator)

    result = boundary.invalidate("clear")

    assert coordinator.invalidate_calls == ["clear"]
    assert result.state.stage_text == "Confirm/sign"
    assert result.state.result_text == ""


def test_signing_action_boundary_delivers_async_completion_on_poll(tmp_path: Path) -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    request = build_signing_request(tmp_path)
    result = SigningResult(
        success=True,
        failure_code=None,
        message="Signing completed successfully.",
    )

    class _AsyncCoordinator(_FakeCoordinator):
        def begin(self):
            return SigningActionTransition(
                request=request,
                state=_state(),
            )

        def complete(self, *, result=None, error=None):
            assert result is not None
            return SigningActionTransition(
                request=request,
                state=_state(result_text=result.message, can_open_signed_output=True),
                status_event="sign_success",
            )

    runner = _FakeTransactionRunner(result)
    status_events: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=_AsyncCoordinator(),
        transaction_runner=runner,
        on_status_change=status_events.append,
    )

    started = boundary.begin_transaction()
    completed = boundary.poll_transaction()

    assert started.request == request
    assert completed is not None
    assert completed.status_event == "sign_success"
    assert status_events == ["sign_started", "sign_success"]
    boundary.close_transaction()
    assert runner.closed is True


def test_signing_action_boundary_does_not_emit_started_when_worker_start_fails(
    tmp_path: Path,
) -> None:
    from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary

    request = build_signing_request(tmp_path)

    class _AsyncCoordinator(_FakeCoordinator):
        def begin(self):
            return SigningActionTransition(request=request, state=_state())

        def complete(self, *, result=None, error=None):
            assert error is not None
            return SigningActionTransition(
                request=request,
                state=_state(result_text=str(error)),
                error_message=str(error),
                error_via_emit=True,
                status_event="sign_failure",
            )

    events: list[str] = []
    errors: list[str] = []
    boundary = SigningActionBoundary(
        coordinator=_AsyncCoordinator(),
        transaction_runner=_FakeTransactionRunner(start_error=RuntimeError("cannot start")),
        on_status_change=events.append,
        emit_error=errors.append,
    )

    result = boundary.begin_transaction()

    assert events == ["sign_failure"]
    assert errors == ["cannot start"]
    assert result.state.transaction_active is False
