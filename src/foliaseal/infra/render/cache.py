"""Render cache policy primitives for Phase 2 viewer performance."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from foliaseal.infra.render.base import RenderPageResult


@dataclass(frozen=True)
class RenderCacheKey:
    """Identity for one rendered page variant."""

    document_path: str
    page_index: int
    zoom: float


class RenderCachePolicy:
    """Small in-memory LRU cache for rendered page buffers."""

    def __init__(self, *, max_entries: int = 16) -> None:
        if max_entries <= 0:
            raise ValueError("max_entries must be greater than zero.")
        self._max_entries = max_entries
        self._entries: OrderedDict[RenderCacheKey, RenderPageResult] = OrderedDict()

    @property
    def max_entries(self) -> int:
        return self._max_entries

    @property
    def size(self) -> int:
        return len(self._entries)

    def get(self, key: RenderCacheKey) -> RenderPageResult | None:
        result = self._entries.get(key)
        if result is None:
            return None
        self._entries.move_to_end(key)
        return result

    def put(self, key: RenderCacheKey, value: RenderPageResult) -> None:
        self._entries[key] = value
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()

    def clear_document(self, document_path: str) -> None:
        keys_to_drop = [key for key in self._entries if key.document_path == document_path]
        for key in keys_to_drop:
            self._entries.pop(key, None)
