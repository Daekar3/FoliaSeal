"""Application-layer session for shell-level viewer and placement interactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
    DocumentReviewWorkspaceTransition,
)
from foliaseal.application.signing_draft_contracts import SignaturePlacementContext
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect


@dataclass(frozen=True)
class ApplyReviewTransition:
    """Apply a review/text transition returned by the review workspace."""

    transition: DocumentReviewWorkspaceTransition


@dataclass(frozen=True)
class EmitInteractionError:
    """Emit one user-facing interaction error and stop further work."""

    message: str


@dataclass(frozen=True)
class RefreshViewer:
    """Refresh the viewer, optionally preserving navigation intent."""

    navigation: bool = False
    error_summary: str = "Unable to refresh viewer"


@dataclass(frozen=True)
class RefreshCurrentPlacementContext:
    """Refresh placement context from the current viewer snapshot."""


@dataclass(frozen=True)
class ApplyPlacementContext:
    """Apply an explicit placement context already computed by the session."""

    placement_context: SignaturePlacementContext | None


@dataclass(frozen=True)
class ApplySignatureRect:
    """Apply a signature rectangle through the non-notifying panel path."""

    signature_rect: SignatureRect
    notify: bool = False


@dataclass(frozen=True)
class SyncSignatureOverlay:
    """Resync the signature overlay with current draft state."""


@dataclass(frozen=True)
class RefreshPreview:
    """Refresh the visible-signature preview."""


@dataclass(frozen=True)
class ReloadSigningActionState:
    """Reload signing-action state from the current boundary."""


@dataclass(frozen=True)
class InvalidateSigningAction:
    """Invalidate current signing-action state for the given reason."""

    reason: str


WorkspaceInteractionEffect: TypeAlias = (
    ApplyReviewTransition
    | EmitInteractionError
    | RefreshViewer
    | RefreshCurrentPlacementContext
    | ApplyPlacementContext
    | ApplySignatureRect
    | SyncSignatureOverlay
    | RefreshPreview
    | ReloadSigningActionState
    | InvalidateSigningAction
)


@dataclass(frozen=True)
class WorkspaceInteractionPlan:
    """One shell-facing ordered interaction plan with no Qt dependencies."""

    effects: tuple[WorkspaceInteractionEffect, ...]


@dataclass
class WorkspaceInteractionSession:
    """Own shell-level interaction sequencing above review and viewer helpers."""

    viewer_workflow: ViewerWorkflow
    viewer_interaction_session: ViewerInteractionSession
    document_review_workspace: DocumentReviewWorkspaceSession

    def select_in_viewer(self, pdf_rect: PdfRect) -> WorkspaceInteractionPlan:
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
            return WorkspaceInteractionPlan(
                effects=(ApplyReviewTransition(review_transition),)
            )
        selection_result = self.viewer_interaction_session.select_signature_rect(
            normalized_rect
        )
        if selection_result.error_message is not None:
            return WorkspaceInteractionPlan(
                effects=(EmitInteractionError(selection_result.error_message),)
            )
        signature_rect = selection_result.signature_rect
        if signature_rect is None:
            return WorkspaceInteractionPlan(effects=())
        return WorkspaceInteractionPlan(
            effects=(
                ApplyPlacementContext(selection_result.placement_context),
                ApplySignatureRect(signature_rect),
                SyncSignatureOverlay(),
                InvalidateSigningAction("selection"),
            )
        )

    def change_page(self, page_number: int) -> WorkspaceInteractionPlan:
        try:
            self.viewer_interaction_session.set_page_number(page_number)
        except Exception as exc:
            return WorkspaceInteractionPlan(
                effects=(EmitInteractionError(f"Unable to change PDF page: {exc}"),)
            )
        return WorkspaceInteractionPlan(
            effects=(
                RefreshViewer(
                    navigation=True,
                    error_summary="Unable to change PDF page",
                ),
                RefreshCurrentPlacementContext(),
                SyncSignatureOverlay(),
                InvalidateSigningAction("page"),
            )
        )

    def refresh_navigation_to_page_index(self, target_index: int) -> WorkspaceInteractionPlan:
        try:
            self.viewer_interaction_session.set_logical_page_index(target_index)
        except Exception as exc:
            return WorkspaceInteractionPlan(
                effects=(
                    EmitInteractionError(
                        f"Unable to show document text match: {exc}"
                    ),
                )
            )
        return WorkspaceInteractionPlan(
            effects=(
                RefreshViewer(
                    navigation=True,
                    error_summary="Unable to show document text match",
                ),
                RefreshCurrentPlacementContext(),
                SyncSignatureOverlay(),
            )
        )

    def refresh_after_panel_change(self) -> WorkspaceInteractionPlan:
        return WorkspaceInteractionPlan(
            effects=(
                RefreshCurrentPlacementContext(),
                SyncSignatureOverlay(),
                InvalidateSigningAction("panel"),
            )
        )

    def refresh_after_viewer_refresh(self) -> WorkspaceInteractionPlan:
        return WorkspaceInteractionPlan(
            effects=(
                RefreshViewer(),
                RefreshCurrentPlacementContext(),
                SyncSignatureOverlay(),
                RefreshPreview(),
                ReloadSigningActionState(),
            )
        )
