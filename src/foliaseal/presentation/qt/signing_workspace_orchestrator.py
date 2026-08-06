"""Shell-local orchestrator for startup and workspace-interaction execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from foliaseal.application import WorkspaceInteractionPlan
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
)
from foliaseal.presentation.qt.signing_workspace_action_bridge import (
    SigningWorkspaceActionBridge,
)
from foliaseal.presentation.qt.signing_workspace_interaction_bridge import (
    SigningWorkspaceInteractionBridge,
)
from foliaseal.presentation.qt.signing_workspace_review_bridge import (
    SigningWorkspaceReviewBridge,
)

if TYPE_CHECKING:
    from foliaseal.presentation.qt.signing_workspace_compatibility_surface import (
        SigningWorkspaceCompatibilitySurface,
    )
    from foliaseal.presentation.qt.signing_workspace_shell_surface import (
        SigningWorkspaceShellSurface,
    )


class SigningWorkspaceOrchestrator:
    """Hide startup ordering and ordered interaction-plan execution."""

    def __init__(
        self,
        *,
        interaction_bridge: SigningWorkspaceInteractionBridge,
        compatibility_surface: SigningWorkspaceCompatibilitySurface,
        shell_surface: SigningWorkspaceShellSurface,
        review_bridge: SigningWorkspaceReviewBridge,
        document_review_workspace: DocumentReviewWorkspaceSession,
        action_bridge: SigningWorkspaceActionBridge,
        refresh_viewer: Callable[[], None],
    ) -> None:
        self._interaction_bridge = interaction_bridge
        self._compatibility_surface = compatibility_surface
        self._shell_surface = shell_surface
        self._review_bridge = review_bridge
        self._document_review_workspace = document_review_workspace
        self._action_bridge = action_bridge
        self._refresh_viewer = refresh_viewer

    def bootstrap(self) -> None:
        self._compatibility_surface.install_widget_exports()
        self._refresh_viewer()
        self._review_bridge.apply_state(self._document_review_workspace.load())
        self._action_bridge.reload_state()

    def apply(self, plan: WorkspaceInteractionPlan) -> None:
        self._interaction_bridge.apply_plan(plan)
