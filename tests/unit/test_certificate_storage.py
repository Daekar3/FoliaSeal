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
    store.save_catalog(build_certificate_catalog())

    updated = store.save_configuration(
        build_certificate_configuration(
            certificate_configuration_id="cert-config-alt",
            display_name="Alternate Signing",
        )
    )

    assert tuple(
        configuration.display_name for configuration in updated.certificate_configurations
    ) == (
        "Corporate Records Signing",
        "Alternate Signing",
    )
    assert store.load_catalog().configuration_named("Alternate Signing").managed_certificate_id == (
        "managed-cert-default"
    )

    removed = store.delete_configuration("Corporate Records Signing")

    assert tuple(
        configuration.display_name for configuration in removed.certificate_configurations
    ) == ("Alternate Signing",)


def test_certificate_catalog_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = CertificateCatalogStore(storage_dir=tmp_path / CERTIFICATE_DIRECTORY_NAME)
    store.catalog_path.parent.mkdir(parents=True, exist_ok=True)
    store.catalog_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="not valid JSON"):
        store.load_catalog()
