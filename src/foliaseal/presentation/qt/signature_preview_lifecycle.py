"""Qt-facing lifecycle manager for canonical signing-preview renders."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application.signing_draft_workflow import SigningDraftPreview
from foliaseal.application.signing_preview_renderer import (
    CanonicalSignaturePreviewSnapshot,
    render_canonical_signature_preview,
)
from foliaseal.infra.render import QtPdfRenderBackend

_CANONICAL_PREVIEW_ACTIVE_STYLE = (
    "QGroupBox { border: none; background: transparent; padding: 0px; }"
)


@dataclass(frozen=True)
class CanonicalPreviewRenderState:
    """Widget-facing canonical preview render output."""

    snapshot: CanonicalSignaturePreviewSnapshot | None
    pixmap: Any | None
    card_style: str
    render_label_visible: bool
    render_body_size: tuple[int, int]


class QtCanonicalPreviewLifecycle:
    """Own canonical preview render/replace/cleanup behavior for the Qt shell."""

    def __init__(
        self,
        *,
        q_pixmap: Any,
        qt: Any,
        render_backend_factory: Any | None = None,
        render_snapshot: Any | None = None,
    ) -> None:
        if render_backend_factory is None:
            render_backend_factory = QtPdfRenderBackend
        if render_snapshot is None:
            render_snapshot = render_canonical_signature_preview
        self._q_pixmap = q_pixmap
        self._qt = qt
        self._render_backend = render_backend_factory()
        self._render_snapshot = render_snapshot
        self._current_snapshot: CanonicalSignaturePreviewSnapshot | None = None

    def refresh(
        self,
        *,
        preview: SigningDraftPreview,
        preview_scale: float,
        inner_body_width: int,
        inner_body_height: int,
        fallback_card_style: str,
    ) -> CanonicalPreviewRenderState:
        try:
            snapshot = self._render_snapshot(
                preview,
                zoom=max(1.0, preview_scale),
                render_backend=self._render_backend,
                include_border=True,
                flatten_to_white=False,
            )
        except (RuntimeError, ValueError):
            snapshot = None
        self._replace_snapshot(snapshot)
        if snapshot is None:
            return CanonicalPreviewRenderState(
                snapshot=None,
                pixmap=None,
                card_style=fallback_card_style,
                render_label_visible=False,
                render_body_size=(inner_body_width, inner_body_height),
            )
        pixmap = self._load_canonical_preview_pixmap(
            snapshot=snapshot,
            max_width=inner_body_width,
            max_height=inner_body_height,
        )
        width = inner_body_width
        height = inner_body_height
        pixmap_width = getattr(pixmap, "width", None)
        pixmap_height = getattr(pixmap, "height", None)
        if callable(pixmap_width):
            pixmap_width = pixmap_width()
        if callable(pixmap_height):
            pixmap_height = pixmap_height()
        if isinstance(pixmap_width, int) and isinstance(pixmap_height, int):
            width = pixmap_width
            height = pixmap_height
        return CanonicalPreviewRenderState(
            snapshot=snapshot,
            pixmap=pixmap,
            card_style=_CANONICAL_PREVIEW_ACTIVE_STYLE,
            render_label_visible=True,
            render_body_size=(width, height),
        )

    def current_snapshot(self) -> CanonicalSignaturePreviewSnapshot | None:
        """Return the current canonical preview snapshot, if any."""
        return self._current_snapshot

    def dispose(self) -> None:
        """Clean up any active canonical preview snapshot."""
        self._replace_snapshot(None)

    def _replace_snapshot(
        self,
        snapshot: CanonicalSignaturePreviewSnapshot | None,
    ) -> None:
        self._cleanup_snapshot(self._current_snapshot)
        self._current_snapshot = snapshot

    def _cleanup_snapshot(
        self,
        snapshot: CanonicalSignaturePreviewSnapshot | None,
    ) -> None:
        if snapshot is None:
            return
        image_path = Path(snapshot.image_path)
        temp_dir = image_path.parent
        if not temp_dir.name.startswith("foliaseal-canonical-preview-"):
            return
        shutil.rmtree(temp_dir, ignore_errors=True)

    def _load_canonical_preview_pixmap(
        self,
        *,
        snapshot: CanonicalSignaturePreviewSnapshot,
        max_width: int,
        max_height: int,
    ) -> Any | None:
        pixmap = self._q_pixmap(snapshot.image_path)
        is_null = getattr(pixmap, "isNull", None)
        if callable(is_null) and is_null():
            return None
        scaled = getattr(pixmap, "scaled", None)
        if callable(scaled):
            keep_aspect = getattr(self._qt, "KeepAspectRatio", None)
            smooth = getattr(self._qt, "SmoothTransformation", None)
            if keep_aspect is not None and smooth is not None:
                return scaled(
                    max_width,
                    max_height,
                    keep_aspect,
                    smooth,
                )
        return pixmap
