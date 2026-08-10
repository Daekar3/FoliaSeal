"""Boundary tests for the viewer interaction session."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.viewer_interaction_session import (
    ViewerInteractionSession,
)
from foliaseal.domain.models import SignatureRect


@dataclass
class _FakeSession:
    current_page: int = 0

    def jump_to_page(self, page_index: int) -> int:
        self.current_page = page_index
        return page_index


@dataclass(frozen=True)
class _FakeSnapshot:
    page_index: int
    page_box: PageBox
    rotation: int


class _FakeViewerWorkflow:
    def __init__(self, *, snapshot: _FakeSnapshot | None = None, current_page: int = 0) -> None:
        self.snapshot = snapshot
        self.session = _FakeSession(current_page=current_page)


def test_select_signature_rect_uses_snapshot_page_index_and_returns_context() -> None:
    workflow = _FakeViewerWorkflow(
        snapshot=_FakeSnapshot(
            page_index=2,
            page_box=PageBox(left=0.0, bottom=0.0, right=612.0, top=792.0),
            rotation=90,
        ),
        current_page=0,
    )
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    result = session.select_signature_rect(PdfRect(x1=10.0, y1=20.0, x2=60.0, y2=80.0))

    assert result.error_message is None
    assert result.signature_rect is not None
    assert result.signature_rect.page_index == 2
    assert result.signature_rect.left_pt == 10.0
    assert result.signature_rect.bottom_pt == 20.0
    assert result.signature_rect.width_pt == 50.0
    assert result.signature_rect.height_pt == 60.0
    assert result.placement_context is not None
    assert result.placement_context.page_index == 2
    assert result.placement_context.rotation == 90


def test_select_signature_rect_falls_back_to_logical_page_without_snapshot() -> None:
    workflow = _FakeViewerWorkflow(snapshot=None, current_page=3)
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    result = session.select_signature_rect(PdfRect(x1=5.0, y1=6.0, x2=20.0, y2=26.0))

    assert result.error_message is None
    assert result.signature_rect is not None
    assert result.signature_rect.page_index == 3
    assert result.placement_context is None


def test_select_signature_rect_returns_stable_error_for_invalid_rectangle() -> None:
    workflow = _FakeViewerWorkflow(snapshot=None, current_page=0)
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    result = session.select_signature_rect(PdfRect(x1=10.0, y1=10.0, x2=10.0, y2=20.0))

    assert result.signature_rect is None
    assert result.placement_context is None
    assert result.error_message == (
        "Unable to apply signature placement: width_pt must be a positive finite number."
    )


def test_current_placement_context_returns_none_without_snapshot() -> None:
    workflow = _FakeViewerWorkflow(snapshot=None, current_page=0)
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    result = session.current_placement_context()

    assert result.placement_context is None
    assert result.error_message is None


def test_set_page_number_normalizes_to_zero_based_page_index() -> None:
    workflow = _FakeViewerWorkflow(snapshot=None, current_page=0)
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    target = session.set_page_number(2)

    assert target == 1
    assert workflow.session.current_page == 1


def test_create_centered_signature_rect_fits_small_page_proportionally() -> None:
    workflow = _FakeViewerWorkflow(
        snapshot=_FakeSnapshot(
            page_index=1,
            page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
            rotation=0,
        )
    )
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    result = session.create_centered_signature_rect()

    assert result.error_message is None
    assert result.signature_rect is not None
    assert result.signature_rect.page_index == 1
    assert result.signature_rect.width_pt == 100.0
    assert result.signature_rect.height_pt == pytest.approx(33.333333333333336)
    assert result.signature_rect.left_pt == 0.0
    assert result.signature_rect.bottom_pt == pytest.approx(33.33333333333333)


def test_move_signature_rect_preserves_exact_delta_without_clamping() -> None:
    workflow = _FakeViewerWorkflow(
        snapshot=_FakeSnapshot(
            page_index=0,
            page_box=PageBox(left=0.0, bottom=0.0, right=100.0, top=100.0),
            rotation=0,
        )
    )
    session = ViewerInteractionSession(viewer_workflow=workflow)  # type: ignore[arg-type]

    result = session.move_signature_rect(
        SignatureRect(page_index=0, left_pt=10.0, bottom_pt=20.0, width_pt=30.0, height_pt=10.0),
        delta_x_pt=-25.0,
        delta_y_pt=110.0,
    )

    assert result.error_message is None
    assert result.signature_rect is not None
    assert result.signature_rect.left_pt == -15.0
    assert result.signature_rect.bottom_pt == 130.0
