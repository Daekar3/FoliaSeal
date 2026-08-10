"""Transactional application state for reusable fixed-page placement editing."""

from __future__ import annotations

from dataclasses import dataclass, replace

from foliaseal.application.coordinate_transform import (
    PdfRect,
    pdf_rect_to_visible_page_rect,
    visible_page_dimensions,
)
from foliaseal.application.reusable_signing_models import (
    PlacementProfile,
    PlacementProfileRect,
    PlacementProfileSourcePage,
    _stable_id,
)
from foliaseal.application.signing_draft_contracts import SignaturePlacementContext
from foliaseal.domain.models import SignatureRect


@dataclass(frozen=True)
class PlacementEditorState:
    """Immutable values shown by the placement editor while it is open."""

    display_name: str
    page_number: int
    source_page: PlacementProfileSourcePage
    rect: PlacementProfileRect
    pinned: bool = False
    placement_profile_id: str | None = None

    @classmethod
    def from_current_page(
        cls,
        *,
        context: SignaturePlacementContext,
        display_name: str = "New placement",
        signature_rect: SignatureRect | None = None,
    ) -> PlacementEditorState:
        """Seed an editor from the current PDF page without retaining document identity."""
        visible_width_pt, visible_height_pt = visible_page_dimensions(
            context.page_box, context.rotation
        )
        if signature_rect is not None and signature_rect.page_index == context.page_index:
            left_pt, top_pt, width_pt, height_pt = pdf_rect_to_visible_page_rect(
                pdf_rect=PdfRect(
                    x1=signature_rect.left_pt,
                    y1=signature_rect.bottom_pt,
                    x2=signature_rect.left_pt + signature_rect.width_pt,
                    y2=signature_rect.bottom_pt + signature_rect.height_pt,
                ),
                page_box=context.page_box,
                rotation=context.rotation,
            )
        else:
            width_pt = min(180.0, visible_width_pt)
            height_pt = min(54.0, visible_height_pt)
            left_pt = (visible_width_pt - width_pt) / 2
            top_pt = (visible_height_pt - height_pt) / 2
        return cls(
            display_name=display_name,
            page_number=context.page_index + 1,
            source_page=PlacementProfileSourcePage(
                visible_width_pt=visible_width_pt,
                visible_height_pt=visible_height_pt,
                rotation_degrees=context.rotation,
            ),
            rect=PlacementProfileRect(
                left_pt=left_pt,
                top_pt=top_pt,
                width_pt=width_pt,
                height_pt=height_pt,
            ),
        )

    @classmethod
    def from_blank_page(
        cls,
        *,
        visible_width_pt: float,
        visible_height_pt: float,
        rotation_degrees: int = 0,
        page_number: int = 1,
        display_name: str = "New placement",
    ) -> PlacementEditorState:
        """Seed an editor for a document-independent blank page."""
        source_page = PlacementProfileSourcePage(
            visible_width_pt=visible_width_pt,
            visible_height_pt=visible_height_pt,
            rotation_degrees=rotation_degrees,
        )
        width_pt = min(180.0, source_page.visible_width_pt)
        height_pt = min(54.0, source_page.visible_height_pt)
        return cls(
            display_name=display_name,
            page_number=page_number,
            source_page=source_page,
            rect=PlacementProfileRect(
                left_pt=(source_page.visible_width_pt - width_pt) / 2,
                top_pt=(source_page.visible_height_pt - height_pt) / 2,
                width_pt=width_pt,
                height_pt=height_pt,
            ),
        )

    @classmethod
    def from_profile(cls, profile: PlacementProfile) -> PlacementEditorState:
        return cls(
            display_name=profile.display_name,
            page_number=profile.page_number,
            source_page=profile.source_page,
            rect=profile.rect,
            pinned=profile.pinned,
            placement_profile_id=profile.placement_profile_id,
        )

    def with_values(self, **changes: object) -> PlacementEditorState:
        return replace(self, **changes)

    def to_profile(self) -> PlacementProfile:
        name = self.display_name.strip()
        if not name:
            raise ValueError("Placement name is required.")
        return PlacementProfile(
            schema_version=2,
            placement_profile_id=self.placement_profile_id or _stable_id("placement", name),
            display_name=name,
            pinned=self.pinned,
            page_number=self.page_number,
            source_page=self.source_page,
            rect=self.rect,
        )


class PlacementEditorSession:
    """Own an isolated placement draft until an explicit Save operation."""

    def __init__(self, initial: PlacementEditorState) -> None:
        self._initial = initial
        self._draft = initial
        self._closed = False

    @property
    def draft(self) -> PlacementEditorState:
        return self._draft

    @property
    def closed(self) -> bool:
        return self._closed

    def update(self, **changes: object) -> PlacementEditorState:
        if self._closed:
            raise RuntimeError("Placement editor is already closed.")
        self._draft = self._draft.with_values(**changes)
        return self._draft

    def save(self) -> PlacementProfile:
        if self._closed:
            raise RuntimeError("Placement editor is already closed.")
        profile = self._draft.to_profile()
        self._closed = True
        return profile

    def cancel(self) -> None:
        if self._closed:
            return
        self._draft = self._initial
        self._closed = True


__all__ = ["PlacementEditorSession", "PlacementEditorState"]
