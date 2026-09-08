"""Typed lifecycle state for one keyboard-driven placement adjustment."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from foliaseal.domain.models import SignatureRect


class PlacementKeyboardAdjustmentStatus(StrEnum):
    """Outcome of a keyboard adjustment session operation."""

    BEGUN = "begun"
    ACCEPTED = "accepted"
    NOOP = "noop"
    FLUSHED = "flushed"
    CANCELED = "canceled"
    CLOSED = "closed"
    IGNORED = "ignored"


@dataclass(frozen=True)
class PlacementKeyboardAdjustmentResult:
    """Immutable result returned by a session lifecycle operation."""

    status: PlacementKeyboardAdjustmentStatus
    start: SignatureRect | None
    current: SignatureRect | None
    key: int | None = None
    modifiers: int = 0

    @property
    def changed(self) -> bool:
        return self.start != self.current


class PlacementKeyboardAdjustmentSession:
    """Own one physical keyboard adjustment batch independently of Qt."""

    def __init__(self) -> None:
        self._start: SignatureRect | None = None
        self._current: SignatureRect | None = None
        self._key: int | None = None
        self._modifiers = 0
        self._active = False

    @property
    def active(self) -> bool:
        return self._active

    @property
    def key(self) -> int | None:
        return self._key

    @property
    def modifiers(self) -> int:
        return self._modifiers

    def begin(
        self,
        initial: SignatureRect | None,
        *,
        key: int,
        modifiers: int,
    ) -> PlacementKeyboardAdjustmentResult:
        if self._active:
            return self._result(PlacementKeyboardAdjustmentStatus.NOOP)
        self._start = initial
        self._current = initial
        self._key = key
        self._modifiers = modifiers
        self._active = True
        return self._result(PlacementKeyboardAdjustmentStatus.BEGUN)

    def accept(
        self,
        current: SignatureRect | None,
    ) -> PlacementKeyboardAdjustmentResult:
        if not self._active:
            return self._result(PlacementKeyboardAdjustmentStatus.IGNORED)
        if current is None or current == self._current:
            return self._result(PlacementKeyboardAdjustmentStatus.NOOP)
        self._current = current
        return self._result(PlacementKeyboardAdjustmentStatus.ACCEPTED)

    def flush(self) -> PlacementKeyboardAdjustmentResult:
        if not self._active:
            return self._result(PlacementKeyboardAdjustmentStatus.IGNORED)
        result = self._result(PlacementKeyboardAdjustmentStatus.FLUSHED)
        self._reset()
        return result

    def release(
        self,
        *,
        key: int,
        modifiers: int,
        auto_repeat: bool,
    ) -> PlacementKeyboardAdjustmentResult:
        """Classify a Qt key release, ignoring synthetic autorepeat releases."""

        if auto_repeat or not self._active:
            return self._result(PlacementKeyboardAdjustmentStatus.IGNORED)
        if key != self._key:
            return self._result(PlacementKeyboardAdjustmentStatus.IGNORED)
        del modifiers  # Release modifiers can differ after a modifier key is released.
        return self.flush()

    def cancel(self) -> PlacementKeyboardAdjustmentResult:
        if not self._active:
            return self._result(PlacementKeyboardAdjustmentStatus.IGNORED)
        result = self._result(PlacementKeyboardAdjustmentStatus.CANCELED)
        self._reset()
        return result

    def close(self) -> PlacementKeyboardAdjustmentResult:
        if not self._active:
            return self._result(PlacementKeyboardAdjustmentStatus.CLOSED)
        result = self._result(PlacementKeyboardAdjustmentStatus.CLOSED)
        self._reset()
        return result

    def _result(
        self, status: PlacementKeyboardAdjustmentStatus
    ) -> PlacementKeyboardAdjustmentResult:
        return PlacementKeyboardAdjustmentResult(
            status=status,
            start=self._start,
            current=self._current,
            key=self._key,
            modifiers=self._modifiers,
        )

    def _reset(self) -> None:
        self._start = None
        self._current = None
        self._key = None
        self._modifiers = 0
        self._active = False
