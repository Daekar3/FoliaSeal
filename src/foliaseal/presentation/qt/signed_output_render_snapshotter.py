"""Signed-output render-analysis boundary for Acceptance QA."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from foliaseal.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewTransform,
    pdf_rect_to_view_rect,
)
from foliaseal.infra.render import RenderPageRequest

RenderBackendFactory = Callable[[], Any]
RenderSignedAnnotationAppearanceDirect = Callable[..., dict[str, Any]]
ParseSnapshotRect = Callable[[Any], tuple[float, float, float, float] | None]
PreviewPaddingForCaptureFromSnapshot = Callable[[dict[str, Any]], int]
SnapshotPreviewCardBounds = Callable[[dict[str, Any]], dict[str, int] | None]
SnapshotPreviewAnalysisImage = Callable[[dict[str, Any]], str | None]
NormalizedImageCropChangeRatio = Callable[..., float | None]
AspectRatioDelta = Callable[[float, float, float, float], float | None]
NormalizeVisibleTextForComparison = Callable[[str], str]
SnapshotVisibleAppearanceTextFragments = Callable[[dict[str, Any]], list[str]]
SnapshotVisibleAppearanceImageXObjects = Callable[[dict[str, Any]], list[str]]
DetectTextContentBoundsInPreview = Callable[..., tuple[dict[str, Any] | None, str | None]]
DetectTextLineBoundsInPreview = Callable[..., tuple[tuple[dict[str, Any], ...], str | None]]
PreviewTextColorRgbaFromSnapshot = Callable[[dict[str, Any]], tuple[int, int, int, int]]
PreviewAppearanceSnapshotFromCapture = Callable[..., Any]
SignedOutputAppearanceSnapshot = Callable[..., Any]
CompareSignatureAppearanceSnapshots = Callable[[Any, Any], Any]
SignatureRectFromSnapshot = Callable[[dict[str, Any]], dict[str, Any] | None]
SnapshotRectSizeAndOriginDict = Callable[[Any], dict[str, Any] | None]
RectDelta = Callable[[dict[str, Any], dict[str, Any] | None], dict[str, Any] | None]
RectDeltaWithinTolerance = Callable[[dict[str, Any] | None, float], bool | None]
RectanglesWithinTolerance = Callable[[Any, Any, int], bool | None]
WriteSideBySideComparison = Callable[..., None]
JsonableCapture = Callable[[Any], Any]
Mapping = Callable[[Any], dict[str, Any]]


@dataclass(frozen=True)
class AcceptanceSignedOutputRenderSnapshotter:
    """Own signed-output render analysis for one successful output."""

    render_backend_factory: RenderBackendFactory
    render_signed_annotation_appearance_direct: RenderSignedAnnotationAppearanceDirect
    parse_snapshot_rect: ParseSnapshotRect
    preview_padding_for_capture_from_snapshot: PreviewPaddingForCaptureFromSnapshot
    snapshot_preview_card_bounds: SnapshotPreviewCardBounds
    snapshot_preview_analysis_image: SnapshotPreviewAnalysisImage
    normalized_image_crop_change_ratio: NormalizedImageCropChangeRatio
    aspect_ratio_delta: AspectRatioDelta
    normalize_visible_text_for_comparison: NormalizeVisibleTextForComparison
    snapshot_visible_appearance_text_fragments: SnapshotVisibleAppearanceTextFragments
    snapshot_visible_appearance_image_xobjects: SnapshotVisibleAppearanceImageXObjects
    detect_text_content_bounds_in_preview: DetectTextContentBoundsInPreview
    detect_text_line_bounds_in_preview: DetectTextLineBoundsInPreview
    preview_text_color_rgba_from_snapshot: PreviewTextColorRgbaFromSnapshot
    preview_appearance_snapshot_from_capture: PreviewAppearanceSnapshotFromCapture
    signed_output_appearance_snapshot: SignedOutputAppearanceSnapshot
    compare_signature_appearance_snapshots: CompareSignatureAppearanceSnapshots
    signature_rect_from_snapshot: SignatureRectFromSnapshot
    snapshot_rect_size_and_origin_dict: SnapshotRectSizeAndOriginDict
    rect_delta: RectDelta
    rect_delta_within_tolerance: RectDeltaWithinTolerance
    rectangles_within_tolerance: RectanglesWithinTolerance
    write_side_by_side_comparison: WriteSideBySideComparison
    jsonable_capture: JsonableCapture
    mapping: Mapping

    def run(
        self,
        *,
        output_pdf_path: str | None,
        page_index: int | None,
        preview_snapshot: dict[str, Any],
        preview_text: str,
        output_visible_appearance_snapshot: dict[str, Any] | None,
        artifacts_dir: str | None,
        artifact_basename: str | None,
    ) -> dict[str, Any] | None:
        if output_pdf_path is None or page_index is None:
            return None

        result: dict[str, Any] = {
            "page_index": page_index,
            "page_number": page_index + 1,
            "page_render_path": None,
            "signature_crop_path": None,
            "normalized_signature_crop_path": None,
            "comparison_path": None,
            "page_render_error": None,
            "signature_crop_error": None,
            "comparison_error": None,
            "preview_crop_bounds_px": None,
            "signed_crop_bounds_px": None,
            "preview_crop_dimensions_px": None,
            "signed_crop_dimensions_px": None,
            "normalized_signed_crop_dimensions_px": None,
            "preview_vs_signed_output_change_ratio": None,
            "preview_vs_signed_output_aspect_ratio_delta": None,
            "preview_text_fragments_match_output": None,
            "annotation_rect_delta_pt": None,
            "annotation_rect_matches_request": None,
            "output_text_content_bounds_px": None,
            "output_text_detection_error": None,
            "output_text_bounds_match_preview": None,
            "preview_has_image_stamp": None,
            "signed_output_has_image_stamp": None,
            "output_image_presence_matches_preview": None,
            "preview_vs_signed_output_passed": None,
            "preview_appearance_snapshot": None,
            "signed_output_appearance_snapshot": None,
            "appearance_layer_comparison": None,
            "direct_appearance_render_path": None,
            "direct_appearance_render_error": None,
        }
        if artifacts_dir is None or artifact_basename is None:
            result["page_render_error"] = "Signed-output render artifacts are unavailable."
            return result

        backend = self.render_backend_factory()
        diagnostic = backend.diagnostics()
        if not diagnostic.available:
            result["page_render_error"] = diagnostic.message
            return result

        try:
            render_zoom = 3.0
            render = backend.render_page(
                RenderPageRequest(
                    document_path=output_pdf_path,
                    page_index=page_index,
                    zoom=render_zoom,
                )
            )
            page_image = Image.frombytes(
                "RGBA",
                (render.width_px, render.height_px),
                render.rgba_bytes,
            )
            if page_image.mode != "RGBA":
                page_image = page_image.convert("RGBA")
            white_page = Image.new("RGBA", page_image.size, (255, 255, 255, 255))
            page_image = Image.alpha_composite(white_page, page_image)
            page_render_path = Path(artifacts_dir) / f"{artifact_basename}_signed_output_page.png"
            page_image.save(page_render_path)
            result["page_render_path"] = str(page_render_path)
        except Exception as exc:
            result["page_render_error"] = str(exc)
            return result

        direct_appearance_render = self.render_signed_annotation_appearance_direct(
            output_pdf_path=output_pdf_path,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
            zoom=render_zoom,
        )
        result["direct_appearance_render_path"] = direct_appearance_render.get("image_path")
        result["direct_appearance_render_error"] = direct_appearance_render.get("error")

        try:
            visible_snapshot = output_visible_appearance_snapshot or {}
            rect = self.parse_snapshot_rect(visible_snapshot.get("annotation_rect"))
            if rect is None:
                result["signature_crop_error"] = (
                    "Output visible appearance did not include a rect."
                )
                return result
            geometry = backend.get_page_geometry(output_pdf_path, page_index)
            page_box = PageBox(*geometry.crop_box)
            pdf_rect = PdfRect(*rect)
            view_rect = pdf_rect_to_view_rect(
                pdf_rect=pdf_rect,
                transform=ViewTransform(zoom=render_zoom, pan_x=0.0, pan_y=0.0),
                page_box=page_box,
                rotation=geometry.rotation,
            )
            view_left = min(view_rect.x1, view_rect.x2)
            view_right = max(view_rect.x1, view_rect.x2)
            view_top = min(view_rect.y1, view_rect.y2)
            view_bottom = max(view_rect.y1, view_rect.y2)
            padding = max(6, self.preview_padding_for_capture_from_snapshot(preview_snapshot))
            crop_bounds = {
                "x": max(0, int(round(view_left)) - padding),
                "y": max(0, int(round(view_top)) - padding),
                "width": max(
                    1,
                    min(
                        render.width_px,
                        int(round(view_right)) + padding,
                    )
                    - max(0, int(round(view_left)) - padding),
                ),
                "height": max(
                    1,
                    min(
                        render.height_px,
                        int(round(view_bottom)) + padding,
                    )
                    - max(0, int(round(view_top)) - padding),
                ),
            }
            crop_right = crop_bounds["x"] + crop_bounds["width"]
            crop_bottom = crop_bounds["y"] + crop_bounds["height"]
            if crop_right <= crop_bounds["x"] or crop_bottom <= crop_bounds["y"]:
                result["signature_crop_error"] = "Signed output crop is empty."
                return result
            cropped = page_image.crop(
                (crop_bounds["x"], crop_bounds["y"], crop_right, crop_bottom)
            )
            crop_path = Path(artifacts_dir) / f"{artifact_basename}_signed_output_crop.png"
            cropped.save(crop_path)
            result["signature_crop_path"] = str(crop_path)
            result["signed_crop_bounds_px"] = crop_bounds
            result["signed_crop_dimensions_px"] = {
                "width": cropped.size[0],
                "height": cropped.size[1],
            }
            result["signature_crop_sha256"] = hashlib.sha256(cropped.tobytes()).hexdigest()
            preview_crop_bounds = self.snapshot_preview_card_bounds(preview_snapshot)
            if preview_crop_bounds is not None:
                preview_analysis_image_path = self.snapshot_preview_analysis_image(
                    preview_snapshot
                )
                parity_source = cropped
                if direct_appearance_render.get("image_path"):
                    with Image.open(direct_appearance_render["image_path"]) as direct_image:
                        parity_source = direct_image.convert("RGBA")
                normalized_crop = parity_source.resize(
                    (
                        preview_crop_bounds["width"],
                        preview_crop_bounds["height"],
                    ),
                    Image.Resampling.LANCZOS,
                )
                normalized_crop_path = (
                    Path(artifacts_dir)
                    / f"{artifact_basename}_signed_output_crop_normalized.png"
                )
                normalized_crop.save(normalized_crop_path)
                result["normalized_signature_crop_path"] = str(normalized_crop_path)
                result["normalized_signed_crop_dimensions_px"] = {
                    "width": normalized_crop.size[0],
                    "height": normalized_crop.size[1],
                }
                result["preview_crop_bounds_px"] = preview_crop_bounds
                result["preview_crop_dimensions_px"] = {
                    "width": preview_crop_bounds["width"],
                    "height": preview_crop_bounds["height"],
                }
                result["preview_vs_signed_output_change_ratio"] = (
                    self.normalized_image_crop_change_ratio(
                        previous_image_path=preview_analysis_image_path,
                        previous_bounds=preview_crop_bounds,
                        current_image_path=str(normalized_crop_path),
                        current_bounds={
                            "x": 0,
                            "y": 0,
                            "width": normalized_crop.size[0],
                            "height": normalized_crop.size[1],
                        },
                    )
                )
                result["preview_vs_signed_output_aspect_ratio_delta"] = self.aspect_ratio_delta(
                    preview_crop_bounds["width"],
                    preview_crop_bounds["height"],
                    cropped.size[0],
                    cropped.size[1],
                )
                preview_text_normalized = self.normalize_visible_text_for_comparison(
                    preview_text
                )
                output_text = self.normalize_visible_text_for_comparison(
                    " ".join(
                        self.snapshot_visible_appearance_text_fragments(visible_snapshot)
                    )
                )
                result["preview_text_fragments_match_output"] = (
                    preview_text_normalized == output_text
                )
                result["preview_has_image_stamp"] = bool(
                    preview_snapshot.get("image_stamp_path")
                )
                result["signed_output_has_image_stamp"] = bool(
                    self.snapshot_visible_appearance_image_xobjects(visible_snapshot)
                )
                result["output_image_presence_matches_preview"] = (
                    result["preview_has_image_stamp"]
                    == result["signed_output_has_image_stamp"]
                )
                render_capture = self.mapping(preview_snapshot.get("render_capture"))
                reference_bounds = self.mapping(
                    render_capture.get("text_rendered_content_bounds_px")
                )
                output_text_bounds, output_text_error = (
                    self.detect_text_content_bounds_in_preview(
                        preview_image_path=str(normalized_crop_path),
                        text_widget_bounds={
                            "x": 0,
                            "y": 0,
                            "width": normalized_crop.size[0],
                            "height": normalized_crop.size[1],
                        },
                        text_color_rgba=self.preview_text_color_rgba_from_snapshot(
                            preview_snapshot
                        ),
                        reference_text_content_bounds=reference_bounds,
                    )
                )
                output_text_line_bounds, output_text_line_error = (
                    self.detect_text_line_bounds_in_preview(
                        preview_image_path=str(normalized_crop_path),
                        text_widget_bounds={
                            "x": 0,
                            "y": 0,
                            "width": normalized_crop.size[0],
                            "height": normalized_crop.size[1],
                        },
                        text_color_rgba=self.preview_text_color_rgba_from_snapshot(
                            preview_snapshot
                        ),
                        reference_text_content_bounds=reference_bounds,
                    )
                )
                result["output_text_content_bounds_px"] = output_text_bounds
                result["output_text_detection_error"] = output_text_error
                result["output_text_line_bounds_px"] = output_text_line_bounds
                result["output_text_line_detection_error"] = output_text_line_error
                result["output_text_bounds_match_preview"] = (
                    self.rectangles_within_tolerance(
                        result.get("output_text_content_bounds_px"),
                        reference_bounds,
                        tolerance_px=6,
                    )
                )
                preview_appearance_snapshot = self.preview_appearance_snapshot_from_capture(
                    preview_snapshot=preview_snapshot
                )
                signed_output_appearance_snapshot = (
                    self.signed_output_appearance_snapshot(
                        normalized_image_path=str(normalized_crop_path),
                        normalized_image_size={
                            "width": normalized_crop.size[0],
                            "height": normalized_crop.size[1],
                        },
                        text_bounds_px=result.get("output_text_content_bounds_px"),
                        line_bounds_px=tuple(result.get("output_text_line_bounds_px") or ()),
                        visible_appearance_snapshot=visible_snapshot,
                        preview_snapshot=preview_snapshot,
                    )
                )
                result["preview_appearance_snapshot"] = preview_appearance_snapshot
                result["signed_output_appearance_snapshot"] = (
                    signed_output_appearance_snapshot
                )
                appearance_comparison = self.jsonable_capture(
                    self.compare_signature_appearance_snapshots(
                        preview_appearance_snapshot,
                        signed_output_appearance_snapshot,
                    )
                )
                result["appearance_layer_comparison"] = appearance_comparison
                requested_rect = self.signature_rect_from_snapshot(preview_snapshot)
                if requested_rect is not None:
                    result["annotation_rect_delta_pt"] = self.rect_delta(
                        requested_rect,
                        self.snapshot_rect_size_and_origin_dict(
                            self.mapping(visible_snapshot).get("annotation_rect")
                        ),
                    )
                    result["annotation_rect_matches_request"] = (
                        self.rect_delta_within_tolerance(
                            result["annotation_rect_delta_pt"],
                            tolerance_pt=0.75,
                        )
                    )
                result["preview_vs_signed_output_passed"] = (
                    appearance_comparison.get("is_consistent") is True
                    and result["annotation_rect_matches_request"] is not False
                )
            comparison_path = (
                Path(artifacts_dir) / f"{artifact_basename}_signed_output_compare.png"
            )
            self.write_side_by_side_comparison(
                preview_image_path=self.snapshot_preview_analysis_image(preview_snapshot),
                preview_bounds=preview_crop_bounds,
                signed_image_path=(
                    result.get("normalized_signature_crop_path") or str(crop_path)
                ),
                signed_bounds={
                    "x": 0,
                    "y": 0,
                    "width": (
                        preview_crop_bounds["width"]
                        if preview_crop_bounds is not None
                        else cropped.size[0]
                    ),
                    "height": (
                        preview_crop_bounds["height"]
                        if preview_crop_bounds is not None
                        else cropped.size[1]
                    ),
                },
                output_path=str(comparison_path),
            )
            result["comparison_path"] = str(comparison_path)
            return result
        except Exception as exc:
            result["signature_crop_error"] = str(exc)
            return result
