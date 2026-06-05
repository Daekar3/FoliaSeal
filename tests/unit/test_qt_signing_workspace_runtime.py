from types import SimpleNamespace

from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.signing_draft_workflow import SignaturePlacementContext
from foliaseal.presentation.qt.signing_workspace_runtime import (
    SigningWorkspaceRuntime,
)


class _FakeWorkspaceInteractionSession:
    def __init__(self) -> None:
        self.selection_rects = []
        self.page_changes = []
        self.select_plan = object()
        self.panel_plan = object()
        self.page_plan = object()

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


class _FakeInteractionBridge:
    def __init__(self) -> None:
        self.plans = []

    def apply_plan(self, plan) -> None:
        self.plans.append(plan)


class _FakeReviewBridge:
    def __init__(self) -> None:
        self.selected_indices = []

    def select_review_signature(self, index: int) -> None:
        self.selected_indices.append(index)


class _FakeViewerWidget:
    def __init__(self) -> None:
        self.overlays = []

    def set_signature_overlay(self, signature_rect) -> None:
        self.overlays.append(signature_rect)


class _FakeResultLabel:
    def __init__(self) -> None:
        self.text = ""
        self.style = None

    def setText(self, value):  # noqa: N802
        self.text = value

    def setStyleSheet(self, value):  # noqa: N802
        self.style = value


class _FakeDraftWorkflow:
    def __init__(self) -> None:
        self.signature_rect = object()
        self.placement_context = None

    def set_placement_context(self, placement_context) -> None:
        self.placement_context = placement_context


def _bind_runtime(
    *,
    on_error=None,
    on_status_change=None,
):
    runtime = SigningWorkspaceRuntime(
        draft_workflow=_FakeDraftWorkflow(),
        on_error=on_error,
        on_status_change=on_status_change,
    )
    interaction_session = _FakeWorkspaceInteractionSession()
    interaction_bridge = _FakeInteractionBridge()
    review_bridge = _FakeReviewBridge()
    viewer_widget = _FakeViewerWidget()
    result_label = _FakeResultLabel()
    runtime.bind(
        viewer_interaction_session=SimpleNamespace(),
        document_review_workspace=SimpleNamespace(),
        workspace_interaction_session=interaction_session,
        review_bridge=review_bridge,
        interaction_bridge=interaction_bridge,
        viewer_widget=viewer_widget,
        result_label=result_label,
    )
    return (
        runtime,
        interaction_session,
        interaction_bridge,
        review_bridge,
        viewer_widget,
        result_label,
    )


def test_signing_workspace_runtime_routes_viewer_selection_through_workspace_session() -> None:
    runtime, interaction_session, interaction_bridge, *_rest = _bind_runtime()
    pdf_rect = PdfRect(x1=1.0, y1=2.0, x2=3.0, y2=4.0)

    runtime.on_viewer_selection(pdf_rect)

    assert interaction_session.selection_rects == [pdf_rect]
    assert interaction_bridge.plans == [interaction_session.select_plan]


def test_signing_workspace_runtime_routes_panel_and_page_changes() -> None:
    runtime, interaction_session, interaction_bridge, *_rest = _bind_runtime()

    runtime.on_panel_change()
    runtime.on_page_change(3)

    assert interaction_bridge.plans == [
        interaction_session.panel_plan,
        interaction_session.page_plan,
    ]
    assert interaction_session.page_changes == [3]


def test_signing_workspace_runtime_emits_shell_error_and_updates_result_label() -> None:
    errors = []
    (
        runtime,
        _interaction_session,
        _interaction_bridge,
        _review_bridge,
        _viewer_widget,
        result_label,
    ) = _bind_runtime(on_error=errors.append)

    runtime.on_viewer_error("boom")

    assert errors == ["boom"]
    assert result_label.text == "boom"
    assert result_label.style == "color: #9f1d1d; font-weight: 600;"


def test_signing_workspace_runtime_forwards_status_and_review_selection() -> None:
    statuses = []
    (
        runtime,
        _interaction_session,
        _interaction_bridge,
        review_bridge,
        _viewer_widget,
        _result_label,
    ) = _bind_runtime(on_status_change=statuses.append)

    runtime.on_viewer_interaction("selection_success")
    runtime.on_document_review_signature_selected(2)

    assert statuses == ["selection_success"]
    assert review_bridge.selected_indices == [2]


def test_signing_workspace_runtime_applies_placement_context_and_overlay() -> None:
    (
        runtime,
        _interaction_session,
        _interaction_bridge,
        _review_bridge,
        viewer_widget,
        _result_label,
    ) = _bind_runtime()
    draft_workflow = runtime._draft_workflow
    placement_context = SignaturePlacementContext(
        page_index=0,
        page_box=PageBox(left=0.0, bottom=0.0, right=200.0, top=80.0),
    )

    runtime.apply_placement_context(placement_context)
    runtime.sync_signature_overlay()

    assert draft_workflow.placement_context == placement_context
    assert viewer_widget.overlays == [draft_workflow.signature_rect]
