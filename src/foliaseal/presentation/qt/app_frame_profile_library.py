"""Settings dialog for inspecting and managing reusable signing objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from foliaseal.application.signature_profile_library import SignatureProfileLibrary
from foliaseal.infra.config.schemas import ConfigValidationError


@dataclass(frozen=True)
class SignatureProfileLibraryControls:
    """Widgets exposed by the reusable-signing-object library dialog."""

    dialog: Any
    object_selector: Any
    details_label: Any
    name_input: Any
    rename_button: Any
    delete_button: Any
    close_button: Any


class SignatureProfileLibraryDialog:
    """Manage saved appearance, placement, and composed preset objects.

    The dialog delegates queries and mutations to an application boundary. A
    profile rename retains the stable component id, so presets that reference
    it remain valid; deletion is rejected by the catalog when a dependency is
    still present.
    """

    _APPEARANCE_PREFIX = "Appearance: "
    _PLACEMENT_PREFIX = "Placement: "
    _PRESET_PREFIX = "Preset: "

    def __init__(self, *, bindings: Any, parent: Any, library: SignatureProfileLibrary) -> None:
        self._bindings = bindings
        self._library = library
        self.controls = self._build_controls(parent)
        self.refresh()

    def exec(self) -> Any:
        execute = getattr(self.controls.dialog, "exec", None)
        return execute() if callable(execute) else None

    def refresh(self) -> None:
        items = self._library.items()
        selector = self.controls.object_selector
        clear = getattr(selector, "clear", None)
        if callable(clear):
            clear()
        selector.addItems(
            [self._prefix_for(item.kind) + item.display_name for item in items]
        )
        self._render_selection()

    def rename_selected(self) -> bool:
        selected = self._selected_object()
        new_name = self.controls.name_input.text().strip()
        if selected is None or not new_name:
            self._show_error("Select a saved object and enter a new name.")
            return False
        kind, name = selected
        try:
            self._library.rename(kind, name, new_name)
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        self._set_selector_text(self._prefix_for(kind) + new_name)
        return True

    def delete_selected(self) -> bool:
        selected = self._selected_object()
        if selected is None:
            self._show_error("Select a saved object before deleting it.")
            return False
        kind, name = selected
        try:
            self._library.delete(kind, name)
        except (ConfigValidationError, KeyError) as exc:
            self._show_error(str(exc))
            return False
        self.refresh()
        return True

    def _build_controls(self, parent: Any) -> SignatureProfileLibraryControls:
        dialog = self._bindings.q_dialog(parent)
        set_title = getattr(dialog, "setWindowTitle", None)
        if callable(set_title):
            set_title("Manage signing profiles")
        layout = self._bindings.q_form_layout(dialog)
        selector = self._bindings.q_combo_box()
        details = self._bindings.q_label("")
        name_input = self._bindings.q_line_edit()
        name_input.setPlaceholderText("New name")
        rename = self._bindings.q_push_button("Rename")
        delete = self._bindings.q_push_button("Delete")
        close = self._bindings.q_push_button("Close")
        layout.addRow("Saved signing object", selector)
        layout.addRow("References", details)
        layout.addRow("Rename selected object", name_input)
        layout.addRow(rename, delete)
        layout.addRow(close)
        selector.currentTextChanged.connect(lambda _value: self._render_selection())
        rename.clicked.connect(self.rename_selected)
        delete.clicked.connect(self.delete_selected)
        reject = getattr(dialog, "reject", None)
        if callable(reject):
            close.clicked.connect(reject)
        return SignatureProfileLibraryControls(
            dialog=dialog,
            object_selector=selector,
            details_label=details,
            name_input=name_input,
            rename_button=rename,
            delete_button=delete,
            close_button=close,
        )

    def _render_selection(self) -> None:
        selected = self._selected_object()
        if selected is None:
            self.controls.details_label.setText("Select an object to inspect its saved references.")
            return
        kind, name = selected
        item = next(
            (item for item in self._library.items()
             if item.kind == kind and item.display_name == name),
            None,
        )
        self.controls.details_label.setText(
            item.details if item is not None else "Saved object is no longer available."
        )
        self.controls.name_input.setText(name)

    def _selected_object(self) -> tuple[str, str] | None:
        value = self.controls.object_selector.currentText().strip()
        for kind, prefix in (
            ("appearance", self._APPEARANCE_PREFIX),
            ("placement", self._PLACEMENT_PREFIX),
            ("preset", self._PRESET_PREFIX),
        ):
            if value.startswith(prefix):
                return kind, value.removeprefix(prefix)
        return None

    def _set_selector_text(self, value: str) -> None:
        setter = getattr(self.controls.object_selector, "setCurrentText", None)
        if callable(setter):
            setter(value)

    def _prefix_for(self, kind: str) -> str:
        return {
            "appearance": self._APPEARANCE_PREFIX,
            "placement": self._PLACEMENT_PREFIX,
            "preset": self._PRESET_PREFIX,
        }[kind]

    def _show_error(self, message: str) -> None:
        warning = getattr(self._bindings.q_message_box, "warning", None)
        if callable(warning):
            warning(self.controls.dialog, "Signing profile error", message)
