"""Workspace-open boundary for the Qt app frame."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from foliaseal.application import SigningDraftWorkflow, suggest_signed_output_path
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.signing_shell import SigningRequestExecutor
from foliaseal.presentation.qt.signing_shell_port import (
    SigningWorkspaceBootstrap,
    SigningWorkspaceFactory,
    SigningWorkspacePort,
)
from foliaseal.presentation.qt.signing_workspace_testing_port import (
    SigningWorkspaceTestingPort,
)


@dataclass(frozen=True)
class OpenWorkspaceCommand:
    """Typed inputs required to open one signing workspace."""

    source_pdf: Path
    app_settings: AppSettings
    app_settings_store: AppSettingsStore | None = None
    certificate_catalog_store: CertificateCatalogStore | None = None
    certificate_secret_provider: Any | None = None
    preset_catalog_store: SignaturePresetCatalogStore | None = None
    sign_executor: SigningRequestExecutor | None = None
    on_sign_request: Callable[[SigningRequest], None] | None = None
    reopen_target: Callable[[str | Path], Any | None] | None = None
    on_error: Callable[[str], None] | None = None
    on_status_change: Callable[[str], None] | None = None


@dataclass(frozen=True)
class WorkspaceHandle:
    """The one active workspace record published after a successful mount."""

    source_pdf: Path
    widget: Any
    shell: SigningWorkspacePort
    testing: SigningWorkspaceTestingPort
    viewer_workflow: ViewerWorkflow
    signing_workflow: SigningDraftWorkflow


@dataclass(frozen=True)
class WorkspaceOpenPort(Protocol):
    """Open one signing workspace from app-frame command inputs."""

    def open_workspace(self, command: OpenWorkspaceCommand) -> WorkspaceHandle:
        """Build the workspace or raise."""


class PdfPageCountPort(Protocol):
    """Load the page count for one source PDF."""

    def load_page_count(self, pdf_path: Path) -> int:
        """Return a positive page count or raise."""


@dataclass(frozen=True)
class WorkspaceCompositionRequest:
    """Inputs required once the PDF page count is known."""

    command: OpenWorkspaceCommand
    page_count: int


class WorkspaceCompositionPort(Protocol):
    """Compose one live signing workspace from open inputs."""

    def compose(self, request: WorkspaceCompositionRequest) -> WorkspaceHandle:
        """Build the workspace outcome or raise."""


@dataclass(frozen=True)
class QtPdfPageCountLoader:
    """Qt-backed page-count loader used by the app-frame open boundary."""

    qpdf_document: type[Any]

    def load_page_count(self, pdf_path: Path) -> int:
        document = self.qpdf_document()
        status = document.load(str(pdf_path))
        if status != self.qpdf_document.Error.None_:
            raise RuntimeError(f"Failed to load PDF document: {pdf_path}")
        page_count = int(document.pageCount())
        if page_count <= 0:
            raise RuntimeError(f"PDF has no pages: {pdf_path}")
        return page_count


@dataclass(frozen=True)
class SigningWorkspaceCompositionService:
    """Build one live signing workspace from page-count-validated inputs."""

    render_backend_factory: Callable[[], Any]
    shell_factory: SigningWorkspaceFactory

    def compose(self, request: WorkspaceCompositionRequest) -> WorkspaceHandle:
        command = request.command
        source_path = command.source_pdf
        viewer_workflow = ViewerWorkflow(
            document_path=str(source_path),
            render_backend=self.render_backend_factory(),
            session=ViewerSession(page_count=request.page_count),
        )
        signing_workflow = SigningDraftWorkflow(
            input_pdf_path=str(source_path),
            output_pdf_path=str(
                suggest_signed_output_path(
                    input_pdf_path=source_path,
                    default_output_directory=command.app_settings.default_output_directory,
                )
            ),
            certificate_path="",
            passphrase="",
            tsa_url="",
            timestamp_required=False,
        )
        bundle = self.shell_factory.create(
            SigningWorkspaceBootstrap(
                viewer_workflow=viewer_workflow,
                signing_workflow=signing_workflow,
                certificate_catalog_store=command.certificate_catalog_store,
                certificate_secret_provider=command.certificate_secret_provider,
                preset_catalog_store=command.preset_catalog_store,
                app_settings=command.app_settings,
                app_settings_store=command.app_settings_store,
                sign_executor=command.sign_executor,
                on_sign_request=command.on_sign_request,
                on_open_signed_output=command.reopen_target,
                on_error=command.on_error,
                on_status_change=command.on_status_change,
            )
        )
        return WorkspaceHandle(
            source_pdf=source_path,
            widget=bundle.widget,
            shell=bundle.port,
            testing=bundle.testing_adapter,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
        )


@dataclass(frozen=True)
class WorkspaceOpenService:
    """App-frame-facing service that opens one live signing workspace."""

    page_count_port: PdfPageCountPort
    composition_port: WorkspaceCompositionPort

    def open_workspace(self, command: OpenWorkspaceCommand) -> WorkspaceHandle:
        page_count = self.page_count_port.load_page_count(command.source_pdf)
        return self.composition_port.compose(
            WorkspaceCompositionRequest(command=command, page_count=page_count)
        )
