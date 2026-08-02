from pathlib import Path

import pytest

from foliaseal.infra.config.certificate_storage import (
    CERTIFICATE_DIRECTORY_NAME,
    CertificateCatalogStore,
    default_certificate_config_directory,
)
from foliaseal.infra.config.schemas import ConfigValidationError
from tests.support.signing_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_managed_certificate,
)


def test_default_certificate_config_directory_uses_xdg_data_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

    directory = default_certificate_config_directory()

    assert directory == tmp_path / "xdg-data" / "FoliaSeal" / CERTIFICATE_DIRECTORY_NAME


def test_certificate_catalog_store_loads_empty_when_missing(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)

    catalog = store.load_catalog()

    assert catalog.schema_version == 1
    assert catalog.managed_certificates == ()
    assert catalog.certificate_configurations == ()


def test_certificate_catalog_store_saves_human_readable_json_without_password(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    original = build_certificate_catalog(
        certificate_configurations=(
            build_certificate_configuration(
                save_password=True,
                password_secret_ref="secret://foliaseal/cert-config-default",
            ),
        )
    )

    store.save_catalog(original)

    payload_text = store.catalog_path.read_text(encoding="utf-8")
    assert store.catalog_path.parent.name == CERTIFICATE_DIRECTORY_NAME
    assert payload_text.startswith("{\n")
    assert '  "certificate_configurations": [' in payload_text
    assert '  "managed_certificates": [' in payload_text
    assert '"password_secret_ref": "secret://foliaseal/cert-config-default"' in payload_text
    assert "secret-passphrase" not in payload_text
    assert '"password"' not in payload_text
    assert '"passphrase"' not in payload_text
    assert payload_text.endswith("\n")

    reloaded = store.load_catalog()

    assert reloaded == original


def test_certificate_catalog_store_removes_temp_file_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    original_replace = Path.replace

    def fail_catalog_replace(path: Path, target: Path) -> Path:
        if path.name == "certificates.json.tmp":
            raise OSError("replace failed")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_catalog_replace)

    with pytest.raises(OSError, match="replace failed"):
        store.save_catalog(build_certificate_catalog())

    assert not store.catalog_path.exists()
    assert not store.catalog_path.with_name("certificates.json.tmp").exists()


def test_certificate_catalog_store_upserts_and_deletes_configurations(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
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

    updated = store.save_configuration(
        build_certificate_configuration(
            certificate_configuration_id="cert-config-alt",
            display_name="Alternate Signing",
            managed_certificate_id="managed-cert-alt",
        )
    )

    assert tuple(
        configuration.display_name for configuration in updated.certificate_configurations
    ) == (
        "Corporate Records Signing",
        "Alternate Signing",
    )
    assert store.load_catalog().configuration_named("Alternate Signing").managed_certificate_id == (
        "managed-cert-alt"
    )

    removed = store.delete_configuration("Corporate Records Signing")

    assert tuple(
        configuration.display_name for configuration in removed.certificate_configurations
    ) == ("Alternate Signing",)


def test_certificate_catalog_store_deletes_configuration_by_id_only(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    original = build_certificate_catalog(
        managed_certificates=(
            build_managed_certificate(),
            build_managed_certificate(
                managed_certificate_id="managed-cert-alt",
                display_name="Alternate Signing Certificate",
                storage_filename="cert_alt.p12",
            ),
        ),
        certificate_configurations=(
            build_certificate_configuration(),
            build_certificate_configuration(
                certificate_configuration_id="cert-config-alt",
                display_name="Alternate Signing",
                managed_certificate_id="managed-cert-alt",
            ),
        )
    )
    store.save_catalog(original)

    removed = store.delete_configuration_by_id("cert-config-default")

    assert tuple(
        certificate.managed_certificate_id
        for certificate in removed.managed_certificates
    ) == ("managed-cert-default", "managed-cert-alt")
    assert tuple(
        configuration.certificate_configuration_id
        for configuration in removed.certificate_configurations
    ) == ("cert-config-alt",)
    with pytest.raises(KeyError):
        store.delete_configuration_by_id("missing-config")


def test_certificate_catalog_store_rename_preserves_configuration_id(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    store.save_catalog(build_certificate_catalog())
    configuration = store.load_catalog().configuration_named("Corporate Records Signing")
    renamed = build_certificate_configuration(
        certificate_configuration_id=configuration.certificate_configuration_id,
        managed_certificate_id=configuration.managed_certificate_id,
        display_name="Board Records Signing",
        notes="Used for board packets.",
    )

    updated = store.save_configuration(renamed)

    assert updated.configuration_by_id("cert-config-default").display_name == (
        "Board Records Signing"
    )
    assert updated.configuration_by_id("cert-config-default").notes == (
        "Used for board packets."
    )


def test_certificate_catalog_store_rename_rejects_duplicate_display_name(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    store.save_catalog(
        build_certificate_catalog(
            managed_certificates=(
                build_managed_certificate(),
                build_managed_certificate(
                    managed_certificate_id="managed-cert-alt",
                    display_name="Alternate Signing Certificate",
                    storage_filename="cert_alt.p12",
                ),
            ),
            certificate_configurations=(
                build_certificate_configuration(),
                build_certificate_configuration(
                    certificate_configuration_id="cert-config-alt",
                    display_name="Alternate Signing",
                    managed_certificate_id="managed-cert-alt",
                ),
            ),
        )
    )

    with pytest.raises(ConfigValidationError, match="duplicate names"):
        store.save_configuration(
            build_certificate_configuration(
                certificate_configuration_id="cert-config-alt",
                display_name="Corporate Records Signing",
                managed_certificate_id="managed-cert-alt",
            )
        )


def test_certificate_catalog_store_deletes_unreferenced_managed_certificate_file(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    default_file = store.managed_certificate_dir / "cert_default.p12"
    alt_file = store.managed_certificate_dir / "cert_alt.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    default_file.write_bytes(b"default-pkcs12")
    alt_file.write_bytes(b"alt-pkcs12")
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

    updated = store.delete_managed_certificate_by_id("managed-cert-alt")

    assert tuple(
        certificate.managed_certificate_id
        for certificate in updated.managed_certificates
    ) == ("managed-cert-default",)
    assert default_file.exists()
    assert not alt_file.exists()
    assert tuple(
        certificate.managed_certificate_id
        for certificate in store.load_catalog().managed_certificates
    ) == ("managed-cert-default",)


def test_certificate_catalog_store_blocks_referenced_managed_certificate_delete(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    managed_file = store.managed_certificate_dir / "cert_default.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    managed_file.write_bytes(b"default-pkcs12")
    original = build_certificate_catalog()
    store.save_catalog(original)

    with pytest.raises(ConfigValidationError, match="delete the configuration first"):
        store.delete_managed_certificate_by_id("managed-cert-default")

    assert managed_file.exists()
    assert store.load_catalog() == original


def test_certificate_catalog_store_deletes_missing_managed_certificate_file(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
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

    updated = store.delete_managed_certificate_by_id("managed-cert-alt")

    assert tuple(
        certificate.managed_certificate_id
        for certificate in updated.managed_certificates
    ) == ("managed-cert-default",)


def test_certificate_catalog_store_exports_managed_certificate_file(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    source = store.managed_certificate_dir / "cert_default.p12"
    destination = tmp_path / "backup" / "board-secretary.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"managed-pkcs12")
    store.save_catalog(build_certificate_catalog())

    exported = store.export_managed_certificate_by_id(
        "managed-cert-default",
        destination,
    )

    assert exported == destination
    assert destination.read_bytes() == b"managed-pkcs12"
    assert source.read_bytes() == b"managed-pkcs12"
    assert store.load_catalog() == build_certificate_catalog()


def test_certificate_catalog_store_export_overwrites_destination(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    source = store.managed_certificate_dir / "cert_default.p12"
    destination = tmp_path / "backup.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"current-managed-pkcs12")
    destination.write_bytes(b"old-backup")
    store.save_catalog(build_certificate_catalog())

    store.export_managed_certificate_by_id("managed-cert-default", destination)

    assert destination.read_bytes() == b"current-managed-pkcs12"


def test_certificate_catalog_store_export_rejects_missing_source(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    store.save_catalog(build_certificate_catalog())

    with pytest.raises(FileNotFoundError, match="Managed certificate file is missing"):
        store.export_managed_certificate_by_id(
            "managed-cert-default",
            tmp_path / "backup.p12",
        )


def test_certificate_catalog_store_export_rejects_same_source_destination(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    source = store.managed_certificate_dir / "cert_default.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"managed-pkcs12")
    store.save_catalog(build_certificate_catalog())

    with pytest.raises(ConfigValidationError, match="different"):
        store.export_managed_certificate_by_id("managed-cert-default", source)


def test_certificate_catalog_store_export_rejects_managed_storage_destination(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    source = store.managed_certificate_dir / "cert_default.p12"
    other_managed_file = store.managed_certificate_dir / "other_backup.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"managed-pkcs12")
    other_managed_file.write_bytes(b"other-managed-pkcs12")
    store.save_catalog(build_certificate_catalog())

    with pytest.raises(ConfigValidationError, match="outside FoliaSeal managed"):
        store.export_managed_certificate_by_id(
            "managed-cert-default",
            other_managed_file,
        )

    assert other_managed_file.read_bytes() == b"other-managed-pkcs12"


def test_certificate_catalog_store_export_rejects_symlink_destination(
    tmp_path: Path,
) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    source = store.managed_certificate_dir / "cert_default.p12"
    target = store.managed_certificate_dir / "other_managed.p12"
    symlink = tmp_path / "backup-link.p12"
    store.managed_certificate_dir.mkdir(parents=True)
    source.write_bytes(b"managed-pkcs12")
    target.write_bytes(b"other-managed-pkcs12")
    symlink.symlink_to(target)
    store.save_catalog(build_certificate_catalog())

    with pytest.raises(ConfigValidationError, match="symbolic link"):
        store.export_managed_certificate_by_id("managed-cert-default", symlink)

    assert target.read_bytes() == b"other-managed-pkcs12"


def test_certificate_catalog_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    store.catalog_path.parent.mkdir(parents=True, exist_ok=True)
    store.catalog_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="not valid JSON"):
        store.load_catalog()
