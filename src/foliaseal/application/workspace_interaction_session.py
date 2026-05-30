"""Application-layer session for shell-level viewer and placement interactions."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
    DocumentReviewWorkspaceTransition,
)
from foliaseal.application.signing_draft_workflow import SignaturePlacementContext
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect


@dataclass(frozen=True)
class WorkspaceInteractionTransition:
    """One shell-facing interaction transition with no Qt dependencies."""

    review_transition: DocumentReviewWorkspaceTransition | None = None
    signature_rect: SignatureRect | None = None
    placement_context: SignaturePlacementContext | None = None
    refresh_viewer: bool = False
    navigation_refresh: bool = False
    refresh_current_placement_context: bool = False
    sync_signature_overlay: bool = False
    refresh_preview: bool = False
    reload_signing_action_state: bool = False
    signing_action_invalidation_reason: str | None = None
    error_message: str | None = None


@dataclass
class WorkspaceInteractionSession:
    """Own shell-level interaction sequencing above review and viewer helpers."""

    viewer_workflow: ViewerWorkflow
    viewer_interaction_session: ViewerInteractionSession
    document_review_workspace: DocumentReviewWorkspaceSession

    def select_in_viewer(self, pdf_rect: PdfRect) -> WorkspaceInteractionTransition:
        snapshot = getattr(self.viewer_workflow, "snapshot", None)
        page_index = (
            snapshot.page_index
            if snapshot is not None
            else self.viewer_workflow.session.current_page
        )
        normalized_rect = pdf_rect.normalized()
        review_transition = self.document_review_workspace.handle_viewer_selection(
            page_index=page_index,
            selection_rect=normalized_rect,
        )
        if review_transition.viewer_selection_consumed:
            return WorkspaceInteractionTransition(review_transition=review_transition)
        selection_result = self.viewer_interaction_session.select_signature_rect(
            normalized_rect
        )
        if selection_result.error_message is not None:
            return WorkspaceInteractionTransition(error_message=selection_result.error_message)
        return WorkspaceInteractionTransition(
            signature_rect=selection_result.signature_rect,
            placement_context=selection_result.placement_context,
            sync_signature_overlay=True,
            signing_action_invalidation_reason="selection",
        )

    def change_page(self, page_number: int) -> WorkspaceInteractionTransition:
        try:
            self.viewer_interaction_session.set_page_number(page_number)
        except Exception as exc:
            return WorkspaceInteractionTransition(
                error_message=f"Unable to change PDF page: {exc}"
            )
        return WorkspaceInteractionTransition(
            refresh_viewer=True,
            navigation_refresh=True,
            refresh_current_placement_context=True,
            sync_signature_overlay=True,
            signing_action_invalidation_reason="page",
        )

    def refresh_navigation_to_page_index(self, target_index: int) -> WorkspaceInteractionTransition:
        try:
            self.viewer_interaction_session.set_logical_page_index(target_index)
        except Exception as exc:
            return WorkspaceInteractionTransition(
                error_message=f"Unable to show document text match: {exc}"
            )
        return WorkspaceInteractionTransition(
            refresh_viewer=True,
            navigation_refresh=True,
            refresh_current_placement_context=True,
            sync_signature_overlay=True,
        )

    def refresh_after_panel_change(self) -> WorkspaceInteractionTransition:
        return WorkspaceInteractionTransition(
            refresh_current_placement_context=True,
            sync_signature_overlay=True,
            signing_action_invalidation_reason="panel",
        )

    def refresh_after_viewer_refresh(self) -> WorkspaceInteractionTransition:
        return WorkspaceInteractionTransition(
            refresh_viewer=True,
            refresh_current_placement_context=True,
            sync_signature_overlay=True,
            refresh_preview=True,
            reload_signing_action_state=True,
        )
