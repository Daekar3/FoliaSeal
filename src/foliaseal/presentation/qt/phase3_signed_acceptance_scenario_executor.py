"""Per-scenario signed-acceptance execution boundary for Phase 3 QA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

ApplyPreviewMatrixScenario = Callable[..., None]
CompatSurface = Callable[[Any], Any]
SnapshotCurrentDraftRequest = Callable[[Any], Any]
BuildBackendReservationEvidence = Callable[[Any], Any]
CapturePreviewRender = Callable[..., dict[str, Any]]
SnapshotPreview = Callable[..., dict[str, Any]]
SnapshotSigningRequest = Callable[[Any], dict[str, Any] | None]
ScenarioSlug = Callable[[str], str]
SnapshotSigningResultPayload = Callable[[Any], dict[str, Any]]
SnapshotSuccessfulSignedOutput = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class Phase3SignedAcceptanceScenarioExecutor:
    """Own one signed-acceptance scenario row from preview to signed output."""

    apply_preview_matrix_scenario: ApplyPreviewMatrixScenario
    compat_surface: CompatSurface
    snapshot_current_draft_request: SnapshotCurrentDraftRequest
    build_backend_reservation_evidence: BuildBackendReservationEvidence
    capture_preview_render: CapturePreviewRender
    snapshot_preview: SnapshotPreview
    snapshot_signing_request: SnapshotSigningRequest
    scenario_slug: ScenarioSlug
    snapshot_signing_result_payload: SnapshotSigningResultPayload
    snapshot_successful_signed_output: SnapshotSuccessfulSignedOutput

    def run(
        self,
        *,
        shell: Any,
        scenario: dict[str, Any],
        profile_store: Any,
        artifacts_dir: Path,
        base_input_path: Path,
        certificate_path: str,
        passphrase: str,
        sign_executor: Any,
    ) -> dict[str, Any]:
        self.apply_preview_matrix_scenario(
            shell=shell,
            scenario=scenario,
            profile_store=profile_store,
        )
        compat = self.compat_surface(shell)
        preview = compat.properties_panel.refresh_preview()
        preview_text = compat.properties_panel.preview_text()
        validation_text = compat.properties_panel.validation_text()
        request = self.snapshot_current_draft_request(compat.properties_panel._workflow)
        artifact_basename = self.scenario_slug(str(scenario["name"]))
        render_capture = self.capture_preview_render(
            shell=shell,
            preview=preview,
            artifacts_dir=str(artifacts_dir),
            artifact_basename=artifact_basename,
        )
        preview_snapshot = self.snapshot_preview(preview, render_capture=render_capture)
        backend_reservation = self.build_backend_reservation_evidence(request)

        result = {
            "name": scenario["name"],
            "profile_name": scenario.get("profile_name"),
            "expected_outcome": scenario.get("expected_outcome"),
            "expected_failure_message_contains": scenario.get(
                "expected_failure_message_contains"
            ),
            "preview_snapshot": preview_snapshot,
            "preview_text": preview_text,
            "validation_text": validation_text,
            "sign_request_snapshot": self.snapshot_signing_request(request),
            "backend_reservation_snapshot": (
                None if backend_reservation is None else backend_reservation.snapshot
            ),
            "signing_result": None,
            "output_file_exists": False,
            "output_signature_count": None,
            "output_signature_snapshot": None,
            "output_verification_snapshot": None,
            "output_visible_appearance_snapshot": None,
            "signed_output_render_snapshot": None,
            "signed_output_preview_comparison": None,
        }

        if request is None:
            return result

        scenario_output = artifacts_dir / f"{artifact_basename}_signed.pdf"
        scenario_request = replace(
            request,
            input_pdf_path=str(base_input_path),
            output_pdf_path=str(scenario_output),
            certificate_path=certificate_path,
            passphrase=passphrase,
        )
        signing_result = sign_executor.execute(scenario_request)
        result["signing_result"] = self.snapshot_signing_result_payload(signing_result)
        if signing_result.success and scenario_output.exists():
            result.update(
                self.snapshot_successful_signed_output(
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
            )
        return result
