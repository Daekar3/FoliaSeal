"""Qt-backed signed-acceptance matrix runner boundary for Phase 3 QA."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.render.qt_backend import QtPdfRenderBackend

LoadQtHarnessBindings = Callable[[], Any]
LoadPreviewMatrixManifest = Callable[[str], dict[str, Any]]
BuildPhase3SigningExecutor = Callable[..., Any]
BuildDummyTimestamper = Callable[[], Any]
LoadPageCount = Callable[..., int]
BuildQtSigningShell = Callable[..., Any]
CompatSurface = Callable[[Any], Any]
ExecuteSignedAcceptanceScenario = Callable[..., dict[str, Any]]
PreviewMatrixErrorResult = Callable[..., dict[str, Any]]
SignedMatrixDiagnosticSummary = Callable[[list[dict[str, Any]]], dict[str, int]]
EvaluateSignedMatrixAcceptanceExpectations = Callable[..., tuple[bool, list[str]]]
JsonableCapture = Callable[[Any], Any]


@dataclass(frozen=True)
class Phase3SignedAcceptanceMatrixRunner:
    """Own one signed-output acceptance sweep and summary artifact."""

    load_qt_harness_bindings: LoadQtHarnessBindings
    load_preview_matrix_manifest: LoadPreviewMatrixManifest
    build_phase3_signing_executor: BuildPhase3SigningExecutor
    build_dummy_timestamper: BuildDummyTimestamper
    load_page_count: LoadPageCount
    build_qt_signing_shell: BuildQtSigningShell
    compat_surface: CompatSurface
    execute_signed_acceptance_scenario: ExecuteSignedAcceptanceScenario
    preview_matrix_error_result: PreviewMatrixErrorResult
    signed_matrix_diagnostic_summary: SignedMatrixDiagnosticSummary
    evaluate_signed_matrix_acceptance_expectations: (
        EvaluateSignedMatrixAcceptanceExpectations
    )
    jsonable_capture: JsonableCapture

    def run(
        self,
        *,
        pdf_path: str,
        certificate_path: str,
        passphrase: str,
        scenario_manifest_path: str,
        artifacts_dir: str,
    ) -> dict[str, Any]:
        bindings = self.load_qt_harness_bindings()
        source_path = Path(pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF does not exist: {pdf_path}")

        manifest = self.load_preview_matrix_manifest(scenario_manifest_path)
        scenarios = manifest["scenarios"]
        artifact_root = Path(artifacts_dir)
        artifact_root.mkdir(parents=True, exist_ok=True)
        timestamping_mode = manifest.get("timestamping_mode", "real")
        if timestamping_mode not in {"real", "dummy"}:
            raise ValueError("'timestamping_mode' must be one of 'real' or 'dummy'.")
        sign_executor = self.build_phase3_signing_executor(
            timestamper_factory=(
                (lambda _tsa_url: self.build_dummy_timestamper())
                if timestamping_mode == "dummy"
                else None
            )
        )

        page_count = self.load_page_count(bindings=bindings, pdf_path=str(source_path))
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
        window.setWindowTitle(
            f"FoliaSeal Phase 3 Signed Acceptance Matrix - {source_path.name}"
        )
        window.resize(1440, 980)
        shell = self.build_qt_signing_shell(
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            preset_catalog_store=profile_store,
            sign_executor=sign_executor,
        )
        window.setCentralWidget(shell)
        window.show()
        self.compat_surface(shell).refresh_viewer()
        app.processEvents()

        results: list[dict[str, Any]] = []
        for scenario in scenarios:
            try:
                result = self.execute_signed_acceptance_scenario(
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
                result = self.preview_matrix_error_result(scenario=scenario, error=exc)
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
                1
                for item in results
                if _mapping(item.get("signing_result")).get("success") is True
            ),
            "error_scenario_count": sum(1 for item in results if "error" in item),
            **self.signed_matrix_diagnostic_summary(results),
            "results": results,
        }
        if "acceptance_expectations" in manifest:
            summary["acceptance_expectations"] = manifest["acceptance_expectations"]
        summary["timestamping_mode"] = timestamping_mode
        expectations_passed, expectation_errors = (
            self.evaluate_signed_matrix_acceptance_expectations(
                summary=summary,
                manifest_expectations=_mapping(manifest.get("acceptance_expectations")),
            )
        )
        summary["acceptance_expectations_passed"] = expectations_passed
        summary["acceptance_expectation_errors"] = expectation_errors
        summary_path = artifact_root / "summary.json"
        summary_path.write_text(
            json.dumps(self.jsonable_capture(summary), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return summary


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
