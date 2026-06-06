from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from foliaseal.domain.models import SigningResult
from foliaseal.presentation.qt.phase3_harness_capture_assembler import (
    Phase3HarnessCaptureAssembler,
)
from tests.support.phase3_builders import (
    build_signature_rect,
    build_signing_request,
)


def _assembler(
    *,
    analyze_capture_state_transitions=None,
    count_embedded_signatures=None,
    snapshot_output_signature=None,
    snapshot_output_verification=None,
    snapshot_visible_signature_appearance=None,
    snapshot_signed_output_render=None,
) -> Phase3HarnessCaptureAssembler:
    return Phase3HarnessCaptureAssembler(
        count_embedded_signatures=count_embedded_signatures or (lambda _path: 1),
        snapshot_output_signature=snapshot_output_signature
        or (lambda _path: {"field_name": "Signature1"}),
        snapshot_output_verification=snapshot_output_verification
        or (lambda _path, _trust_policy: {"valid": True}),
        snapshot_visible_signature_appearance=snapshot_visible_signature_appearance
        or (lambda _path: {"field_name": "Signature1"}),
        snapshot_signed_output_render=snapshot_signed_output_render
        or (lambda **_kwargs: {"comparison_path": "compare.png"}),
        analyze_capture_state_transitions=analyze_capture_state_transitions
        or (lambda captured_states: [{"count": len(captured_states)}]),
    )


def test_phase3_harness_capture_assembler_build_signed_run_bundle_freezes_sign_time_state(
    tmp_path: Path,
) -> None:
    output_pdf = tmp_path / "signed.pdf"
    output_pdf.write_bytes(b"%PDF-1.7\n")
    request = build_signing_request(
        tmp_path,
        input_name="input.pdf",
        output_name="signed.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=0, width_pt=320.0, height_pt=48.0),
    )
    signing_result = SigningResult(
        success=True,
        failure_code=None,
        message="Signing completed successfully.",
    )
    sign_time_state = {
        "capture_label": "signed_run_01_single_line_top",
        "preview_snapshot": {"title": "Before mutation"},
        "preview_text": "Before mutation",
        "validation_text": "Ready to sign.",
        "sign_request_snapshot": {"output_pdf_path": request.output_pdf_path},
        "backend_reservation_snapshot": {"stamp_text": "Before mutation"},
        "backend_reservation_error": None,
    }

    assembler = _assembler(
        snapshot_signed_output_render=lambda **_kwargs: {
            "comparison_path": "compare.png",
            "preview_vs_signed_output_passed": True,
        }
    )

    bundle = assembler.build_signed_run_bundle(
        run_index=1,
        sign_time_state=sign_time_state,
        request=request,
        signing_result=signing_result,
        artifacts_dir=str(tmp_path),
        artifact_basename="signed_run_01_signed_output",
    )

    sign_time_state["preview_snapshot"]["title"] = "After mutation"
    sign_time_state["sign_request_snapshot"]["output_pdf_path"] = "mutated.pdf"
    sign_time_state["backend_reservation_snapshot"]["stamp_text"] = "After mutation"

    assert bundle["preview_snapshot"]["title"] == "Before mutation"
    assert bundle["sign_request_snapshot"]["output_pdf_path"] == str(output_pdf)
    assert bundle["backend_reservation_snapshot"]["stamp_text"] == "Before mutation"
    assert bundle["signed_output_preview_comparison"]["preview_vs_signed_output_passed"] is True


def test_phase3_harness_capture_assembler_build_capture_payload_uses_latest_signed_run() -> None:
    source_path = Path("/tmp/input.pdf")
    final_state = {
        "preview_snapshot": {"title": "Final preview"},
        "sign_request_snapshot": {"output_pdf_path": "/tmp/final.pdf"},
        "backend_reservation_snapshot": {"layout_template": "single_line"},
        "backend_reservation_error": None,
        "preview_text": "Ready",
        "validation_text": "Ready to sign.",
    }
    request = build_signing_request(
        Path("/tmp"),
        input_name="input.pdf",
        output_name="final.pdf",
        certificate_name="cert.p12",
        passphrase="secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=2, width_pt=200.0, height_pt=40.0),
    )
    session = SimpleNamespace(
        first_render_ms=12.5,
        sign_requests=(request,),
        signed_runs=(
            {
                "output_pdf_path": "/tmp/signed.pdf",
                "output_file_exists": True,
                "output_file_size_bytes": 321,
                "output_signature_count": 1,
                "output_signature_snapshot": {"field_name": "Signature1"},
                "output_verification_snapshot": {"valid": True},
                "output_visible_appearance_snapshot": {"field_name": "Signature1"},
                "signed_output_render_snapshot": {"comparison_path": "compare.png"},
            },
        ),
        errors=("debug issue",),
        interaction_counts={"selection_success": 1},
        captured_states=({"capture_label": "manual", "preview_snapshot": {"title": "Manual"}},),
        final_state=final_state,
        capture_request=request,
        last_signing_result=SimpleNamespace(message="Signed", success=True),
    )
    assembler = _assembler(
        analyze_capture_state_transitions=lambda captured_states: [
            {"from": captured_states[0]["capture_label"], "to": "final"}
        ]
    )

    payload = assembler.build_capture_payload(
        source_path=source_path,
        summary_json_path="/tmp/summary.json",
        checklist_results_path="/tmp/results.md",
        artifacts_dir="/tmp/artifacts",
        session=session,
    )

    assert payload["pdf_path"] == str(source_path)
    assert payload["last_signature_output_path"] == "/tmp/signed.pdf"
    assert payload["output_file_size_bytes"] == 321
    assert payload["preview_text"] == "Ready"
    assert payload["captured_states"][-1]["preview_snapshot"]["title"] == "Final preview"
    assert payload["captured_state_transition_diagnostics"] == [{"from": "manual", "to": "final"}]
