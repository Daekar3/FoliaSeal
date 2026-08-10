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
from foliaseal.application.signature_library_session import CertificateLibraryRef
from foliaseal.presentation.qt.app_frame_profile_library import ReusableObjectLibraryDialog
from foliaseal.presentation.qt.appearance_profile_editor_dialog import AppearanceProfileEditorDialog
from foliaseal.presentation.qt.signature_preset_editor_dialog import SignaturePresetEditorDialog
from tests.support.signing_builders import (
    build_certificate_catalog,
    build_certificate_configuration,
    build_signature_appearance,
)
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


def test_document_independent_appearance_editor_saves_without_active_document() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    errors: list[str] = []
    editor = AppearanceProfileEditorDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        on_error=errors.append,
    )
    editor.controls.name_input.setText("Board appearance")
    editor.controls.setup_form.appearance_controls.signer_label_prefix.setText("Signed by Board")
    editor.controls.save_button.click()

    assert errors == []
    assert service.view().appearance_names == ("Board appearance",)
    profile = service.resolve(service.view().appearances[0].ref)
    assert profile.appearance.signer_label_prefix == "Signed by Board"


def test_document_independent_appearance_editor_edit_preserves_identity_and_cancel_isolation(
) -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    original = service.view().appearances[0]
    editor = AppearanceProfileEditorDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        initial_ref=original.ref,
    )
    editor.controls.name_input.setText("Approved")
    editor.controls.setup_form.appearance_controls.signer_label_prefix.setText("Changed")
    editor.controls.cancel_button.click()

    assert service.view().appearances[0] == original

    editor = AppearanceProfileEditorDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        initial_ref=original.ref,
    )
    editor.controls.name_input.setText("Approved")
    editor.controls.setup_form.appearance_controls.signer_label_prefix.setText("Changed")
    editor.controls.save_button.click()

    updated = service.view().appearances[0]
    profile = service.resolve(updated.ref)
    assert updated.ref == original.ref
    assert updated.display_name == "Approved"
    assert profile.appearance.signer_label_prefix == "Changed"


def test_library_exposes_appearance_create_and_edit_actions() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    created: list[str] = []
    edited: list[str] = []
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        on_create_appearance=lambda: created.append("create") or True,
        on_edit_appearance=lambda ref: edited.append(ref.object_id) or True,
    )

    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.controls.create_button.click()
    assert created == ["create"]

    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    dialog.refresh()
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.edit_button.click()
    assert edited == [service.view().appearances[0].ref.object_id]


def test_library_owns_nested_appearance_editor_and_discards_dirty_child() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
    )

    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.controls.create_button.click()
    editor = dialog.controls.appearance_editor
    assert editor is not None
    assert dialog.controls.detail_view.visible is False
    assert dialog.controls.appearance_editor_host.visible is True
    assert (
        "Signature Library / Appearances / New appearance"
        in editor.controls.breadcrumb_label.text()
    )
    assert "Sample preview (synthetic data" in editor.controls.sample_preview_label.text()

    editor.controls.name_input.setText("Discarded appearance")
    assert editor.dirty is True
    bindings.q_message_box.next_result = bindings.q_message_box.Discard
    editor.controls.cancel_button.click()

    assert dialog.controls.appearance_editor is None
    assert service.view().appearance_names == ()
    assert dialog.controls.detail_view.visible is True


def test_nested_appearance_editor_save_preserves_identity_and_preview_is_not_persisted() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    original_ref = service.view().appearances[0].ref
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
    )

    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.edit_button.click()
    editor = dialog.controls.appearance_editor
    assert editor is not None
    assert "Sample signer: Ada Example" in editor.controls.sample_preview_label.text()
    editor.controls.name_input.setText("Approved")
    editor.controls.setup_form.appearance_controls.signer_label_prefix.setText("Signed by Board")
    editor.controls.save_button.click()

    assert dialog.controls.appearance_editor is None
    updated = service.view().appearances[0]
    assert updated.ref == original_ref
    assert updated.display_name == "Approved"
    profile = service.resolve(original_ref)
    assert profile.appearance.signer_label_prefix == "Signed by Board"
    assert "Ada Example" not in str(profile.appearance)


def test_nested_appearance_editor_continue_keeps_dirty_child_until_discard() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
    )

    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.controls.object_selector.setCurrentIndex(0)
    dialog.controls.edit_button.click()
    editor = dialog.controls.appearance_editor
    assert editor is not None
    editor.controls.name_input.setText("Unsaved")

    bindings.q_message_box.next_result = bindings.q_message_box.Cancel
    editor.controls.cancel_button.click()
    assert dialog.controls.appearance_editor is editor
    assert editor.dirty is True

    bindings.q_message_box.next_result = bindings.q_message_box.Discard
    editor.controls.cancel_button.click()
    assert dialog.controls.appearance_editor is None
    assert service.view().appearance_names == ("Approval",)


def test_nested_appearance_editor_removes_old_widget_on_reopen() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
    )
    dialog.controls.catalog_selector.setCurrentText("Appearances")

    for _ in range(3):
        dialog.controls.create_button.click()
        editor = dialog.controls.appearance_editor
        assert editor is not None
        editor.controls.cancel_button.click()

    assert dialog.controls.appearance_editor is None
    assert dialog._appearance_editor_host_layout.items == []  # noqa: SLF001


def test_nested_appearance_editor_restores_parent_catalog_selection_and_draft() -> None:
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
    dialog.controls.object_selector.setCurrentIndex(0)
    parent_ref = dialog._session.selected_ref  # noqa: SLF001
    dialog.controls.name_input.setText("Parent draft")
    dialog.controls.create_button.click()
    assert dialog.controls.appearance_editor is not None

    dialog.controls.appearance_editor.controls.cancel_button.click()

    assert dialog._session.catalog.value == "Appearances"  # noqa: SLF001
    assert dialog._session.selected_ref == parent_ref  # noqa: SLF001
    assert dialog._session.draft_name == "Parent draft"  # noqa: SLF001


def test_nested_preset_editor_creates_appearance_and_returns_stable_reference() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
    )

    dialog.controls.catalog_selector.setCurrentText("Presets")
    dialog.controls.create_button.click()
    preset_editor = dialog.controls.preset_editor
    assert preset_editor is not None
    assert (
        "Signature Library / Presets / New preset"
        in preset_editor.controls.breadcrumb_label.text()
    )

    preset_editor.controls.name_input.setText("Board approval")
    preset_editor.controls.create_appearance_button.click()
    appearance_editor = preset_editor.appearance_child
    assert appearance_editor is not None
    assert "Appearance / New appearance" in appearance_editor.controls.breadcrumb_label.text()
    appearance_editor.controls.name_input.setText("Board appearance")
    appearance_editor.controls.save_button.click()

    assert preset_editor.appearance_child is None
    assert preset_editor.controls.appearance_selector.currentText() == "Board appearance"
    preset_editor.controls.save_button.click()

    assert dialog.controls.preset_editor is None
    assert service.view().appearance_names == ("Board appearance",)
    assert service.view().preset_names == ("Board approval",)
    resolved = service.resolve(service.view().presets[0].ref)
    assert resolved.preset.appearance_profile_id == service.view().appearances[0].ref.object_id


def test_nested_preset_child_discard_leaves_parent_and_catalog_unchanged() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
    )
    dialog.controls.catalog_selector.setCurrentText("Presets")
    dialog.controls.create_button.click()
    preset_editor = dialog.controls.preset_editor
    assert preset_editor is not None
    preset_editor.controls.name_input.setText("Discarded preset")
    preset_editor.controls.create_appearance_button.click()
    appearance_editor = preset_editor.appearance_child
    assert appearance_editor is not None
    appearance_editor.controls.name_input.setText("Discarded appearance")

    bindings.q_message_box.next_result = bindings.q_message_box.Discard
    appearance_editor.controls.cancel_button.click()

    assert preset_editor.appearance_child is None
    assert preset_editor.controls.appearance_selector.count() == 0
    assert service.view().appearance_names == ()
    assert service.view().preset_names == ()


def test_nested_preset_parent_back_resolves_save_discard_and_continue() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
    )
    dialog.controls.catalog_selector.setCurrentText("Presets")
    dialog.controls.create_button.click()
    editor = dialog.controls.preset_editor
    assert editor is not None
    editor.controls.appearance_selector.setCurrentIndex(0)
    editor.controls.name_input.setText("Saved preset")

    bindings.q_message_box.next_result = bindings.q_message_box.Cancel
    editor.controls.cancel_button.click()
    assert dialog.controls.preset_editor is editor
    assert editor.dirty is True

    bindings.q_message_box.next_result = bindings.q_message_box.Save
    editor.controls.cancel_button.click()
    assert dialog.controls.preset_editor is None
    assert service.view().preset_names == ("Saved preset",)


def test_nested_preset_close_resolves_dirty_child_before_parent_and_cleans_widgets() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
    )
    dialog.controls.catalog_selector.setCurrentText("Presets")

    for _ in range(3):
        dialog.controls.create_button.click()
        editor = dialog.controls.preset_editor
        assert editor is not None
        editor.controls.create_appearance_button.click()
        child = editor.appearance_child
        assert child is not None
        child.controls.name_input.setText("Unsaved appearance")
        bindings.q_message_box.next_result = bindings.q_message_box.Cancel
        dialog.controls.close_button.click()
        assert dialog.controls.preset_editor is editor
        assert editor.appearance_child is child
        bindings.q_message_box.next_result = bindings.q_message_box.Discard
        dialog.controls.close_button.click()
        assert dialog.controls.preset_editor is None

    assert dialog._appearance_editor_host_layout.items == []  # noqa: SLF001


def test_nested_preset_catalog_switch_resolves_child_then_parent() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
        certificate_catalog=CertificateCatalog(schema_version=1),
    )
    dialog.controls.catalog_selector.setCurrentText("Presets")
    dialog.controls.create_button.click()
    editor = dialog.controls.preset_editor
    assert editor is not None
    editor.controls.name_input.setText("Unsaved preset")
    editor.controls.create_appearance_button.click()
    child = editor.appearance_child
    assert child is not None
    child.controls.name_input.setText("Unsaved appearance")

    bindings.q_message_box.next_result = bindings.q_message_box.Cancel
    dialog.controls.catalog_selector.setCurrentText("Placements")
    assert dialog.controls.preset_editor is editor
    assert dialog._session.catalog.value == "Presets"  # noqa: SLF001

    bindings.q_message_box.next_result = bindings.q_message_box.Discard
    dialog.controls.catalog_selector.setCurrentText("Placements")
    assert dialog.controls.preset_editor is None
    assert dialog._session.catalog.value == "Placements"  # noqa: SLF001


def test_library_exposes_configure_action_for_retained_certificate() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    configured: list[CertificateLibraryRef] = []
    catalog = build_certificate_catalog(certificate_configurations=())
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        certificate_catalog=catalog,
        on_configure_certificate=lambda ref: configured.append(ref) or True,
    )

    dialog.controls.catalog_selector.setCurrentText("Certificates")
    dialog.refresh()
    dialog.controls.object_selector.setCurrentIndex(0)

    assert dialog.controls.edit_button._text == "Configure certificate"
    assert dialog.controls.edit_button._enabled is True
    dialog.controls.edit_button.click()

    assert configured == [CertificateLibraryRef("managed-cert-default")]


def test_library_refreshes_retained_certificate_row_after_configuration() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    managed = build_certificate_catalog(certificate_configurations=())
    configured = build_certificate_catalog(
        managed_certificates=managed.managed_certificates,
        certificate_configurations=(
            build_certificate_configuration(
                managed_certificate_id=managed.managed_certificates[0].managed_certificate_id
            ),
        ),
    )
    current = [managed]

    def configure(_ref: CertificateLibraryRef) -> bool:
        current[0] = configured
        return True

    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        certificate_catalog=managed,
        certificate_catalog_provider=lambda: current[0],
        on_configure_certificate=configure,
    )
    dialog.controls.catalog_selector.setCurrentText("Certificates")
    dialog.controls.object_selector.setCurrentIndex(0)

    assert dialog.controls.edit_button.click() is None
    assert dialog._rows[0].configured is True  # noqa: SLF001 - verifies the public row refresh
    assert "Configured signing certificate" in dialog.controls.details_label.text()


def test_library_delete_requires_confirmation_before_mutating_reusable_object() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    service.execute(SaveAppearance("Approval", build_signature_appearance()))
    bindings = _fake_bindings()
    dialog = ReusableObjectLibraryDialog(bindings=bindings, parent=None, library=service)
    dialog.controls.catalog_selector.setCurrentText("Appearances")
    dialog.controls.object_selector.setCurrentIndex(0)

    bindings.q_message_box.next_result = bindings.q_message_box.No
    assert dialog.delete_selected() is False
    assert service.view().appearance_names == ("Approval",)
    assert bindings.q_message_box.calls[-1][1:] == (
        "Delete saved object?",
        "Delete saved object 'Approval'?",
    )

    bindings.q_message_box.next_result = bindings.q_message_box.Yes
    assert dialog.delete_selected() is True
    assert service.view().appearance_names == ()


def test_library_delete_confirmation_gates_certificate_callback() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    bindings = _fake_bindings()
    deleted: list[CertificateLibraryRef] = []
    dialog = ReusableObjectLibraryDialog(
        bindings=bindings,
        parent=None,
        library=service,
        certificate_catalog=build_certificate_catalog(certificate_configurations=()),
        on_delete_certificate=lambda ref: deleted.append(ref) or True,
    )
    dialog.controls.catalog_selector.setCurrentText("Certificates")
    dialog.controls.object_selector.setCurrentIndex(0)

    bindings.q_message_box.next_result = bindings.q_message_box.No
    assert dialog.delete_selected() is False
    assert deleted == []

    bindings.q_message_box.next_result = bindings.q_message_box.Yes
    assert dialog.delete_selected() is True
    assert deleted == [CertificateLibraryRef("managed-cert-default")]


def test_library_expiration_sort_propagates_persisted_preference() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    preferences: list[tuple[str, str]] = []
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
        on_preferences_changed=lambda catalog, sort: preferences.append((catalog, sort)),
    )

    dialog.controls.catalog_selector.setCurrentText("Certificates")
    dialog.controls.sort_selector.setCurrentIndex(2)

    assert preferences[-1] == ("Certificates", "expiration_soonest")


def test_library_exposes_expiration_sort_choice() -> None:
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    dialog = ReusableObjectLibraryDialog(
        bindings=_fake_bindings(),
        parent=None,
        library=service,
    )

    assert dialog.controls.sort_selector._items == [
        "Name A–Z",
        "Name Z–A",
        "Expiration soonest",
    ]
