"""Qt-local modal editor for refining one visible-signature setup."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.application.signature_properties_coordinator import (
    SignaturePropertiesCoordinatorError,
    SignaturePropertiesViewState,
    VisibleSignatureSetupDraft,
)
from foliaseal.application.signing_draft_contracts import SigningDraftValidationIssue
from foliaseal.application.signing_setup_session import SigningSetupSession
from foliaseal.presentation.qt.visible_signature_setup_form import QtVisibleSignatureSetupForm


@dataclass(frozen=True)
class RefinementDialogState:
    """Ephemeral controls retained only while the refinement dialog is open."""

    dialog: Any
    setup_form: QtVisibleSignatureSetupForm
    apply_button: Any
    save_appearance_button: Any
    save_placement_button: Any
    save_preset_button: Any
    appearance_profile_combo: Any
    placement_profile_combo: Any
    cancel_button: Any


@dataclass(frozen=True)
class RefinementDialogResult:
    """Result of the modal refinement interaction."""

    accepted: bool
    draft: VisibleSignatureSetupDraft | None = None


def _compose_row(bindings: Any, *widgets: Any) -> Any:
    container = bindings.q_widget()
    layout = bindings.q_hbox_layout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    for widget in widgets:
        layout.addWidget(widget)
    return container


def _combo_text(combo: Any) -> str:
    getter = getattr(combo, "currentText", None)
    return str(getter()) if callable(getter) else ""


class SignatureRefinementDialog:
    """Build and execute the focused refinement dialog without owning domain state."""

    def __init__(
        self,
        *,
        bindings: Any,
        parent: Any,
        setup_session: SigningSetupSession,
        control_issue_getter: Callable[[], SigningDraftValidationIssue | None],
        apply_state: Callable[[SignaturePropertiesViewState], None],
        on_error: Callable[[str], None],
        certificate_configuration_id_getter: Callable[[], str | None],
        active_state_changed: Callable[[RefinementDialogState | None], None] | None = None,
    ) -> None:
        self._bindings = bindings
        self._parent = parent
        self._setup_session = setup_session
        self._control_issue_getter = control_issue_getter
        self._apply_state = apply_state
        self._on_error = on_error
        self._certificate_configuration_id_getter = certificate_configuration_id_getter
        self._active_state_changed = active_state_changed or (lambda _state: None)

    def open(self, draft: VisibleSignatureSetupDraft) -> RefinementDialogResult:
        dialog = self._bindings.q_dialog(self._parent)
        if hasattr(dialog, "setWindowTitle"):
            dialog.setWindowTitle("Refine current PDF setup")
        layout = self._bindings.q_vbox_layout(dialog)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        helper_label = self._bindings.q_label(
            "Use this dialog to adjust the current PDF's visible signature "
            "without reopening the old inline editor in the main window."
        )
        if hasattr(helper_label, "setWordWrap"):
            helper_label.setWordWrap(True)
        layout.addWidget(helper_label)

        setup_form = QtVisibleSignatureSetupForm(bindings=self._bindings)
        setup_form.load(draft)
        layout.addWidget(setup_form.visible_signature_controls.container)
        layout.addWidget(setup_form.placement_controls.container)

        profile_state = self._setup_session.load(control_issue=self._control_issue_getter())
        appearance_profile_combo = self._bindings.q_combo_box()
        appearance_profile_combo.addItems(profile_state.appearance_profile_names)
        placement_profile_combo = self._bindings.q_combo_box()
        placement_profile_combo.addItem("No saved placement profile")
        placement_profile_combo.addItems(profile_state.placement_profile_names)
        layout.addWidget(
            _compose_row(
                self._bindings,
                self._bindings.q_label("Appearance profile"),
                appearance_profile_combo,
                self._bindings.q_label("Placement profile"),
                placement_profile_combo,
            )
        )

        def _refresh_profile_choices(state: SignaturePropertiesViewState) -> None:
            appearance_profile_combo.clear()
            appearance_profile_combo.addItems(state.appearance_profile_names)
            placement_profile_combo.clear()
            placement_profile_combo.addItem("No saved placement profile")
            placement_profile_combo.addItems(state.placement_profile_names)

        apply_button = self._bindings.q_push_button("Apply")
        save_appearance_button = self._bindings.q_push_button("Save appearance for reuse...")
        save_placement_button = self._bindings.q_push_button("Save placement for reuse...")
        save_preset_button = self._bindings.q_push_button("Save signature preset for reuse...")
        cancel_button = self._bindings.q_push_button("Cancel")
        layout.addWidget(
            _compose_row(
                self._bindings,
                save_appearance_button,
                save_placement_button,
                save_preset_button,
                apply_button,
                cancel_button,
            )
        )

        def _accept() -> None:
            dialog._selected_draft = setup_form.build_draft()  # type: ignore[attr-defined]
            accept = getattr(dialog, "accept", None)
            if callable(accept):
                accept()

        def _reject() -> None:
            reject = getattr(dialog, "reject", None)
            if callable(reject):
                reject()

        apply_button.clicked.connect(_accept)  # type: ignore[attr-defined]

        def _profile_name(title: str) -> str | None:
            get_text = getattr(self._bindings.q_input_dialog, "getText", None)
            if not callable(get_text):
                return None
            name, accepted = get_text(dialog, title, "Profile name")
            return str(name) if accepted else None

        def _save_appearance() -> None:
            name = _profile_name("Save appearance profile")
            if name is None:
                return
            try:
                state = self._setup_session.save_appearance_profile(
                    name,
                    setup_form.build_draft().appearance,
                    control_issue=self._control_issue_getter(),
                )
                _refresh_profile_choices(state)
            except SignaturePropertiesCoordinatorError as exc:
                self._on_error(str(exc))

        def _save_placement() -> None:
            name = _profile_name("Save placement profile")
            if name is None:
                return
            try:
                state = self._setup_session.save_placement_profile(
                    name,
                    setup_form.build_draft().placement,
                    control_issue=self._control_issue_getter(),
                )
                _refresh_profile_choices(state)
            except SignaturePropertiesCoordinatorError as exc:
                self._on_error(str(exc))

        def _save_preset() -> None:
            appearance_name = _combo_text(appearance_profile_combo).strip()
            if not appearance_name:
                self._on_error(
                    "Save an appearance profile before composing a signature preset."
                )
                return
            name = _profile_name("Save signature preset")
            if name is None:
                return
            placement_name = _combo_text(placement_profile_combo).strip()
            if placement_name == "No saved placement profile":
                placement_name = ""
            try:
                state = self._setup_session.compose_signature_preset(
                    name,
                    appearance_name,
                    placement_profile_name=placement_name or None,
                    certificate_configuration_id=self._certificate_configuration_id_getter(),
                    control_issue=self._control_issue_getter(),
                )
                self._apply_state(state)
            except SignaturePropertiesCoordinatorError as exc:
                self._on_error(str(exc))

        save_appearance_button.clicked.connect(_save_appearance)  # type: ignore[attr-defined]
        save_placement_button.clicked.connect(_save_placement)  # type: ignore[attr-defined]
        save_preset_button.clicked.connect(_save_preset)  # type: ignore[attr-defined]
        cancel_button.clicked.connect(_reject)  # type: ignore[attr-defined]

        active_state = RefinementDialogState(
            dialog=dialog,
            setup_form=setup_form,
            apply_button=apply_button,
            save_appearance_button=save_appearance_button,
            save_placement_button=save_placement_button,
            save_preset_button=save_preset_button,
            appearance_profile_combo=appearance_profile_combo,
            placement_profile_combo=placement_profile_combo,
            cancel_button=cancel_button,
        )
        self._active_state_changed(active_state)
        try:
            dialog_exec = getattr(dialog, "exec", None)
            result = dialog_exec() if callable(dialog_exec) else None
            accepted = result == self._accepted_dialog_code()
            selected_draft = getattr(dialog, "_selected_draft", None)
            if not accepted or selected_draft is None:
                return RefinementDialogResult(accepted=False)
            return RefinementDialogResult(accepted=True, draft=selected_draft)
        finally:
            self._active_state_changed(None)

    def _accepted_dialog_code(self) -> Any:
        accepted = getattr(self._bindings.q_dialog, "Accepted", None)
        if accepted is not None:
            return accepted
        dialog_code = getattr(self._bindings.q_dialog, "DialogCode", None)
        return getattr(dialog_code, "Accepted", None)
