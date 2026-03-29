from pathlib import Path

import pytest

from foliaseal.infra.config.profile_storage import (
    PROFILE_DIRECTORY_NAME,
    SignaturePresetCatalogStore,
    default_signature_profiles_directory,
)
from foliaseal.infra.config.schemas import ConfigValidationError
from tests.support.phase3_builders import build_signature_preset_catalog


def test_default_signature_profiles_directory_uses_xdg_data_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg-data"))

    directory = default_signature_profiles_directory()

    assert directory == tmp_path / "xdg-data" / "FoliaSeal" / PROFILE_DIRECTORY_NAME


def test_signature_preset_catalog_store_loads_empty_when_missing(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)

    catalog = store.load_catalog()

    assert catalog.schema_version == 1
    assert catalog.profile_names() == ()


def test_signature_preset_catalog_store_saves_and_reloads_human_readable_json(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    original = build_signature_preset_catalog()

    store.save_catalog(original)

    payload_text = store.catalog_path.read_text(encoding="utf-8")
    assert store.catalog_path.parent.name == PROFILE_DIRECTORY_NAME
    assert payload_text.startswith("{\n")
    assert '  "profiles": [' in payload_text
    assert payload_text.endswith("\n")

    reloaded = store.load_catalog()

    assert reloaded == original
    assert reloaded.profile_names() == ("Default", "Compact")


def test_signature_preset_catalog_store_upserts_and_deletes_profiles(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    original = build_signature_preset_catalog()
    store.save_catalog(original)

    removed = store.delete_profile("Compact")

    assert removed.profile_names() == ("Default",)
    assert store.load_catalog().profile_names() == ("Default",)

    removed = store.delete_profile("Default")

    assert removed.profile_names() == ()
    assert store.load_catalog().profile_names() == ()


def test_signature_preset_catalog_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.catalog_path.parent.mkdir(parents=True, exist_ok=True)
    store.catalog_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="not valid JSON"):
        store.load_catalog()
