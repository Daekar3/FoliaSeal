"""Headless preview-matrix runner boundary for Phase 3 QA."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LoadPreviewMatrixManifest = Callable[[str], dict[str, Any]]
ExecuteHeadlessPreviewMatrixScenario = Callable[..., dict[str, Any]]
PreviewMatrixErrorResult = Callable[..., dict[str, Any]]
PreviewMatrixDiagnosticSummary = Callable[[list[dict[str, Any]]], dict[str, int]]
JsonableCapture = Callable[[Any], Any]


@dataclass(frozen=True)
class Phase3PreviewMatrixRunnerDeps:
    """Typed collaborator bundle for the preview-matrix runner."""

    load_preview_matrix_manifest: LoadPreviewMatrixManifest
    execute_headless_preview_matrix_scenario: ExecuteHeadlessPreviewMatrixScenario
    preview_matrix_error_result: PreviewMatrixErrorResult
    preview_matrix_diagnostic_summary: PreviewMatrixDiagnosticSummary
    jsonable_capture: JsonableCapture
    profile_store_factory: Callable[[], Any]


@dataclass(frozen=True)
class Phase3PreviewMatrixRunner:
    """Own one preview-only matrix sweep and summary artifact."""

    deps: Phase3PreviewMatrixRunnerDeps

    def run(
        self,
        *,
        pdf_path: str,
        certificate_path: str,
        passphrase: str,
        scenario_manifest_path: str,
        artifacts_dir: str,
    ) -> dict[str, Any]:
        source_path = Path(pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF does not exist: {pdf_path}")

        manifest = self.deps.load_preview_matrix_manifest(scenario_manifest_path)
        scenarios = manifest["scenarios"]
        artifact_root = Path(artifacts_dir)
        artifact_root.mkdir(parents=True, exist_ok=True)

        profile_store = self.deps.profile_store_factory()
        results: list[dict[str, Any]] = []
        for scenario in scenarios:
            try:
                result = self.deps.execute_headless_preview_matrix_scenario(
                    source_path=source_path,
                    certificate_path=certificate_path,
                    passphrase=passphrase,
                    scenario=scenario,
                    profile_store=profile_store,
                    artifacts_dir=artifact_root,
                )
            except Exception as exc:
                result = self.deps.preview_matrix_error_result(scenario=scenario, error=exc)
            results.append(result)

        summary = {
            "pdf_path": str(source_path),
            "scenario_manifest_path": scenario_manifest_path,
            "artifacts_dir": str(artifact_root),
            "scenario_count": len(results),
            "successful_scenario_count": sum(1 for item in results if "error" not in item),
            "error_scenario_count": sum(1 for item in results if "error" in item),
            **self.deps.preview_matrix_diagnostic_summary(results),
            "results": results,
        }
        summary_path = artifact_root / "summary.json"
        summary_path.write_text(
            json.dumps(self.deps.jsonable_capture(summary), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return summary
