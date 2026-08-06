from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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


def test_application_certificate_modules_do_not_import_infra_store() -> None:
    script = """
import sys
import foliaseal.application.certificate_catalog_repository
import foliaseal.application.certificate_manager
import foliaseal.application.signature_properties_coordinator
assert 'foliaseal.infra.config.certificate_storage' not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
