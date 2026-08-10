"""Qt-free policy values for app-frame workspace actions."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class WorkspaceActionState:
    """Describe the enabled/checked state of workspace-related frame actions."""

    workspace_open: bool
    save_as_enabled: bool
    text_selection_enabled: bool
    text_selection_checked: bool
    copy_selected_text_enabled: bool
    previous_page_enabled: bool = False
    next_page_enabled: bool = False

    @property
    def save_enabled(self) -> bool:
        """Return whether the active workspace can receive Save."""

        return self.workspace_open

    @property
    def close_enabled(self) -> bool:
        """Return whether the active workspace can be closed."""

        return self.workspace_open


def workspace_action_state_closed() -> WorkspaceActionState:
    """Return the action state shown while the placeholder is mounted."""

    return WorkspaceActionState(
        workspace_open=False,
        save_as_enabled=False,
        text_selection_enabled=False,
        text_selection_checked=False,
        copy_selected_text_enabled=False,
    )


def workspace_action_state_open(
    *,
    previous_page_enabled: bool = False,
    next_page_enabled: bool = False,
) -> WorkspaceActionState:
    """Return the action state shown after a workspace opens successfully."""

    return WorkspaceActionState(
        workspace_open=True,
        save_as_enabled=True,
        text_selection_enabled=True,
        text_selection_checked=False,
        copy_selected_text_enabled=True,
        previous_page_enabled=previous_page_enabled,
        next_page_enabled=next_page_enabled,
    )


def workspace_action_state_with_selection_result(
    state: WorkspaceActionState,
    checked: bool,
) -> WorkspaceActionState:
    """Return ``state`` with only the selection checked flag replaced."""

    return replace(state, text_selection_checked=bool(checked))
