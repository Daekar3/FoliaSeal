from dataclasses import dataclass

from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.document_review_workspace import (
    DocumentReviewWorkspaceState,
    DocumentReviewWorkspaceTransition,
)
from foliaseal.application.document_text_search import DocumentTextSearchState
from foliaseal.application.document_text_selection import DocumentTextSelectionState
from foliaseal.application.signing_draft_workflow import SignaturePlacementContext
from foliaseal.application.workspace_interaction_session import (
    WorkspaceInteractionSession,
)
from foliaseal.domain.models import SignatureRect


@dataclass
class _FakeViewerSession:
    current_page: int = 0


@dataclass
class _FakeSnapshot:
    page_index: int


@dataclass
class _FakeViewerWorkflow:
    session: _FakeViewerSession
    snapshot: _FakeSnapshot | None = None


@dataclass
class _FakeSelectionResult:
    signature_rect: SignatureRect | None
    placement_context: SignaturePlacementContext | None
    error_message: str | None = None


class _FakeViewerInteractionSession:
    def __init__(self) -> None:
        self.selection_rects: list[PdfRect] = []
        self.page_numbers: list[int] = []
        self.page_indexes: list[int] = []
        self.selection_result = _FakeSelectionResult(
            signature_rect=None,
            placement_context=None,
        )
        self.page_error: Exception | None = None
        self.page_index_error: Exception | None = None

    def select_signature_rect(self, pdf_rect: PdfRect) -> _FakeSelectionResult:
        self.selection_rects.append(pdf_rect)
        return self.selection_result

    def set_page_number(self, page_number: int) -> int:
        self.page_numbers.append(page_number)
        if self.page_error is not None:
            raise self.page_error
        return max(page_number - 1, 0)

    def set_logical_page_index(self, page_index: int) -> int:
        self.page_indexes.append(page_index)
        if self.page_index_error is not None:
            raise self.page_index_error
        return page_index


class _FakeDocumentReviewWorkspace:
    def __init__(self) -> None:
        self.calls: list[tuple[int, PdfRect]] = []
        self.transition = DocumentReviewWorkspaceTransition(
            state=_workspace_state(),
            viewer_selection_consumed=False,
        )

    def handle_viewer_selection(
        self,
        *,
        page_index: int,
        selection_rect: PdfRect,
    ) -> DocumentReviewWorkspaceTransition:
        self.calls.append((page_index, selection_rect))
        return self.transition


def _workspace_state() -> DocumentReviewWorkspaceState:
    return DocumentReviewWorkspaceState(
        review_summary=DocumentReviewSummary(
            headline="No signatures found",
            detail="You can place and sign a new visible approval signature.",
            signature_count=0,
        ),
        review_signature_labels=(),
        selected_review_signature_index=None,
        selected_review_signature_label=None,
        selected_review_signature_detail="",
        review_selector_enabled=False,
        text_search_state=DocumentTextSearchState(
            query="",
            match_count=0,
            current_index=None,
            status_text="Enter text to search this PDF.",
            detail_text="",
            current_match=None,
            can_go_previous=False,
            can_go_next=False,
            can_copy=False,
        ),
        text_selection_state=DocumentTextSelectionState(
            status_text="No document text selected.",
            detail_text="Enable Select text, then drag across visible PDF text.",
            selection=None,
            can_copy=False,
            can_clear=False,
        ),
        text_selection_mode_enabled=False,
        document_text_display_source="search",
        document_text_status_text="Enter text to search this PDF.",
        document_text_detail_text="",
    )


def test_workspace_interaction_session_returns_review_transition_when_consumed() -> None:
    viewer_interaction = _FakeViewerInteractionSession()
    review_workspace = _FakeDocumentReviewWorkspace()
    consumed_transition = DocumentReviewWorkspaceTransition(
        state=_workspace_state(),
        viewer_selection_consumed=True,
    )
    review_workspace.transition = consumed_transition
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=3)),
        viewer_interaction_session=viewer_interaction,
        document_review_workspace=review_workspace,
    )

    transition = session.select_in_viewer(PdfRect(x1=30.0, y1=20.0, x2=10.0, y2=12.0))

    assert transition.review_transition is consumed_transition
    assert review_workspace.calls == [(3, PdfRect(x1=10.0, y1=12.0, x2=30.0, y2=20.0))]
    assert viewer_interaction.selection_rects == []


def test_workspace_interaction_session_returns_signature_rect_transition() -> None:
    placement_context = SignaturePlacementContext(
        page_index=2,
        page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
        rotation=0,
    )
    viewer_interaction = _FakeViewerInteractionSession()
    viewer_interaction.selection_result = _FakeSelectionResult(
        signature_rect=SignatureRect(
            page_index=2,
            left_pt=10.0,
            bottom_pt=12.0,
            width_pt=20.0,
            height_pt=8.0,
        ),
        placement_context=placement_context,
    )
    review_workspace = _FakeDocumentReviewWorkspace()
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(
            session=_FakeViewerSession(current_page=0),
            snapshot=_FakeSnapshot(page_index=2),
        ),
        viewer_interaction_session=viewer_interaction,
        document_review_workspace=review_workspace,
    )

    transition = session.select_in_viewer(PdfRect(x1=30.0, y1=20.0, x2=10.0, y2=12.0))

    assert transition.signature_rect is not None
    assert transition.signature_rect.page_index == 2
    assert transition.placement_context == placement_context
    assert transition.sync_signature_overlay is True
    assert transition.signing_action_invalidation_reason == "selection"
    assert viewer_interaction.selection_rects == [PdfRect(x1=10.0, y1=12.0, x2=30.0, y2=20.0)]


def test_workspace_interaction_session_change_page_returns_navigation_refresh() -> None:
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=_FakeViewerInteractionSession(),
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    transition = session.change_page(2)

    assert transition.refresh_viewer is True
    assert transition.navigation_refresh is True
    assert transition.refresh_current_placement_context is True
    assert transition.sync_signature_overlay is True
    assert transition.signing_action_invalidation_reason == "page"


def test_workspace_interaction_session_navigation_error_is_mapped() -> None:
    viewer_interaction = _FakeViewerInteractionSession()
    viewer_interaction.page_index_error = RuntimeError("jump failed")
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=viewer_interaction,
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    transition = session.refresh_navigation_to_page_index(4)

    assert transition.error_message == "Unable to show document text match: jump failed"


def test_workspace_interaction_session_refresh_after_viewer_refresh_requests_follow_up() -> None:
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=_FakeViewerInteractionSession(),
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    transition = session.refresh_after_viewer_refresh()

    assert transition.refresh_viewer is True
    assert transition.refresh_preview is True
    assert transition.reload_signing_action_state is True
    assert transition.sync_signature_overlay is True
    assert transition.refresh_current_placement_context is True
