"""Interactive Qt harness for Phase 3 signing-shell acceptance."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import shutil
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any

from PIL import Image, ImageDraw
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter
from pyhanko.sign import validation
from pyhanko_certvalidator import ValidationContext

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.coordinate_transform import (
    PageBox,
    PdfRect,
    ViewTransform,
    pdf_rect_to_view_rect,
)
from foliaseal.application.phase3_signing_backend import (
    _background_layout_for_stamp,
    _build_stamp_style,
    _build_stamp_text,
    _build_text_box_style,
    _current_signing_time,
    _effective_layout_edge_margin,
    _ensure_layout_can_fit,
    _layout_reservation_for_template,
    _load_simple_signer,
    _measure_text_box_dimensions,
    _single_line_vertical_outer_margin,
    _stamp_background_for_path,
    _stamp_image_aspect_ratio,
    build_phase3_signing_executor,
)
from foliaseal.application.qa_evidence_contract import evaluate_phase3_evidence_contract
from foliaseal.application.qa_preview_stress_fixtures import (
    apply_preview_stress_fixture_profile,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signature_font_registry import preview_font_family_supported
from foliaseal.application.signing_preview_renderer import (
    SignatureAppearanceSnapshot,
    _layout_rule_bounds_px,
    _structural_line_bounds_px,
    compare_signature_appearance_snapshots,
    render_canonical_signature_preview,
)
from foliaseal.application.text_raster_analysis import (
    detect_text_content_bounds_in_image,
    detect_text_line_bounds_in_image,
)
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureBoxStyle,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
    SigningRequest,
    SigningResult,
    TimestampTrustPolicy,
)
from foliaseal.infra.certification import inspect_pdf_certification_reader
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.render import RenderPageRequest
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend
from foliaseal.infra.tsa import build_dummy_timestamper, build_timestamp_validation_context
from foliaseal.presentation.qt.signing_shell import build_qt_signing_shell

DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH = "artifacts/phase3_fr3b_acceptance_checklist.md"
DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH = "artifacts/phase3_fr3b_acceptance_results.md"
# Matrix reliability matters more than shell reuse speed. A fresh shell per scenario
# keeps the canonical preview sweep from accumulating Qt state across hundreds of runs.
_PREVIEW_MATRIX_SHELL_RECYCLE_INTERVAL = 1


@dataclass(frozen=True)
class Phase3HarnessCapture:
    """Structured capture emitted by the interactive Phase 3 harness."""

    pdf_path: str
    summary_json_path: str | None
    summary_json_written: bool
    checklist_results_path: str
    checklist_results_written: bool
    first_render_ms: float | None
    selection_count: int
    sign_request_count: int
    last_signature_page_index: int | None
    last_signature_page_number: int | None
    last_signature_has_visible_appearance: bool
    last_signature_output_path: str | None
    last_signing_result_message: str | None
    last_signing_result_success: bool | None
    preview_snapshot: dict[str, Any]
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    backend_reservation_error: str | None
    output_file_exists: bool
    output_file_size_bytes: int | None
    output_signature_count: int | None
    output_signature_snapshot: dict[str, Any] | None
    output_visible_appearance_snapshot: dict[str, Any] | None
    preview_available: bool
    preview_text: str
    validation_text: str
    evidence_contract_version: str
    acceptance_tier: str
    gate_verdict: str
    evidence_validation_passed: bool
    evidence_validation_errors: tuple[str, ...]
    evidence_validation_warnings: tuple[str, ...]
    interaction_counts: dict[str, int]
    errors: tuple[str, ...]
    output_verification_snapshot: dict[str, Any] | None = None
    signed_output_render_snapshot: dict[str, Any] | None = None
    signed_output_preview_comparison: dict[str, Any] | None = None
    signed_runs: tuple[dict[str, Any], ...] = ()
    captured_states: tuple[dict[str, Any], ...] = ()
    captured_state_transition_diagnostics: tuple[dict[str, Any], ...] = ()

    def to_json(self) -> str:
        """Return a stable JSON representation for later review."""

        return json.dumps(_jsonable_capture(self), indent=2, sort_keys=True)


def build_phase3_checklist_results_markdown(
    capture: Phase3HarnessCapture,
    *,
    checklist_template_path: str = DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
) -> str:
    """Render a run-specific Phase 3 checklist seeded from the immutable template."""

    template = Path(checklist_template_path).read_text(encoding="utf-8")
    auto_checked_items = _derive_phase3_auto_checked_items(capture)
    visible_appearance_snapshot = capture.output_visible_appearance_snapshot
    preview_content_top_distance = _snapshot_preview_edge_distance(
        capture.preview_snapshot, "content_top_to_border_px"
    )
    preview_content_bottom_distance = _snapshot_preview_edge_distance(
        capture.preview_snapshot, "content_bottom_to_border_px"
    )
    checkbox_pattern = re.compile(r"^(\s*-\s*)\[(?: |x|X)\](\s+)(.+)$")

    rendered_lines = [
        "# Phase 3 FR-3B Acceptance Results",
        "",
        f"Source checklist: `{checklist_template_path}`",
        f"Captured PDF: `{capture.pdf_path}`",
        (
            f"Capture JSON path: `{capture.summary_json_path}`"
            if capture.summary_json_path
            else "Capture JSON path: not written"
        ),
        f"Results markdown path: `{capture.checklist_results_path}`",
        "",
        "This file was generated by `foliaseal phase3-signing-harness`.",
        "Review the pre-checked items, complete the remaining manual-only checks, and keep",
        "notes in this file so Phase 3 acceptance can be reviewed from one artifact.",
        "",
        "## Gate status",
        "",
        f"- Acceptance tier: `{capture.acceptance_tier}`",
        f"- Automated gate verdict: `{capture.gate_verdict}`",
        f"- Evidence contract version: `{capture.evidence_contract_version}`",
        (
            f"- Evidence validation passed: {'yes' if capture.evidence_validation_passed else 'no'}"
        ),
        f"- Summary JSON written: {'yes' if capture.summary_json_written else 'no'}",
        f"- Checklist results written: {'yes' if capture.checklist_results_written else 'no'}",
        (
            "- Evidence validation errors: none"
            if not capture.evidence_validation_errors
            else f"- Evidence validation errors: {list(capture.evidence_validation_errors)}"
        ),
        (
            "- Evidence validation warnings: none"
            if not capture.evidence_validation_warnings
            else f"- Evidence validation warnings: {list(capture.evidence_validation_warnings)}"
        ),
        (
            "- Release-gating pass still requires a completed FR-3B worksheet "
            "and explicit human judgment."
        ),
        "",
        "## Automated capture summary",
        "",
        f"- First render recorded: {'yes' if capture.first_render_ms is not None else 'no'}",
        f"- Preview available: {'yes' if capture.preview_available else 'no'}",
        f"- Selection interactions captured: {capture.selection_count}",
        f"- Sign requests captured: {capture.sign_request_count}",
        f"- Request snapshot origin: {_snapshot_request_origin(capture)}",
        (
            f"- Last signature page number: {capture.last_signature_page_number}"
            if capture.last_signature_page_number is not None
            else "- Last signature page number: not captured"
        ),
        (
            "- Last sign request had visible appearance: "
            f"{'yes' if capture.last_signature_has_visible_appearance else 'no'}"
        ),
        (
            f"- Last sign request output path: `{capture.last_signature_output_path}`"
            if capture.last_signature_output_path is not None
            else "- Last sign request output path: not captured"
        ),
        (
            f"- Last request layout template: "
            f"{_snapshot_layout_template(capture.sign_request_snapshot)}"
            if capture.sign_request_snapshot is not None
            else "- Last request layout template: not captured"
        ),
        (
            f"- Last request stamp position: "
            f"{_snapshot_stamp_position(capture.sign_request_snapshot)}"
            if capture.sign_request_snapshot is not None
            else "- Last request stamp position: not captured"
        ),
        (
            f"- Last request show field names: "
            f"{'yes' if _snapshot_show_field_names(capture.sign_request_snapshot) else 'no'}"
            if capture.sign_request_snapshot is not None
            else "- Last request show field names: not captured"
        ),
        (
            f"- Last request field snapshot count: "
            f"{_snapshot_request_field_count(capture.sign_request_snapshot)}"
            if capture.sign_request_snapshot is not None
            else "- Last request field snapshot count: not captured"
        ),
        (
            f"- Backend reservation layout template: "
            f"{_snapshot_layout_template(capture.backend_reservation_snapshot)}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation layout template: not captured"
        ),
        (
            f"- Backend reservation stamp position: "
            f"{_snapshot_stamp_position(capture.backend_reservation_snapshot)}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation stamp position: not captured"
        ),
        (
            f"- Backend reservation stamp text length: "
            f"{_snapshot_reservation_text_length(capture.backend_reservation_snapshot)}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation stamp text length: not captured"
        ),
        (
            f"- Backend reservation stamp background: "
            f"{_snapshot_reservation_stamp_background_text(capture.backend_reservation_snapshot)}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation stamp background: not captured"
        ),
        (
            f"- Backend reservation background scaling: "
            f"{_snapshot_layout_scaling(capture.backend_reservation_snapshot, 'background')}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation background scaling: not captured"
        ),
        (
            f"- Backend reservation content scaling: "
            f"{_snapshot_layout_scaling(capture.backend_reservation_snapshot, 'content')}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation content scaling: not captured"
        ),
        (
            f"- Backend reservation content bottom margin: "
            f"{_snapshot_reservation_margin_bottom(capture.backend_reservation_snapshot)}"
            if capture.backend_reservation_snapshot is not None
            else "- Backend reservation content bottom margin: not captured"
        ),
        (
            f"- Backend reservation error: `{capture.backend_reservation_error}`"
            if capture.backend_reservation_error
            else "- Backend reservation error: none"
        ),
        (
            f"- Preview layout template: {capture.preview_snapshot['layout_template']}"
            if capture.preview_snapshot
            else "- Preview layout template: not captured"
        ),
        (
            f"- Preview stamp position: "
            f"{_snapshot_preview_stamp_position(capture.preview_snapshot)}"
            if capture.preview_snapshot
            else "- Preview stamp position: not captured"
        ),
        (
            f"- Preview show field names: "
            f"{'yes' if _snapshot_preview_show_field_names(capture.preview_snapshot) else 'no'}"
            if capture.preview_snapshot
            else "- Preview show field names: not captured"
        ),
        (
            f"- Preview field count: {len(capture.preview_snapshot['fields'])}"
            if capture.preview_snapshot
            else "- Preview field count: not captured"
        ),
        (
            f"- Preview capture image: "
            f"`{_snapshot_preview_capture_image(capture.preview_snapshot)}`"
            if _snapshot_preview_capture_image(capture.preview_snapshot) is not None
            else "- Preview capture image: not captured"
        ),
        (
            f"- Preview content top distance: "
            f"{preview_content_top_distance}"
            " px"
            if preview_content_top_distance is not None
            else "- Preview content top distance: not captured"
        ),
        (
            f"- Preview content bottom distance: "
            f"{preview_content_bottom_distance}"
            " px"
            if preview_content_bottom_distance is not None
            else "- Preview content bottom distance: not captured"
        ),
        (
            "- Last signing result: "
            f"{'success' if capture.last_signing_result_success else 'failure'}"
            if capture.last_signing_result_success is not None
            else "- Last signing result: not captured"
        ),
        (
            f"- Last signing message: `{capture.last_signing_result_message}`"
            if capture.last_signing_result_message
            else "- Last signing message: not captured"
        ),
        f"- Output file exists: {'yes' if capture.output_file_exists else 'no'}",
        (
            f"- Output file size: {capture.output_file_size_bytes} bytes"
            if capture.output_file_size_bytes is not None
            else "- Output file size: not captured"
        ),
        (
            f"- Output embedded signature count: {capture.output_signature_count}"
            if capture.output_signature_count is not None
            else "- Output embedded signature count: not captured"
        ),
        (
            f"- Output signature field name: {capture.output_signature_snapshot['field_name']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("field_name") is not None
            else "- Output signature field name: not captured"
        ),
        (
            f"- Output signature name: {capture.output_signature_snapshot['name']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("name") is not None
            else "- Output signature name: not captured"
        ),
        (
            f"- Output signature location: {capture.output_signature_snapshot['location']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("location") is not None
            else "- Output signature location: not captured"
        ),
        (
            f"- Output signature contact info: {capture.output_signature_snapshot['contact_info']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("contact_info") is not None
            else "- Output signature contact info: not captured"
        ),
        (
            f"- Output signature byte range: {capture.output_signature_snapshot['byte_range']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("byte_range") is not None
            else "- Output signature byte range: not captured"
        ),
        (
            f"- Output signature subfilter: {capture.output_signature_snapshot['subfilter']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("subfilter") is not None
            else "- Output signature subfilter: not captured"
        ),
        (
            f"- Output signature md algorithm: {capture.output_signature_snapshot['md_algorithm']}"
            if capture.output_signature_snapshot
            and capture.output_signature_snapshot.get("md_algorithm") is not None
            else "- Output signature md algorithm: not captured"
        ),
        (
            f"- Output visible appearance field name: "
            f"{_snapshot_visible_appearance_field_name(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance field name: not captured"
        ),
        (
            f"- Output visible appearance annotation rect: "
            f"{_snapshot_visible_appearance_annotation_rect(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance annotation rect: not captured"
        ),
        (
            f"- Output visible appearance bbox: "
            f"{_snapshot_visible_appearance_bbox(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance bbox: not captured"
        ),
        (
            f"- Output visible appearance stream length: "
            f"{_snapshot_visible_appearance_stream_length(visible_appearance_snapshot)} bytes"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance stream length: not captured"
        ),
        (
            f"- Output visible appearance has visible text: "
            f"{_snapshot_visible_appearance_has_text(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance has visible text: not captured"
        ),
        (
            f"- Output visible appearance text fragments: "
            f"{_snapshot_visible_appearance_text_fragments_summary(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance text fragments: not captured"
        ),
        (
            f"- Output visible appearance image XObjects: "
            f"{_snapshot_visible_appearance_image_xobjects(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance image XObjects: not captured"
        ),
        (
            f"- Output visible appearance error: "
            f"{_snapshot_visible_appearance_error(visible_appearance_snapshot)}"
            if visible_appearance_snapshot is not None
            else "- Output visible appearance error: not captured"
        ),
        (
            f"- Signed output page render: "
            f"`{capture.signed_output_render_snapshot['page_render_path']}`"
            if capture.signed_output_render_snapshot
            and capture.signed_output_render_snapshot.get("page_render_path") is not None
            else "- Signed output page render: not captured"
        ),
        (
            f"- Signed output signature crop: "
            f"`{capture.signed_output_render_snapshot['signature_crop_path']}`"
            if capture.signed_output_render_snapshot
            and capture.signed_output_render_snapshot.get("signature_crop_path") is not None
            else "- Signed output signature crop: not captured"
        ),
        (
            f"- Signed output preview comparison: "
            f"`{capture.signed_output_render_snapshot['comparison_path']}`"
            if capture.signed_output_render_snapshot
            and capture.signed_output_render_snapshot.get("comparison_path") is not None
            else "- Signed output preview comparison: not captured"
        ),
        (
            "- Signed output preview comparison passed: "
            + _snapshot_bool_text(
                capture.signed_output_preview_comparison,
                "preview_vs_signed_output_passed",
            )
            if capture.signed_output_preview_comparison is not None
            else "- Signed output preview comparison passed: not captured"
        ),
        (
            "- Signed output preview comparison change ratio: "
            + _snapshot_number_text(
                capture.signed_output_preview_comparison,
                "preview_vs_signed_output_change_ratio",
            )
            if capture.signed_output_preview_comparison is not None
            else "- Signed output preview comparison change ratio: not captured"
        ),
        (
            "- Signed output preview comparison text match: "
            + _snapshot_bool_text(
                capture.signed_output_preview_comparison,
                "preview_text_fragments_match_output",
            )
            if capture.signed_output_preview_comparison is not None
            else "- Signed output preview comparison text match: not captured"
        ),
        (
            "- Signed output preview comparison error: "
            + _snapshot_text_value(
                capture.signed_output_preview_comparison,
                "preview_vs_signed_output_error",
            )
            if capture.signed_output_preview_comparison is not None
            else "- Signed output preview comparison error: not captured"
        ),
        f"- Current validation text: `{capture.validation_text or 'n/a'}`",
        "",
    ]
    for raw_line in template.splitlines():
        match = checkbox_pattern.match(raw_line)
        if not match:
            rendered_lines.append(raw_line)
            continue
        prefix, spacing, item_text = match.groups()
        marker = "x" if item_text.strip() in auto_checked_items else " "
        rendered_lines.append(f"{prefix}[{marker}]{spacing}{item_text}")
    return "\n".join(rendered_lines) + "\n"


def run_phase3_signing_harness(
    *,
    pdf_path: str,
    certificate_path: str = "demo-cert.p12",
    passphrase: str = "demo-passphrase",
    summary_json_path: str | None = None,
    checklist_results_path: str = DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
    checklist_template_path: str = DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
    artifacts_dir: str | None = None,
) -> Phase3HarnessCapture:
    """Launch an interactive Qt signing-shell harness for Phase 3 acceptance."""

    bindings = _load_qt_harness_bindings()
    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PDF does not exist: {pdf_path}")
    artifacts_dir = _default_harness_artifacts_dir(
        summary_json_path=summary_json_path,
        artifacts_dir=artifacts_dir,
    )

    page_count = _load_page_count(bindings=bindings, pdf_path=str(source_path))
    backend = QtPdfRenderBackend()
    diagnostic = backend.diagnostics()
    if not diagnostic.available:
        raise RuntimeError(diagnostic.message)

    viewer_workflow = ViewerWorkflow(
        document_path=str(source_path),
        render_backend=backend,
        session=ViewerSession(page_count=page_count),
    )
    signing_workflow = SigningDraftWorkflow(
        input_pdf_path=str(source_path),
        output_pdf_path=_default_harness_output_pdf_path(
            pdf_path=str(source_path),
            artifacts_dir=artifacts_dir,
            sign_attempt_index=1,
        ),
        certificate_path=certificate_path,
        passphrase=passphrase,
        tsa_url="https://tsa.example.invalid",
        timestamp_required=False,
    )
    profile_store = SignaturePresetCatalogStore.default()
    sign_executor = build_phase3_signing_executor()

    sign_requests: list[SigningRequest] = []
    signed_runs: list[dict[str, Any]] = []
    errors: list[str] = []
    interaction_counts: Counter[str] = Counter()

    app = bindings.q_application.instance() or bindings.q_application([])
    window = bindings.q_main_window()
    window.setWindowTitle(f"FoliaSeal Phase 3 Harness - {source_path.name}")
    window.resize(1440, 980)

    central = bindings.q_widget()
    layout = bindings.q_v_box_layout(central)
    toolbar = bindings.q_h_box_layout()
    layout.addLayout(toolbar)
    body_layout = bindings.q_h_box_layout()
    layout.addLayout(body_layout, 1)

    window.setCentralWidget(central)

    def refocus_shell() -> None:
        focus_setter = getattr(shell, "setFocus", None)
        if callable(focus_setter):
            focus_setter()

    captured_states: list[dict[str, Any]] = []

    def on_sign_request(request: SigningRequest) -> None:
        sign_requests.append(request)
        signing_workflow.output_pdf_path = _default_harness_output_pdf_path(
            pdf_path=str(source_path),
            artifacts_dir=artifacts_dir,
            sign_attempt_index=len(sign_requests) + 1,
        )

    def on_error(message: str) -> None:
        errors.append(message)

    def on_status_change(name: str) -> None:
        interaction_counts[name] += 1
        if name != "sign_success" or not sign_requests:
            return
        signing_result = getattr(shell, "last_signing_result", None)
        if not isinstance(signing_result, SigningResult) or not signing_result.success:
            return
        request = sign_requests[-1]
        run_index = len(signed_runs) + 1
        sign_time_state = _capture_interactive_state(
            shell=shell,
            request=request,
            artifacts_dir=artifacts_dir,
            artifact_basename=(
                f"signed_run_{run_index:02d}_preview" if artifacts_dir is not None else None
            ),
            capture_index=run_index,
            capture_kind="signed_run",
        )
        signed_runs.append(
            _build_signed_run_bundle(
                run_index=run_index,
                sign_time_state=sign_time_state,
                request=request,
                signing_result=signing_result,
                artifacts_dir=artifacts_dir,
                artifact_basename=(
                    f"signed_run_{run_index:02d}_signed_output"
                    if artifacts_dir is not None
                    else None
                ),
            )
        )

    shell = build_qt_signing_shell(
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        preset_catalog_store=profile_store,
        sign_executor=sign_executor,
        on_sign_request=on_sign_request,
        on_error=on_error,
        on_status_change=on_status_change,
    )
    body_layout.addWidget(shell, 1)

    def do_refresh() -> None:
        shell.refresh_viewer()
        refocus_shell()

    def navigate(action_name: str) -> None:
        action = getattr(shell.viewer_widget, action_name)
        action()
        refocus_shell()

    controls = [
        ("Refresh", do_refresh),
        ("Prev Page", lambda: navigate("go_to_previous_page")),
        ("Next Page", lambda: navigate("go_to_next_page")),
        ("Reset Zoom", lambda: navigate("reset_zoom_view")),
    ]
    for label, callback in controls:
        button = bindings.q_push_button(label)
        button.clicked.connect(callback)
        toolbar.addWidget(button)

    capture_count_label = bindings.q_label("Captured states: 0")

    def capture_current_state(
        *,
        capture_kind: str,
        request: SigningRequest | None = None,
    ) -> dict[str, Any]:
        current_request = request
        if current_request is None:
            current_request = _snapshot_current_draft_request(shell.properties_panel._workflow)
        capture_index = (
            len(captured_states) + 1
            if capture_kind == "manual"
            else len(captured_states)
        )
        artifact_basename = None
        if artifacts_dir is not None:
            artifact_basename = (
                f"interactive_state_{capture_index:02d}"
                if capture_kind == "manual"
                else "interactive_final"
            )
        return _capture_interactive_state(
            shell=shell,
            request=current_request,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
            capture_index=(capture_index if capture_kind == "manual" else len(captured_states) + 1),
            capture_kind=capture_kind,
        )

    def update_capture_count_label() -> None:
        capture_count_label.setText(f"Captured states: {len(captured_states)}")

    def on_capture_state() -> None:
        captured_states.append(capture_current_state(capture_kind="manual"))
        update_capture_count_label()
        refocus_shell()

    capture_button = bindings.q_push_button("Capture State")
    capture_button.clicked.connect(on_capture_state)
    toolbar.addWidget(capture_button)

    confirm_button = bindings.q_push_button("Confirm/Sign")
    confirm_button.clicked.connect(shell.submit_sign_request)
    toolbar.addWidget(confirm_button)

    toolbar.addStretch(1)
    toolbar.addWidget(capture_count_label)

    start = perf_counter()
    shell.refresh_viewer()
    _elapsed_ms = (perf_counter() - start) * 1000.0

    window.show()
    refocus_shell()
    app.exec()

    capture_request = (
        sign_requests[-1]
        if sign_requests
        else _snapshot_current_draft_request(shell.properties_panel._workflow)
    )
    final_state = capture_current_state(capture_kind="final", request=capture_request)
    preview_text = final_state["preview_text"]
    validation_text = final_state["validation_text"]
    last_signing_result = getattr(shell, "last_signing_result", None)
    backend_reservation_snapshot = final_state["backend_reservation_snapshot"]
    backend_reservation_error = final_state["backend_reservation_error"]
    last_signature_page_index = (
        sign_requests[-1].signature_rect.page_index
        if sign_requests and sign_requests[-1].signature_rect is not None
        else None
    )
    output_path = sign_requests[-1].output_pdf_path if sign_requests else None
    output_exists = False
    output_size_bytes = None
    output_signature_count = None
    output_signature_snapshot = None
    output_verification_snapshot = None
    output_visible_appearance_snapshot = None
    signed_output_render_snapshot = None
    if signed_runs:
        latest_signed_run = _mapping(signed_runs[-1])
        output_path = latest_signed_run.get("output_pdf_path")
        output_exists = bool(latest_signed_run.get("output_file_exists"))
        output_size_bytes = latest_signed_run.get("output_file_size_bytes")
        output_signature_count = latest_signed_run.get("output_signature_count")
        output_signature_snapshot = latest_signed_run.get("output_signature_snapshot")
        output_verification_snapshot = latest_signed_run.get("output_verification_snapshot")
        output_visible_appearance_snapshot = latest_signed_run.get(
            "output_visible_appearance_snapshot"
        )
        signed_output_render_snapshot = latest_signed_run.get("signed_output_render_snapshot")
    elif output_path is not None:
        output_file = Path(output_path)
        output_exists = output_file.exists()
        if output_exists:
            output_size_bytes = output_file.stat().st_size
            output_signature_count = _count_embedded_signatures(output_file)
            output_signature_snapshot = _snapshot_output_signature(output_file)
            output_verification_snapshot = _snapshot_output_verification(
                output_file,
                trust_policy=(
                    capture_request.trust_policy
                    if capture_request is not None
                    else None
                ),
            )
            output_visible_appearance_snapshot = _snapshot_visible_signature_appearance(output_file)
            signed_output_render_snapshot = _snapshot_signed_output_render(
                output_pdf_path=str(output_file),
                page_index=last_signature_page_index,
                preview_snapshot=final_state["preview_snapshot"],
                preview_text=preview_text,
                output_visible_appearance_snapshot=output_visible_appearance_snapshot,
                artifacts_dir=artifacts_dir,
                artifact_basename="final_signed_output",
            )
    checklist_results_written = bool(checklist_results_path)
    capture_payload = {
        "pdf_path": str(source_path),
        "summary_json_path": summary_json_path,
        "summary_json_written": summary_json_path is not None,
        "checklist_results_path": checklist_results_path,
        "checklist_results_written": checklist_results_written,
        "first_render_ms": viewer_workflow.timing_tracker.snapshot().first_render_ms,
        "selection_count": interaction_counts.get("selection_success", 0),
        "sign_request_count": len(sign_requests),
        "last_signature_page_index": last_signature_page_index,
        "last_signature_page_number": (
            last_signature_page_index + 1 if last_signature_page_index is not None else None
        ),
        "last_signature_has_visible_appearance": (
            sign_requests[-1].has_visible_signature_settings() if sign_requests else False
        ),
        "last_signature_output_path": output_path,
        "last_signing_result_message": (
            last_signing_result.message if isinstance(last_signing_result, SigningResult) else None
        ),
        "last_signing_result_success": (
            last_signing_result.success if isinstance(last_signing_result, SigningResult) else None
        ),
        "preview_snapshot": final_state["preview_snapshot"],
        "sign_request_snapshot": final_state["sign_request_snapshot"],
        "backend_reservation_snapshot": backend_reservation_snapshot,
        "backend_reservation_error": backend_reservation_error,
        "output_file_exists": output_exists,
        "output_file_size_bytes": output_size_bytes,
        "output_signature_count": output_signature_count,
        "output_signature_snapshot": output_signature_snapshot,
        "output_verification_snapshot": output_verification_snapshot,
        "output_visible_appearance_snapshot": output_visible_appearance_snapshot,
        "signed_output_render_snapshot": signed_output_render_snapshot,
        "signed_output_preview_comparison": (
            None
            if signed_output_render_snapshot is None
            else {
                "page_render_path": signed_output_render_snapshot.get("page_render_path"),
                "signature_crop_path": signed_output_render_snapshot.get(
                    "signature_crop_path"
                ),
                "comparison_path": signed_output_render_snapshot.get("comparison_path"),
                "preview_crop_bounds_px": signed_output_render_snapshot.get(
                    "preview_crop_bounds_px"
                ),
                "signed_crop_bounds_px": signed_output_render_snapshot.get(
                    "signed_crop_bounds_px"
                ),
                "preview_vs_signed_output_change_ratio": signed_output_render_snapshot.get(
                    "preview_vs_signed_output_change_ratio"
                ),
                "preview_vs_signed_output_aspect_ratio_delta": signed_output_render_snapshot.get(
                    "preview_vs_signed_output_aspect_ratio_delta"
                ),
                "preview_text_fragments_match_output": signed_output_render_snapshot.get(
                    "preview_text_fragments_match_output"
                ),
                "annotation_rect_matches_request": signed_output_render_snapshot.get(
                    "annotation_rect_matches_request"
                ),
                "output_text_bounds_match_preview": signed_output_render_snapshot.get(
                    "output_text_bounds_match_preview"
                ),
                "output_image_presence_matches_preview": signed_output_render_snapshot.get(
                    "output_image_presence_matches_preview"
                ),
                "preview_vs_signed_output_passed": signed_output_render_snapshot.get(
                    "preview_vs_signed_output_passed"
                ),
                "preview_vs_signed_output_error": signed_output_render_snapshot.get(
                    "comparison_error"
                )
                or signed_output_render_snapshot.get("signature_crop_error")
                or signed_output_render_snapshot.get("page_render_error"),
            }
        ),
        "preview_available": bool(preview_text.strip()),
        "preview_text": preview_text,
        "validation_text": validation_text,
        "interaction_counts": dict(sorted(interaction_counts.items())),
        "errors": tuple(errors),
        "signed_runs": tuple(signed_runs),
        "captured_states": tuple(captured_states + [final_state]),
    }
    capture_payload["captured_state_transition_diagnostics"] = (
        _analyze_capture_state_transitions(capture_payload["captured_states"])
    )
    contract = evaluate_phase3_evidence_contract(capture_payload)
    capture = Phase3HarnessCapture(
        pdf_path=capture_payload["pdf_path"],
        summary_json_path=summary_json_path,
        summary_json_written=summary_json_path is not None,
        checklist_results_path=checklist_results_path,
        checklist_results_written=checklist_results_written,
        first_render_ms=capture_payload["first_render_ms"],
        selection_count=capture_payload["selection_count"],
        sign_request_count=capture_payload["sign_request_count"],
        last_signature_page_index=capture_payload["last_signature_page_index"],
        last_signature_page_number=capture_payload["last_signature_page_number"],
        last_signature_has_visible_appearance=capture_payload["last_signature_has_visible_appearance"],
        last_signature_output_path=capture_payload["last_signature_output_path"],
        last_signing_result_message=capture_payload["last_signing_result_message"],
        last_signing_result_success=capture_payload["last_signing_result_success"],
        preview_snapshot=capture_payload["preview_snapshot"],
        sign_request_snapshot=capture_payload["sign_request_snapshot"],
        backend_reservation_snapshot=capture_payload["backend_reservation_snapshot"],
        backend_reservation_error=capture_payload["backend_reservation_error"],
        output_file_exists=capture_payload["output_file_exists"],
        output_file_size_bytes=capture_payload["output_file_size_bytes"],
        output_signature_count=capture_payload["output_signature_count"],
        output_signature_snapshot=capture_payload["output_signature_snapshot"],
        output_verification_snapshot=capture_payload["output_verification_snapshot"],
        output_visible_appearance_snapshot=capture_payload["output_visible_appearance_snapshot"],
        signed_output_render_snapshot=capture_payload["signed_output_render_snapshot"],
        signed_output_preview_comparison=capture_payload["signed_output_preview_comparison"],
        signed_runs=capture_payload["signed_runs"],
        preview_available=capture_payload["preview_available"],
        preview_text=capture_payload["preview_text"],
        validation_text=capture_payload["validation_text"],
        evidence_contract_version=contract.contract_version,
        acceptance_tier=contract.acceptance_tier,
        gate_verdict=contract.gate_verdict,
        evidence_validation_passed=contract.passed,
        evidence_validation_errors=contract.errors,
        evidence_validation_warnings=contract.warnings,
        interaction_counts=capture_payload["interaction_counts"],
        errors=capture_payload["errors"],
        captured_states=capture_payload["captured_states"],
        captured_state_transition_diagnostics=capture_payload[
            "captured_state_transition_diagnostics"
        ],
    )
    _write_optional_text(target_path=summary_json_path, content=capture.to_json() + "\n")
    checklist_results = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=checklist_template_path,
    )
    _write_optional_text(target_path=checklist_results_path, content=checklist_results)
    if summary_json_path is None:
        print("Phase 3 harness capture")
        print(capture.to_json())
        print()
    else:
        print("Phase 3 harness capture written")
        print(f"- summary json: {summary_json_path}")
        print(f"- acceptance tier: {capture.acceptance_tier}")
        print(f"- gate verdict: {capture.gate_verdict}")
        print(f"- validation: {capture.validation_text}")
        print(f"- captured states: {len(capture.captured_states)}")
        print()
    print(f"Checklist results file: {checklist_results_path}")
    print("Review the pre-checked items, complete the remaining manual-only checks, and")
    print("use the generated file as the acceptance worksheet for Phase 3.")
    return capture


def _default_harness_artifacts_dir(
    *,
    summary_json_path: str | None,
    artifacts_dir: str | None,
) -> str | None:
    if artifacts_dir is not None:
        return artifacts_dir
    if summary_json_path is None:
        return None
    summary_path = Path(summary_json_path)
    return str(summary_path.with_name(f"{summary_path.stem}_artifacts"))


def _default_harness_output_pdf_path(
    *,
    pdf_path: str,
    artifacts_dir: str | None,
    sign_attempt_index: int = 1,
) -> str:
    source_path = Path(pdf_path)
    if artifacts_dir is None:
        return str(source_path.with_name(source_path.stem + "-signed.pdf"))
    target_dir = Path(artifacts_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return str(target_dir / f"{source_path.stem}_harness_signed_{sign_attempt_index:03d}.pdf")


def _capture_interactive_state(
    *,
    shell: Any,
    request: SigningRequest | None,
    artifacts_dir: str | None,
    artifact_basename: str | None,
    capture_index: int,
    capture_kind: str,
) -> dict[str, Any]:
    preview = shell.properties_panel.refresh_preview()
    app = _widget_application(shell)
    if app is not None and hasattr(app, "processEvents"):
        app.processEvents()
    preview_text = shell.properties_panel.preview_text()
    validation_text = shell.properties_panel.validation_text()
    render_capture = _capture_preview_render(
        shell=shell,
        preview=preview,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
    )
    backend_reservation_snapshot = (
        _snapshot_backend_reservation(request) if request is not None else None
    )
    sign_time_diagnostics = _snapshot_sign_time_fit_diagnostics(
        preview_render_capture=render_capture,
        backend_reservation_snapshot=backend_reservation_snapshot,
    )
    capture_label = _interactive_capture_label(
        preview=preview,
        capture_index=capture_index,
        capture_kind=capture_kind,
    )
    return {
        "capture_index": capture_index,
        "capture_kind": capture_kind,
        "capture_label": capture_label,
        "preview_snapshot": _snapshot_preview(
            preview,
            render_capture=render_capture,
            sign_time_diagnostics=sign_time_diagnostics,
        ),
        "preview_text": preview_text,
        "validation_text": validation_text,
        "sign_request_snapshot": _snapshot_signing_request(request),
        "backend_reservation_snapshot": backend_reservation_snapshot,
        "backend_reservation_error": _backend_reservation_error(request) if request else None,
    }


def _interactive_capture_label(*, preview, capture_index: int, capture_kind: str) -> str:
    layout_name = preview.layout_template.value if preview.layout_template else "unknown_layout"
    stamp_name = preview.stamp_position.value if preview.stamp_position else "unknown_stamp"
    return f"{capture_kind}_{capture_index:02d}_{layout_name}_{stamp_name}"


def _snapshot_signing_result_payload(signing_result: SigningResult) -> dict[str, Any]:
    return {
        "success": signing_result.success,
        "failure_code": (
            signing_result.failure_code.value
            if getattr(signing_result, "failure_code", None) is not None
            else None
        ),
        "message": signing_result.message,
        "output_pdf_version": signing_result.output_pdf_version,
        "signature_subfilter": signing_result.signature_subfilter,
        "timestamp_present": signing_result.timestamp_present,
        "timestamp_cryptographically_valid": signing_result.timestamp_cryptographically_valid,
        "tsa_chain_trusted": signing_result.tsa_chain_trusted,
        "timestamp_validation_error": signing_result.timestamp_validation_error,
        "docmdp_permission": signing_result.docmdp_permission,
        "certification_restricted": signing_result.certification_restricted,
        "restriction_reason": signing_result.restriction_reason,
        "operation_type": (
            signing_result.operation_type.value
            if getattr(signing_result, "operation_type", None) is not None
            else None
        ),
        "revision_strategy": (
            signing_result.revision_strategy.value
            if getattr(signing_result, "revision_strategy", None) is not None
            else None
        ),
        "standards_summary": signing_result.standards_summary,
    }


def _signed_output_preview_comparison_snapshot(
    signed_output_render_snapshot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if signed_output_render_snapshot is None:
        return None
    return {
        "page_render_path": signed_output_render_snapshot.get("page_render_path"),
        "signature_crop_path": signed_output_render_snapshot.get("signature_crop_path"),
        "normalized_signature_crop_path": signed_output_render_snapshot.get(
            "normalized_signature_crop_path"
        ),
        "comparison_path": signed_output_render_snapshot.get("comparison_path"),
        "preview_crop_bounds_px": signed_output_render_snapshot.get("preview_crop_bounds_px"),
        "signed_crop_bounds_px": signed_output_render_snapshot.get("signed_crop_bounds_px"),
        "preview_vs_signed_output_change_ratio": signed_output_render_snapshot.get(
            "preview_vs_signed_output_change_ratio"
        ),
        "preview_vs_signed_output_aspect_ratio_delta": signed_output_render_snapshot.get(
            "preview_vs_signed_output_aspect_ratio_delta"
        ),
        "preview_text_fragments_match_output": signed_output_render_snapshot.get(
            "preview_text_fragments_match_output"
        ),
        "annotation_rect_matches_request": signed_output_render_snapshot.get(
            "annotation_rect_matches_request"
        ),
        "output_text_bounds_match_preview": signed_output_render_snapshot.get(
            "output_text_bounds_match_preview"
        ),
        "output_image_presence_matches_preview": signed_output_render_snapshot.get(
            "output_image_presence_matches_preview"
        ),
        "preview_vs_signed_output_passed": signed_output_render_snapshot.get(
            "preview_vs_signed_output_passed"
        ),
        "preview_vs_signed_output_error": signed_output_render_snapshot.get("comparison_error")
        or signed_output_render_snapshot.get("signature_crop_error")
        or signed_output_render_snapshot.get("page_render_error"),
        "appearance_layer_comparison": signed_output_render_snapshot.get(
            "appearance_layer_comparison"
        ),
    }


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
    output_signature_count = _count_embedded_signatures(output_file)
    output_signature_snapshot = _snapshot_output_signature(output_file)
    output_verification_snapshot = _snapshot_output_verification(
        output_file,
        trust_policy=trust_policy,
    )
    output_visible_appearance_snapshot = _snapshot_visible_signature_appearance(output_file)
    signed_output_render_snapshot = _snapshot_signed_output_render(
        output_pdf_path=str(output_file),
        page_index=page_index,
        preview_snapshot=preview_snapshot,
        preview_text=preview_text,
        output_visible_appearance_snapshot=output_visible_appearance_snapshot,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
    )
    return {
        "output_file_exists": True,
        "output_file_size_bytes": output_file.stat().st_size,
        "output_signature_count": output_signature_count,
        "output_signature_snapshot": output_signature_snapshot,
        "output_verification_snapshot": output_verification_snapshot,
        "output_visible_appearance_snapshot": output_visible_appearance_snapshot,
        "signed_output_render_snapshot": signed_output_render_snapshot,
        "signed_output_preview_comparison": _signed_output_preview_comparison_snapshot(
            signed_output_render_snapshot
        ),
    }


def _build_signed_run_bundle(
    *,
    run_index: int,
    sign_time_state: dict[str, Any],
    request: SigningRequest,
    signing_result: SigningResult,
    artifacts_dir: str | None,
    artifact_basename: str | None,
) -> dict[str, Any]:
    bundle = {
        "run_index": run_index,
        "capture_label": sign_time_state.get("capture_label"),
        "preview_snapshot": deepcopy(sign_time_state.get("preview_snapshot")),
        "preview_text": sign_time_state.get("preview_text"),
        "validation_text": sign_time_state.get("validation_text"),
        "sign_request_snapshot": deepcopy(sign_time_state.get("sign_request_snapshot")),
        "backend_reservation_snapshot": deepcopy(
            sign_time_state.get("backend_reservation_snapshot")
        ),
        "backend_reservation_error": sign_time_state.get("backend_reservation_error"),
        "signing_result": _snapshot_signing_result_payload(signing_result),
        "output_pdf_path": request.output_pdf_path,
        "output_file_exists": False,
        "output_file_size_bytes": None,
        "output_signature_count": None,
        "output_signature_snapshot": None,
        "output_verification_snapshot": None,
        "output_visible_appearance_snapshot": None,
        "signed_output_render_snapshot": None,
        "signed_output_preview_comparison": None,
    }
    output_file = Path(request.output_pdf_path)
    if signing_result.success and output_file.exists():
        bundle.update(
            _snapshot_successful_signed_output(
                output_file=output_file,
                page_index=(
                    request.signature_rect.page_index
                    if request.signature_rect is not None
                    else None
                ),
                preview_snapshot=_mapping(sign_time_state.get("preview_snapshot")),
                preview_text=str(sign_time_state.get("preview_text", "")),
                trust_policy=request.trust_policy,
                artifacts_dir=artifacts_dir,
                artifact_basename=artifact_basename,
            )
        )
    return bundle


def run_phase3_preview_matrix(
    *,
    pdf_path: str,
    certificate_path: str,
    passphrase: str,
    scenario_manifest_path: str,
    artifacts_dir: str,
) -> dict[str, Any]:
    """Run a repeatable preview-only scenario sweep and capture rendered artifacts."""

    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PDF does not exist: {pdf_path}")

    manifest = _load_preview_matrix_manifest(scenario_manifest_path)
    scenarios = manifest["scenarios"]
    artifact_root = Path(artifacts_dir)
    artifact_root.mkdir(parents=True, exist_ok=True)

    profile_store = SignaturePresetCatalogStore.default()
    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        try:
            result = _execute_headless_preview_matrix_scenario(
                source_path=source_path,
                certificate_path=certificate_path,
                passphrase=passphrase,
                scenario=scenario,
                profile_store=profile_store,
                artifacts_dir=artifact_root,
            )
        except Exception as exc:
            result = _preview_matrix_error_result(scenario=scenario, error=exc)
        results.append(result)

    summary = {
        "pdf_path": str(source_path),
        "scenario_manifest_path": scenario_manifest_path,
        "artifacts_dir": str(artifact_root),
        "scenario_count": len(results),
        "successful_scenario_count": sum(1 for item in results if "error" not in item),
        "error_scenario_count": sum(1 for item in results if "error" in item),
        **_preview_matrix_diagnostic_summary(results),
        "results": results,
    }
    summary_path = artifact_root / "summary.json"
    summary_path.write_text(
        json.dumps(_jsonable_capture(summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def run_phase3_signed_acceptance_matrix(
    *,
    pdf_path: str,
    certificate_path: str,
    passphrase: str,
    scenario_manifest_path: str,
    artifacts_dir: str,
) -> dict[str, Any]:
    """Run a repeatable signed-output acceptance sweep over representative cases."""

    bindings = _load_qt_harness_bindings()
    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PDF does not exist: {pdf_path}")

    manifest = _load_preview_matrix_manifest(scenario_manifest_path)
    scenarios = manifest["scenarios"]
    artifact_root = Path(artifacts_dir)
    artifact_root.mkdir(parents=True, exist_ok=True)
    timestamping_mode = manifest.get("timestamping_mode", "real")
    if timestamping_mode not in {"real", "dummy"}:
        raise ValueError("'timestamping_mode' must be one of 'real' or 'dummy'.")
    sign_executor = build_phase3_signing_executor(
        timestamper_factory=(
            (lambda _tsa_url: build_dummy_timestamper())
            if timestamping_mode == "dummy"
            else None
        )
    )

    page_count = _load_page_count(bindings=bindings, pdf_path=str(source_path))
    backend = QtPdfRenderBackend()
    diagnostic = backend.diagnostics()
    if not diagnostic.available:
        raise RuntimeError(diagnostic.message)

    viewer_workflow = ViewerWorkflow(
        document_path=str(source_path),
        render_backend=backend,
        session=ViewerSession(page_count=page_count),
    )
    signing_workflow = SigningDraftWorkflow(
        input_pdf_path=str(source_path),
        output_pdf_path=str(source_path.with_name(source_path.stem + "-signed.pdf")),
        certificate_path=certificate_path,
        passphrase=passphrase,
        tsa_url="https://tsa.example.invalid",
        timestamp_required=False,
    )
    profile_store = SignaturePresetCatalogStore.default()

    app = bindings.q_application.instance() or bindings.q_application([])
    window = bindings.q_main_window()
    window.setWindowTitle(f"FoliaSeal Phase 3 Signed Acceptance Matrix - {source_path.name}")
    window.resize(1440, 980)
    shell = build_qt_signing_shell(
        viewer_workflow=viewer_workflow,
        signing_workflow=signing_workflow,
        preset_catalog_store=profile_store,
        sign_executor=sign_executor,
    )
    window.setCentralWidget(shell)
    window.show()
    shell.refresh_viewer()
    app.processEvents()

    results: list[dict[str, Any]] = []
    for scenario in scenarios:
        try:
            result = _execute_signed_acceptance_scenario(
                shell=shell,
                scenario=scenario,
                profile_store=profile_store,
                artifacts_dir=artifact_root,
                base_input_path=source_path,
                certificate_path=certificate_path,
                passphrase=passphrase,
                sign_executor=sign_executor,
            )
        except Exception as exc:
            result = _preview_matrix_error_result(scenario=scenario, error=exc)
        results.append(result)
        app.processEvents()

    close = getattr(window, "close", None)
    if callable(close):
        close()

    summary = {
        "pdf_path": str(source_path),
        "scenario_manifest_path": scenario_manifest_path,
        "artifacts_dir": str(artifact_root),
        "scenario_count": len(results),
        "successful_scenario_count": sum(
            1 for item in results if _mapping(item.get("signing_result")).get("success") is True
        ),
        "error_scenario_count": sum(1 for item in results if "error" in item),
        **_signed_matrix_diagnostic_summary(results),
        "results": results,
    }
    if "acceptance_expectations" in manifest:
        summary["acceptance_expectations"] = manifest["acceptance_expectations"]
    summary["timestamping_mode"] = timestamping_mode
    expectations_passed, expectation_errors = _evaluate_signed_matrix_acceptance_expectations(
        summary=summary,
        manifest_expectations=_mapping(manifest.get("acceptance_expectations")),
    )
    summary["acceptance_expectations_passed"] = expectations_passed
    summary["acceptance_expectation_errors"] = expectation_errors
    summary_path = artifact_root / "summary.json"
    summary_path.write_text(
        json.dumps(_jsonable_capture(summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


@dataclass(frozen=True)
class _QtHarnessBindings:
    q_application: type[Any]
    q_main_window: type[Any]
    q_widget: type[Any]
    q_v_box_layout: type[Any]
    q_h_box_layout: type[Any]
    q_group_box: type[Any]
    q_push_button: type[Any]
    q_label: type[Any]
    q_plain_text_edit: type[Any]
    qpdf_document: type[Any]


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


def _derive_phase3_auto_checked_items(capture: Phase3HarnessCapture) -> set[str]:
    auto_checked: set[str] = set()

    if capture.preview_available:
        auto_checked.add(
            "Confirm the signature properties flow is reachable from the main signing UI."
        )
        auto_checked.add(
            "Confirm the viewer preview renders before any signing action is attempted."
        )
        auto_checked.add(
            "The focused properties panel shows the available appearance controls."
        )

    if not capture.errors:
        auto_checked.add(
            "Confirm the selected PDF can be used without unexpected dependency or backend errors."
        )

    if capture.first_render_ms is not None:
        auto_checked.add(
            "Launch the Phase 3 desktop build in an environment with the relevant "
            "PDF signing UI enabled."
        )

    if capture.selection_count > 0:
        auto_checked.add("The user can draw a signature rectangle on the preview.")
        auto_checked.add("The resulting placement lands on the expected page area.")

    if capture.selection_count > 1:
        auto_checked.add("The placed rectangle can be resized or repositioned in the workflow.")

    if capture.sign_request_count > 0:
        auto_checked.add("The sign action is available from the properties flow.")
        auto_checked.add(
            "The app shows the expected confirmation or summary before signing, if applicable."
        )

    if capture.last_signature_page_index is not None:
        auto_checked.add("The user can choose the target page before placement.")

    return auto_checked


def _write_optional_text(*, target_path: str | None, content: str) -> None:
    if target_path is None:
        return
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _count_embedded_signatures(output_file: Path) -> int | None:
    try:
        with output_file.open("rb") as handle:
            reader = PdfFileReader(handle)
            return len(list(reader.embedded_signatures))
    except Exception:
        return None


def _snapshot_output_signature(output_file: Path) -> dict[str, Any] | None:
    try:
        with output_file.open("rb") as handle:
            reader = PdfFileReader(handle)
            embedded_signatures = list(reader.embedded_signatures)
            if not embedded_signatures:
                return None
            signature = embedded_signatures[-1]
            sig_object = signature.sig_object
            return {
                "field_name": signature.field_name,
                "name": sig_object.get("/Name"),
                "location": sig_object.get("/Location"),
                "contact_info": sig_object.get("/ContactInfo"),
                "byte_range": list(sig_object.get("/ByteRange", [])),
                "subfilter": sig_object.get("/SubFilter"),
                "md_algorithm": signature.md_algorithm,
                "coverage": _serialize_signature_metadata(signature.coverage),
                "docmdp_level": _serialize_signature_metadata(signature.docmdp_level),
            }
    except Exception:
        return None


def _snapshot_output_verification(
    output_file: Path,
    trust_policy: TimestampTrustPolicy | None = None,
) -> dict[str, Any] | None:
    try:
        with output_file.open("rb") as handle:
            reader = PdfFileReader(handle)
            embedded_signatures = list(reader.embedded_signatures)
            if not embedded_signatures:
                return {
                    "cryptographic_validation_passed": False,
                    "signature_count": 0,
                    "docmdp_permission": None,
                    "certification_restricted": False,
                    "restriction_reason": None,
                    "error": "No embedded signature fields were found in the output PDF.",
                }

            signature = embedded_signatures[-1]
            validation_context = ValidationContext(trust_roots=[signature.signer_cert])
            ts_validation_context = build_timestamp_validation_context(trust_policy)
            status = validation.validate_pdf_signature(
                signature,
                signer_validation_context=validation_context,
                ts_validation_context=ts_validation_context,
            )
            certification = inspect_pdf_certification_reader(reader)
            signer_subject = None
            if getattr(signature, "signer_cert", None) is not None:
                subject = getattr(signature.signer_cert, "subject", None)
                if subject is not None:
                    human_friendly = getattr(subject, "human_friendly", None)
                    signer_subject = (
                        human_friendly if isinstance(human_friendly, str) else str(subject)
                    )
            return {
                "cryptographic_validation_passed": bool(status.intact and status.valid),
                "intact": bool(status.intact),
                "valid": bool(status.valid),
                "trusted": bool(getattr(status, "trust_problem_indicative", False) is False),
                "signature_count": len(embedded_signatures),
                "timestamp_present": _status_has_timestamp_for_snapshot(status),
                "timestamp_cryptographically_valid": (
                    _status_timestamp_cryptographically_valid_for_snapshot(status)
                    if trust_policy is not None
                    else None
                ),
                "tsa_chain_trusted": (
                    _status_timestamp_trusted_for_snapshot(status)
                    if trust_policy is not None
                    else None
                ),
                "timestamp_validation_error": (
                    _describe_timestamp_trust_for_snapshot(status)
                    if trust_policy is not None
                    and not _status_timestamp_trusted_for_snapshot(status)
                    else None
                ),
                "docmdp_permission": certification.docmdp_permission,
                "certification_restricted": certification.certification_restricted,
                "restriction_reason": certification.restriction_reason,
                "field_name": signature.field_name,
                "subfilter": signature.sig_object.get("/SubFilter"),
                "byte_range_present": bool(signature.sig_object.get("/ByteRange")),
                "md_algorithm": signature.md_algorithm,
                "signer_subject": signer_subject,
                "error": None,
            }
    except Exception as exc:
        return {
            "cryptographic_validation_passed": False,
            "signature_count": None,
            "docmdp_permission": None,
            "certification_restricted": False,
            "restriction_reason": None,
            "error": str(exc),
        }


def _snapshot_visible_signature_appearance(output_file: Path) -> dict[str, Any] | None:
    try:
        with output_file.open("rb") as handle:
            reader = PdfFileReader(handle)
            embedded_signatures = list(reader.embedded_signatures)
            if not embedded_signatures:
                return None

            signature = embedded_signatures[-1]
            sig_field = signature.sig_field
            rect = _snapshot_pdf_rect(sig_field.get("/Rect"))
            appearance_dict = sig_field.get("/AP")
            if appearance_dict is None:
                return {
                    "field_name": signature.field_name,
                    "annotation_rect": rect,
                    "error": "Missing /AP entry on the signature field.",
                }

            normal_appearance = appearance_dict.get("/N")
            if normal_appearance is None:
                return {
                    "field_name": signature.field_name,
                    "annotation_rect": rect,
                    "error": "Missing normal appearance stream for the signature field.",
                }

            appearance_stream = normal_appearance.get_object()
            appearance_data = appearance_stream.data
            appearance_text = appearance_data.decode("latin1", errors="replace")
            xobject_summaries = _snapshot_appearance_xobjects(
                appearance_stream.get("/Resources")
            )
            text_fragments = _extract_pdf_text_fragments(appearance_text)
            visible_text_present = bool(text_fragments)
            image_xobject_count = sum(
                1 for item in xobject_summaries if item.get("subtype") == "/Image"
            )
            appearance_bbox = _snapshot_pdf_rect(appearance_stream.get("/BBox"))
            rounded_border = _appearance_text_uses_rounded_border(appearance_text)
            return {
                "field_name": signature.field_name,
                "annotation_rect": rect,
                "appearance_bbox": appearance_bbox,
                "appearance_stream_length": len(appearance_data),
                "appearance_text_fragments": text_fragments,
                "appearance_text_snippet": appearance_text[:240],
                "appearance_text_operator_count": _count_pdf_text_operators(appearance_text),
                "appearance_xobjects": xobject_summaries,
                "appearance_image_xobject_count": image_xobject_count,
                "appearance_has_visible_text": visible_text_present,
                "visible_text_present": visible_text_present,
                "text_fragments": text_fragments,
                "image_xobjects": xobject_summaries,
                "annotation_rect_size": _snapshot_rect_size(rect),
                "appearance_bbox_size": _snapshot_rect_size(appearance_bbox),
                "text_fragment_count": len(text_fragments),
                "image_xobject_count": image_xobject_count,
                "appearance_uses_rounded_border": rounded_border,
            }
    except Exception as exc:
        return {"error": str(exc)}


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
            bbox = _snapshot_pdf_rect(imported_appearance.get("/BBox"))
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
                stream_data=(
                    f"q 1 0 0 1 {-min_x} {-min_y} cm /Fx Do Q".encode("ascii")
                )
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


def _status_has_timestamp_for_snapshot(status: Any) -> bool:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return False
    return bool(
        getattr(timestamp_validity, "intact", True)
        and getattr(timestamp_validity, "valid", True)
    )


def _status_timestamp_cryptographically_valid_for_snapshot(status: Any) -> bool | None:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return None
    return bool(
        getattr(timestamp_validity, "intact", True)
        and getattr(timestamp_validity, "valid", True)
    )


def _status_timestamp_trusted_for_snapshot(status: Any) -> bool | None:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return None
    return bool(getattr(timestamp_validity, "trusted", False))


def _describe_timestamp_trust_for_snapshot(status: Any) -> str | None:
    timestamp_validity = getattr(status, "timestamp_validity", None)
    if timestamp_validity is None:
        return None
    describe_timestamp_trust = getattr(timestamp_validity, "describe_timestamp_trust", None)
    if not callable(describe_timestamp_trust):
        return None
    try:
        return describe_timestamp_trust()
    except Exception:
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

    backend = QtPdfRenderBackend()
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

    direct_appearance_render = _render_signed_annotation_appearance_direct(
        output_pdf_path=output_pdf_path,
        artifacts_dir=artifacts_dir,
        artifact_basename=artifact_basename,
        zoom=render_zoom,
    )
    result["direct_appearance_render_path"] = direct_appearance_render.get("image_path")
    result["direct_appearance_render_error"] = direct_appearance_render.get("error")

    try:
        visible_snapshot = output_visible_appearance_snapshot or {}
        rect = _parse_snapshot_rect(visible_snapshot.get("annotation_rect"))
        if rect is None:
            result["signature_crop_error"] = "Output visible appearance did not include a rect."
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
        padding = max(6, _preview_padding_for_capture_from_snapshot(preview_snapshot))
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
        preview_crop_bounds = _snapshot_preview_card_bounds(preview_snapshot)
        if preview_crop_bounds is not None:
            preview_analysis_image_path = _snapshot_preview_analysis_image(preview_snapshot)
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
                Path(artifacts_dir) / f"{artifact_basename}_signed_output_crop_normalized.png"
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
            result["preview_vs_signed_output_change_ratio"] = _normalized_image_crop_change_ratio(
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
            result["preview_vs_signed_output_aspect_ratio_delta"] = _aspect_ratio_delta(
                preview_crop_bounds["width"],
                preview_crop_bounds["height"],
                cropped.size[0],
                cropped.size[1],
            )
            preview_text_normalized = _normalize_visible_text_for_comparison(preview_text)
            output_text = _normalize_visible_text_for_comparison(
                " ".join(_snapshot_visible_appearance_text_fragments(visible_snapshot))
            )
            result["preview_text_fragments_match_output"] = (
                preview_text_normalized == output_text
            )
            result["preview_has_image_stamp"] = bool(preview_snapshot.get("image_stamp_path"))
            result["signed_output_has_image_stamp"] = bool(
                _snapshot_visible_appearance_image_xobjects(visible_snapshot)
            )
            result["output_image_presence_matches_preview"] = (
                result["preview_has_image_stamp"] == result["signed_output_has_image_stamp"]
            )
            render_capture = _mapping(preview_snapshot.get("render_capture"))
            output_text_bounds, output_text_error = _detect_text_content_bounds_in_preview(
                preview_image_path=str(normalized_crop_path),
                text_widget_bounds={
                    "x": 0,
                    "y": 0,
                    "width": normalized_crop.size[0],
                    "height": normalized_crop.size[1],
                },
                text_color_rgba=_preview_text_color_rgba_from_snapshot(preview_snapshot),
                reference_text_content_bounds=_mapping(
                    render_capture.get(
                        "text_rendered_content_bounds_px"
                    )
                ),
            )
            output_text_line_bounds, output_text_line_error = _detect_text_line_bounds_in_preview(
                preview_image_path=str(normalized_crop_path),
                text_widget_bounds={
                    "x": 0,
                    "y": 0,
                    "width": normalized_crop.size[0],
                    "height": normalized_crop.size[1],
                },
                text_color_rgba=_preview_text_color_rgba_from_snapshot(preview_snapshot),
                reference_text_content_bounds=_mapping(
                    render_capture.get(
                        "text_rendered_content_bounds_px"
                    )
                ),
            )
            result["output_text_content_bounds_px"] = output_text_bounds
            result["output_text_detection_error"] = output_text_error
            result["output_text_line_bounds_px"] = output_text_line_bounds
            result["output_text_line_detection_error"] = output_text_line_error
            result["output_text_bounds_match_preview"] = _rectangles_within_tolerance(
                result.get("output_text_content_bounds_px"),
                _mapping(preview_snapshot.get("render_capture")).get(
                    "text_rendered_content_bounds_px"
                ),
                tolerance_px=6,
            )
            preview_appearance_snapshot = _preview_appearance_snapshot_from_capture(
                preview_snapshot=preview_snapshot
            )
            signed_output_appearance_snapshot = _signed_output_appearance_snapshot(
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
            result["preview_appearance_snapshot"] = preview_appearance_snapshot
            result["signed_output_appearance_snapshot"] = signed_output_appearance_snapshot
            appearance_comparison = compare_signature_appearance_snapshots(
                preview_appearance_snapshot,
                signed_output_appearance_snapshot,
            )
            result["appearance_layer_comparison"] = _jsonable_capture(appearance_comparison)
            requested_rect = _signature_rect_from_snapshot(preview_snapshot)
            if requested_rect is not None:
                result["annotation_rect_delta_pt"] = _rect_delta(
                    requested_rect,
                    _snapshot_rect_size_and_origin_dict(_mapping(visible_snapshot).get("annotation_rect")),
                )
                result["annotation_rect_matches_request"] = _rect_delta_within_tolerance(
                    result["annotation_rect_delta_pt"],
                    tolerance_pt=0.75,
                )
            result["preview_vs_signed_output_passed"] = (
                appearance_comparison.is_consistent
                and result["annotation_rect_matches_request"] is not False
            )
        comparison_path = Path(artifacts_dir) / f"{artifact_basename}_signed_output_compare.png"
        _write_side_by_side_comparison(
            preview_image_path=_snapshot_preview_analysis_image(preview_snapshot),
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


def _preview_appearance_snapshot_from_capture(
    *,
    preview_snapshot: dict[str, Any],
) -> SignatureAppearanceSnapshot:
    render_capture = _mapping(preview_snapshot.get("render_capture"))
    analysis_snapshot = _mapping(render_capture.get("analysis_appearance_snapshot"))
    box_style = _mapping(preview_snapshot.get("box_style"))
    if analysis_snapshot:
        border_style = _mapping(analysis_snapshot.get("border_style")) or None
        border_bounds = _mapping(analysis_snapshot.get("border_bounds_px")) or None
        if border_style is None and box_style.get("show_border") is True:
            border_style = {
                "show_border": True,
                "shape": "rounded",
                "border_color_hex": box_style.get("border_color_hex"),
                "border_width_pt": box_style.get("border_width_pt"),
                "background_color_hex": box_style.get("background_color_hex"),
            }
            border_bounds = _mapping(analysis_snapshot.get("container_bounds_px")) or None
        return SignatureAppearanceSnapshot(
            image_path=analysis_snapshot.get("image_path"),
            image_size_px=_mapping(analysis_snapshot.get("image_size_px")) or None,
            container_bounds_px=_mapping(analysis_snapshot.get("container_bounds_px")) or None,
            border_bounds_px=border_bounds,
            border_style=border_style,
            text_bounds_px=_mapping(analysis_snapshot.get("text_bounds_px")) or None,
            stamp_bounds_px=_mapping(analysis_snapshot.get("stamp_bounds_px")) or None,
            text_fragments=tuple(analysis_snapshot.get("text_fragments", ())),
            line_bounds_px=tuple(analysis_snapshot.get("line_bounds_px", ())),
        )
    card_bounds = _mapping(render_capture.get("card_bounds_px"))
    image_size = None
    if card_bounds:
        image_size = {"width": card_bounds["width"], "height": card_bounds["height"]}
    border_style = None
    if box_style.get("show_border") is True:
        border_style = {
            "show_border": True,
            "shape": "rounded",
            "border_color_hex": box_style.get("border_color_hex"),
            "border_width_pt": box_style.get("border_width_pt"),
            "background_color_hex": box_style.get("background_color_hex"),
        }
    text_fragments = tuple(
        field.get("text", "").strip()
        for field in preview_snapshot.get("fields", ())
        if (
            isinstance(field, dict)
            and field.get("visible") is True
            and field.get("text", "").strip()
        )
    )
    text_style = _signature_text_style_from_snapshot(preview_snapshot.get("text_style"))
    text_bounds = _mapping(render_capture.get("text_rendered_content_bounds_px")) or None
    line_bounds = tuple(render_capture.get("text_rendered_line_bounds_px", ()))
    if not line_bounds:
        line_bounds = _structural_line_bounds_px(
            text_fragments=text_fragments,
            text_style=text_style,
            text_bounds_px=text_bounds,
        )
    return SignatureAppearanceSnapshot(
        image_path=render_capture.get("analysis_preview_image_path")
        or render_capture.get("preview_image_path"),
        image_size_px=image_size,
        container_bounds_px=card_bounds or None,
        border_bounds_px=(card_bounds or None) if border_style is not None else None,
        border_style=border_style,
        text_bounds_px=text_bounds,
        stamp_bounds_px=_mapping(render_capture.get("stamp_rendered_content_bounds_px")) or None,
        text_fragments=text_fragments,
        line_bounds_px=line_bounds,
    )


def _snapshot_sign_time_fit_diagnostics(
    *,
    preview_render_capture: dict[str, Any] | None,
    backend_reservation_snapshot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    backend = _mapping(backend_reservation_snapshot)
    render_capture = _mapping(preview_render_capture)
    if not backend and not render_capture:
        return None
    analysis_snapshot = _mapping(render_capture.get("analysis_appearance_snapshot"))
    structural_line_bounds = tuple(
        analysis_snapshot.get("line_bounds_px")
        or render_capture.get("text_structural_line_bounds_px")
        or ()
    )
    structural_text_bounds = _mapping(analysis_snapshot.get("text_bounds_px")) or _mapping(
        render_capture.get("text_structural_content_bounds_px")
    )
    glyph_ink_line_bounds = tuple(render_capture.get("text_rendered_line_bounds_px") or ())
    glyph_ink_text_bounds = _mapping(render_capture.get("text_rendered_content_bounds_px"))
    canonical_stamp_bounds = _mapping(analysis_snapshot.get("stamp_bounds_px")) or _mapping(
        render_capture.get("stamp_rendered_content_bounds_px")
    )
    canonical_image_size = _mapping(analysis_snapshot.get("image_size_px")) or {
        "width": _mapping(render_capture.get("card_bounds_px")).get("width"),
        "height": _mapping(render_capture.get("card_bounds_px")).get("height"),
    }
    if canonical_image_size == {"width": None, "height": None}:
        canonical_image_size = None
    return {
        "backend_fit": {
            "coordinate_space": "pdf_points",
            "measured_text_box_width_pt": backend.get("measured_text_box_width_pt"),
            "measured_text_box_height_pt": backend.get("measured_text_box_height_pt"),
            "text_area_width_pt": backend.get("text_area_width_pt"),
            "text_area_height_pt": backend.get("text_area_height_pt"),
            "stamp_area_width_pt": backend.get("stamp_area_width_pt"),
            "stamp_area_height_pt": backend.get("stamp_area_height_pt"),
            "reserved_primary_extent_pt": backend.get("reserved_primary_extent_pt"),
            "fit_gate_width_limit_pt": backend.get("fit_gate_width_limit_pt"),
            "fit_gate_height_limit_pt": backend.get("fit_gate_height_limit_pt"),
            "fit_gate_passed": backend.get("fit_gate_passed"),
            "error": backend.get("error"),
        },
        "canonical_preview_geometry": {
            "coordinate_space": "canonical_preview_pixels",
            "image_path": analysis_snapshot.get("image_path")
            or render_capture.get("analysis_preview_image_path")
            or render_capture.get("preview_image_path"),
            "image_size_px": canonical_image_size,
            "container_bounds_px": _mapping(analysis_snapshot.get("container_bounds_px"))
            or _mapping(render_capture.get("card_bounds_px")),
            "text_bounds_px": glyph_ink_text_bounds or structural_text_bounds,
            "line_bounds_px": glyph_ink_line_bounds or structural_line_bounds,
            "structural_text_bounds_px": structural_text_bounds,
            "structural_line_bounds_px": structural_line_bounds,
            "glyph_ink_text_bounds_px": glyph_ink_text_bounds,
            "glyph_ink_line_bounds_px": glyph_ink_line_bounds,
            "stamp_bounds_px": canonical_stamp_bounds,
        },
    }


def _signed_output_appearance_snapshot(
    *,
    normalized_image_path: str,
    normalized_image_size: dict[str, int],
    text_bounds_px: dict[str, int] | None,
    line_bounds_px: tuple[dict[str, int], ...] = (),
    visible_appearance_snapshot: dict[str, Any],
    preview_snapshot: dict[str, Any],
) -> SignatureAppearanceSnapshot:
    preview_box_style = _mapping(preview_snapshot.get("box_style"))
    border_shape = "rounded"
    if visible_appearance_snapshot.get("appearance_uses_rounded_border") is False:
        border_shape = "square"
    elif visible_appearance_snapshot.get("appearance_uses_rounded_border") is None:
        border_shape = "unknown"
    border_style = None
    if preview_box_style.get("show_border") is True:
        border_style = {
            "show_border": True,
            "shape": border_shape,
            "border_color_hex": preview_box_style.get("border_color_hex"),
            "border_width_pt": preview_box_style.get("border_width_pt"),
            "background_color_hex": preview_box_style.get("background_color_hex"),
        }
    container_bounds = {
        "x": 0,
        "y": 0,
        "width": normalized_image_size["width"],
        "height": normalized_image_size["height"],
    }
    stamp_bounds = None
    if _snapshot_visible_appearance_image_xobjects(visible_appearance_snapshot):
        preview_render_capture = _mapping(preview_snapshot.get("render_capture"))
        stamp_bounds = (
            _mapping(preview_render_capture.get("stamp_rendered_content_bounds_px")) or None
        )
    text_fragments = tuple(_snapshot_visible_appearance_text_fragments(visible_appearance_snapshot))
    text_style = _signature_text_style_from_snapshot(preview_snapshot.get("text_style"))
    reconstructed_text_box_bounds = _reconstruct_text_box_bounds_px(
        preview_snapshot=preview_snapshot,
        text_fragments=text_fragments,
        container_bounds_px=container_bounds,
    )
    structural_line_bounds = _structural_line_bounds_px(
        text_fragments=text_fragments,
        text_style=text_style,
        text_bounds_px=reconstructed_text_box_bounds or text_bounds_px,
    )
    return SignatureAppearanceSnapshot(
        image_path=normalized_image_path,
        image_size_px=normalized_image_size,
        container_bounds_px=container_bounds,
        border_bounds_px=container_bounds if border_style is not None else None,
        border_style=border_style,
        text_bounds_px=(
            _union_rectangles(structural_line_bounds)
            or reconstructed_text_box_bounds
            or text_bounds_px
        ),
        stamp_bounds_px=stamp_bounds,
        text_fragments=text_fragments,
        line_bounds_px=structural_line_bounds or line_bounds_px,
    )


def _signature_text_style_from_snapshot(snapshot: object) -> SignatureTextStyle | None:
    if not isinstance(snapshot, dict):
        return None
    font_family = snapshot.get("font_family")
    font_size_pt = snapshot.get("font_size_pt")
    text_color_hex = snapshot.get("text_color_hex")
    if not isinstance(font_family, str) or font_size_pt is None or not isinstance(
        text_color_hex, str
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
    text_box_style = _build_text_box_style(text_style)
    text_box_width, text_box_height = _measure_text_box_dimensions(
        stamp_text,
        text_box_style,
    )
    image_stamp_path = preview_snapshot.get("image_stamp_path")
    stamp_background = (
        _stamp_background_for_path(image_stamp_path)
        if isinstance(image_stamp_path, str) and image_stamp_path
        else None
    )
    reservation = _layout_reservation_for_template(
        layout_template,
        stamp_position=stamp_position,
        signature_rect=signature_rect,
        text_box_width=text_box_width,
        text_box_height=text_box_height,
        box_style=box_style,
        has_visible_stamp_image=stamp_background is not None,
        stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
    )
    return _layout_rule_bounds_px(
        reservation.inner_content_layout,
        reserved_width_pt=reservation.text_box_width_pt,
        reserved_height_pt=reservation.text_box_height_pt,
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
                f"Scenario '{name}' has unsupported timestamp_required: "
                f"{timestamp_required!r}"
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
    return manifest


def _execute_preview_matrix_scenario(
    *,
    shell: Any,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
    artifacts_dir: Path,
) -> dict[str, Any]:
    _apply_preview_matrix_scenario(
        shell=shell,
        scenario=scenario,
        profile_store=profile_store,
    )
    preview = shell.properties_panel.refresh_preview()
    preview_text = shell.properties_panel.preview_text()
    validation_text = shell.properties_panel.validation_text()
    request = _snapshot_current_draft_request(shell.properties_panel._workflow)
    artifact_basename = _scenario_slug(str(scenario["name"]))
    render_capture = _capture_preview_render(
        shell=shell,
        preview=preview,
        artifacts_dir=str(artifacts_dir),
        artifact_basename=artifact_basename,
    )
    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "preview_snapshot": _snapshot_preview(preview, render_capture=render_capture),
        "preview_text": preview_text,
        "validation_text": validation_text,
        "sign_request_snapshot": _snapshot_signing_request(request),
        "backend_reservation_snapshot": (
            _snapshot_backend_reservation(request) if request is not None else None
        ),
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
    _apply_preview_matrix_scenario_to_workflow(
        workflow=workflow,
        scenario=scenario,
        profile_store=profile_store,
    )
    preview = workflow.preview()
    preview_text = _headless_preview_text(preview)
    validation_text = _headless_validation_text(preview)
    request = _snapshot_current_draft_request(workflow)
    artifact_basename = _scenario_slug(str(scenario["name"]))
    render_capture = _capture_headless_preview_render(
        preview=preview,
        artifacts_dir=str(artifacts_dir),
        artifact_basename=artifact_basename,
    )
    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "preview_snapshot": _snapshot_preview(preview, render_capture=render_capture),
        "preview_text": preview_text,
        "validation_text": validation_text,
        "sign_request_snapshot": _snapshot_signing_request(request),
        "backend_reservation_snapshot": (
            _snapshot_backend_reservation(request) if request is not None else None
        ),
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


def _apply_preview_matrix_scenario_to_workflow(
    *,
    workflow: SigningDraftWorkflow,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
) -> None:
    catalog = profile_store.load_catalog()
    profile_name = scenario.get("profile_name")
    if profile_name is not None:
        if not isinstance(profile_name, str) or not profile_name.strip():
            raise ValueError("Scenario 'profile_name' must be a non-empty string.")
        preset = catalog.profile_named(profile_name)
        base_appearance = preset.appearance
    else:
        base_appearance = workflow.current_signature_appearance or SignatureAppearance()
    appearance = _apply_appearance_overrides(
        base_appearance,
        scenario.get("appearance_overrides"),
    )
    workflow.set_signature_appearance(appearance)
    if "timestamp_required" in scenario:
        workflow.timestamp_required = bool(scenario["timestamp_required"])
    signature_rect_payload = scenario.get("signature_rect")
    if signature_rect_payload is not None:
        workflow.set_signature_rect(_signature_rect_from_payload(signature_rect_payload))


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
    shell: Any,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
    artifacts_dir: Path,
    base_input_path: Path,
    certificate_path: str,
    passphrase: str,
    sign_executor: Any,
) -> dict[str, Any]:
    _apply_preview_matrix_scenario(
        shell=shell,
        scenario=scenario,
        profile_store=profile_store,
    )
    preview = shell.properties_panel.refresh_preview()
    preview_text = shell.properties_panel.preview_text()
    validation_text = shell.properties_panel.validation_text()
    request = _snapshot_current_draft_request(shell.properties_panel._workflow)
    artifact_basename = _scenario_slug(str(scenario["name"]))
    render_capture = _capture_preview_render(
        shell=shell,
        preview=preview,
        artifacts_dir=str(artifacts_dir),
        artifact_basename=artifact_basename,
    )
    preview_snapshot = _snapshot_preview(preview, render_capture=render_capture)
    output_signature_count = None
    output_signature_snapshot = None
    output_verification_snapshot = None
    output_visible_appearance_snapshot = None
    signed_output_render_snapshot = None
    output_file_exists = False
    signing_result_payload = None

    request_snapshot = _snapshot_signing_request(request)
    if request is not None:
        scenario_output = artifacts_dir / f"{artifact_basename}_signed.pdf"
        scenario_request = replace(
            request,
            input_pdf_path=str(base_input_path),
            output_pdf_path=str(scenario_output),
            certificate_path=certificate_path,
            passphrase=passphrase,
        )
        signing_result = sign_executor.execute(scenario_request)
        signing_result_payload = _snapshot_signing_result_payload(signing_result)
        if signing_result.success:
            output_file_exists = scenario_output.exists()
            if output_file_exists:
                output_snapshot = _snapshot_successful_signed_output(
                    output_file=scenario_output,
                    page_index=(
                        scenario_request.signature_rect.page_index
                        if scenario_request.signature_rect is not None
                        else None
                    ),
                    preview_snapshot=preview_snapshot,
                    preview_text=preview_text,
                    trust_policy=scenario_request.trust_policy,
                    artifacts_dir=str(artifacts_dir),
                    artifact_basename=artifact_basename,
                )
                output_signature_count = output_snapshot["output_signature_count"]
                output_signature_snapshot = output_snapshot["output_signature_snapshot"]
                output_verification_snapshot = output_snapshot["output_verification_snapshot"]
                output_visible_appearance_snapshot = output_snapshot[
                    "output_visible_appearance_snapshot"
                ]
                signed_output_render_snapshot = output_snapshot[
                    "signed_output_render_snapshot"
                ]

    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "expected_outcome": scenario.get("expected_outcome"),
        "expected_failure_message_contains": scenario.get("expected_failure_message_contains"),
        "preview_snapshot": preview_snapshot,
        "preview_text": preview_text,
        "validation_text": validation_text,
        "sign_request_snapshot": request_snapshot,
        "backend_reservation_snapshot": (
            _snapshot_backend_reservation(request) if request is not None else None
        ),
        "signing_result": signing_result_payload,
        "output_file_exists": output_file_exists,
        "output_signature_count": output_signature_count,
        "output_signature_snapshot": output_signature_snapshot,
        "output_verification_snapshot": output_verification_snapshot,
        "output_visible_appearance_snapshot": output_visible_appearance_snapshot,
        "signed_output_render_snapshot": signed_output_render_snapshot,
        "signed_output_preview_comparison": (
            None
            if signed_output_render_snapshot is None
            else {
                "preview_vs_signed_output_passed": signed_output_render_snapshot.get(
                    "preview_vs_signed_output_passed"
                ),
                "annotation_rect_matches_request": signed_output_render_snapshot.get(
                    "annotation_rect_matches_request"
                ),
                "output_text_bounds_match_preview": signed_output_render_snapshot.get(
                    "output_text_bounds_match_preview"
                ),
                "output_image_presence_matches_preview": signed_output_render_snapshot.get(
                    "output_image_presence_matches_preview"
                ),
                "page_render_path": signed_output_render_snapshot.get("page_render_path"),
                "signature_crop_path": signed_output_render_snapshot.get(
                    "signature_crop_path"
                ),
                "comparison_path": signed_output_render_snapshot.get("comparison_path"),
            }
        ),
    }


def _preview_matrix_error_result(*, scenario: dict[str, Any], error: Exception) -> dict[str, Any]:
    return {
        "name": scenario["name"],
        "profile_name": scenario.get("profile_name"),
        "error": str(error),
        "error_type": error.__class__.__name__,
    }


def _preview_matrix_diagnostic_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    text_clip_count = 0
    text_overlap_count = 0
    stamp_warning_count = 0
    stamp_edge_touch_count = 0
    signable_text_clip_count = 0
    rejected_text_clip_count = 0
    signable_text_overlap_count = 0
    rejected_text_overlap_count = 0
    signable_stamp_warning_count = 0
    rejected_stamp_warning_count = 0
    signable_stamp_edge_touch_count = 0
    rejected_stamp_edge_touch_count = 0
    for result in results:
        preview_snapshot = result.get("preview_snapshot")
        if not isinstance(preview_snapshot, dict):
            continue
        render_capture = preview_snapshot.get("render_capture")
        if not isinstance(render_capture, dict):
            continue
        can_submit = preview_snapshot.get("can_submit") is True
        if render_capture.get("text_content_clipped_in_preview") is True:
            text_clip_count += 1
            if can_submit:
                signable_text_clip_count += 1
            else:
                rejected_text_clip_count += 1
        if (
            render_capture.get("text_content_overlaps_stamp_band") is True
            or render_capture.get("text_content_overlaps_stamp_content") is True
        ):
            text_overlap_count += 1
            if can_submit:
                signable_text_overlap_count += 1
            else:
                rejected_text_overlap_count += 1
        if render_capture.get("stamp_content_within_warning_distance") is True:
            stamp_warning_count += 1
            if can_submit:
                signable_stamp_warning_count += 1
            else:
                rejected_stamp_warning_count += 1
        if render_capture.get("stamp_content_touches_band_edge") is True:
            stamp_edge_touch_count += 1
            if can_submit:
                signable_stamp_edge_touch_count += 1
            else:
                rejected_stamp_edge_touch_count += 1
    return {
        "text_clipping_risk_scenario_count": text_clip_count,
        "signable_text_clipping_risk_scenario_count": signable_text_clip_count,
        "rejected_text_clipping_risk_scenario_count": rejected_text_clip_count,
        "text_stamp_overlap_risk_scenario_count": text_overlap_count,
        "signable_text_stamp_overlap_risk_scenario_count": signable_text_overlap_count,
        "rejected_text_stamp_overlap_risk_scenario_count": rejected_text_overlap_count,
        "stamp_warning_scenario_count": stamp_warning_count,
        "signable_stamp_warning_scenario_count": signable_stamp_warning_count,
        "rejected_stamp_warning_scenario_count": rejected_stamp_warning_count,
        "stamp_edge_touch_scenario_count": stamp_edge_touch_count,
        "signable_stamp_edge_touch_scenario_count": signable_stamp_edge_touch_count,
        "rejected_stamp_edge_touch_scenario_count": rejected_stamp_edge_touch_count,
    }


def _signed_scenario_matches_expectation(result: dict[str, Any]) -> tuple[bool | None, str | None]:
    expected_outcome = result.get("expected_outcome")
    if expected_outcome is None:
        return None, None
    signing_result = _mapping(result.get("signing_result"))
    actual_success = signing_result.get("success") is True
    if expected_outcome == "success":
        if actual_success:
            return True, None
        message = signing_result.get("message")
        return False, (
            "Expected signing success but scenario failed"
            + (f": {message}" if isinstance(message, str) and message else ".")
        )
    if expected_outcome == "validation_rejection":
        if actual_success:
            return False, "Expected an intentional validation rejection but signing succeeded."
        fragment = result.get("expected_failure_message_contains")
        if isinstance(fragment, str) and fragment:
            message = signing_result.get("message")
            if not isinstance(message, str) or fragment not in message:
                return (
                    False,
                    "Expected rejection message to contain "
                    f"{fragment!r}, got {message!r}.",
                )
        return True, None
    return False, f"Unsupported expected_outcome: {expected_outcome!r}"


def _signed_matrix_diagnostic_summary(results: list[dict[str, Any]]) -> dict[str, int]:
    cryptographic_failures = 0
    preview_output_failures = 0
    annotation_rect_mismatches = 0
    sign_success_count = 0
    expected_success_count = 0
    expected_rejection_count = 0
    matched_expected_success_count = 0
    matched_expected_rejection_count = 0
    expected_outcome_mismatch_count = 0
    expectation_errors: list[str] = []
    for result in results:
        signing_result = _mapping(result.get("signing_result"))
        if signing_result.get("success") is True:
            sign_success_count += 1
        verification = _mapping(result.get("output_verification_snapshot"))
        if verification.get("cryptographic_validation_passed") is False:
            cryptographic_failures += 1
        comparison = _mapping(result.get("signed_output_preview_comparison"))
        if comparison.get("preview_vs_signed_output_passed") is False:
            preview_output_failures += 1
        if comparison.get("annotation_rect_matches_request") is False:
            annotation_rect_mismatches += 1
        expected_outcome = result.get("expected_outcome")
        if expected_outcome == "success":
            expected_success_count += 1
        elif expected_outcome == "validation_rejection":
            expected_rejection_count += 1
        matched, error = _signed_scenario_matches_expectation(result)
        if matched is True:
            if expected_outcome == "success":
                matched_expected_success_count += 1
            elif expected_outcome == "validation_rejection":
                matched_expected_rejection_count += 1
        elif matched is False:
            expected_outcome_mismatch_count += 1
            expectation_errors.append(f"{result.get('name')}: {error}")
    return {
        "successful_signing_run_count": sign_success_count,
        "cryptographic_validation_failure_count": cryptographic_failures,
        "preview_output_comparison_failure_count": preview_output_failures,
        "annotation_rect_mismatch_count": annotation_rect_mismatches,
        "expected_success_scenario_count": expected_success_count,
        "expected_intentional_rejection_count": expected_rejection_count,
        "matched_expected_success_count": matched_expected_success_count,
        "matched_expected_intentional_rejection_count": matched_expected_rejection_count,
        "expected_outcome_mismatch_count": expected_outcome_mismatch_count,
        "acceptance_expectation_errors": expectation_errors,
    }


def _evaluate_signed_matrix_acceptance_expectations(
    *,
    summary: dict[str, Any],
    manifest_expectations: dict[str, Any] | None,
) -> tuple[bool, list[str]]:
    if not manifest_expectations:
        return True, []
    errors: list[str] = []
    scenario_count = int(summary.get("scenario_count", 0))
    success_count = int(summary.get("successful_signing_run_count", 0))
    rejection_count = int(summary.get("matched_expected_intentional_rejection_count", 0))
    mismatch_count = int(summary.get("expected_outcome_mismatch_count", 0))
    crypto_failures = int(summary.get("cryptographic_validation_failure_count", 0))
    comparison_failures = int(summary.get("preview_output_comparison_failure_count", 0))
    annotation_mismatches = int(summary.get("annotation_rect_mismatch_count", 0))

    if "scenario_count" in manifest_expectations:
        expected = int(manifest_expectations["scenario_count"])
        if scenario_count != expected:
            errors.append(f"Expected {expected} scenarios, observed {scenario_count}.")
    if "minimum_successful_signing_run_count" in manifest_expectations:
        expected = int(manifest_expectations["minimum_successful_signing_run_count"])
        if success_count < expected:
            errors.append(
                f"Expected at least {expected} successful signings, observed {success_count}."
            )
    if "expected_intentional_rejection_count" in manifest_expectations:
        expected = int(manifest_expectations["expected_intentional_rejection_count"])
        if rejection_count != expected:
            errors.append(
                "Expected "
                f"{expected} intentional rejections, observed {rejection_count}."
            )
    if manifest_expectations.get("require_zero_cryptographic_validation_failures") is True:
        if crypto_failures != 0:
            errors.append(
                "Expected zero cryptographic validation failures, observed "
                f"{crypto_failures}."
            )
    if manifest_expectations.get("require_zero_preview_output_comparison_failures") is True:
        if comparison_failures != 0:
            errors.append(
                "Expected zero preview/output comparison failures, observed "
                f"{comparison_failures}."
            )
    if manifest_expectations.get("require_zero_annotation_rect_mismatches") is True:
        if annotation_mismatches != 0:
            errors.append(
                f"Expected zero annotation rect mismatches, observed {annotation_mismatches}."
            )
    if mismatch_count != 0:
        errors.append(
            f"Expected zero per-scenario expectation mismatches, observed {mismatch_count}."
        )
    return not errors, errors


def _apply_preview_matrix_scenario(
    *,
    shell: Any,
    scenario: dict[str, Any],
    profile_store: SignaturePresetCatalogStore,
) -> None:
    catalog = profile_store.load_catalog()
    profile_name = scenario.get("profile_name")
    if profile_name is not None:
        if not isinstance(profile_name, str) or not profile_name.strip():
            raise ValueError("Scenario 'profile_name' must be a non-empty string.")
        preset = catalog.profile_named(profile_name)
        base_appearance = preset.appearance
    else:
        base_appearance = (
            shell.properties_panel._workflow.current_signature_appearance or SignatureAppearance()
        )
    appearance = _apply_appearance_overrides(
        base_appearance,
        scenario.get("appearance_overrides"),
    )
    shell.properties_panel.set_signature_appearance(appearance)
    if "timestamp_required" in scenario:
        shell.properties_panel._workflow.timestamp_required = bool(
            scenario["timestamp_required"]
        )
    signature_rect_payload = scenario.get("signature_rect")
    if signature_rect_payload is not None:
        signature_rect = _signature_rect_from_payload(signature_rect_payload)
        shell.properties_panel.set_signature_rect(signature_rect)
        viewer_workflow = getattr(shell, "_viewer_workflow", None)
        viewer_widget = getattr(shell, "_viewer_widget", None)
        if viewer_workflow is not None and hasattr(viewer_workflow, "jump_to_page"):
            viewer_workflow.jump_to_page(signature_rect.page_index)
        refresh = getattr(viewer_widget, "refresh", None)
        if callable(refresh):
            refresh(navigation=True)
        sync_placement = getattr(shell, "_sync_placement_context_from_viewer", None)
        if callable(sync_placement):
            sync_placement()
        sync_overlay = getattr(shell, "_sync_signature_overlay", None)
        if callable(sync_overlay):
            sync_overlay()
        refresh_sign_button = getattr(shell, "_refresh_sign_button_state", None)
        if callable(refresh_sign_button):
            refresh_sign_button()
    shell.refresh_viewer()
    app = _widget_application(shell)
    if app is not None and hasattr(app, "processEvents"):
        app.processEvents()


def _signature_rect_from_payload(payload: object) -> SignatureRect:
    if not isinstance(payload, dict):
        raise ValueError("Scenario 'signature_rect' must be an object.")
    return SignatureRect(
        page_index=int(payload["page_index"]),
        left_pt=float(payload["left_pt"]),
        bottom_pt=float(payload["bottom_pt"]),
        width_pt=float(payload["width_pt"]),
        height_pt=float(payload["height_pt"]),
    )


def _apply_appearance_overrides(
    appearance: SignatureAppearance,
    overrides: object,
) -> SignatureAppearance:
    if overrides is None:
        return appearance
    if not isinstance(overrides, dict):
        raise ValueError("Scenario 'appearance_overrides' must be an object.")

    updated = appearance
    direct_updates: dict[str, Any] = {}
    enum_mappings = {
        "layout_template": SignatureLayoutTemplate,
        "stamp_position": SignatureStampPosition,
        "timezone_display_mode": SignatureTimezoneDisplayMode,
    }
    fixture_profile = overrides.get("fixture_profile")
    if fixture_profile is not None:
        if not isinstance(fixture_profile, str) or not fixture_profile.strip():
            raise ValueError("Scenario 'fixture_profile' must be a non-empty string.")
        updated = apply_preview_stress_fixture_profile(
            appearance=updated,
            profile_name=fixture_profile,
        )

    for key in (
        "signer_label_prefix",
        "show_field_names",
        "datetime_format",
        "image_stamp_path",
    ):
        if key in overrides:
            direct_updates[key] = overrides[key]
    for key, enum_cls in enum_mappings.items():
        if key in overrides:
            direct_updates[key] = enum_cls(str(overrides[key]))
    if direct_updates:
        updated = replace(updated, **direct_updates)
    if "text_style" in overrides:
        updated = replace(
            updated,
            text_style=_apply_text_style_overrides(updated.text_style, overrides["text_style"]),
        )
    if "box_style" in overrides:
        updated = replace(
            updated,
            box_style=_apply_box_style_overrides(updated.box_style, overrides["box_style"]),
        )
    if "visible_fields" in overrides:
        updated = _apply_visible_fields_override(updated, overrides["visible_fields"])
    return updated


def _apply_text_style_overrides(style: SignatureTextStyle, overrides: object) -> SignatureTextStyle:
    if not isinstance(overrides, dict):
        raise ValueError("Scenario 'text_style' overrides must be an object.")
    allowed: dict[str, Any] = {}
    for key in ("font_family", "font_size_pt", "bold", "italic", "text_color_hex"):
        if key in overrides:
            allowed[key] = overrides[key]
    return replace(style, **allowed)


def _apply_box_style_overrides(style: SignatureBoxStyle, overrides: object) -> SignatureBoxStyle:
    if not isinstance(overrides, dict):
        raise ValueError("Scenario 'box_style' overrides must be an object.")
    allowed: dict[str, Any] = {}
    for key in ("show_border", "border_color_hex", "border_width_pt", "background_color_hex"):
        if key in overrides:
            allowed[key] = overrides[key]
    return replace(style, **allowed)


def _apply_visible_fields_override(
    appearance: SignatureAppearance,
    visible_fields: object,
) -> SignatureAppearance:
    if not isinstance(visible_fields, list) or not visible_fields:
        raise ValueError("Scenario 'visible_fields' must be a non-empty array.")

    visible_keys = {
        _signature_field_key_from_manifest_value(value)
        for value in visible_fields
    }
    updates: dict[str, Any] = {}
    for field_key in appearance.field_order:
        binding = appearance.binding_for(field_key)
        if field_key in visible_keys:
            source = binding.source
            if source == SignatureFieldSource.HIDDEN:
                source = SignatureFieldSource.DERIVED
            updates[field_key.value] = SignatureFieldBinding(
                source=source,
                show_in_visible_appearance=True,
                override_text=(
                    binding.override_text
                    if source == SignatureFieldSource.OVERRIDE
                    else None
                ),
                display_label=binding.display_label,
            )
            continue
        updates[field_key.value] = SignatureFieldBinding(
            source=SignatureFieldSource.HIDDEN,
            show_in_visible_appearance=False,
            display_label=binding.display_label,
        )
    return replace(appearance, **updates)


def _signature_field_key_from_manifest_value(value: object) -> SignatureFieldKey:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Scenario field names must be non-empty strings.")
    return SignatureFieldKey(value)


def _capture_preview_render(
    *,
    shell: Any,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
) -> dict[str, Any]:
    controls = shell.properties_panel.preview_controls
    card_container = controls.card_container
    single_body = controls.single_body_container
    multi_body = controls.multi_body_container
    detail_label = controls.detail_label
    stamp_label = controls.stamp_label
    multi_detail = controls.multi_detail_label
    multi_stamp = controls.multi_stamp_label
    canonical_snapshot = getattr(card_container, "_canonical_preview_snapshot", None)
    analysis_snapshot = None
    image_path = None
    analysis_image_path = None
    image_error = None
    analysis_text_widget_bounds = None
    target_dir = None
    if artifacts_dir is not None:
        target_dir = Path(artifacts_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        image_path = str(target_dir / f"{artifact_basename}.png")
        if canonical_snapshot is not None:
            shutil.copyfile(canonical_snapshot.image_path, image_path)
            analysis_snapshot = render_canonical_signature_preview(
                preview,
                zoom=1.0,
                render_backend=getattr(
                    shell.properties_panel,
                    "_canonical_preview_render_backend",
                    None,
                ),
                include_border=True,
                flatten_to_white=True,
            )
            if analysis_snapshot is not None:
                analysis_image_path = str(target_dir / f"{artifact_basename}_analysis.png")
                shutil.copyfile(analysis_snapshot.image_path, analysis_image_path)
                analysis_text_widget_bounds = analysis_snapshot.text_area_bounds_px
            else:
                analysis_image_path = str(target_dir / f"{artifact_basename}_analysis.png")
                _flatten_preview_image_to_white(
                    source_path=canonical_snapshot.image_path,
                    output_path=analysis_image_path,
                )
        else:
            image_error = _write_widget_capture_png(card_container, image_path)
            analysis_image_path = image_path

    use_single_body = _widget_is_visible(single_body)
    active_body = single_body if use_single_body else multi_body
    active_detail = detail_label if use_single_body else multi_detail
    active_stamp = stamp_label if use_single_body else multi_stamp

    body_bounds = _widget_rect_snapshot(active_body)
    detail_bounds = _widget_rect_snapshot(active_detail)
    stamp_bounds = _widget_rect_snapshot(active_stamp)
    card_bounds = _widget_rect_snapshot(card_container)
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
    body_bounds = _widget_rect_snapshot_relative_to(card_container, active_body) or body_bounds
    text_widget_bounds = _widget_rect_snapshot_relative_to(card_container, active_detail)
    stamp_band_bounds = _widget_rect_snapshot_relative_to(card_container, active_stamp)
    if canonical_snapshot is not None:
        body_bounds = image_card_bounds
        text_widget_bounds = canonical_snapshot.text_area_bounds_px
        stamp_band_bounds = canonical_snapshot.stamp_area_bounds_px
    stamp_alignment = _label_alignment_snapshot(active_stamp)
    stamp_pixmap_size = _label_pixmap_size_snapshot(active_stamp)
    stamp_pixmap_bounds = _project_pixmap_bounds_within_label(
        label_bounds=stamp_band_bounds,
        pixmap_size=stamp_pixmap_size,
        alignment=stamp_alignment,
    )
    stamp_source_analysis = _analyze_stamp_source_image(preview.image_stamp_path)
    stamp_content_bounds = _project_content_bounds_to_preview(
        source_image_size=stamp_source_analysis.get("stamp_source_image_size_px"),
        source_content_bounds=stamp_source_analysis.get("stamp_source_content_bounds_px"),
        pixmap_bounds=stamp_pixmap_bounds,
    )
    if canonical_snapshot is not None:
        stamp_content_bounds = canonical_snapshot.stamp_bounds_px
        stamp_pixmap_bounds = canonical_snapshot.stamp_bounds_px
        if canonical_snapshot.stamp_bounds_px is not None:
            stamp_pixmap_size = {
                "width": canonical_snapshot.stamp_bounds_px["width"],
                "height": canonical_snapshot.stamp_bounds_px["height"],
            }
    stamp_diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds=stamp_band_bounds,
        stamp_pixmap_bounds=stamp_pixmap_bounds,
        stamp_content_bounds=stamp_content_bounds,
    )
    text_rendered_content_bounds = None
    text_rendered_line_bounds: tuple[dict[str, int], ...] = ()
    text_structural_content_bounds = None
    text_structural_line_bounds: tuple[dict[str, int], ...] = ()
    text_content_error = None
    text_reference_content_bounds = None
    text_reference_error = None
    text_line_detection_error = None
    if canonical_snapshot is not None:
        text_structural_content_bounds = canonical_snapshot.text_bounds_px
        text_reference_content_bounds = canonical_snapshot.text_bounds_px
        base_snapshot = getattr(canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is not None:
            text_structural_line_bounds = tuple(base_snapshot.line_bounds_px or ())
    elif text_widget_bounds is not None:
        text_reference_content_bounds, text_reference_error = _reference_text_content_bounds(
            source_label=active_detail,
            text_color_rgba=_preview_text_color_rgba(preview),
        )
    analysis_text_image_path = analysis_image_path or image_path
    analysis_detection_bounds = analysis_text_widget_bounds or text_widget_bounds
    if (
        analysis_text_image_path is not None
        and image_error is None
        and analysis_detection_bounds is not None
    ):
        text_rendered_content_bounds, text_content_error = _detect_text_content_bounds_in_preview(
            preview_image_path=analysis_text_image_path,
            text_widget_bounds=analysis_detection_bounds,
            text_color_rgba=_preview_text_color_rgba(preview),
            reference_text_content_bounds=text_reference_content_bounds,
        )
        if text_rendered_content_bounds is None and canonical_snapshot is not None:
            text_rendered_content_bounds = text_structural_content_bounds
    if (
        analysis_text_image_path is not None
        and image_error is None
        and analysis_detection_bounds is not None
    ):
        text_rendered_line_bounds, text_line_detection_error = _detect_text_line_bounds_in_preview(
            preview_image_path=analysis_text_image_path,
            text_widget_bounds=analysis_detection_bounds,
            text_color_rgba=_preview_text_color_rgba(preview),
            reference_text_content_bounds=text_reference_content_bounds,
        )
        if not text_rendered_line_bounds and canonical_snapshot is not None:
            text_rendered_line_bounds = text_structural_line_bounds
    text_diagnostics = _text_edge_diagnostics(
        preview=preview,
        card_bounds=image_card_bounds,
        text_widget_bounds=text_widget_bounds,
        text_content_bounds=text_rendered_content_bounds,
        reference_text_content_bounds=text_reference_content_bounds,
        stamp_band_bounds=stamp_band_bounds,
        stamp_content_bounds=stamp_content_bounds,
    )
    band_distances = _preview_edge_distances(
        preview=preview,
        card_bounds=card_bounds,
        body_bounds=body_bounds,
        detail_bounds=detail_bounds,
        stamp_bounds=stamp_bounds,
    )
    stamp_debug_image_path = None
    stamp_debug_image_error = None
    text_debug_image_path = None
    text_debug_image_error = None
    if (
        image_path is not None
        and image_error is None
        and stamp_band_bounds is not None
        and stamp_pixmap_bounds is not None
    ):
        stamp_debug_image_path = str(target_dir / f"{artifact_basename}_stamp_debug.png")
        stamp_debug_image_error = _write_stamp_debug_overlay(
            preview_image_path=image_path,
            output_path=stamp_debug_image_path,
            stamp_band_bounds=stamp_band_bounds,
            stamp_pixmap_bounds=stamp_pixmap_bounds,
            stamp_content_bounds=stamp_content_bounds,
            crop_padding=max(6, _preview_padding_for_capture(preview)),
        )
    if image_path is not None and image_error is None and text_widget_bounds is not None:
        text_debug_image_path = str(target_dir / f"{artifact_basename}_text_debug.png")
        text_debug_image_error = _write_text_debug_overlay(
            preview_image_path=image_path,
            output_path=text_debug_image_path,
            text_widget_bounds=text_widget_bounds,
            text_content_bounds=text_rendered_content_bounds,
            stamp_band_bounds=stamp_band_bounds,
            crop_padding=max(6, _preview_padding_for_capture(preview)),
        )
    text_widget_image_sha256 = _image_crop_sha256(
        preview_image_path=image_path,
        crop_bounds=text_widget_bounds,
    )
    font_diagnostics = _text_font_diagnostics(
        preview=preview,
        active_label=active_detail,
    )
    analysis_appearance_snapshot = None
    if canonical_snapshot is not None:
        base_snapshot = None
        if analysis_snapshot is not None:
            base_snapshot = getattr(analysis_snapshot, "appearance_snapshot", None)
        if base_snapshot is None:
            base_snapshot = getattr(canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is None:
            base_snapshot = SignatureAppearanceSnapshot(
                image_path=analysis_image_path,
                image_size_px=(
                    None
                    if image_card_bounds is None
                    else {
                        "width": image_card_bounds["width"],
                        "height": image_card_bounds["height"],
                    }
                ),
                container_bounds_px=image_card_bounds,
                border_bounds_px=image_card_bounds,
                border_style=(
                    None
                    if preview.box_style is None or not preview.box_style.show_border
                    else {
                        "show_border": True,
                        "shape": "rounded",
                        "border_color_hex": preview.box_style.border_color_hex,
                        "border_width_pt": preview.box_style.border_width_pt,
                        "background_color_hex": preview.box_style.background_color_hex,
                    }
                ),
                text_bounds_px=text_rendered_content_bounds,
                stamp_bounds_px=stamp_content_bounds,
                text_fragments=(),
                line_bounds_px=(),
            )
        analysis_appearance_snapshot = replace(
            base_snapshot,
            image_path=analysis_image_path or base_snapshot.image_path,
            line_bounds_px=base_snapshot.line_bounds_px or text_rendered_line_bounds,
        )
    _cleanup_canonical_preview_tempdir(analysis_snapshot)
    return {
        "preview_image_path": image_path,
        "analysis_preview_image_path": analysis_image_path,
        "analysis_appearance_snapshot": (
            None
            if analysis_appearance_snapshot is None
            else _jsonable_capture(analysis_appearance_snapshot)
        ),
        "preview_image_error": image_error,
        "card_bounds_px": card_bounds,
        "text_widget_bounds_px": text_widget_bounds,
        "single_body_bounds_px": _widget_rect_snapshot(single_body),
        "multi_body_bounds_px": _widget_rect_snapshot(multi_body),
        "detail_label_bounds_px": _widget_rect_snapshot(detail_label),
        "stamp_label_bounds_px": _widget_rect_snapshot(stamp_label),
        "multi_detail_bounds_px": _widget_rect_snapshot(multi_detail),
        "multi_stamp_bounds_px": _widget_rect_snapshot(multi_stamp),
        "detail_text_size_hint_px": _size_hint_snapshot(detail_label),
        "stamp_pixmap_size_px": stamp_pixmap_size,
        "layout_spacing_px": _layout_spacing(active_body),
        "preview_padding_px": _preview_padding_for_capture(preview),
        "edge_distances_px": band_distances,
        "text_debug_image_path": text_debug_image_path,
        "text_debug_image_error": text_debug_image_error,
        "text_widget_image_sha256": text_widget_image_sha256,
        "text_rendered_content_bounds_px": text_rendered_content_bounds,
        "text_structural_content_bounds_px": text_structural_content_bounds,
        "text_content_detection_error": text_content_error,
        "text_rendered_line_bounds_px": text_rendered_line_bounds,
        "text_structural_line_bounds_px": text_structural_line_bounds,
        "text_line_detection_error": text_line_detection_error,
        "text_reference_content_bounds_px": text_reference_content_bounds,
        "text_reference_detection_error": text_reference_error,
        **font_diagnostics,
        "stamp_debug_image_path": stamp_debug_image_path,
        "stamp_debug_image_error": stamp_debug_image_error,
        "stamp_band_bounds_px": stamp_band_bounds,
        "stamp_alignment": stamp_alignment,
        "stamp_rendered_pixmap_bounds_px": stamp_pixmap_bounds,
        "stamp_rendered_content_bounds_px": stamp_content_bounds,
        **stamp_source_analysis,
        **text_diagnostics,
        **stamp_diagnostics,
    }


def _capture_headless_preview_render(
    *,
    preview: Any,
    artifacts_dir: str | None,
    artifact_basename: str,
) -> dict[str, Any]:
    canonical_snapshot = render_canonical_signature_preview(preview)
    image_path = None
    analysis_image_path = None
    image_error = None
    target_dir = None
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
    text_rendered_line_bounds: tuple[dict[str, int], ...] = ()
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

    stamp_source_analysis = _analyze_stamp_source_image(preview.image_stamp_path)
    stamp_diagnostics = _stamp_edge_diagnostics(
        preview=preview,
        stamp_band_bounds=stamp_band_bounds,
        stamp_pixmap_bounds=stamp_pixmap_bounds,
        stamp_content_bounds=stamp_content_bounds,
    )
    text_structural_content_bounds = text_rendered_content_bounds
    text_structural_line_bounds: tuple[dict[str, int], ...] = ()
    if canonical_snapshot is not None:
        base_snapshot = getattr(canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is not None:
            text_structural_line_bounds = tuple(base_snapshot.line_bounds_px or ())
    text_content_error = None
    text_line_detection_error = None
    if image_path is not None and image_error is None and text_widget_bounds is not None:
        text_rendered_content_bounds, text_content_error = _detect_text_content_bounds_in_preview(
            preview_image_path=analysis_image_path or image_path,
            text_widget_bounds=text_widget_bounds,
            text_color_rgba=_preview_text_color_rgba(preview),
            reference_text_content_bounds=text_structural_content_bounds,
        )
        if text_rendered_content_bounds is None and canonical_snapshot is not None:
            text_rendered_content_bounds = text_structural_content_bounds
        text_rendered_line_bounds, text_line_detection_error = _detect_text_line_bounds_in_preview(
            preview_image_path=analysis_image_path or image_path,
            text_widget_bounds=text_widget_bounds,
            text_color_rgba=_preview_text_color_rgba(preview),
            reference_text_content_bounds=text_structural_content_bounds,
        )
        if not text_rendered_line_bounds and canonical_snapshot is not None:
            text_rendered_line_bounds = text_structural_line_bounds
    text_diagnostics = _text_edge_diagnostics(
        preview=preview,
        card_bounds=card_bounds,
        text_widget_bounds=text_widget_bounds,
        text_content_bounds=text_rendered_content_bounds,
        reference_text_content_bounds=text_rendered_content_bounds,
        stamp_band_bounds=stamp_band_bounds,
        stamp_content_bounds=stamp_content_bounds,
    )
    band_distances = _preview_edge_distances(
        preview=preview,
        card_bounds=card_bounds,
        body_bounds=card_bounds,
        detail_bounds=text_widget_bounds,
        stamp_bounds=stamp_band_bounds,
    )
    stamp_debug_image_path = None
    stamp_debug_image_error = None
    text_debug_image_path = None
    text_debug_image_error = None
    if (
        image_path is not None
        and image_error is None
        and stamp_band_bounds is not None
        and stamp_pixmap_bounds is not None
    ):
        stamp_debug_image_path = str(target_dir / f"{artifact_basename}_stamp_debug.png")
        stamp_debug_image_error = _write_stamp_debug_overlay(
            preview_image_path=image_path,
            output_path=stamp_debug_image_path,
            stamp_band_bounds=stamp_band_bounds,
            stamp_pixmap_bounds=stamp_pixmap_bounds,
            stamp_content_bounds=stamp_content_bounds,
            crop_padding=max(6, _preview_padding_for_capture(preview)),
        )
    if image_path is not None and image_error is None and text_widget_bounds is not None:
        text_debug_image_path = str(target_dir / f"{artifact_basename}_text_debug.png")
        text_debug_image_error = _write_text_debug_overlay(
            preview_image_path=image_path,
            output_path=text_debug_image_path,
            text_widget_bounds=text_widget_bounds,
            text_content_bounds=text_rendered_content_bounds,
            stamp_band_bounds=stamp_band_bounds,
            crop_padding=max(6, _preview_padding_for_capture(preview)),
        )
    text_widget_image_sha256 = _image_crop_sha256(
        preview_image_path=image_path,
        crop_bounds=text_widget_bounds,
    )
    font_diagnostics = _headless_text_font_diagnostics(preview)
    analysis_appearance_snapshot = None
    if canonical_snapshot is not None:
        base_snapshot = getattr(canonical_snapshot, "appearance_snapshot", None)
        if base_snapshot is None:
            base_snapshot = SignatureAppearanceSnapshot(
                image_path=analysis_image_path,
                image_size_px=(
                    None
                    if card_bounds is None
                    else {
                        "width": card_bounds["width"],
                        "height": card_bounds["height"],
                    }
                ),
                container_bounds_px=card_bounds,
                border_bounds_px=card_bounds,
                border_style=(
                    None
                    if preview.box_style is None or not preview.box_style.show_border
                    else {
                        "show_border": True,
                        "shape": "rounded",
                        "border_color_hex": preview.box_style.border_color_hex,
                        "border_width_pt": preview.box_style.border_width_pt,
                        "background_color_hex": preview.box_style.background_color_hex,
                    }
                ),
                text_bounds_px=text_rendered_content_bounds,
                stamp_bounds_px=stamp_content_bounds,
                text_fragments=(),
                line_bounds_px=(),
            )
        analysis_appearance_snapshot = replace(
            base_snapshot,
            image_path=analysis_image_path,
            line_bounds_px=base_snapshot.line_bounds_px or text_rendered_line_bounds,
        )
    _cleanup_canonical_preview_tempdir(canonical_snapshot)
    return {
        "preview_image_path": image_path,
        "analysis_preview_image_path": analysis_image_path,
        "analysis_appearance_snapshot": (
            None
            if analysis_appearance_snapshot is None
            else _jsonable_capture(analysis_appearance_snapshot)
        ),
        "preview_image_error": image_error,
        "card_bounds_px": card_bounds,
        "text_widget_bounds_px": text_widget_bounds,
        "single_body_bounds_px": card_bounds,
        "multi_body_bounds_px": card_bounds,
        "detail_label_bounds_px": text_widget_bounds,
        "stamp_label_bounds_px": stamp_band_bounds,
        "multi_detail_bounds_px": text_widget_bounds,
        "multi_stamp_bounds_px": stamp_band_bounds,
        "detail_text_size_hint_px": None,
        "stamp_pixmap_size_px": stamp_pixmap_size,
        "layout_spacing_px": 0,
        "preview_padding_px": _preview_padding_for_capture(preview),
        "edge_distances_px": band_distances,
        "text_debug_image_path": text_debug_image_path,
        "text_debug_image_error": text_debug_image_error,
        "text_widget_image_sha256": text_widget_image_sha256,
        "text_rendered_content_bounds_px": text_rendered_content_bounds,
        "text_structural_content_bounds_px": text_structural_content_bounds,
        "text_content_detection_error": text_content_error,
        "text_rendered_line_bounds_px": text_rendered_line_bounds,
        "text_structural_line_bounds_px": text_structural_line_bounds,
        "text_line_detection_error": text_line_detection_error,
        "text_reference_content_bounds_px": text_structural_content_bounds,
        "text_reference_detection_error": None,
        **font_diagnostics,
        "stamp_debug_image_path": stamp_debug_image_path,
        "stamp_debug_image_error": stamp_debug_image_error,
        "stamp_band_bounds_px": stamp_band_bounds,
        "stamp_alignment": None,
        "stamp_rendered_pixmap_bounds_px": stamp_pixmap_bounds,
        "stamp_rendered_content_bounds_px": stamp_content_bounds,
        **stamp_source_analysis,
        **text_diagnostics,
        **stamp_diagnostics,
    }


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
        return _single_line_vertical_outer_margin(
            box_height=max(1, int(round(preview.signature_rect.height_pt))),
            box_style=preview.box_style,
        )
    if preview.signature_rect is None or preview.stamp_position is None:
        return 6
    return _effective_layout_edge_margin(
        stamp_position=preview.stamp_position,
        box_height=max(1, int(round(preview.signature_rect.height_pt))),
        box_style=preview.box_style,
    )


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


def _draw_overlay_rect(
    draw: ImageDraw.ImageDraw,
    bounds: dict[str, int],
    color: tuple[int, ...],
) -> None:
    left = bounds["x"]
    top = bounds["y"]
    right = left + max(0, bounds["width"] - 1)
    bottom = top + max(0, bounds["height"] - 1)
    draw.rectangle((left, top, right, bottom), outline=color, width=2)


def _offset_rect(bounds: dict[str, int], *, dx: int, dy: int) -> dict[str, int]:
    return {
        "x": bounds["x"] + dx,
        "y": bounds["y"] + dy,
        "width": bounds["width"],
        "height": bounds["height"],
    }


def _widget_rect_snapshot(widget: Any) -> dict[str, int] | None:
    geometry = getattr(widget, "geometry", None)
    if callable(geometry):
        rect = geometry()
        x = getattr(rect, "x", None)
        y = getattr(rect, "y", None)
        width = getattr(rect, "width", None)
        height = getattr(rect, "height", None)
        if all(callable(item) for item in (x, y, width, height)):
            return {
                "x": int(x()),
                "y": int(y()),
                "width": int(width()),
                "height": int(height()),
            }
    size = getattr(widget, "fixed_size", None)
    if isinstance(size, tuple) and len(size) == 2:
        return {"x": 0, "y": 0, "width": int(size[0]), "height": int(size[1])}
    width = _widget_width(widget)
    height = None
    size_hint = getattr(widget, "sizeHint", None)
    if callable(size_hint):
        hint = size_hint()
        hint_height = getattr(hint, "height", None)
        if callable(hint_height):
            height = int(hint_height())
    if width is not None and height is not None:
        return {"x": 0, "y": 0, "width": int(width), "height": int(height)}
    return None


def _widget_width(widget: Any) -> int | None:
    width = getattr(widget, "width", None)
    if callable(width):
        value = width()
        if isinstance(value, int):
            return value
    fixed_width = getattr(widget, "fixed_width", None)
    if isinstance(fixed_width, int):
        return fixed_width
    return None


def _size_hint_snapshot(widget: Any) -> dict[str, int] | None:
    size_hint = getattr(widget, "sizeHint", None)
    if not callable(size_hint):
        return None
    hint = size_hint()
    width = getattr(hint, "width", None)
    height = getattr(hint, "height", None)
    if callable(width) and callable(height):
        return {"width": int(width()), "height": int(height())}
    return None


def _label_pixmap_size_snapshot(label: Any) -> dict[str, int] | None:
    pixmap = getattr(label, "pixmap", None)
    pixmap = pixmap() if callable(pixmap) else None
    if pixmap is None:
        return None
    width = getattr(pixmap, "width", None)
    height = getattr(pixmap, "height", None)
    if callable(width) and callable(height):
        return {"width": int(width()), "height": int(height())}
    return None


def _label_alignment_snapshot(label: Any) -> int | None:
    alignment = getattr(label, "alignment", None)
    if callable(alignment):
        value = alignment()
        if isinstance(value, int):
            return value
    if isinstance(alignment, int):
        return alignment
    return None


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


def _translate_child_bounds(
    parent_bounds: dict[str, int] | None,
    child_bounds: dict[str, int] | None,
) -> dict[str, int] | None:
    if parent_bounds is None or child_bounds is None:
        return None
    return {
        "x": parent_bounds["x"] + child_bounds["x"],
        "y": parent_bounds["y"] + child_bounds["y"],
        "width": child_bounds["width"],
        "height": child_bounds["height"],
    }


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


def _project_pixmap_bounds_within_label(
    *,
    label_bounds: dict[str, int] | None,
    pixmap_size: dict[str, int] | None,
    alignment: int | None,
) -> dict[str, int] | None:
    if label_bounds is None or pixmap_size is None:
        return None
    width = min(label_bounds["width"], pixmap_size["width"])
    height = min(label_bounds["height"], pixmap_size["height"])
    horizontal_space = max(0, label_bounds["width"] - width)
    vertical_space = max(0, label_bounds["height"] - height)
    x_offset = horizontal_space // 2
    y_offset = vertical_space // 2
    if alignment is not None:
        align_left = _qt_alignment_flag("AlignLeft")
        align_right = _qt_alignment_flag("AlignRight")
        align_top = _qt_alignment_flag("AlignTop")
        align_bottom = _qt_alignment_flag("AlignBottom")
        if alignment & align_left:
            x_offset = 0
        elif alignment & align_right:
            x_offset = horizontal_space
        if alignment & align_top:
            y_offset = 0
        elif alignment & align_bottom:
            y_offset = vertical_space
    return {
        "x": label_bounds["x"] + x_offset,
        "y": label_bounds["y"] + y_offset,
        "width": width,
        "height": height,
    }


def _analyze_stamp_source_image(image_path: str | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "stamp_source_image_size_px": None,
        "stamp_source_content_bounds_px": None,
        "stamp_source_content_error": None,
    }
    if not image_path:
        return result
    try:
        with Image.open(image_path) as image:
            width, height = image.size
            result["stamp_source_image_size_px"] = {"width": width, "height": height}
            alpha_bounds = image.convert("RGBA").getchannel("A").getbbox()
            if alpha_bounds is None:
                result["stamp_source_content_error"] = (
                    "Stamp source image contains no non-transparent pixels."
                )
                return result
            left, top, right, bottom = alpha_bounds
            result["stamp_source_content_bounds_px"] = {
                "x": int(left),
                "y": int(top),
                "width": int(right - left),
                "height": int(bottom - top),
            }
    except OSError as exc:
        result["stamp_source_content_error"] = f"Failed to open stamp source image: {exc}"
    return result


def _project_content_bounds_to_preview(
    *,
    source_image_size: dict[str, int] | None,
    source_content_bounds: dict[str, int] | None,
    pixmap_bounds: dict[str, int] | None,
) -> dict[str, int] | None:
    if source_image_size is None or source_content_bounds is None or pixmap_bounds is None:
        return None
    source_width = max(1, source_image_size["width"])
    source_height = max(1, source_image_size["height"])
    content_left = int(round(source_content_bounds["x"] * pixmap_bounds["width"] / source_width))
    content_top = int(round(source_content_bounds["y"] * pixmap_bounds["height"] / source_height))
    content_width = max(
        1,
        int(round(source_content_bounds["width"] * pixmap_bounds["width"] / source_width)),
    )
    content_height = max(
        1,
        int(round(source_content_bounds["height"] * pixmap_bounds["height"] / source_height)),
    )
    content_width = min(content_width, pixmap_bounds["width"] - content_left)
    content_height = min(content_height, pixmap_bounds["height"] - content_top)
    return {
        "x": pixmap_bounds["x"] + content_left,
        "y": pixmap_bounds["y"] + content_top,
        "width": max(1, content_width),
        "height": max(1, content_height),
    }


def _detect_text_content_bounds_in_preview(
    *,
    preview_image_path: str,
    text_widget_bounds: dict[str, int],
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None = None,
) -> tuple[dict[str, int] | None, str | None]:
    return detect_text_content_bounds_in_image(
        preview_image_path=preview_image_path,
        text_widget_bounds=text_widget_bounds,
        text_color_rgba=text_color_rgba,
        reference_text_content_bounds=reference_text_content_bounds,
    )


def _detect_text_line_bounds_in_preview(
    *,
    preview_image_path: str,
    text_widget_bounds: dict[str, int],
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None = None,
) -> tuple[tuple[dict[str, int], ...], str | None]:
    return detect_text_line_bounds_in_image(
        preview_image_path=preview_image_path,
        text_widget_bounds=text_widget_bounds,
        text_color_rgba=text_color_rgba,
        reference_text_content_bounds=reference_text_content_bounds,
    )


def _detect_text_geometry_in_preview(
    *,
    preview_image_path: str,
    text_widget_bounds: dict[str, int],
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None = None,
) -> tuple[dict[str, int] | None, tuple[dict[str, int], ...], str | None]:
    try:
        with Image.open(preview_image_path) as image:
            preview_image = image.convert("RGBA")
    except OSError as exc:
        return None, (), f"Failed to open preview image for text analysis: {exc}"

    image_width, image_height = preview_image.size
    crop_left = max(0, text_widget_bounds["x"])
    crop_top = max(0, text_widget_bounds["y"])
    crop_right = min(image_width, crop_left + max(0, text_widget_bounds["width"]))
    crop_bottom = min(image_height, crop_top + max(0, text_widget_bounds["height"]))
    if crop_right <= crop_left or crop_bottom <= crop_top:
        return None, (), "Text widget bounds do not intersect the captured preview image."

    cropped = preview_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    crop_width, crop_height = cropped.size
    candidate_pixels = _text_candidate_pixels_in_crop(
        cropped=cropped,
        crop_width=crop_width,
        crop_height=crop_height,
        text_color_rgba=text_color_rgba,
        reference_text_content_bounds=reference_text_content_bounds,
    )
    if not candidate_pixels:
        return None, (), "No rendered text pixels detected in the preview text widget."
    line_bounds = _line_bounds_from_candidate_pixels(
        candidate_pixels,
        crop_left=crop_left,
        crop_top=crop_top,
    )
    if not line_bounds:
        return None, (), "No rendered text pixels detected in the preview text widget."
    text_bounds = _union_rectangles(line_bounds)
    return text_bounds, line_bounds, None


def _text_candidate_pixels_in_crop(
    *,
    cropped: Image.Image,
    crop_width: int,
    crop_height: int,
    text_color_rgba: tuple[int, int, int, int] | None,
    reference_text_content_bounds: dict[str, int] | None,
) -> set[tuple[int, int]]:
    background = _estimate_crop_background_rgba(cropped)
    candidate_pixels: set[tuple[int, int]] = set()
    for y in range(crop_height):
        for x in range(crop_width):
            pixel = cropped.getpixel((x, y))
            if not _is_text_candidate_pixel(
                pixel,
                text_color_rgba=text_color_rgba,
                background_rgba=background,
            ):
                continue
            candidate_pixels.add((x, y))
    candidate_pixels = _filter_border_like_candidate_components(
        candidate_pixels,
        crop_width=crop_width,
        crop_height=crop_height,
    )
    return _restrict_candidates_to_reference_envelope(
        candidate_pixels,
        reference_text_content_bounds=reference_text_content_bounds,
        crop_width=crop_width,
        crop_height=crop_height,
    )


def _line_bounds_from_candidate_pixels(
    candidate_pixels: set[tuple[int, int]],
    *,
    crop_left: int,
    crop_top: int,
) -> tuple[dict[str, int], ...]:
    if not candidate_pixels:
        return ()
    row_values = sorted({y for _x, y in candidate_pixels})
    groups: list[list[int]] = [[row_values[0]]]
    for row in row_values[1:]:
        if row <= groups[-1][-1] + 2:
            groups[-1].append(row)
        else:
            groups.append([row])
    line_bounds: list[dict[str, int]] = []
    for group in groups:
        group_pixels = [(x, y) for x, y in candidate_pixels if group[0] <= y <= group[-1]]
        if not group_pixels:
            continue
        min_x = min(x for x, _y in group_pixels)
        max_x = max(x for x, _y in group_pixels)
        min_y = min(y for _x, y in group_pixels)
        max_y = max(y for _x, y in group_pixels)
        line_bounds.append(
            {
                "x": crop_left + min_x,
                "y": crop_top + min_y,
                "width": (max_x - min_x) + 1,
                "height": (max_y - min_y) + 1,
            }
        )
    return tuple(line_bounds)


def _union_rectangles(rectangles: tuple[dict[str, int], ...]) -> dict[str, int] | None:
    if not rectangles:
        return None
    min_x = min(rect["x"] for rect in rectangles)
    min_y = min(rect["y"] for rect in rectangles)
    max_x = max(rect["x"] + rect["width"] - 1 for rect in rectangles)
    max_y = max(rect["y"] + rect["height"] - 1 for rect in rectangles)
    return {
        "x": min_x,
        "y": min_y,
        "width": (max_x - min_x) + 1,
        "height": (max_y - min_y) + 1,
    }


def _restrict_candidates_to_reference_envelope(
    candidate_pixels: set[tuple[int, int]],
    *,
    reference_text_content_bounds: dict[str, int] | None,
    crop_width: int,
    crop_height: int,
) -> set[tuple[int, int]]:
    if not candidate_pixels or reference_text_content_bounds is None:
        return candidate_pixels
    pad = 4
    left = max(0, reference_text_content_bounds["x"] - pad)
    top = max(0, reference_text_content_bounds["y"] - pad)
    right = min(
        crop_width,
        reference_text_content_bounds["x"] + reference_text_content_bounds["width"] + pad,
    )
    bottom = min(
        crop_height,
        reference_text_content_bounds["y"] + reference_text_content_bounds["height"] + pad,
    )
    restricted = {
        (x, y)
        for x, y in candidate_pixels
        if left <= x < right and top <= y < bottom
    }
    return restricted or candidate_pixels


def _filter_border_like_candidate_components(
    candidate_pixels: set[tuple[int, int]],
    *,
    crop_width: int,
    crop_height: int,
) -> set[tuple[int, int]]:
    if not candidate_pixels:
        return candidate_pixels

    remaining = set(candidate_pixels)
    filtered: set[tuple[int, int]] = set()
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}
        while stack:
            x, y = stack.pop()
            for neighbor in (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            ):
                if neighbor not in remaining:
                    continue
                remaining.remove(neighbor)
                component.add(neighbor)
                stack.append(neighbor)
        if _component_looks_like_border_stroke(
            component,
            crop_width=crop_width,
            crop_height=crop_height,
        ):
            continue
        filtered.update(component)
    return filtered


def _component_looks_like_border_stroke(
    component: set[tuple[int, int]],
    *,
    crop_width: int,
    crop_height: int,
) -> bool:
    min_x = min(x for x, _y in component)
    max_x = max(x for x, _y in component)
    min_y = min(y for _x, y in component)
    max_y = max(y for _x, y in component)
    width = (max_x - min_x) + 1
    height = (max_y - min_y) + 1
    touches_left = min_x <= 0
    touches_right = max_x >= crop_width - 1
    touches_top = min_y <= 0
    touches_bottom = max_y >= crop_height - 1

    spans_full_width = width >= max(1, crop_width - 2)
    spans_full_height = height >= max(1, crop_height - 2)
    thin_horizontal = height <= 2 and spans_full_width and (touches_top or touches_bottom)
    thin_vertical = width <= 2 and spans_full_height and (touches_left or touches_right)
    return thin_horizontal or thin_vertical


def _reference_text_content_bounds(
    *,
    source_label: Any,
    text_color_rgba: tuple[int, int, int, int] | None,
) -> tuple[dict[str, int] | None, str | None]:
    widgets = importlib.import_module("PySide6.QtWidgets")
    qt_core = importlib.import_module("PySide6.QtCore")
    reference_label = getattr(widgets, "QLabel")()
    try:
        reference_label.setAttribute(
            getattr(qt_core.Qt.WidgetAttribute, "WA_DontShowOnScreen"),
            True,
        )
        reference_label.setText(source_label.text())
        reference_label.setFont(source_label.font())
        reference_label.setAlignment(source_label.alignment())
        reference_label.setWordWrap(source_label.wordWrap())
        reference_label.setTextFormat(source_label.textFormat())
        reference_label.setIndent(source_label.indent())
        reference_label.setMargin(source_label.margin())
        reference_label.setContentsMargins(source_label.contentsMargins())
        reference_label.setStyleSheet(source_label.styleSheet())
        reference_label.ensurePolished()

        if source_label.wordWrap():
            reference_width = max(1, source_label.width())
            reference_label.setFixedWidth(reference_width)
            reference_height = max(
                source_label.height(),
                reference_label.sizeHint().height(),
                source_label.sizeHint().height(),
            )
            reference_label.resize(reference_width, max(1, reference_height))
        else:
            reference_label.adjustSize()
            hint = reference_label.sizeHint()
            reference_width = max(source_label.width(), hint.width())
            reference_height = max(source_label.height(), hint.height())
            reference_label.resize(max(1, reference_width), max(1, reference_height))

        with NamedTemporaryFile(suffix=".png", delete=False) as handle:
            capture_path = handle.name
        try:
            capture_error = _write_widget_capture_png(reference_label, capture_path)
            if capture_error is not None:
                return None, capture_error
            return _detect_text_content_bounds_in_preview(
                preview_image_path=capture_path,
                text_widget_bounds={
                    "x": 0,
                    "y": 0,
                    "width": reference_label.width(),
                    "height": reference_label.height(),
                },
                text_color_rgba=text_color_rgba,
            )
        finally:
            Path(capture_path).unlink(missing_ok=True)
    finally:
        reference_label.deleteLater()


def _estimate_crop_background_rgba(image: Image.Image) -> tuple[int, int, int, int]:
    width, height = image.size
    if width <= 0 or height <= 0:
        return (255, 255, 255, 255)
    sample_points = {
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, 0),
        (width // 2, height - 1),
        (0, height // 2),
        (width - 1, height // 2),
    }
    samples = [image.getpixel(point) for point in sample_points]
    return tuple(
        int(round(sum(component[index] for component in samples) / len(samples)))
        for index in range(4)
    )


def _preview_text_color_rgba(preview: Any) -> tuple[int, int, int, int] | None:
    text_style = getattr(preview, "text_style", None)
    if text_style is None:
        return None
    color_hex = getattr(text_style, "text_color_hex", None)
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


def _is_text_candidate_pixel(
    pixel: tuple[int, int, int, int],
    *,
    text_color_rgba: tuple[int, int, int, int] | None,
    background_rgba: tuple[int, int, int, int],
) -> bool:
    if pixel[3] <= 0:
        return False
    pixel_luma = _rgba_luma(pixel)
    background_luma = _rgba_luma(background_rgba)
    if text_color_rgba is not None:
        text_distance = sum(abs(pixel[index] - text_color_rgba[index]) for index in range(3))
        if text_distance <= 150:
            return True
        return (background_luma - pixel_luma) >= 28
    color_distance = sum(abs(pixel[index] - background_rgba[index]) for index in range(3))
    return color_distance > 80 or (background_luma - pixel_luma) >= 28


def _rgba_luma(pixel: tuple[int, int, int, int]) -> int:
    return int(round((pixel[0] * 299 + pixel[1] * 587 + pixel[2] * 114) / 1000))


def _rect_edge_distances(
    *,
    outer_bounds: dict[str, int] | None,
    inner_bounds: dict[str, int] | None,
) -> dict[str, int] | None:
    if outer_bounds is None or inner_bounds is None:
        return None
    outer_right = outer_bounds["x"] + outer_bounds["width"]
    outer_bottom = outer_bounds["y"] + outer_bounds["height"]
    inner_right = inner_bounds["x"] + inner_bounds["width"]
    inner_bottom = inner_bounds["y"] + inner_bounds["height"]
    return {
        "left": inner_bounds["x"] - outer_bounds["x"],
        "top": inner_bounds["y"] - outer_bounds["y"],
        "right": outer_right - inner_right,
        "bottom": outer_bottom - inner_bottom,
    }


def _stamp_edge_diagnostics(
    *,
    preview: Any,
    stamp_band_bounds: dict[str, int] | None,
    stamp_pixmap_bounds: dict[str, int] | None,
    stamp_content_bounds: dict[str, int] | None,
) -> dict[str, Any]:
    # Rendered stamp content bounds already include anti-aliased edge pixels, so
    # a remaining 1px border-facing gap is visually acceptable. Only actual
    # border contact is treated as a stamp warning; explicit edge-touch remains
    # separately reported.
    warning_threshold = 0

    pixmap_distances = _rect_edge_distances(
        outer_bounds=stamp_band_bounds,
        inner_bounds=stamp_pixmap_bounds,
    )
    content_distances = _rect_edge_distances(
        outer_bounds=stamp_band_bounds,
        inner_bounds=stamp_content_bounds,
    )

    relevant_content_distances = _relevant_stamp_edge_distances(
        layout_template=getattr(preview, "layout_template", None),
        stamp_position=getattr(preview, "stamp_position", None),
        edge_distances=content_distances,
    )

    def _min_distance(distances: dict[str, int] | None) -> int | None:
        if distances is None:
            return None
        return min(distances.values())

    pixmap_min_distance = _min_distance(pixmap_distances)
    content_min_distance = _min_distance(relevant_content_distances)
    return {
        "stamp_pixmap_edge_distances_px": pixmap_distances,
        "stamp_content_edge_distances_px": content_distances,
        "stamp_pixmap_touches_band_edge": (
            None if pixmap_min_distance is None else pixmap_min_distance <= 0
        ),
        "stamp_content_touches_band_edge": (
            None if content_min_distance is None else content_min_distance <= 0
        ),
        "stamp_content_warning_threshold_px": warning_threshold,
        "stamp_pixmap_min_edge_distance_px": pixmap_min_distance,
        "stamp_content_min_edge_distance_px": content_min_distance,
        "stamp_content_within_warning_distance": (
            None if content_min_distance is None else content_min_distance <= warning_threshold
        ),
    }


def _text_edge_diagnostics(
    *,
    preview: Any,
    card_bounds: dict[str, int] | None,
    text_widget_bounds: dict[str, int] | None,
    text_content_bounds: dict[str, int] | None,
    reference_text_content_bounds: dict[str, int] | None,
    stamp_band_bounds: dict[str, int] | None,
    stamp_content_bounds: dict[str, int] | None,
) -> dict[str, Any]:
    widget_distances = _rect_edge_distances(
        outer_bounds=text_widget_bounds,
        inner_bounds=text_content_bounds,
    )
    border_distances = _rect_edge_distances(
        outer_bounds=card_bounds,
        inner_bounds=text_content_bounds,
    )
    border_edge, stamp_edge = _text_widget_edge_roles(
        stamp_position=getattr(preview, "stamp_position", None),
    )
    border_facing_distance = None if widget_distances is None else widget_distances.get(border_edge)
    stamp_facing_distance = None if widget_distances is None else widget_distances.get(stamp_edge)
    width_loss_tolerance_px = 3
    height_loss_tolerance_px = 1
    raster_tolerance_px = 3
    stamp_band_overlap = _rectangles_overlap_exceeds_tolerance(
        text_content_bounds,
        stamp_band_bounds,
        tolerance_px=raster_tolerance_px,
    )
    stamp_content_overlap = _rectangles_overlap_exceeds_tolerance(
        text_content_bounds,
        stamp_content_bounds,
        tolerance_px=raster_tolerance_px,
    )
    widget_min_distance = None if widget_distances is None else min(widget_distances.values())
    border_min_distance = None if border_distances is None else min(border_distances.values())
    touches_widget_edge = None if widget_min_distance is None else widget_min_distance <= 0
    touches_border_edge = None if border_min_distance is None else border_min_distance <= 0
    reference_width_loss = None
    reference_height_loss = None
    if text_content_bounds is not None and reference_text_content_bounds is not None:
        reference_width_loss = max(
            0,
            reference_text_content_bounds["width"] - text_content_bounds["width"],
        )
        reference_height_loss = max(
            0,
            reference_text_content_bounds["height"] - text_content_bounds["height"],
        )
    clipped_from_reference = None
    if reference_width_loss is not None and reference_height_loss is not None:
        clipped_from_reference = (
            reference_width_loss > width_loss_tolerance_px
            or reference_height_loss > height_loss_tolerance_px
        )
    clipped_with_edge_contact = None
    if clipped_from_reference is not None:
        clipped_with_edge_contact = clipped_from_reference and (
            touches_widget_edge is True or touches_border_edge is True
        )
    return {
        "text_content_edge_distances_px": widget_distances,
        "text_content_border_edge_distances_px": border_distances,
        "text_content_min_edge_distance_px": widget_min_distance,
        "text_content_min_border_distance_px": border_min_distance,
        "text_content_reference_width_loss_px": reference_width_loss,
        "text_content_reference_height_loss_px": reference_height_loss,
        "text_content_reference_width_tolerance_px": width_loss_tolerance_px,
        "text_content_reference_height_tolerance_px": height_loss_tolerance_px,
        "text_content_border_facing_distance_px": border_facing_distance,
        "text_content_stamp_facing_distance_px": stamp_facing_distance,
        "text_content_touches_widget_edge": touches_widget_edge,
        "text_content_touches_border_facing_edge": (
            None if border_facing_distance is None else border_facing_distance <= 0
        ),
        "text_content_touches_stamp_facing_edge": (
            None if stamp_facing_distance is None else stamp_facing_distance <= 0
        ),
        "text_content_overlaps_stamp_band": stamp_band_overlap,
        "text_content_overlaps_stamp_content": stamp_content_overlap,
        "text_content_clipped_in_preview": (
            None
            if (
                clipped_from_reference is None
                and widget_min_distance is None
                and stamp_band_overlap is None
                and stamp_content_overlap is None
            )
            else (
                clipped_with_edge_contact is True
                or stamp_band_overlap is True
                or stamp_content_overlap is True
            )
        ),
    }


def _text_widget_edge_roles(
    *,
    stamp_position: SignatureStampPosition | None,
) -> tuple[str, str]:
    if stamp_position == SignatureStampPosition.TOP:
        return ("bottom", "top")
    if stamp_position == SignatureStampPosition.BOTTOM:
        return ("top", "bottom")
    if stamp_position == SignatureStampPosition.LEFT:
        return ("right", "left")
    return ("left", "right")


def _text_font_diagnostics(
    *,
    preview: Any,
    active_label: Any,
) -> dict[str, Any]:
    requested_family = None
    requested_size = None
    text_style = getattr(preview, "text_style", None)
    if text_style is not None:
        requested_family = getattr(text_style, "font_family", None)
        requested_size = getattr(text_style, "font_size_pt", None)
    effective_family = None
    effective_point_size = None
    font_getter = getattr(active_label, "font", None)
    if callable(font_getter):
        label_font = font_getter()
        family_getter = getattr(label_font, "family", None)
        if callable(family_getter):
            effective_family = family_getter()
        point_size_getter = getattr(label_font, "pointSizeF", None)
        if callable(point_size_getter):
            effective_point_size = point_size_getter()
    font_info_getter = getattr(active_label, "fontInfo", None)
    if callable(font_info_getter):
        font_info = font_info_getter()
        family_getter = getattr(font_info, "family", None)
        if callable(family_getter):
            effective_family = family_getter() or effective_family
        point_size_getter = getattr(font_info, "pointSizeF", None)
        if callable(point_size_getter):
            point_size = point_size_getter()
            if point_size and point_size > 0:
                effective_point_size = point_size
    requested_category = _font_family_category(str(requested_family or ""))
    effective_category = _font_family_category(str(effective_family or ""))
    direct_mapping_supported = preview_font_family_supported(str(requested_family or ""))
    return {
        "requested_text_font_family": requested_family,
        "requested_text_font_size_pt": requested_size,
        "effective_text_font_family": effective_family,
        "effective_text_font_point_size_pt": effective_point_size,
        "requested_text_font_category": requested_category,
        "effective_text_font_category": effective_category,
        "font_family_direct_preview_mapping_supported": direct_mapping_supported,
        "font_family_category_mismatch": (
            None
            if not requested_category or not effective_category
            else requested_category != effective_category
        ),
    }


def _headless_text_font_diagnostics(
    preview: Any,
) -> dict[str, Any]:
    requested_family = None
    requested_size = None
    text_style = getattr(preview, "text_style", None)
    if text_style is not None:
        requested_family = getattr(text_style, "font_family", None)
        requested_size = getattr(text_style, "font_size_pt", None)
    requested_category = _font_family_category(str(requested_family or ""))
    direct_mapping_supported = preview_font_family_supported(str(requested_family or ""))
    return {
        "requested_text_font_family": requested_family,
        "requested_text_font_size_pt": requested_size,
        "effective_text_font_family": requested_family,
        "effective_text_font_point_size_pt": requested_size,
        "requested_text_font_category": requested_category,
        "effective_text_font_category": requested_category,
        "font_family_direct_preview_mapping_supported": direct_mapping_supported,
        "font_family_category_mismatch": False if requested_category else None,
    }


def _font_family_category(font_family: str) -> str | None:
    normalized = font_family.strip().lower()
    if not normalized:
        return None
    normalized = re.sub(r"\s*\[[^\]]+\]\s*$", "", normalized)
    if any(
        token in normalized
        for token in (
            "sans serif",
            "sans-serif",
            "sans",
            "helvetica",
            "arial",
            "nimbus sans",
            "liberation sans",
            "dejavu sans",
            "noto sans",
            "source sans",
            "verdana",
        )
    ):
        return "sans_serif"
    if any(token in normalized for token in ("courier", "mono", "code", "consola", "menlo")):
        return "monospace"
    if any(
        token in normalized
        for token in (
            "fantasy",
            "decor",
            "display",
            "papyrus",
            "noto serif display",
        )
    ):
        return "fantasy"
    if any(
        token in normalized
        for token in (
            "times",
            "serif",
            "georgia",
            "garamond",
            "cambria",
            "baskerville",
            "liberation serif",
            "noto serif",
        )
    ):
        return "serif"
    if any(
        token in normalized
        for token in ("cursive", "script", "hand", "brush", "callig", "comic", "zapfino")
    ):
        return "cursive"
    return "unknown"


def _image_crop_sha256(
    *,
    preview_image_path: str | None,
    crop_bounds: dict[str, int] | None,
) -> str | None:
    if preview_image_path is None or crop_bounds is None:
        return None
    try:
        with Image.open(preview_image_path) as image:
            preview_image = image.convert("RGBA")
    except OSError:
        return None
    crop_left = max(0, crop_bounds["x"])
    crop_top = max(0, crop_bounds["y"])
    crop_right = min(preview_image.width, crop_left + max(0, crop_bounds["width"]))
    crop_bottom = min(preview_image.height, crop_top + max(0, crop_bounds["height"]))
    if crop_right <= crop_left or crop_bottom <= crop_top:
        return None
    cropped = preview_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    return hashlib.sha256(cropped.tobytes()).hexdigest()


def _flatten_preview_image_to_white(*, source_path: str, output_path: str) -> None:
    with Image.open(source_path) as image:
        rgba_image = image.convert("RGBA")
    flattened = Image.new("RGBA", rgba_image.size, (255, 255, 255, 255))
    flattened.alpha_composite(rgba_image)
    flattened.save(output_path)


def _image_crop_change_ratio(
    *,
    previous_image_path: str | None,
    previous_bounds: dict[str, int] | None,
    current_image_path: str | None,
    current_bounds: dict[str, int] | None,
) -> float | None:
    if (
        previous_image_path is None
        or previous_bounds is None
        or current_image_path is None
        or current_bounds is None
    ):
        return None
    if (
        previous_bounds["width"] != current_bounds["width"]
        or previous_bounds["height"] != current_bounds["height"]
    ):
        return None
    try:
        with Image.open(previous_image_path) as image:
            previous_image = image.convert("RGBA")
        with Image.open(current_image_path) as image:
            current_image = image.convert("RGBA")
    except OSError:
        return None
    previous_crop = previous_image.crop(
        (
            previous_bounds["x"],
            previous_bounds["y"],
            previous_bounds["x"] + previous_bounds["width"],
            previous_bounds["y"] + previous_bounds["height"],
        )
    )
    current_crop = current_image.crop(
        (
            current_bounds["x"],
            current_bounds["y"],
            current_bounds["x"] + current_bounds["width"],
            current_bounds["y"] + current_bounds["height"],
        )
    )
    total_pixels = previous_crop.width * previous_crop.height
    if total_pixels <= 0 or previous_crop.size != current_crop.size:
        return None
    changed_pixels = 0
    for y in range(previous_crop.height):
        for x in range(previous_crop.width):
            if previous_crop.getpixel((x, y)) != current_crop.getpixel((x, y)):
                changed_pixels += 1
    return changed_pixels / total_pixels


def _normalized_image_crop_change_ratio(
    *,
    previous_image_path: str | None,
    previous_bounds: dict[str, int] | None,
    current_image_path: str | None,
    current_bounds: dict[str, int] | None,
) -> float | None:
    if (
        previous_image_path is None
        or previous_bounds is None
        or current_image_path is None
        or current_bounds is None
    ):
        return None
    try:
        with Image.open(previous_image_path) as image:
            previous_image = image.convert("RGBA")
        with Image.open(current_image_path) as image:
            current_image = image.convert("RGBA")
    except OSError:
        return None

    previous_crop = previous_image.crop(
        (
            max(0, previous_bounds["x"]),
            max(0, previous_bounds["y"]),
            max(0, previous_bounds["x"]) + max(0, previous_bounds["width"]),
            max(0, previous_bounds["y"]) + max(0, previous_bounds["height"]),
        )
    )
    current_crop = current_image.crop(
        (
            max(0, current_bounds["x"]),
            max(0, current_bounds["y"]),
            max(0, current_bounds["x"]) + max(0, current_bounds["width"]),
            max(0, current_bounds["y"]) + max(0, current_bounds["height"]),
        )
    )
    if previous_crop.width <= 0 or previous_crop.height <= 0:
        return None
    if current_crop.width <= 0 or current_crop.height <= 0:
        return None
    target_width = max(previous_crop.width, current_crop.width)
    target_height = max(previous_crop.height, current_crop.height)
    if target_width <= 0 or target_height <= 0:
        return None
    previous_normalized = previous_crop.resize(
        (target_width, target_height), Image.Resampling.LANCZOS
    )
    current_normalized = current_crop.resize(
        (target_width, target_height), Image.Resampling.LANCZOS
    )
    total_pixels = target_width * target_height
    changed_pixels = 0
    for y in range(target_height):
        for x in range(target_width):
            if previous_normalized.getpixel((x, y)) != current_normalized.getpixel((x, y)):
                changed_pixels += 1
    return changed_pixels / total_pixels


def _aspect_ratio_delta(
    previous_width: int,
    previous_height: int,
    current_width: int,
    current_height: int,
) -> float | None:
    if previous_width <= 0 or previous_height <= 0:
        return None
    if current_width <= 0 or current_height <= 0:
        return None
    previous_ratio = previous_width / previous_height
    current_ratio = current_width / current_height
    return abs(previous_ratio - current_ratio) / max(previous_ratio, current_ratio)


def _write_side_by_side_comparison(
    *,
    preview_image_path: str | None,
    preview_bounds: dict[str, int] | None,
    signed_image_path: str | None,
    signed_bounds: dict[str, int] | None,
    output_path: str,
) -> str | None:
    if (
        preview_image_path is None
        or preview_bounds is None
        or signed_image_path is None
        or signed_bounds is None
    ):
        return (
            "Signed-output comparison is unavailable because preview or signed crop "
            "evidence is missing."
        )
    try:
        with Image.open(preview_image_path) as image:
            preview_image = image.convert("RGBA")
        with Image.open(signed_image_path) as image:
            signed_image = image.convert("RGBA")
    except OSError as exc:
        return f"Failed to open images for comparison overlay: {exc}"

    preview_crop = preview_image.crop(
        (
            max(0, preview_bounds["x"]),
            max(0, preview_bounds["y"]),
            max(0, preview_bounds["x"]) + max(0, preview_bounds["width"]),
            max(0, preview_bounds["y"]) + max(0, preview_bounds["height"]),
        )
    )
    signed_crop = signed_image.crop(
        (
            max(0, signed_bounds["x"]),
            max(0, signed_bounds["y"]),
            max(0, signed_bounds["x"]) + max(0, signed_bounds["width"]),
            max(0, signed_bounds["y"]) + max(0, signed_bounds["height"]),
        )
    )
    spacer = 12
    width = preview_crop.width + signed_crop.width + spacer
    height = max(preview_crop.height, signed_crop.height)
    canvas = Image.new("RGBA", (width, height), color=(255, 255, 255, 255))
    canvas.paste(preview_crop, (0, 0))
    canvas.paste(signed_crop, (preview_crop.width + spacer, 0))
    canvas.save(output_path)
    return None


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


def _analyze_capture_state_transitions(
    states: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], ...]:
    diagnostics: list[dict[str, Any]] = []
    for index in range(1, len(states)):
        previous = states[index - 1]
        current = states[index]
        previous_preview = previous.get("preview_snapshot") if isinstance(previous, dict) else None
        current_preview = current.get("preview_snapshot") if isinstance(current, dict) else None
        if not isinstance(previous_preview, dict) or not isinstance(current_preview, dict):
            continue
        previous_style = previous_preview.get("text_style") or {}
        current_style = current_preview.get("text_style") or {}
        previous_render = previous_preview.get("render_capture") or {}
        current_render = current_preview.get("render_capture") or {}
        if _normalized_preview_text_for_transition(previous.get("preview_text")) != (
            _normalized_preview_text_for_transition(current.get("preview_text"))
        ):
            continue
        if (
            previous_preview.get("layout_template") != current_preview.get("layout_template")
            or previous_preview.get("stamp_position") != current_preview.get("stamp_position")
            or previous_preview.get("signature_rect") != current_preview.get("signature_rect")
        ):
            continue
        change_ratio = _image_crop_change_ratio(
            previous_image_path=previous_render.get("preview_image_path"),
            previous_bounds=previous_render.get("text_widget_bounds_px"),
            current_image_path=current_render.get("preview_image_path"),
            current_bounds=current_render.get("text_widget_bounds_px"),
        )
        same_bounds = (
            previous_render.get("text_rendered_content_bounds_px")
            == current_render.get("text_rendered_content_bounds_px")
            and previous_render.get("text_rendered_content_bounds_px") is not None
        )
        if (
            previous_style.get("font_size_pt") != current_style.get("font_size_pt")
            and same_bounds
            and change_ratio is not None
            and change_ratio < 0.005
        ):
            diagnostics.append(
                {
                    "from_capture_label": previous.get("capture_label"),
                    "to_capture_label": current.get("capture_label"),
                    "issue_code": "font_size_change_had_negligible_visual_effect",
                    "previous_font_size_pt": previous_style.get("font_size_pt"),
                    "current_font_size_pt": current_style.get("font_size_pt"),
                    "changed_pixel_ratio": round(change_ratio, 6),
                }
            )
        if (
            previous_style.get("font_family") != current_style.get("font_family")
            and previous_render.get("effective_text_font_category")
            == current_render.get("effective_text_font_category")
            and change_ratio is not None
            and change_ratio < 0.01
        ):
            diagnostics.append(
                {
                    "from_capture_label": previous.get("capture_label"),
                    "to_capture_label": current.get("capture_label"),
                    "issue_code": "font_family_change_had_negligible_visual_effect",
                    "previous_font_family": previous_style.get("font_family"),
                    "current_font_family": current_style.get("font_family"),
                    "effective_text_font_category": current_render.get(
                        "effective_text_font_category"
                    ),
                    "changed_pixel_ratio": round(change_ratio, 6),
                }
            )
    return tuple(diagnostics)


def _normalized_preview_text_for_transition(preview_text: Any) -> str:
    text = str(preview_text or "")
    return re.sub(
        r"\b\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?(?:\s+[A-Z]{2,5})?\b",
        "<signing_time>",
        text,
    )


def _normalize_visible_text_for_comparison(text: Any) -> str:
    normalized = _normalized_preview_text_for_transition(text)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _rectangles_intersect(
    first: dict[str, int] | None,
    second: dict[str, int] | None,
) -> bool | None:
    if first is None or second is None:
        return None
    first_right = first["x"] + first["width"]
    first_bottom = first["y"] + first["height"]
    second_right = second["x"] + second["width"]
    second_bottom = second["y"] + second["height"]
    return not (
        first_right <= second["x"]
        or second_right <= first["x"]
        or first_bottom <= second["y"]
        or second_bottom <= first["y"]
    )


def _rectangles_overlap_exceeds_tolerance(
    first: dict[str, int] | None,
    second: dict[str, int] | None,
    *,
    tolerance_px: int,
) -> bool | None:
    if first is None or second is None:
        return None
    if not _rectangles_intersect(first, second):
        return False
    overlap_left = max(first["x"], second["x"])
    overlap_top = max(first["y"], second["y"])
    overlap_right = min(first["x"] + first["width"], second["x"] + second["width"])
    overlap_bottom = min(first["y"] + first["height"], second["y"] + second["height"])
    overlap_width = max(0, overlap_right - overlap_left)
    overlap_height = max(0, overlap_bottom - overlap_top)
    return overlap_width > tolerance_px and overlap_height > tolerance_px


def _relevant_stamp_edge_distances(
    *,
    layout_template: SignatureLayoutTemplate | None,
    stamp_position: SignatureStampPosition | None,
    edge_distances: dict[str, int] | None,
) -> dict[str, int] | None:
    if edge_distances is None:
        return None
    # Stamp warnings are about crowding against the signature border. Text-facing
    # crowding is covered by the text overlap/clipping diagnostics instead of
    # inferring it indirectly from stamp-band geometry.
    if stamp_position == SignatureStampPosition.TOP:
        return {"top": edge_distances["top"]}
    if stamp_position == SignatureStampPosition.BOTTOM:
        return {"bottom": edge_distances["bottom"]}
    if stamp_position == SignatureStampPosition.LEFT:
        return {"left": edge_distances["left"]}
    if stamp_position == SignatureStampPosition.RIGHT:
        return {"right": edge_distances["right"]}
    return dict(edge_distances)


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


def _preview_edge_distances(
    *,
    preview: Any,
    card_bounds: dict[str, int] | None,
    body_bounds: dict[str, int] | None,
    detail_bounds: dict[str, int] | None,
    stamp_bounds: dict[str, int] | None,
) -> dict[str, Any]:
    padding = _preview_padding_for_capture(preview)
    result = {
        "preview_padding_px": padding,
        "text_top_to_border_px": None,
        "text_bottom_to_border_px": None,
        "stamp_top_to_border_px": None,
        "stamp_bottom_to_border_px": None,
        "content_top_to_border_px": None,
        "content_bottom_to_border_px": None,
    }
    if card_bounds is None or body_bounds is None:
        return result
    body_top = body_bounds["y"]
    card_height = card_bounds["height"]
    if detail_bounds is not None:
        detail_top = body_top + detail_bounds["y"]
        detail_bottom = detail_top + detail_bounds["height"]
        result["text_top_to_border_px"] = detail_top
        result["text_bottom_to_border_px"] = max(0, card_height - detail_bottom)
    if stamp_bounds is not None:
        stamp_top = body_top + stamp_bounds["y"]
        stamp_bottom = stamp_top + stamp_bounds["height"]
        result["stamp_top_to_border_px"] = stamp_top
        result["stamp_bottom_to_border_px"] = max(0, card_height - stamp_bottom)
    content_tops = [
        value
        for value in (
            result["text_top_to_border_px"],
            result["stamp_top_to_border_px"],
        )
        if value is not None
    ]
    content_bottoms = [
        value
        for value in (
            result["text_bottom_to_border_px"],
            result["stamp_bottom_to_border_px"],
        )
        if value is not None
    ]
    if content_tops:
        result["content_top_to_border_px"] = min(content_tops)
    if content_bottoms:
        result["content_bottom_to_border_px"] = min(content_bottoms)
    return result


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
    if snapshot is None:
        return []
    fragments = snapshot.get("appearance_text_fragments")
    if isinstance(fragments, list):
        return [str(item) for item in fragments if isinstance(item, str)]
    fragments = snapshot.get("text_fragments")
    if isinstance(fragments, list):
        return [str(item) for item in fragments if isinstance(item, str)]
    return []


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
    if snapshot is None:
        return None
    render_capture = snapshot.get("render_capture")
    if not isinstance(render_capture, dict):
        return None
    distances = render_capture.get("edge_distances_px")
    if not isinstance(distances, dict):
        return None
    value = distances.get(key)
    return value if isinstance(value, int) else None


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


def _snapshot_current_draft_request(workflow: SigningDraftWorkflow) -> SigningRequest | None:
    signature_rect = workflow.current_signature_rect
    signature_appearance = workflow.current_signature_appearance
    if signature_rect is None or signature_appearance is None:
        return None
    return SigningRequest(
        input_pdf_path=workflow.input_pdf_path,
        output_pdf_path=workflow.output_pdf_path,
        certificate_path=workflow.certificate_path,
        passphrase=workflow.passphrase,
        tsa_url=workflow.tsa_url,
        timestamp_required=workflow.timestamp_required,
        trust_policy=workflow.trust_policy,
        certificate_alias=workflow.certificate_alias,
        signature_rect=signature_rect,
        signature_appearance=signature_appearance,
    )


def _snapshot_backend_reservation(request: SigningRequest) -> dict[str, Any] | None:
    if request.signature_rect is None or request.signature_appearance is None:
        return None

    appearance = SigningBackendAppearance.from_signature_appearance(
        request.signature_appearance
    )
    snapshot = {
        "layout_template": appearance.layout_template.value,
        "stamp_position": appearance.stamp_position.value,
        "signature_rect": _snapshot_signature_rect(request.signature_rect),
    }
    try:
        signer = _load_simple_signer(request.certificate_path, request.passphrase)
        signing_time = _current_signing_time(appearance.timezone_display_mode)
        stamp_text = _build_stamp_text(
            appearance=appearance,
            signer=signer,
            signing_time=signing_time,
            signature_rect=request.signature_rect,
        )
        stamp_background = _stamp_background_for_path(appearance.image_stamp_path)
        text_box_style = _build_text_box_style(appearance.text_style)
        text_box_width, text_box_height = _measure_text_box_dimensions(
            stamp_text,
            text_box_style,
        )
        layout_reservation = _layout_reservation_for_template(
            appearance.layout_template,
            stamp_position=appearance.stamp_position,
            signature_rect=request.signature_rect,
            text_box_width=text_box_width,
            text_box_height=text_box_height,
            box_style=appearance.box_style,
            has_visible_stamp_image=stamp_background is not None,
            stamp_aspect_ratio=_stamp_image_aspect_ratio(stamp_background),
        )
        fit_gate_width_limit = layout_reservation.text_area_width_pt + 1
        fit_gate_height_limit = layout_reservation.text_area_height_pt
        fit_gate_passed = True
        try:
            _ensure_layout_can_fit(
                layout_reservation,
                has_visible_stamp_image=stamp_background is not None,
            )
        except Exception as exc:
            fit_gate_passed = False
            snapshot["error"] = str(exc)
        background_layout = _background_layout_for_stamp(
            appearance.layout_template,
            stamp_position=appearance.stamp_position,
            stamp_background=stamp_background,
            signature_rect=request.signature_rect,
            text_box_width=text_box_width,
            text_box_height=text_box_height,
            box_style=appearance.box_style,
        )
        snapshot.update(
            {
                "stamp_text": stamp_text,
                "stamp_text_length": len(stamp_text),
                "stamp_text_line_count": len(stamp_text.splitlines()) if stamp_text else 0,
                "stamp_background_present": stamp_background is not None,
                "measured_text_box_width_pt": text_box_width,
                "measured_text_box_height_pt": text_box_height,
                "reserved_primary_extent_pt": layout_reservation.reserved_primary_extent_pt,
                "stamp_area_width_pt": layout_reservation.stamp_area_width_pt,
                "stamp_area_height_pt": layout_reservation.stamp_area_height_pt,
                "text_area_width_pt": layout_reservation.text_area_width_pt,
                "text_area_height_pt": layout_reservation.text_area_height_pt,
                "fit_gate_width_limit_pt": fit_gate_width_limit,
                "fit_gate_height_limit_pt": fit_gate_height_limit,
                "fit_gate_passed": fit_gate_passed,
                "text_style": _snapshot_text_style(appearance.text_style),
                "box_style": _snapshot_box_style(appearance.box_style),
                "background_layout": _snapshot_layout_rule(background_layout),
                "content_layout": _snapshot_layout_rule(layout_reservation.inner_content_layout),
            }
        )
    except Exception as exc:
        snapshot["error"] = str(exc)
        return snapshot
    return snapshot


def _backend_reservation_error(request: SigningRequest) -> str | None:
    if request.signature_rect is None or request.signature_appearance is None:
        return None
    try:
        appearance = SigningBackendAppearance.from_signature_appearance(
            request.signature_appearance
        )
        signer = _load_simple_signer(request.certificate_path, request.passphrase)
        signing_time = _current_signing_time(appearance.timezone_display_mode)
        stamp_text = _build_stamp_text(
            appearance=appearance,
            signer=signer,
            signing_time=signing_time,
            signature_rect=request.signature_rect,
        )
        stamp_background = _stamp_background_for_path(appearance.image_stamp_path)
        _build_stamp_style(
            appearance,
            stamp_text=stamp_text,
            stamp_background=stamp_background,
            signature_rect=request.signature_rect,
        )
    except Exception as exc:
        return str(exc)
    return None


def _snapshot_layout_rule(layout_rule) -> dict[str, Any] | None:
    if layout_rule is None:
        return None
    return {
        "x_align": layout_rule.x_align.name.lower(),
        "y_align": layout_rule.y_align.name.lower(),
        "inner_content_scaling": layout_rule.inner_content_scaling.name.lower(),
        "margins": {
            "left": layout_rule.margins.left,
            "right": layout_rule.margins.right,
            "top": layout_rule.margins.top,
            "bottom": layout_rule.margins.bottom,
        },
    }


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
    if snapshot is None:
        return None
    appearance = snapshot.get("signature_appearance")
    if not isinstance(appearance, dict):
        return None
    return appearance


def _snapshot_request_origin(capture: Phase3HarnessCapture) -> str:
    if capture.sign_request_snapshot is None:
        return "not captured"
    if capture.sign_request_count > 0:
        return "submitted request"
    return "current draft"


def _snapshot_layout_template(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    direct_template = snapshot.get("layout_template")
    if isinstance(direct_template, str):
        return direct_template
    appearance = _snapshot_sign_request_appearance(snapshot)
    if appearance is None:
        return None
    layout_template = appearance.get("layout_template")
    return layout_template if isinstance(layout_template, str) else None


def _snapshot_stamp_position(snapshot: dict[str, Any] | None) -> str | None:
    if snapshot is None:
        return None
    direct_position = snapshot.get("stamp_position")
    if isinstance(direct_position, str):
        return direct_position
    appearance = _snapshot_sign_request_appearance(snapshot)
    if appearance is None:
        return None
    stamp_position = appearance.get("stamp_position")
    return stamp_position if isinstance(stamp_position, str) else None


def _snapshot_show_field_names(snapshot: dict[str, Any] | None) -> bool:
    appearance = _snapshot_sign_request_appearance(snapshot)
    if appearance is None:
        return False
    return bool(appearance.get("show_field_names"))


def _snapshot_request_field_count(snapshot: dict[str, Any] | None) -> int:
    appearance = _snapshot_sign_request_appearance(snapshot)
    if appearance is None:
        return 0
    fields = appearance.get("fields")
    if not isinstance(fields, list):
        return 0
    return len(fields)


def _snapshot_reservation_text_length(snapshot: dict[str, Any] | None) -> int:
    if snapshot is None:
        return 0
    stamp_text = snapshot.get("stamp_text")
    return len(stamp_text) if isinstance(stamp_text, str) else 0


def _snapshot_reservation_stamp_background(snapshot: dict[str, Any] | None) -> bool:
    if snapshot is None:
        return False
    return bool(snapshot.get("stamp_background_present"))


def _snapshot_reservation_stamp_background_text(snapshot: dict[str, Any] | None) -> str:
    return "yes" if _snapshot_reservation_stamp_background(snapshot) else "no"


def _snapshot_layout_scaling(snapshot: dict[str, Any] | None, key: str) -> str | None:
    if snapshot is None:
        return None
    layout = snapshot.get(f"{key}_layout")
    if not isinstance(layout, dict):
        return None
    scaling = layout.get("inner_content_scaling")
    return scaling if isinstance(scaling, str) else None


def _snapshot_reservation_margin_bottom(snapshot: dict[str, Any] | None) -> int | None:
    if snapshot is None:
        return None
    layout = snapshot.get("content_layout")
    if not isinstance(layout, dict):
        return None
    margins = layout.get("margins")
    if not isinstance(margins, dict):
        return None
    bottom = margins.get("bottom")
    return int(bottom) if isinstance(bottom, int) else None


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
    if snapshot is None:
        return "not captured"
    value = snapshot.get("field_name")
    return str(value) if value is not None else "not captured"


def _snapshot_visible_appearance_annotation_rect(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get("annotation_rect")
    return str(value) if value is not None else "not captured"


def _snapshot_visible_appearance_bbox(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get("appearance_bbox")
    return str(value) if value is not None else "not captured"


def _snapshot_visible_appearance_stream_length(snapshot: dict[str, Any] | None) -> int:
    if snapshot is None:
        return 0
    value = snapshot.get("appearance_stream_length")
    return int(value) if isinstance(value, int) else 0


def _snapshot_visible_appearance_has_text(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get("visible_text_present", snapshot.get("appearance_has_visible_text"))
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "not captured"


def _snapshot_visible_appearance_text_fragments_summary(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "not captured"
    fragments = snapshot.get("text_fragments", snapshot.get("appearance_text_fragments"))
    if not isinstance(fragments, list):
        return "not captured"
    if not fragments:
        return "[]"
    preview = ", ".join(repr(fragment) for fragment in fragments[:6])
    if len(fragments) > 6:
        return f"[{preview}, ...]"
    return f"[{preview}]"


def _snapshot_visible_appearance_image_xobjects(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "not captured"
    xobjects = snapshot.get("image_xobjects", snapshot.get("appearance_xobjects"))
    if not isinstance(xobjects, list):
        return "not captured"
    if not xobjects:
        return "[]"
    entries: list[str] = []
    for item in xobjects[:6]:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        subtype = item.get("subtype")
        width = item.get("width")
        height = item.get("height")
        size = f" {width}x{height}" if width is not None and height is not None else ""
        entries.append(f"{name}:{subtype}{size}")
    if len(xobjects) > 6:
        return f"[{', '.join(entries)}, ...]"
    return f"[{', '.join(entries)}]"


def _snapshot_visible_appearance_error(snapshot: dict[str, Any] | None) -> str:
    if snapshot is None:
        return "not captured"
    value = snapshot.get("error")
    return str(value) if value is not None else "none"


def _snapshot_appearance_xobjects(resources) -> list[dict[str, Any]]:
    if resources is None:
        return []
    xobjects = resources.get("/XObject")
    if xobjects is None:
        return []
    summaries: list[dict[str, Any]] = []
    for name, ref in xobjects.items():
        try:
            obj = ref.get_object()
        except Exception:
            obj = ref
        summaries.append(
            {
                "name": str(name),
                "subtype": _snapshot_pdf_name(obj.get("/Subtype")),
                "width": _snapshot_pdf_numeric(obj.get("/Width")),
                "height": _snapshot_pdf_numeric(obj.get("/Height")),
                "bbox": _snapshot_pdf_rect(obj.get("/BBox")),
            }
        )
    return summaries


def _count_pdf_text_operators(appearance_text: str) -> int:
    return len(re.findall(r"\)\s*T[Jj]\b", appearance_text))


def _extract_pdf_text_fragments(appearance_text: str) -> list[str]:
    fragments: list[str] = []
    for match in re.finditer(r"\((?:\\.|[^()])*\)", appearance_text):
        fragment = _decode_pdf_literal_string(match.group(0))
        if fragment:
            fragments.append(fragment)
    return fragments


def _decode_pdf_literal_string(literal: str) -> str:
    if not literal.startswith("(") or not literal.endswith(")"):
        return literal

    body = literal[1:-1]
    out: list[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        if char != "\\":
            out.append(char)
            index += 1
            continue

        index += 1
        if index >= len(body):
            break
        escape = body[index]
        if escape in "nrtbf()\\":
            out.append(
                {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "b": "\b",
                    "f": "\f",
                    "(": "(",
                    ")": ")",
                    "\\": "\\",
                }[escape]
            )
            index += 1
            continue
        if escape in "\r\n":
            if escape == "\r" and index + 1 < len(body) and body[index + 1] == "\n":
                index += 2
            else:
                index += 1
            continue
        if escape in "01234567":
            digits = [escape]
            index += 1
            while index < len(body) and len(digits) < 3 and body[index] in "01234567":
                digits.append(body[index])
                index += 1
            out.append(chr(int("".join(digits), 8)))
            continue
        out.append(escape)
        index += 1
    return "".join(out)


def _snapshot_pdf_rect(value) -> list[float] | None:
    if value is None:
        return None
    try:
        return [float(component) for component in value]
    except Exception:
        return None


def _snapshot_rect_size(rect: list[float] | None) -> dict[str, float] | None:
    if rect is None or len(rect) != 4:
        return None
    left, bottom, right, top = rect
    return {
        "width": float(right - left),
        "height": float(top - bottom),
    }


def _snapshot_pdf_name(value) -> str | None:
    if value is None:
        return None
    return str(value)


def _snapshot_pdf_numeric(value) -> float | int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except Exception:
        return None
    if numeric.is_integer():
        return int(numeric)
    return numeric


def _serialize_signature_metadata(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _serialize_signature_metadata(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_signature_metadata(item) for item in value]
    return str(value)


def _jsonable_capture(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {
            field.name: _jsonable_capture(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _jsonable_capture(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable_capture(item) for item in value]
    return str(value)
