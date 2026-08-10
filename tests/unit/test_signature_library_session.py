from __future__ import annotations

from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
)
from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
    SaveAppearance,
    SavePreset,
    SetPinned,
)
from foliaseal.application.signature_library_session import (
    LibraryCatalog,
    LibrarySort,
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


def test_session_keeps_pinned_rows_first_in_both_name_orders() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance(name="Zulu", appearance=build_signature_appearance()))
    service.execute(SaveAppearance(name="Alpha", appearance=build_signature_appearance()))
    alpha = service.view().appearances[0].ref
    service.execute(SetPinned(ref=alpha, pinned=True))
    session = SignatureLibrarySession(
        service, initial_catalog=LibraryCatalog.APPEARANCES, sort=LibrarySort.NAME_DESCENDING
    )

    assert [row.display_name for row in session.rows()] == ["Zulu", "Alpha"]
    session.set_sort(LibrarySort.NAME_ASCENDING)
    assert [row.display_name for row in session.rows()] == ["Zulu", "Alpha"]


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


def test_certificate_catalog_projects_one_combined_entry_and_unconfigured_files() -> None:
    session = SignatureLibrarySession(
        _session()._library,  # noqa: SLF001 - test keeps one service boundary
        CertificateCatalog(
            schema_version=1,
            managed_certificates=(
                ManagedCertificate(
                    schema_version=1,
                    managed_certificate_id="managed-configured",
                    display_name="File name",
                    storage_filename="configured.p12",
                    source_kind="created",
                    created_at="2026-08-10T00:00:00Z",
                    subject_summary=ManagedCertificateSubjectSummary(common_name="Alice"),
                ),
                ManagedCertificate(
                    schema_version=1,
                    managed_certificate_id="managed-unconfigured",
                    display_name="Alpha unconfigured",
                    storage_filename="unconfigured.p12",
                    source_kind="imported",
                    created_at="2026-08-10T00:00:00Z",
                    subject_summary=ManagedCertificateSubjectSummary(common_name="Bob"),
                ),
            ),
            certificate_configurations=(
                CertificateConfiguration(
                    schema_version=1,
                    certificate_configuration_id="config-alice",
                    display_name="Zulu signing",
                    managed_certificate_id="managed-configured",
                    save_password=False,
                ),
            ),
        ),
    )
    session.select_catalog(LibraryCatalog.CERTIFICATES)

    rows = session.rows()
    assert len(rows) == 2
    configured = next(row for row in rows if row.ref.object_id == "managed-configured")
    unconfigured = next(row for row in rows if row.ref.object_id == "managed-unconfigured")
    assert configured.display_name == "Zulu signing"
    assert configured.ref.configuration_id == "config-alice"
    assert unconfigured.display_name == "Alpha unconfigured"
    assert "Not configured" in unconfigured.details
    assert rows[0].ref.object_id == "managed-configured"


def test_certificate_catalog_keeps_pinned_retained_rows_before_unpinned_configured_rows() -> None:
    retained = ManagedCertificate(
        schema_version=1,
        managed_certificate_id="managed-retained",
        display_name="Retained certificate",
        storage_filename="retained.p12",
        source_kind="imported",
        created_at="2026-08-10T00:00:00Z",
        pinned=True,
        subject_summary=ManagedCertificateSubjectSummary(common_name="Retained"),
    )
    configured = ManagedCertificate(
        schema_version=1,
        managed_certificate_id="managed-configured",
        display_name="Configured certificate",
        storage_filename="configured.p12",
        source_kind="created",
        created_at="2026-08-10T00:00:00Z",
        subject_summary=ManagedCertificateSubjectSummary(common_name="Configured"),
    )
    session = SignatureLibrarySession(
        _session()._library,  # noqa: SLF001 - test keeps one service boundary
        CertificateCatalog(
            schema_version=1,
            managed_certificates=(configured, retained),
            certificate_configurations=(
                CertificateConfiguration(
                    schema_version=1,
                    certificate_configuration_id="config-configured",
                    display_name="Configured signing",
                    managed_certificate_id="managed-configured",
                    save_password=False,
                ),
            ),
        ),
        initial_catalog=LibraryCatalog.CERTIFICATES,
    )

    rows = session.rows()

    assert rows[0].ref.object_id == "managed-retained"
    assert rows[0].pinned is True
    assert rows[1].configured is True


def test_certificate_catalog_expiration_sort_puts_known_dates_first_and_unknown_last() -> None:
    session = SignatureLibrarySession(
        _session()._library,  # noqa: SLF001 - test keeps one service boundary
        CertificateCatalog(
            schema_version=1,
            managed_certificates=(
                ManagedCertificate(
                    schema_version=1,
                    managed_certificate_id="managed-later",
                    display_name="Later",
                    storage_filename="later.p12",
                    source_kind="imported",
                    created_at="2026-01-01T00:00:00Z",
                    subject_summary=ManagedCertificateSubjectSummary(common_name="Later"),
                    valid_until="2027-06-01T00:00:00Z",
                ),
                ManagedCertificate(
                    schema_version=1,
                    managed_certificate_id="managed-sooner",
                    display_name="Sooner",
                    storage_filename="sooner.p12",
                    source_kind="imported",
                    created_at="2026-01-01T00:00:00Z",
                    subject_summary=ManagedCertificateSubjectSummary(common_name="Sooner"),
                    valid_until="2026-09-01T00:00:00Z",
                ),
                ManagedCertificate(
                    schema_version=1,
                    managed_certificate_id="managed-legacy",
                    display_name="Legacy",
                    storage_filename="legacy.p12",
                    source_kind="imported",
                    created_at="2026-01-01T00:00:00Z",
                    subject_summary=ManagedCertificateSubjectSummary(common_name="Legacy"),
                    valid_until="not-a-date",
                ),
            ),
        ),
        initial_catalog=LibraryCatalog.CERTIFICATES,
        sort=LibrarySort.EXPIRATION_SOONEST,
    )

    assert [row.display_name for row in session.rows()] == ["Sooner", "Later", "Legacy"]
    assert session.rows()[-1].expiration == "not-a-date"
