"""Shell-internal bridge for signing-action glue."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from foliaseal.application import suggest_signed_output_path
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
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
        state = self._signing_action_boundary.load()
        if not state.can_sign:
            return True
        setup = self._setup_port.load_setup_state()
        certificate = setup.selected_certificate_configuration_name or "No certificate selected"
        preset = setup.selected_signature_preset_name or "Current-document custom setup"
        message_box = self._bindings.q_message_box
        question = getattr(message_box, "question", None)
        if not callable(question):
            return False
        yes_value = getattr(message_box, "Yes", None)
        if yes_value is None:
            yes_value = getattr(getattr(message_box, "StandardButton", None), "Yes", None)
        result = question(
            self._widget,
            "Confirm signing",
            "You are about to create an irreversible signed PDF.\n\n"
            f"Output: {self._draft_workflow.output_pdf_path}\n"
            f"Certificate: {certificate}\n"
            f"Setup: {preset}\n\n"
            f"Readiness: {state.detail_text}\n\n"
            "Review the preview and any caveats, then choose Yes to sign.",
        )
        return result == yes_value

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
        if not self._confirm_output_overwrite(selected_path):
            return None
        self._apply_signing_action_state(
            self._signing_action_boundary.accept_output_path(selected_path).state
        )
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
        self._widget.last_signing_result = state.last_signing_result
        self._sidebar.render_signing_action_state(state)

    def _default_output_dialog_path(self) -> Path:
        app_settings: AppSettings = self._app_settings_getter()
        return suggest_signed_output_path(
            input_pdf_path=self._draft_workflow.input_pdf_path,
            default_output_directory=app_settings.default_output_directory,
            current_output_path=self._draft_workflow.output_pdf_path,
        )

    def _confirm_output_overwrite(self, selected_path: str) -> bool:
        selected = Path(selected_path)
        if not selected.exists():
            return True
        message_box = self._bindings.q_message_box
        question = getattr(message_box, "question", None)
        if not callable(question):
            return False
        yes_value = getattr(message_box, "Yes", None)
        if yes_value is None:
            standard_button = getattr(message_box, "StandardButton", None)
            yes_value = getattr(standard_button, "Yes", None)
        result = question(
            self._widget,
            "Overwrite signed PDF?",
            f"Replace existing signed PDF at {selected_path}?",
        )
        return result == yes_value
