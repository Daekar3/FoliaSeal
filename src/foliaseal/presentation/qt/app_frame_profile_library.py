"""Settings dialog for inspecting and managing reusable signing objects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.reusable_signing_objects import (
    DeleteObject,
    RenameObject,
    ReusableObjectRef,
    ReusableSigningObjects,
)
from foliaseal.infra.config.schemas import ConfigValidationError


@dataclass(frozen=True)
class ReusableObjectLibraryControls:
    """Widgets exposed by the reusable-signing-object library dialog."""

    dialog: Any
    object_selector: Any
    details_label: Any
    name_input: Any
    rename_button: Any
    delete_button: Any
    create_button: Any
    edit_button: Any
    close_button: Any


class ReusableObjectLibraryDialog:
    """Manage saved appearance, placement, and composed preset objects.

    The dialog delegates queries and mutations to an application boundary. A
    profile rename retains the stable component id, so presets that reference
    it remain valid; deletion is rejected by the catalog when a dependency is
    still present.
    """

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        library: ReusableSigningObjects,
        on_create: Callable[[], bool] | None = None,
        on_edit: Callable[[], bool] | None = None,
    ) -> None:
        self._bindings = bindings
        self._library = library
        self._on_create = on_create
        self._on_edit = on_edit
        self._refs: list[ReusableObjectRef] = []
        self.controls = self._build_controls(parent)
        self.refresh()

    def show(self) -> Any:
        """Show the modeless Library window without blocking the main frame."""
        show = getattr(self.controls.dialog, "show", None)
        if callable(show):
            show()
        raise_window = getattr(self.controls.dialog, "raise_", None)
        if callable(raise_window):
            raise_window()
        activate = getattr(self.controls.dialog, "activateWindow", None)
        if callable(activate):
            activate()
        return self

    def refresh(self) -> None:
        items = self._library.view().all_items
        self._refs = [item.ref for item in items]
        selector = self.controls.object_selector
        clear = getattr(selector, "clear", None)
        if callable(clear):
            clear()
        selector.addItems([item.display_name for item in items])
        set_item_data = getattr(selector, "setItemData", None)
        if callable(set_item_data):
            for index, ref in enumerate(self._refs):
                set_item_data(index, ref)
        self._render_selection()

    def rename_selected(self) -> bool:
        selected = self._selected_object()
        new_name = self.controls.name_input.text().strip()
        if selected is None or not new_name:
            self._show_error("Select a saved object and enter a new name.")
            return False
        ref, name = selected
        try:
            self._library.execute(RenameObject(ref=ref, new_name=new_name))
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        self._set_selector_text(new_name)
        return True

    def delete_selected(self) -> bool:
        selected = self._selected_object()
        if selected is None:
            self._show_error("Select a saved object before deleting it.")
            return False
        ref, _name = selected
        try:
            self._library.execute(DeleteObject(ref=ref))
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        return True

    def _build_controls(self, parent: Any) -> ReusableObjectLibraryControls:
        dialog = self._bindings.q_dialog(parent)
        set_title = getattr(dialog, "setWindowTitle", None)
        if callable(set_title):
            set_title("Manage reusable signing objects")
        layout = self._bindings.q_form_layout(dialog)
        selector = self._bindings.q_combo_box()
        details = self._bindings.q_label("")
        name_input = self._bindings.q_line_edit()
        name_input.setPlaceholderText("New name")
        rename = self._bindings.q_push_button("Rename")
        delete = self._bindings.q_push_button("Delete")
        create = self._bindings.q_push_button("Create in signing workflow")
        edit = self._bindings.q_push_button("Edit in signing workflow")
        close = self._bindings.q_push_button("Close")
        layout.addRow("Saved signing object", selector)
        layout.addRow("References", details)
        layout.addRow("Rename selected object", name_input)
        layout.addRow(rename, delete)
        layout.addRow(create, edit)
        layout.addRow(close)
        selector.currentTextChanged.connect(lambda _value: self._render_selection())
        rename.clicked.connect(self.rename_selected)
        delete.clicked.connect(self.delete_selected)
        if self._on_create is not None:
            create.clicked.connect(self._on_create)
        if self._on_edit is not None:
            edit.clicked.connect(self._on_edit)
        reject = getattr(dialog, "reject", None)
        if callable(reject):
            close.clicked.connect(reject)
        return ReusableObjectLibraryControls(
            dialog=dialog,
            object_selector=selector,
            details_label=details,
            name_input=name_input,
            rename_button=rename,
            delete_button=delete,
            create_button=create,
            edit_button=edit,
            close_button=close,
        )

    def _render_selection(self) -> None:
        selected = self._selected_object()
        if selected is None:
            self.controls.details_label.setText("Select an object to inspect its saved references.")
            return
        ref, name = selected
        item = next(
            (item for item in self._library.view().all_items if item.ref == ref),
            None,
        )
        self.controls.details_label.setText(
            item.details if item is not None else "Saved object is no longer available."
        )
        self.controls.name_input.setText(name)

    def _selected_object(self) -> tuple[ReusableObjectRef, str] | None:
        selector = self.controls.object_selector
        index = getattr(selector, "currentIndex", lambda: -1)()
        if isinstance(index, int) and 0 <= index < len(self._refs):
            return self._refs[index], selector.currentText().strip()
        value = selector.currentText().strip()
        for ref in self._refs:
            item = next((item for item in self._library.view().all_items if item.ref == ref), None)
            if item is not None and item.display_name == value:
                return ref, value
        return None

    def _set_selector_text(self, value: str) -> None:
        setter = getattr(self.controls.object_selector, "setCurrentText", None)
        if callable(setter):
            setter(value)

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Reusable signing object error", message)
