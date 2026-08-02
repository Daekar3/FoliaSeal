from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application import (
    CertificateManager,
    CreateCertificateRequest,
    ExportCertificateRequest,
    ImportCertificateRequest,
    SaveConfigurationRequest,
)
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


def _manager(
    store: CertificateCatalogStore,
    *,
    secret_store: FakeSecretStore | None = None,
    ids: tuple[str, ...] = ("managed-cert-one", "cert-config-one"),
) -> CertificateManager:
    id_values = iter(ids)
    return CertificateManager(
        store=store,
        secret_store=secret_store,
        id_factory=lambda: next(id_values),
        clock=lambda: datetime(2026, 5, 13, 12, 0, tzinfo=UTC),
    )


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
