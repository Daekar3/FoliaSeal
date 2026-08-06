"""Deep app-frame boundary for opening and closing signing workspaces."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application.certificate_catalog_repository import CertificateCatalogRepository
from foliaseal.application.reusable_signing_objects import ReusableSigningObjects
from foliaseal.application.signing_material_resolver import CertificateSigningMaterialPort
from foliaseal.domain.models import SigningRequest
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame_workspace_open import (
    OpenWorkspaceCommand,
    WorkspaceHandle,
    WorkspaceOpenPort,
)
from foliaseal.presentation.qt.signing_shell import SigningRequestExecutor
from foliaseal.presentation.qt.signing_workspace_lifecycle import (
    SigningWorkspaceLifecycle,
    WorkspaceMountPort,
)


@dataclass(frozen=True)
class SigningWorkspaceEnvironment:
    """Injected app dependencies used to build each open command."""

    app_settings: Callable[[], AppSettings]
    app_settings_store: AppSettingsStore | None
    certificate_catalog_store: CertificateCatalogRepository | None
    sign_executor: SigningRequestExecutor | None
    on_sign_request: Callable[[SigningRequest], None] | None
    reopen_target: Callable[[str | Path], Any | None] | None
    on_error: Callable[[str], None] | None
    on_status_change: Callable[[str], None] | None
    reusable_objects: ReusableSigningObjects | None = None
    certificate_material_port: CertificateSigningMaterialPort | None = None

    def command_for(self, source_pdf: Path) -> OpenWorkspaceCommand:
        return OpenWorkspaceCommand(
            source_pdf=source_pdf,
            app_settings=self.app_settings(),
            app_settings_store=self.app_settings_store,
            certificate_catalog_store=self.certificate_catalog_store,
            certificate_material_port=self.certificate_material_port,
            reusable_objects=self.reusable_objects,
            sign_executor=self.sign_executor,
            on_sign_request=self.on_sign_request,
            reopen_target=self.reopen_target,
            on_error=self.on_error,
            on_status_change=self.on_status_change,
        )


class SigningWorkspaceHost:
    """Own the frame-facing open/close/active workspace lifecycle."""

    def __init__(
        self,
        *,
        environment: SigningWorkspaceEnvironment,
        workspace_open_port: WorkspaceOpenPort,
        mount_port: WorkspaceMountPort,
    ) -> None:
        self._environment = environment
        self._lifecycle = SigningWorkspaceLifecycle(
            workspace_open_port=workspace_open_port,
            mount_port=mount_port,
        )

    def open(self, source_pdf: str | Path) -> WorkspaceHandle:
        """Atomically replace the active workspace with ``source_pdf``."""

        return self._lifecycle.replace(
            self._environment.command_for(Path(source_pdf))
        )

    def close(self) -> None:
        """Dispose the active workspace, if any."""

        self._lifecycle.close()

    def active(self) -> WorkspaceHandle | None:
        """Return the currently published workspace handle."""

        return self._lifecycle.active()
