"""Document-independent Qt editor for one reusable signature appearance."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.reusable_signing_models import AppearanceProfile
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectKind,
    ReusableObjectRef,
    ReusableSigningObjects,
    SaveAppearance,
)
from foliaseal.application.signature_properties_coordinator import (
    VisibleSignaturePlacementDraft,
    VisibleSignatureSetupDraft,
)
from foliaseal.domain.models import SignatureAppearance
from foliaseal.infra.config.schemas import ConfigValidationError
from foliaseal.presentation.qt.visible_signature_setup_form import QtVisibleSignatureSetupForm


@dataclass(frozen=True)
class AppearanceProfileEditorControls:
    dialog: Any
    name_input: Any
    setup_form: QtVisibleSignatureSetupForm
    save_button: Any
    cancel_button: Any


class AppearanceProfileEditorDialog:
    """Edit an appearance profile without requiring an open document or draft."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        library: ReusableSigningObjects,
        initial_ref: ReusableObjectRef | None = None,
        on_saved: Callable[[], None] | None = None,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._library = library
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

    def _initial_appearance(self) -> SignatureAppearance:
        if self._initial_ref is None:
            return SignatureAppearance()
        resolved = self._library.resolve(self._initial_ref)
        if not isinstance(resolved, AppearanceProfile):
            raise ConfigValidationError("Select an appearance profile to edit.")
        return resolved.appearance

    def _build_controls(self, parent: Any) -> AppearanceProfileEditorControls:
        dialog = self._bindings.q_dialog(parent)
        dialog.setWindowTitle(
            "Create appearance" if self._initial_ref is None else "Edit appearance"
        )
        layout = self._bindings.q_vbox_layout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        helper = self._bindings.q_label(
            "Compose the visible signature style. This editor is independent of "
            "the active document."
        )
        if hasattr(helper, "setWordWrap"):
            helper.setWordWrap(True)
        layout.addWidget(helper)

        name_input = self._bindings.q_line_edit()
        name_input.setPlaceholderText("Appearance name")
        layout.addWidget(self._bindings.q_label("Name"))
        layout.addWidget(name_input)

        setup_form = QtVisibleSignatureSetupForm(bindings=self._bindings)
        setup_form.load(
            VisibleSignatureSetupDraft(
                appearance=self._initial_appearance(),
                placement=VisibleSignaturePlacementDraft(
                    page_number=1,
                    left_pt=24.0,
                    bottom_pt=18.0,
                    width_pt=180.0,
                    height_pt=54.0,
                    enabled=False,
                ),
            )
        )
        layout.addWidget(setup_form.visible_signature_controls.container)

        save_button = self._bindings.q_push_button("Save")
        cancel_button = self._bindings.q_push_button("Cancel")
        layout.addWidget(_compose_row(self._bindings, cancel_button, save_button))
        save_button.clicked.connect(lambda: self._save(dialog, name_input, setup_form))  # type: ignore[attr-defined]
        cancel_button.clicked.connect(lambda: getattr(dialog, "reject", lambda: None)())  # type: ignore[attr-defined]

        if self._initial_ref is not None:
            resolved = self._library.resolve(self._initial_ref)
            if isinstance(resolved, AppearanceProfile):
                name_input.setText(resolved.display_name)
        return AppearanceProfileEditorControls(
            dialog=dialog,
            name_input=name_input,
            setup_form=setup_form,
            save_button=save_button,
            cancel_button=cancel_button,
        )

    def _save(self, dialog: Any, name_input: Any, setup_form: QtVisibleSignatureSetupForm) -> None:
        name = str(name_input.text()).strip()
        if not name:
            self._on_error("Appearance profile name is required.")
            return
        overwrite = False
        if (
            self._initial_ref is None
            and self._library.resolve_name(ReusableObjectKind.APPEARANCE, name) is not None
        ):
            message_box = getattr(self._bindings, "q_message_box", None)
            question = getattr(message_box, "question", None)
            yes = getattr(message_box, "Yes", None)
            if callable(question):
                result = question(
                    dialog,
                    "Replace appearance?",
                    f"Appearance '{name}' already exists. Replace it?",
                )
                if result == yes:
                    overwrite = True
                else:
                    return
            else:
                self._on_error(f"Appearance '{name}' already exists.")
                return
        try:
            self._library.execute(
                SaveAppearance(
                    name=name,
                    appearance=setup_form.build_draft().appearance,
                    appearance_profile_id=(
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


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


__all__ = ["AppearanceProfileEditorControls", "AppearanceProfileEditorDialog"]
