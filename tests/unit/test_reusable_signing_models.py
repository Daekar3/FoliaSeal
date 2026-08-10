from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from foliaseal.application.reusable_signing_models import (
    AppearanceProfile,
    PlacementProfile,
    PlacementProfileRect,
    PlacementProfileSourcePage,
    ReusableObjectValidationError,
    SignaturePreset,
    SignaturePresetCatalog,
    migrate_legacy_placement_payload,
)
from tests.support.signing_builders import build_signature_appearance


def test_application_models_round_trip_without_infra_schema_import() -> None:
    appearance = AppearanceProfile(
        schema_version=1,
        appearance_profile_id="appearance-approval",
        display_name="Approval",
        appearance=build_signature_appearance(),
    )
    placement = PlacementProfile(
        schema_version=2,
        placement_profile_id="placement-approval",
        display_name="Approval placement",
        pinned=False,
        page_number=1,
        source_page=PlacementProfileSourcePage(
            visible_width_pt=612.0,
            visible_height_pt=792.0,
            rotation_degrees=0,
        ),
        rect=PlacementProfileRect(left_pt=10, top_pt=712, width_pt=180, height_pt=60),
    )
    catalog = SignaturePresetCatalog(
        schema_version=1,
        appearance_profiles=(appearance,),
        placement_profiles=(placement,),
        signature_presets=(
            SignaturePreset.from_profile_parts(
                display_name="Approval",
                appearance_profile_id=appearance.appearance_profile_id,
                placement_profile_id=placement.placement_profile_id,
            ),
        ),
    )
    assert SignaturePresetCatalog.from_dict(catalog.to_dict()) == catalog
    assert catalog.preset_named("Approval").appearance == appearance.appearance


def test_placement_profile_v2_round_trip_uses_visible_top_left_geometry() -> None:
    profile = PlacementProfile(
        schema_version=2,
        placement_profile_id="placement-board",
        display_name="Board",
        pinned=True,
        page_number=3,
        source_page=PlacementProfileSourcePage(
            visible_width_pt=792.0,
            visible_height_pt=612.0,
            rotation_degrees=90,
        ),
        rect=PlacementProfileRect(left_pt=360.0, top_pt=420.0, width_pt=180.0, height_pt=54.0),
    )

    payload = profile.to_dict()

    assert payload == {
        "schema_version": 2,
        "placement_profile_id": "placement-board",
        "display_name": "Board",
        "pinned": True,
        "page_number": 3,
        "source_page": {
            "visible_width_pt": 792.0,
            "visible_height_pt": 612.0,
            "rotation_degrees": 90,
        },
        "rect": {
            "left_pt": 360.0,
            "top_pt": 420.0,
            "width_pt": 180.0,
            "height_pt": 54.0,
        },
    }
    assert PlacementProfile.from_dict(payload) == profile


def test_context_free_legacy_placement_payload_is_rejected() -> None:
    legacy = {
        "schema_version": 1,
        "placement_profile_id": "placement-old",
        "display_name": "Old",
        "page_selection_mode": "current_page",
        "rect": {"left_pt": 10.0, "bottom_pt": 20.0, "width_pt": 180.0, "height_pt": 60.0},
        "numeric_fine_tuning_enabled": True,
    }

    with pytest.raises(ReusableObjectValidationError, match="migration context"):
        PlacementProfile.from_dict(legacy)


def test_legacy_placement_migration_converts_bottom_left_with_explicit_context() -> None:
    legacy = {
        "schema_version": 1,
        "placement_profile_id": "placement-old",
        "display_name": "Old",
        "page_selection_mode": "current_page",
        "rect": {"left_pt": 10.0, "bottom_pt": 20.0, "width_pt": 180.0, "height_pt": 60.0},
        "numeric_fine_tuning_enabled": True,
    }

    migrated = migrate_legacy_placement_payload(
        legacy,
        source_page=PlacementProfileSourcePage(
            visible_width_pt=612.0, visible_height_pt=792.0, rotation_degrees=0
        ),
        page_number=2,
    )

    assert migrated.schema_version == 2
    assert migrated.page_number == 2
    assert migrated.rect == PlacementProfileRect(
        left_pt=10.0, top_pt=712.0, width_pt=180.0, height_pt=60.0
    )
    assert "page_selection_mode" not in migrated.to_dict()
    assert "bottom_pt" not in migrated.to_dict()["rect"]

    source_root = Path(__file__).parents[2] / "src"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(source_root), environment.get("PYTHONPATH", ""))
    )
    script = (
        "import sys; "
        "import foliaseal.application.reusable_signing_models; "
        "assert not any(name == 'foliaseal.infra.config.schemas' or "
        "name.startswith('foliaseal.infra.config.schemas.') for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", script], env=environment, check=True)
