"""Preview render evidence adapters for live Qt and headless harness captures."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application.signing_preview_renderer import SignatureAppearanceSnapshot
from foliaseal.presentation.qt.preview_analysis import PreviewAnalysisRequest
from foliaseal.presentation.qt.preview_render_adapter import QtPreviewRasterRenderer
from foliaseal.presentation.qt.preview_render_evidence_projection import (
    PreviewEvidenceFrame,
    assemble_preview_evidence,
    build_preview_analysis_request,
)


@dataclass(frozen=True)
class PreviewRenderEvidenceDependencies:
    render_canonical_signature_preview: Callable[..., Any]
    build_preview_analysis_engine: Callable[[], Any]
    preview_analysis_request_type: type[PreviewAnalysisRequest]
    appearance_snapshot_type: type[SignatureAppearanceSnapshot]
    jsonable_capture: Callable[[Any], dict[str, Any]]
    size_hint_snapshot: Callable[[Any], dict[str, int] | None]
    write_widget_capture_png: Callable[[Any, str], str | None]
    widget_is_visible: Callable[[Any], bool]
    widget_rect_snapshot: Callable[[Any], dict[str, int] | None]
    widget_rect_snapshot_relative_to: Callable[[Any, Any], dict[str, int] | None]
    label_alignment_snapshot: Callable[[Any], str]
    label_pixmap_size_snapshot: Callable[[Any], dict[str, int] | None]
    project_pixmap_bounds_within_label: Callable[..., dict[str, int] | None]
    qt_alignment_flag: Callable[[str], int]
    preview_text_color_rgba: Callable[[Any], tuple[int, int, int, int] | None]
    preview_padding_for_capture: Callable[[Any], int]
    layout_spacing: Callable[[Any], int | None]
    write_stamp_debug_overlay: Callable[..., str | None]
    write_text_debug_overlay: Callable[..., str | None]
    cleanup_canonical_preview_tempdir: Callable[[Any], None]


@dataclass(frozen=True)
class QtPreviewRenderEvidenceAdapter:
    dependencies: PreviewRenderEvidenceDependencies

    def capture_payload(
        self,
        *,
        preview_controls: Any,
        canonical_preview_render_backend: Any,
        preview: Any,
        artifacts_dir: str | None,
        artifact_basename: str,
    ) -> dict[str, Any]:
        return build_qt_preview_render_capture_payload(
            dependencies=self.dependencies,
            preview_controls=preview_controls,
            canonical_preview_render_backend=canonical_preview_render_backend,
            preview=preview,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
        )


@dataclass(frozen=True)
class HeadlessPreviewRenderEvidenceAdapter:
    dependencies: PreviewRenderEvidenceDependencies

    def capture_payload(
        self,
        *,
        preview: Any,
        artifacts_dir: str | None,
        artifact_basename: str,
    ) -> dict[str, Any]:
        return capture_headless_preview_render(
            dependencies=self.dependencies,
            preview=preview,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
        )


def build_qt_preview_render_capture_payload(
    *,
    dependencies: PreviewRenderEvidenceDependencies,
    preview_controls: Any,
    canonical_preview_render_backend: Any,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
) -> dict[str, Any]:
    render_canonical_signature_preview = dependencies.render_canonical_signature_preview
    build_preview_analysis_engine = dependencies.build_preview_analysis_engine
    write_widget_capture_png = dependencies.write_widget_capture_png
    size_hint_snapshot = dependencies.size_hint_snapshot
    widget_is_visible = dependencies.widget_is_visible
    widget_rect_snapshot = dependencies.widget_rect_snapshot
    widget_rect_snapshot_relative_to = dependencies.widget_rect_snapshot_relative_to
    label_alignment_snapshot = dependencies.label_alignment_snapshot
    label_pixmap_size_snapshot = dependencies.label_pixmap_size_snapshot
    project_pixmap_bounds_within_label = dependencies.project_pixmap_bounds_within_label
    qt_alignment_flag = dependencies.qt_alignment_flag
    preview_text_color_rgba = dependencies.preview_text_color_rgba
    preview_padding_for_capture = dependencies.preview_padding_for_capture
    layout_spacing = dependencies.layout_spacing
    cleanup_canonical_preview_tempdir = dependencies.cleanup_canonical_preview_tempdir

    card_container = preview_controls.card_container
    single_body = preview_controls.single_body_container
    multi_body = preview_controls.multi_body_container
    detail_label = preview_controls.detail_label
    stamp_label = preview_controls.stamp_label
    multi_detail = preview_controls.multi_detail_label
    multi_stamp = preview_controls.multi_stamp_label
    canonical_snapshot = getattr(card_container, "_canonical_preview_snapshot", None)
    analysis_snapshot = None
    image_path = None
    analysis_image_path = None
    image_error = None
    analysis_text_widget_bounds = None
    if artifacts_dir is not None:
        target_dir = Path(artifacts_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        image_path = str(target_dir / f"{artifact_basename}.png")
        if canonical_snapshot is not None:
            shutil.copyfile(canonical_snapshot.image_path, image_path)
            render_kwargs: dict[str, Any] = {
                "zoom": 1.0,
                "include_border": True,
                "flatten_to_white": True,
            }
            if canonical_preview_render_backend is not None:
                render_kwargs["render_port"] = QtPreviewRasterRenderer(
                    canonical_preview_render_backend
                )
            analysis_snapshot = render_canonical_signature_preview(preview, **render_kwargs)
            analysis_image_path = str(target_dir / f"{artifact_basename}_analysis.png")
            if analysis_snapshot is not None:
                shutil.copyfile(analysis_snapshot.image_path, analysis_image_path)
                analysis_text_widget_bounds = analysis_snapshot.text_area_bounds_px
            else:
                build_preview_analysis_engine().image_comparison.flatten_preview_image_to_white(
                    source_path=canonical_snapshot.image_path,
                    output_path=analysis_image_path,
                )
        else:
            image_error = write_widget_capture_png(card_container, image_path)
            analysis_image_path = image_path

    use_single_body = widget_is_visible(single_body)
    active_body = single_body if use_single_body else multi_body
    active_detail = detail_label if use_single_body else multi_detail
    active_stamp = stamp_label if use_single_body else multi_stamp
    body_bounds = widget_rect_snapshot(active_body)
    detail_bounds = widget_rect_snapshot(active_detail)
    stamp_bounds = widget_rect_snapshot(active_stamp)
    card_bounds = widget_rect_snapshot(card_container)
    if canonical_snapshot is not None:
        card_bounds = {
            "x": 0,
            "y": 0,
            "width": canonical_snapshot.width_px,
            "height": canonical_snapshot.height_px,
        }
    image_card_bounds = (
        None
        if card_bounds is None
        else {"x": 0, "y": 0, "width": card_bounds["width"], "height": card_bounds["height"]}
    )
    body_bounds = widget_rect_snapshot_relative_to(card_container, active_body) or body_bounds
    text_widget_bounds = widget_rect_snapshot_relative_to(card_container, active_detail)
    stamp_band_bounds = widget_rect_snapshot_relative_to(card_container, active_stamp)
    if canonical_snapshot is not None:
        body_bounds = image_card_bounds
        text_widget_bounds = canonical_snapshot.text_area_bounds_px
        stamp_band_bounds = canonical_snapshot.stamp_area_bounds_px
    stamp_alignment = label_alignment_snapshot(active_stamp)
    stamp_pixmap_size = label_pixmap_size_snapshot(active_stamp)
    stamp_pixmap_bounds = project_pixmap_bounds_within_label(
        label_bounds=stamp_band_bounds,
        pixmap_size=stamp_pixmap_size,
        alignment=stamp_alignment,
        alignment_flag=qt_alignment_flag,
    )
    if canonical_snapshot is not None:
        stamp_pixmap_bounds = canonical_snapshot.stamp_bounds_px
        if canonical_snapshot.stamp_bounds_px is not None:
            stamp_pixmap_size = {
                "width": canonical_snapshot.stamp_bounds_px["width"],
                "height": canonical_snapshot.stamp_bounds_px["height"],
            }
    text_structural_content_bounds = None
    text_structural_line_bounds: tuple[dict[str, int], ...] = ()
    text_reference_content_bounds = None
    text_reference_error = None
    if canonical_snapshot is not None:
        text_structural_content_bounds = canonical_snapshot.text_bounds_px
        text_reference_content_bounds = canonical_snapshot.text_bounds_px
        base_snapshot = getattr(canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is not None:
            text_structural_line_bounds = tuple(base_snapshot.line_bounds_px or ())
    elif text_widget_bounds is not None:
        text_reference_content_bounds, text_reference_error = (
            build_preview_analysis_engine().text_geometry.reference_text_content_bounds(
                source_label=active_detail,
                text_color_rgba=preview_text_color_rgba(preview),
            )
        )
    analysis_request_image_path = analysis_image_path or image_path
    analysis_detection_bounds = analysis_text_widget_bounds or text_widget_bounds
    frame = PreviewEvidenceFrame(
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
        preview_image_path=image_path,
        analysis_image_path=analysis_image_path,
        analysis_request_image_path=analysis_request_image_path,
        image_error=image_error,
        card_bounds=image_card_bounds,
        body_bounds=body_bounds,
        detail_bounds=detail_bounds,
        stamp_bounds=stamp_bounds,
        text_widget_bounds=text_widget_bounds,
        analysis_detection_bounds=analysis_detection_bounds,
        stamp_band_bounds=stamp_band_bounds,
        stamp_pixmap_bounds=stamp_pixmap_bounds,
        stamp_pixmap_size=stamp_pixmap_size,
        stamp_content_bounds_override=(
            None if canonical_snapshot is None else canonical_snapshot.stamp_bounds_px
        ),
        structural_text_content_bounds=text_structural_content_bounds,
        structural_line_bounds=text_structural_line_bounds,
        reference_text_content_bounds=text_reference_content_bounds,
        reference_text_detection_error=text_reference_error,
        text_color_rgba=preview_text_color_rgba(preview),
        active_label=active_detail,
        preview_padding_px=preview_padding_for_capture(preview),
        layout_spacing_px=layout_spacing(active_body),
        stamp_alignment=stamp_alignment,
        single_body_bounds=widget_rect_snapshot(single_body),
        multi_body_bounds=widget_rect_snapshot(multi_body),
        detail_label_bounds=widget_rect_snapshot(detail_label),
        stamp_label_bounds=widget_rect_snapshot(stamp_label),
        multi_detail_bounds=widget_rect_snapshot(multi_detail),
        multi_stamp_bounds=widget_rect_snapshot(multi_stamp),
        detail_text_size_hint=size_hint_snapshot(detail_label),
        canonical_snapshot=canonical_snapshot,
        analysis_snapshot=analysis_snapshot,
        prefer_analysis_snapshot=True,
        fallback_snapshot_image_path_to_base=True,
    )
    analysis_values = (
        build_preview_analysis_engine()
        .analyze(build_preview_analysis_request(frame=frame, dependencies=dependencies))
        .as_mapping()
    )
    payload = assemble_preview_evidence(
        frame=frame,
        analysis_values=analysis_values,
        dependencies=dependencies,
    )
    cleanup_canonical_preview_tempdir(analysis_snapshot)
    return payload


def capture_headless_preview_render(
    *,
    dependencies: PreviewRenderEvidenceDependencies,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
) -> dict[str, Any]:
    render_canonical_signature_preview = dependencies.render_canonical_signature_preview
    build_preview_analysis_engine = dependencies.build_preview_analysis_engine
    cleanup_canonical_preview_tempdir = dependencies.cleanup_canonical_preview_tempdir
    preview_text_color_rgba = dependencies.preview_text_color_rgba
    preview_padding_for_capture = dependencies.preview_padding_for_capture
    canonical_snapshot = render_canonical_signature_preview(preview)
    image_path = None
    analysis_image_path = None
    image_error = None
    if artifacts_dir is not None:
        target_dir = Path(artifacts_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        image_path = str(target_dir / f"{artifact_basename}.png")
        if canonical_snapshot is not None:
            shutil.copyfile(canonical_snapshot.image_path, image_path)
            analysis_image_path = image_path
        else:
            image_error = "Canonical preview render is unavailable for this scenario."

    card_bounds = None
    text_widget_bounds = None
    stamp_band_bounds = None
    text_rendered_content_bounds = None
    text_structural_line_bounds: tuple[dict[str, int], ...] = ()
    stamp_content_bounds = None
    stamp_pixmap_bounds = None
    stamp_pixmap_size = None
    if canonical_snapshot is not None:
        card_bounds = {
            "x": 0,
            "y": 0,
            "width": canonical_snapshot.width_px,
            "height": canonical_snapshot.height_px,
        }
        text_widget_bounds = canonical_snapshot.text_area_bounds_px
        stamp_band_bounds = canonical_snapshot.stamp_area_bounds_px
        text_rendered_content_bounds = canonical_snapshot.text_bounds_px
        stamp_content_bounds = canonical_snapshot.stamp_bounds_px
        stamp_pixmap_bounds = canonical_snapshot.stamp_bounds_px
        if canonical_snapshot.stamp_bounds_px is not None:
            stamp_pixmap_size = {
                "width": canonical_snapshot.stamp_bounds_px["width"],
                "height": canonical_snapshot.stamp_bounds_px["height"],
            }
        base_snapshot = getattr(canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is not None:
            text_structural_line_bounds = tuple(base_snapshot.line_bounds_px or ())

    frame = PreviewEvidenceFrame(
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
        preview_image_path=image_path,
        analysis_image_path=analysis_image_path,
        analysis_request_image_path=analysis_image_path,
        image_error=image_error,
        card_bounds=card_bounds,
        body_bounds=card_bounds,
        detail_bounds=text_widget_bounds,
        stamp_bounds=stamp_band_bounds,
        text_widget_bounds=text_widget_bounds,
        analysis_detection_bounds=text_widget_bounds,
        stamp_band_bounds=stamp_band_bounds,
        stamp_pixmap_bounds=stamp_pixmap_bounds,
        stamp_pixmap_size=stamp_pixmap_size,
        stamp_content_bounds_override=stamp_content_bounds,
        structural_text_content_bounds=text_rendered_content_bounds,
        structural_line_bounds=text_structural_line_bounds,
        reference_text_content_bounds=text_rendered_content_bounds,
        reference_text_detection_error=None,
        text_color_rgba=preview_text_color_rgba(preview),
        active_label=None,
        preview_padding_px=preview_padding_for_capture(preview),
        layout_spacing_px=0,
        stamp_alignment=None,
        single_body_bounds=card_bounds,
        multi_body_bounds=card_bounds,
        detail_label_bounds=text_widget_bounds,
        stamp_label_bounds=stamp_band_bounds,
        multi_detail_bounds=text_widget_bounds,
        multi_stamp_bounds=stamp_band_bounds,
        detail_text_size_hint=None,
        canonical_snapshot=canonical_snapshot,
        analysis_snapshot=None,
        prefer_analysis_snapshot=False,
        fallback_snapshot_image_path_to_base=False,
    )
    analysis_values = (
        build_preview_analysis_engine()
        .analyze(build_preview_analysis_request(frame=frame, dependencies=dependencies))
        .as_mapping()
    )
    payload = assemble_preview_evidence(
        frame=frame,
        analysis_values=analysis_values,
        dependencies=dependencies,
    )
    cleanup_canonical_preview_tempdir(canonical_snapshot)
    return payload


__all__ = [
    "HeadlessPreviewRenderEvidenceAdapter",
    "PreviewRenderEvidenceDependencies",
    "QtPreviewRenderEvidenceAdapter",
    "build_qt_preview_render_capture_payload",
    "capture_headless_preview_render",
]
