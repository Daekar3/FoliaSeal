"""Atomic replacement and cleanup for one live signing workspace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from foliaseal.presentation.qt.app_frame_workspace_open import (
    OpenWorkspaceCommand,
    OpenWorkspaceOutcome,
    WorkspaceOpenPort,
)


class WorkspaceMountPort(Protocol):
    """Mount a concrete workspace widget into its presentation host."""

    def mount(self, widget: Any) -> None:
        """Install ``widget`` as the active central view."""


@dataclass(frozen=True)
class QtWorkspaceMount:
    """Qt adapter for mounting a workspace in a ``QMainWindow``."""

    window: Any

    def mount(self, widget: Any) -> None:
        self.window.setCentralWidget(widget)


class SigningWorkspaceLifecyclePort(Protocol):
    """Frame-facing lifecycle commands for one active signing workspace."""

    def replace(self, command: OpenWorkspaceCommand) -> OpenWorkspaceOutcome:
        """Compose and mount a workspace, replacing the current one atomically."""

    def close(self) -> None:
        """Close the active workspace, if any, without raising for repeated calls."""


@dataclass
class _ActiveWorkspace:
    outcome: OpenWorkspaceOutcome
    widget: Any


class SigningWorkspaceLifecycle:
    """Coordinate composition, mounting, replacement, and widget cleanup.

    The coordinator deliberately does not import Qt. A workspace is composed
    through the existing ``WorkspaceOpenPort`` and installed through the small
    ``WorkspaceMountPort`` adapter, which keeps this state transition usable by
    fake-Qt and headless tests.
    """

    def __init__(
        self,
        *,
        workspace_open_port: WorkspaceOpenPort,
        mount_port: WorkspaceMountPort,
    ) -> None:
        self._workspace_open_port = workspace_open_port
        self._mount_port = mount_port
        self._active: _ActiveWorkspace | None = None

    def replace(self, command: OpenWorkspaceCommand) -> OpenWorkspaceOutcome:
        """Compose and mount a candidate before disposing the old workspace."""

        outcome = self._workspace_open_port.open_workspace(command)
        candidate = outcome.compatibility.shell_widget
        previous = self._active

        try:
            self._mount_port.mount(candidate)
        except Exception:
            self._dispose_widget(candidate)
            raise

        if previous is not None and previous.widget is not candidate:
            self._dispose_widget(previous.widget)
        self._active = _ActiveWorkspace(outcome=outcome, widget=candidate)
        return outcome

    def close(self) -> None:
        """Dispose the active workspace once and clear the active record."""

        active = self._active
        self._active = None
        if active is not None:
            self._dispose_widget(active.widget)

    @staticmethod
    def _dispose_widget(widget: Any) -> None:
        close = getattr(widget, "close", None)
        if callable(close):
            try:
                close()
        except Exception:
            pass
        delete_later = getattr(widget, "deleteLater", None)
        if callable(delete_later):
            try:
                delete_later()
            except Exception:
                pass
