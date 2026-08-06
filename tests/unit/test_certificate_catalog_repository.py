from __future__ import annotations

import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from foliaseal.application.certificate_catalog_repository import (
    CertificateCatalogRepository,
    InMemoryCertificateCatalogRepository,
)
from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
    ManagedCertificate,
    ManagedCertificateSubjectSummary,
)
from foliaseal.domain.errors import ConfigValidationError
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore


def _managed() -> ManagedCertificate:
    return ManagedCertificate(
        schema_version=1,
        managed_certificate_id="managed-1",
        display_name="Example",
        storage_filename="cert_managed-1.p12",
        source_kind="imported",
        created_at="2026-01-01T00:00:00Z",
        subject_summary=ManagedCertificateSubjectSummary(common_name="Example"),
    )


def _configuration() -> CertificateConfiguration:
    return CertificateConfiguration(
        schema_version=1,
        certificate_configuration_id="config-1",
        display_name="Example",
        managed_certificate_id="managed-1",
        save_password=False,
    )


def test_in_memory_repository_supports_application_catalog_operations(tmp_path: Path) -> None:
    repository = InMemoryCertificateCatalogRepository(
        catalog=CertificateCatalog(schema_version=1, managed_certificates=(_managed(),)),
        storage_dir=tmp_path / "Certificates",
    )

    assert isinstance(repository, CertificateCatalogRepository)
    assert repository.storage_dir == tmp_path / "Certificates"
    assert repository.managed_certificate_dir == tmp_path / "Certificates" / "Managed"

    saved = repository.save_configuration(_configuration())
    assert saved.configuration_by_id("config-1").display_name == "Example"
    assert repository.load_catalog() == saved

    managed_path = repository.managed_certificate_dir / _managed().storage_filename
    managed_path.parent.mkdir(parents=True)
    managed_path.write_bytes(b"pkcs12")
    destination = tmp_path / "exported.p12"
    assert repository.export_managed_certificate_by_id("managed-1", destination) == destination
    assert destination.read_bytes() == b"pkcs12"

    removed = repository.delete_configuration_by_id("config-1")
    assert removed.certificate_configurations == ()


def test_real_store_structurally_conforms_to_application_repository(tmp_path: Path) -> None:
    assert isinstance(
        CertificateCatalogStore(storage_dir=tmp_path / "Certificates"),
        CertificateCatalogRepository,
    )


def test_in_memory_managed_file_transaction_tracks_bytes_and_validates_record(
    tmp_path: Path,
) -> None:
    managed = _managed()
    original = CertificateCatalog(schema_version=1, managed_certificates=(managed,))
    repository = InMemoryCertificateCatalogRepository(
        catalog=original,
        storage_dir=tmp_path / "Certificates",
    )

    committed = repository.commit_managed_certificate(
        payload=b"pkcs12",
        managed_certificate=managed,
        catalog=original,
    )
    assert committed.catalog == original
    assert repository._managed_files[managed.storage_filename] == b"pkcs12"
    destination = tmp_path / "backup.p12"
    repository.export_managed_certificate_by_id(managed.managed_certificate_id, destination)
    assert destination.read_bytes() == b"pkcs12"

    updated = original.remove_managed_certificate_by_id(managed.managed_certificate_id)
    mismatched = replace(managed, storage_filename="other.p12")
    with pytest.raises(ConfigValidationError, match="supplied managed certificate"):
        repository.delete_managed_certificate(
            managed_certificate=mismatched,
            original_catalog=original,
            updated_catalog=updated,
        )

    repository.delete_managed_certificate(
        managed_certificate=managed,
        original_catalog=original,
        updated_catalog=updated,
    )
    assert managed.storage_filename not in repository._managed_files


def test_application_certificate_modules_do_not_import_infra_store() -> None:
    script = """
import sys
from foliaseal.application import CertificateSecretStoreError
import foliaseal.application.certificate_catalog_repository
import foliaseal.application.certificate_manager
import foliaseal.application.signature_properties_coordinator
assert CertificateSecretStoreError.__module__ == 'foliaseal.application.certificate_secret_store'
assert 'foliaseal.infra.config.certificate_storage' not in sys.modules
assert 'foliaseal.infra.secret_storage' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
