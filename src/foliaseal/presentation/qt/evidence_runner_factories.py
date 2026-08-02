"""Lazy composition factories for evidence runners.

This module owns runner construction; the large harness module supplies the
behavior-bearing collaborators (rendering, scenario, and snapshot helpers).
Keeping the imports inside the factories preserves headless application import
isolation while removing the duplicate gateway layer.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from foliaseal.application.phase3_evidence_service import (
    Phase3HarnessCaptureRequest,
    Phase3MatrixRequest,
)

if TYPE_CHECKING:
    from foliaseal.presentation.qt.phase3_interactive_capture import (
        Phase3HarnessCapture,
        Phase3InteractiveHarnessRunner,
    )
    from foliaseal.presentation.qt.phase3_matrix_operations import MatrixOperation
    from foliaseal.presentation.qt.phase3_preview_matrix_runner import (
        Phase3PreviewMatrixRunner,
    )
    from foliaseal.presentation.qt.phase3_signed_acceptance_matrix_runner import (
        Phase3SignedAcceptanceMatrixRunner,
    )
else:
    Phase3HarnessCapture = Any
    Phase3InteractiveHarnessRunner = Any
    Phase3PreviewMatrixRunner = Any
    Phase3SignedAcceptanceMatrixRunner = Any
    MatrixOperation = Any


def build_interactive_evidence_runner() -> Phase3InteractiveHarnessRunner:
    """Build the interactive runner only after a capture is requested."""

    from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
    from foliaseal.application.qa_evidence_contract import evaluate_phase3_evidence_contract
    from foliaseal.presentation.qt import phase3_harness as harness
    from foliaseal.presentation.qt.phase3_harness_reporting import (
        build_phase3_checklist_results_markdown as render_phase3_checklist_results_markdown,
    )
    from foliaseal.presentation.qt.phase3_harness_reporting import (
        finalize_phase3_harness_report,
    )
    from foliaseal.presentation.qt.phase3_interactive_capture import (
        Phase3InteractiveCaptureArtifactPolicy,
        Phase3InteractiveHarnessRunner,
        default_harness_artifacts_dir,
        default_harness_output_pdf_path,
        write_optional_text,
    )

    return Phase3InteractiveHarnessRunner(
        load_qt_harness_bindings=harness._load_qt_harness_bindings,
        load_page_count=harness._load_page_count,
        render_backend_factory=harness.QtPdfRenderBackend,
        profile_store_factory=harness.SignaturePresetCatalogStore.default,
        build_phase3_signing_executor=build_phase3_signing_executor,
        session_runner=harness._build_phase3_harness_session_runner(),
        capture_assembler=harness._build_phase3_harness_capture_assembler(),
        contract_evaluator=evaluate_phase3_evidence_contract,
        capture_factory=harness._build_phase3_harness_capture,
        checklist_renderer=render_phase3_checklist_results_markdown,
        report_finalizer=finalize_phase3_harness_report,
        artifact_policy=Phase3InteractiveCaptureArtifactPolicy(
            default_artifacts_dir=default_harness_artifacts_dir,
            output_pdf_path=default_harness_output_pdf_path,
            write_text=write_optional_text,
        ),
    )


def build_preview_evidence_runner() -> Phase3PreviewMatrixRunner:
    """Build the headless preview runner lazily."""

    from foliaseal.presentation.qt import phase3_harness as harness
    from foliaseal.presentation.qt.phase3_preview_matrix_runner import (
        Phase3PreviewMatrixRunner,
        Phase3PreviewMatrixRunnerDeps,
    )

    return Phase3PreviewMatrixRunner(
        deps=Phase3PreviewMatrixRunnerDeps(
            load_preview_matrix_manifest=harness._load_preview_matrix_manifest,
            execute_headless_preview_matrix_scenario=(
                harness._execute_headless_preview_matrix_scenario
            ),
            preview_matrix_error_result=harness._preview_matrix_error_result,
            preview_matrix_diagnostic_summary=harness._preview_matrix_diagnostic_summary,
            jsonable_capture=harness._jsonable_capture,
            profile_store_factory=harness.SignaturePresetCatalogStore.default,
        )
    )


def build_signed_acceptance_evidence_runner() -> Phase3SignedAcceptanceMatrixRunner:
    """Build the Qt-backed signed matrix runner lazily."""

    from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
    from foliaseal.infra.tsa import build_dummy_timestamper
    from foliaseal.presentation.qt import phase3_harness as harness
    from foliaseal.presentation.qt.phase3_signed_acceptance_matrix_runner import (
        Phase3SignedAcceptanceMatrixRunner,
        Phase3SignedAcceptanceMatrixRunnerDeps,
    )

    return Phase3SignedAcceptanceMatrixRunner(
        deps=Phase3SignedAcceptanceMatrixRunnerDeps(
            load_qt_harness_bindings=harness._load_qt_harness_bindings,
            load_preview_matrix_manifest=harness._load_preview_matrix_manifest,
            build_phase3_signing_executor=build_phase3_signing_executor,
            build_dummy_timestamper=build_dummy_timestamper,
            load_page_count=harness._load_page_count,
            build_qt_signing_shell=harness.build_qt_signing_shell,
            build_workspace=harness._build_preview_matrix_qt_workspace,
            execute_signed_acceptance_scenario=harness._execute_signed_acceptance_scenario,
            preview_matrix_error_result=harness._preview_matrix_error_result,
            signed_matrix_diagnostic_summary=harness._signed_matrix_diagnostic_summary,
            evaluate_signed_matrix_acceptance_expectations=(
                harness._evaluate_signed_matrix_acceptance_expectations
            ),
            jsonable_capture=harness._jsonable_capture,
            render_backend_factory=harness.QtPdfRenderBackend,
        )
    )


def build_interactive_evidence_operation() -> Callable[
    [Phase3HarnessCaptureRequest], Phase3HarnessCapture
]:
    """Return a lazy request callable for interactive capture."""

    runner: Phase3InteractiveHarnessRunner | None = None

    def run(request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture:
        nonlocal runner
        if runner is None:
            runner = build_interactive_evidence_runner()
        return runner.run(request)

    return run


def build_preview_evidence_operation() -> MatrixOperation:
    """Return a lazy request callable for preview matrices."""

    runner: Phase3PreviewMatrixRunner | None = None

    def run(request: Phase3MatrixRequest):
        nonlocal runner
        if runner is None:
            runner = build_preview_evidence_runner()
        return runner.run(
            pdf_path=request.pdf_path,
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            scenario_manifest_path=request.scenario_manifest_path,
            artifacts_dir=request.artifacts_dir,
        )

    return run


def build_signed_acceptance_evidence_operation() -> MatrixOperation:
    """Return a lazy request callable for signed-acceptance matrices."""

    runner: Phase3SignedAcceptanceMatrixRunner | None = None

    def run(request: Phase3MatrixRequest):
        nonlocal runner
        if runner is None:
            runner = build_signed_acceptance_evidence_runner()
        return runner.run(
            pdf_path=request.pdf_path,
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            scenario_manifest_path=request.scenario_manifest_path,
            artifacts_dir=request.artifacts_dir,
        )

    return run
