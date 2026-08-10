from foliaseal.application.reusable_signing_models import (
    PlacementProfileRect,
    PlacementProfileSourcePage,
    SignaturePresetCatalog,
)
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
    SavePlacement,
)
from foliaseal.presentation.qt.app_frame_profile_library import ReusableObjectLibraryDialog
from tests.unit.test_qt_signing_shell import _fake_bindings


def test_library_exposes_reachable_create_and_edit_placement_actions() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    created: list[str] = []
    edited = []
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        on_create_placement=lambda: created.append("create") or True,
        on_edit_placement=lambda profile: edited.append(profile) or True,
    )

    dialog.controls.create_placement_button.click()
    assert created == ["create"]
    assert dialog.controls.edit_placement_button._enabled is True

    service.execute(
        SavePlacement(
            "Board",
            PlacementProfileRect(left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0),
            source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
            page_number=3,
        )
    )
    dialog.refresh()
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.edit_placement_button.click()

    assert [profile.display_name for profile in edited] == ["Board"]
