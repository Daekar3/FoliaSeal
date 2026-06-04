"""Shell-internal bridge for workspace interaction plan execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application import (
    ApplyPlacementContext,
    ApplyReviewTransition,
    ApplySignatureRect,
    EmitInteractionError,
    InvalidateSigningAction,
    RefreshCurrentPlacementContext,
    RefreshPreview,
    RefreshViewer,
    ReloadSigningActionState,
    SyncSignatureOverlay,
    WorkspaceInteractionEffect,
    WorkspaceInteractionPlan,
)
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.domain.models import SignatureRect
from foliaseal.presentation.qt.signing_workspace_review_bridge import (
    SigningWorkspaceReviewBridge,
)


class SigningWorkspaceInteractionBridge:
    """Execute ordered workspace-interaction effects against live Qt collaborators."""

    def __init__(
        self,
        *,
        review_bridge: SigningWorkspaceReviewBridge,
        viewer_widget: Any,
        viewer_interaction_session: ViewerInteractionSession,
        apply_placement_context: Callable[[Any], None],
        apply_signature_rect: Callable[[SignatureRect, bool], None],
        sync_signature_overlay: Callable[[], None],
        refresh_preview: Callable[[], None],
        load_signing_action_state: Callable[[], None],
        invalidate_signing_action_state: Callable[[str], None],
        emit_error: Callable[[str], None],
    ) -> None:
        self._review_bridge = review_bridge
        self._viewer_widget = viewer_widget
        self._viewer_interaction_session = viewer_interaction_session
        self._apply_placement_context = apply_placement_context
        self._apply_signature_rect = apply_signature_rect
        self._sync_signature_overlay = sync_signature_overlay
        self._refresh_preview = refresh_preview
        self._load_signing_action_state = load_signing_action_state
        self._invalidate_signing_action_state = invalidate_signing_action_state
        self._emit_error = emit_error

    def apply_plan(self, plan: WorkspaceInteractionPlan) -> None:
        for effect in plan.effects:
            self._apply_effect(effect)

    def _apply_effect(self, effect: WorkspaceInteractionEffect) -> None:
        if isinstance(effect, ApplyReviewTransition):
            self._review_bridge.apply_transition(effect.transition)
            return
        if isinstance(effect, EmitInteractionError):
            self._emit_error(effect.message)
            return
        if isinstance(effect, RefreshViewer):
            try:
                self._viewer_widget.refresh(navigation=effect.navigation)
            except Exception as exc:
                self._emit_error(f"{effect.error_summary}: {exc}")
            return
        if isinstance(effect, RefreshCurrentPlacementContext):
            result = self._viewer_interaction_session.current_placement_context()
            self._apply_placement_context(result.placement_context)
            return
        if isinstance(effect, ApplyPlacementContext):
            self._apply_placement_context(effect.placement_context)
            return
        if isinstance(effect, ApplySignatureRect):
            self._apply_signature_rect(effect.signature_rect, effect.notify)
            return
        if isinstance(effect, SyncSignatureOverlay):
            self._sync_signature_overlay()
            return
        if isinstance(effect, RefreshPreview):
            self._refresh_preview()
            return
        if isinstance(effect, ReloadSigningActionState):
            self._load_signing_action_state()
            return
        if isinstance(effect, InvalidateSigningAction):
            self._invalidate_signing_action_state(effect.reason)
            return
        raise TypeError(f"Unsupported workspace interaction effect: {effect!r}")
