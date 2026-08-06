"""Qt-backed signed-acceptance matrix runner boundary for Phase 3 QA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.reusable_signing_objects import ReusableSigningObjects
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.evidence_artifacts import (
    EvidenceArtifactPort,
    FilesystemEvidenceArtifactPort,
)
from foliaseal.presentation.qt.phase3_harness_workspace import (
    Phase3HarnessWorkspacePort,
)
from foliaseal.presentation.qt.phase3_signed_acceptance_lifecycle import (
    Phase3SignedAcceptanceLifecyclePort,
    QtPhase3SignedAcceptanceLifecycle,
)
from foliaseal.presentation.qt.phase3_signed_acceptance_scenario_executor import (
    Phase3SignedAcceptanceScenarioResult,
)
from foliaseal.presentation.qt.signing_shell_port import (
    SigningWorkspaceBootstrap,
    SigningWorkspaceBundle,
)

LoadQtHarnessBindings = Callable[[], Any]
LoadPreviewMatrixManifest = Callable[[str], dict[str, Any]]
BuildPhase3SigningExecutor = Callable[..., Any]
BuildDummyTimestamper = Callable[[], Any]
LoadPageCount = Callable[..., int]
BuildQtSigningShell = Callable[..., Any]
BuildWorkspace = Callable[..., Phase3HarnessWorkspacePort]
CreateWorkspace = Callable[[SigningWorkspaceBootstrap], SigningWorkspaceBundle]
ExecuteSignedAcceptanceScenario = Callable[
    ..., Phase3SignedAcceptanceScenarioResult | dict[str, Any]
]
PreviewMatrixErrorResult = Callable[..., dict[str, Any]]
SignedMatrixDiagnosticSummary = Callable[[list[dict[str, Any]]], dict[str, int]]
EvaluateSignedMatrixAcceptanceExpectations = Callable[..., tuple[bool, list[str]]]
JsonableCapture = Callable[[Any], Any]
LifecycleFactory = Callable[[Any], Phase3SignedAcceptanceLifecyclePort]
ArtifactPortFactory = Callable[[], EvidenceArtifactPort]


@dataclass(frozen=True)
class Phase3SignedAcceptanceMatrixRunnerDeps:
    """Typed collaborator bundle for the signed-acceptance matrix runner."""

    load_qt_harness_bindings: LoadQtHarnessBindings
    load_preview_matrix_manifest: LoadPreviewMatrixManifest
    build_phase3_signing_executor: BuildPhase3SigningExecutor
    build_dummy_timestamper: BuildDummyTimestamper
    load_page_count: LoadPageCount
    build_qt_signing_shell: BuildQtSigningShell
    build_workspace: BuildWorkspace
    execute_signed_acceptance_scenario: ExecuteSignedAcceptanceScenario
    preview_matrix_error_result: PreviewMatrixErrorResult
    signed_matrix_diagnostic_summary: SignedMatrixDiagnosticSummary
    evaluate_signed_matrix_acceptance_expectations: (
        EvaluateSignedMatrixAcceptanceExpectations
    )
    jsonable_capture: JsonableCapture
    render_backend_factory: Callable[[], Any]
    profile_store_factory: Callable[[], Any] = SignaturePresetCatalogStore.default
    lifecycle_factory: LifecycleFactory | None = None
    artifact_port_factory: ArtifactPortFactory | None = None
    create_workspace: CreateWorkspace | None = None


@dataclass(frozen=True)
class Phase3SignedAcceptanceMatrixRunner:
    """Own one signed-output acceptance sweep and summary artifact."""

    deps: Phase3SignedAcceptanceMatrixRunnerDeps

    def run(
        self,
        *,
        pdf_path: str,
        certificate_path: str,
        passphrase: str,
        scenario_manifest_path: str,
        artifacts_dir: str,
    ) -> dict[str, Any]:
        bindings = self.deps.load_qt_harness_bindings()
        source_path = Path(pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF does not exist: {pdf_path}")

        manifest = self.deps.load_preview_matrix_manifest(scenario_manifest_path)
        scenarios = manifest["scenarios"]
        artifact_port_factory = (
            self.deps.artifact_port_factory or FilesystemEvidenceArtifactPort
        )
        artifact_port = artifact_port_factory()
        artifact_root = artifact_port.prepare(artifacts_dir)
        timestamping_mode = manifest.get("timestamping_mode", "real")
        if timestamping_mode not in {"real", "dummy"}:
            raise ValueError("'timestamping_mode' must be one of 'real' or 'dummy'.")
        sign_executor = self.deps.build_phase3_signing_executor(
            timestamper_factory=(
                (lambda _tsa_url: self.deps.build_dummy_timestamper())
                if timestamping_mode == "dummy"
                else None
            )
        )

        page_count = self.deps.load_page_count(bindings=bindings, pdf_path=str(source_path))
        backend = self.deps.render_backend_factory()
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
        profile_store = self.deps.profile_store_factory()
        reusable_objects = ReusableSigningObjects(profile_store)

        lifecycle_factory = self.deps.lifecycle_factory or QtPhase3SignedAcceptanceLifecycle
        lifecycle = lifecycle_factory(bindings)
        try:
            lifecycle.start(
                title=f"FoliaSeal Phase 3 Signed Acceptance Matrix - {source_path.name}"
            )
            shell = self.deps.build_qt_signing_shell(
                viewer_workflow=viewer_workflow,
                signing_workflow=signing_workflow,
                reusable_objects=reusable_objects,
                sign_executor=sign_executor,
            )
            lifecycle.attach_shell(shell)
            workspace_bundle: SigningWorkspaceBundle | None = None
            if self.deps.create_workspace is not None:
                workspace_bundle = self.deps.create_workspace(
                    SigningWorkspaceBootstrap(
                        viewer_workflow=viewer_workflow,
                        signing_workflow=signing_workflow,
                        app_settings=AppSettings.default(),
                        reusable_objects=reusable_objects,
                        sign_executor=sign_executor,
                    )
                )
                workspace = self.deps.build_workspace(
                    workspace=workspace_bundle,
                    profile_store=profile_store,
                )
            else:
                workspace = self.deps.build_workspace(shell=shell, profile_store=profile_store)
            workspace.refresh_viewer()
            lifecycle.process_events()

            results: list[dict[str, Any]] = []
            for scenario in scenarios:
                try:
                    scenario_result = self.deps.execute_signed_acceptance_scenario(
                        shell=shell,
                        workspace=workspace_bundle,
                        scenario=scenario,
                        profile_store=profile_store,
                        artifacts_dir=artifact_root,
                        base_input_path=source_path,
                        certificate_path=certificate_path,
                        passphrase=passphrase,
                        sign_executor=sign_executor,
                    )
                except Exception as exc:
                    scenario_result = self.deps.preview_matrix_error_result(
                        scenario=scenario,
                        error=exc,
                    )
                results.append(
                    scenario_result.as_mapping()
                    if isinstance(scenario_result, Phase3SignedAcceptanceScenarioResult)
                    else dict(scenario_result)
                )
                lifecycle.process_events()
            summary = {
                "pdf_path": str(source_path),
                "scenario_manifest_path": scenario_manifest_path,
                "artifacts_dir": str(artifact_root),
                "scenario_count": len(results),
                "successful_scenario_count": sum(
                    1
                    for item in results
                    if _mapping(item.get("signing_result")).get("success") is True
                ),
                "error_scenario_count": sum(1 for item in results if "error" in item),
                **self.deps.signed_matrix_diagnostic_summary(results),
                "results": results,
            }
            if "acceptance_expectations" in manifest:
                summary["acceptance_expectations"] = manifest["acceptance_expectations"]
            summary["timestamping_mode"] = timestamping_mode
            expectations_passed, expectation_errors = (
                self.deps.evaluate_signed_matrix_acceptance_expectations(
                    summary=summary,
                    manifest_expectations=_mapping(manifest.get("acceptance_expectations")),
                )
            )
            summary["acceptance_expectations_passed"] = expectations_passed
            summary["acceptance_expectation_errors"] = expectation_errors
            summary_path = artifact_port.write_summary(
                artifact_root,
                self.deps.jsonable_capture(summary),
            )
            summary["summary_json_path"] = summary_path
            artifact_port.write_summary(
                artifact_root,
                self.deps.jsonable_capture(summary),
            )
            return summary
        finally:
            lifecycle.close()


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
