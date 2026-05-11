from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from foliaseal.application.certificate_import import (
    CertificateImportError,
    CertificateImportService,
)
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import CertificateCatalog, ConfigValidationError


def _write_test_pkcs12(
    path: Path,
    *,
    passphrase: str | None,
    common_name: str = "Alice Example",
) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FoliaSeal"),
            x509.NameAttribute(NameOID.TITLE, "Board Secretary"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "QA"),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, "alice@example.com"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Wytheville"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Virginia"),
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        ]
    )
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
            name=common_name.encode("utf-8"),
            key=key,
            cert=certificate,
            cas=None,
            encryption_algorithm=(
                serialization.BestAvailableEncryption(passphrase.encode("utf-8"))
                if passphrase is not None
                else serialization.NoEncryption()
            ),
        )
    )


class _FakeSecretStore:
    def __init__(self, *, available: bool = True) -> None:
        self.available = available
        self.secrets: dict[str, str] = {}
        self.deleted: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        return f"secret://test/{configuration_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        self.secrets[secret_ref] = secret

    def delete_secret(self, secret_ref: str) -> None:
        self.deleted.append(secret_ref)
        self.secrets.pop(secret_ref, None)


def _service(
    store: CertificateCatalogStore,
    *,
    secret_store: _FakeSecretStore | None = None,
) -> CertificateImportService:
    ids = iter(("managed-cert-imported", "cert-config-imported"))
    return CertificateImportService(
        store=store,
        id_factory=lambda: next(ids),
        clock=lambda: datetime(2026, 5, 9, 13, 29, tzinfo=UTC),
        secret_store=secret_store,
    )


def test_certificate_import_copies_pkcs12_and_persists_catalog(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase="secret", common_name="Alice Example")
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")

    result = _service(store).import_pkcs12(
        source_path=source,
        display_name="Alice Signing",
        passphrase="secret",
    )

    assert result.managed_file_path == store.managed_certificate_dir / (
        "cert_managed-cert-imported.p12"
    )
    assert result.managed_file_path.read_bytes() == source.read_bytes()
    assert result.managed_certificate.display_name == "Alice Signing"
    assert result.managed_certificate.source_kind == "imported"
    assert result.managed_certificate.created_at == "2026-05-09T13:29:00Z"
    assert result.managed_certificate.subject_summary.common_name == "Alice Example"
    assert result.managed_certificate.subject_summary.email == "alice@example.com"
    assert result.managed_certificate.subject_summary.title == "Board Secretary"
    assert result.managed_certificate.subject_summary.company == "FoliaSeal"
    assert result.certificate_configuration.display_name == "Alice Signing"
    assert result.certificate_configuration.managed_certificate_id == (
        "managed-cert-imported"
    )
    assert result.certificate_configuration.save_password is False
    assert result.certificate_configuration.password_secret_ref is None

    reloaded = store.load_catalog()
    assert reloaded.managed_certificate_by_id("managed-cert-imported").storage_filename == (
        "cert_managed-cert-imported.p12"
    )
    assert reloaded.configuration_named("Alice Signing").certificate_configuration_id == (
        "cert-config-imported"
    )


def test_certificate_import_can_save_password_in_secret_store(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.p12"
    passphrase = "correct horse"
    _write_test_pkcs12(source, passphrase=passphrase, common_name="Alice Example")
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore()

    result = _service(store, secret_store=secret_store).import_pkcs12(
        source_path=source,
        display_name="Alice Signing",
        passphrase=passphrase,
        save_password=True,
    )

    configuration = result.certificate_configuration
    assert configuration.save_password is True
    assert configuration.password_secret_ref == "secret://test/cert-config-imported"
    assert secret_store.secrets == {
        "secret://test/cert-config-imported": passphrase,
    }
    assert passphrase not in store.catalog_path.read_text(encoding="utf-8")


def test_certificate_import_rejects_saved_password_when_store_unavailable(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase="secret")
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore(available=False)

    with pytest.raises(ConfigValidationError, match="not available"):
        _service(store, secret_store=secret_store).import_pkcs12(
            source_path=source,
            display_name="Alice Signing",
            passphrase="secret",
            save_password=True,
        )

    assert store.load_catalog().certificate_configurations == ()
    assert not store.managed_certificate_dir.exists()
    assert secret_store.secrets == {}


def test_certificate_import_removes_saved_password_when_catalog_save_fails(
    tmp_path: Path,
) -> None:
    class _FailingSaveStore(CertificateCatalogStore):
        def save_catalog(self, catalog: CertificateCatalog) -> None:
            raise OSError("disk full")

    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase="secret")
    store = _FailingSaveStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore()

    with pytest.raises(OSError, match="disk full"):
        _service(store, secret_store=secret_store).import_pkcs12(
            source_path=source,
            display_name="Alice Signing",
            passphrase="secret",
            save_password=True,
        )

    assert not (store.managed_certificate_dir / "cert_managed-cert-imported.p12").exists()
    assert secret_store.deleted == ["secret://test/cert-config-imported"]
    assert secret_store.secrets == {}


def test_certificate_import_rejects_wrong_password_without_copying(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase="secret")
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")

    with pytest.raises(CertificateImportError, match="Check the file and password"):
        _service(store).import_pkcs12(
            source_path=source,
            display_name="Alice Signing",
            passphrase="wrong",
        )

    assert store.load_catalog().certificate_configurations == ()
    assert not store.managed_certificate_dir.exists()


def test_certificate_import_rejects_blank_password_without_copying(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase=None)
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")

    with pytest.raises(CertificateImportError, match="password-protected"):
        _service(store).import_pkcs12(
            source_path=source,
            display_name="Alice Signing",
            passphrase="",
        )

    assert store.load_catalog().certificate_configurations == ()
    assert not store.managed_certificate_dir.exists()


def test_certificate_import_rejects_duplicate_display_name_before_copying(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase="secret")
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    service = _service(store)
    service.import_pkcs12(
        source_path=source,
        display_name="Alice Signing",
        passphrase="secret",
    )
    managed_files = tuple(store.managed_certificate_dir.iterdir())

    with pytest.raises(ConfigValidationError, match="already exists"):
        CertificateImportService(
            store=store,
            id_factory=lambda: "second-id",
        ).import_pkcs12(
            source_path=source,
            display_name="Alice Signing",
            passphrase="secret",
        )

    assert tuple(store.managed_certificate_dir.iterdir()) == managed_files
