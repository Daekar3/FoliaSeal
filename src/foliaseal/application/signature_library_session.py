"""Document-independent state for the modeless Signature Library surface."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SignatureLibraryRow:
    """One searchable, display-ready row in the Library master list."""

    ref: ReusableObjectRef | CertificateLibraryRef
    display_name: str
    details: str


@dataclass(frozen=True)
class CertificateLibraryRef:
    """Stable identity for a managed certificate or its signing configuration."""

    object_id: str
    is_configuration: bool = False


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
    ) -> None:
        self._library = library
        self._certificate_catalog = certificate_catalog
        self._catalog = LibraryCatalog.PRESETS
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
            )
            for summary in summaries
            if not query
            or query in summary.display_name.casefold()
            or query in summary.details.casefold()
        )
        return tuple(sorted(rows, key=lambda row: row.display_name.casefold()))

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
        managed = tuple(
            SignatureLibraryRow(
                ref=CertificateLibraryRef(item.managed_certificate_id),
                display_name=item.display_name,
                details=(
                    f"Certificate file ({item.source_kind}); "
                    f"subject: {item.subject_summary.common_name or 'not supplied'}"
                ),
            )
            for item in self._certificate_catalog.managed_certificates
        )
        configurations = tuple(
            SignatureLibraryRow(
                ref=CertificateLibraryRef(item.certificate_configuration_id, True),
                display_name=item.display_name,
                details=(
                    "Signing configuration; "
                    + ("saved password" if item.save_password else "password prompted at signing")
                ),
            )
            for item in self._certificate_catalog.certificate_configurations
        )
        return managed + configurations


__all__ = [
    "CertificateLibraryRef",
    "LibraryCatalog",
    "SignatureLibraryRow",
    "SignatureLibrarySession",
]
