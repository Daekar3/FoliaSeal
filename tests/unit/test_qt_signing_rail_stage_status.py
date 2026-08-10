"""Focused tests for the fixed signing rail and protected status region."""

from foliaseal.presentation.qt.signing_action_coordinator import SigningActionState
from foliaseal.presentation.qt.signing_workspace_sidebar import SigningWorkspaceSidebar
from tests.unit.test_signing_workspace_sidebar import _build_sidebar


def _state(*, recommended_action=None, can_sign=False, can_open=False):
    return SigningActionState(
        can_sign=can_sign,
        stage_text="Step 5 of 6 — Confirm and sign",
        detail_text="Review the output and continue.",
        result_text="",
        result_kind="neutral",
        last_signing_result=None,
        last_successful_output_path=None,
        can_open_signed_output=can_open,
        recommended_action=recommended_action,
    )


def test_sidebar_uses_fixed_rail_and_protected_status_region() -> None:
    sidebar = _build_sidebar()

    assert sidebar.container.fixed_width == SigningWorkspaceSidebar.RAIL_WIDTH
    assert (
        sidebar.status_region.minimum_height
        == SigningWorkspaceSidebar.STATUS_REGION_MINIMUM_HEIGHT
    )
    assert sidebar.signing_action_controls.container.parent is sidebar.status_region


def test_sidebar_marks_at_most_one_recommended_primary_action() -> None:
    sidebar = _build_sidebar()

    sidebar.render_signing_action_state(_state(can_sign=True, recommended_action="sign"))
    assert sidebar.sign_button.property("foliasealPrimaryAction") is True
    assert sidebar.open_signed_output_button.property("foliasealPrimaryAction") is False

    sidebar.render_signing_action_state(
        _state(can_open=True, recommended_action="open_signed_output")
    )
    assert sidebar.sign_button.property("foliasealPrimaryAction") is False
    assert sidebar.open_signed_output_button.property("foliasealPrimaryAction") is True

    sidebar.render_signing_action_state(_state())
    assert sidebar.sign_button.property("foliasealPrimaryAction") is False
    assert sidebar.open_signed_output_button.property("foliasealPrimaryAction") is False
