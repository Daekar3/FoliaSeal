"""Shell-owned caller-facing port for one live signing workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.certificate_models import CertificateCatalog
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.signing_draft_contracts import SigningDraftPreview
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect, SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signing_shell import (
    SigningRequestExecutor,
    build_qt_signing_shell,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import SigningWorkspaceSnapshot
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

    def choose_output_pdf_path(self) -> str | None:
        """Drive the shell's Save As behavior."""

    def apply_app_settings(self, settings: AppSettings) -> None:
        """Apply updated app settings to the live shell."""

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        """Refresh live certificate configuration choices."""

    def refresh_signature_profiles(self) -> None:
        """Refresh reusable signing-profile and preset choices."""

    def open_reusable_object_editor(self) -> bool:
        """Open the contextual reusable-object editor for the active PDF."""

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        """Toggle document text-selection mode for the live shell."""

    def copy_selected_document_text(self) -> str | None:
        """Copy the current arbitrary text selection, if any."""


class SigningWorkspaceSessionPort(Protocol):
    """Primary review/place/preview/sign flow for one active workspace."""

    def refresh_viewer(self) -> None: ...
    def refresh_document_review(self) -> DocumentReviewSummary: ...

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
    ) -> SignatureRect: ...

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...
    def preview(self) -> SigningDraftPreview: ...
    def snapshot(self) -> SigningWorkspaceSnapshot: ...
    def submit_sign_request(self) -> SigningRequest | None: ...
    def open_signed_output(self) -> str | None: ...
    def go_to_previous_page(self) -> None: ...
    def go_to_next_page(self) -> None: ...
    def reset_zoom_view(self) -> None: ...
    def focus(self) -> None: ...


class WorkspaceViewPort(Protocol):
    """Opaque lifecycle view; callers cannot inspect child widgets."""

    def mount_target(self) -> object: ...
    def dispose(self) -> None: ...


class SigningWorkspaceFactory(Protocol):
    """Create a live signing workspace from typed bootstrap inputs."""

    def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle:
        """Build and return the active workspace port."""


@dataclass(frozen=True)
class SigningWorkspaceBundle:
    """Caller-facing bundle for one live workspace instance."""

    maintenance: SigningWorkspacePort
    session: SigningWorkspaceSessionPort
    testing: SigningWorkspaceTestingPort
    view: WorkspaceViewPort


@dataclass(frozen=True)
class QtWorkspaceView:
    """Qt-local lifecycle adapter around the composite shell facade."""

    shell: Any
    _disposed: bool = field(default=False, init=False, compare=False)

    def mount_target(self) -> object:
        return getattr(self.shell, "container", self.shell)

    def dispose(self) -> None:
        if self._disposed:
            return
        object.__setattr__(self, "_disposed", True)
        close = getattr(self.shell, "close", None)
        if callable(close):
            close()
        container = getattr(self.shell, "container", self.shell)
        delete_later = getattr(container, "deleteLater", None)
        if callable(delete_later):
            delete_later()


@dataclass(frozen=True)
class QtSigningWorkspacePort:
    """Port adapter over the concrete Qt signing shell widget."""

    shell_widget: Any

    def choose_output_pdf_path(self) -> str | None:
        return self.shell_widget.choose_output_pdf_path()

    def apply_app_settings(self, settings: AppSettings) -> None:
        self.shell_widget.apply_app_settings(settings)

    def refresh_certificate_configurations(self) -> CertificateCatalog:
        return self.shell_widget.refresh_certificate_configurations()

    def refresh_signature_profiles(self) -> None:
        self.shell_widget.refresh_signature_profiles()

    def open_reusable_object_editor(self) -> bool:
        return self.shell_widget.open_reusable_object_editor()

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        return self.shell_widget.set_document_text_selection_mode(enabled)

    def copy_selected_document_text(self) -> str | None:
        return self.shell_widget.copy_selected_document_text()


@dataclass(frozen=True)
class QtSigningWorkspaceSessionPort:
    """Typed adapter over the shell's primary workflow methods."""

    shell_widget: Any

    def refresh_viewer(self) -> None:
        self.shell_widget.refresh_viewer()

    def refresh_document_review(self) -> DocumentReviewSummary:
        return self.shell_widget.refresh_document_review()

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
    ) -> SignatureRect:
        return self.shell_widget.set_signature_rect(
            page_index=page_index,
            left_pt=left_pt,
            bottom_pt=bottom_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        )

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self.shell_widget.apply_signature_rect_placement(signature_rect)

    def preview(self) -> SigningDraftPreview:
        return self.shell_widget.preview()

    def snapshot(self) -> SigningWorkspaceSnapshot:
        return self.shell_widget.snapshot()

    def submit_sign_request(self) -> SigningRequest | None:
        return self.shell_widget.submit_sign_request()

    def open_signed_output(self) -> str | None:
        return self.shell_widget.open_signed_output()

    def go_to_previous_page(self) -> None:
        self.shell_widget.viewer_navigation_controls.go_to_previous_page()

    def go_to_next_page(self) -> None:
        self.shell_widget.viewer_navigation_controls.go_to_next_page()

    def reset_zoom_view(self) -> None:
        self.shell_widget.viewer_navigation_controls.reset_zoom_view()

    def focus(self) -> None:
        self.shell_widget.setFocus()


def build_qt_signing_workspace_bundle(shell_widget: Any) -> SigningWorkspaceBundle:
    """Adapt one Qt shell widget into the typed workspace bundle at the Qt edge."""
    testing_adapter = getattr(shell_widget, "testing_adapter", None)
    if testing_adapter is None:
        raise TypeError("Qt signing shell widgets must expose 'testing_adapter'.")
    return SigningWorkspaceBundle(
        maintenance=QtSigningWorkspacePort(shell_widget=shell_widget),
        session=QtSigningWorkspaceSessionPort(shell_widget=shell_widget),
        testing=testing_adapter,
        view=QtWorkspaceView(shell=shell_widget),
    )


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
        return build_qt_signing_workspace_bundle(shell_widget)
