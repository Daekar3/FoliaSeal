"""Qt-free provider records for evidence-runner composition."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InteractiveEvidenceProviders:
    """Collaborators required by the interactive evidence capture engine."""

    load_qt_harness_bindings: Callable[..., Any]
    load_page_count: Callable[..., Any]
    render_backend_factory: Callable[..., Any]
    profile_store_factory: Callable[..., Any]
    build_signing_executor: Callable[..., Any]
    session_runner: Any
    capture_assembler: Any
    contract_evaluator: Callable[..., Any]
    capture_factory: Callable[..., Any]
    checklist_renderer: Callable[..., Any]
    report_finalizer: Callable[..., Any]
    artifact_policy: Any


@dataclass(frozen=True)
class PreviewMatrixEvidenceProviders:
    """Collaborators required by the headless preview matrix runner."""

    load_preview_matrix_manifest: Callable[..., Any]
    execute_headless_preview_matrix_scenario: Callable[..., Any]
    preview_matrix_error_result: Callable[..., Any]
    preview_matrix_diagnostic_summary: Callable[..., Any]
    jsonable_capture: Callable[..., Any]
    profile_store_factory: Callable[..., Any]


@dataclass(frozen=True)
class SignedAcceptanceEvidenceProviders:
    """Collaborators required by the signed-acceptance matrix runner."""

    load_qt_harness_bindings: Callable[..., Any]
    load_preview_matrix_manifest: Callable[..., Any]
    build_signing_executor: Callable[..., Any]
    build_dummy_timestamper: Callable[..., Any]
    load_page_count: Callable[..., Any]
    build_workspace: Callable[..., Any]
    execute_signed_acceptance_scenario: Callable[..., Any]
    preview_matrix_error_result: Callable[..., Any]
    signed_matrix_diagnostic_summary: Callable[..., Any]
    evaluate_signed_matrix_acceptance_expectations: Callable[..., Any]
    jsonable_capture: Callable[..., Any]
    render_backend_factory: Callable[..., Any]
    profile_store_factory: Callable[..., Any]
    create_workspace: Callable[..., Any]


@dataclass(frozen=True)
class EvidenceRunnerProviders:
    """Operation-scoped evidence providers assembled by the Qt harness."""

    interactive: InteractiveEvidenceProviders
    preview: PreviewMatrixEvidenceProviders
    signed: SignedAcceptanceEvidenceProviders
