"""Document-independent Qt editor for one reusable signature preset."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectRef,
    ReusableSigningObjects,
)
from foliaseal.presentation.qt.signature_preset_editor_widget import (
    SignaturePresetEditorWidget,
)


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
        layout = self._bindings.q_vbox_layout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        def on_saved() -> None:
            self._on_saved()
            accept = getattr(dialog, "accept", None)
            if callable(accept):
                accept()

        widget = SignaturePresetEditorWidget(
            bindings=self._bindings,
            parent=dialog,
            library=self._library,
            certificate_catalog=self._certificate_catalog,
            initial_ref=self._initial_ref,
            on_saved=on_saved,
            on_cancel_requested=lambda: getattr(dialog, "reject", lambda: None)() or True,
            on_error=self._on_error,
        )
        layout.addWidget(widget.controls.container)
        return SignaturePresetEditorControls(
            dialog=dialog,
            name_input=widget.controls.name_input,
            appearance_selector=widget.controls.appearance_selector,
            placement_selector=widget.controls.placement_selector,
            certificate_selector=widget.controls.certificate_selector,
            save_button=widget.controls.save_button,
            cancel_button=widget.controls.cancel_button,
        )

__all__ = ["SignaturePresetEditorControls", "SignaturePresetEditorDialog"]
