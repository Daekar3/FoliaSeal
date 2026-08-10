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
    copy_enabled: bool = False
    undo_placement_enabled: bool = False
    redo_placement_enabled: bool = False
    cut_enabled: bool = False
    paste_enabled: bool = False
    select_all_enabled: bool = False
    previous_page_enabled: bool = False
    next_page_enabled: bool = False
    back_link_enabled: bool = False
    forward_link_enabled: bool = False

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
    undo_placement_enabled: bool = False,
    redo_placement_enabled: bool = False,
    previous_page_enabled: bool = False,
    next_page_enabled: bool = False,
    back_link_enabled: bool = False,
    forward_link_enabled: bool = False,
) -> WorkspaceActionState:
    """Return the action state shown after a workspace opens successfully."""

    return WorkspaceActionState(
        workspace_open=True,
        save_as_enabled=True,
        text_selection_enabled=True,
        text_selection_checked=False,
        copy_selected_text_enabled=False,
        undo_placement_enabled=undo_placement_enabled,
        redo_placement_enabled=redo_placement_enabled,
        previous_page_enabled=previous_page_enabled,
        next_page_enabled=next_page_enabled,
        back_link_enabled=back_link_enabled,
        forward_link_enabled=forward_link_enabled,
    )


def workspace_action_state_with_selection_result(
    state: WorkspaceActionState,
    checked: bool,
) -> WorkspaceActionState:
    """Return ``state`` with only the selection checked flag replaced."""

    return replace(state, text_selection_checked=bool(checked))


def workspace_action_state_with_document_text_result(
    state: WorkspaceActionState,
    *,
    selection_mode_enabled: bool,
    can_copy_selected_text: bool,
) -> WorkspaceActionState:
    """Project current document-text mode and selection capability onto frame actions."""
    return replace(
        state,
        text_selection_checked=bool(selection_mode_enabled),
        copy_selected_text_enabled=bool(can_copy_selected_text),
        copy_enabled=bool(can_copy_selected_text),
    )


def workspace_action_state_with_native_edit_result(
    state: WorkspaceActionState,
    *,
    copy_enabled: bool,
    cut_enabled: bool,
    paste_enabled: bool,
    select_all_enabled: bool,
) -> WorkspaceActionState:
    """Project focused-native-editor capabilities onto Edit actions."""

    return replace(
        state,
        copy_enabled=bool(copy_enabled),
        cut_enabled=bool(cut_enabled),
        paste_enabled=bool(paste_enabled),
        select_all_enabled=bool(select_all_enabled),
    )
