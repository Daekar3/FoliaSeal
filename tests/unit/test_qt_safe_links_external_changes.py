"""Focused tests for the production external-link confirmation boundary."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from foliaseal.application.document_safety import (
    LinkDecision,
    LinkDecisionKind,
    classify_link_destination,
)
from foliaseal.presentation.qt.app_frame import FoliaSealAppFrame
from foliaseal.presentation.qt.external_link_confirmation import ExternalLinkOutcome
from foliaseal.presentation.qt.signing_action_boundary import SigningActionBoundary
from foliaseal.presentation.qt.signing_action_coordinator import SigningActionTransition
from tests.unit.test_qt_app_frame import _fake_bindings, _settings
from tests.unit.test_qt_signing_action_boundary import _FakeCoordinator, _state


def _frame(tmp_path: Path, opened: list[str], statuses: list[str]) -> FoliaSealAppFrame:
    return FoliaSealAppFrame(
        bindings=_fake_bindings(),
        app_settings=_settings(tmp_path),
        app_settings_store=None,
        shell_factory=None,
        render_backend_factory=lambda: object(),
        external_link_launcher=lambda destination: opened.append(destination) or True,
        on_status_change=statuses.append,
    )


def _external(destination: str) -> LinkDecision:
    return LinkDecision(
        kind=LinkDecisionKind.CONFIRM_EXTERNAL,
        destination=destination,
        reason="External destinations require confirmation before opening.",
    )


def test_external_link_approval_launches_once_and_cancel_is_safe(tmp_path: Path) -> None:
    opened: list[str] = []
    statuses: list[str] = []
    frame = _frame(tmp_path, opened, statuses)
    message_box = frame._bindings.q_message_box  # noqa: SLF001

    message_box.next_question_result = message_box.Yes
    approved = frame._handle_external_link_confirmation(_external("https://example.test/a"))  # noqa: SLF001
    assert approved.outcome is ExternalLinkOutcome.OPENED
    assert approved.launched is True
    assert opened == ["https://example.test/a"]

    message_box.next_question_result = message_box.No
    canceled = frame._handle_external_link_confirmation(_external("mailto:help@example.test"))  # noqa: SLF001
    assert canceled.outcome is ExternalLinkOutcome.CANCELED
    assert opened == ["https://example.test/a"]


def test_blocked_destination_never_reaches_dialog_or_launcher(tmp_path: Path) -> None:
    opened: list[str] = []
    frame = _frame(tmp_path, opened, [])
    message_box = frame._bindings.q_message_box  # noqa: SLF001
    decision = classify_link_destination("file:///tmp/private.pdf")

    result = frame._handle_external_link_confirmation(decision)  # noqa: SLF001

    assert result.outcome is ExternalLinkOutcome.IGNORED
    assert opened == []
    assert message_box.question_calls == []


def test_destination_display_is_bounded_before_confirmation(tmp_path: Path) -> None:
    opened: list[str] = []
    frame = _frame(tmp_path, opened, [])
    message_box = frame._bindings.q_message_box  # noqa: SLF001
    message_box.next_question_result = message_box.No
    decision = classify_link_destination("https://example.test/" + ("x" * 800))

    result = frame._handle_external_link_confirmation(decision)  # noqa: SLF001

    assert result.outcome is ExternalLinkOutcome.CANCELED
    assert len(decision.destination) == 512
    assert len(message_box.question_calls[-1][2]) < 700


def test_long_destination_displays_bounded_text_but_launches_full_target(tmp_path: Path) -> None:
    opened: list[str] = []
    frame = _frame(tmp_path, opened, [])
    message_box = frame._bindings.q_message_box  # noqa: SLF001
    message_box.next_question_result = message_box.Yes
    raw_destination = "https://example.test/" + ("x" * 800)

    result = frame._handle_external_link_confirmation(  # noqa: SLF001
        classify_link_destination(raw_destination)
    )

    assert result.outcome is ExternalLinkOutcome.OPENED
    assert result.destination == raw_destination[:512]
    assert result.launch_destination == raw_destination
    assert opened == [raw_destination]


def test_active_signing_defers_and_replaces_until_success(tmp_path: Path) -> None:
    opened: list[str] = []
    statuses: list[str] = []
    frame = _frame(tmp_path, opened, statuses)
    message_box = frame._bindings.q_message_box  # noqa: SLF001
    frame._signing_transaction_active = True  # noqa: SLF001

    first = frame._handle_external_link_confirmation(_external("https://example.test/old"))  # noqa: SLF001
    second = frame._handle_external_link_confirmation(_external("https://example.test/new"))  # noqa: SLF001

    assert first.outcome is ExternalLinkOutcome.DEFERRED
    assert second.outcome is ExternalLinkOutcome.REPLACED
    assert opened == []
    assert statuses[-2:] == ["external_link_deferred", "external_link_replaced"]

    message_box.next_question_result = message_box.Yes
    frame._signing_transaction_active = False  # noqa: SLF001
    frame._offer_pending_external_link()  # noqa: SLF001

    assert opened == ["https://example.test/new"]
    assert frame._pending_external_link is None  # noqa: SLF001


def test_signing_status_path_defers_then_offers_pending_link(tmp_path: Path) -> None:
    opened: list[str] = []
    frame = _frame(tmp_path, opened, [])
    message_box = frame._bindings.q_message_box  # noqa: SLF001
    message_box.next_question_result = message_box.Yes
    coordinator = _FakeCoordinator()
    coordinator.submitted_transition = SigningActionTransition(
        request=None,
        state=_state(result_text="Signing completed successfully."),
        status_event="sign_success",
    )

    def handle_status(status: str) -> None:
        frame._handle_status_change(status)  # noqa: SLF001
        if status == "sign_started":
            frame._handle_external_link_confirmation(  # noqa: SLF001
                _external("https://example.test/deferred")
            )

    boundary = SigningActionBoundary(
        coordinator=coordinator,
        on_status_change=handle_status,
    )
    boundary.submit()

    assert opened == ["https://example.test/deferred"]
    assert frame._pending_external_link is None  # noqa: SLF001


def test_default_launcher_uses_injected_qt_desktop_services_shape(tmp_path: Path) -> None:
    opened: list[object] = []
    frame = _frame(tmp_path, [], [])
    frame._bindings = replace(  # noqa: SLF001
        frame._bindings,
        q_desktop_services=type(
            "_DesktopServices",
            (),
            {"openUrl": staticmethod(lambda url: opened.append(url) or True)},
        ),
        q_url=lambda destination: ("QUrl", destination),
    )

    assert frame._launch_external_url("https://example.test/default") is True  # noqa: SLF001
    assert opened == [("QUrl", "https://example.test/default")]
