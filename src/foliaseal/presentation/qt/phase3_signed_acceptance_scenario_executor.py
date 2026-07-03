"""Per-scenario signed-acceptance execution boundary for Phase 3 QA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from foliaseal.presentation.qt.phase3_harness_workspace import (
    Phase3HarnessCaptureCommand,
    Phase3HarnessWorkspacePort,
)

ApplyPreviewMatrixScenario = Callable[..., None]
BuildHarnessWorkspace = Callable[..., Phase3HarnessWorkspacePort]
ScenarioSlug = Callable[[str], str]
SnapshotSigningResultPayload = Callable[[Any], dict[str, Any]]
SnapshotSuccessfulSignedOutput = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class Phase3SignedAcceptanceScenarioExecutor:
    """Own one signed-acceptance scenario row from preview to signed output."""

    apply_preview_matrix_scenario: ApplyPreviewMatrixScenario
    build_workspace: BuildHarnessWorkspace
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
        workspace = self.build_workspace(shell=shell, profile_store=profile_store)
        artifact_basename = self.scenario_slug(str(scenario["name"]))
        snapshot = workspace.capture_snapshot(
            Phase3HarnessCaptureCommand(
                request=None,
                artifacts_dir=str(artifacts_dir),
                artifact_basename=artifact_basename,
                capture_index=1,
                capture_kind="signed_acceptance_preview",
            )
        )
        request = snapshot.current_request

        result = {
            "name": scenario["name"],
            "profile_name": scenario.get("profile_name"),
            "expected_outcome": scenario.get("expected_outcome"),
            "expected_failure_message_contains": scenario.get(
                "expected_failure_message_contains"
            ),
            "preview_snapshot": snapshot.preview_snapshot,
            "preview_text": snapshot.preview_text,
            "validation_text": snapshot.validation_text,
            "sign_request_snapshot": snapshot.sign_request_snapshot,
            "backend_reservation_snapshot": snapshot.backend_reservation_snapshot,
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
                    preview_snapshot=snapshot.preview_snapshot,
                    preview_text=snapshot.preview_text,
                    trust_policy=scenario_request.trust_policy,
                    artifacts_dir=str(artifacts_dir),
                    artifact_basename=artifact_basename,
                )
            )
        return result
