"""Qt editor for an isolated reusable fixed-page placement draft."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.placement_editor import PlacementEditorSession, PlacementEditorState
from foliaseal.application.reusable_signing_models import PlacementProfile, PlacementProfileRect
from foliaseal.application.reusable_signing_objects import ReusableObjectMutationRejected


@dataclass(frozen=True)
class PlacementProfileEditorControls:
    dialog: Any
    name_input: Any
    pinned_check: Any
    page_spin: Any
    left_spin: Any
    top_spin: Any
    width_spin: Any
    height_spin: Any
    save_button: Any
    cancel_button: Any


class PlacementProfileEditorDialog:
    """Build and run a Save/Cancel editor without mutating its caller's draft."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        initial: PlacementEditorState,
        on_save: Callable[[PlacementProfile], None],
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._initial = initial
        self._on_save = on_save
        self._on_error = on_error or (lambda _message: None)
        self._session = PlacementEditorSession(initial)
        self.controls = self._build_controls(parent)

    def open(self) -> bool:
        exec_dialog = getattr(self.controls.dialog, "exec", None)
        if not callable(exec_dialog):
            show = getattr(self.controls.dialog, "show", None)
            if callable(show):
                show()
            return False
        result = exec_dialog()
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        return result == accepted

    def _build_controls(self, parent: Any) -> PlacementProfileEditorControls:
        dialog = self._bindings.q_dialog(parent)
        dialog.setWindowTitle("Edit placement")
        layout = self._bindings.q_vbox_layout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        heading = self._bindings.q_label(
            "Fixed page placement — the source PDF is never stored with this reusable object."
        )
        if hasattr(heading, "setWordWrap"):
            heading.setWordWrap(True)
        layout.addWidget(heading)

        name_input = self._bindings.q_line_edit()
        name_input.setText(self._initial.display_name)
        layout.addWidget(self._row("Name", name_input))
        pinned_check = self._bindings.q_check_box("Pinned in the Placement catalog")
        pinned_check.setChecked(self._initial.pinned)
        layout.addWidget(pinned_check)

        source = self._initial.source_page
        summary = self._bindings.q_label(
            f"Visible source page: {source.visible_width_pt:g} × {source.visible_height_pt:g} pt; "
            f"rotation {source.rotation_degrees}°"
        )
        if hasattr(summary, "setWordWrap"):
            summary.setWordWrap(True)
        layout.addWidget(summary)

        page_spin = self._spin(integer=True, minimum=1, maximum=9999)
        page_spin.setValue(self._initial.page_number)
        layout.addWidget(self._row("Page", page_spin))

        left_spin = self._spin()
        top_spin = self._spin()
        width_spin = self._spin(minimum=0.01)
        height_spin = self._spin(minimum=0.01)
        for spin, value in (
            (left_spin, self._initial.rect.left_pt),
            (top_spin, self._initial.rect.top_pt),
            (width_spin, self._initial.rect.width_pt),
            (height_spin, self._initial.rect.height_pt),
        ):
            spin.setValue(value)
        layout.addWidget(self._row("Left (pt)", left_spin))
        layout.addWidget(self._row("Top (pt)", top_spin))
        layout.addWidget(self._row("Width (pt)", width_spin))
        layout.addWidget(self._row("Height (pt)", height_spin))

        hint = self._bindings.q_label(
            "Coordinates use the visible page's upper-left origin. Numeric edits are exact."
        )
        if hasattr(hint, "setWordWrap"):
            hint.setWordWrap(True)
        layout.addWidget(hint)

        save_button = self._bindings.q_push_button("Save")
        cancel_button = self._bindings.q_push_button("Cancel")
        buttons = self._bindings.q_widget()
        button_layout = self._bindings.q_hbox_layout(buttons)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addWidget(buttons)

        def reject() -> None:
            self._session.cancel()
            callback = getattr(dialog, "reject", None)
            if callable(callback):
                callback()

        def accept() -> None:
            try:
                self._session.update(
                    display_name=str(name_input.text()),
                    pinned=bool(pinned_check.isChecked()),
                    page_number=int(page_spin.value()),
                    rect=PlacementProfileRect(
                        left_pt=float(left_spin.value()),
                        top_pt=float(top_spin.value()),
                        width_pt=float(width_spin.value()),
                        height_pt=float(height_spin.value()),
                    ),
                )
                profile = self._session.save()
                self._on_save(profile)
            except ReusableObjectMutationRejected:
                return
            except (RuntimeError, ValueError) as exc:
                self._on_error(str(exc))
                return
            callback = getattr(dialog, "accept", None)
            if callable(callback):
                callback()

        cancel_button.clicked.connect(reject)  # type: ignore[attr-defined]
        save_button.clicked.connect(accept)  # type: ignore[attr-defined]
        return PlacementProfileEditorControls(
            dialog=dialog,
            name_input=name_input,
            pinned_check=pinned_check,
            page_spin=page_spin,
            left_spin=left_spin,
            top_spin=top_spin,
            width_spin=width_spin,
            height_spin=height_spin,
            save_button=save_button,
            cancel_button=cancel_button,
        )

    def _row(self, label: str, widget: Any) -> Any:
        container = self._bindings.q_widget()
        row = self._bindings.q_hbox_layout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._bindings.q_label(label))
        row.addWidget(widget)
        return container

    def _spin(
        self,
        *,
        integer: bool = False,
        minimum: float = -1_000_000.0,
        maximum: float = 1_000_000.0,
    ) -> Any:
        spin = self._bindings.q_spin_box() if integer else self._bindings.q_double_spin_box()
        spin.setRange(minimum, maximum)
        if not integer:
            spin.setDecimals(2)
            spin.setSingleStep(1.0)
        return spin


__all__ = ["PlacementProfileEditorControls", "PlacementProfileEditorDialog"]
