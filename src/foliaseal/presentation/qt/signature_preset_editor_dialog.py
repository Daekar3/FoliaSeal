"""Document-independent Qt editor for one reusable signature preset."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.reusable_signing_models import ResolvedSignaturePreset
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectKind,
    ReusableObjectRef,
    ReusableSigningObjects,
    SavePreset,
)
from foliaseal.infra.config.schemas import ConfigValidationError


@dataclass(frozen=True)
class SignaturePresetEditorControls:
    dialog: Any
    name_input: Any
    appearance_selector: Any
    placement_selector: Any
    certificate_selector: Any
    save_button: Any
    cancel_button: Any


class SignaturePresetEditorDialog:
    """Edit a preset's references without requiring an open document or signing draft."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        library: ReusableSigningObjects,
        certificate_catalog: CertificateCatalog,
        initial_ref: ReusableObjectRef | None = None,
        on_saved: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._library = library
        self._certificate_catalog = certificate_catalog
        self._initial_ref = initial_ref
        self._on_saved = on_saved or (lambda: None)
        self._on_error = on_error or (lambda _message: None)
        self.controls = self._build_controls(parent)

    def open(self) -> bool:
        execute = getattr(self.controls.dialog, "exec", None)
        if not callable(execute):
            return False
        result = execute()
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        return result == accepted

    def _build_controls(self, parent: Any) -> SignaturePresetEditorControls:
        dialog = self._bindings.q_dialog(parent)
        dialog.setWindowTitle("Edit signature preset")
        layout = self._bindings.q_form_layout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        name_input = self._bindings.q_line_edit()
        name_input.setPlaceholderText("Preset name")
        appearance_selector = self._bindings.q_combo_box()
        placement_selector = self._bindings.q_combo_box()
        certificate_selector = self._bindings.q_combo_box()
        self._populate_selectors(
            appearance_selector,
            placement_selector,
            certificate_selector,
            name_input,
        )
        layout.addRow("Name", name_input)
        layout.addRow("Appearance", appearance_selector)
        layout.addRow("Placement", placement_selector)
        layout.addRow("Certificate", certificate_selector)

        helper = self._bindings.q_label(
            "Presets reference reusable objects. Saving here never changes the active document."
        )
        if hasattr(helper, "setWordWrap"):
            helper.setWordWrap(True)
        layout.addRow(helper)

        save_button = self._bindings.q_push_button("Save")
        cancel_button = self._bindings.q_push_button("Cancel")
        layout.addRow(cancel_button, save_button)

        save_button.clicked.connect(  # type: ignore[attr-defined]
            lambda: self._save(
                dialog,
                name_input,
                appearance_selector,
                placement_selector,
                certificate_selector,
            )
        )
        cancel_button.clicked.connect(  # type: ignore[attr-defined]
            lambda: getattr(dialog, "reject", lambda: None)()
        )
        return SignaturePresetEditorControls(
            dialog=dialog,
            name_input=name_input,
            appearance_selector=appearance_selector,
            placement_selector=placement_selector,
            certificate_selector=certificate_selector,
            save_button=save_button,
            cancel_button=cancel_button,
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
        self._add_item(placement_selector, "No placement", None)
        for item in snapshot.placements:
            self._add_item(placement_selector, item.display_name, item.ref.object_id)
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
        name_input.setText(resolved.name)
        self._set_selector_data(appearance_selector, resolved.preset.appearance_profile_id)
        self._set_selector_data(placement_selector, resolved.preset.placement_profile_id)
        self._set_selector_data(
            certificate_selector,
            resolved.preset.certificate_configuration_id,
        )

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

    def _save(
        self,
        dialog: Any,
        name_input: Any,
        appearance_selector: Any,
        placement_selector: Any,
        certificate_selector: Any,
    ) -> None:
        name = str(name_input.text()).strip()
        appearance_id = self._current_data(appearance_selector)
        if not name:
            self._on_error("Preset name is required.")
            return
        if not appearance_id:
            self._on_error("A signature preset must reference an appearance.")
            return
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
                    dialog,
                    "Replace signature preset?",
                    f"Signature preset '{name}' already exists. Replace it?",
                )
                if result == yes:
                    overwrite = True
                else:
                    return
            else:
                self._on_error(f"Signature preset '{name}' already exists.")
                return
        try:
            self._library.execute(
                SavePreset(
                    name=name,
                    appearance_profile_id=str(appearance_id),
                    placement_profile_id=(
                        None
                        if self._current_data(placement_selector) is None
                        else str(self._current_data(placement_selector))
                    ),
                    certificate_configuration_id=(
                        None
                        if self._current_data(certificate_selector) is None
                        else str(self._current_data(certificate_selector))
                    ),
                    signature_preset_id=(
                        None if self._initial_ref is None else self._initial_ref.object_id
                    ),
                    overwrite=overwrite,
                )
            )
        except (ConfigValidationError, KeyError, ValueError) as exc:
            self._on_error(str(exc))
            return
        self._on_saved()
        accept = getattr(dialog, "accept", None)
        if callable(accept):
            accept()


__all__ = ["SignaturePresetEditorControls", "SignaturePresetEditorDialog"]
