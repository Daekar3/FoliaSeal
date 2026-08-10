"""Narrow caller-facing shell surface for the signing workspace."""

from __future__ import annotations

from collections.abc import Callable

from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)


class SigningWorkspaceShellSurface:
    """Own the narrow caller-facing production shell verbs."""

    def __init__(
        self,
        *,
        action_bridge: SigningWorkspaceActionBridge,
        set_app_settings: Callable[[AppSettings], None],
        set_document_text_selection_mode: Callable[[bool], bool],
        copy_selected_document_text: Callable[[], str | None],
        open_reusable_object_editor: Callable[[], bool],
        initial_app_settings: AppSettings,
    ) -> None:
        self._action_bridge = action_bridge
        self._set_app_settings = set_app_settings
        self._set_document_text_selection_mode = set_document_text_selection_mode
        self._copy_selected_document_text = copy_selected_document_text
        self._open_reusable_object_editor = open_reusable_object_editor
        self._app_settings = initial_app_settings

    def apply_app_settings(self, settings: AppSettings) -> None:
        self._app_settings = settings
        self._set_app_settings(settings)

    def choose_output_pdf_path(self) -> str | None:
        return self._action_bridge.choose_output_pdf_path()

    def has_explicit_output_pdf_path(self) -> bool:
        return self._action_bridge.has_explicit_output_pdf_path()

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self._action_bridge.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> None:
        """Reload reusable profile selectors exposed through the workspace port."""
        self._action_bridge.refresh_signature_profiles()

    def open_reusable_object_editor(self) -> bool:
        return bool(self._open_reusable_object_editor())

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self._set_document_text_selection_mode(enabled)

    def copy_selected_document_text(self) -> str | None:
        return self._copy_selected_document_text()

    def submit_sign_request(self) -> SigningRequest | None:
        return self._action_bridge.submit_sign_request()

    def open_signed_output(self) -> str | None:
        return self._action_bridge.open_signed_output()
