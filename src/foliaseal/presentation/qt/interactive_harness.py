"""Interactive Qt harness for Acceptance signing-shell acceptance."""

from __future__ import annotations

import importlib
import json
import re
import shutil
from functools import partial
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.fidelity_contract import validate_release_fidelity_contract
from foliaseal.application.qa_evidence_contract import evaluate_acceptance_evidence_contract
from foliaseal.application.signing_backend import (
    build_backend_reservation_evidence,
    build_signing_executor,
)
from foliaseal.application.signing_preview_renderer import (
    SignatureAppearanceSnapshot,
    _layout_rule_bounds_px,
    _structural_line_bounds_px,
    compare_signature_appearance_snapshots,
    render_canonical_signature_preview,
)
from foliaseal.application.visible_signature_layout import (
    VisibleSignatureLayoutEngine,
    VisibleSignatureLayoutInput,
    VisibleSignatureLayoutPolicy,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureImageProminence,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SigningRequest,
    TimestampTrustPolicy,
)
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.signing_transaction_journal import FileSigningTransactionJournal
from foliaseal.infra.render import RenderPageRequest
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend
from foliaseal.infra.tsa import build_dummy_timestamper
from foliaseal.presentation.qt.acceptance_harness_workspace import (
    AcceptanceHarnessWorkspacePort,
    HeadlessAcceptanceHarnessWorkspaceAdapter,
    HeadlessAcceptanceHarnessWorkspaceDeps,
    InteractiveHarnessCaptureCommand,
    InteractiveHarnessScenarioCommand,
    QtAcceptanceHarnessWorkspaceAdapter,
    QtAcceptanceHarnessWorkspaceDeps,
    capture_qt_preview_render,
)
from foliaseal.presentation.qt.appearance_snapshotter import (
    AcceptanceAppearanceSnapshotter,
)
from foliaseal.presentation.qt.evidence_harness_projection import (
    evaluate_signed_matrix_acceptance_expectations,
    preview_matrix_diagnostic_summary,
    preview_matrix_error_result,
    signed_matrix_diagnostic_summary,
)
from foliaseal.presentation.qt.evidence_interactive_capture import (
    InteractiveEvidenceArtifactPolicy,
    InteractiveHarnessCapture,
    build_capture_from_payload,
    default_harness_artifacts_dir,
    default_harness_output_pdf_path,
    jsonable_capture,
    write_optional_text,
)
from foliaseal.presentation.qt.evidence_runner_providers import (
    EvidenceRunnerProviders,
    InteractiveEvidenceProviders,
    PreviewMatrixEvidenceProviders,
    SignedAcceptanceEvidenceProviders,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_layout_scaling as _project_layout_scaling,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_layout_template as _project_layout_template,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_preview_edge_distance as _project_preview_edge_distance,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_request_field_count as _project_request_field_count,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_reservation_margin_bottom as _project_reservation_margin_bottom,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_reservation_stamp_background as _project_reservation_stamp_background,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_reservation_text_length as _project_reservation_text_length,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_show_field_names as _project_show_field_names,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_sign_request_appearance as _project_sign_request_appearance,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_stamp_position as _project_stamp_position,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_annotation_rect as _project_visible_annotation_rect,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_bbox as _project_visible_bbox,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_error as _project_visible_error,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_field_name as _project_visible_field_name,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_has_text as _project_visible_has_text,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_image_xobjects as _project_visible_xobjects,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_stream_length as _project_visible_stream_length,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_text_fragments as _project_visible_fragments,
)
from foliaseal.presentation.qt.evidence_snapshot_projection import (
    snapshot_visible_appearance_text_fragments_summary as _project_visible_fragments_summary,
)
from foliaseal.presentation.qt.interactive_harness_capture_assembler import (
    InteractiveHarnessCaptureAssembler,
    snapshot_signing_result_payload,
)
from foliaseal.presentation.qt.interactive_harness_reporting import (
    build_acceptance_checklist_results_markdown,
    finalize_interactive_harness_report,
)
from foliaseal.presentation.qt.interactive_harness_session_runner import (
    InteractiveHarnessSessionRunner,
    InteractiveHarnessSessionRunnerDeps,
    _QtHarnessBindings,
)
from foliaseal.presentation.qt.pdf_signature_snapshotter import (
    AcceptancePdfSignatureSnapshotter,
    snapshot_pdf_rect,
)
from foliaseal.presentation.qt.preview_analysis import (
    PreviewAnalysisEngine,
    PreviewAnalysisRequest,
    build_preview_analysis_engine,
    normalize_visible_text_for_comparison,
)
from foliaseal.presentation.qt.preview_render_adapter import QtPreviewRasterRenderer
from foliaseal.presentation.qt.preview_render_capture import (
    HeadlessPreviewRenderCaptureAdapter,
    QtPreviewRenderCaptureAdapter,
)
from foliaseal.presentation.qt.preview_render_evidence_adapters import (
    HeadlessPreviewRenderEvidenceAdapter,
    PreviewRenderEvidenceDependencies,
    QtPreviewRenderEvidenceAdapter,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    draw_overlay_rect as _draw_overlay_rect,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    label_alignment_snapshot as _label_alignment_snapshot,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    label_pixmap_size_snapshot as _label_pixmap_size_snapshot,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    offset_rect as _offset_rect,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    preview_text_color_rgba as _preview_text_color_rgba,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    project_pixmap_bounds_within_label as _project_pixmap_bounds_within_label,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    size_hint_snapshot as _size_hint_snapshot,
)
from foliaseal.presentation.qt.preview_widget_evidence import (
    widget_rect_snapshot as _widget_rect_snapshot,
)
from foliaseal.presentation.qt.sign_time_diagnostics_snapshotter import (
    AcceptanceSignTimeDiagnosticsSnapshotter,
)
from foliaseal.presentation.qt.signed_acceptance_scenario_executor import (
    SignedAcceptanceScenarioExecutor,
    SignedAcceptanceScenarioExecutorDeps,
    SignedAcceptanceScenarioResult,
)
from foliaseal.presentation.qt.signed_output_render_snapshotter import (
    AcceptanceSignedOutputRenderSnapshotter,
)
from foliaseal.presentation.qt.signed_output_snapshotter import (
    AcceptanceSignedOutputSnapshotter,
)
from foliaseal.presentation.qt.signing_shell_port import (
    QtSigningWorkspaceFactory,
    SigningWorkspaceBundle,
)

DEFAULT_ACCEPTANCE_CHECKLIST_TEMPLATE_PATH = "artifacts/acceptance_fr3b_acceptance_checklist.md"
DEFAULT_ACCEPTANCE_CHECKLIST_RESULTS_PATH = "artifacts/acceptance_fr3b_acceptance_results.md"


def _build_qt_signing_executor(*, timestamper_factory: Any | None = None) -> Any:
    """Compose signing with the neutral preview raster boundary at the Qt edge."""

    return build_signing_executor(
        timestamper_factory=timestamper_factory,
        render_port=QtPreviewRasterRenderer(QtPdfRenderBackend()),
        transaction_journal=FileSigningTransactionJournal.default(),
    )


def build_capture_assembler() -> InteractiveHarnessCaptureAssembler:
    pdf_snapshotter = AcceptancePdfSignatureSnapshotter()
    analysis_engine = _build_preview_analysis_engine()
    return InteractiveHarnessCaptureAssembler(
        count_embedded_signatures=pdf_snapshotter.count_embedded_signatures,
        snapshot_output_signature=pdf_snapshotter.snapshot_output_signature,
        snapshot_output_verification=pdf_snapshotter.snapshot_output_verification,
        snapshot_visible_signature_appearance=pdf_snapshotter.snapshot_visible_signature_appearance,
        snapshot_signed_output_render=_snapshot_signed_output_render,
        analyze_capture_state_transitions=analysis_engine.analyze_capture_transitions,
    )


def build_interactive_session_runner() -> InteractiveHarnessSessionRunner:
    return InteractiveHarnessSessionRunner(
        deps=InteractiveHarnessSessionRunnerDeps(
            build_workspace=_build_qt_evidence_workspace,
            default_harness_output_pdf_path=default_harness_output_pdf_path,
            create_workspace=QtSigningWorkspaceFactory().create,
        )
    )


def build_evidence_runner_providers() -> EvidenceRunnerProviders:
    """Build the complete evidence-runner provider bundle at the composition root."""

    return EvidenceRunnerProviders(
        interactive=InteractiveEvidenceProviders(
            load_qt_harness_bindings=_load_qt_harness_bindings,
            load_page_count=_load_page_count,
            render_backend_factory=QtPdfRenderBackend,
            profile_store_factory=SignaturePresetCatalogStore.default,
            build_signing_executor=_build_qt_signing_executor,
            session_runner=build_interactive_session_runner(),
            capture_assembler=build_capture_assembler(),
            contract_evaluator=evaluate_acceptance_evidence_contract,
            capture_factory=build_capture_from_payload,
            checklist_renderer=build_acceptance_checklist_results_markdown,
            report_finalizer=finalize_interactive_harness_report,
            artifact_policy=InteractiveEvidenceArtifactPolicy(
                default_artifacts_dir=default_harness_artifacts_dir,
                output_pdf_path=default_harness_output_pdf_path,
                write_text=write_optional_text,
            ),
        ),
        preview=PreviewMatrixEvidenceProviders(
            load_preview_matrix_manifest=_load_preview_matrix_manifest,
            execute_headless_preview_matrix_scenario=(
                _execute_headless_preview_matrix_scenario
            ),
            preview_matrix_error_result=preview_matrix_error_result,
            preview_matrix_diagnostic_summary=preview_matrix_diagnostic_summary,
            jsonable_capture=jsonable_capture,
            profile_store_factory=SignaturePresetCatalogStore.default,
        ),
        signed=SignedAcceptanceEvidenceProviders(
            load_qt_harness_bindings=_load_qt_harness_bindings,
            load_preview_matrix_manifest=_load_preview_matrix_manifest,
            build_signing_executor=_build_qt_signing_executor,
            build_dummy_timestamper=build_dummy_timestamper,
            load_page_count=_load_page_count,
            build_workspace=_build_preview_matrix_qt_workspace,
            execute_signed_acceptance_scenario=_execute_signed_acceptance_scenario,
            preview_matrix_error_result=preview_matrix_error_result,
            signed_matrix_diagnostic_summary=signed_matrix_diagnostic_summary,
            evaluate_signed_matrix_acceptance_expectations=(
                evaluate_signed_matrix_acceptance_expectations
            ),
            jsonable_capture=jsonable_capture,
            render_backend_factory=QtPdfRenderBackend,
            profile_store_factory=SignaturePresetCatalogStore.default,
            create_workspace=QtSigningWorkspaceFactory().create,
        ),
    )


def _build_live_evidence_workspace(
    *,
    workspace: SigningWorkspaceBundle,
    profile_store: Any,
) -> AcceptanceHarnessWorkspacePort:
    return QtAcceptanceHarnessWorkspaceAdapter(
        workspace=workspace,
        profile_store=profile_store,
        deps=QtAcceptanceHarnessWorkspaceDeps(
            capture_preview_render=QtPreviewRenderCaptureAdapter(
                callback=partial(
                    capture_qt_preview_render,
                    build_preview_render_capture_payload=_build_qt_preview_render_capture_payload,
                ),
            ),
            snapshot_preview=_snapshot_preview,
            snapshot_signing_request=_snapshot_signing_request,
            build_backend_reservation_evidence=build_backend_reservation_evidence,
            snapshot_sign_time_fit_diagnostics=_snapshot_sign_time_fit_diagnostics,
            interactive_capture_label=_interactive_capture_label,
        ),
    )


def _build_qt_evidence_workspace(
    workspace: SigningWorkspaceBundle,
) -> AcceptanceHarnessWorkspacePort:
    return _build_live_evidence_workspace(workspace=workspace, profile_store=object())


def _build_preview_matrix_qt_workspace(
    *,
    workspace: SigningWorkspaceBundle,
    profile_store: SignaturePresetCatalogStore,
) -> AcceptanceHarnessWorkspacePort:
    return _build_live_evidence_workspace(workspace=workspace, profile_store=profile_store)


def _build_preview_matrix_headless_workspace(
    *,
    workflow: SigningDraftWorkflow,
    profile_store: SignaturePresetCatalogStore,
) -> AcceptanceHarnessWorkspacePort:
    return HeadlessAcceptanceHarnessWorkspaceAdapter(
        workflow=workflow,
        profile_store=profile_store,
        deps=HeadlessAcceptanceHarnessWorkspaceDeps(
            headless_preview_text=_headless_preview_text,
            headless_validation_text=_headless_validation_text,
            capture_headless_preview_render=HeadlessPreviewRenderCaptureAdapter(
                callback=_capture_headless_preview_render,
            ),
            snapshot_preview=_snapshot_preview,
            snapshot_signing_request=_snapshot_signing_request,
            build_backend_reservation_evidence=build_backend_reservation_evidence,
        ),
    )


def _interactive_capture_label(*, preview, capture_index: int, capture_kind: str) -> str:
    layout_name = preview.layout_template.value if preview.layout_template else "unknown_layout"
    stamp_name = preview.stamp_position.value if preview.stamp_position else "unknown_stamp"
    return f"{capture_kind}_{capture_index:02d}_{layout_name}_{stamp_name}"


def _snapshot_successful_signed_output(
    *,
    output_file: Path,
    page_index: int | None,
    preview_snapshot: dict[str, Any],
    preview_text: str,
    trust_policy: TimestampTrustPolicy | None,
    artifacts_dir: str | None,
    artifact_basename: str | None,
) -> dict[str, Any]:
    return _build_signed_output_snapshotter().snapshot_successful_signed_output(
        output_file=output_file,
        page_index=page_index,
        preview_snapshot=preview_snapshot,
        preview_text=preview_text,
        trust_policy=trust_policy,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
    )


def _build_signed_acceptance_scenario_executor() -> SignedAcceptanceScenarioExecutor:
    return SignedAcceptanceScenarioExecutor(
        deps=SignedAcceptanceScenarioExecutorDeps(
            apply_preview_matrix_scenario=_apply_preview_matrix_scenario,
            build_workspace=_build_preview_matrix_qt_workspace,
            scenario_slug=_scenario_slug,
            snapshot_signing_result_payload=snapshot_signing_result_payload,
            snapshot_successful_signed_output=_snapshot_successful_signed_output,
        )
    )


def _build_signed_output_snapshotter() -> AcceptanceSignedOutputSnapshotter:
    pdf_snapshotter = AcceptancePdfSignatureSnapshotter()
    return AcceptanceSignedOutputSnapshotter(
        count_embedded_signatures=pdf_snapshotter.count_embedded_signatures,
        snapshot_output_signature=pdf_snapshotter.snapshot_output_signature,
        snapshot_output_verification=pdf_snapshotter.snapshot_output_verification,
        snapshot_visible_signature_appearance=pdf_snapshotter.snapshot_visible_signature_appearance,
        snapshot_signed_output_render=_snapshot_signed_output_render,
    )


def _build_signed_output_render_snapshotter() -> AcceptanceSignedOutputRenderSnapshotter:
    analysis_engine = _build_preview_analysis_engine()
    return AcceptanceSignedOutputRenderSnapshotter(
        render_backend_factory=QtPdfRenderBackend,
        render_signed_annotation_appearance_direct=_render_signed_annotation_appearance_direct,
        parse_snapshot_rect=_parse_snapshot_rect,
        preview_padding_for_capture_from_snapshot=_preview_padding_for_capture_from_snapshot,
        snapshot_preview_card_bounds=_snapshot_preview_card_bounds,
        snapshot_preview_analysis_image=_snapshot_preview_analysis_image,
        normalized_image_crop_change_ratio=(
            analysis_engine.image_comparison.normalized_image_crop_change_ratio
        ),
        aspect_ratio_delta=analysis_engine.image_comparison.aspect_ratio_delta,
        normalize_visible_text_for_comparison=normalize_visible_text_for_comparison,
        snapshot_visible_appearance_text_fragments=_snapshot_visible_appearance_text_fragments,
        snapshot_visible_appearance_image_xobjects=_snapshot_visible_appearance_image_xobjects,
        detect_text_content_bounds_in_preview=(
            analysis_engine.text_geometry.detect_text_content_bounds_in_preview
        ),
        detect_text_line_bounds_in_preview=(
            analysis_engine.text_geometry.detect_text_line_bounds_in_preview
        ),
        preview_text_color_rgba_from_snapshot=_preview_text_color_rgba_from_snapshot,
        preview_appearance_snapshot_from_capture=_preview_appearance_snapshot_from_capture,
        signed_output_appearance_snapshot=_signed_output_appearance_snapshot,
        compare_signature_appearance_snapshots=compare_signature_appearance_snapshots,
        signature_rect_from_snapshot=_signature_rect_from_snapshot,
        snapshot_rect_size_and_origin_dict=_snapshot_rect_size_and_origin_dict,
        rect_delta=_rect_delta,
        rect_delta_within_tolerance=_rect_delta_within_tolerance,
        rectangles_within_tolerance=_rectangles_within_tolerance,
        write_side_by_side_comparison=(
            analysis_engine.image_comparison.write_side_by_side_comparison
        ),
        jsonable_capture=jsonable_capture,
        mapping=_mapping,
    )


def _build_appearance_snapshotter() -> AcceptanceAppearanceSnapshotter:
    analysis_engine = _build_preview_analysis_engine()
    return AcceptanceAppearanceSnapshotter(
        mapping=_mapping,
        signature_text_style_from_snapshot=_signature_text_style_from_snapshot,
        structural_line_bounds=_structural_line_bounds_px,
        visible_appearance_image_xobjects=_snapshot_visible_appearance_image_xobjects,
        visible_appearance_text_fragments=_snapshot_visible_appearance_text_fragments,
        reconstruct_text_box_bounds=_reconstruct_text_box_bounds_px,
        union_rectangles=analysis_engine.text_geometry.union_rectangles,
    )


def _load_qt_harness_bindings() -> _QtHarnessBindings:
    widgets = importlib.import_module("PySide6.QtWidgets")
    qtpdf = importlib.import_module("PySide6.QtPdf")
    return _QtHarnessBindings(
        q_application=getattr(widgets, "QApplication"),
        q_main_window=getattr(widgets, "QMainWindow"),
        q_widget=getattr(widgets, "QWidget"),
        q_v_box_layout=getattr(widgets, "QVBoxLayout"),
        q_h_box_layout=getattr(widgets, "QHBoxLayout"),
        q_group_box=getattr(widgets, "QGroupBox"),
        q_push_button=getattr(widgets, "QPushButton"),
        q_label=getattr(widgets, "QLabel"),
        q_plain_text_edit=getattr(widgets, "QPlainTextEdit"),
        qpdf_document=getattr(qtpdf, "QPdfDocument"),
    )


def _load_page_count(*, bindings: _QtHarnessBindings, pdf_path: str) -> int:
    document = bindings.qpdf_document()
    status = document.load(pdf_path)
    if status != bindings.qpdf_document.Error.None_:
        raise RuntimeError(f"Failed to load PDF document: {pdf_path}")
    return int(document.pageCount())


def _render_signed_annotation_appearance_direct(
    *,
    output_pdf_path: str,
    artifacts_dir: str,
    artifact_basename: str,
    zoom: float = 3.0,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "image_path": None,
        "image_size_px": None,
        "wrapper_pdf_path": None,
        "error": None,
    }
    try:
        output_path = Path(output_pdf_path)
        with output_path.open("rb") as handle:
            reader = PdfFileReader(handle)
            embedded_signatures = list(reader.embedded_signatures)
            if not embedded_signatures:
                result["error"] = "Signed PDF does not contain an embedded signature."
                return result
            signature = embedded_signatures[-1]
            appearance_dict = signature.sig_field.get("/AP")
            if appearance_dict is None or appearance_dict.get("/N") is None:
                result["error"] = "Signed PDF does not contain a normal appearance stream."
                return result
            normal_appearance = appearance_dict["/N"]

            writer = PdfFileWriter()
            imported_appearance = writer.import_object(normal_appearance)
            appearance_ref = writer.add_object(imported_appearance)
            bbox = snapshot_pdf_rect(imported_appearance.get("/BBox"))
            if bbox is None:
                result["error"] = "Signed appearance stream does not define a /BBox."
                return result
            left, bottom, right, top = bbox
            min_x = min(left, right)
            max_x = max(left, right)
            min_y = min(bottom, top)
            max_y = max(bottom, top)
            width = max(1.0, max_x - min_x)
            height = max(1.0, max_y - min_y)

            page_resources = generic.DictionaryObject(
                {
                    generic.pdf_name("/XObject"): generic.DictionaryObject(
                        {generic.pdf_name("/Fx"): appearance_ref}
                    )
                }
            )
            content_stream = generic.StreamObject(
                stream_data=(f"q 1 0 0 1 {-min_x} {-min_y} cm /Fx Do Q".encode("ascii"))
            )
            stream_ref = writer.add_object(content_stream)
            page = PageObject(
                contents=stream_ref,
                media_box=(0, 0, width, height),
                resources=page_resources,
            )
            writer.insert_page(page)

            target_dir = Path(artifacts_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            wrapper_pdf_path = target_dir / f"{artifact_basename}_signed_output_appearance.pdf"
            with wrapper_pdf_path.open("wb") as handle:
                writer.write(handle)
            result["wrapper_pdf_path"] = str(wrapper_pdf_path)

        backend = QtPdfRenderBackend()
        diagnostic = backend.diagnostics()
        if not diagnostic.available:
            result["error"] = diagnostic.message
            return result

        render = backend.render_page(
            RenderPageRequest(
                document_path=str(wrapper_pdf_path),
                page_index=0,
                zoom=zoom,
            )
        )
        image = Image.frombytes("RGBA", (render.width_px, render.height_px), render.rgba_bytes)
        image_path = target_dir / f"{artifact_basename}_signed_output_appearance.png"
        image.save(image_path)
        result["image_path"] = str(image_path)
        result["image_size_px"] = {"width": render.width_px, "height": render.height_px}
        return result
    except Exception as exc:
        result["error"] = str(exc)
        return result


def _appearance_text_uses_rounded_border(appearance_text: str) -> bool | None:
    if not appearance_text.strip():
        return None
    if " c " in appearance_text or appearance_text.strip().startswith("c "):
        return True
    if " re S" in appearance_text or "\nre\nS" in appearance_text:
        return False
    return None


def _snapshot_signed_output_render(
    *,
    output_pdf_path: str | None,
    page_index: int | None,
    preview_snapshot: dict[str, Any],
    preview_text: str,
    output_visible_appearance_snapshot: dict[str, Any] | None,
    artifacts_dir: str | None,
    artifact_basename: str | None,
) -> dict[str, Any] | None:
    return _build_signed_output_render_snapshotter().run(
        output_pdf_path=output_pdf_path,
        page_index=page_index,
        preview_snapshot=preview_snapshot,
        preview_text=preview_text,
        output_visible_appearance_snapshot=output_visible_appearance_snapshot,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
    )


def _preview_appearance_snapshot_from_capture(
    *,
    preview_snapshot: dict[str, Any],
) -> SignatureAppearanceSnapshot:
    return _build_appearance_snapshotter().preview_appearance_snapshot_from_capture(
        preview_snapshot=preview_snapshot
    )


def _build_sign_time_diagnostics_snapshotter() -> AcceptanceSignTimeDiagnosticsSnapshotter:
    return AcceptanceSignTimeDiagnosticsSnapshotter(mapping=_mapping)


def _build_preview_analysis_engine() -> PreviewAnalysisEngine:
    return build_preview_analysis_engine(write_widget_capture_png=_write_widget_capture_png)


def _snapshot_sign_time_fit_diagnostics(
    *,
    preview_render_capture: dict[str, Any] | None,
    backend_reservation_snapshot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    return _build_sign_time_diagnostics_snapshotter().snapshot(
        preview_render_capture=preview_render_capture,
        backend_reservation_snapshot=backend_reservation_snapshot,
    )


def _signed_output_appearance_snapshot(
    *,
    normalized_image_path: str,
    normalized_image_size: dict[str, int],
    text_bounds_px: dict[str, int] | None,
    line_bounds_px: tuple[dict[str, int], ...] = (),
    visible_appearance_snapshot: dict[str, Any],
    preview_snapshot: dict[str, Any],
) -> SignatureAppearanceSnapshot:
    return _build_appearance_snapshotter().signed_output_appearance_snapshot(
        normalized_image_path=normalized_image_path,
        normalized_image_size=normalized_image_size,
        text_bounds_px=text_bounds_px,
        line_bounds_px=line_bounds_px,
        visible_appearance_snapshot=visible_appearance_snapshot,
        preview_snapshot=preview_snapshot,
    )


def _signature_text_style_from_snapshot(snapshot: object) -> SignatureTextStyle | None:
    if not isinstance(snapshot, dict):
        return None
    font_family = snapshot.get("font_family")
    font_size_pt = snapshot.get("font_size_pt")
    text_color_hex = snapshot.get("text_color_hex")
    if (
        not isinstance(font_family, str)
        or font_size_pt is None
        or not isinstance(text_color_hex, str)
    ):
        return None
    return SignatureTextStyle(
        font_family=font_family,
        font_size_pt=float(font_size_pt),
        bold=bool(snapshot.get("bold")),
        italic=bool(snapshot.get("italic")),
        text_color_hex=text_color_hex,
    )


def _signature_box_style_from_snapshot(snapshot: object) -> SignatureBoxStyle | None:
    if not isinstance(snapshot, dict):
        return None
    border_color_hex = snapshot.get("border_color_hex")
    background_color_hex = snapshot.get("background_color_hex")
    border_width_pt = snapshot.get("border_width_pt")
    if not isinstance(border_color_hex, str) or not isinstance(background_color_hex, str):
        return None
    if border_width_pt is None:
        return None
    return SignatureBoxStyle(
        show_border=bool(snapshot.get("show_border")),
        border_color_hex=border_color_hex,
        border_width_pt=float(border_width_pt),
        background_color_hex=background_color_hex,
    )


def _signature_rect_from_preview_snapshot(snapshot: object) -> SignatureRect | None:
    if not isinstance(snapshot, dict):
        return None
    rect = snapshot.get("signature_rect")
    if not isinstance(rect, dict):
        return None
    try:
        return SignatureRect(
            page_index=int(rect["page_index"]),
            left_pt=float(rect["left_pt"]),
            bottom_pt=float(rect["bottom_pt"]),
            width_pt=float(rect["width_pt"]),
            height_pt=float(rect["height_pt"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _reconstruct_text_box_bounds_px(
    *,
    preview_snapshot: dict[str, Any],
    text_fragments: tuple[str, ...],
    container_bounds_px: dict[str, int],
) -> dict[str, int] | None:
    if not text_fragments:
        return None
    layout_template_value = preview_snapshot.get("layout_template")
    stamp_position_value = preview_snapshot.get("stamp_position")
    if not isinstance(layout_template_value, str) or not isinstance(stamp_position_value, str):
        return None
    text_style = _signature_text_style_from_snapshot(preview_snapshot.get("text_style"))
    box_style = _signature_box_style_from_snapshot(preview_snapshot.get("box_style"))
    signature_rect = _signature_rect_from_preview_snapshot(preview_snapshot)
    if text_style is None or box_style is None or signature_rect is None:
        return None
    try:
        layout_template = SignatureLayoutTemplate(layout_template_value)
        stamp_position = SignatureStampPosition(stamp_position_value)
    except ValueError:
        return None
    stamp_text = "\n".join(fragment for fragment in text_fragments if fragment.strip())
    if not stamp_text:
        return None
    image_stamp_path_value = preview_snapshot.get("image_stamp_path")
    image_stamp_path = (
        image_stamp_path_value
        if isinstance(image_stamp_path_value, str) and image_stamp_path_value
        else None
    )
    image_prominence_value = preview_snapshot.get("image_prominence")
    try:
        image_prominence = (
            SignatureImageProminence(image_prominence_value)
            if isinstance(image_prominence_value, str)
            else SignatureImageProminence.PRIMARY
        )
    except ValueError:
        image_prominence = SignatureImageProminence.PRIMARY
    layout_plan = VisibleSignatureLayoutEngine().plan(
        VisibleSignatureLayoutInput(
            signature_rect=signature_rect,
            layout_template=layout_template,
            stamp_position=stamp_position,
            text_style=text_style,
            box_style=box_style,
            stamp_text=stamp_text,
            image_stamp_path=image_stamp_path,
            image_prominence=image_prominence,
        )
    )
    return _layout_rule_bounds_px(
        layout_plan.text_layout,
        reserved_width_pt=layout_plan.text_box.width_pt,
        reserved_height_pt=layout_plan.text_box.height_pt,
        width_px=container_bounds_px["width"],
        height_px=container_bounds_px["height"],
        container_width_pt=signature_rect.width_pt,
        container_height_pt=signature_rect.height_pt,
        include_when_empty=True,
    )


def _snapshot_preview(
    preview,
    *,
    render_capture: dict[str, Any] | None = None,
    sign_time_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "title": preview.title,
        "signer_label_prefix": preview.signer_label_prefix,
        "layout_template": preview.layout_template.value if preview.layout_template else None,
        "stamp_position": preview.stamp_position.value if preview.stamp_position else None,
        "timezone_display_mode": (
            preview.timezone_display_mode.value if preview.timezone_display_mode else None
        ),
        "show_field_names": preview.show_field_names,
        "datetime_format": preview.datetime_format,
        "image_stamp_path": preview.image_stamp_path,
        "image_prominence": (
            getattr(preview, "image_prominence", None).value
            if getattr(preview, "image_prominence", None) is not None
            else None
        ),
        "preserve_image_alpha": getattr(preview, "preserve_image_alpha", None),
        "signature_rect": _snapshot_signature_rect(preview.signature_rect),
        "text_style": _snapshot_text_style(preview.text_style),
        "box_style": _snapshot_box_style(preview.box_style),
        "fields": [_snapshot_preview_field(field) for field in preview.fields],
        "issues": [_snapshot_issue(issue) for issue in preview.issues],
        "can_submit": preview.can_submit,
        "render_capture": render_capture,
        "sign_time_diagnostics": sign_time_diagnostics,
    }


def _load_preview_matrix_manifest(path: str) -> dict[str, Any]:
    manifest_path = Path(path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Scenario manifest does not exist: {path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    acceptance_expectations: dict[str, Any] | None = None
    timestamping_mode: str | None = None
    if isinstance(payload, list):
        scenarios = payload
    elif isinstance(payload, dict):
        scenarios = payload.get("scenarios")
        if "manifest_version" in payload or "comparison_contract" in payload:
            validate_release_fidelity_contract(payload)
        raw_expectations = payload.get("acceptance_expectations")
        if raw_expectations is not None:
            if not isinstance(raw_expectations, dict):
                raise ValueError("'acceptance_expectations' must be a JSON object.")
            acceptance_expectations = raw_expectations
        raw_timestamping_mode = payload.get("timestamping_mode")
        if raw_timestamping_mode is not None:
            if raw_timestamping_mode not in {"real", "dummy"}:
                raise ValueError("'timestamping_mode' must be one of 'real' or 'dummy'.")
            timestamping_mode = raw_timestamping_mode
    else:
        raise ValueError("Scenario manifest must be a JSON object or array.")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("Scenario manifest must define a non-empty 'scenarios' array.")
    validated: list[dict[str, Any]] = []
    for index, scenario in enumerate(scenarios):
        if not isinstance(scenario, dict):
            raise ValueError(f"Scenario at index {index} must be a JSON object.")
        name = scenario.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Scenario at index {index} must define a non-empty 'name'.")
        expected_outcome = scenario.get("expected_outcome")
        if expected_outcome is not None and expected_outcome not in (
            "success",
            "validation_rejection",
        ):
            raise ValueError(
                f"Scenario '{name}' has unsupported expected_outcome: {expected_outcome!r}"
            )
        timestamp_required = scenario.get("timestamp_required")
        if timestamp_required is not None and not isinstance(timestamp_required, bool):
            raise ValueError(
                f"Scenario '{name}' has unsupported timestamp_required: {timestamp_required!r}"
            )
        validated.append(scenario)
    manifest: dict[str, Any] = {"scenarios": validated}
    if acceptance_expectations is not None:
        manifest["acceptance_expectations"] = acceptance_expectations
    if timestamping_mode is not None:
        manifest["timestamping_mode"] = timestamping_mode
    for key in ("fixture_profile", "fixture_role"):
        if isinstance(payload, dict) and key in payload:
            manifest[key] = payload[key]
    if isinstance(payload, dict):
        for key in ("manifest_version", "comparison_contract"):
            if key in payload:
                manifest[key] = payload[key]
    return manifest


def _execute_preview_matrix_scenario(
    *,
    workspace: SigningWorkspaceBundle,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
    artifacts_dir: Path,
) -> dict[str, Any]:
    workspace = _build_preview_matrix_qt_workspace(
        workspace=workspace,
        profile_store=profile_store,
    )
    workspace.apply_scenario(InteractiveHarnessScenarioCommand.from_mapping(scenario))
    artifact_basename = _scenario_slug(str(scenario["name"]))
    capture = workspace.capture_snapshot(
        InteractiveHarnessCaptureCommand(
            request=None,
            artifacts_dir=str(artifacts_dir),
            artifact_basename=artifact_basename,
            capture_index=1,
            capture_kind="preview_matrix",
        )
    ).as_mapping()
    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "preview_snapshot": capture["preview_snapshot"],
        "preview_text": capture["preview_text"],
        "validation_text": capture["validation_text"],
        "sign_request_snapshot": capture["sign_request_snapshot"],
        "backend_reservation_snapshot": capture["backend_reservation_snapshot"],
    }


def _execute_headless_preview_matrix_scenario(
    *,
    source_path: Path,
    certificate_path: str,
    passphrase: str,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
    artifacts_dir: Path,
) -> dict[str, Any]:
    workflow = _build_headless_preview_matrix_workflow(
        source_path=source_path,
        certificate_path=certificate_path,
        passphrase=passphrase,
    )
    workspace = _build_preview_matrix_headless_workspace(
        workflow=workflow,
        profile_store=profile_store,
    )
    workspace.apply_scenario(InteractiveHarnessScenarioCommand.from_mapping(scenario))
    artifact_basename = _scenario_slug(str(scenario["name"]))
    capture = workspace.capture_snapshot(
        InteractiveHarnessCaptureCommand(
            request=None,
            artifacts_dir=str(artifacts_dir),
            artifact_basename=artifact_basename,
            capture_index=1,
            capture_kind="preview_matrix",
        )
    ).as_mapping()
    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "preview_snapshot": capture["preview_snapshot"],
        "preview_text": capture["preview_text"],
        "validation_text": capture["validation_text"],
        "sign_request_snapshot": capture["sign_request_snapshot"],
        "backend_reservation_snapshot": capture["backend_reservation_snapshot"],
    }


def _build_headless_preview_matrix_workflow(
    *,
    source_path: Path,
    certificate_path: str,
    passphrase: str,
) -> SigningDraftWorkflow:
    workflow = SigningDraftWorkflow(
        input_pdf_path=str(source_path),
        output_pdf_path=str(source_path.with_name(source_path.stem + "-signed.pdf")),
        certificate_path=certificate_path,
        passphrase=passphrase,
        tsa_url="https://tsa.example.invalid",
        timestamp_required=False,
    )
    if workflow.signature_appearance is None:
        workflow.set_signature_appearance(SignatureAppearance())
    return workflow


def _headless_preview_text(preview: Any) -> str:
    title_text = (preview.signer_label_prefix or preview.title or "").strip()
    detail_text = (getattr(preview, "detail_text", "") or "").strip()
    if title_text and detail_text:
        return f"{title_text}\n{detail_text}"
    if title_text:
        return title_text
    if detail_text:
        return detail_text
    return "No visible fields selected"


def _headless_validation_text(preview: Any) -> str:
    issues = getattr(preview, "issues", ())
    blocking = [issue.message for issue in issues if issue.severity.value == "error"]
    warnings = [issue.message for issue in issues if issue.severity.value == "warning"]
    lines: list[str] = []
    if blocking:
        lines.extend(blocking)
    elif warnings:
        lines.extend(warnings)
    else:
        return "Ready to sign."
    return "\n".join(lines)


def _execute_signed_acceptance_scenario(
    *,
    workspace: SigningWorkspaceBundle,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
    artifacts_dir: Path,
    base_input_path: Path,
    certificate_path: str,
    passphrase: str,
    sign_executor: Any,
) -> SignedAcceptanceScenarioResult | dict[str, Any]:
    kwargs: dict[str, Any] = {
        "workspace": workspace,
        "scenario": scenario,
        "profile_store": profile_store,
        "artifacts_dir": artifacts_dir,
        "base_input_path": base_input_path,
        "certificate_path": certificate_path,
        "passphrase": passphrase,
        "sign_executor": sign_executor,
    }
    return _build_signed_acceptance_scenario_executor().run_result(
        **kwargs,
    )


def _apply_preview_matrix_scenario(
    *,
    workspace: SigningWorkspaceBundle,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
) -> None:
    _build_preview_matrix_qt_workspace(
        workspace=workspace,
        profile_store=profile_store,
    ).apply_scenario(InteractiveHarnessScenarioCommand.from_mapping(scenario))


def _preview_render_evidence_dependencies() -> PreviewRenderEvidenceDependencies:
    return PreviewRenderEvidenceDependencies(
        render_canonical_signature_preview=render_canonical_signature_preview,
        build_preview_analysis_engine=_build_preview_analysis_engine,
        preview_analysis_request_type=PreviewAnalysisRequest,
        appearance_snapshot_type=SignatureAppearanceSnapshot,
        jsonable_capture=jsonable_capture,
        size_hint_snapshot=_size_hint_snapshot,
        write_widget_capture_png=_write_widget_capture_png,
        widget_is_visible=_widget_is_visible,
        widget_rect_snapshot=_widget_rect_snapshot,
        widget_rect_snapshot_relative_to=_widget_rect_snapshot_relative_to,
        label_alignment_snapshot=_label_alignment_snapshot,
        label_pixmap_size_snapshot=_label_pixmap_size_snapshot,
        project_pixmap_bounds_within_label=_project_pixmap_bounds_within_label,
        qt_alignment_flag=_qt_alignment_flag,
        preview_text_color_rgba=_preview_text_color_rgba,
        preview_padding_for_capture=_preview_padding_for_capture,
        layout_spacing=_layout_spacing,
        write_stamp_debug_overlay=_write_stamp_debug_overlay,
        write_text_debug_overlay=_write_text_debug_overlay,
        cleanup_canonical_preview_tempdir=_cleanup_canonical_preview_tempdir,
    )


def _build_qt_preview_render_capture_payload(
    *,
    preview_controls: Any,
    canonical_preview_render_backend: Any,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
) -> dict[str, Any]:
    return QtPreviewRenderEvidenceAdapter(
        dependencies=_preview_render_evidence_dependencies(),
    ).capture_payload(
        preview_controls=preview_controls,
        canonical_preview_render_backend=canonical_preview_render_backend,
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
    )


def _capture_headless_preview_render(
    *,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
) -> dict[str, Any]:
    return HeadlessPreviewRenderEvidenceAdapter(
        dependencies=_preview_render_evidence_dependencies(),
    ).capture_payload(
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
    )


def _cleanup_canonical_preview_tempdir(
    snapshot: Any,
) -> None:
    if snapshot is None:
        return
    image_path = Path(snapshot.image_path)
    temp_dir = image_path.parent
    if not temp_dir.name.startswith("foliaseal-canonical-preview-"):
        return
    shutil.rmtree(temp_dir, ignore_errors=True)


def _preview_padding_for_capture(preview: Any) -> int:
    if (
        preview.signature_rect is not None
        and preview.layout_template == SignatureLayoutTemplate.SINGLE_LINE
        and preview.stamp_position in {SignatureStampPosition.TOP, SignatureStampPosition.BOTTOM}
    ):
        return VisibleSignatureLayoutPolicy.margins(
            stamp_position=SignatureStampPosition.TOP,
            box_height_pt=max(1, int(round(preview.signature_rect.height_pt))),
            box_style=preview.box_style,
        ).top
    if preview.signature_rect is None or preview.stamp_position is None:
        return 6
    return VisibleSignatureLayoutPolicy.margins(
        stamp_position=preview.stamp_position,
        box_height_pt=max(1, int(round(preview.signature_rect.height_pt))),
        box_style=preview.box_style,
    ).top


def _write_widget_capture_png(widget: Any, output_path: str) -> str | None:
    grab = getattr(widget, "grab", None)
    if not callable(grab):
        return "Widget capture is unavailable because the Qt widget does not expose grab()."
    pixmap = grab()
    save = getattr(pixmap, "save", None)
    if not callable(save):
        return "Widget capture is unavailable because the grabbed pixmap does not expose save()."
    if not save(output_path):
        return f"Failed to save preview image to '{output_path}'."
    return None


def _write_stamp_debug_overlay(
    *,
    preview_image_path: str,
    output_path: str,
    stamp_band_bounds: dict[str, int],
    stamp_pixmap_bounds: dict[str, int],
    stamp_content_bounds: dict[str, int] | None,
    crop_padding: int,
) -> str | None:
    try:
        with Image.open(preview_image_path) as image:
            preview_image = image.convert("RGBA")
    except OSError as exc:
        return f"Failed to open preview image for stamp debug overlay: {exc}"

    image_width, image_height = preview_image.size
    crop_left = max(0, stamp_band_bounds["x"] - crop_padding)
    crop_top = max(0, stamp_band_bounds["y"] - crop_padding)
    crop_right = min(
        image_width,
        stamp_band_bounds["x"] + stamp_band_bounds["width"] + crop_padding,
    )
    crop_bottom = min(
        image_height,
        stamp_band_bounds["y"] + stamp_band_bounds["height"] + crop_padding,
    )
    cropped = preview_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    draw = ImageDraw.Draw(cropped)
    for bounds, color in (
        (_offset_rect(stamp_band_bounds, dx=-crop_left, dy=-crop_top), (255, 165, 0, 255)),
        (_offset_rect(stamp_pixmap_bounds, dx=-crop_left, dy=-crop_top), (0, 120, 255, 255)),
    ):
        _draw_overlay_rect(draw, bounds, color)
    if stamp_content_bounds is not None:
        _draw_overlay_rect(
            draw,
            _offset_rect(stamp_content_bounds, dx=-crop_left, dy=-crop_top),
            (0, 200, 120, 255),
        )
    cropped.save(output_path)
    return None


def _write_text_debug_overlay(
    *,
    preview_image_path: str,
    output_path: str,
    text_widget_bounds: dict[str, int],
    text_content_bounds: dict[str, int] | None,
    stamp_band_bounds: dict[str, int] | None,
    crop_padding: int,
) -> str | None:
    try:
        with Image.open(preview_image_path) as image:
            preview_image = image.convert("RGBA")
    except OSError as exc:
        return f"Failed to open preview image for text debug overlay: {exc}"

    highlight_bounds = [text_widget_bounds]
    if text_content_bounds is not None:
        highlight_bounds.append(text_content_bounds)
    if stamp_band_bounds is not None:
        highlight_bounds.append(stamp_band_bounds)
    crop_left = max(0, min(bounds["x"] for bounds in highlight_bounds) - crop_padding)
    crop_top = max(0, min(bounds["y"] for bounds in highlight_bounds) - crop_padding)
    crop_right = min(
        preview_image.size[0],
        max(bounds["x"] + bounds["width"] for bounds in highlight_bounds) + crop_padding,
    )
    crop_bottom = min(
        preview_image.size[1],
        max(bounds["y"] + bounds["height"] for bounds in highlight_bounds) + crop_padding,
    )
    cropped = preview_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    draw = ImageDraw.Draw(cropped)
    _draw_overlay_rect(
        draw,
        _offset_rect(text_widget_bounds, dx=-crop_left, dy=-crop_top),
        (128, 0, 255, 255),
    )
    if text_content_bounds is not None:
        _draw_overlay_rect(
            draw,
            _offset_rect(text_content_bounds, dx=-crop_left, dy=-crop_top),
            (0, 180, 80, 255),
        )
    if stamp_band_bounds is not None:
        _draw_overlay_rect(
            draw,
            _offset_rect(stamp_band_bounds, dx=-crop_left, dy=-crop_top),
            (255, 165, 0, 255),
        )
    cropped.save(output_path)
    return None


def _widget_is_visible(widget: Any) -> bool:
    visible = getattr(widget, "isVisible", None)
    if callable(visible):
        return bool(visible())
    visible = getattr(widget, "visible", None)
    if isinstance(visible, bool):
        return visible
    return True


def _qt_alignment_flag(name: str) -> int:
    try:
        qt_core = importlib.import_module("PySide6.QtCore")
    except ImportError:
        return 0
    qt = getattr(qt_core, "Qt", None)
    if qt is None:
        return 0
    direct = getattr(qt, name, None)
    if direct is not None:
        return int(direct)
    alignment_flag = getattr(qt, "AlignmentFlag", None)
    if alignment_flag is None:
        return 0
    value = getattr(alignment_flag, name, None)
    return int(value) if value is not None else 0


def _widget_rect_snapshot_relative_to(root_widget: Any, widget: Any) -> dict[str, int] | None:
    bounds = _widget_rect_snapshot(widget)
    if root_widget is None or widget is None or bounds is None:
        return bounds
    if root_widget is widget:
        return bounds
    is_ancestor_of = getattr(root_widget, "isAncestorOf", None)
    if callable(is_ancestor_of) and not is_ancestor_of(widget):
        return bounds
    map_to = getattr(widget, "mapTo", None)
    if not callable(map_to):
        return bounds
    qt_core = importlib.import_module("PySide6.QtCore")
    point = map_to(root_widget, getattr(qt_core, "QPoint")(0, 0))
    x_getter = getattr(point, "x", None)
    y_getter = getattr(point, "y", None)
    if not callable(x_getter) or not callable(y_getter):
        return bounds
    return {
        "x": int(x_getter()),
        "y": int(y_getter()),
        "width": bounds["width"],
        "height": bounds["height"],
    }


def _preview_padding_for_capture_from_snapshot(snapshot: dict[str, Any]) -> int:
    signature_rect = snapshot.get("signature_rect")
    layout_template = snapshot.get("layout_template")
    stamp_position = _selected_stamp_position(snapshot)
    box_style = _snapshot_preview_box_style_snapshot(snapshot)
    if not isinstance(signature_rect, dict):
        return 6
    rect = type(
        "_Rect",
        (),
        {"height_pt": signature_rect.get("height_pt", 0.0)},
    )()
    preview_like = type(
        "_PreviewLike",
        (),
        {
            "signature_rect": rect,
            "layout_template": _layout_template_from_snapshot(layout_template),
            "stamp_position": stamp_position,
            "box_style": box_style,
        },
    )()
    return _preview_padding_for_capture(preview_like)


def _preview_text_color_rgba_from_snapshot(
    snapshot: dict[str, Any] | None,
) -> tuple[int, int, int, int] | None:
    if snapshot is None:
        return None
    text_style = snapshot.get("text_style")
    if not isinstance(text_style, dict):
        return None
    color_hex = text_style.get("text_color_hex")
    if not isinstance(color_hex, str):
        return None
    normalized = color_hex.strip().lstrip("#")
    if len(normalized) != 6:
        return None
    try:
        return (
            int(normalized[0:2], 16),
            int(normalized[2:4], 16),
            int(normalized[4:6], 16),
            255,
        )
    except ValueError:
        return None


def _signature_rect_from_snapshot(snapshot: dict[str, Any] | None) -> dict[str, float] | None:
    if snapshot is None:
        return None
    rect = snapshot.get("signature_rect")
    if not isinstance(rect, dict):
        return None
    try:
        return {
            "left_pt": float(rect["left_pt"]),
            "bottom_pt": float(rect["bottom_pt"]),
            "width_pt": float(rect["width_pt"]),
            "height_pt": float(rect["height_pt"]),
        }
    except Exception:
        return None


def _snapshot_rect_size_and_origin_dict(value: Any) -> dict[str, float] | None:
    rect = _parse_snapshot_rect(value)
    if rect is None:
        return None
    left, bottom, right, top = rect
    return {
        "left_pt": left,
        "bottom_pt": bottom,
        "width_pt": max(0.0, right - left),
        "height_pt": max(0.0, top - bottom),
    }


def _rect_delta(
    expected: dict[str, float] | None,
    actual: dict[str, float] | None,
) -> dict[str, float] | None:
    if expected is None or actual is None:
        return None
    return {
        "left_pt": actual["left_pt"] - expected["left_pt"],
        "bottom_pt": actual["bottom_pt"] - expected["bottom_pt"],
        "width_pt": actual["width_pt"] - expected["width_pt"],
        "height_pt": actual["height_pt"] - expected["height_pt"],
    }


def _rect_delta_within_tolerance(
    delta: dict[str, float] | None,
    *,
    tolerance_pt: float,
) -> bool | None:
    if delta is None:
        return None
    return all(abs(value) <= tolerance_pt for value in delta.values())


def _rectangles_within_tolerance(
    first: dict[str, int] | None,
    second: dict[str, int] | None,
    *,
    tolerance_px: int,
) -> bool | None:
    if first is None or second is None:
        return None
    return all(
        abs(int(first.get(key, 0)) - int(second.get(key, 0))) <= tolerance_px
        for key in ("x", "y", "width", "height")
    )


def _selected_stamp_position(snapshot: dict[str, Any] | None) -> SignatureStampPosition | None:
    position = _snapshot_stamp_position(snapshot)
    if position is None:
        return None
    try:
        return SignatureStampPosition(position)
    except ValueError:
        return None


def _snapshot_preview_box_style_snapshot(
    snapshot: dict[str, Any] | None,
) -> SignatureBoxStyle | None:
    if snapshot is None:
        return None
    box_style = snapshot.get("box_style")
    if not isinstance(box_style, dict):
        return None
    try:
        return SignatureBoxStyle(
            show_border=bool(box_style.get("show_border")),
            border_color_hex=str(box_style.get("border_color_hex") or "#000000"),
            border_width_pt=float(box_style.get("border_width_pt") or 0.5),
            background_color_hex=str(box_style.get("background_color_hex") or "#FFFFFF"),
        )
    except Exception:
        return None


def _layout_template_from_snapshot(
    layout_template: str | None,
) -> SignatureLayoutTemplate | None:
    if layout_template is None:
        return None
    try:
        return SignatureLayoutTemplate(layout_template)
    except ValueError:
        return None


def _layout_spacing(widget: Any) -> int | None:
    layout = getattr(widget, "layout", None)
    layout = layout() if callable(layout) else layout
    if layout is None:
        return None
    spacing = getattr(layout, "spacing", None)
    if callable(spacing):
        return int(spacing())
    if isinstance(spacing, int):
        return spacing
    return getattr(layout, "spacing", None)


def _widget_application(widget: Any) -> Any | None:
    app_getter = getattr(type(widget), "window", None)
    _ = app_getter  # keep linter quiet for fake widgets that lack QApplication access.
    try:
        app_module = importlib.import_module("PySide6.QtWidgets")
    except ModuleNotFoundError:
        return None
    q_application = getattr(app_module, "QApplication", None)
    if q_application is None:
        return None
    instance = getattr(q_application, "instance", None)
    return instance() if callable(instance) else None


def _scenario_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "scenario"


def _snapshot_preview_capture_image(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    render_capture = snapshot.get("render_capture")
    if not isinstance(render_capture, dict):
        return None
    image_path = render_capture.get("preview_image_path")
    return str(image_path) if image_path is not None else None


def _snapshot_preview_analysis_image(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    render_capture = snapshot.get("render_capture")
    if not isinstance(render_capture, dict):
        return None
    image_path = render_capture.get("analysis_preview_image_path")
    if image_path is None:
        image_path = render_capture.get("preview_image_path")
    return str(image_path) if image_path is not None else None


def _snapshot_preview_card_bounds(snapshot: dict[str, Any] | None) -> dict[str, int] | None:
    if snapshot is None:
        return None
    render_capture = snapshot.get("render_capture")
    if not isinstance(render_capture, dict):
        return None
    analysis_snapshot = _mapping(render_capture.get("analysis_appearance_snapshot"))
    analysis_bounds = _mapping_int_bounds(analysis_snapshot.get("container_bounds_px"))
    if analysis_bounds is not None:
        return analysis_bounds
    analysis_size = _mapping(analysis_snapshot.get("image_size_px"))
    analysis_width = analysis_size.get("width")
    analysis_height = analysis_size.get("height")
    if isinstance(analysis_width, int) and isinstance(analysis_height, int):
        return {"x": 0, "y": 0, "width": analysis_width, "height": analysis_height}
    bounds = render_capture.get("card_bounds_px")
    return _mapping_int_bounds(bounds)


def _snapshot_visible_appearance_text_fragments(snapshot: dict[str, Any] | None) -> list[str]:
    return _project_visible_fragments(snapshot)


def _parse_snapshot_rect(snapshot_rect: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(snapshot_rect, list) or len(snapshot_rect) != 4:
        return None
    try:
        return tuple(float(value) for value in snapshot_rect)  # type: ignore[return-value]
    except (TypeError, ValueError):
        return None


def _mapping_int_bounds(value: Any) -> dict[str, int] | None:
    if not isinstance(value, dict):
        return None
    x = value.get("x")
    y = value.get("y")
    width = value.get("width")
    height = value.get("height")
    if not all(isinstance(item, int) for item in (x, y, width, height)):
        return None
    return {"x": int(x), "y": int(y), "width": int(width), "height": int(height)}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _snapshot_preview_edge_distance(snapshot: dict[str, Any] | None, key: str) -> int | None:
    value = _project_preview_edge_distance(snapshot, key)
    return None if value is None else int(value)


def _snapshot_bool_text(snapshot: dict[str, Any] | None, key: str) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get(key)
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "not captured"


def _snapshot_number_text(snapshot: dict[str, Any] | None, key: str) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get(key)
    if isinstance(value, (int, float)):
        return str(value)
    return "not captured"


def _snapshot_text_value(snapshot: dict[str, Any] | None, key: str) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get(key)
    if value is None:
        return "none"
    return str(value)


def _snapshot_timestamp_trust_policy(
    trust_policy: TimestampTrustPolicy | None,
) -> dict[str, Any] | None:
    if trust_policy is None:
        return None
    return {
        "use_system_store": trust_policy.use_system_store,
        "extra_ca_bundle_path": trust_policy.extra_ca_bundle_path,
        "revocation_mode": trust_policy.revocation_mode,
    }


def _snapshot_signing_request(request: SigningRequest | None) -> dict[str, Any] | None:
    if request is None:
        return None
    appearance = request.signature_appearance
    return {
        "input_pdf_path": request.input_pdf_path,
        "output_pdf_path": request.output_pdf_path,
        "certificate_path": request.certificate_path,
        "certificate_alias": request.certificate_alias,
        "timestamp_required": request.timestamp_required,
        "tsa_url": request.tsa_url,
        "trust_policy": _snapshot_timestamp_trust_policy(request.trust_policy),
        "signature_rect": _snapshot_signature_rect(request.signature_rect),
        "signature_appearance": (
            None if appearance is None else _snapshot_signing_appearance(appearance)
        ),
    }


def _snapshot_layout_rule(layout_rule) -> dict[str, Any] | None:
    if layout_rule is None:
        return None
    x_align = getattr(layout_rule, "x_align")
    y_align = getattr(layout_rule, "y_align")
    scaling = getattr(
        layout_rule,
        "inner_content_scaling",
        getattr(layout_rule, "scaling", None),
    )
    margins = getattr(layout_rule, "margins")
    return {
        "x_align": _layout_value_name(x_align),
        "y_align": _layout_value_name(y_align),
        "inner_content_scaling": _layout_value_name(scaling),
        "margins": {
            "left": margins.left,
            "right": margins.right,
            "top": margins.top,
            "bottom": margins.bottom,
        },
    }


def _layout_value_name(value: Any) -> str:
    name = getattr(value, "name", value)
    return str(name).lower()


def _snapshot_signing_appearance(appearance) -> dict[str, Any]:
    return {
        "signer_label_prefix": appearance.signer_label_prefix,
        "layout_template": appearance.layout_template.value,
        "stamp_position": appearance.stamp_position.value,
        "timezone_display_mode": appearance.timezone_display_mode.value,
        "show_field_names": appearance.show_field_names,
        "datetime_format": appearance.datetime_format,
        "field_order": [field_key.value for field_key in appearance.field_order],
        "text_style": _snapshot_text_style(appearance.text_style),
        "box_style": _snapshot_box_style(appearance.box_style),
        "image_stamp_path": appearance.image_stamp_path,
        "fields": [
            _snapshot_field_binding(field_key, binding)
            for field_key, binding in appearance.iter_field_bindings()
        ],
    }


def _snapshot_field_binding(field_key, binding) -> dict[str, Any]:
    return {
        "field_key": field_key.value,
        "label": field_key.value,
        "source": binding.source.value,
        "show_in_visible_appearance": binding.show_in_visible_appearance,
        "override_text": binding.override_text,
        "display_label": binding.display_label,
    }


def _snapshot_preview_field(field) -> dict[str, Any]:
    return {
        "field_key": field.field_key.value,
        "label": field.label,
        "text": field.text,
        "visible": field.visible,
        "source": field.source.value,
        "hint": field.hint,
    }


def _snapshot_text_style(text_style) -> dict[str, Any] | None:
    if text_style is None:
        return None
    return {
        "font_family": text_style.font_family,
        "font_size_pt": text_style.font_size_pt,
        "bold": text_style.bold,
        "italic": text_style.italic,
        "text_color_hex": text_style.text_color_hex,
    }


def _snapshot_box_style(box_style) -> dict[str, Any] | None:
    if box_style is None:
        return None
    return {
        "show_border": box_style.show_border,
        "border_color_hex": box_style.border_color_hex,
        "border_width_pt": box_style.border_width_pt,
        "background_color_hex": box_style.background_color_hex,
    }


def _snapshot_signature_rect(signature_rect) -> dict[str, Any] | None:
    if signature_rect is None:
        return None
    return {
        "page_index": signature_rect.page_index,
        "page_number": signature_rect.page_index + 1,
        "left_pt": signature_rect.left_pt,
        "bottom_pt": signature_rect.bottom_pt,
        "width_pt": signature_rect.width_pt,
        "height_pt": signature_rect.height_pt,
    }


def _snapshot_issue(issue) -> dict[str, Any]:
    return {
        "code": issue.code,
        "message": issue.message,
        "field_name": issue.field_name,
        "severity": issue.severity.value,
    }


def _snapshot_sign_request_appearance(
    snapshot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    projected = _project_sign_request_appearance(snapshot)
    return None if projected is None else dict(projected)


def _snapshot_request_origin(capture: InteractiveHarnessCapture) -> str:
    if capture.sign_request_snapshot is None:
        return "not captured"
    if capture.sign_request_count > 0:
        return "submitted request"
    return "current draft"


def _snapshot_layout_template(snapshot: dict[str, Any] | None) -> str | None:
    return _project_layout_template(snapshot)


def _snapshot_stamp_position(snapshot: dict[str, Any] | None) -> str | None:
    return _project_stamp_position(snapshot)


def _snapshot_show_field_names(snapshot: dict[str, Any] | None) -> bool:
    return _project_show_field_names(snapshot)


def _snapshot_request_field_count(snapshot: dict[str, Any] | None) -> int:
    return _project_request_field_count(snapshot)


def _snapshot_reservation_text_length(snapshot: dict[str, Any] | None) -> int:
    return _project_reservation_text_length(snapshot)


def _snapshot_reservation_stamp_background(snapshot: dict[str, Any] | None) -> bool:
    return _project_reservation_stamp_background(snapshot)


def _snapshot_reservation_stamp_background_text(snapshot: dict[str, Any] | None) -> str:
    return "yes" if _snapshot_reservation_stamp_background(snapshot) else "no"


def _snapshot_layout_scaling(snapshot: dict[str, Any] | None, key: str) -> str | None:
    return _project_layout_scaling(snapshot, key)


def _snapshot_reservation_margin_bottom(snapshot: dict[str, Any] | None) -> int | None:
    value = _project_reservation_margin_bottom(snapshot)
    return None if value is None else int(value)


def _snapshot_preview_show_field_names(snapshot: dict[str, Any] | None) -> bool:
    if snapshot is None:
        return False
    return bool(snapshot.get("show_field_names"))


def _snapshot_preview_stamp_position(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    stamp_position = snapshot.get("stamp_position")
    return stamp_position if isinstance(stamp_position, str) else None


def _snapshot_visible_appearance_field_name(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_field_name(snapshot)


def _snapshot_visible_appearance_annotation_rect(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_annotation_rect(snapshot)


def _snapshot_visible_appearance_bbox(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_bbox(snapshot)


def _snapshot_visible_appearance_stream_length(snapshot: dict[str, Any] | None) -> int:
    return _project_visible_stream_length(snapshot)


def _snapshot_visible_appearance_has_text(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_has_text(snapshot)


def _snapshot_visible_appearance_text_fragments_summary(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_fragments_summary(snapshot)


def _snapshot_visible_appearance_image_xobjects(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_xobjects(snapshot)


def _snapshot_visible_appearance_error(snapshot: dict[str, Any] | None) -> str:
    return _project_visible_error(snapshot)
