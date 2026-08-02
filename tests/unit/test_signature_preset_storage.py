from pathlib import Path

import pytest

from foliaseal.infra.config.profile_storage import (
    PROFILE_DIRECTORY_NAME,
    SignaturePresetCatalogStore,
    default_signature_profiles_directory,
)
from foliaseal.infra.config.schemas import ConfigValidationError
from tests.support.signing_builders import (
    build_signature_appearance,
    build_signature_preset_catalog,
)


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
    assert catalog.preset_names() == ()


def test_signature_preset_catalog_store_saves_and_reloads_human_readable_json(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    original = build_signature_preset_catalog()

    store.save_catalog(original)

    payload_text = store.catalog_path.read_text(encoding="utf-8")
    assert store.catalog_path.parent.name == PROFILE_DIRECTORY_NAME
    assert payload_text.startswith("{\n")
    assert '  "appearance_profiles": [' in payload_text
    assert '  "placement_profiles": [' in payload_text
    assert '  "signature_presets": [' in payload_text
    assert payload_text.endswith("\n")

    reloaded = store.load_catalog()

    assert reloaded == original
    assert reloaded.preset_names() == ("Default", "Compact")


def test_signature_preset_catalog_store_deletes_presets(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    original = build_signature_preset_catalog()
    store.save_catalog(original)

    removed = store.delete_preset("Compact")

    assert removed.preset_names() == ("Default",)
    assert removed.appearance_profile_named("Compact")
    assert removed.placement_profile_named("Compact")
    assert store.load_catalog().preset_names() == ("Default",)

    removed = store.delete_preset("Default")

    assert removed.preset_names() == ()
    assert store.load_catalog().preset_names() == ()
    assert store.load_catalog().appearance_profile_named("Default")


def test_signature_preset_catalog_store_manages_independent_profiles(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.save_catalog(build_signature_preset_catalog())
    appearance = build_signature_appearance(signer_label_prefix="Saved independently")

    catalog = store.save_appearance_profile("Independent look", appearance)
    assert catalog.appearance_profile_named("Independent look").appearance == appearance

    catalog = store.save_placement_profile(
        "Independent placement", left_pt=11.0, bottom_pt=12.0, width_pt=130.0, height_pt=44.0
    )
    assert catalog.placement_profile_named("Independent placement").rect.width_pt == 130.0
    assert store.load_catalog() == catalog

    with pytest.raises(ConfigValidationError, match="referenced by signature preset"):
        store.delete_appearance_profile("Compact")

    deleted = store.delete_appearance_profile("Independent look")
    with pytest.raises(KeyError):
        deleted.appearance_profile_named("Independent look")


def test_signature_preset_catalog_store_renames_objects_without_breaking_references(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.save_catalog(build_signature_preset_catalog())

    catalog = store.rename_appearance_profile("Compact", "Compact look")
    catalog = store.rename_placement_profile("Compact", "Compact placement")
    catalog = store.rename_preset("Compact", "Compact preset")

    resolved = catalog.preset_named("Compact preset")
    assert resolved.appearance_profile is not None
    assert resolved.appearance_profile.display_name == "Compact look"
    assert resolved.placement_profile is not None
    assert resolved.placement_profile.display_name == "Compact placement"
    assert store.load_catalog() == catalog


def test_signature_preset_catalog_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / PROFILE_DIRECTORY_NAME)
    store.catalog_path.parent.mkdir(parents=True, exist_ok=True)
    store.catalog_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="not valid JSON"):
        store.load_catalog()
