"""QtPdf link extraction proof for the safe-links prerequisite boundary."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.generic import ArrayObject, NameObject, NumberObject, TextStringObject
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.application.coordinate_transform import PdfRect
from foliaseal.application.document_link_activation import DocumentLinkActivationService
from foliaseal.application.document_links import DocumentLink
from foliaseal.application.document_safety import (
    LinkDecisionKind,
    LinkInteractionMode,
    classify_link_destination,
)
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend


def _write_link_fixture(path: Path) -> None:
    writer = PdfFileWriter()
    contents = writer.add_object(generic.StreamObject(stream_data=b""))
    first_page = writer.insert_page(PageObject(contents=contents, media_box=(0, 0, 612, 792)))
    second_page = writer.insert_page(PageObject(contents=contents, media_box=(0, 0, 612, 792)))
    annotations = []
    for index, destination in enumerate(
        ("https://example.com", "mailto:approvals@example.com", "file:///tmp/private.pdf")
    ):
        action = generic.DictionaryObject(
            {
                NameObject("/S"): NameObject("/URI"),
                NameObject("/URI"): TextStringObject(destination),
            }
        )
        annotation = generic.DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject(
                    [
                        NumberObject(index * 100),
                        NumberObject(0),
                        NumberObject((index + 1) * 100),
                        NumberObject(50),
                    ]
                ),
                NameObject("/A"): action,
            }
        )
        annotations.append(writer.add_object(annotation))
    internal_annotation = generic.DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(300), NumberObject(0), NumberObject(400), NumberObject(50)]
            ),
            NameObject("/Dest"): ArrayObject([second_page, NameObject("/Fit")]),
        }
    )
    annotations.append(writer.add_object(internal_annotation))
    first_page.get_object()[NameObject("/Annots")] = ArrayObject(annotations)
    with path.open("wb") as handle:
        writer.write(handle)


def _write_transformed_link_fixture(path: Path, *, rotation: int) -> None:
    writer = PdfFileWriter()
    contents = writer.add_object(generic.StreamObject(stream_data=b""))
    page = writer.insert_page(PageObject(contents=contents, media_box=(10, 20, 210, 320)))
    page_object = page.get_object()
    page_object[NameObject("/Rotate")] = NumberObject(rotation)
    page_object[NameObject("/CropBox")] = ArrayObject(
        [NumberObject(30), NumberObject(40), NumberObject(180), NumberObject(280)]
    )
    action = generic.DictionaryObject(
        {
            NameObject("/S"): NameObject("/URI"),
            NameObject("/URI"): TextStringObject("https://example.test/transformed"),
        }
    )
    annotation = generic.DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Link"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(50), NumberObject(60), NumberObject(100), NumberObject(90)]
            ),
            NameObject("/A"): action,
        }
    )
    page_object[NameObject("/Annots")] = ArrayObject([writer.add_object(annotation)])
    with path.open("wb") as handle:
        writer.write(handle)


def test_qtpdf_inspector_normalizes_internal_and_external_links(tmp_path: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    source = tmp_path / "links.pdf"
    _write_link_fixture(source)

    links = QtPdfRenderBackend().inspect_links(str(source), 0)

    assert len(links) == 4
    by_destination = {link.raw_destination: link for link in links}
    assert by_destination["https://example.com"].rectangles == (
        PdfRect(0.0, 0.0, 100.0, 50.0),
    )
    assert by_destination["mailto:approvals@example.com"].internal_page_index is None
    assert by_destination["file:///tmp/private.pdf"].raw_destination == "file:///tmp/private.pdf"
    internal = next(link for link in links if link.internal_page_index == 1)
    assert internal.raw_destination is None
    assert internal.rectangles[0] == PdfRect(300.0, 0.0, 400.0, 50.0)

    decisions = [
        classify_link_destination(
            link.raw_destination,
            internal_page_index=link.internal_page_index,
        )
        for link in links
    ]
    assert [decision.kind for decision in decisions] == [
        LinkDecisionKind.CONFIRM_EXTERNAL,
        LinkDecisionKind.CONFIRM_EXTERNAL,
        LinkDecisionKind.BLOCK,
        LinkDecisionKind.ALLOW_INTERNAL,
    ]


def test_document_link_dto_preserves_multiple_hit_rectangles() -> None:
    link = DocumentLink(
        page_index=0,
        rectangles=(PdfRect(0, 0, 10, 10), PdfRect(20, 20, 30, 30)),
        raw_destination="https://example.com",
    )
    assert len(link.rectangles) == 2


@pytest.mark.parametrize(
    ("rotation", "expected_rect"),
    [
        (0, PdfRect(20.0, 20.0, 70.0, 50.0)),
        (90, PdfRect(20.0, 80.0, 50.0, 130.0)),
        (180, PdfRect(80.0, 190.0, 130.0, 220.0)),
        (270, PdfRect(190.0, 20.0, 220.0, 70.0)),
    ],
)
def test_qtpdf_inspector_normalizes_rotated_nonzero_origin_link_rectangles(
    tmp_path: Path,
    rotation: int,
    expected_rect: PdfRect,
) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    pytest.importorskip("PySide6")
    source = tmp_path / f"transformed-{rotation}.pdf"
    _write_transformed_link_fixture(source, rotation=rotation)

    links = QtPdfRenderBackend().inspect_links(str(source), 0)
    rectangle = links[0].rectangles[0].normalized()
    activation = DocumentLinkActivationService().resolve(
        page_index=0,
        pdf_x=(expected_rect.x1 + expected_rect.x2) / 2.0,
        pdf_y=(expected_rect.y1 + expected_rect.y2) / 2.0,
        links=links,
        interaction_mode=LinkInteractionMode.PAN,
    )

    assert rectangle == expected_rect
    assert activation.decision is not None
    assert activation.decision.kind is LinkDecisionKind.CONFIRM_EXTERNAL
