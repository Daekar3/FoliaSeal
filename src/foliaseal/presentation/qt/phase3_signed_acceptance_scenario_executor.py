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
class Phase3SignedAcceptanceScenarioResult:
    """Typed row produced by one signed-acceptance scenario."""

    name: str
    profile_name: str | None
    expected_outcome: str | None
    expected_failure_message_contains: str | None
    preview_snapshot: dict[str, Any]
    preview_text: str
    validation_text: str
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    signing_result: dict[str, Any] | None
    output_file_exists: bool
    output_signature_count: int | None
    output_signature_snapshot: dict[str, Any] | None
    output_verification_snapshot: dict[str, Any] | None
    output_visible_appearance_snapshot: dict[str, Any] | None
    signed_output_render_snapshot: dict[str, Any] | None
    signed_output_preview_comparison: dict[str, Any] | None

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> Phase3SignedAcceptanceScenarioResult:
        return cls(
            name=str(payload["name"]),
            profile_name=payload.get("profile_name"),
            expected_outcome=payload.get("expected_outcome"),
            expected_failure_message_contains=payload.get(
                "expected_failure_message_contains"
            ),
            preview_snapshot=payload.get("preview_snapshot", {}),
            preview_text=str(payload.get("preview_text", "")),
            validation_text=str(payload.get("validation_text", "")),
            sign_request_snapshot=payload.get("sign_request_snapshot"),
            backend_reservation_snapshot=payload.get("backend_reservation_snapshot"),
            signing_result=payload.get("signing_result"),
            output_file_exists=bool(payload.get("output_file_exists", False)),
            output_signature_count=payload.get("output_signature_count"),
            output_signature_snapshot=payload.get("output_signature_snapshot"),
            output_verification_snapshot=payload.get("output_verification_snapshot"),
            output_visible_appearance_snapshot=payload.get(
                "output_visible_appearance_snapshot"
            ),
            signed_output_render_snapshot=payload.get("signed_output_render_snapshot"),
            signed_output_preview_comparison=payload.get(
                "signed_output_preview_comparison"
            ),
        )

    def as_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "profile_name": self.profile_name,
            "expected_outcome": self.expected_outcome,
            "expected_failure_message_contains": self.expected_failure_message_contains,
            "preview_snapshot": self.preview_snapshot,
            "preview_text": self.preview_text,
            "validation_text": self.validation_text,
            "sign_request_snapshot": self.sign_request_snapshot,
            "backend_reservation_snapshot": self.backend_reservation_snapshot,
            "signing_result": self.signing_result,
            "output_file_exists": self.output_file_exists,
            "output_signature_count": self.output_signature_count,
            "output_signature_snapshot": self.output_signature_snapshot,
            "output_verification_snapshot": self.output_verification_snapshot,
            "output_visible_appearance_snapshot": self.output_visible_appearance_snapshot,
            "signed_output_render_snapshot": self.signed_output_render_snapshot,
            "signed_output_preview_comparison": self.signed_output_preview_comparison,
        }


@dataclass(frozen=True)
class Phase3SignedAcceptanceScenarioExecutorDeps:
    """Typed collaborator bundle for one signed-acceptance scenario row."""

    apply_preview_matrix_scenario: ApplyPreviewMatrixScenario
    build_workspace: BuildHarnessWorkspace
    scenario_slug: ScenarioSlug
    snapshot_signing_result_payload: SnapshotSigningResultPayload
    snapshot_successful_signed_output: SnapshotSuccessfulSignedOutput


@dataclass(frozen=True)
class Phase3SignedAcceptanceScenarioExecutor:
    """Own one signed-acceptance scenario row from preview to signed output."""

    deps: Phase3SignedAcceptanceScenarioExecutorDeps

    def run(
        self,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Return the legacy mapping shape for existing runner callers."""

        return self.run_result(**kwargs).as_mapping()

    def run_result(
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
    ) -> Phase3SignedAcceptanceScenarioResult:
        self.deps.apply_preview_matrix_scenario(
            shell=shell,
            scenario=scenario,
            profile_store=profile_store,
        )
        workspace = self.deps.build_workspace(shell=shell, profile_store=profile_store)
        artifact_basename = self.deps.scenario_slug(str(scenario["name"]))
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
            return Phase3SignedAcceptanceScenarioResult.from_mapping(result)

        scenario_output = artifacts_dir / f"{artifact_basename}_signed.pdf"
        scenario_request = replace(
            request,
            input_pdf_path=str(base_input_path),
            output_pdf_path=str(scenario_output),
            certificate_path=certificate_path,
            passphrase=passphrase,
        )
        signing_result = sign_executor.execute(scenario_request)
        result["signing_result"] = self.deps.snapshot_signing_result_payload(signing_result)
        if signing_result.success and scenario_output.exists():
            result.update(
                self.deps.snapshot_successful_signed_output(
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
        return Phase3SignedAcceptanceScenarioResult.from_mapping(result)
