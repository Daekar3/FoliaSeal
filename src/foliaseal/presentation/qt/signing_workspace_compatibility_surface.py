"""Compatibility and harness-facing surface for the signing workspace shell."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application import (
    SigningDraftWorkflow,
    WorkspaceInteractionSession,
)
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
)
from foliaseal.application.document_text_search import DocumentTextSearchState
from foliaseal.application.document_text_selection import DocumentTextSelectionState
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureRect,
)
from foliaseal.presentation.qt.signing_workspace_interaction_bridge import (
    SigningWorkspaceInteractionBridge,
)
from foliaseal.presentation.qt.signing_workspace_properties_panel import (
    SignaturePropertiesPanel,
)
from foliaseal.presentation.qt.signing_workspace_review_bridge import (
    SigningWorkspaceReviewBridge,
)


def _text(line_edit: Any) -> str:
    text = getattr(line_edit, "text", None)
    return text() if callable(text) else ""


class SigningWorkspaceCompatibilitySurface:
    """Own the broad widget-export and harness/testing helper surface."""

    def __init__(
        self,
        *,
        widget: Any,
        properties_panel: SignaturePropertiesPanel,
        viewer_widget: Any,
        properties_scroll: Any,
        sidebar_container: Any,
        sidebar_surface: Any,
        sign_button: Any,
        document_text_query_input: Any,
        on_copy_text: Callable[[str], Any] | None,
        draft_workflow: SigningDraftWorkflow,
        document_review_workspace: DocumentReviewWorkspaceSession,
        review_bridge: SigningWorkspaceReviewBridge,
        viewer_workflow: ViewerWorkflow,
        viewer_interaction_session: ViewerInteractionSession,
        workspace_interaction_session: WorkspaceInteractionSession,
        interaction_bridge: SigningWorkspaceInteractionBridge,
        sync_placement_context_from_viewer: Callable[[], None],
        sync_signature_overlay: Callable[[], None],
        refresh_sign_button_state: Callable[[], None],
    ) -> None:
        self._widget = widget
        self._properties_panel = properties_panel
        self._viewer_widget = viewer_widget
        self._properties_scroll = properties_scroll
        self._sidebar_container = sidebar_container
        self._sidebar_surface = sidebar_surface
        self._sign_button = sign_button
        self._document_text_query_input = document_text_query_input
        self._on_copy_text = on_copy_text
        self._draft_workflow = draft_workflow
        self._document_review_workspace = document_review_workspace
        self._review_bridge = review_bridge
        self._viewer_workflow = viewer_workflow
        self._viewer_interaction_session = viewer_interaction_session
        self._workspace_interaction_session = workspace_interaction_session
        self._interaction_bridge = interaction_bridge
        self._sync_placement_context_from_viewer = sync_placement_context_from_viewer
        self._sync_signature_overlay = sync_signature_overlay
        self._refresh_sign_button_state = refresh_sign_button_state

    @property
    def properties_panel(self) -> SignaturePropertiesPanel:
        return self._properties_panel

    @property
    def viewer_widget(self) -> Any:
        return self._viewer_widget

    @property
    def viewer_workflow(self) -> ViewerWorkflow:
        return self._viewer_workflow

    @property
    def sidebar_surface(self) -> Any:
        return self._sidebar_surface

    @property
    def last_signing_result(self) -> Any:
        return getattr(self._widget, "last_signing_result", None)

    def install_widget_exports(self) -> None:
        self._widget.compat_surface = self  # type: ignore[attr-defined]
        self._widget.properties_panel = self._properties_panel  # type: ignore[attr-defined]
        self._widget.viewer_widget = self._viewer_widget  # type: ignore[attr-defined]
        self._widget.properties_scroll = self._properties_scroll  # type: ignore[attr-defined]
        self._widget.sidebar = self._sidebar_container  # type: ignore[attr-defined]
        self._widget.sidebar_surface = self._sidebar_surface  # type: ignore[attr-defined]
        destroyed_signal = getattr(self._widget, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: self._properties_panel.dispose())
        self._widget.last_signing_result = None  # type: ignore[attr-defined]
        self._widget.refresh_viewer = self.refresh_viewer  # type: ignore[attr-defined]
        self._widget.refresh_document_review = self.refresh_document_review  # type: ignore[attr-defined]
        self._widget.search_document_text = self.search_document_text  # type: ignore[attr-defined]
        self._widget.next_document_text_match = self.next_document_text_match  # type: ignore[attr-defined]
        self._widget.previous_document_text_match = self.previous_document_text_match  # type: ignore[attr-defined]
        self._widget.copy_current_document_text_match = (  # type: ignore[attr-defined]
            self.copy_current_document_text_match
        )
        self._widget.set_document_text_selection_mode = (  # type: ignore[attr-defined]
            self.set_document_text_selection_mode
        )
        self._widget.copy_selected_document_text = self.copy_selected_document_text  # type: ignore[attr-defined]
        self._widget.clear_selected_document_text = self.clear_selected_document_text  # type: ignore[attr-defined]
        self._widget.set_logical_page_index = self.set_logical_page_index  # type: ignore[attr-defined]
        self._widget.logical_page_index = self.logical_page_index  # type: ignore[attr-defined]
        self._widget.set_signature_rect = self.set_signature_rect  # type: ignore[attr-defined]
        self._widget.signature_rect = self.signature_rect  # type: ignore[attr-defined]
        self._widget.set_selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self.set_selected_certificate_configuration_id
        )
        self._widget.selected_certificate_configuration_id = (  # type: ignore[attr-defined]
            self.selected_certificate_configuration_id
        )
        self._widget.signature_appearance = self.signature_appearance  # type: ignore[attr-defined]
        self._widget.is_sign_action_enabled = self.is_sign_action_enabled  # type: ignore[attr-defined]

    def refresh_viewer(self) -> None:
        self._interaction_bridge.apply_plan(
            self._workspace_interaction_session.refresh_after_viewer_refresh(),
        )

    def refresh_document_review(self) -> DocumentReviewSummary:
        state = self._document_review_workspace.refresh_review()
        self._review_bridge.apply_state(state)
        return state.review.review_summary

    def search_document_text(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.search_text(
            _text(self._document_text_query_input)
        )
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.search_state

    def next_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.next_text_match()
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.search_state

    def previous_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace.previous_text_match()
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.search_state

    def copy_current_document_text_match(self) -> str | None:
        copy_text = self._document_review_workspace.copy_current_text_match()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        transition = self._document_review_workspace.set_text_selection_mode(enabled)
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.selection_mode_enabled

    def copy_selected_document_text(self) -> str | None:
        copy_text = self._document_review_workspace.copy_selected_text()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def clear_selected_document_text(self) -> DocumentTextSelectionState:
        transition = self._document_review_workspace.clear_selected_text()
        self._review_bridge.apply_transition(transition)
        return transition.state.document_text.selection_state

    def set_logical_page_index(self, page_index: int) -> None:
        self._viewer_interaction_session.set_logical_page_index(page_index)

    def logical_page_index(self) -> int:
        return self._viewer_workflow.session.current_page

    def set_signature_rect(
        self,
        *,
        page_index: int,
        left_pt: float,
        bottom_pt: float,
        width_pt: float,
        height_pt: float,
    ) -> SignatureRect:
        signature_rect = SignatureRect(
            page_index=page_index,
            left_pt=left_pt,
            bottom_pt=bottom_pt,
            width_pt=width_pt,
            height_pt=height_pt,
        )
        self._properties_panel.set_signature_rect(signature_rect, notify=False)
        self._interaction_bridge.apply_plan(
            self._workspace_interaction_session.refresh_after_panel_change()
        )
        return signature_rect

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self._properties_panel.set_signature_rect(signature_rect)
        jump_to_page = getattr(self._viewer_workflow, "jump_to_page", None)
        if callable(jump_to_page):
            jump_to_page(signature_rect.page_index)
        refresh = getattr(self._viewer_widget, "refresh", None)
        if callable(refresh):
            refresh(navigation=True)
        self._sync_placement_context_from_viewer()
        self._sync_signature_overlay()
        self._refresh_sign_button_state()

    def signature_rect(self) -> SignatureRect | None:
        return self._draft_workflow.signature_rect

    def set_selected_certificate_configuration_id(self, configuration_id: str | None) -> None:
        self._draft_workflow.selected_certificate_configuration_id = configuration_id
        self._properties_panel.load_from_workflow()

    def selected_certificate_configuration_id(self) -> str | None:
        return self._draft_workflow.selected_certificate_configuration_id

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._draft_workflow.signature_appearance

    def is_sign_action_enabled(self) -> bool:
        is_enabled = getattr(self._sign_button, "isEnabled", None)
        if callable(is_enabled):
            return bool(is_enabled())
        if hasattr(self._sign_button, "_enabled"):
            return bool(self._sign_button._enabled)  # type: ignore[attr-defined]
        return bool(getattr(self._sign_button, "enabled", False))
