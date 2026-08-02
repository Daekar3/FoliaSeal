"""Lazy composition factories for evidence runners.

This module owns runner construction; the large harness module supplies the
behavior-bearing collaborators (rendering, scenario, and snapshot helpers).
Keeping the imports inside the factories preserves headless application import
isolation while removing the duplicate gateway layer.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from foliaseal.application.evidence_service import (
    EvidenceCaptureRequest,
    EvidenceMatrixRequest,
)

MatrixOperation = Callable[[EvidenceMatrixRequest], Mapping[str, Any]]


class _LazyOperation:
    def __init__(self, factory: Callable[[], MatrixOperation]) -> None:
        self._factory = factory
        self._operation: MatrixOperation | None = None

    def __call__(self, request: EvidenceMatrixRequest) -> Mapping[str, Any]:
        if self._operation is None:
            self._operation = self._factory()
        return self._operation(request)

if TYPE_CHECKING:
    from foliaseal.presentation.qt.evidence_interactive_capture import (
        InteractiveEvidenceRunner,
        Phase3HarnessCapture,
    )
    from foliaseal.presentation.qt.phase3_preview_matrix_runner import (
        Phase3PreviewMatrixRunner,
    )
    from foliaseal.presentation.qt.phase3_signed_acceptance_matrix_runner import (
        Phase3SignedAcceptanceMatrixRunner,
    )
else:
    Phase3HarnessCapture = Any
    InteractiveEvidenceRunner = Any
    Phase3PreviewMatrixRunner = Any
    Phase3SignedAcceptanceMatrixRunner = Any


def build_interactive_evidence_runner() -> InteractiveEvidenceRunner:
    """Build the interactive runner only after a capture is requested."""

    from foliaseal.application.phase3_signing_backend import build_phase3_signing_executor
    from foliaseal.application.qa_evidence_contract import evaluate_phase3_evidence_contract
    from foliaseal.presentation.qt import phase3_harness as harness
    from foliaseal.presentation.qt.evidence_interactive_capture import (
        InteractiveEvidenceArtifactPolicy,
        InteractiveEvidenceRunner,
        default_harness_artifacts_dir,
        default_harness_output_pdf_path,
        write_optional_text,
    )
    from foliaseal.presentation.qt.phase3_harness_reporting import (
        build_phase3_checklist_results_markdown as render_phase3_checklist_results_markdown,
    )
    from foliaseal.presentation.qt.phase3_harness_reporting import (
        finalize_phase3_harness_report,
    )

    return InteractiveEvidenceRunner(
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
        artifact_policy=InteractiveEvidenceArtifactPolicy(
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
    [EvidenceCaptureRequest], Phase3HarnessCapture
]:
    """Return a lazy request callable for interactive capture."""

    runner: InteractiveEvidenceRunner | None = None

    def run(request: EvidenceCaptureRequest) -> Phase3HarnessCapture:
        nonlocal runner
        if runner is None:
            runner = build_interactive_evidence_runner()
        return runner.run(request)

    return run


def _build_matrix_operation(
    runner_factory: Callable[[], Any],
) -> MatrixOperation:
    runner: Any | None = None

    def run(request: EvidenceMatrixRequest) -> Mapping[str, Any]:
        nonlocal runner
        if runner is None:
            runner = runner_factory()
        if callable(runner) and not hasattr(runner, "run"):
            return runner(request)
        return runner.run(
            pdf_path=request.pdf_path,
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            scenario_manifest_path=request.scenario_manifest_path,
            artifacts_dir=request.artifacts_dir,
        )

    return run


def build_preview_evidence_operation() -> MatrixOperation:
    """Return a lazy request callable for preview matrices."""

    return _build_matrix_operation(build_preview_evidence_runner)


def build_signed_acceptance_evidence_operation() -> MatrixOperation:
    """Return a lazy request callable for signed-acceptance matrices."""

    return _build_matrix_operation(build_signed_acceptance_evidence_runner)
