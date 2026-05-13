from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from foliaseal.application.certificate_lifecycle import (
    CertificateLifecycleError,
    CertificateLifecycleService,
)
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.schemas import CertificateCatalog, ConfigValidationError
from tests.support.phase3_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
)
from tests.unit.test_certificate_import import _write_test_pkcs12


class _FakeSecretStore:
    def __init__(
        self,
        *,
        available: bool = True,
        fail_set: bool = False,
    ) -> None:
        self.available = available
        self.fail_set = fail_set
        self.secrets: dict[str, str] = {}
        self.deleted: list[str] = []

    def is_available(self) -> bool:
        return self.available

    def secret_ref_for_configuration(self, configuration_id: str) -> str:
        return f"secret://test/{configuration_id}"

    def set_secret(self, secret_ref: str, secret: str) -> None:
        if self.fail_set:
            raise OSError("secure storage restore failed")
        self.secrets[secret_ref] = secret

    def get_secret(self, secret_ref: str) -> str | None:
        return self.secrets.get(secret_ref)

    def delete_secret(self, secret_ref: str) -> None:
        self.deleted.append(secret_ref)
        self.secrets.pop(secret_ref, None)


def _service(
    store: CertificateCatalogStore,
    *,
    secret_store: _FakeSecretStore | None = None,
    ids: tuple[str, ...] = ("managed-cert-one", "cert-config-one"),
) -> CertificateLifecycleService:
    id_values = iter(ids)
    return CertificateLifecycleService(
        store=store,
        secret_store=secret_store,
        id_factory=lambda: next(id_values),
        clock=lambda: datetime(2026, 5, 13, 12, 0, tzinfo=UTC),
    )


def test_lifecycle_creates_self_signed_certificate_and_requests_refresh(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")

    result = _service(store).create_self_signed_certificate(
        display_name="Alice Signing",
        passphrase="correct horse",
    )

    assert result.refresh_shell is True
    assert result.user_message == "Created certificate configuration 'Alice Signing'."
    assert result.managed_certificate is not None
    assert result.managed_certificate.source_kind == "created"
    assert result.certificate_configuration is not None
    assert result.certificate_configuration.display_name == "Alice Signing"
    assert result.managed_file_path == (
        store.managed_certificate_dir / "cert_managed-cert-one.p12"
    )
    assert result.managed_file_path.exists()
    assert store.load_catalog().configuration_named(
        "Alice Signing"
    ).certificate_configuration_id == "cert-config-one"


def test_lifecycle_imports_pkcs12_and_requests_refresh(tmp_path: Path) -> None:
    source = tmp_path / "source.p12"
    _write_test_pkcs12(source, passphrase="secret", common_name="Alice Example")
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")

    result = _service(store).import_pkcs12(
        source_path=source,
        display_name="Alice Imported",
        passphrase="secret",
    )

    assert result.refresh_shell is True
    assert result.user_message == "Imported certificate configuration 'Alice Imported'."
    assert result.managed_certificate is not None
    assert result.managed_certificate.source_kind == "imported"
    assert result.managed_certificate.subject_summary.common_name == "Alice Example"
    assert result.managed_file_path is not None
    assert result.managed_file_path.read_bytes() == source.read_bytes()


def test_lifecycle_saves_configuration_and_requests_refresh(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(build_certificate_catalog())

    result = _service(store).save_configuration(
        configuration_id="cert-config-default",
        display_name="Board Records Signing",
        notes="  Used for board packets.  ",
    )

    assert result.refresh_shell is True
    assert result.user_message == "Certificate configuration saved."
    assert result.certificate_configuration is not None
    assert result.certificate_configuration.display_name == "Board Records Signing"
    assert result.certificate_configuration.notes == "Used for board packets."
    reloaded = store.load_catalog().configuration_by_id("cert-config-default")
    assert reloaded.display_name == "Board Records Signing"
    assert reloaded.notes == "Used for board packets."


def test_lifecycle_deletes_configuration_with_saved_secret(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
        build_certificate_catalog(
            certificate_configurations=(
                build_certificate_configuration(
                    save_password=True,
                    password_secret_ref="secret://test/cert-config-default",
                ),
            )
        )
    )
    secret_store = _FakeSecretStore()
    secret_store.secrets["secret://test/cert-config-default"] = "secret"

    result = _service(store, secret_store=secret_store).delete_configuration(
        "cert-config-default"
    )

    assert result.refresh_shell is True
    assert result.user_message == "Certificate configuration deleted."
    assert secret_store.deleted == ["secret://test/cert-config-default"]
    assert "secret://test/cert-config-default" not in secret_store.secrets
    assert store.load_catalog().certificate_configurations == ()


def test_lifecycle_keeps_configuration_when_secret_store_unavailable(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
        build_certificate_catalog(
            certificate_configurations=(
                build_certificate_configuration(
                    save_password=True,
                    password_secret_ref="secret://test/cert-config-default",
                ),
            )
        )
    )
    secret_store = _FakeSecretStore(available=False)

    with pytest.raises(ConfigValidationError, match="was not deleted"):
        _service(store, secret_store=secret_store).delete_configuration(
            "cert-config-default"
        )

    assert store.load_catalog().configuration_by_id("cert-config-default")
    assert secret_store.deleted == []


def test_lifecycle_restores_secret_when_delete_persist_fails(tmp_path: Path) -> None:
    class _FailingDeleteStore(CertificateCatalogStore):
        def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog:
            raise OSError("disk full")

    store = _FailingDeleteStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
        build_certificate_catalog(
            certificate_configurations=(
                build_certificate_configuration(
                    save_password=True,
                    password_secret_ref="secret://test/cert-config-default",
                ),
            )
        )
    )
    secret_store = _FakeSecretStore()
    secret_store.secrets["secret://test/cert-config-default"] = "secret"

    with pytest.raises(OSError, match="disk full"):
        _service(store, secret_store=secret_store).delete_configuration(
            "cert-config-default"
        )

    assert secret_store.deleted == ["secret://test/cert-config-default"]
    assert secret_store.secrets["secret://test/cert-config-default"] == "secret"


def test_lifecycle_reports_secret_restore_failure(tmp_path: Path) -> None:
    class _FailingDeleteStore(CertificateCatalogStore):
        def delete_configuration_by_id(self, configuration_id: str) -> CertificateCatalog:
            raise OSError("disk full")

    store = _FailingDeleteStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
        build_certificate_catalog(
            certificate_configurations=(
                build_certificate_configuration(
                    save_password=True,
                    password_secret_ref="secret://test/cert-config-default",
                ),
            )
        )
    )
    secret_store = _FakeSecretStore(fail_set=True)
    secret_store.secrets["secret://test/cert-config-default"] = "secret"

    with pytest.raises(CertificateLifecycleError, match="could not be restored"):
        _service(store, secret_store=secret_store).delete_configuration(
            "cert-config-default"
        )

    assert secret_store.deleted == ["secret://test/cert-config-default"]
    assert "secret://test/cert-config-default" not in secret_store.secrets


def test_lifecycle_deletes_configuration_when_secret_already_missing(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    store.save_catalog(
        build_certificate_catalog(
            certificate_configurations=(
                build_certificate_configuration(
                    save_password=True,
                    password_secret_ref="secret://test/cert-config-default",
                ),
            )
        )
    )
    secret_store = _FakeSecretStore()

    result = _service(store, secret_store=secret_store).delete_configuration(
        "cert-config-default"
    )

    assert result.refresh_shell is True
    assert secret_store.deleted == ["secret://test/cert-config-default"]
    assert store.load_catalog().certificate_configurations == ()


def test_lifecycle_deletes_unreferenced_managed_certificate(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    managed_file = store.managed_certificate_dir / "cert_alt.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    managed_file.write_bytes(b"alt-pkcs12")
    store.save_catalog(
        build_certificate_catalog(
            managed_certificates=(
                build_managed_certificate(),
                build_managed_certificate(
                    managed_certificate_id="managed-cert-alt",
                    display_name="Alternate Signing Certificate",
                    storage_filename="cert_alt.p12",
                ),
            )
        )
    )

    result = _service(store).delete_managed_certificate("managed-cert-alt")

    assert result.refresh_shell is True
    assert result.user_message == "Managed certificate deleted."
    assert not managed_file.exists()
    assert tuple(
        certificate.managed_certificate_id
        for certificate in store.load_catalog().managed_certificates
    ) == ("managed-cert-default",)


def test_lifecycle_exports_managed_certificate_without_refresh(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / "Certificates")
    source = store.managed_certificate_dir / "cert_default.p12"
    destination = tmp_path / "backup" / "board-secretary.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"managed-pkcs12")
    store.save_catalog(build_certificate_catalog())

    result = _service(store).export_managed_certificate(
        certificate_id="managed-cert-default",
        destination_path=destination,
    )

    assert result.refresh_shell is False
    assert result.exported_path == destination
    assert result.user_message == f"Managed certificate exported to {destination}."
    assert destination.read_bytes() == b"managed-pkcs12"
