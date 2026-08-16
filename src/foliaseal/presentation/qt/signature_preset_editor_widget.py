"""Library detail editor for reference-only Signature Presets."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.reusable_signing_models import PlacementProfile, ResolvedSignaturePreset
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectKind,
    ReusableObjectRef,
    ReusableSigningObjects,
    SavePreset,
)
from foliaseal.application.signature_image_import import ManagedSignatureImageStore
from foliaseal.infra.config.schemas import ConfigValidationError
from foliaseal.presentation.qt.appearance_profile_editor_widget import (
    AppearanceProfileEditorWidget,
)


@dataclass(frozen=True)
class SignaturePresetEditorWidgetControls:
    """Public controls for the nested Library Preset editor."""

    container: Any
    breadcrumb_label: Any
    name_input: Any
    appearance_selector: Any
    placement_selector: Any
    certificate_selector: Any
    create_appearance_button: Any
    edit_appearance_button: Any
    create_placement_button: Any
    save_button: Any
    cancel_button: Any
    child_host: Any


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


class SignaturePresetEditorWidget:
    """Own an isolated preset draft and one explicit Appearance child session."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        library: ReusableSigningObjects,
        certificate_catalog: CertificateCatalog,
        initial_ref: ReusableObjectRef | None = None,
        breadcrumb: str = "Signature Library / Presets",
        on_saved: Callable[[], None] | None = None,
        on_reusable_objects_changed: Callable[[], None] | None = None,
        on_cancel_requested: Callable[[], bool] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_create_placement: Callable[[], PlacementProfile | None] | None = None,
        image_store: ManagedSignatureImageStore | None = None,
    ) -> None:
        self._bindings = bindings
        self._library = library
        self._certificate_catalog = certificate_catalog
        self._initial_ref = initial_ref
        self._breadcrumb = breadcrumb
        self._on_saved = on_saved or (lambda: None)
        self._on_reusable_objects_changed = on_reusable_objects_changed or (lambda: None)
        self._on_cancel_requested = on_cancel_requested or (lambda: True)
        self._on_error = on_error or (lambda _message: None)
        self._on_create_placement = on_create_placement
        self._image_store = image_store
        self._suspend_updates = True
        self._dirty = False
        self._saved_ref: ReusableObjectRef | None = None
        self._appearance_child: AppearanceProfileEditorWidget | None = None
        self._original_name = ""
        self._original_appearance_id: str | None = None
        self._original_placement_id: str | None = None
        self._original_certificate_id: str | None = None
        self.controls = self._build_controls(parent)
        self._suspend_updates = False

    @property
    def dirty(self) -> bool:
        return self._dirty

    @property
    def saved_ref(self) -> ReusableObjectRef | None:
        return self._saved_ref

    @property
    def child_active(self) -> bool:
        return self._appearance_child is not None

    @property
    def appearance_child(self) -> AppearanceProfileEditorWidget | None:
        return self._appearance_child

    def save(self) -> bool:
        """Commit the parent preset draft after any child session has returned."""

        if self._appearance_child is not None:
            if not self.resolve_child():
                return False
        name = str(self.controls.name_input.text()).strip()
        appearance_id = self._current_data(self.controls.appearance_selector)
        if not name:
            self._on_error("Preset name is required.")
            return False
        if not appearance_id:
            self._on_error("A signature preset must reference an appearance.")
            return False
        overwrite = self._initial_ref is not None
        if (
            not overwrite
            and self._library.resolve_name(ReusableObjectKind.PRESET, name) is not None
        ):
            message_box = getattr(self._bindings, "q_message_box", None)
            question = getattr(message_box, "question", None)
            yes = getattr(message_box, "Yes", None)
            if callable(question):
                result = question(
                    self.controls.container,
                    "Replace signature preset?",
                    f"Signature preset '{name}' already exists. Replace it?",
                )
                if result == yes:
                    overwrite = True
                else:
                    return False
            else:
                self._on_error(f"Signature preset '{name}' already exists.")
                return False
        try:
            self._library.execute(
                SavePreset(
                    name=name,
                    appearance_profile_id=str(appearance_id),
                    placement_profile_id=self._string_data(self.controls.placement_selector),
                    certificate_configuration_id=self._string_data(
                        self.controls.certificate_selector
                    ),
                    signature_preset_id=(
                        None if self._initial_ref is None else self._initial_ref.object_id
                    ),
                    overwrite=overwrite,
                )
            )
        except (ConfigValidationError, KeyError, ValueError) as exc:
            self._on_error(str(exc))
            return False
        self._saved_ref = self._library.resolve_name(ReusableObjectKind.PRESET, name)
        self._dirty = False
        self._on_saved()
        return True

    def request_cancel(self) -> bool:
        """Resolve the child first, then ask the Library to resolve the parent."""

        if self._appearance_child is not None and not self.resolve_child():
            return False
        return bool(self._on_cancel_requested())

    def resolve_child(self) -> bool:
        """Resolve the nested Appearance child with Save/Discard/Continue."""

        child = self._appearance_child
        if child is None:
            return True
        if not child.dirty:
            self._leave_appearance_child()
            return True
        message_box = getattr(self._bindings, "q_message_box", None)
        question = getattr(message_box, "question", None)
        save = getattr(message_box, "Save", None)
        discard = getattr(message_box, "Discard", None)
        continue_editing = getattr(message_box, "Cancel", None)
        standard_button = getattr(message_box, "StandardButton", None)
        if standard_button is not None:
            save = save if save is not None else getattr(standard_button, "Save", None)
            discard = discard if discard is not None else getattr(standard_button, "Discard", None)
            continue_editing = (
                continue_editing
                if continue_editing is not None
                else getattr(standard_button, "Cancel", None)
            )
        if not callable(question) or save is None or discard is None or continue_editing is None:
            self._on_error("Unable to resolve unsaved Appearance changes; continue editing.")
            return False
        try:
            result = question(
                self.controls.container,
                "Unsaved appearance changes",
                "Save changes, discard them, or continue editing?",
                save | discard | continue_editing,
                continue_editing,
            )
        except TypeError:
            result = question(
                self.controls.container,
                "Unsaved appearance changes",
                "Save changes, discard them, or continue editing?",
            )
        if result == save:
            return child.save()
        if result == discard:
            self._leave_appearance_child()
            return True
        return False

    def _build_controls(self, parent: Any) -> SignaturePresetEditorWidgetControls:
        bindings = self._bindings
        container = bindings.q_widget(parent)
        layout = bindings.q_vbox_layout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        breadcrumb = bindings.q_label(self._breadcrumb)
        layout.addWidget(breadcrumb)
        name_input = bindings.q_line_edit()
        name_input.setPlaceholderText("Preset name")
        layout.addWidget(bindings.q_label("Name"))
        layout.addWidget(name_input)

        appearance_selector = bindings.q_combo_box()
        placement_selector = bindings.q_combo_box()
        certificate_selector = bindings.q_combo_box()
        self._populate_selectors(
            appearance_selector,
            placement_selector,
            certificate_selector,
            name_input,
        )
        layout.addWidget(bindings.q_label("Appearance"))
        layout.addWidget(appearance_selector)
        create_appearance = bindings.q_push_button("Create appearance…")
        edit_appearance = bindings.q_push_button("Edit appearance…")
        layout.addWidget(_compose_row(bindings, create_appearance, edit_appearance))
        layout.addWidget(bindings.q_label("Placement"))
        layout.addWidget(placement_selector)
        create_placement = bindings.q_push_button("Create placement…")
        if self._on_create_placement is None:
            create_placement.setEnabled(False)
        layout.addWidget(create_placement)
        layout.addWidget(bindings.q_label("Certificate"))
        layout.addWidget(certificate_selector)
        helper = bindings.q_label(
            "Presets reference reusable objects. Saving here never changes the active document."
        )
        if hasattr(helper, "setWordWrap"):
            helper.setWordWrap(True)
        layout.addWidget(helper)

        child_host = bindings.q_widget()
        child_layout = bindings.q_vbox_layout(child_host)
        child_layout.setContentsMargins(0, 0, 0, 0)
        child_layout.setSpacing(4)
        layout.addWidget(child_host)
        set_visible = getattr(child_host, "setVisible", None)
        if callable(set_visible):
            set_visible(False)

        save_button = bindings.q_push_button("Save")
        cancel_button = bindings.q_push_button("Back")
        layout.addWidget(_compose_row(bindings, cancel_button, save_button))

        name_input.textChanged.connect(self._mark_dirty)  # type: ignore[attr-defined]
        appearance_selector.currentIndexChanged.connect(self._mark_dirty)  # type: ignore[attr-defined]
        placement_selector.currentIndexChanged.connect(self._mark_dirty)  # type: ignore[attr-defined]
        certificate_selector.currentIndexChanged.connect(self._mark_dirty)  # type: ignore[attr-defined]
        create_appearance.clicked.connect(self._create_appearance_child)  # type: ignore[attr-defined]
        edit_appearance.clicked.connect(self._edit_appearance_child)  # type: ignore[attr-defined]
        create_placement.clicked.connect(self._create_placement)  # type: ignore[attr-defined]
        save_button.clicked.connect(self.save)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(self.request_cancel)  # type: ignore[attr-defined]
        return SignaturePresetEditorWidgetControls(
            container=container,
            breadcrumb_label=breadcrumb,
            name_input=name_input,
            appearance_selector=appearance_selector,
            placement_selector=placement_selector,
            certificate_selector=certificate_selector,
            create_appearance_button=create_appearance,
            edit_appearance_button=edit_appearance,
            create_placement_button=create_placement,
            save_button=save_button,
            cancel_button=cancel_button,
            child_host=child_host,
        )

    def _populate_selectors(
        self,
        appearance_selector: Any,
        placement_selector: Any,
        certificate_selector: Any,
        name_input: Any,
    ) -> None:
        snapshot = self._library.snapshot()
        for item in snapshot.appearances:
            self._add_item(appearance_selector, item.display_name, item.ref.object_id)
        self._populate_placement_selector(placement_selector)
        self._add_item(certificate_selector, "No certificate", None)
        for item in self._certificate_catalog.certificate_configurations:
            self._add_item(
                certificate_selector,
                item.display_name,
                item.certificate_configuration_id,
            )
        if self._initial_ref is None:
            return
        resolved = self._library.resolve(self._initial_ref)
        if not isinstance(resolved, ResolvedSignaturePreset):
            raise ConfigValidationError("Select a signature preset to edit.")
        self._original_name = resolved.name
        self._original_appearance_id = resolved.preset.appearance_profile_id
        self._original_placement_id = resolved.preset.placement_profile_id
        self._original_certificate_id = resolved.preset.certificate_configuration_id
        name_input.setText(resolved.name)
        self._set_selector_data(appearance_selector, self._original_appearance_id)
        self._set_selector_data(placement_selector, self._original_placement_id)
        self._set_selector_data(certificate_selector, self._original_certificate_id)

    def _create_appearance_child(self) -> bool:
        return self._open_appearance_child(None)

    def _create_placement(self) -> bool:
        """Create a reusable placement and attach it to this suspended draft."""
        callback = self._on_create_placement
        if callback is None:
            self._on_error("Placement creation is unavailable.")
            return False
        self._set_parent_editor_visible(False)
        try:
            created = callback()
        finally:
            self._set_parent_editor_visible(True)
        if not isinstance(created, PlacementProfile):
            return False
        placement_id = getattr(created, "placement_profile_id", None)
        self._populate_placement_selector(self.controls.placement_selector, placement_id)
        self._dirty = True
        self._on_reusable_objects_changed()
        return True

    def _edit_appearance_child(self) -> bool:
        appearance_id = self._string_data(self.controls.appearance_selector)
        if appearance_id is None:
            self._on_error("Select an appearance before editing it.")
            return False
        return self._open_appearance_child(
            ReusableObjectRef(ReusableObjectKind.APPEARANCE, appearance_id)
        )

    def _open_appearance_child(self, initial_ref: ReusableObjectRef | None) -> bool:
        if self._appearance_child is not None:
            return False
        child = AppearanceProfileEditorWidget(
            bindings=self._bindings,
            parent=self.controls.child_host,
            library=self._library,
            initial_ref=initial_ref,
            breadcrumb=(
                self._breadcrumb
                + " / Appearance / "
                + ("New appearance" if initial_ref is None else "Edit appearance")
            ),
            on_saved=self._appearance_child_saved,
            on_cancel_requested=self._appearance_child_cancel_requested,
            on_error=self._on_error,
            image_store=self._image_store,
        )
        self._appearance_child = child
        self.controls.child_host.setVisible(True)
        self._set_parent_editor_visible(False)
        child_layout = self.controls.child_host.layout
        if child_layout is not None:
            child_layout.addWidget(child.controls.container)
        return True

    def _appearance_child_saved(self) -> None:
        child = self._appearance_child
        saved_ref = None if child is None else child.saved_ref
        self._refresh_appearance_selector(saved_ref)
        self._leave_appearance_child()
        self._dirty = True
        self._on_reusable_objects_changed()

    def _appearance_child_cancel_requested(self) -> None:
        self.resolve_child()

    def _leave_appearance_child(self) -> None:
        child = self._appearance_child
        if child is not None:
            child.discard_staged_images()
            remove_widget = getattr(self.controls.child_host.layout, "removeWidget", None)
            if callable(remove_widget):
                remove_widget(child.controls.container)
            set_visible = getattr(child.controls.container, "setVisible", None)
            if callable(set_visible):
                set_visible(False)
            delete_later = getattr(child.controls.container, "deleteLater", None)
            if callable(delete_later):
                delete_later()
        self._appearance_child = None
        self.controls.child_host.setVisible(False)
        self._set_parent_editor_visible(True)

    def _set_parent_editor_visible(self, visible: bool) -> None:
        layout = self.controls.container.layout
        if layout is None:
            return
        for item in getattr(layout, "items", ()):
            widget = item[0] if isinstance(item, tuple) else None
            if widget is not None and widget is not self.controls.child_host:
                setter = getattr(widget, "setVisible", None)
                if callable(setter):
                    setter(visible)

    def _refresh_appearance_selector(self, selected_ref: ReusableObjectRef | None) -> None:
        selector = self.controls.appearance_selector
        clear = getattr(selector, "clear", None)
        if callable(clear):
            clear()
        if hasattr(selector, "_foliaseal_data"):
            setattr(selector, "_foliaseal_data", {})
        for item in self._library.view().appearances:
            self._add_item(selector, item.display_name, item.ref.object_id)
        if selected_ref is not None:
            self._set_selector_data(selector, selected_ref.object_id)

    def _populate_placement_selector(
        self,
        selector: Any,
        selected_id: str | None = None,
    ) -> None:
        clear = getattr(selector, "clear", None)
        if callable(clear):
            clear()
        if hasattr(selector, "_foliaseal_data"):
            setattr(selector, "_foliaseal_data", {})
        self._add_item(selector, "No placement", None)
        for item in self._library.view().placements:
            self._add_item(selector, item.display_name, item.ref.object_id)
        if selected_id is not None:
            self._set_selector_data(selector, selected_id)

    def _mark_dirty(self, *_args: object) -> None:
        if not self._suspend_updates:
            self._dirty = True

    def _set_selector_data(self, selector: Any, value: str | None) -> None:
        if value is None:
            return
        for index in range(int(selector.count())):
            if self._item_data(selector, index) == value:
                selector.setCurrentIndex(index)
                return

    def _add_item(self, selector: Any, label: str, value: str | None) -> None:
        try:
            selector.addItem(label, value)
        except TypeError:
            selector.addItem(label)
            data = getattr(selector, "_foliaseal_data", {})
            data[len(data)] = value
            setattr(selector, "_foliaseal_data", data)

    def _item_data(self, selector: Any, index: int) -> Any:
        getter = getattr(selector, "itemData", None)
        if callable(getter):
            return getter(index)
        return getattr(selector, "_foliaseal_data", {}).get(index)

    def _current_data(self, selector: Any) -> Any:
        getter = getattr(selector, "currentData", None)
        if callable(getter):
            return getter()
        index_getter = getattr(selector, "currentIndex", None)
        if callable(index_getter):
            index = int(index_getter())
            return self._item_data(selector, index) if index >= 0 else None
        text = str(getattr(selector, "currentText", lambda: "")())
        find_text = getattr(selector, "findText", None)
        if callable(find_text):
            index = int(find_text(text))
            return self._item_data(selector, index) if index >= 0 else None
        return None

    def _string_data(self, selector: Any) -> str | None:
        value = self._current_data(selector)
        return None if value is None else str(value)


__all__ = ["SignaturePresetEditorWidget", "SignaturePresetEditorWidgetControls"]
