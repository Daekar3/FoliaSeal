from foliaseal.application.certificate_models import CertificateCatalog
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
    SavePreset,
)
from foliaseal.presentation.qt.app_frame_profile_library import ReusableObjectLibraryDialog
from foliaseal.presentation.qt.signature_preset_editor_dialog import SignaturePresetEditorDialog
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


def test_document_independent_preset_editor_saves_reference_transaction() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    errors: list[str] = []
    saved: list[bool] = []
    editor = SignaturePresetEditorDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
        on_saved=lambda: saved.append(True),
        on_error=errors.append,
    )
    editor.controls.name_input.setText("Board approval")
    editor.controls.save_button.click()

    assert errors == []
    assert saved == [True]
    assert service.view().preset_names == ("Board approval",)
    assert service.view().presets[0].details.startswith("Appearance: Approval;")


def test_document_independent_preset_editor_edit_preserves_preset_identity() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    service.execute(
        SavePreset(
            "Board approval",
            appearance_profile_id=service.view().appearances[0].ref.object_id,
        )
    )
    original_ref = service.view().presets[0].ref
    editor = SignaturePresetEditorDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
        initial_ref=original_ref,
    )
    editor.controls.name_input.setText("Board approval v2")
    editor.controls.save_button.click()

    assert service.view().presets[0].ref == original_ref
    assert service.view().preset_names == ("Board approval v2",)
