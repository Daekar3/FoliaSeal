"""Capture-assembly helpers for Phase 3 harness evidence."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.domain.models import SigningRequest, SigningResult, TimestampTrustPolicy
from foliaseal.presentation.qt.phase3_signed_output_snapshotter import (
    Phase3SignedOutputSnapshotter,
    signed_output_preview_comparison_snapshot,
)

CountEmbeddedSignatures = Callable[[Path], int | None]
SnapshotOutputSignature = Callable[[Path], dict[str, Any] | None]
SnapshotOutputVerification = Callable[
    [Path, TimestampTrustPolicy | None],
    dict[str, Any] | None,
]
SnapshotVisibleSignatureAppearance = Callable[[Path], dict[str, Any] | None]
SnapshotSignedOutputRender = Callable[..., dict[str, Any] | None]
AnalyzeCaptureStateTransitions = Callable[
    [list[dict[str, Any]]],
    list[dict[str, Any]],
]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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

@dataclass(frozen=True)
class Phase3HarnessCaptureAssembler:
    """Turns raw session state into stable JSON-ready harness evidence."""

    count_embedded_signatures: CountEmbeddedSignatures
    snapshot_output_signature: SnapshotOutputSignature
    snapshot_output_verification: SnapshotOutputVerification
    snapshot_visible_signature_appearance: SnapshotVisibleSignatureAppearance
    snapshot_signed_output_render: SnapshotSignedOutputRender
    analyze_capture_state_transitions: AnalyzeCaptureStateTransitions

    def _signed_output_snapshotter(self) -> Phase3SignedOutputSnapshotter:
        return Phase3SignedOutputSnapshotter(
            count_embedded_signatures=self.count_embedded_signatures,
            snapshot_output_signature=self.snapshot_output_signature,
            snapshot_output_verification=self.snapshot_output_verification,
            snapshot_visible_signature_appearance=self.snapshot_visible_signature_appearance,
            snapshot_signed_output_render=self.snapshot_signed_output_render,
        )

    def build_signed_run_bundle(
        self,
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
                self._signed_output_snapshotter().snapshot_successful_signed_output(
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

    def build_capture_payload(
        self,
        *,
        source_path: Path,
        summary_json_path: str | None,
        checklist_results_path: str,
        artifacts_dir: str | None,
        session: Any,
    ) -> dict[str, Any]:
        preview_text = session.final_state["preview_text"]
        validation_text = session.final_state["validation_text"]
        backend_reservation_snapshot = session.final_state["backend_reservation_snapshot"]
        backend_reservation_error = session.final_state["backend_reservation_error"]
        last_signature_page_index = (
            session.sign_requests[-1].signature_rect.page_index
            if session.sign_requests and session.sign_requests[-1].signature_rect is not None
            else None
        )
        output_path = session.sign_requests[-1].output_pdf_path if session.sign_requests else None
        output_exists = False
        output_size_bytes = None
        output_signature_count = None
        output_signature_snapshot = None
        output_verification_snapshot = None
        output_visible_appearance_snapshot = None
        signed_output_render_snapshot = None
        if session.signed_runs:
            latest_signed_run = _mapping(session.signed_runs[-1])
            output_path = latest_signed_run.get("output_pdf_path")
            output_exists = bool(latest_signed_run.get("output_file_exists"))
            output_size_bytes = latest_signed_run.get("output_file_size_bytes")
            output_signature_count = latest_signed_run.get("output_signature_count")
            output_signature_snapshot = latest_signed_run.get("output_signature_snapshot")
            output_verification_snapshot = latest_signed_run.get(
                "output_verification_snapshot"
            )
            output_visible_appearance_snapshot = latest_signed_run.get(
                "output_visible_appearance_snapshot"
            )
            signed_output_render_snapshot = latest_signed_run.get(
                "signed_output_render_snapshot"
            )
        elif output_path is not None:
            output_file = Path(output_path)
            output_exists = output_file.exists()
            if output_exists:
                snapshotter = self._signed_output_snapshotter()
                output_snapshot = snapshotter.snapshot_successful_signed_output(
                    output_file=output_file,
                    page_index=last_signature_page_index,
                    preview_snapshot=session.final_state["preview_snapshot"],
                    preview_text=preview_text,
                    trust_policy=(
                        session.capture_request.trust_policy
                        if session.capture_request is not None
                        else None
                    ),
                    artifacts_dir=artifacts_dir,
                    artifact_basename="final_signed_output",
                )
                output_size_bytes = output_snapshot["output_file_size_bytes"]
                output_signature_count = output_snapshot["output_signature_count"]
                output_signature_snapshot = output_snapshot["output_signature_snapshot"]
                output_verification_snapshot = output_snapshot[
                    "output_verification_snapshot"
                ]
                output_visible_appearance_snapshot = output_snapshot[
                    "output_visible_appearance_snapshot"
                ]
                signed_output_render_snapshot = output_snapshot[
                    "signed_output_render_snapshot"
                ]

        captured_states = list(session.captured_states) + [session.final_state]
        checklist_results_written = bool(checklist_results_path)
        return {
            "pdf_path": str(source_path),
            "summary_json_path": summary_json_path,
            "summary_json_written": summary_json_path is not None,
            "checklist_results_path": checklist_results_path,
            "checklist_results_written": checklist_results_written,
            "first_render_ms": session.first_render_ms,
            "selection_count": session.interaction_counts.get("selection_success", 0),
            "sign_request_count": len(session.sign_requests),
            "last_signature_page_index": last_signature_page_index,
            "last_signature_page_number": (
                last_signature_page_index + 1 if last_signature_page_index is not None else None
            ),
            "last_signature_has_visible_appearance": (
                session.sign_requests[-1].has_visible_signature_settings()
                if session.sign_requests
                else False
            ),
            "last_signature_output_path": output_path,
            "last_signing_result_message": (
                session.last_signing_result.message
                if isinstance(session.last_signing_result, SigningResult)
                else None
            ),
            "last_signing_result_success": (
                session.last_signing_result.success
                if isinstance(session.last_signing_result, SigningResult)
                else None
            ),
            "preview_snapshot": session.final_state["preview_snapshot"],
            "sign_request_snapshot": session.final_state["sign_request_snapshot"],
            "backend_reservation_snapshot": backend_reservation_snapshot,
            "backend_reservation_error": backend_reservation_error,
            "output_file_exists": output_exists,
            "output_file_size_bytes": output_size_bytes,
            "output_signature_count": output_signature_count,
            "output_signature_snapshot": output_signature_snapshot,
            "output_verification_snapshot": output_verification_snapshot,
            "output_visible_appearance_snapshot": output_visible_appearance_snapshot,
            "signed_output_render_snapshot": signed_output_render_snapshot,
            "signed_output_preview_comparison": signed_output_preview_comparison_snapshot(
                signed_output_render_snapshot
            ),
            "signed_runs": list(session.signed_runs),
            "preview_available": session.final_state["preview_snapshot"] is not None,
            "preview_text": preview_text,
            "validation_text": validation_text,
            "interaction_counts": session.interaction_counts,
            "errors": list(session.errors),
            "captured_states": captured_states,
            "captured_state_transition_diagnostics": list(
                self.analyze_capture_state_transitions(captured_states)
            ),
        }
