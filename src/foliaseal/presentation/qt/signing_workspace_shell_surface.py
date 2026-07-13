"""Narrow caller-facing shell surface for the signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.schemas import (
    AppSettings,
    CertificateCatalog,
)
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)


class SigningWorkspaceShellSurface:
    """Own the narrow caller-facing production shell verbs."""

    def __init__(
        self,
        *,
        widget: Any,
        action_bridge: SigningWorkspaceActionBridge,
        set_app_settings: Callable[[AppSettings], None],
        set_document_text_selection_mode: Callable[[bool], bool],
        copy_selected_document_text: Callable[[], str | None],
        initial_app_settings: AppSettings,
    ) -> None:
        self._widget = widget
        self._action_bridge = action_bridge
        self._set_app_settings = set_app_settings
        self._set_document_text_selection_mode = set_document_text_selection_mode
        self._copy_selected_document_text = copy_selected_document_text
        self._app_settings = initial_app_settings

    def install_port_exports(self) -> None:
        self._widget.app_settings = self._app_settings  # type: ignore[attr-defined]
        self._widget.apply_app_settings = self.apply_app_settings  # type: ignore[attr-defined]
        self._widget.choose_output_pdf_path = self.choose_output_pdf_path  # type: ignore[attr-defined]
        self._widget.refresh_certificate_configurations = (  # type: ignore[attr-defined]
            self.refresh_certificate_configurations
        )
        self._widget.set_document_text_selection_mode = (  # type: ignore[attr-defined]
            self.set_document_text_selection_mode
        )
        self._widget.copy_selected_document_text = self.copy_selected_document_text  # type: ignore[attr-defined]
        self._widget.submit_sign_request = self.submit_sign_request  # type: ignore[attr-defined]
        self._widget.open_signed_output = self.open_signed_output  # type: ignore[attr-defined]

    def apply_app_settings(self, settings: AppSettings) -> None:
        self._app_settings = settings
        self._set_app_settings(settings)
        self._widget.app_settings = settings  # type: ignore[attr-defined]

    def choose_output_pdf_path(self) -> str | None:
        return self._action_bridge.choose_output_pdf_path()

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self._action_bridge.refresh_certificate_configurations()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self._set_document_text_selection_mode(enabled)

    def copy_selected_document_text(self) -> str | None:
        return self._copy_selected_document_text()

    def submit_sign_request(self) -> SigningRequest | None:
        return self._action_bridge.submit_sign_request()

    def open_signed_output(self) -> str | None:
        return self._action_bridge.open_signed_output()
