"""Undo/redo state for one in-progress visible-signature placement."""

from __future__ import annotations

from foliaseal.domain.models import SignatureRect


class PlacementHistory:
    """Keep a bounded, exact history of placement mutations."""

    def __init__(self, current: SignatureRect | None = None) -> None:
        self._current = current
        self._undo: list[SignatureRect | None] = []
        self._redo: list[SignatureRect | None] = []

    @property
    def current(self) -> SignatureRect | None:
        return self._current

    def synchronize(self, current: SignatureRect | None) -> None:
        """Adopt external state and clear history when it differs."""
        if current != self._current:
            self._undo.clear()
            self._redo.clear()
        self._current = current

    def commit(self, current: SignatureRect | None) -> None:
        """Record one user mutation and invalidate the redo branch."""
        if current == self._current:
            return
        self._undo.append(self._current)
        self._current = current
        self._redo.clear()

    def undo(self) -> SignatureRect | None:
        """Move one step backward, returning the restored value."""
        if not self._undo:
            return self._current
        self._redo.append(self._current)
        self._current = self._undo.pop()
        return self._current

    def redo(self) -> SignatureRect | None:
        """Move one step forward, returning the restored value."""
        if not self._redo:
            return self._current
        self._undo.append(self._current)
        self._current = self._redo.pop()
        return self._current

    def clear(self, *, current: SignatureRect | None = None) -> None:
        """Clear history at a lifecycle boundary while retaining current state."""
        self._undo.clear()
        self._redo.clear()
        self._current = current
