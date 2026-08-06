from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from foliaseal.application.reusable_signing_models import (
    AppearanceProfile,
    PlacementProfile,
    PlacementProfileRect,
    SignaturePreset,
    SignaturePresetCatalog,
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
        schema_version=1,
        placement_profile_id="placement-approval",
        display_name="Approval placement",
        page_selection_mode="current_page",
        rect=PlacementProfileRect(left_pt=10, bottom_pt=20, width_pt=180, height_pt=60),
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
