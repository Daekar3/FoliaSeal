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
from foliaseal.presentation.qt.evidence_harness_runtime import EvidenceHarnessRuntime
from foliaseal.presentation.qt.evidence_runner_providers import EvidenceRunnerProviders

MatrixOperation = Callable[[EvidenceMatrixRequest], Mapping[str, Any]]

if TYPE_CHECKING:
    from foliaseal.presentation.qt.evidence_interactive_capture import (
        InteractiveCaptureEngine,
        InteractiveHarnessCapture,
    )
    from foliaseal.presentation.qt.preview_matrix_runner import (
        PreviewMatrixRunner,
    )
    from foliaseal.presentation.qt.signed_acceptance_matrix_runner import (
        SignedAcceptanceMatrixRunner,
    )
else:
    InteractiveHarnessCapture = Any
    InteractiveCaptureEngine = Any
    PreviewMatrixRunner = Any
    SignedAcceptanceMatrixRunner = Any


def build_interactive_capture_engine(
    *, providers: EvidenceRunnerProviders | None = None
) -> InteractiveCaptureEngine:
    """Build the interactive capture engine only after a request is made."""

    from foliaseal.presentation.qt.evidence_interactive_capture import (
        InteractiveCaptureEngine,
    )
    if providers is None:
        from foliaseal.presentation.qt.interactive_harness import (
            build_evidence_runner_providers,
        )

        providers = build_evidence_runner_providers()
    interactive = providers.interactive

    return InteractiveCaptureEngine(
        load_qt_harness_bindings=interactive.load_qt_harness_bindings,
        load_page_count=interactive.load_page_count,
        render_backend_factory=interactive.render_backend_factory,
        profile_store_factory=interactive.profile_store_factory,
        build_signing_executor=interactive.build_signing_executor,
        session_runner=interactive.session_runner,
        capture_assembler=interactive.capture_assembler,
        contract_evaluator=interactive.contract_evaluator,
        capture_factory=interactive.capture_factory,
        checklist_renderer=interactive.checklist_renderer,
        report_finalizer=interactive.report_finalizer,
        artifact_policy=interactive.artifact_policy,
    )


def build_preview_evidence_runner(
    *, providers: EvidenceRunnerProviders | None = None
) -> PreviewMatrixRunner:
    """Build the headless preview runner lazily."""

    from foliaseal.presentation.qt.preview_matrix_runner import (
        PreviewMatrixRunner,
        PreviewMatrixRunnerDeps,
    )
    if providers is None:
        from foliaseal.presentation.qt.interactive_harness import (
            build_evidence_runner_providers,
        )

        providers = build_evidence_runner_providers()
    preview = providers.preview

    return PreviewMatrixRunner(
        deps=PreviewMatrixRunnerDeps(
            load_preview_matrix_manifest=preview.load_preview_matrix_manifest,
            execute_headless_preview_matrix_scenario=(
                preview.execute_headless_preview_matrix_scenario
            ),
            preview_matrix_error_result=preview.preview_matrix_error_result,
            preview_matrix_diagnostic_summary=preview.preview_matrix_diagnostic_summary,
            jsonable_capture=preview.jsonable_capture,
            profile_store_factory=preview.profile_store_factory,
        )
    )


def build_signed_acceptance_evidence_runner(
    *, providers: EvidenceRunnerProviders | None = None
) -> SignedAcceptanceMatrixRunner:
    """Build the Qt-backed signed matrix runner lazily."""

    from foliaseal.presentation.qt.signed_acceptance_matrix_runner import (
        SignedAcceptanceMatrixRunner,
        SignedAcceptanceMatrixRunnerDeps,
    )
    if providers is None:
        from foliaseal.presentation.qt.interactive_harness import (
            build_evidence_runner_providers,
        )

        providers = build_evidence_runner_providers()
    signed = providers.signed

    return SignedAcceptanceMatrixRunner(
        deps=SignedAcceptanceMatrixRunnerDeps(
            load_qt_harness_bindings=signed.load_qt_harness_bindings,
            load_preview_matrix_manifest=signed.load_preview_matrix_manifest,
            build_signing_executor=signed.build_signing_executor,
            build_dummy_timestamper=signed.build_dummy_timestamper,
            load_page_count=signed.load_page_count,
            build_workspace=signed.build_workspace,
            execute_signed_acceptance_scenario=signed.execute_signed_acceptance_scenario,
            preview_matrix_error_result=signed.preview_matrix_error_result,
            signed_matrix_diagnostic_summary=signed.signed_matrix_diagnostic_summary,
            evaluate_signed_matrix_acceptance_expectations=(
                signed.evaluate_signed_matrix_acceptance_expectations
            ),
            jsonable_capture=signed.jsonable_capture,
            render_backend_factory=signed.render_backend_factory,
            profile_store_factory=signed.profile_store_factory,
            create_workspace=signed.create_workspace,
        )
    )


def build_interactive_capture_operation() -> Callable[
    [EvidenceCaptureRequest], InteractiveHarnessCapture
]:
    """Return a lazy request callable for interactive capture."""

    runner: InteractiveCaptureEngine | None = None

    def run(request: EvidenceCaptureRequest) -> InteractiveHarnessCapture:
        nonlocal runner
        if runner is None:
            runner = build_interactive_capture_engine()
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


def build_evidence_harness_runtime() -> EvidenceHarnessRuntime:
    """Build explicit lazy evidence operations without loading heavy adapters."""

    return EvidenceHarnessRuntime(
        capture_operation=build_interactive_capture_operation(),
        preview_matrix_operation=build_preview_evidence_operation(),
        signed_acceptance_matrix_operation=build_signed_acceptance_evidence_operation(),
    )
