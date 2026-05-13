from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.serialization import pkcs12

from foliaseal.application.certificate_creation import (
    CertificateCreationError,
    CertificateCreationService,
)
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import CertificateCatalog, ConfigValidationError


class _FakeSecretStore:
    def __init__(
        self,
        *,
        available: bool = True,
        fail_delete: bool = False,
    ) -> None:
        self.available = available
        self.fail_delete = fail_delete
        self.secrets: dict[str, str] = {}
        self.deleted: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        return f"secret://test/{configuration_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        self.secrets[secret_ref] = secret

    def delete_secret(self, secret_ref: str) -> None:
        if self.fail_delete:
            raise OSError("secure storage cleanup failed")
        self.deleted.append(secret_ref)
        self.secrets.pop(secret_ref, None)


def _service(
    store: CertificateCatalogStore,
    *,
    secret_store: _FakeSecretStore | None = None,
) -> CertificateCreationService:
    ids = iter(("managed-cert-created", "cert-config-created"))
    return CertificateCreationService(
        store=store,
        id_factory=lambda: next(ids),
        clock=lambda: datetime(2026, 5, 13, 1, 30, tzinfo=UTC),
        secret_store=secret_store,
    )


def test_certificate_creation_writes_pkcs12_and_persists_catalog(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")

    result = _service(store).create_self_signed_certificate(
        display_name="Alice Signing",
        passphrase="correct horse",
    )

    assert result.managed_file_path == store.managed_certificate_dir / (
        "cert_managed-cert-created.p12"
    )
    assert result.managed_file_path.exists()
    key, certificate, extra = pkcs12.load_key_and_certificates(
        result.managed_file_path.read_bytes(),
        b"correct horse",
    )
    assert key is not None
    assert certificate is not None
    assert extra == []
    assert result.managed_certificate.source_kind == "created"
    assert result.managed_certificate.display_name == "Alice Signing"
    assert result.managed_certificate.created_at == "2026-05-13T01:30:00Z"
    assert result.managed_certificate.subject_summary.common_name == "Alice Signing"
    assert result.certificate_configuration.display_name == "Alice Signing"
    assert result.certificate_configuration.save_password is False
    assert result.certificate_configuration.password_secret_ref is None

    reloaded = store.load_catalog()
    assert reloaded.managed_certificate_by_id(
        "managed-cert-created"
    ).source_kind == "created"
    assert reloaded.configuration_named("Alice Signing").certificate_configuration_id == (
        "cert-config-created"
    )


def test_certificate_creation_can_save_password_outside_catalog(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore()

    result = _service(store, secret_store=secret_store).create_self_signed_certificate(
        display_name="Alice Signing",
        passphrase="correct horse",
        save_password=True,
    )

    configuration = result.certificate_configuration
    assert configuration.save_password is True
    assert configuration.password_secret_ref == "secret://test/cert-config-created"
    assert secret_store.secrets == {
        "secret://test/cert-config-created": "correct horse",
    }
    assert "correct horse" not in store.catalog_path.read_text(encoding="utf-8")


def test_certificate_creation_rejects_saved_password_when_store_unavailable(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore(available=False)

    with pytest.raises(ConfigValidationError, match="not available"):
        _service(store, secret_store=secret_store).create_self_signed_certificate(
            display_name="Alice Signing",
            passphrase="correct horse",
            save_password=True,
        )

    assert store.load_catalog().certificate_configurations == ()
    assert not store.managed_certificate_dir.exists()
    assert secret_store.secrets == {}


def test_certificate_creation_rejects_duplicate_display_name_before_writing(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    service = _service(store)
    service.create_self_signed_certificate(
        display_name="Alice Signing",
        passphrase="correct horse",
    )
    managed_files = tuple(store.managed_certificate_dir.iterdir())

    with pytest.raises(ConfigValidationError, match="already exists"):
        CertificateCreationService(
            store=store,
            id_factory=lambda: "second-id",
        ).create_self_signed_certificate(
            display_name="Alice Signing",
            passphrase="correct horse",
        )

    assert tuple(store.managed_certificate_dir.iterdir()) == managed_files


def test_certificate_creation_removes_file_and_secret_when_catalog_save_fails(
    tmp_path: Path,
) -> None:
    class _FailingSaveStore(CertificateCatalogStore):
        def save_catalog(self, catalog: CertificateCatalog) -> None:
            raise OSError("disk full")

    store = _FailingSaveStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore()

    with pytest.raises(OSError, match="disk full"):
        _service(store, secret_store=secret_store).create_self_signed_certificate(
            display_name="Alice Signing",
            passphrase="correct horse",
            save_password=True,
        )

    assert not (store.managed_certificate_dir / "cert_managed-cert-created.p12").exists()
    assert secret_store.deleted == ["secret://test/cert-config-created"]
    assert secret_store.secrets == {}


def test_certificate_creation_reports_saved_password_cleanup_failure(
    tmp_path: Path,
) -> None:
    class _FailingSaveStore(CertificateCatalogStore):
        def save_catalog(self, catalog: CertificateCatalog) -> None:
            raise OSError("disk full")

    store = _FailingSaveStore(storage_dir=tmp_path / "Certificates")
    secret_store = _FakeSecretStore(fail_delete=True)

    with pytest.raises(CertificateCreationError, match="could not be removed"):
        _service(store, secret_store=secret_store).create_self_signed_certificate(
            display_name="Alice Signing",
            passphrase="correct horse",
            save_password=True,
        )

    assert secret_store.secrets == {
        "secret://test/cert-config-created": "correct horse",
    }
