from dataclasses import dataclass

from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.document_review import DocumentReviewSummary
from foliaseal.application.document_review_workspace import (
    DocumentReviewCardState,
    DocumentReviewWorkspaceState,
    DocumentReviewWorkspaceTransition,
    DocumentTextWorkspaceState,
)
from foliaseal.application.document_text_search import DocumentTextSearchState
from foliaseal.application.document_text_selection import DocumentTextSelectionState
from foliaseal.application.signing_draft_contracts import SignaturePlacementContext
from foliaseal.application.workspace_interaction_session import (
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
    WorkspaceInteractionPlan,
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
        review=DocumentReviewCardState(
            review_summary=DocumentReviewSummary(
                headline="No signatures found",
                detail="You can place and sign a new visible approval signature.",
                signature_count=0,
            ),
            signature_labels=(),
            selected_signature_index=None,
            selected_signature_label=None,
            selected_signature_detail="",
            selector_enabled=False,
        ),
        document_text=DocumentTextWorkspaceState(
            search_state=DocumentTextSearchState(
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
            selection_state=DocumentTextSelectionState(
                status_text="No document text selected.",
                detail_text="Enable Select text, then drag across visible PDF text.",
                selection=None,
                can_copy=False,
                can_clear=False,
            ),
            selection_mode_enabled=False,
            display_source="search",
            status_text="Enter text to search this PDF.",
            detail_text="",
        ),
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

    plan = session.select_in_viewer(PdfRect(x1=30.0, y1=20.0, x2=10.0, y2=12.0))

    assert plan == WorkspaceInteractionPlan(
        effects=(ApplyReviewTransition(consumed_transition),)
    )
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

    plan = session.select_in_viewer(PdfRect(x1=30.0, y1=20.0, x2=10.0, y2=12.0))

    assert plan == WorkspaceInteractionPlan(
        effects=(
            ApplyPlacementContext(placement_context),
            ApplySignatureRect(
                SignatureRect(
                    page_index=2,
                    left_pt=10.0,
                    bottom_pt=12.0,
                    width_pt=20.0,
                    height_pt=8.0,
                )
            ),
            SyncSignatureOverlay(),
            InvalidateSigningAction("selection"),
        )
    )
    assert viewer_interaction.selection_rects == [PdfRect(x1=10.0, y1=12.0, x2=30.0, y2=20.0)]


def test_workspace_interaction_session_change_page_returns_ordered_effects() -> None:
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=_FakeViewerInteractionSession(),
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    plan = session.change_page(2)

    assert plan == WorkspaceInteractionPlan(
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


def test_workspace_interaction_session_change_page_error_is_mapped() -> None:
    viewer_interaction = _FakeViewerInteractionSession()
    viewer_interaction.page_error = RuntimeError("page failed")
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=viewer_interaction,
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    plan = session.change_page(4)

    assert plan == WorkspaceInteractionPlan(
        effects=(EmitInteractionError("Unable to change PDF page: page failed"),)
    )


def test_workspace_interaction_session_navigation_error_is_mapped() -> None:
    viewer_interaction = _FakeViewerInteractionSession()
    viewer_interaction.page_index_error = RuntimeError("jump failed")
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=viewer_interaction,
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    plan = session.refresh_navigation_to_page_index(4)

    assert plan == WorkspaceInteractionPlan(
        effects=(EmitInteractionError("Unable to show document text match: jump failed"),)
    )


def test_workspace_interaction_session_navigation_success_returns_ordered_effects() -> None:
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=_FakeViewerInteractionSession(),
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    plan = session.refresh_navigation_to_page_index(4)

    assert plan == WorkspaceInteractionPlan(
        effects=(
            RefreshViewer(
                navigation=True,
                error_summary="Unable to show document text match",
            ),
            RefreshCurrentPlacementContext(),
            SyncSignatureOverlay(),
        )
    )


def test_workspace_interaction_session_refresh_after_panel_change_returns_ordered_effects() -> None:
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=_FakeViewerInteractionSession(),
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    plan = session.refresh_after_panel_change()

    assert plan == WorkspaceInteractionPlan(
        effects=(
            RefreshCurrentPlacementContext(),
            SyncSignatureOverlay(),
            InvalidateSigningAction("panel"),
        )
    )


def test_workspace_interaction_session_refresh_after_viewer_refresh_requests_follow_up() -> None:
    session = WorkspaceInteractionSession(
        viewer_workflow=_FakeViewerWorkflow(session=_FakeViewerSession(current_page=0)),
        viewer_interaction_session=_FakeViewerInteractionSession(),
        document_review_workspace=_FakeDocumentReviewWorkspace(),
    )

    plan = session.refresh_after_viewer_refresh()

    assert plan == WorkspaceInteractionPlan(
        effects=(
            RefreshViewer(),
            RefreshCurrentPlacementContext(),
            SyncSignatureOverlay(),
            RefreshPreview(),
            ReloadSigningActionState(),
        )
    )
