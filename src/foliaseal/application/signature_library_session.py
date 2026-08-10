"""Document-independent state for the modeless Signature Library surface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.reusable_signing_models import ReusableObjectValidationError
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectRef,
    ReusableObjectSummary,
    ReusableSigningObjects,
)


class LibraryCatalog(StrEnum):
    """Catalogs shown by the Library navigation column."""

    PRESETS = "Presets"
    APPEARANCES = "Appearances"
    PLACEMENTS = "Placements"
    CERTIFICATES = "Certificates"


class LibrarySort(StrEnum):
    """Sort choices shared by the Library session and persisted UI settings."""

    NAME_ASCENDING = "name_ascending"
    NAME_DESCENDING = "name_descending"
    EXPIRATION_SOONEST = "expiration_soonest"


@dataclass(frozen=True)
class SignatureLibraryRow:
    """One searchable, display-ready row in the Library master list."""

    ref: ReusableObjectRef | CertificateLibraryRef
    display_name: str
    details: str
    pinned: bool = False
    configured: bool = False
    expiration: str | None = None


@dataclass(frozen=True)
class CertificateLibraryRef:
    """Stable identity for one user-facing managed certificate entry."""

    object_id: str
    configuration_id: str | None = None


class SignatureLibrarySession:
    """Own selection/search state without owning catalog persistence.

    The service is deliberately injected and remains the only authority that can
    mutate reusable signing objects. This session can therefore be discarded on
    window close without restoring or changing a document draft.
    """

    def __init__(
        self,
        library: ReusableSigningObjects,
        certificate_catalog: CertificateCatalog | None = None,
        initial_catalog: str | LibraryCatalog = LibraryCatalog.PRESETS,
        sort: str | LibrarySort = LibrarySort.NAME_ASCENDING,
    ) -> None:
        self._library = library
        self._certificate_catalog = certificate_catalog
        self._catalog = _catalog_from_value(initial_catalog)
        self._sort = _sort_from_value(sort)
        self._search = ""
        self._selected_ref: ReusableObjectRef | CertificateLibraryRef | None = None
        self._draft_name: str | None = None
        self._original_name: str | None = None

    @property
    def catalog(self) -> LibraryCatalog:
        return self._catalog

    @property
    def search(self) -> str:
        return self._search

    @property
    def sort(self) -> LibrarySort:
        return self._sort

    def set_sort(self, value: str | LibrarySort) -> tuple[SignatureLibraryRow, ...]:
        self._sort = _sort_from_value(value)
        return self.rows()

    @property
    def selected_ref(self) -> ReusableObjectRef | CertificateLibraryRef | None:
        return self._selected_ref

    def select_catalog(self, catalog: LibraryCatalog) -> tuple[SignatureLibraryRow, ...]:
        self._catalog = catalog
        self._selected_ref = None
        self._draft_name = None
        self._original_name = None
        return self.rows()

    def set_search(self, value: str) -> tuple[SignatureLibraryRow, ...]:
        self._search = value.strip()
        return self.rows()

    @property
    def draft_name(self) -> str | None:
        return self._draft_name

    @property
    def detail_dirty(self) -> bool:
        return self._draft_name is not None and self._draft_name != self._original_name

    def refresh(self) -> tuple[SignatureLibraryRow, ...]:
        snapshot = self._library.refresh()
        if self._selected_ref is not None:
            if isinstance(self._selected_ref, CertificateLibraryRef):
                if not any(row.ref == self._selected_ref for row in self.rows()):
                    self._selected_ref = None
            else:
                try:
                    snapshot.resolve(self._selected_ref)
                except ReusableObjectValidationError:
                    self._selected_ref = None
        return self.rows()

    def set_certificate_catalog(self, catalog: CertificateCatalog | None) -> None:
        self._certificate_catalog = catalog

    def rows(self) -> tuple[SignatureLibraryRow, ...]:
        summaries = self._summaries_for_catalog()
        query = self._search.casefold()
        rows = tuple(
            SignatureLibraryRow(
                ref=summary.ref,
                display_name=summary.display_name,
                details=summary.details,
                pinned=summary.pinned,
                configured=getattr(summary, "configured", False),
                expiration=getattr(summary, "expiration", None),
            )
            for summary in summaries
            if not query
            or query in summary.display_name.casefold()
            or query in summary.details.casefold()
        )
        if self._sort is LibrarySort.EXPIRATION_SOONEST:
            name_sorted = sorted(
                rows,
                key=lambda row: (_expiration_key(row.expiration), row.display_name.casefold()),
            )
        else:
            reverse = self._sort is LibrarySort.NAME_DESCENDING
            name_sorted = sorted(rows, key=lambda row: row.display_name.casefold(), reverse=reverse)
        configured_sorted = sorted(name_sorted, key=lambda row: not row.configured)
        return tuple(sorted(configured_sorted, key=lambda row: not row.pinned))

    def select(
        self, ref: ReusableObjectRef | CertificateLibraryRef | None
    ) -> SignatureLibraryRow | None:
        if ref is None:
            self._selected_ref = None
            return None
        row = next((row for row in self.rows() if row.ref == ref), None)
        self._selected_ref = ref if row is not None else None
        self._original_name = None if row is None else row.display_name
        self._draft_name = self._original_name
        return row

    def selected_row(self) -> SignatureLibraryRow | None:
        if self._selected_ref is None:
            return None
        return next((row for row in self.rows() if row.ref == self._selected_ref), None)

    def cancel_detail(self) -> None:
        """Discard the current detail selection/draft without a catalog write."""

        self._selected_ref = None
        self._draft_name = None
        self._original_name = None

    def set_draft_name(self, value: str) -> None:
        if self._selected_ref is not None:
            self._draft_name = value

    def commit_detail(self) -> None:
        """Mark the current draft clean after the caller commits its command."""

        self._original_name = self._draft_name

    def _summaries_for_catalog(self) -> tuple[ReusableObjectSummary, ...]:
        view = self._library.view()
        if self._catalog is LibraryCatalog.PRESETS:
            return view.presets
        if self._catalog is LibraryCatalog.APPEARANCES:
            return view.appearances
        if self._catalog is LibraryCatalog.PLACEMENTS:
            return view.placements
        if self._certificate_catalog is None:
            return ()
        configurations = {
            item.managed_certificate_id: item
            for item in self._certificate_catalog.certificate_configurations
        }
        managed_ids = {
            item.managed_certificate_id
            for item in self._certificate_catalog.managed_certificates
        }
        rows = [
            SignatureLibraryRow(
                ref=CertificateLibraryRef(
                    item.managed_certificate_id,
                    configurations.get(item.managed_certificate_id).certificate_configuration_id
                    if item.managed_certificate_id in configurations
                    else None,
                ),
                display_name=(
                    configurations[item.managed_certificate_id].display_name
                    if item.managed_certificate_id in configurations
                    else item.display_name
                ),
                details=(
                    "Configured signing certificate; "
                    + ("saved password" if configurations[item.managed_certificate_id].save_password
                       else "password prompted at signing")
                    if item.managed_certificate_id in configurations
                    else f"Not configured for signing; certificate file ({item.source_kind}); "
                    f"subject: {item.subject_summary.common_name or 'not supplied'}"
                ),
                pinned=item.pinned
                or (
                    configurations[item.managed_certificate_id].pinned
                    if item.managed_certificate_id in configurations
                    else False
                ),
                configured=item.managed_certificate_id in configurations,
                expiration=item.valid_until,
            )
            for item in self._certificate_catalog.managed_certificates
        ]
        rows.extend(
            SignatureLibraryRow(
                ref=CertificateLibraryRef(
                    item.managed_certificate_id,
                    item.certificate_configuration_id,
                ),
                display_name=item.display_name,
                details="Managed certificate file is unavailable; configure or remove this entry.",
                pinned=item.pinned,
                configured=False,
                expiration=None,
            )
            for item in self._certificate_catalog.certificate_configurations
            if item.managed_certificate_id not in managed_ids
        )
        return tuple(rows)


def _catalog_from_value(value: str | LibraryCatalog) -> LibraryCatalog:
    if isinstance(value, LibraryCatalog):
        return value
    normalized = str(value).strip().casefold()
    return next(
        (catalog for catalog in LibraryCatalog if catalog.value.casefold() == normalized),
        LibraryCatalog.PRESETS,
    )


def _sort_from_value(value: str | LibrarySort) -> LibrarySort:
    if isinstance(value, LibrarySort):
        return value
    try:
        return LibrarySort(str(value).strip().lower())
    except ValueError:
        return LibrarySort.NAME_ASCENDING


def _expiration_key(value: str | None) -> tuple[int, datetime]:
    """Sort known UTC dates first and legacy/invalid values last."""

    if not value:
        return (1, datetime.max.replace(tzinfo=UTC))
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return (0, parsed.astimezone(UTC))
    except (TypeError, ValueError):
        return (1, datetime.max.replace(tzinfo=UTC))


__all__ = [
    "CertificateLibraryRef",
    "LibraryCatalog",
    "LibrarySort",
    "SignatureLibraryRow",
    "SignatureLibrarySession",
]
