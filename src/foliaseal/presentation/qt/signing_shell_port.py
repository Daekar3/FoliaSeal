"""Shell-owned caller-facing port for one live signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings, CertificateCatalog
from foliaseal.presentation.qt.signing_shell import (
    SigningRequestExecutor,
    build_qt_signing_shell,
)
from foliaseal.presentation.qt.signing_workspace_testing_port import (
    SigningWorkspaceTestingPort,
)


@dataclass(frozen=True)
class SigningWorkspaceBootstrap:
    """Typed inputs required to create one signing workspace."""

    viewer_workflow: ViewerWorkflow
    signing_workflow: SigningDraftWorkflow
    app_settings: AppSettings
    app_settings_store: AppSettingsStore | None = None
    certificate_catalog_store: CertificateCatalogStore | None = None
    certificate_secret_provider: Any | None = None
    preset_catalog_store: SignaturePresetCatalogStore | None = None
    sign_executor: SigningRequestExecutor | None = None
    on_sign_request: Callable[[SigningRequest], None] | None = None
    on_open_signed_output: Callable[[str | Path], Any | None] | None = None
    on_error: Callable[[str], None] | None = None
    on_status_change: Callable[[str], None] | None = None


class SigningWorkspacePort(Protocol):
    """Explicit caller-facing contract for an active signing workspace."""

    def widget(self) -> Any:
        """Return the concrete widget to install as the central widget."""

    def choose_output_pdf_path(self) -> str | None:
        """Drive the shell's Save As behavior."""

    def apply_app_settings(self, settings: AppSettings) -> None:
        """Apply updated app settings to the live shell."""

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        """Refresh live certificate configuration choices."""

    def refresh_signature_profiles(self) -> None:
        """Refresh reusable signing-profile and preset choices."""

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        """Toggle document text-selection mode for the live shell."""

    def copy_selected_document_text(self) -> str | None:
        """Copy the current arbitrary text selection, if any."""


class SigningWorkspaceFactory(Protocol):
    """Create a live signing workspace from typed bootstrap inputs."""

    def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
        """Build and return the active workspace port."""


@dataclass(frozen=True)
class SigningWorkspaceBundle:
    """Caller-facing bundle for one live workspace instance."""

    port: SigningWorkspacePort
    testing_adapter: SigningWorkspaceTestingPort


@dataclass(frozen=True)
class QtSigningWorkspacePort:
    """Port adapter over the concrete Qt signing shell widget."""

    shell_widget: Any

    def widget(self) -> Any:
        return self.shell_widget

    def choose_output_pdf_path(self) -> str | None:
        return self.shell_widget.choose_output_pdf_path()

    def apply_app_settings(self, settings: AppSettings) -> None:
        self.shell_widget.apply_app_settings(settings)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self.shell_widget.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> None:
        self.shell_widget.refresh_signature_profiles()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self.shell_widget.set_document_text_selection_mode(enabled)

    def copy_selected_document_text(self) -> str | None:
        return self.shell_widget.copy_selected_document_text()


class QtSigningWorkspaceFactory:
    """Production factory that wraps the Qt signing shell behind a port."""

    def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
        shell_widget = build_qt_signing_shell(
            viewer_workflow=bootstrap.viewer_workflow,
            signing_workflow=bootstrap.signing_workflow,
            certificate_catalog_store=bootstrap.certificate_catalog_store,
            certificate_secret_provider=bootstrap.certificate_secret_provider,
            preset_catalog_store=bootstrap.preset_catalog_store,
            app_settings=bootstrap.app_settings,
            app_settings_store=bootstrap.app_settings_store,
            sign_executor=bootstrap.sign_executor,
            on_sign_request=bootstrap.on_sign_request,
            on_open_signed_output=bootstrap.on_open_signed_output,
            on_error=bootstrap.on_error,
            on_status_change=bootstrap.on_status_change,
        )
        testing_adapter = getattr(shell_widget, "testing_adapter", None)
        if testing_adapter is None:
            raise TypeError(
                "Qt signing shell widgets must expose 'testing_adapter'."
            )
        return SigningWorkspaceBundle(
            port=QtSigningWorkspacePort(shell_widget=shell_widget),
            testing_adapter=testing_adapter,
        )
