import pytest

from foliaseal.application.coordinate_transform import PageBox
from foliaseal.application.placement_editor import PlacementEditorSession, PlacementEditorState
from foliaseal.application.reusable_signing_models import (
    PlacementProfile,
    PlacementProfileRect,
    PlacementProfileSourcePage,
)
from foliaseal.application.signing_draft_contracts import SignaturePlacementContext
from foliaseal.domain.models import SignatureRect


def _state() -> PlacementEditorState:
    return PlacementEditorState(
        display_name="Approval",
        page_number=3,
        source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
        rect=PlacementProfileRect(left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0),
    )


def test_save_commits_only_the_editor_draft_as_v2_profile() -> None:
    session = PlacementEditorSession(_state())
    session.update(
        display_name="  Board approval  ",
        rect=PlacementProfileRect(left_pt=24.0, top_pt=700.0, width_pt=180.0, height_pt=54.0),
    )

    profile = session.save()

    assert profile.schema_version == 2
    assert profile.display_name == "Board approval"
    assert profile.page_number == 3
    assert profile.rect.left_pt == 24.0
    assert profile.to_dict()["source_page"] == {
        "visible_width_pt": 612.0,
        "visible_height_pt": 792.0,
        "rotation_degrees": 0,
    }
    assert session.closed


def test_cancel_discards_changes_without_mutating_initial_profile() -> None:
    original = PlacementProfile(
        schema_version=2,
        placement_profile_id="placement-approval",
        display_name="Approval",
        pinned=False,
        page_number=3,
        source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
        rect=PlacementProfileRect(left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0),
    )
    session = PlacementEditorSession(PlacementEditorState.from_profile(original))
    session.update(page_number=4, display_name="Changed")

    session.cancel()

    assert session.closed
    assert session.draft == PlacementEditorState.from_profile(original)
    with pytest.raises(RuntimeError, match="already closed"):
        session.save()


def test_save_rejects_blank_name_without_closing_transaction() -> None:
    session = PlacementEditorSession(_state())
    session.update(display_name=" ")

    with pytest.raises(ValueError, match="name is required"):
        session.save()

    assert not session.closed


def test_current_pdf_seed_converts_pdf_bottom_left_to_visible_top_left() -> None:
    state = PlacementEditorState.from_current_page(
        context=SignaturePlacementContext(
            page_index=2,
            page_box=PageBox(left=0, bottom=0, right=612, top=792),
            rotation=0,
        ),
        signature_rect=SignatureRect(
            page_index=2,
            left_pt=360.0,
            bottom_pt=72.0,
            width_pt=180.0,
            height_pt=54.0,
        ),
    )

    assert state.page_number == 3
    assert state.rect == PlacementProfileRect(
        left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0
    )


def test_blank_page_seed_is_document_independent() -> None:
    state = PlacementEditorState.from_blank_page(
        visible_width_pt=612.0,
        visible_height_pt=792.0,
        page_number=1,
    )

    assert state.source_page.to_dict() == {
        "visible_width_pt": 612.0,
        "visible_height_pt": 792.0,
        "rotation_degrees": 0,
    }
    assert state.rect.width_pt == 180.0
    assert state.rect.height_pt == 54.0
