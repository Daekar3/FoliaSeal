from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_link_activation import (
    DocumentLinkActivationService,
    ViewerLinkHistory,
)
from foliaseal.application.document_links import DocumentLink
from foliaseal.application.document_safety import (
    LinkDecisionKind,
    LinkInteractionMode,
)


def _service() -> DocumentLinkActivationService:
    return DocumentLinkActivationService()


def _link(
    *,
    rectangle: PdfRect,
    raw_destination: str | None = None,
    internal_page_index: int | None = None,
    page_index: int = 0,
) -> DocumentLink:
    return DocumentLink(
        page_index=page_index,
        rectangles=(rectangle,),
        raw_destination=raw_destination,
        internal_page_index=internal_page_index,
    )


def test_activation_resolves_internal_link_on_rectangle_boundary() -> None:
    result = _service().resolve(
        page_index=0,
        pdf_x=100,
        pdf_y=50,
        links=(_link(rectangle=PdfRect(0, 0, 100, 50), internal_page_index=2),),
        interaction_mode=LinkInteractionMode.PAN,
    )

    assert result.is_hit
    assert result.decision is not None
    assert result.decision.kind is LinkDecisionKind.ALLOW_INTERNAL
    assert result.decision.page_index == 2


def test_activation_supports_multiple_rectangles_and_ignores_other_pages() -> None:
    link = DocumentLink(
        page_index=0,
        rectangles=(PdfRect(0, 0, 10, 10), PdfRect(20, 20, 30, 30)),
        raw_destination="https://example.test",
    )

    result = _service().resolve(
        page_index=0,
        pdf_x=25,
        pdf_y=25,
        links=(link,),
        interaction_mode=LinkInteractionMode.PAN,
    )
    other_page = _service().resolve(
        page_index=1,
        pdf_x=25,
        pdf_y=25,
        links=(link,),
        interaction_mode=LinkInteractionMode.PAN,
    )

    assert result.decision is not None
    assert result.decision.kind is LinkDecisionKind.CONFIRM_EXTERNAL
    assert result.rectangle == PdfRect(20, 20, 30, 30)
    assert not other_page.is_hit


def test_activation_projects_blocked_and_non_pan_policy_results() -> None:
    blocked = _service().resolve(
        page_index=0,
        pdf_x=5,
        pdf_y=5,
        links=(_link(rectangle=PdfRect(0, 0, 10, 10), raw_destination="file:///tmp/a.pdf"),),
        interaction_mode=LinkInteractionMode.PAN,
    )
    text_mode = _service().resolve(
        page_index=0,
        pdf_x=5,
        pdf_y=5,
        links=(_link(rectangle=PdfRect(0, 0, 10, 10), internal_page_index=1),),
        interaction_mode=LinkInteractionMode.SELECT_TEXT,
    )

    assert blocked.decision is not None
    assert blocked.decision.kind is LinkDecisionKind.BLOCK
    assert text_mode.decision is not None
    assert text_mode.decision.kind is LinkDecisionKind.BLOCK


def test_activation_returns_no_hit_outside_all_rectangles() -> None:
    result = _service().resolve(
        page_index=0,
        pdf_x=11,
        pdf_y=11,
        links=(_link(rectangle=PdfRect(0, 0, 10, 10), internal_page_index=1),),
        interaction_mode=LinkInteractionMode.PAN,
    )

    assert not result.is_hit
    assert result.decision is None


def test_viewer_link_history_supports_back_forward_and_branch_reset() -> None:
    history = ViewerLinkHistory(current_page_index=0)
    history.record_internal_navigation(from_page_index=0, to_page_index=2)
    history.record_internal_navigation(from_page_index=2, to_page_index=4)

    assert history.current_page_index == 4
    assert history.back() == 2
    assert history.back() == 0
    assert history.forward() == 2
    history.record_internal_navigation(from_page_index=2, to_page_index=7)
    assert history.forward() is None
    assert history.back() == 2
