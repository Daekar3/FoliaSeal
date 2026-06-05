"""Shell-internal runtime/controller for signing workspace orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application import (
    SignaturePlacementContext,
    SigningDraftWorkflow,
    WorkspaceInteractionPlan,
    WorkspaceInteractionSession,
)
from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
)
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.presentation.qt.signing_workspace_interaction_bridge import (
    SigningWorkspaceInteractionBridge,
)
from foliaseal.presentation.qt.signing_workspace_review_bridge import (
    SigningWorkspaceReviewBridge,
)


class SigningWorkspaceRuntime:
    """Own the remaining shell-local orchestration cluster."""

    def __init__(
        self,
        *,
        draft_workflow: SigningDraftWorkflow,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
    ) -> None:
        self._draft_workflow = draft_workflow
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._viewer_interaction_session: ViewerInteractionSession | None = None
        self._document_review_workspace: DocumentReviewWorkspaceSession | None = None
        self._workspace_interaction_session: WorkspaceInteractionSession | None = None
        self._review_bridge: SigningWorkspaceReviewBridge | None = None
        self._interaction_bridge: SigningWorkspaceInteractionBridge | None = None
        self._viewer_widget: Any = None
        self._result_label: Any = None

    def bind(
        self,
        *,
        viewer_interaction_session: ViewerInteractionSession,
        document_review_workspace: DocumentReviewWorkspaceSession,
        workspace_interaction_session: WorkspaceInteractionSession,
        review_bridge: SigningWorkspaceReviewBridge,
        interaction_bridge: SigningWorkspaceInteractionBridge,
        viewer_widget: Any,
        result_label: Any,
    ) -> None:
        self._viewer_interaction_session = viewer_interaction_session
        self._document_review_workspace = document_review_workspace
        self._workspace_interaction_session = workspace_interaction_session
        self._review_bridge = review_bridge
        self._interaction_bridge = interaction_bridge
        self._viewer_widget = viewer_widget
        self._result_label = result_label

    def on_viewer_selection(self, pdf_rect: PdfRect) -> None:
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().select_in_viewer(pdf_rect),
        )

    def on_viewer_error(self, message: str) -> None:
        self.emit_error(message)

    def on_viewer_interaction(self, name: str) -> None:
        if self._on_status_change is not None:
            self._on_status_change(name)

    def on_panel_change(self) -> None:
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().refresh_after_panel_change()
        )

    def on_page_change(self, page_number: int) -> None:
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().change_page(page_number),
        )

    def on_document_review_signature_selected(self, index: int) -> None:
        self._review_bridge_required().select_review_signature(index)

    def apply_workspace_interaction_plan(self, plan: WorkspaceInteractionPlan) -> None:
        self._interaction_bridge_required().apply_plan(plan)

    def apply_placement_context(
        self,
        placement_context: SignaturePlacementContext | None,
    ) -> None:
        if placement_context is None:
            return
        self._draft_workflow.set_placement_context(placement_context)

    def sync_signature_overlay(self) -> None:
        setter = getattr(self._viewer_widget_required(), "set_signature_overlay", None)
        if callable(setter):
            setter(self._draft_workflow.signature_rect)

    def refresh_review_jump_to_page_index(self, page_index: int) -> None:
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().refresh_navigation_to_page_index(
                page_index
            ),
        )

    def emit_error(self, message: str) -> None:
        self._set_sign_result_text(message, success=False)
        if self._on_error is not None:
            self._on_error(message)
            return
        raise RuntimeError(message)

    def _set_sign_result_text(self, message: str, *, success: bool | None = None) -> None:
        result_label = self._result_label_required()
        result_label.setText(message)
        if not hasattr(result_label, "setStyleSheet"):
            return
        if success is True:
            result_label.setStyleSheet("color: #1f6f2a; font-weight: 600;")
        elif success is False:
            result_label.setStyleSheet("color: #9f1d1d; font-weight: 600;")
        else:
            result_label.setStyleSheet("color: #444;")

    def _workspace_interaction_session_required(self) -> WorkspaceInteractionSession:
        if self._workspace_interaction_session is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a workspace session.")
        return self._workspace_interaction_session

    def _review_bridge_required(self) -> SigningWorkspaceReviewBridge:
        if self._review_bridge is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a review bridge.")
        return self._review_bridge

    def _interaction_bridge_required(self) -> SigningWorkspaceInteractionBridge:
        if self._interaction_bridge is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to an interaction bridge.")
        return self._interaction_bridge

    def _viewer_widget_required(self) -> Any:
        if self._viewer_widget is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a viewer widget.")
        return self._viewer_widget

    def _result_label_required(self) -> Any:
        if self._result_label is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a result label.")
        return self._result_label
