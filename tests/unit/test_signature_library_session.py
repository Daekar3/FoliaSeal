from __future__ import annotations

from foliaseal.application.certificate_models import (
    CertificateCatalog,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
)
from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
    SaveAppearance,
    SavePreset,
)
from foliaseal.application.signature_library_session import (
    LibraryCatalog,
    SignatureLibrarySession,
)
from tests.support.signing_builders import build_signature_appearance


def _session() -> SignatureLibrarySession:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance(name="Approval", appearance=build_signature_appearance()))
    service.execute(SavePreset(name="Board approval", appearance=build_signature_appearance()))
    return SignatureLibrarySession(service)


def test_session_starts_on_presets_and_projects_searchable_rows() -> None:
    session = _session()

    assert session.catalog is LibraryCatalog.PRESETS
    assert [row.display_name for row in session.rows()] == ["Board approval"]

    session.set_search("BOARD")
    assert [row.display_name for row in session.rows()] == ["Board approval"]
    session.set_search("missing")
    assert session.rows() == ()


def test_session_switches_catalog_and_keeps_selection_typed() -> None:
    session = _session()

    session.select_catalog(LibraryCatalog.APPEARANCES)
    row = session.rows()[0]
    session.select(row.ref)

    assert session.catalog is LibraryCatalog.APPEARANCES
    assert session.selected_ref == row.ref
    assert session.selected_row() == row


def test_session_cancel_clears_detail_selection_without_mutating_catalog() -> None:
    session = _session()
    row = session.rows()[0]
    session.select(row.ref)

    session.cancel_detail()

    assert session.selected_ref is None
    assert [item.display_name for item in session.rows()] == ["Board approval"]


def test_session_tracks_a_dirty_name_draft_and_projects_certificate_catalog() -> None:
    session = SignatureLibrarySession(
        _session()._library,  # noqa: SLF001 - test keeps one service boundary
        CertificateCatalog(
            schema_version=1,
            managed_certificates=(
                ManagedCertificate(
                    schema_version=1,
                    managed_certificate_id="managed-alice",
                    display_name="Alice certificate",
                    storage_filename="alice.p12",
                    source_kind="created",
                    created_at="2026-08-10T00:00:00Z",
                    subject_summary=ManagedCertificateSubjectSummary(common_name="Alice"),
                ),
            ),
        ),
    )

    session.select_catalog(LibraryCatalog.CERTIFICATES)
    row = session.rows()[0]
    session.select(row.ref)
    session.set_draft_name("Renamed locally")

    assert session.detail_dirty is True
    assert session.rows()[0].display_name == "Alice certificate"
    session.set_certificate_catalog(CertificateCatalog(schema_version=1))
    assert session.refresh() == ()
    session.cancel_detail()
    assert session.detail_dirty is False
