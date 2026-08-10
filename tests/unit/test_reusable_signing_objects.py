import json
from pathlib import Path

import pytest

from foliaseal.application.reusable_signing_models import (
    PlacementProfileRect,
    PlacementProfileSourcePage,
    _deserialize_appearance,
    _serialize_appearance,
)
from foliaseal.application.reusable_signing_objects import (
    DeleteObject,
    DuplicateObject,
    RenameObject,
    ReusableObjectKind,
    ReusableSigningObjects,
    SaveAppearance,
    SavePlacement,
    SavePreset,
    SetPinned,
)
from foliaseal.domain.models import SignatureImageProminence
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import ConfigValidationError
from tests.support.signing_builders import build_signature_appearance


def test_typed_boundary_lists_and_renames_objects_without_prefix_parsing(tmp_path: Path) -> None:
    service = ReusableSigningObjects(SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"))

    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    service.execute(
        SavePlacement(
            "Bottom right",
            PlacementProfileRect(
                left_pt=10.0,
                top_pt=744.0,
                width_pt=120.0,
                height_pt=36.0,
            ),
            source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
            page_number=1,
        )
    )
    view = service.view()
    appearance_ref = view.appearances[0].ref
    placement_ref = view.placements[0].ref
    service.execute(
        SavePreset(
            "Contract",
            appearance_profile_id=appearance_ref.object_id,
            placement_profile_id=placement_ref.object_id,
        )
    )

    preset = service.view().presets[0]
    assert preset.ref.kind is ReusableObjectKind.PRESET
    assert preset.details == (
        "Appearance: Approval; placement: Bottom right; certificate configuration id: none."
    )

    service.execute(RenameObject(ref=appearance_ref, new_name="Approved"))

    assert service.view().presets[0].details.startswith("Appearance: Approved;")
    assert service.resolve(appearance_ref).display_name == "Approved"

    with pytest.raises(ConfigValidationError, match="referenced"):
        service.execute(DeleteObject(ref=appearance_ref))


def test_save_placement_round_trips_v2_geometry_across_store_reload(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    service = ReusableSigningObjects(store)
    service.execute(
        SavePlacement(
            "Board approval",
            PlacementProfileRect(left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0),
            source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
            page_number=3,
            pinned=True,
        )
    )

    reloaded = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles").load_catalog()
    saved = reloaded.placement_profile_named("Board approval")

    assert saved.schema_version == 2
    assert saved.pinned is True
    assert saved.page_number == 3
    assert saved.rect.top_pt == 666.0


def test_boundary_preserves_ids_and_does_not_cascade_preset_delete(tmp_path: Path) -> None:
    service = ReusableSigningObjects(SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"))
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    appearance_ref = service.view().appearances[0].ref
    service.execute(
        SavePreset(
            "Contract",
            appearance_profile_id=appearance_ref.object_id,
        )
    )
    preset_ref = service.view().presets[0].ref

    service.execute(DeleteObject(ref=preset_ref))

    assert service.view().presets == ()
    assert service.view().appearances[0].ref == appearance_ref


def test_duplicate_save_requires_overwrite_and_failed_write_keeps_catalog(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    service = ReusableSigningObjects(store)
    appearance = build_signature_appearance()
    service.execute(SaveAppearance("Approval", appearance))

    with pytest.raises(ConfigValidationError, match="already exists"):
        service.execute(SaveAppearance("Approval", appearance))

    class FailingStore:
        def load_catalog(self):
            return store.load_catalog()

        def save_catalog(self, _catalog):
            raise OSError("disk full")

    failing = ReusableSigningObjects(FailingStore())
    with pytest.raises(OSError, match="disk full"):
        failing.execute(SaveAppearance("New", appearance))
    assert all(item.display_name != "New" for item in service.view().appearances)


def test_names_are_case_insensitively_unique_and_duplicate_starts_unpinned(tmp_path: Path) -> None:
    service = ReusableSigningObjects(SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"))
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    with pytest.raises(ConfigValidationError, match="already exists"):
        service.execute(SaveAppearance(" approval ", build_signature_appearance()))

    original = service.view().appearances[0].ref
    service.execute(SetPinned(ref=original, pinned=True))
    service.execute(DuplicateObject(ref=original, new_name="Approval copy"))

    rows = service.view().appearances
    assert {row.display_name for row in rows} == {"Approval", "Approval copy"}
    assert rows[0].pinned is True
    assert rows[1].pinned is False
    assert rows[0].ref.object_id != rows[1].ref.object_id


def test_production_boundary_rejects_missing_certificate_references(tmp_path: Path) -> None:
    service = ReusableSigningObjects(
        SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"),
        certificate_configuration_exists=lambda value: value == "known-config",
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    appearance_ref = service.view().appearances[0].ref

    with pytest.raises(ConfigValidationError, match="missing certificate configuration"):
        service.execute(
            SavePreset(
                "Missing certificate",
                appearance_profile_id=appearance_ref.object_id,
                certificate_configuration_id="missing-config",
            )
        )

    service.execute(
        SavePreset(
            "Known certificate",
            appearance_profile_id=appearance_ref.object_id,
            certificate_configuration_id="known-config",
        )
    )


def test_inline_preset_overwrite_preserves_component_ids(tmp_path: Path) -> None:
    service = ReusableSigningObjects(SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles"))
    service.execute(
        SavePreset(
            "Contract",
            appearance=build_signature_appearance(signer_label_prefix="First"),
            overwrite=False,
        )
    )
    first = service.view()
    first_appearance = first.appearances[0].ref
    first_preset = first.presets[0].ref

    service.execute(
        SavePreset(
            "Contract",
            appearance=build_signature_appearance(signer_label_prefix="Second"),
            overwrite=True,
        )
    )
    second = service.view()

    assert second.appearances[0].ref == first_appearance
    assert second.presets[0].ref == first_preset
    assert len(second.appearances) == 1


def test_inline_preset_overwrite_preserves_custom_preset_id(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    service = ReusableSigningObjects(store)
    service.execute(SavePreset("Contract", appearance=build_signature_appearance()))
    catalog = store.load_catalog()
    original = catalog.signature_presets[0]
    custom = type(original)(
        schema_version=original.schema_version,
        signature_preset_id="custom-preset-id",
        display_name=original.display_name,
        certificate_configuration_id=original.certificate_configuration_id,
        appearance_profile_id=original.appearance_profile_id,
        placement_profile_id=original.placement_profile_id,
    )
    store.save_catalog(
        type(catalog)(
            schema_version=catalog.schema_version,
            appearance_profiles=catalog.appearance_profiles,
            placement_profiles=catalog.placement_profiles,
            signature_presets=(custom,),
        )
    )

    service.execute(
        SavePreset(
            "Contract",
            appearance=build_signature_appearance(signer_label_prefix="Updated"),
            overwrite=True,
        )
    )

    assert service.view().presets[0].ref.object_id == "custom-preset-id"


def test_legacy_profile_payload_drops_unconvertible_placement_without_page_context(
    tmp_path: Path,
) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    store.catalog_path.parent.mkdir(parents=True)
    legacy = {
        "profiles": [
            {
                "name": "Legacy",
                "appearance": _serialize_appearance(build_signature_appearance()),
                "placement_defaults": {
                    "width_pt": 120.0,
                    "height_pt": 36.0,
                    "anchor": "bottom_right",
                },
            }
        ]
    }
    store.catalog_path.write_text(json.dumps(legacy), encoding="utf-8")

    catalog = store.load_catalog()

    assert catalog.preset_names() == ("Legacy",)
    assert catalog.appearance_profile_named("Legacy").display_name == "Legacy"
    assert catalog.placement_profiles == ()


def test_appearance_image_fields_round_trip_and_old_payload_defaults() -> None:
    appearance = build_signature_appearance()
    payload = _serialize_appearance(appearance)
    payload["image_prominence"] = SignatureImageProminence.BALANCED.value
    payload["preserve_image_alpha"] = False

    reconstructed = _deserialize_appearance(payload)

    assert reconstructed.image_prominence is SignatureImageProminence.BALANCED
    assert reconstructed.preserve_image_alpha is False

    old_payload = dict(payload)
    old_payload.pop("image_prominence")
    old_payload.pop("preserve_image_alpha")
    legacy = _deserialize_appearance(old_payload)
    assert legacy.image_prominence is SignatureImageProminence.PRIMARY
    assert legacy.preserve_image_alpha is True


def test_catalog_load_rejects_dangling_preset_reference(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    service = ReusableSigningObjects(store)
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    payload = store.load_catalog().to_dict()
    payload["signature_presets"] = [
        {
            "schema_version": 1,
            "signature_preset_id": "preset-dangling",
            "display_name": "Broken",
            "certificate_configuration_id": None,
            "appearance_profile_id": "missing",
            "placement_profile_id": None,
        }
    ]
    store.catalog_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="missing appearance"):
        store.load_catalog()


def test_snapshot_indexes_are_reused_until_refresh_and_resolve_names(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    service = ReusableSigningObjects(store)
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    first = service.snapshot()
    assert service.snapshot() is first
    assert not hasattr(first, "catalog")
    ref = first.resolve_name(ReusableObjectKind.APPEARANCE, "Approval")
    assert ref is not None
    assert service.resolve_name(ReusableObjectKind.APPEARANCE, "Approval") == ref
    refreshed = service.refresh()
    assert refreshed is not first
    assert refreshed.resolve_name(ReusableObjectKind.APPEARANCE, "Approval") == ref


def test_compose_preset_validates_components_before_one_atomic_write(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    service = ReusableSigningObjects(store)
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    committed = service.compose_preset("Contract", "Approval")
    assert committed.name == "Contract"
    assert committed.preset.preset.signature_preset_id
    assert service.snapshot().preset_names == ("Contract",)
    with pytest.raises(ConfigValidationError, match="Placement profile 'Missing'"):
        service.compose_preset("Broken", "Approval", placement_name="Missing")
    assert service.snapshot().preset_names == ("Contract",)
