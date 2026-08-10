from foliaseal.application.placement_history import PlacementHistory
from foliaseal.domain.models import SignatureRect


def _rect(left: float) -> SignatureRect:
    return SignatureRect(page_index=0, left_pt=left, bottom_pt=10, width_pt=20, height_pt=10)


def test_placement_history_undo_redo_and_branch_invalidation() -> None:
    first = _rect(1)
    second = _rect(2)
    third = _rect(3)
    history = PlacementHistory()

    history.commit(first)
    history.commit(second)
    assert history.undo() == first
    assert history.redo() == second
    assert history.undo() == first
    history.commit(third)

    assert history.redo() == third


def test_placement_history_synchronization_clears_external_state() -> None:
    history = PlacementHistory(_rect(1))
    history.commit(_rect(2))

    history.synchronize(_rect(9))

    assert history.undo() == _rect(9)
