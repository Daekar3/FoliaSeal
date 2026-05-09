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
from foliaseal.infra.config.schemas import ConfigValidationError


def _write_test_pkcs12(
    path: Path,
    *,
    passphrase: str,
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
            encryption_algorithm=serialization.BestAvailableEncryption(
                passphrase.encode("utf-8")
            ),
        )
    )


def _service(store: CertificateCatalogStore) -> CertificateImportService:
    ids = iter(("managed-cert-imported", "cert-config-imported"))
    return CertificateImportService(
        store=store,
        id_factory=lambda: next(ids),
        clock=lambda: datetime(2026, 5, 9, 13, 29, tzinfo=UTC),
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
