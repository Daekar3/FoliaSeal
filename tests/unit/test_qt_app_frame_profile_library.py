from foliaseal.application.reusable_signing_models import (
    PlacementProfileRect,
    PlacementProfileSourcePage,
    SignaturePresetCatalog,
)
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
    SaveAppearance,
    SavePlacement,
)
from foliaseal.presentation.qt.app_frame_profile_library import ReusableObjectLibraryDialog
from tests.support.signing_builders import build_signature_appearance
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
    assert dialog.controls.edit_placement_button._enabled is False

    service.execute(
        SavePlacement(
            "Board",
            PlacementProfileRect(left_pt=360.0, top_pt=666.0, width_pt=180.0, height_pt=54.0),
            source_page=PlacementProfileSourcePage(612.0, 792.0, 0),
            page_number=3,
        )
    )
    dialog.controls.catalog_selector.setCurrentText("Placements")
    dialog.refresh()
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.edit_placement_button.click()

    assert [profile.display_name for profile in edited] == ["Board"]


def test_library_pin_and_duplicate_controls_use_typed_catalog_commands() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
    )

    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.refresh()
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.pin_button.click()
    dialog.controls.duplicate_button.click()

    rows = service.view().appearances
    assert rows[0].pinned is True
    assert len(rows) == 2
    assert rows[1].pinned is False


def test_library_save_button_commits_explicit_detail_transaction() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
    )
    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.refresh()
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.name_input.setText("Approved")

    assert dialog.controls.save_button.click() is None
    assert service.view().appearance_names == ("Approved",)
