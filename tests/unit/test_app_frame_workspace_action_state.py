import os
import subprocess
import sys
from pathlib import Path

import pytest

from foliaseal.presentation.qt.app_frame_workspace_action_state import (
    WorkspaceActionState,
    workspace_action_state_closed,
    workspace_action_state_open,
    workspace_action_state_with_selection_result,
)


def test_closed_state_disables_all_workspace_actions() -> None:
    assert workspace_action_state_closed() == WorkspaceActionState(
        False,
        False,
        False,
        False,
        False,
    )


def test_open_state_enables_actions_and_starts_unchecked() -> None:
    assert workspace_action_state_open() == WorkspaceActionState(True, True, True, False, True)


def test_selection_result_is_immutable_and_changes_only_checked_flag() -> None:
    state = workspace_action_state_open()
    selected = workspace_action_state_with_selection_result(state, True)

    assert selected == WorkspaceActionState(True, True, True, True, True)
    assert state.text_selection_checked is False
    with pytest.raises(Exception):
        state.text_selection_checked = True


def test_projection_module_has_no_heavy_gui_or_filesystem_imports() -> None:
    script = """
import sys
import foliaseal.presentation.qt.app_frame_workspace_action_state
blocked = ('PyQt', 'PySide6', 'PIL', 'pyhanko', 'foliaseal.infra')
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
)
assert not loaded, loaded
"""
    source_root = str(Path(__file__).resolve().parents[2] / "src")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (source_root, environment.get("PYTHONPATH", ""))
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
