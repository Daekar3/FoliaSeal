"""Registry for enabled and disabled document operations."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.domain.models import DocumentOperation, DocumentOperationType


@dataclass(frozen=True)
class RegisteredOperation:
    """Metadata and handler for a known operation."""

    handler: DocumentOperation
    enabled: bool


class OperationRegistry:
    """Store and query operation capabilities by type."""

    def __init__(self) -> None:
        self._entries: dict[DocumentOperationType, RegisteredOperation] = {}

    def register(self, handler: DocumentOperation, *, enabled: bool) -> None:
        """Register an operation handler and whether it is enabled."""
        self._entries[handler.operation_type] = RegisteredOperation(
            handler=handler,
            enabled=enabled,
        )

    def is_enabled(self, operation_type: DocumentOperationType) -> bool:
        """Return whether the operation is currently enabled."""
        entry = self._entries.get(operation_type)
        return bool(entry and entry.enabled)

    def get(self, operation_type: DocumentOperationType) -> RegisteredOperation:
        """Get operation metadata or raise KeyError if missing."""
        return self._entries[operation_type]

    def all_operations(self) -> dict[DocumentOperationType, RegisteredOperation]:
        """Return a shallow copy of registered operations."""
        return dict(self._entries)
