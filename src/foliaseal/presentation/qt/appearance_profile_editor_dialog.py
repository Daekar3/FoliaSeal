"""Document-independent Qt editor for one reusable signature appearance."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.reusable_signing_objects import (
    ReusableObjectRef,
    ReusableSigningObjects,
)
from foliaseal.presentation.qt.appearance_profile_editor_widget import (
    AppearanceProfileEditorWidget,
)
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

    def _build_controls(self, parent: Any) -> AppearanceProfileEditorControls:
        dialog = self._bindings.q_dialog(parent)
        dialog.setWindowTitle(
            "Create appearance" if self._initial_ref is None else "Edit appearance"
        )
        layout = self._bindings.q_vbox_layout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        widget: AppearanceProfileEditorWidget | None = None

        def on_saved() -> None:
            self._on_saved()
            accept = getattr(dialog, "accept", None)
            if callable(accept):
                accept()

        widget = AppearanceProfileEditorWidget(
            bindings=self._bindings,
            parent=dialog,
            library=self._library,
            initial_ref=self._initial_ref,
            on_saved=on_saved,
            on_cancel_requested=lambda: getattr(dialog, "reject", lambda: None)(),
            on_error=self._on_error,
        )
        layout.addWidget(widget.controls.container)
        return AppearanceProfileEditorControls(
            dialog=dialog,
            name_input=widget.controls.name_input,
            setup_form=widget.controls.setup_form,
            save_button=widget.controls.save_button,
            cancel_button=widget.controls.cancel_button,
        )


__all__ = ["AppearanceProfileEditorControls", "AppearanceProfileEditorDialog"]
