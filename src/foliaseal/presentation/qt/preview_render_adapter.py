"""Qt composition adapter for the neutral application preview raster port."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.application.preview_render_boundary import (
    PreviewRasterRenderer,
    PreviewRasterRequest,
    PreviewRasterResult,
)
from foliaseal.infra.render.base import RenderPageRequest


@dataclass(frozen=True)
class QtPreviewRasterRenderer(PreviewRasterRenderer):
    """Adapt one configured Qt/PDF backend to the application port."""

    backend: object

    def render_page(self, request: PreviewRasterRequest) -> PreviewRasterResult:
        result = self.backend.render_page(
            RenderPageRequest(
                document_path=str(request.document_path),
                page_index=request.page_index,
                zoom=request.zoom,
            )
        )
        return PreviewRasterResult(
            width_px=result.width_px,
            height_px=result.height_px,
            rgba_bytes=result.rgba_bytes,
        )
