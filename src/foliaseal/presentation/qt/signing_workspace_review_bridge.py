"""Shell-internal bridge for document review and document text behavior."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
    DocumentReviewWorkspaceState,
    DocumentReviewWorkspaceTransition,
    DocumentReviewWorkspaceViewerEffects,
)


class SigningWorkspaceReviewBridge:
    """Apply review/text state and viewer effects for the live signing shell."""

    def __init__(
        self,
        *,
        sidebar: Any,
        viewer_widget: Any,
        document_review_workspace: DocumentReviewWorkspaceSession,
        on_jump_to_page_index: Callable[[int], Any],
        can_copy_text: bool,
    ) -> None:
        self._sidebar = sidebar
        self._viewer_widget = viewer_widget
        self._document_review_workspace = document_review_workspace
        self._on_jump_to_page_index = on_jump_to_page_index
        self._can_copy_text = can_copy_text

    def apply_state(self, state: DocumentReviewWorkspaceState) -> None:
        self._sidebar.apply_document_review_workspace_state(
            state,
            can_copy_text=self._can_copy_text,
        )

    def select_review_signature(self, index: int) -> None:
        state = self._document_review_workspace.select_review_signature(index)
        self.apply_state(state)

    def apply_transition(self, transition: DocumentReviewWorkspaceTransition) -> None:
        self.apply_state(transition.state)
        self._apply_effects(transition.effects)

    def _apply_effects(self, effects: DocumentReviewWorkspaceViewerEffects) -> None:
        if effects.interaction_mode is not None:
            setter = getattr(self._viewer_widget, "set_interaction_mode", None)
            if callable(setter):
                setter(effects.interaction_mode)
        if effects.clear_highlights:
            clearer = getattr(self._viewer_widget, "clear_text_highlight_overlay", None)
            if callable(clearer):
                clearer()
        elif effects.highlight_page_index is not None:
            setter = getattr(self._viewer_widget, "set_text_highlight_overlay", None)
            if callable(setter):
                setter(
                    page_index=effects.highlight_page_index,
                    highlight_rects=effects.highlight_rects,
                )
        if effects.jump_to_page_index is None:
            return
        self._on_jump_to_page_index(effects.jump_to_page_index)
