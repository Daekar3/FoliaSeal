from pathlib import Path

import pytest

from foliaseal.application.signing_material_resolver import (
    CertificateSigningMaterialResolver,
    SigningMaterialResolutionError,
)
from tests.support.phase3_builders import (
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


def test_resolver_uses_explicit_passphrase_for_unsaved_password(tmp_path: Path) -> None:
    cert_file = tmp_path / "managed" / "cert_default.p12"
    cert_file.parent.mkdir()
    cert_file.write_bytes(b"pkcs12-bytes")
    catalog = build_certificate_catalog()
    resolver = CertificateSigningMaterialResolver(managed_certificate_dir=cert_file.parent)

    material = resolver.resolve_by_configuration_id(
        catalog,
        "cert-config-default",
        passphrase="typed-secret",
    )

    assert material.certificate_path == str(cert_file)
    assert material.passphrase == "typed-secret"
    assert material.certificate_alias is None


def test_resolver_uses_secret_provider_for_saved_password(tmp_path: Path) -> None:
    cert_file = tmp_path / "managed" / "cert_default.p12"
    cert_file.parent.mkdir()
    cert_file.write_bytes(b"pkcs12-bytes")
    secret_ref = "secret://foliaseal/cert-config-default"
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref=secret_ref,
            ),
        )
    )
    resolver = CertificateSigningMaterialResolver(
        managed_certificate_dir=cert_file.parent,
        secret_provider=MemorySecretProvider({secret_ref: "stored-secret"}),
    )

    material = resolver.resolve_by_configuration_id(catalog, "cert-config-default")

    assert material.certificate_path == str(cert_file)
    assert material.passphrase == "stored-secret"


def test_resolver_fails_helpfully_when_managed_certificate_file_is_missing(
    tmp_path: Path,
) -> None:
    catalog = build_certificate_catalog()
    resolver = CertificateSigningMaterialResolver(managed_certificate_dir=tmp_path / "managed")

    with pytest.raises(SigningMaterialResolutionError, match="certificate file is missing"):
        resolver.resolve_by_configuration_id(
            catalog,
            "cert-config-default",
            passphrase="typed-secret",
        )


def test_resolver_fails_helpfully_when_saved_password_store_unavailable(
    tmp_path: Path,
) -> None:
    cert_file = tmp_path / "managed" / "cert_default.p12"
    cert_file.parent.mkdir()
    cert_file.write_bytes(b"pkcs12-bytes")
    catalog = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref="secret://foliaseal/cert-config-default",
            ),
        )
    )
    resolver = CertificateSigningMaterialResolver(
        managed_certificate_dir=cert_file.parent,
        secret_provider=MemorySecretProvider(available=False),
    )

    with pytest.raises(SigningMaterialResolutionError, match="Saved password storage"):
        resolver.resolve_by_configuration_id(catalog, "cert-config-default")


def test_resolver_fails_helpfully_when_unsaved_password_is_not_supplied(
    tmp_path: Path,
) -> None:
    cert_file = tmp_path / "managed" / "cert_default.p12"
    cert_file.parent.mkdir()
    cert_file.write_bytes(b"pkcs12-bytes")
    catalog = build_certificate_catalog()
    resolver = CertificateSigningMaterialResolver(managed_certificate_dir=cert_file.parent)

    with pytest.raises(SigningMaterialResolutionError, match="requires a certificate password"):
        resolver.resolve_by_configuration_id(catalog, "cert-config-default")
