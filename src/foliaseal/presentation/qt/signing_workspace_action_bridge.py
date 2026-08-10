"""Shell-internal bridge for signing-action glue."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foliaseal.application import suggest_signed_output_path
from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.output_path_policy import paths_refer_to_same_file
from foliaseal.application.signing_confirmation import SigningConfirmationSummary
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signing_action_boundary import (
    SigningActionBoundary,
)
from foliaseal.presentation.qt.signing_action_coordinator import (
    SigningActionState,
)
from foliaseal.presentation.qt.signing_workspace_setup_port import (
    SigningWorkspaceSetupPort,
)


class SigningWorkspaceActionBridge:
    """Own shell-facing signing-action glue over the action boundary."""

    def __init__(
        self,
        *,
        widget: Any,
        bindings: Any,
        sidebar: Any,
        setup_port: SigningWorkspaceSetupPort,
        signing_action_boundary: SigningActionBoundary,
        draft_workflow: Any,
        app_settings_getter: Any,
    ) -> None:
        self._widget = widget
        self._bindings = bindings
        self._sidebar = sidebar
        self._setup_port = setup_port
        self._signing_action_boundary = signing_action_boundary
        self._draft_workflow = draft_workflow
        self._app_settings_getter = app_settings_getter
        self._has_explicit_output_pdf_path = False

    def has_explicit_output_pdf_path(self) -> bool:
        """Return whether Save As has accepted a path for the current draft."""

        return self._has_explicit_output_pdf_path

    def reload_state(self) -> None:
        self._apply_signing_action_state(self._signing_action_boundary.load())

    def invalidate_state(self, reason: str) -> None:
        self._apply_signing_action_state(
            self._signing_action_boundary.invalidate(reason).state
        )

    def submit_sign_request(self) -> SigningRequest | None:
        if not self._confirm_signing_request():
            return None
        result = self._signing_action_boundary.submit()
        self._apply_signing_action_state(result.state)
        return result.request

    def _confirm_signing_request(self) -> bool:
        apply_changes = getattr(self._setup_port, "apply_changes", None)
        if callable(apply_changes):
            # Synchronize the visible controls before taking the preview snapshot;
            # the same draft then flows through the coordinator's submit path.
            apply_changes()
        state = self._signing_action_boundary.load()
        if not state.can_sign:
            return True
        setup = self._setup_port.load_setup_state()
        certificate = setup.selected_certificate_configuration_name or "No certificate selected"
        preset = setup.selected_signature_preset_name or "Current-document custom setup"
        preview = self._draft_workflow.preview()
        summary = SigningConfirmationSummary.from_preview(
            preview=preview,
            preset_name=preset,
            certificate_name=certificate,
            output_path=self._draft_workflow.output_pdf_path,
            signing_time=self._draft_workflow.preview_signing_time,
        )
        return self._ask_consequence_confirmation(
            title="Confirm signing",
            text=summary.as_message() + f"\n\nReadiness: {state.detail_text}",
            affirmative_label="Sign and save",
        )

    def open_signed_output(self) -> str | None:
        result = self._signing_action_boundary.open_signed_output()
        return result.opened_output_path

    def choose_output_pdf_path(self) -> str | None:
        initial_path = self._default_output_dialog_path()
        selected = self._bindings.q_file_dialog.getSaveFileName(
            self._widget,
            "Save signed PDF",
            str(initial_path),
            "PDF files (*.pdf)",
        )
        if isinstance(selected, tuple):
            selected_path = str(selected[0])
        else:
            selected_path = str(selected)
        selected_path = selected_path.strip()
        if not selected_path:
            return None
        source_overwrite = paths_refer_to_same_file(
            self._draft_workflow.input_pdf_path,
            selected_path,
        )
        if not self._confirm_output_overwrite(
            selected_path,
            source_overwrite=source_overwrite,
        ):
            return None
        self._apply_signing_action_state(
            self._signing_action_boundary.accept_output_path(
                selected_path,
                allow_source_overwrite=source_overwrite,
            ).state
        )
        self._has_explicit_output_pdf_path = True
        return selected_path

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        catalog = self._setup_port.refresh_certificate_configurations()
        self.reload_state()
        return catalog

    def refresh_signature_profiles(self) -> None:
        """Reload reusable profiles and presets in the mounted shell."""
        self._setup_port.refresh_signature_profiles()
        self.reload_state()

    def _apply_signing_action_state(self, state: SigningActionState) -> None:
        self._sidebar.render_signing_action_state(state)

    def _default_output_dialog_path(self) -> Path:
        app_settings: AppSettings = self._app_settings_getter()
        return suggest_signed_output_path(
            input_pdf_path=self._draft_workflow.input_pdf_path,
            default_output_directory=app_settings.default_output_directory,
            current_output_path=self._draft_workflow.output_pdf_path,
        )

    def _confirm_output_overwrite(
        self,
        selected_path: str,
        *,
        source_overwrite: bool = False,
    ) -> bool:
        selected = Path(selected_path)
        if not source_overwrite and not selected.exists():
            return True
        if source_overwrite:
            title = "Replace source PDF?"
            text = (
                f"Replace the source PDF at {selected_path} after the signed sibling output "
                "is verified? Cancel keeps the original source unchanged."
            )
            affirmative_label = "Replace source PDF"
        else:
            title = "Overwrite signed PDF?"
            text = f"Replace existing signed PDF at {selected_path}?"
            affirmative_label = "Replace signed PDF"
        return self._ask_consequence_confirmation(
            title=title,
            text=text,
            affirmative_label=affirmative_label,
        )

    def _ask_consequence_confirmation(
        self,
        *,
        title: str,
        text: str,
        affirmative_label: str,
    ) -> bool:
        """Use consequence-labeled buttons when the concrete QMessageBox supports them."""

        message_box = self._bindings.q_message_box
        if isinstance(message_box, type):
            dialog = message_box(self._widget)
            add_button = getattr(dialog, "addButton", None)
            role_type = getattr(message_box, "ButtonRole", None)
            if callable(add_button) and role_type is not None:
                cancel_button = add_button("Cancel", role_type.RejectRole)
                affirmative_button = add_button(
                    affirmative_label,
                    role_type.AcceptRole,
                )
                dialog.setWindowTitle(title)
                dialog.setText(text)
                set_default = getattr(dialog, "setDefaultButton", None)
                if callable(set_default):
                    set_default(cancel_button)
                exec_method = getattr(dialog, "exec", None) or getattr(dialog, "exec_", None)
                if callable(exec_method):
                    exec_method()
                    return (
                        getattr(dialog, "clickedButton", lambda: None)()
                        is affirmative_button
                    )

        question = getattr(message_box, "question", None)
        if not callable(question):
            return False
        yes_value = getattr(message_box, "Yes", None)
        if yes_value is None:
            yes_value = getattr(getattr(message_box, "StandardButton", None), "Yes", None)
        return question(self._widget, title, text) == yes_value
