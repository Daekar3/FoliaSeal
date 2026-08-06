from pathlib import Path

import pytest

from foliaseal.application.certificate_catalog_repository import (
    InMemoryCertificateCatalogRepository,
)
from foliaseal.application.signing_material_resolver import (
    RepositoryBackedCertificateSigningMaterialPort,
    SigningMaterialResolutionError,
)
from tests.support.signing_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
)


class MemorySecretProvider:
    def __init__(self, secrets: dict[str, str] | None = None, *, available: bool = True) -> None:
        self._secrets = secrets or {}
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def get_secret(self, secret_ref: str) -> str | None:
        return self._secrets.get(secret_ref)


class FailingSecretProvider(MemorySecretProvider):
    def get_secret(self, secret_ref: str) -> str | None:
        raise RuntimeError("backend failed")


def _repository(catalog, tmp_path: Path) -> InMemoryCertificateCatalogRepository:
    repository = InMemoryCertificateCatalogRepository(
        catalog=catalog,
        storage_dir=tmp_path / "Certificates",
    )
    managed = catalog.managed_certificate_by_id("managed-cert-default")
    repository.commit_managed_certificate(
        payload=b"pkcs12-bytes",
        managed_certificate=managed,
        catalog=catalog,
    )
    return repository


def test_port_uses_explicit_passphrase_for_unsaved_password(tmp_path: Path) -> None:
    catalog = build_certificate_catalog()
    repository = _repository(catalog, tmp_path)
    port = RepositoryBackedCertificateSigningMaterialPort(repository=repository)

    material = port.resolve(
        certificate_configuration_id="cert-config-default",
        passphrase="typed-secret",
    )

    assert material.certificate_path == str(
        repository.managed_certificate_dir / "cert_default.p12"
    )
    assert material.passphrase == "typed-secret"
    assert material.certificate_alias is None


def test_port_uses_secret_provider_for_saved_password(tmp_path: Path) -> None:
    secret_ref = "secret://foliaseal/cert-config-default"
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref=secret_ref,
            ),
        )
    )
    repository = _repository(catalog, tmp_path)
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=repository,
        secret_provider=MemorySecretProvider({secret_ref: "stored-secret"}),
    )

    material = port.resolve(certificate_configuration_id="cert-config-default")

    assert material.passphrase == "stored-secret"


def test_port_preserves_certificate_alias(tmp_path: Path) -> None:
    catalog = build_certificate_catalog()
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=_repository(catalog, tmp_path),
    )

    material = port.resolve(
        certificate_configuration_id="cert-config-default",
        passphrase="typed-secret",
        certificate_alias="primary",
    )

    assert material.certificate_alias == "primary"


def test_port_fails_helpfully_when_managed_certificate_file_is_missing(
    tmp_path: Path,
) -> None:
    catalog = build_certificate_catalog()
    repository = InMemoryCertificateCatalogRepository(
        catalog=catalog,
        storage_dir=tmp_path / "Certificates",
    )
    port = RepositoryBackedCertificateSigningMaterialPort(repository=repository)

    with pytest.raises(SigningMaterialResolutionError, match="certificate file is missing"):
        port.resolve(
            certificate_configuration_id="cert-config-default",
            passphrase="typed-secret",
        )


def test_port_fails_helpfully_when_saved_password_store_unavailable(tmp_path: Path) -> None:
    secret_ref = "secret://foliaseal/cert-config-default"
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref=secret_ref,
            ),
        )
    )
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=_repository(catalog, tmp_path),
        secret_provider=MemorySecretProvider(available=False),
    )

    with pytest.raises(SigningMaterialResolutionError, match="Saved password storage"):
        port.resolve(certificate_configuration_id="cert-config-default")


def test_port_fails_helpfully_when_saved_password_read_fails(tmp_path: Path) -> None:
    secret_ref = "secret://foliaseal/cert-config-default"
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref=secret_ref,
            ),
        )
    )
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=_repository(catalog, tmp_path),
        secret_provider=FailingSecretProvider(),
    )

    with pytest.raises(
        SigningMaterialResolutionError,
        match=(
            "^Saved password storage could not read the certificate password\\. "
            "Enter the password manually or try again after fixing secure storage\\.$"
        ),
    ):
        port.resolve(certificate_configuration_id="cert-config-default")


def test_port_fails_helpfully_when_unsaved_password_is_not_supplied(tmp_path: Path) -> None:
    catalog = build_certificate_catalog()
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=_repository(catalog, tmp_path),
    )

    with pytest.raises(SigningMaterialResolutionError, match="requires a certificate password"):
        port.resolve(certificate_configuration_id="cert-config-default")


def test_port_rejects_unknown_configuration(tmp_path: Path) -> None:
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=_repository(build_certificate_catalog(), tmp_path),
    )

    with pytest.raises(
        SigningMaterialResolutionError,
        match="^Certificate configuration 'missing' was not found\\.$",
    ):
        port.resolve(certificate_configuration_id="missing", passphrase="typed-secret")


def test_port_rejects_dangling_managed_certificate_reference(tmp_path: Path) -> None:
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(managed_certificate_id="missing-managed"),
        )
    )
    repository = InMemoryCertificateCatalogRepository(
        catalog=catalog,
        storage_dir=tmp_path / "Certificates",
    )
    port = RepositoryBackedCertificateSigningMaterialPort(repository=repository)

    with pytest.raises(SigningMaterialResolutionError, match="no longer exists"):
        port.resolve(certificate_configuration_id="cert-config-default", passphrase="typed-secret")


def test_port_rejects_blank_explicit_passphrase(tmp_path: Path) -> None:
    port = RepositoryBackedCertificateSigningMaterialPort(
        repository=_repository(build_certificate_catalog(), tmp_path),
    )

    with pytest.raises(
        SigningMaterialResolutionError,
        match="^The certificate password cannot be blank\\.$",
    ):
        port.resolve(certificate_configuration_id="cert-config-default", passphrase="")


def test_port_rejects_missing_or_blank_saved_secret(tmp_path: Path) -> None:
    secret_ref = "secret://foliaseal/cert-config-default"
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref=secret_ref,
            ),
        )
    )
    repository = _repository(catalog, tmp_path)
    missing_port = RepositoryBackedCertificateSigningMaterialPort(
        repository=repository,
        secret_provider=MemorySecretProvider(),
    )
    with pytest.raises(SigningMaterialResolutionError, match="could not be found"):
        missing_port.resolve(certificate_configuration_id="cert-config-default")

    blank_port = RepositoryBackedCertificateSigningMaterialPort(
        repository=repository,
        secret_provider=MemorySecretProvider({secret_ref: ""}),
    )
    with pytest.raises(SigningMaterialResolutionError, match="cannot be blank"):
        blank_port.resolve(certificate_configuration_id="cert-config-default")


def test_port_accepts_repository_without_path_attributes() -> None:
    catalog = build_certificate_catalog()

    class FakeRepository:
        def load_catalog(self):
            return catalog

        def material_for(self, managed_certificate):
            from foliaseal.application.certificate_catalog_repository import (
                ManagedCertificateMaterial,
            )

            return ManagedCertificateMaterial(certificate_path="virtual/cert_default.p12")

    port = RepositoryBackedCertificateSigningMaterialPort(repository=FakeRepository())

    material = port.resolve(
        certificate_configuration_id="cert-config-default",
        passphrase="typed-secret",
    )

    assert material.certificate_path == "virtual/cert_default.p12"
