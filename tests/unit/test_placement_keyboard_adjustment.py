from foliaseal.application.placement_keyboard_adjustment import (
    PlacementKeyboardAdjustmentSession,
    PlacementKeyboardAdjustmentStatus,
)
from foliaseal.domain.models import SignatureRect


def test_keyboard_adjustment_session_accepts_and_flushes_one_batch() -> None:
    start = SignatureRect(0, 10, 20, 30, 10)
    current = SignatureRect(0, 11, 20, 30, 10)
    session = PlacementKeyboardAdjustmentSession()

    assert (
        session.begin(start, key=1, modifiers=2).status
        is PlacementKeyboardAdjustmentStatus.BEGUN
    )
    assert session.accept(current).status is PlacementKeyboardAdjustmentStatus.ACCEPTED
    result = session.flush()

    assert result.status is PlacementKeyboardAdjustmentStatus.FLUSHED
    assert result.start == start
    assert result.current == current
    assert result.changed is True
    assert session.active is False


def test_keyboard_adjustment_session_noop_cancel_and_close_are_typed() -> None:
    start = SignatureRect(0, 10, 20, 30, 10)
    session = PlacementKeyboardAdjustmentSession()

    assert session.accept(start).status is PlacementKeyboardAdjustmentStatus.IGNORED
    session.begin(start, key=1, modifiers=0)
    assert session.accept(start).status is PlacementKeyboardAdjustmentStatus.NOOP
    canceled = session.cancel()
    assert canceled.status is PlacementKeyboardAdjustmentStatus.CANCELED
    assert canceled.current == start
    assert session.flush().status is PlacementKeyboardAdjustmentStatus.IGNORED
    session.begin(start, key=1, modifiers=0)
    closed = session.close()
    assert closed.status is PlacementKeyboardAdjustmentStatus.CLOSED
    assert closed.current == start


def test_keyboard_adjustment_session_marks_synthetic_release_ignored() -> None:
    start = SignatureRect(0, 10, 20, 30, 10)
    session = PlacementKeyboardAdjustmentSession()
    session.begin(start, key=1, modifiers=2)

    synthetic = session.release(key=1, modifiers=2, auto_repeat=True)
    assert synthetic.status is PlacementKeyboardAdjustmentStatus.IGNORED
    assert session.active is True

    physical = session.release(key=1, modifiers=2, auto_repeat=False)
    assert physical.status is PlacementKeyboardAdjustmentStatus.FLUSHED
    assert session.active is False
