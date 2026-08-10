"""Application-layer session for viewer-driven signature placement interactions."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.coordinate_transform import PageBox, PdfRect
from foliaseal.application.signing_draft_contracts import SignaturePlacementContext
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import SignatureRect


@dataclass(frozen=True)
class ViewerPlacementContextResult:
    """Current placement context derived from the active viewer snapshot."""

    placement_context: SignaturePlacementContext | None
    error_message: str | None = None


@dataclass(frozen=True)
class ViewerSelectionPlacementResult:
    """Result of translating a viewer selection into signing placement state."""

    signature_rect: SignatureRect | None
    placement_context: SignaturePlacementContext | None
    error_message: str | None = None


@dataclass(frozen=True)
class ViewerKeyboardPlacementResult:
    """Result of a keyboard-created or keyboard-moved placement."""

    signature_rect: SignatureRect | None
    error_message: str | None = None
    recovery_edges: tuple[str, ...] = ()


class ViewerInteractionSession:
    """Own viewer-to-signing translation logic while keeping Qt outside."""

    def __init__(self, *, viewer_workflow: ViewerWorkflow) -> None:
        self._viewer_workflow = viewer_workflow

    def current_placement_context(self) -> ViewerPlacementContextResult:
        snapshot = getattr(self._viewer_workflow, "snapshot", None)
        if snapshot is None:
            return ViewerPlacementContextResult(placement_context=None)
        page_box = snapshot.page_box
        return ViewerPlacementContextResult(
            placement_context=SignaturePlacementContext(
                page_index=snapshot.page_index,
                page_box=PageBox(
                    left=page_box.left,
                    bottom=page_box.bottom,
                    right=page_box.right,
                    top=page_box.top,
                ),
                rotation=snapshot.rotation,
            )
        )

    def select_signature_rect(self, pdf_rect: PdfRect) -> ViewerSelectionPlacementResult:
        normalized_rect = pdf_rect.normalized()
        snapshot = getattr(self._viewer_workflow, "snapshot", None)
        page_index = (
            snapshot.page_index
            if snapshot is not None
            else self._viewer_workflow.session.current_page
        )
        try:
            signature_rect = SignatureRect(
                page_index=page_index,
                left_pt=normalized_rect.x1,
                bottom_pt=normalized_rect.y1,
                width_pt=normalized_rect.x2 - normalized_rect.x1,
                height_pt=normalized_rect.y2 - normalized_rect.y1,
            )
        except ValueError as exc:
            return ViewerSelectionPlacementResult(
                signature_rect=None,
                placement_context=None,
                error_message=f"Unable to apply signature placement: {exc}",
            )
        return ViewerSelectionPlacementResult(
            signature_rect=signature_rect,
            placement_context=self.current_placement_context().placement_context,
        )

    def create_centered_signature_rect(
        self,
        *,
        width_pt: float = 216.0,
        height_pt: float = 72.0,
    ) -> ViewerKeyboardPlacementResult:
        """Create the centered default placement, proportionally fitting the page."""
        context = self.current_placement_context().placement_context
        if context is None:
            return ViewerKeyboardPlacementResult(
                signature_rect=None,
                error_message="Unable to create placement without visible page context.",
            )
        page_box = context.page_box
        scale = min(1.0, page_box.width / width_pt, page_box.height / height_pt)
        fitted_width = width_pt * scale
        fitted_height = height_pt * scale
        try:
            return ViewerKeyboardPlacementResult(
                signature_rect=SignatureRect(
                    page_index=context.page_index,
                    left_pt=page_box.left + (page_box.width - fitted_width) / 2.0,
                    bottom_pt=page_box.bottom + (page_box.height - fitted_height) / 2.0,
                    width_pt=fitted_width,
                    height_pt=fitted_height,
                )
            )
        except ValueError as exc:
            return ViewerKeyboardPlacementResult(signature_rect=None, error_message=str(exc))

    def move_signature_rect(
        self,
        signature_rect: SignatureRect,
        *,
        delta_x_pt: float,
        delta_y_pt: float,
    ) -> ViewerKeyboardPlacementResult:
        """Move a placement exactly without clamping or snapping."""
        try:
            return ViewerKeyboardPlacementResult(
                signature_rect=SignatureRect(
                    page_index=signature_rect.page_index,
                    left_pt=signature_rect.left_pt + delta_x_pt,
                    bottom_pt=signature_rect.bottom_pt + delta_y_pt,
                    width_pt=signature_rect.width_pt,
                    height_pt=signature_rect.height_pt,
                )
            )
        except ValueError as exc:
            return ViewerKeyboardPlacementResult(signature_rect=None, error_message=str(exc))

    def resize_signature_rect(
        self,
        signature_rect: SignatureRect,
        *,
        delta_width_pt: float,
        delta_height_pt: float,
    ) -> ViewerKeyboardPlacementResult:
        """Resize from the fixed bottom/left anchor without clamping or snapping."""
        try:
            return ViewerKeyboardPlacementResult(
                signature_rect=SignatureRect(
                    page_index=signature_rect.page_index,
                    left_pt=signature_rect.left_pt,
                    bottom_pt=signature_rect.bottom_pt,
                    width_pt=signature_rect.width_pt + delta_width_pt,
                    height_pt=signature_rect.height_pt + delta_height_pt,
                )
            )
        except ValueError as exc:
            return ViewerKeyboardPlacementResult(signature_rect=None, error_message=str(exc))

    def move_signature_rect_fully_onto_page(
        self,
        signature_rect: SignatureRect,
    ) -> ViewerKeyboardPlacementResult:
        """Move an off-page placement onto the visible page without scaling it."""
        context = self.current_placement_context().placement_context
        if context is None:
            return ViewerKeyboardPlacementResult(
                signature_rect=None,
                error_message="Unable to recover placement without visible page context.",
            )
        page_box = context.page_box
        if signature_rect.width_pt > page_box.width or signature_rect.height_pt > page_box.height:
            return ViewerKeyboardPlacementResult(
                signature_rect=None,
                error_message=(
                    "Placement is larger than the visible page; resize it before moving it onto "
                    "the page."
                ),
            )
        left = min(
            max(signature_rect.left_pt, page_box.left),
            page_box.right - signature_rect.width_pt,
        )
        bottom = min(
            max(signature_rect.bottom_pt, page_box.bottom),
            page_box.top - signature_rect.height_pt,
        )
        try:
            return ViewerKeyboardPlacementResult(
                signature_rect=SignatureRect(
                    page_index=context.page_index,
                    left_pt=left,
                    bottom_pt=bottom,
                    width_pt=signature_rect.width_pt,
                    height_pt=signature_rect.height_pt,
                )
            )
        except ValueError as exc:
            return ViewerKeyboardPlacementResult(signature_rect=None, error_message=str(exc))

    def set_logical_page_index(self, page_index: int) -> int:
        return self._viewer_workflow.session.jump_to_page(page_index)

    def set_page_number(self, page_number: int) -> int:
        target_index = max(page_number - 1, 0)
        return self.set_logical_page_index(target_index)
