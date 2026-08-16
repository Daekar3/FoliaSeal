"""Shell-internal runtime/controller for signing workspace orchestration."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from foliaseal.application import (
    DocumentLinkActivationService,
    DocumentLinkInspector,
    SignaturePlacementContext,
    SigningDraftWorkflow,
    WorkspaceInteractionPlan,
    WorkspaceInteractionSession,
)
from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_link_activation import ViewerLinkHistory
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceSession,
)
from foliaseal.application.document_safety import (
    LinkDecision,
    LinkDecisionKind,
    LinkInteractionMode,
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
    SigningRequest,
    SigningResult,
)
from foliaseal.presentation.qt.signing_workspace_diagnostics import (
    SigningWorkspaceSnapshot,
)
from foliaseal.presentation.qt.signing_workspace_orchestrator import (
    SigningWorkspaceOrchestrator,
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


def _snapshot_current_request(workflow: SigningDraftWorkflow) -> SigningRequest | None:
    signature_rect = workflow.current_signature_rect
    signature_appearance = workflow.current_signature_appearance
    if signature_rect is None or signature_appearance is None:
        return None
    return SigningRequest(
        input_pdf_path=workflow.input_pdf_path,
        output_pdf_path=workflow.output_pdf_path,
        certificate_path=workflow.certificate_path,
        passphrase=workflow.passphrase,
        tsa_url=workflow.tsa_url,
        timestamp_required=workflow.timestamp_required,
        trust_policy=workflow.trust_policy,
        certificate_alias=workflow.certificate_alias,
        signature_rect=signature_rect,
        signature_field_name=getattr(workflow, "signature_field_name", None),
        signature_appearance=signature_appearance,
    )


class SigningWorkspaceRuntime:
    """Own the remaining shell-local orchestration cluster."""

    def __init__(
        self,
        *,
        draft_workflow: SigningDraftWorkflow,
        on_copy_text: Callable[[str], Any] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_status_change: Callable[[str], None] | None = None,
        document_link_inspector: DocumentLinkInspector | None = None,
        on_external_link_confirmation: Callable[[LinkDecision], Any] | None = None,
    ) -> None:
        self._draft_workflow = draft_workflow
        self._on_copy_text = on_copy_text
        self._on_error = on_error
        self._on_status_change = on_status_change
        self._document_link_inspector = document_link_inspector
        self._on_external_link_confirmation = on_external_link_confirmation
        self._link_activation_service = DocumentLinkActivationService()
        self._link_history = ViewerLinkHistory()
        self._viewer_interaction_session: ViewerInteractionSession | None = None
        self._viewer_workflow: ViewerWorkflow | None = None
        self._document_review_workspace: DocumentReviewWorkspaceSession | None = None
        self._workspace_interaction_session: WorkspaceInteractionSession | None = None
        self._review_bridge: SigningWorkspaceReviewBridge | None = None
        self._orchestrator: SigningWorkspaceOrchestrator | None = None
        self._properties_panel: SignaturePropertiesPanel | None = None
        self._viewer_widget: Any = None
        self._document_text_query_input: Any = None
        self._sign_button: Any = None
        self._refresh_sign_button_state: Callable[[], None] | None = None
        self._refresh_page_navigation_state: Callable[[], None] | None = None
        self._result_label: Any = None

    def bind(
        self,
        *,
        viewer_interaction_session: ViewerInteractionSession,
        viewer_workflow: ViewerWorkflow,
        document_review_workspace: DocumentReviewWorkspaceSession,
        workspace_interaction_session: WorkspaceInteractionSession,
        review_bridge: SigningWorkspaceReviewBridge,
        orchestrator: SigningWorkspaceOrchestrator,
        properties_panel: SignaturePropertiesPanel,
        viewer_widget: Any,
        document_text_query_input: Any,
        sign_button: Any,
        refresh_sign_button_state: Callable[[], None],
        refresh_page_navigation_state: Callable[[], None],
        result_label: Any,
    ) -> None:
        self._viewer_interaction_session = viewer_interaction_session
        self._viewer_workflow = viewer_workflow
        self._document_review_workspace = document_review_workspace
        self._workspace_interaction_session = workspace_interaction_session
        self._review_bridge = review_bridge
        self._orchestrator = orchestrator
        self._properties_panel = properties_panel
        self._viewer_widget = viewer_widget
        self._document_text_query_input = document_text_query_input
        self._sign_button = sign_button
        self._refresh_sign_button_state = refresh_sign_button_state
        self._refresh_page_navigation_state = refresh_page_navigation_state
        self._result_label = result_label
        self._last_panel_signature_rect = self._draft_workflow.signature_rect
        self._link_history.reset(viewer_workflow.session.current_page)

    def on_viewer_selection(self, pdf_rect: PdfRect) -> None:
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().select_in_viewer(pdf_rect),
        )
        if self._on_status_change is not None:
            self._on_status_change("document_text_selection_changed")

    def on_viewer_error(self, message: str) -> None:
        self.emit_error(message)

    def on_viewer_link_click(self, pdf_x: float, pdf_y: float) -> None:
        """Resolve a Pan click through link policy and route its typed outcome."""
        workflow = self._viewer_workflow_required()
        snapshot = workflow.snapshot
        if snapshot is None:
            self._emit_link_status("link_inspection_unavailable")
            return
        inspector = self._document_link_inspector
        if inspector is None:
            inspector_candidate = getattr(workflow.render_backend, "inspect_links", None)
            if callable(inspector_candidate):
                inspector = workflow.render_backend  # type: ignore[assignment]
        if inspector is None:
            self._emit_link_status("link_inspection_unavailable")
            return
        try:
            links = inspector.inspect_links(workflow.document_path, snapshot.page_index)
        except Exception:
            self._emit_link_status("link_inspection_unavailable")
            return
        activation = self._link_activation_service.resolve(
            page_index=snapshot.page_index,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            links=tuple(links),
            interaction_mode=LinkInteractionMode.PAN,
        )
        decision = activation.decision
        if decision is None:
            return
        if decision.page_index is not None and decision.kind is LinkDecisionKind.ALLOW_INTERNAL:
            from_page = snapshot.page_index
            try:
                self.refresh_review_jump_to_page_index(decision.page_index)
            except Exception:
                self._emit_link_status("link_navigation_failed")
                return
            self._link_history.record_internal_navigation(
                from_page_index=from_page,
                to_page_index=decision.page_index,
            )
            self._emit_link_status("link_internal_navigation")
            return
        if decision.kind is LinkDecisionKind.CONFIRM_EXTERNAL:
            if self._on_external_link_confirmation is not None:
                self._on_external_link_confirmation(decision)
            else:
                self._emit_link_status("link_external_confirmation_required")
            return
        self._emit_link_status("link_blocked")

    def go_back_link(self) -> None:
        target = self._link_history.back()
        if target is None:
            self._emit_link_status("link_history_back_unavailable")
            return
        try:
            self.refresh_review_jump_to_page_index(target, preserve_link_history=True)
        except Exception:
            self._link_history.reset(self._viewer_workflow_required().session.current_page)
            self._emit_link_status("link_navigation_failed")
            return
        self._emit_link_status("link_history_back")

    def go_forward_link(self) -> None:
        target = self._link_history.forward()
        if target is None:
            self._emit_link_status("link_history_forward_unavailable")
            return
        try:
            self.refresh_review_jump_to_page_index(target, preserve_link_history=True)
        except Exception:
            self._link_history.reset(self._viewer_workflow_required().session.current_page)
            self._emit_link_status("link_navigation_failed")
            return
        self._emit_link_status("link_history_forward")

    def can_go_back_link(self) -> bool:
        return self._link_history.can_go_back

    def can_go_forward_link(self) -> bool:
        return self._link_history.can_go_forward

    def create_keyboard_placement(self) -> SignatureRect | None:
        result = self._viewer_interaction_session_required().create_centered_signature_rect()
        if result.error_message is not None:
            self.emit_error(result.error_message)
            return None
        if result.signature_rect is not None:
            self.apply_signature_rect_placement(result.signature_rect)
        return result.signature_rect

    def move_keyboard_placement(self, delta_x_pt: float, delta_y_pt: float) -> SignatureRect | None:
        current = self._draft_workflow.signature_rect
        if current is None:
            return None
        result = self._viewer_interaction_session_required().move_signature_rect(
            current,
            delta_x_pt=delta_x_pt,
            delta_y_pt=delta_y_pt,
        )
        if result.error_message is not None:
            self.emit_error(result.error_message)
            return None
        if result.signature_rect is not None:
            self.apply_signature_rect_placement(result.signature_rect)
        return result.signature_rect

    def resize_keyboard_placement(
        self, delta_width_pt: float, delta_height_pt: float
    ) -> SignatureRect | None:
        current = self._draft_workflow.signature_rect
        if current is None:
            return None
        result = self._viewer_interaction_session_required().resize_signature_rect(
            current,
            delta_width_pt=delta_width_pt,
            delta_height_pt=delta_height_pt,
        )
        if result.error_message is not None:
            self.emit_error(result.error_message)
            return None
        if result.signature_rect is not None:
            self.apply_signature_rect_placement(result.signature_rect)
        return result.signature_rect

    def recover_keyboard_placement(self) -> SignatureRect | None:
        current = self._draft_workflow.signature_rect
        if current is None:
            return None
        result = self._viewer_interaction_session_required().move_signature_rect_fully_onto_page(
            current
        )
        if result.error_message is not None:
            self.emit_error(result.error_message)
            return None
        if result.signature_rect is not None:
            self.apply_signature_rect_placement(result.signature_rect)
        return result.signature_rect

    def apply_keyboard_placement(
        self, signature_rect: SignatureRect | None
    ) -> SignatureRect | None:
        """Apply a keyboard history target, including deletion."""
        if signature_rect is None:
            self._properties_panel_required().set_signature_rect(None)
            self.sync_signature_overlay()
            self._refresh_sign_button_state_required()()
            if self._on_status_change is not None:
                self._on_status_change("signing_readiness_changed")
            return None
        self.apply_signature_rect_placement(signature_rect)
        return signature_rect

    def can_undo_placement(self) -> bool:
        """Return whether the active viewer can undo a placement mutation."""

        capability = getattr(self._viewer_widget_required(), "can_undo_signature_placement", None)
        return bool(capability()) if callable(capability) else False

    def can_redo_placement(self) -> bool:
        """Return whether the active viewer can redo a placement mutation."""

        capability = getattr(self._viewer_widget_required(), "can_redo_signature_placement", None)
        return bool(capability()) if callable(capability) else False

    def undo_placement(self) -> SignatureRect | None:
        """Undo one placement mutation and refresh readiness projections."""

        undo = getattr(self._viewer_widget_required(), "undo_signature_placement", None)
        result = undo() if callable(undo) else self._draft_workflow.signature_rect
        if self._on_status_change is not None:
            self._on_status_change("signing_readiness_changed")
        return result

    def redo_placement(self) -> SignatureRect | None:
        """Redo one placement mutation and refresh readiness projections."""

        redo = getattr(self._viewer_widget_required(), "redo_signature_placement", None)
        result = redo() if callable(redo) else self._draft_workflow.signature_rect
        if self._on_status_change is not None:
            self._on_status_change("signing_readiness_changed")
        return result

    def on_viewer_interaction(self, name: str) -> None:
        if name == "navigation_changed":
            self.clear_selected_document_text()
            self.clear_document_review_highlight()
            self._refresh_page_navigation_state_required()()
        if name == "text_selection_clear_requested":
            self.clear_selected_document_text()
        if self._on_status_change is not None:
            self._on_status_change(name)

    def on_panel_change(self) -> None:
        current_signature_rect = self._draft_workflow.signature_rect
        record_edit = getattr(self._viewer_widget_required(), "record_signature_edit", None)
        clear_history = getattr(self._viewer_widget_required(), "clear_signature_history", None)
        if current_signature_rect != self._last_panel_signature_rect:
            if callable(record_edit):
                record_edit(current_signature_rect)
        elif callable(clear_history):
            clear_history()
        self._last_panel_signature_rect = current_signature_rect
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().refresh_after_panel_change()
        )
        if self._on_status_change is not None:
            self._on_status_change("signing_readiness_changed")

    def clear_signature_history(self) -> None:
        clear_history = getattr(self._viewer_widget_required(), "clear_signature_history", None)
        if callable(clear_history):
            clear_history()

    def on_page_change(self, page_number: int) -> None:
        if self._viewer_workflow_required().session.current_page != page_number - 1:
            self.clear_selected_document_text()
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().change_page(page_number),
        )
        self._link_history.reset(self._viewer_workflow_required().session.current_page)
        self._refresh_page_navigation_state_required()()
        if self._on_status_change is not None:
            self._on_status_change("signing_readiness_changed")

    def on_document_review_signature_selected(self, index: int) -> None:
        self._review_bridge_required().select_review_signature(index)

    def document_review_state(self) -> Any:
        return self._document_review_workspace_required().current_state()

    def select_document_review_item(self, signature_id: str) -> Any:
        transition = self._document_review_workspace_required().select_review_item(signature_id)
        self._review_bridge_required().apply_transition(transition)
        return transition.state

    def clear_document_review_highlight(self) -> None:
        self._review_bridge_required().clear_review_highlight()

    def refresh_viewer(self) -> None:
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().refresh_after_viewer_refresh()
        )
        self._refresh_page_navigation_state_required()()

    def refresh_document_review(self) -> DocumentReviewSummary:
        state = self._document_review_workspace_required().refresh_review()
        self._review_bridge_required().apply_state(state)
        return state.review.review_summary

    def search_document_text(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace_required().search_text(
            _text(self._document_text_query_input)
        )
        self._review_bridge_required().apply_transition(transition)
        return transition.state.document_text.search_state

    def focus_document_search(self) -> None:
        focus = getattr(self._document_text_query_input, "setFocus", None)
        if callable(focus):
            focus()
        select_all = getattr(self._document_text_query_input, "selectAll", None)
        if callable(select_all):
            select_all()

    def next_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace_required().next_text_match()
        self._review_bridge_required().apply_transition(transition)
        return transition.state.document_text.search_state

    def previous_document_text_match(self) -> DocumentTextSearchState:
        transition = self._document_review_workspace_required().previous_text_match()
        self._review_bridge_required().apply_transition(transition)
        return transition.state.document_text.search_state

    def copy_current_document_text_match(self) -> str | None:
        copy_text = self._document_review_workspace_required().copy_current_text_match()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def set_document_text_selection_mode(self, enabled: bool) -> bool:
        transition = self._document_review_workspace_required().set_text_selection_mode(enabled)
        self._review_bridge_required().apply_transition(transition)
        if self._on_status_change is not None:
            self._on_status_change("document_text_mode_changed")
        return transition.state.document_text.selection_mode_enabled

    def can_select_all_document_text(self) -> bool:
        """Return whether the active viewer has a current page for Select All."""

        return self.logical_page_index() >= 0

    def select_all_document_text(self) -> DocumentTextSelectionState:
        """Select all extractable text on the viewer's current page."""

        transition = self._document_review_workspace_required().select_all_text(
            page_index=self.logical_page_index(),
        )
        self._review_bridge_required().apply_transition(transition)
        if self._on_status_change is not None:
            self._on_status_change("document_text_selection_changed")
        return transition.state.document_text.selection_state

    def set_viewer_interaction_mode(self, mode: str) -> str:
        """Select the explicit Pan, Place, or Text viewer tool."""
        if mode not in {"pan", "signature", "text"}:
            raise ValueError(f"Unsupported viewer interaction mode: {mode}")
        if mode != "text" and self.document_text_selection_mode_enabled():
            transition = self._document_review_workspace_required().set_text_selection_mode(False)
            self._review_bridge_required().apply_transition(transition)
        setter = getattr(self._viewer_widget_required(), "set_interaction_mode", None)
        if not callable(setter):
            raise RuntimeError("The active viewer does not expose interaction modes.")
        setter(mode)
        if self._on_status_change is not None:
            self._on_status_change(f"viewer_mode_{mode}")
        return mode

    def can_place_signature_placement(self) -> bool:
        return (
            self._draft_workflow.signature_field_name is None
            and self._draft_workflow.signature_rect is None
        )

    def can_adjust_signature_placement(self) -> bool:
        return (
            self._draft_workflow.signature_field_name is None
            and self._draft_workflow.signature_rect is not None
        )

    def can_remove_signature_placement(self) -> bool:
        return self.can_adjust_signature_placement()

    def remove_signature_placement(self) -> bool:
        if not self.can_remove_signature_placement():
            return False
        self.apply_keyboard_placement(None)
        if self._on_status_change is not None:
            self._on_status_change("placement_removed")
        return True

    def document_text_selection_mode_enabled(self) -> bool:
        state = self._document_review_workspace_required().current_state()
        return state.document_text.selection_mode_enabled

    def can_copy_selected_document_text(self) -> bool:
        state = self._document_review_workspace_required().current_state()
        return state.document_text.selection_state.can_copy

    def copy_selected_document_text(self) -> str | None:
        copy_text = self._document_review_workspace_required().copy_selected_text()
        if copy_text is None or self._on_copy_text is None:
            return None
        self._on_copy_text(copy_text)
        return copy_text

    def clear_selected_document_text(self) -> DocumentTextSelectionState:
        transition = self._document_review_workspace_required().clear_selected_text()
        self._review_bridge_required().apply_transition(transition)
        if self._on_status_change is not None:
            self._on_status_change("document_text_selection_changed")
        return transition.state.document_text.selection_state

    def set_logical_page_index(self, page_index: int) -> None:
        self._viewer_interaction_session_required().set_logical_page_index(page_index)
        self._link_history.reset(page_index)
        self._refresh_page_navigation_state_required()()

    def logical_page_index(self) -> int:
        return self._viewer_workflow_required().session.current_page

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
        self._properties_panel_required().set_signature_rect(signature_rect, notify=False)
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().refresh_after_panel_change()
        )
        return signature_rect

    def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None:
        self._properties_panel_required().set_signature_rect(signature_rect)
        jump_to_page = getattr(self._viewer_workflow_required(), "jump_to_page", None)
        if callable(jump_to_page):
            jump_to_page(signature_rect.page_index)
        refresh = getattr(self._viewer_widget_required(), "refresh", None)
        if callable(refresh):
            refresh(navigation=True)
        placement_context = (
            self._viewer_interaction_session_required()
            .current_placement_context()
            .placement_context
        )
        self.apply_placement_context(placement_context)
        self.sync_signature_overlay()
        self._refresh_sign_button_state_required()()
        if self._on_status_change is not None:
            self._on_status_change("signing_readiness_changed")

    def select_signature_field(self, field_name: str, signature_rect: SignatureRect) -> None:
        """Target an existing unsigned field and lock its page/geometry."""
        self._draft_workflow.select_signature_field(
            field_name=field_name,
            signature_rect=signature_rect,
        )
        self._properties_panel_required().set_signature_rect(signature_rect, notify=False)
        jump_to_page = getattr(self._viewer_workflow_required(), "jump_to_page", None)
        if callable(jump_to_page):
            jump_to_page(signature_rect.page_index)
        refresh = getattr(self._viewer_widget_required(), "refresh", None)
        if callable(refresh):
            refresh(navigation=True)
        self.sync_signature_overlay()
        self._refresh_sign_button_state_required()()

    def signature_rect(self) -> SignatureRect | None:
        return self._draft_workflow.signature_rect

    def current_placement_context(self) -> SignaturePlacementContext | None:
        """Return the active visible-page context without mutating the draft."""

        return (
            self._viewer_interaction_session_required()
            .current_placement_context()
            .placement_context
        )

    def set_selected_certificate_configuration_id(self, configuration_id: str | None) -> None:
        self._draft_workflow.selected_certificate_configuration_id = configuration_id
        self._properties_panel_required().load_from_workflow()

    def selected_certificate_configuration_id(self) -> str | None:
        return self._draft_workflow.selected_certificate_configuration_id

    def signature_appearance(self) -> SignatureAppearance | None:
        return self._draft_workflow.signature_appearance

    def set_timestamp_required(self, required: bool) -> None:
        self._draft_workflow.timestamp_required = required
        self._properties_panel_required().load_from_workflow()

    def current_request(self) -> SigningRequest | None:
        return _snapshot_current_request(self._draft_workflow)

    def snapshot(
        self,
        *,
        last_signing_result: SigningResult | None = None,
    ) -> SigningWorkspaceSnapshot:
        """Return one coherent read model for diagnostics and harness callers."""

        return SigningWorkspaceSnapshot(
            logical_page_index=self.logical_page_index(),
            signature_rect=self.signature_rect(),
            signature_appearance=self.signature_appearance(),
            selected_certificate_configuration_id=(
                self.selected_certificate_configuration_id()
            ),
            timestamp_required=self._draft_workflow.timestamp_required,
            current_request=self.current_request(),
            sign_action_enabled=self.is_sign_action_enabled(),
            last_signing_result=last_signing_result,
        )

    def is_sign_action_enabled(self) -> bool:
        sign_button = self._sign_button_required()
        is_enabled = getattr(sign_button, "isEnabled", None)
        if callable(is_enabled):
            return bool(is_enabled())
        if hasattr(sign_button, "_enabled"):
            return bool(sign_button._enabled)  # type: ignore[attr-defined]
        return bool(getattr(sign_button, "enabled", False))

    def apply_workspace_interaction_plan(self, plan: WorkspaceInteractionPlan) -> None:
        self._orchestrator_required().apply(plan)

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

    def refresh_review_jump_to_page_index(
        self,
        page_index: int,
        *,
        preserve_link_history: bool = False,
    ) -> None:
        if self._viewer_workflow_required().session.current_page != page_index:
            self.clear_selected_document_text()
            self.clear_document_review_highlight()
        self.apply_workspace_interaction_plan(
            self._workspace_interaction_session_required().refresh_navigation_to_page_index(
                page_index
            ),
        )
        if not preserve_link_history:
            self._link_history.reset(page_index)
        self._refresh_page_navigation_state_required()()

    def _emit_link_status(self, status: str) -> None:
        if self._on_status_change is not None:
            self._on_status_change(status)

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

    def _viewer_interaction_session_required(self) -> ViewerInteractionSession:
        if self._viewer_interaction_session is None:
            raise RuntimeError(
                "SigningWorkspaceRuntime is not bound to a viewer interaction session."
            )
        return self._viewer_interaction_session

    def _viewer_workflow_required(self) -> ViewerWorkflow:
        if self._viewer_workflow is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a viewer workflow.")
        return self._viewer_workflow

    def _document_review_workspace_required(self) -> DocumentReviewWorkspaceSession:
        if self._document_review_workspace is None:
            raise RuntimeError(
                "SigningWorkspaceRuntime is not bound to a document review workspace."
            )
        return self._document_review_workspace

    def _review_bridge_required(self) -> SigningWorkspaceReviewBridge:
        if self._review_bridge is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a review bridge.")
        return self._review_bridge

    def _orchestrator_required(self) -> SigningWorkspaceOrchestrator:
        if self._orchestrator is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to an orchestrator.")
        return self._orchestrator

    def _viewer_widget_required(self) -> Any:
        if self._viewer_widget is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a viewer widget.")
        return self._viewer_widget

    def _properties_panel_required(self) -> SignaturePropertiesPanel:
        if self._properties_panel is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a properties panel.")
        return self._properties_panel

    def _sign_button_required(self) -> Any:
        if self._sign_button is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a sign button.")
        return self._sign_button

    def _refresh_sign_button_state_required(self) -> Callable[[], None]:
        if self._refresh_sign_button_state is None:
            raise RuntimeError(
                "SigningWorkspaceRuntime is not bound to a sign-button refresh callback."
            )
        return self._refresh_sign_button_state

    def _result_label_required(self) -> Any:
        if self._result_label is None:
            raise RuntimeError("SigningWorkspaceRuntime is not bound to a result label.")
        return self._result_label

    def _refresh_page_navigation_state_required(self) -> Callable[[], None]:
        if self._refresh_page_navigation_state is None:
            raise RuntimeError(
                "SigningWorkspaceRuntime is not bound to a page-navigation refresh callback."
            )
        return self._refresh_page_navigation_state
