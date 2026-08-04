from __future__ import annotations

import pytest

from foliaseal.presentation.qt.app_frame_workspace_open import (
    WorkspaceHandle,
)
from foliaseal.presentation.qt.signing_workspace_lifecycle import (
    SigningWorkspaceLifecycle,
)


class _Widget:
    def __init__(self, name: str, events: list[str]) -> None:
        self.name = name
        self.events = events
        self.close_calls = 0
        self.delete_later_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        self.events.append(f"close:{self.name}")

    def deleteLater(self) -> None:  # noqa: N802
        self.delete_later_calls += 1
        self.events.append(f"delete:{self.name}")


class _WidgetWithoutCleanup:
    pass


class _Outcome:
    def __init__(self, widget) -> None:
        self.handle = WorkspaceHandle(
            source_pdf=object(),
            widget=widget,
            shell=object(),
            testing=object(),
            viewer_workflow=object(),
            signing_workflow=object(),
        )


class _OpenPort:
    def __init__(self, outcomes) -> None:
        self.outcomes = list(outcomes)
        self.commands = []

    def open_workspace(self, command):
        self.commands.append(command)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome.handle


class _Mount:
    def __init__(self, events: list[str], *, fail: bool = False) -> None:
        self.events = events
        self.fail = fail
        self.widgets = []

    def mount(self, widget) -> None:
        self.events.append(f"mount:{getattr(widget, 'name', 'plain')}")
        if self.fail:
            raise RuntimeError("mount failed")
        self.widgets.append(widget)


def _command():
    return object()


def test_replace_mounts_candidate_before_closing_previous_workspace() -> None:
    events: list[str] = []
    first = _Widget("first", events)
    second = _Widget("second", events)
    mount = _Mount(events)
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=_OpenPort([_Outcome(first), _Outcome(second)]),
        mount_port=mount,
    )

    lifecycle.replace(_command())
    handle = lifecycle.replace(_command())

    assert handle.widget is second
    assert lifecycle.active() is handle
    assert mount.widgets == [first, second]
    assert events == ["mount:first", "mount:second", "close:first", "delete:first"]
    assert first.close_calls == 1
    assert first.delete_later_calls == 1
    assert second.close_calls == 0


def test_failed_composition_preserves_current_workspace() -> None:
    events: list[str] = []
    first = _Widget("first", events)
    mount = _Mount(events)
    open_port = _OpenPort([_Outcome(first), RuntimeError("bad pdf")])
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=open_port,
        mount_port=mount,
    )
    lifecycle.replace(_command())

    with pytest.raises(RuntimeError, match="bad pdf"):
        lifecycle.replace(_command())

    assert mount.widgets == [first]
    assert first.close_calls == 0


def test_failed_mount_disposes_candidate_and_preserves_previous_workspace() -> None:
    events: list[str] = []
    first = _Widget("first", events)
    second = _Widget("second", events)
    mount = _Mount(events)
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=_OpenPort([_Outcome(first), _Outcome(second)]),
        mount_port=mount,
    )
    lifecycle.replace(_command())
    mount.fail = True

    with pytest.raises(RuntimeError, match="mount failed"):
        lifecycle.replace(_command())

    assert mount.widgets == [first]
    assert first.close_calls == 0
    assert second.close_calls == 1
    assert second.delete_later_calls == 1


def test_close_is_idempotent_and_supports_plain_test_widgets() -> None:
    events: list[str] = []
    widget = _Widget("only", events)
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=_OpenPort([_Outcome(widget)]),
        mount_port=_Mount(events),
    )
    lifecycle.replace(_command())

    lifecycle.close()
    lifecycle.close()

    assert widget.close_calls == 1
    assert widget.delete_later_calls == 1

    plain = _WidgetWithoutCleanup()
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=_OpenPort([_Outcome(plain)]),
        mount_port=_Mount(events),
    )
    lifecycle.replace(_command())
    lifecycle.close()


def test_close_before_any_replace_is_a_no_op() -> None:
    events: list[str] = []
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=_OpenPort([]),
        mount_port=_Mount(events),
    )

    lifecycle.close()

    assert events == []


def test_replacing_with_same_widget_does_not_close_the_active_instance() -> None:
    events: list[str] = []
    widget = _Widget("shared", events)
    lifecycle = SigningWorkspaceLifecycle(
        workspace_open_port=_OpenPort([_Outcome(widget), _Outcome(widget)]),
        mount_port=_Mount(events),
    )

    lifecycle.replace(_command())
    lifecycle.replace(_command())

    assert widget.close_calls == 0
