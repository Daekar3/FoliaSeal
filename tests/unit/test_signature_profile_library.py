from pathlib import Path

import pytest

from foliaseal.application.signature_profile_library import SignatureProfileLibrary
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import ConfigValidationError, SignaturePreset
from tests.support.signing_builders import build_signature_appearance


def test_profile_library_owns_reference_safe_management(tmp_path: Path) -> None:
    store = SignaturePresetCatalogStore(storage_dir=tmp_path / "profiles")
    catalog = store.save_appearance_profile("Approval", build_signature_appearance())
    catalog = store.save_placement_profile(
        "Bottom right",
        left_pt=10.0,
        bottom_pt=12.0,
        width_pt=120.0,
        height_pt=36.0,
    )
    appearance = catalog.appearance_profile_named("Approval")
    placement = catalog.placement_profile_named("Bottom right")
    store.save_catalog(
        catalog.upsert_reference_preset(
            SignaturePreset.from_profile_parts(
                display_name="Contract",
                appearance_profile_id=appearance.appearance_profile_id,
                placement_profile_id=placement.placement_profile_id,
            )
        )
    )
    library = SignatureProfileLibrary(store)

    assert library.items()[-1].details == (
        "Appearance: Approval; placement: Bottom right; certificate configuration id: none."
    )
    library.rename("appearance", "Approval", "Approved")

    assert library.items()[-1].details == (
        "Appearance: Approved; placement: Bottom right; certificate configuration id: none."
    )
    with pytest.raises(ConfigValidationError, match="referenced"):
        library.delete("appearance", "Approved")
