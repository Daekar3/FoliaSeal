from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_links import DocumentLink, DocumentLinkInspector


def test_document_link_contract_is_neutral_and_typed() -> None:
    link = DocumentLink(
        page_index=2,
        rectangles=(PdfRect(x1=1, y1=2, x2=3, y2=4),),
        raw_destination="https://example.com",
    )
    assert link.page_index == 2
    assert isinstance(link, DocumentLink)
    assert DocumentLinkInspector is not None
