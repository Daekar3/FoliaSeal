"""Atomic replacement and cleanup for one live signing workspace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from foliaseal.presentation.qt.app_frame_workspace_open import (
    OpenWorkspaceCommand,
    WorkspaceHandle,
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

    def replace(self, command: OpenWorkspaceCommand) -> WorkspaceHandle:
        """Compose and mount a workspace, replacing the current one atomically."""

    def prepare(self, command: OpenWorkspaceCommand) -> WorkspaceHandle:
        """Compose a candidate without changing the active mounted workspace."""

    def replace_prepared(self, handle: WorkspaceHandle) -> WorkspaceHandle:
        """Mount a previously prepared candidate and publish it atomically."""

    def close(self) -> None:
        """Close the active workspace, if any, without raising for repeated calls."""


@dataclass
class _ActiveWorkspace:
    handle: WorkspaceHandle


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

    def replace(self, command: OpenWorkspaceCommand) -> WorkspaceHandle:
        """Compose and mount a candidate before disposing the old workspace."""

        return self.replace_prepared(self.prepare(command))

    def prepare(self, command: OpenWorkspaceCommand) -> WorkspaceHandle:
        """Compose a candidate without changing the active mounted workspace."""
        return self._workspace_open_port.open_workspace(command)

    def replace_prepared(self, handle: WorkspaceHandle) -> WorkspaceHandle:
        """Mount a prepared candidate before disposing the old workspace."""
        candidate = handle.view.mount_target()
        previous = self._active

        try:
            self._mount_port.mount(candidate)
        except Exception:
            handle.view.dispose()
            raise

        self._active = _ActiveWorkspace(handle=handle)
        if (
            previous is not None
            and previous.handle.view.mount_target() is not candidate
        ):
            previous.handle.view.dispose()
        return handle

    def active(self) -> WorkspaceHandle | None:
        """Return the published handle, or ``None`` before/after close."""

        return None if self._active is None else self._active.handle

    def close(self) -> None:
        """Dispose the active workspace once and clear the active record."""

        active = self._active
        self._active = None
        if active is not None:
            active.handle.view.dispose()
