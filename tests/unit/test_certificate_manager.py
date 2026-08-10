from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application import (
    CertificateCatalog,
    CertificateManager,
    CertificateManagerError,
    ConfigureCertificateRequest,
    CreateCertificateRequest,
    ExportCertificateRequest,
    ImportCertificateRequest,
    SaveConfigurationRequest,
)
from foliaseal.application.certificate_catalog_repository import ManagedCertificateCommit
from foliaseal.domain.errors import ConfigValidationError
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from tests.support.signing_builders import (
    build_certificate_catalog,
)


class FakeSecretStore:
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.values: dict[str, str] = {}

    def is_available(self) -> bool:
        return self.available

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        return f"secret://test/{configuration_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        self.values[secret_ref] = secret

    def get_secret(self, secret_ref: str) -> str | None:
        return self.values.get(secret_ref)

    def delete_secret(self, secret_ref: str) -> None:
        self.values.pop(secret_ref, None)


class _FailAfterDeleteSecretStore(FakeSecretStore):
    def delete_secret(self, secret_ref: str) -> None:
        super().delete_secret(secret_ref)
        raise RuntimeError("secret delete failed after side effect")


def _manager(
    store: CertificateCatalogStore,
    *,
    secret_store: FakeSecretStore | None = None,
    ids: tuple[str, ...] = ("managed-cert-one", "cert-config-one"),
    referenced_configuration_ids=None,
) -> CertificateManager:
    id_values = iter(ids)
    return CertificateManager(
        store=store,
        secret_store=secret_store,
        id_factory=lambda: next(id_values),
        clock=lambda: datetime(2026, 5, 13, 12, 0, tzinfo=UTC),
        referenced_configuration_ids=referenced_configuration_ids,
    )


class _NoPathRepository:
    """Application fake proving the manager never composes repository paths."""

    def __init__(self, catalog: CertificateCatalog) -> None:
        self.catalog = catalog
        self.commit_calls = []
        self.delete_calls = []

    def load_catalog(self) -> CertificateCatalog:
        return self.catalog

    def save_catalog(self, catalog: CertificateCatalog) -> None:
        self.catalog = catalog

    def save_configuration(self, configuration):
        self.catalog = self.catalog.upsert_configuration(configuration)
        return self.catalog

    def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog:
        self.catalog = self.catalog.remove_configuration_by_id(configuration_id)
        return self.catalog

    def export_managed_certificate_by_id(self, certificate_id: str, destination_path):
        raise AssertionError("export is not part of this boundary test")

    def commit_managed_certificate(self, **kwargs) -> ManagedCertificateCommit:
        self.commit_calls.append(kwargs)
        self.catalog = kwargs["catalog"]
        return ManagedCertificateCommit(
            catalog=self.catalog,
            managed_file_path=Path("/virtual/managed.p12"),
        )

    def delete_managed_certificate(self, **kwargs) -> None:
        self.delete_calls.append(kwargs)
        self.catalog = kwargs["updated_catalog"]


def _write_pkcs12(path: Path, *, passphrase: str, common_name: str) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    path.write_bytes(
        pkcs12.serialize_key_and_certificates(
            name=common_name.encode(),
            key=key,
            cert=certificate,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(
                passphrase.encode()
            ),
        )
    )


def test_manager_create_and_import_return_typed_operations(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    manager = _manager(store, ids=("managed-created", "config-created"))

    created = manager.create(CreateCertificateRequest("Alice Signing", "secret"))

    assert created.operation == "created"
    assert created.certificate_configuration is not None
    assert created.certificate_configuration.display_name == "Alice Signing"
    assert created.managed_file_path is not None and created.managed_file_path.exists()

    source = tmp_path / "source.p12"
    _write_pkcs12(source, passphrase="secret", common_name="Alice Imported")
    imported = _manager(
        store,
        ids=("managed-imported", "config-imported"),
    ).import_(ImportCertificateRequest(source, "Alice Imported", "secret"))

    assert imported.operation == "imported"
    assert imported.managed_certificate is not None
    assert imported.managed_certificate.subject_summary.common_name == "Alice Imported"


def test_manager_create_uses_five_year_identity_fields_and_confirmation(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    manager = _manager(store, ids=("managed-created", "config-created"))

    result = manager.create(
        CreateCertificateRequest(
            display_name="Alice Signing",
            passphrase="secret",
            passphrase_confirmation="secret",
            common_name="Alice Example",
            email="alice@example.test",
            title="Board Secretary",
            organization="Example Org",
        )
    )

    assert result.managed_file_path is not None
    key, certificate, _ = pkcs12.load_key_and_certificates(
        result.managed_file_path.read_bytes(), b"secret"
    )
    assert key is not None
    assert certificate is not None
    assert certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == (
        "Alice Example"
    )
    assert certificate.subject.get_attributes_for_oid(NameOID.EMAIL_ADDRESS)[0].value == (
        "alice@example.test"
    )
    assert certificate.subject.get_attributes_for_oid(NameOID.TITLE)[0].value == (
        "Board Secretary"
    )
    assert certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value == (
        "Example Org"
    )
    assert certificate.not_valid_after_utc.year == 2031


def test_manager_create_rejects_mismatched_confirmation(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    manager = _manager(store)

    with pytest.raises(ValueError, match="passwords do not match"):
        manager.create(
            CreateCertificateRequest(
                display_name="Alice Signing",
                passphrase="secret",
                passphrase_confirmation="different",
            )
        )


def test_manager_inspects_import_without_mutating_catalog(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    source = tmp_path / "alice.p12"
    _write_pkcs12(source, passphrase="secret", common_name="Alice Imported")
    manager = _manager(store)

    inspection = manager.inspect_import(source, "secret")

    assert inspection.subject == "CN=Alice Imported"
    assert inspection.issuer == "CN=Alice Imported"
    assert inspection.private_key_present is True
    assert inspection.self_signed is True
    assert any("created locally" in warning for warning in inspection.warnings)
    assert store.load_catalog().managed_certificates == ()
    assert not store.managed_certificate_dir.exists()


def test_manager_configures_retained_managed_certificate(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog(certificate_configurations=()))
    manager = _manager(store, ids=("config-retained",))

    result = manager.configure_managed_certificate(
        ConfigureCertificateRequest(
            managed_certificate_id="managed-cert-default",
            display_name="Retained signing",
        )
    )

    assert result.operation == "configuration_created"
    assert result.certificate_configuration is not None
    assert result.certificate_configuration.managed_certificate_id == "managed-cert-default"
    assert store.load_catalog().configuration_named("Retained signing")


def test_manager_uses_atomic_repository_verb_without_path_properties() -> None:
    repository = _NoPathRepository(CertificateCatalog(schema_version=1))
    manager = CertificateManager(
        store=repository,
        id_factory=iter(("managed-fake", "config-fake")).__next__,
        clock=lambda: datetime(2026, 5, 13, 12, 0, tzinfo=UTC),
    )

    result = manager.create(CreateCertificateRequest("Fake Boundary", "secret"))

    assert result.operation == "created"
    assert len(repository.commit_calls) == 1
    assert not hasattr(repository, "managed_certificate_dir")


def test_manager_removes_saved_secret_when_repository_commit_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _NoPathRepository(CertificateCatalog(schema_version=1))
    secret_store = FakeSecretStore()
    manager = CertificateManager(
        store=repository,
        secret_store=secret_store,
        id_factory=iter(("managed-fake", "config-fake")).__next__,
        clock=lambda: datetime(2026, 5, 13, 12, 0, tzinfo=UTC),
    )

    def fail_commit(**kwargs):
        raise OSError("catalog write failed")

    monkeypatch.setattr(repository, "commit_managed_certificate", fail_commit)

    with pytest.raises(OSError, match="catalog write failed"):
        manager.create(CreateCertificateRequest("Fake Boundary", "secret", save_password=True))

    assert secret_store.values == {}


def test_manager_restores_secret_when_delete_reports_failure_after_side_effect(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    catalog = build_certificate_catalog()
    configuration = replace(
        catalog.certificate_configurations[0],
        save_password=True,
        password_secret_ref="secret://test/config-default",
    )
    catalog = replace(catalog, certificate_configurations=(configuration,))
    store.save_catalog(catalog)
    secret_store = _FailAfterDeleteSecretStore()
    secret_ref = catalog.certificate_configurations[0].password_secret_ref
    assert secret_ref is not None
    secret_store.values[secret_ref] = "secret"

    with pytest.raises(CertificateManagerError, match="saved password was restored"):
        _manager(store, secret_store=secret_store).delete_configuration(
            catalog.certificate_configurations[0].certificate_configuration_id
        )

    assert secret_store.values[secret_ref] == "secret"


def test_manager_save_and_delete_configuration_preserves_managed_certificate(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    manager = _manager(store)

    saved = manager.save_configuration(
        SaveConfigurationRequest("cert-config-default", "Board Signing", "Board packets")
    )
    assert saved.operation == "configuration_saved"
    deleted = manager.delete_configuration("cert-config-default")

    assert deleted.operation == "configuration_deleted"
    catalog = manager.snapshot()
    assert catalog.certificate_configurations == ()
    assert catalog.managed_certificates


def test_manager_save_configuration_preserves_and_explicitly_disables_password(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    secret_store = FakeSecretStore()
    store.save_catalog(build_certificate_catalog())
    configuration = store.load_catalog().certificate_configurations[0]
    secret_ref = "secret://test/cert-config-default"
    secret_store.values[secret_ref] = "secret"
    store.save_catalog(
        replace(
            store.load_catalog(),
            certificate_configurations=(
                replace(configuration, save_password=True, password_secret_ref=secret_ref),
            ),
        )
    )
    manager = _manager(store, secret_store=secret_store)

    preserved = manager.save_configuration(
        SaveConfigurationRequest("cert-config-default", "Renamed Signing", "Notes")
    )
    assert preserved.certificate_configuration is not None
    assert preserved.certificate_configuration.save_password is True
    assert secret_store.values[secret_ref] == "secret"

    disabled = manager.save_configuration(
        SaveConfigurationRequest(
            "cert-config-default",
            "Renamed Signing",
            "Notes",
            save_password=False,
        )
    )
    assert disabled.certificate_configuration is not None
    assert disabled.certificate_configuration.save_password is False
    assert secret_ref not in secret_store.values


def test_manager_export_validates_supplied_password_without_mutating_state(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    manager = _manager(store, ids=("managed-created", "config-created"))
    created = manager.create(CreateCertificateRequest("Alice Signing", "secret"))
    assert created.managed_certificate is not None
    destination = tmp_path / "backup" / "alice.p12"

    with pytest.raises(ValueError, match="password"):
        manager.export(
            ExportCertificateRequest(
                created.managed_certificate.managed_certificate_id,
                destination,
                passphrase="wrong",
            )
        )
    exported = manager.export(
        ExportCertificateRequest(
            created.managed_certificate.managed_certificate_id,
            destination,
            passphrase="secret",
        )
    )
    assert exported.exported_path == destination
    assert manager.snapshot() == created.catalog


def test_manager_blocks_deleting_configuration_referenced_by_preset(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    manager = _manager(
        store,
        referenced_configuration_ids=lambda: {"cert-config-default"},
    )

    with pytest.raises(ConfigValidationError, match="referenced by a signature preset"):
        manager.delete_configuration("cert-config-default")

    assert manager.snapshot().configuration_by_id("cert-config-default")


def test_manager_delete_managed_certificate_restores_state_when_unlink_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog(certificate_configurations=()))
    managed_path = store.managed_certificate_dir / "cert_default.p12"
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_bytes(b"certificate")
    original_unlink = Path.unlink

    def fail_staged_unlink(path: Path, *args: object, **kwargs: object) -> None:
        if path.name.endswith(".deleting"):
            raise OSError("unlink failed")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_staged_unlink)
    with pytest.raises(OSError, match="unlink failed"):
        _manager(store).delete_managed_certificate("managed-cert-default")

    assert managed_path.read_bytes() == b"certificate"
    assert store.load_catalog().managed_certificate_by_id("managed-cert-default")


def test_manager_export_preserves_catalog_and_enforces_store_boundary(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())
    managed_path = store.managed_certificate_dir / "cert_default.p12"
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_bytes(b"certificate")
    manager = _manager(store)

    destination = tmp_path / "backup" / "certificate.p12"
    result = manager.export(ExportCertificateRequest("managed-cert-default", destination))

    assert result.operation == "exported"
    assert result.exported_path == destination
    assert destination.read_bytes() == b"certificate"
    with pytest.raises(ValueError):
        manager.export(
            ExportCertificateRequest(
                "managed-cert-default",
                store.managed_certificate_dir / "forbidden.p12",
            )
        )
