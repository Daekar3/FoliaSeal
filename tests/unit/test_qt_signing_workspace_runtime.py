from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.document_links import DocumentLink
from foliaseal.application.signing_draft_contracts import SignaturePlacementContext
from foliaseal.domain.models import SignatureRect, SigningResult
from foliaseal.presentation.qt.signing_workspace_diagnostics import (
    SigningWorkspaceSnapshot,
)
from foliaseal.presentation.qt.signing_workspace_runtime import (
    SigningWorkspaceRuntime,
)
from tests.support.signing_builders import build_signature_appearance


class _FakeWorkspaceInteractionSession:
    def __init__(self) -> None:
        self.selection_rects = []
        self.page_changes = []
        self.select_plan = object()
        self.panel_plan = object()
        self.page_plan = object()
        self.refresh_plan = object()

    def select_in_viewer(self, pdf_rect):
        self.selection_rects.append(pdf_rect)
        return self.select_plan

    def refresh_after_panel_change(self):
        return self.panel_plan

    def change_page(self, page_number: int):
        self.page_changes.append(page_number)
        return self.page_plan

    def refresh_navigation_to_page_index(self, page_index: int):
        return ("jump", page_index)

    def refresh_after_viewer_refresh(self):
        return self.refresh_plan


class _FakeOrchestrator:
    def __init__(self, order=None) -> None:
        self.plans = []
        self._order = order

    def apply(self, plan) -> None:
        if self._order is not None:
            self._order.append(("apply_plan", plan))
        self.plans.append(plan)


class _FakeReviewBridge:
    def __init__(self) -> None:
        self.selected_indices = []
        self.states = []
        self.transitions = []

    def select_review_signature(self, index: int) -> None:
        self.selected_indices.append(index)

    def clear_review_highlight(self) -> None:
        return None

    def apply_state(self, state) -> None:
        self.states.append(state)

    def apply_transition(self, transition) -> None:
        self.transitions.append(transition)


class _FakeViewerWidget:
    def __init__(self, order=None) -> None:
        self.overlays = []
        self.refresh_calls = []
        self._order = order

    def set_signature_overlay(self, signature_rect) -> None:
        if self._order is not None:
            self._order.append(("overlay", signature_rect))
        self.overlays.append(signature_rect)

    def refresh(self, *, navigation: bool = False) -> None:
        if self._order is not None:
            self._order.append(("refresh", navigation))
        self.refresh_calls.append(navigation)


class _FakeResultLabel:
    def __init__(self) -> None:
        self.text = ""
        self.style = None

    def setText(self, value):  # noqa: N802
        self.text = value

    def setStyleSheet(self, value):  # noqa: N802
        self.style = value


class _FakePropertiesPanel:
    def __init__(self, order=None) -> None:
        self.set_signature_rect_calls = []
        self.load_from_workflow_calls = 0
        self._order = order

    def set_signature_rect(self, signature_rect, notify=True) -> None:
        if self._order is not None:
            self._order.append(("set_signature_rect", notify))
        self.set_signature_rect_calls.append((signature_rect, notify))

    def load_from_workflow(self) -> None:
        self.load_from_workflow_calls += 1


class _FakeLineEdit:
    def __init__(self, value: str = "") -> None:
        self._value = value

    def text(self) -> str:
        return self._value


class _FakeSignButton:
    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    def isEnabled(self) -> bool:  # noqa: N802
        return self._enabled


class _FakeDraftWorkflow:
    def __init__(self, order=None) -> None:
        self.signature_rect = object()
        self.current_signature_rect = None
        self.signature_appearance = None
        self.current_signature_appearance = None
        self.placement_context = None
        self.selected_certificate_configuration_id = None
        self.timestamp_required = False
        self.input_pdf_path = "/tmp/input.pdf"
        self.output_pdf_path = "/tmp/output.pdf"
        self.certificate_path = "/tmp/cert.p12"
        self.passphrase = "secret"
        self.tsa_url = "https://tsa.example"
        self.trust_policy = None
        self.certificate_alias = "alias"
        self._order = order

    def set_placement_context(self, placement_context) -> None:
        if self._order is not None:
            self._order.append(("placement_context", placement_context))
        self.placement_context = placement_context


class _FakeViewerInteractionSession:
    def __init__(self, order=None) -> None:
        self.logical_page_indexes = []
        self.current_placement = SignaturePlacementContext(
            page_index=0,
            page_box=PageBox(left=0.0, bottom=0.0, right=200.0, top=80.0),
        )
        self._order = order

    def set_logical_page_index(self, page_index: int) -> None:
        self.logical_page_indexes.append(page_index)

    def current_placement_context(self):
        if self._order is not None:
            self._order.append(("current_placement_context", None))
        return SimpleNamespace(placement_context=self.current_placement)


class _FakeViewerWorkflow:
    def __init__(self, order=None) -> None:
        self.session = SimpleNamespace(current_page=1)
        self.document_path = "/tmp/sample.pdf"
        self.render_backend = SimpleNamespace()
        self.snapshot = SimpleNamespace(page_index=1)
        self.jump_calls = []
        self._order = order

    def jump_to_page(self, page_index: int) -> None:
        if self._order is not None:
            self._order.append(("jump_to_page", page_index))
        self.jump_calls.append(page_index)


class _FakeDocumentReviewWorkspace:
    def __init__(self) -> None:
        self.search_queries = []
        self.selection_mode_calls = []
        self.review_state = SimpleNamespace(review=SimpleNamespace(review_summary="summary"))
        self.search_state = SimpleNamespace(document_text=SimpleNamespace(search_state="search"))
        self.selection_state = SimpleNamespace(
            document_text=SimpleNamespace(
                selection_mode_enabled=True,
                selection_state="selection-state",
            )
        )

    def refresh_review(self):
        return self.review_state

    def search_text(self, query: str):
        self.search_queries.append(query)
        return SimpleNamespace(state=self.search_state)

    def next_text_match(self):
        return SimpleNamespace(state=self.search_state)

    def previous_text_match(self):
        return SimpleNamespace(state=self.search_state)

    def copy_current_text_match(self):
        return "match"

    def set_text_selection_mode(self, enabled: bool):
        self.selection_mode_calls.append(enabled)
        return SimpleNamespace(state=self.selection_state)

    def copy_selected_text(self):
        return "selected"

    def clear_selected_text(self):
        return SimpleNamespace(state=self.selection_state)


def _bind_runtime(
    *,
    on_copy_text=None,
    on_error=None,
    on_status_change=None,
    document_link_inspector=None,
    on_external_link_confirmation=None,
):
    order = []
    runtime = SigningWorkspaceRuntime(
        draft_workflow=_FakeDraftWorkflow(order),
        on_copy_text=on_copy_text,
        on_error=on_error,
        on_status_change=on_status_change,
        document_link_inspector=document_link_inspector,
        on_external_link_confirmation=on_external_link_confirmation,
    )
    viewer_interaction_session = _FakeViewerInteractionSession(order)
    viewer_workflow = _FakeViewerWorkflow(order)
    document_review_workspace = _FakeDocumentReviewWorkspace()
    interaction_session = _FakeWorkspaceInteractionSession()
    orchestrator = _FakeOrchestrator(order)
    review_bridge = _FakeReviewBridge()
    properties_panel = _FakePropertiesPanel(order)
    viewer_widget = _FakeViewerWidget(order)
    sign_button = _FakeSignButton()
    result_label = _FakeResultLabel()
    refresh_sign_button_state_calls = []
    refresh_page_navigation_state_calls = []
    runtime.bind(
        viewer_interaction_session=viewer_interaction_session,
        viewer_workflow=viewer_workflow,
        document_review_workspace=document_review_workspace,
        workspace_interaction_session=interaction_session,
        review_bridge=review_bridge,
        orchestrator=orchestrator,
        properties_panel=properties_panel,
        viewer_widget=viewer_widget,
        document_text_query_input=_FakeLineEdit("Alice"),
        sign_button=sign_button,
        refresh_sign_button_state=lambda: (
            order.append(("refresh_sign_button_state", None)),
            refresh_sign_button_state_calls.append("refresh"),
        )[-1],
        refresh_page_navigation_state=lambda: (
            order.append(("refresh_page_navigation_state", None)),
            refresh_page_navigation_state_calls.append("refresh"),
        )[-1],
        result_label=result_label,
    )
    return SimpleNamespace(
        runtime=runtime,
        draft_workflow=runtime._draft_workflow,
        viewer_interaction_session=viewer_interaction_session,
        viewer_workflow=viewer_workflow,
        document_review_workspace=document_review_workspace,
        interaction_session=interaction_session,
        orchestrator=orchestrator,
        review_bridge=review_bridge,
        properties_panel=properties_panel,
        viewer_widget=viewer_widget,
        sign_button=sign_button,
        result_label=result_label,
        refresh_sign_button_state_calls=refresh_sign_button_state_calls,
        refresh_page_navigation_state_calls=refresh_page_navigation_state_calls,
        order=order,
    )


def test_signing_workspace_runtime_routes_viewer_selection_through_workspace_session() -> None:
    bound = _bind_runtime()
    pdf_rect = PdfRect(x1=1.0, y1=2.0, x2=3.0, y2=4.0)

    bound.runtime.on_viewer_selection(pdf_rect)

    assert bound.interaction_session.selection_rects == [pdf_rect]
    assert bound.orchestrator.plans == [bound.interaction_session.select_plan]


def test_signing_workspace_runtime_routes_internal_link_and_history() -> None:
    class _Inspector:
        def inspect_links(self, document_path, page_index):
            assert document_path == "/tmp/sample.pdf"
            assert page_index == 1
            return (
                DocumentLink(
                    page_index=1,
                    rectangles=(PdfRect(0, 0, 10, 10),),
                    internal_page_index=3,
                ),
            )

    statuses = []
    bound = _bind_runtime(
        on_status_change=statuses.append,
        document_link_inspector=_Inspector(),
    )

    bound.runtime.on_viewer_link_click(5, 5)
    bound.runtime.go_back_link()
    bound.runtime.go_forward_link()

    assert "link_internal_navigation" in statuses
    assert "link_history_back" in statuses
    assert "link_history_forward" in statuses
    assert ("jump", 3) in bound.orchestrator.plans
    assert ("jump", 1) in bound.orchestrator.plans


def test_signing_workspace_runtime_emits_external_confirmation_without_launching() -> None:
    class _Inspector:
        def inspect_links(self, document_path, page_index):
            return (
                DocumentLink(
                    page_index=page_index,
                    rectangles=(PdfRect(0, 0, 10, 10),),
                    raw_destination="https://example.test/review",
                ),
            )

    confirmations = []
    bound = _bind_runtime(
        document_link_inspector=_Inspector(),
        on_external_link_confirmation=confirmations.append,
    )

    bound.runtime.on_viewer_link_click(5, 5)

    assert len(confirmations) == 1
    assert confirmations[0].destination == "https://example.test/review"
    assert bound.viewer_workflow.jump_calls == []


def test_signing_workspace_runtime_blocks_unsafe_link_with_status() -> None:
    class _Inspector:
        def inspect_links(self, document_path, page_index):
            return (
                DocumentLink(
                    page_index=page_index,
                    rectangles=(PdfRect(0, 0, 10, 10),),
                    raw_destination="file:///tmp/private.pdf",
                ),
            )

    statuses = []
    bound = _bind_runtime(
        on_status_change=statuses.append,
        document_link_inspector=_Inspector(),
    )

    bound.runtime.on_viewer_link_click(5, 5)

    assert statuses == ["link_blocked"]
    assert bound.viewer_workflow.jump_calls == []


def test_signing_workspace_runtime_routes_panel_page_and_refresh_changes() -> None:
    bound = _bind_runtime()

    bound.runtime.on_panel_change()
    bound.runtime.on_page_change(3)
    bound.runtime.refresh_viewer()

    assert bound.orchestrator.plans == [
        bound.interaction_session.panel_plan,
        bound.interaction_session.page_plan,
        bound.interaction_session.refresh_plan,
    ]
    assert bound.interaction_session.page_changes == [3]


def test_signing_workspace_runtime_emits_shell_error_and_updates_result_label() -> None:
    errors = []
    bound = _bind_runtime(on_error=errors.append)

    bound.runtime.on_viewer_error("boom")

    assert errors == ["boom"]
    assert bound.result_label.text == "boom"
    assert bound.result_label.style == "color: #9f1d1d; font-weight: 600;"


def test_signing_workspace_runtime_forwards_status_and_review_selection() -> None:
    statuses = []
    bound = _bind_runtime(on_status_change=statuses.append)

    bound.runtime.on_viewer_interaction("selection_success")
    bound.runtime.on_document_review_signature_selected(2)

    assert statuses == ["selection_success"]
    assert bound.review_bridge.selected_indices == [2]


def test_signing_workspace_runtime_applies_review_and_document_text_verbs() -> None:
    copied = []
    bound = _bind_runtime(on_copy_text=copied.append)

    summary = bound.runtime.refresh_document_review()
    search_state = bound.runtime.search_document_text()
    next_state = bound.runtime.next_document_text_match()
    previous_state = bound.runtime.previous_document_text_match()
    selection_mode = bound.runtime.set_document_text_selection_mode(True)
    selected_text = bound.runtime.copy_selected_document_text()
    current_text = bound.runtime.copy_current_document_text_match()
    cleared = bound.runtime.clear_selected_document_text()

    assert summary == "summary"
    assert search_state == "search"
    assert next_state == "search"
    assert previous_state == "search"
    assert selection_mode is True
    assert selected_text == "selected"
    assert current_text == "match"
    assert cleared == "selection-state"
    assert bound.document_review_workspace.search_queries == ["Alice"]
    assert bound.document_review_workspace.selection_mode_calls == [True]
    assert copied == ["selected", "match"]
    assert len(bound.review_bridge.states) == 1
    assert len(bound.review_bridge.transitions) == 5


def test_signing_workspace_runtime_applies_placement_context_and_overlay() -> None:
    bound = _bind_runtime()
    placement_context = SignaturePlacementContext(
        page_index=0,
        page_box=PageBox(left=0.0, bottom=0.0, right=200.0, top=80.0),
    )

    bound.runtime.apply_placement_context(placement_context)
    bound.runtime.sync_signature_overlay()

    assert bound.draft_workflow.placement_context == placement_context
    assert bound.viewer_widget.overlays == [bound.draft_workflow.signature_rect]


def test_signing_workspace_runtime_owns_page_rect_and_current_request_helpers() -> None:
    bound = _bind_runtime()
    appearance = build_signature_appearance()
    rect = bound.runtime.set_signature_rect(
        page_index=2,
        left_pt=10.0,
        bottom_pt=12.0,
        width_pt=30.0,
        height_pt=18.0,
    )
    bound.draft_workflow.current_signature_rect = rect
    bound.draft_workflow.signature_rect = rect
    bound.draft_workflow.current_signature_appearance = appearance
    bound.draft_workflow.signature_appearance = appearance
    bound.runtime.set_logical_page_index(4)

    assert isinstance(rect, SignatureRect)
    assert bound.properties_panel.set_signature_rect_calls == [(rect, False)]
    assert bound.orchestrator.plans == [bound.interaction_session.panel_plan]
    assert bound.viewer_interaction_session.logical_page_indexes == [4]
    assert bound.runtime.logical_page_index() == 1
    assert bound.runtime.signature_rect() == rect
    assert bound.runtime.signature_appearance() is appearance
    assert bound.runtime.current_request() is not None
    assert bound.order[:2] == [
        ("set_signature_rect", False),
        ("apply_plan", bound.interaction_session.panel_plan),
    ]


def test_signing_workspace_runtime_snapshot_is_complete_and_immutable() -> None:
    bound = _bind_runtime()
    appearance = build_signature_appearance()
    rect = SignatureRect(
        page_index=2,
        left_pt=10.0,
        bottom_pt=12.0,
        width_pt=30.0,
        height_pt=18.0,
    )
    bound.viewer_workflow.session.current_page = 4
    bound.draft_workflow.current_signature_rect = rect
    bound.draft_workflow.signature_rect = rect
    bound.draft_workflow.current_signature_appearance = appearance
    bound.draft_workflow.signature_appearance = appearance
    bound.draft_workflow.selected_certificate_configuration_id = "cert-1"
    bound.draft_workflow.timestamp_required = True
    result = SigningResult(success=True, failure_code=None, message="ok")

    snapshot = bound.runtime.snapshot(last_signing_result=result)

    assert isinstance(snapshot, SigningWorkspaceSnapshot)
    assert snapshot.logical_page_index == 4
    assert snapshot.signature_rect == rect
    assert snapshot.signature_appearance is appearance
    assert snapshot.selected_certificate_configuration_id == "cert-1"
    assert snapshot.timestamp_required is True
    assert snapshot.current_request is not None
    assert snapshot.sign_action_enabled is True
    assert snapshot.last_signing_result is result
    with pytest.raises(FrozenInstanceError):
        snapshot.logical_page_index = 99  # type: ignore[misc]


def test_signing_workspace_runtime_applies_signature_rect_placement_and_testing_state() -> None:
    bound = _bind_runtime()
    rect = SignatureRect(
        page_index=3,
        left_pt=24.0,
        bottom_pt=18.0,
        width_pt=40.0,
        height_pt=20.0,
    )

    bound.runtime.apply_signature_rect_placement(rect)
    bound.runtime.set_selected_certificate_configuration_id("cert-1")
    bound.runtime.set_timestamp_required(True)

    assert bound.properties_panel.set_signature_rect_calls == [(rect, True)]
    assert bound.viewer_workflow.jump_calls == [3]
    assert bound.viewer_widget.refresh_calls == [True]
    assert (
        bound.draft_workflow.placement_context
        == bound.viewer_interaction_session.current_placement
    )
    assert bound.viewer_widget.overlays == [bound.draft_workflow.signature_rect]
    assert bound.refresh_sign_button_state_calls == ["refresh"]
    assert bound.draft_workflow.selected_certificate_configuration_id == "cert-1"
    assert bound.draft_workflow.timestamp_required is True
    assert bound.properties_panel.load_from_workflow_calls == 2
    assert bound.runtime.selected_certificate_configuration_id() == "cert-1"
    assert bound.runtime.is_sign_action_enabled() is True
    assert bound.order[:5] == [
        ("set_signature_rect", True),
        ("jump_to_page", 3),
        ("refresh", True),
        ("current_placement_context", None),
        ("placement_context", bound.viewer_interaction_session.current_placement),
    ]
    assert bound.order[5:7] == [
        ("overlay", bound.draft_workflow.signature_rect),
        ("refresh_sign_button_state", None),
    ]
