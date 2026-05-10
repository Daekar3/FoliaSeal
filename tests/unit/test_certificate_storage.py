from pathlib import Path

import pytest

from foliaseal.infra.config.certificate_storage import (
    CERTIFICATE_DIRECTORY_NAME,
    CertificateCatalogStore,
    default_certificate_config_directory,
)
from foliaseal.infra.config.schemas import ConfigValidationError
from tests.support.phase3_builders import (
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


def test_certificate_catalog_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    store.catalog_path.parent.mkdir(parents=True, exist_ok=True)
    store.catalog_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="not valid JSON"):
        store.load_catalog()
