"""Interactive Phase 3 capture contract and lazy composition boundary."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from foliaseal.application import SigningDraftWorkflow
from foliaseal.application.phase3_evidence_service import Phase3HarnessCaptureRequest
from foliaseal.application.viewer_session import ViewerSession
from foliaseal.application.viewer_workflow import ViewerWorkflow
from foliaseal.presentation.qt.phase3_harness_capture_assembler import (
    Phase3HarnessCaptureAssembler,
)
from foliaseal.presentation.qt.phase3_harness_reporting import (
    Phase3HarnessReportRequest,
)
from foliaseal.presentation.qt.phase3_harness_session_runner import (
    Phase3HarnessSessionRunner,
    _QtHarnessBindings,
)


@dataclass(frozen=True)
class Phase3HarnessCapture:
    """Structured capture emitted by the interactive Phase 3 harness."""

    pdf_path: str
    summary_json_path: str | None
    summary_json_written: bool
    checklist_results_path: str
    checklist_results_written: bool
    first_render_ms: float | None
    selection_count: int
    sign_request_count: int
    last_signature_page_index: int | None
    last_signature_page_number: int | None
    last_signature_has_visible_appearance: bool
    last_signature_output_path: str | None
    last_signing_result_message: str | None
    last_signing_result_success: bool | None
    preview_snapshot: dict[str, Any]
    sign_request_snapshot: dict[str, Any] | None
    backend_reservation_snapshot: dict[str, Any] | None
    backend_reservation_error: str | None
    output_file_exists: bool
    output_file_size_bytes: int | None
    output_signature_count: int | None
    output_signature_snapshot: dict[str, Any] | None
    output_visible_appearance_snapshot: dict[str, Any] | None
    preview_available: bool
    preview_text: str
    validation_text: str
    evidence_contract_version: str
    acceptance_tier: str
    gate_verdict: str
    evidence_validation_passed: bool
    evidence_validation_errors: tuple[str, ...]
    evidence_validation_warnings: tuple[str, ...]
    interaction_counts: dict[str, int]
    errors: tuple[str, ...]
    output_verification_snapshot: dict[str, Any] | None = None
    signed_output_render_snapshot: dict[str, Any] | None = None
    signed_output_preview_comparison: dict[str, Any] | None = None
    signed_runs: tuple[dict[str, Any], ...] = ()
    captured_states: tuple[dict[str, Any], ...] = ()
    captured_state_transition_diagnostics: tuple[dict[str, Any], ...] = ()

    def to_json(self) -> str:
        """Return the stable JSON representation used by acceptance tooling."""

        return json.dumps(jsonable_capture(self), indent=2, sort_keys=True)


@dataclass(frozen=True)
class Phase3InteractiveCaptureArtifactPolicy:
    """Artifact-path and optional-text policy for one interactive capture."""

    default_artifacts_dir: Callable[..., str | None]
    output_pdf_path: Callable[..., str]
    write_text: Callable[..., None]


@dataclass(frozen=True)
class Phase3InteractiveHarnessRunner:
    """Interactive capture runner hiding session, artifact, and report choreography."""

    load_qt_harness_bindings: Callable[[], _QtHarnessBindings]
    load_page_count: Callable[..., int]
    render_backend_factory: Callable[[], Any]
    profile_store_factory: Callable[[], Any]
    build_phase3_signing_executor: Callable[[], Any]
    session_runner: Phase3HarnessSessionRunner
    capture_assembler: Phase3HarnessCaptureAssembler
    contract_evaluator: Callable[..., Any]
    capture_factory: Callable[..., Phase3HarnessCapture]
    checklist_renderer: Callable[..., str]
    report_finalizer: Callable[..., Any]
    artifact_policy: Phase3InteractiveCaptureArtifactPolicy

    def run(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture:
        bindings = self.load_qt_harness_bindings()
        source_path = Path(request.pdf_path)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF does not exist: {request.pdf_path}")
        artifacts_dir = self.artifact_policy.default_artifacts_dir(
            summary_json_path=request.summary_json_path,
            artifacts_dir=request.artifacts_dir,
        )

        page_count = self.load_page_count(bindings=bindings, pdf_path=str(source_path))
        backend = self.render_backend_factory()
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
            output_pdf_path=self.artifact_policy.output_pdf_path(
                pdf_path=str(source_path),
                artifacts_dir=artifacts_dir,
                sign_attempt_index=1,
            ),
            certificate_path=request.certificate_path,
            passphrase=request.passphrase,
            tsa_url="https://tsa.example.invalid",
            timestamp_required=False,
        )
        session = self.session_runner.run(
            bindings=bindings,
            source_path=source_path,
            artifacts_dir=artifacts_dir,
            viewer_workflow=viewer_workflow,
            signing_workflow=signing_workflow,
            profile_store=self.profile_store_factory(),
            sign_executor=self.build_phase3_signing_executor(),
            capture_assembler=self.capture_assembler,
        )
        capture_payload = self.capture_assembler.build_capture_payload(
            source_path=source_path,
            summary_json_path=request.summary_json_path,
            checklist_results_path=request.checklist_results_path,
            artifacts_dir=artifacts_dir,
            session=session,
        )
        report = self.report_finalizer(
            Phase3HarnessReportRequest(
                capture_payload=capture_payload,
                summary_json_path=request.summary_json_path,
                checklist_results_path=request.checklist_results_path,
                checklist_template_path=request.checklist_template_path,
            ),
            contract_evaluator=self.contract_evaluator,
            capture_factory=self.capture_factory,
            checklist_renderer=self.checklist_renderer,
            text_writer=self.artifact_policy.write_text,
        )
        capture = report.capture
        if request.summary_json_path is None:
            print("Phase 3 harness capture")
            print(capture.to_json())
            print()
        else:
            print("Phase 3 harness capture written")
            print(f"- summary json: {request.summary_json_path}")
            print(f"- acceptance tier: {capture.acceptance_tier}")
            print(f"- gate verdict: {capture.gate_verdict}")
            print(f"- validation: {capture.validation_text}")
            print(f"- captured states: {len(capture.captured_states)}")
            print()
        print(f"Checklist results file: {request.checklist_results_path}")
        print("Review the pre-checked items, complete the remaining manual-only checks, and")
        print("use the generated file as the acceptance worksheet for Phase 3.")
        return capture


def build_interactive_evidence_capture_runner() -> Callable[
    [Phase3HarnessCaptureRequest], Phase3HarnessCapture
]:
    """Build the interactive runner lazily without importing the Qt harness graph."""

    runner: Phase3InteractiveHarnessRunner | None = None

    def run(request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture:
        nonlocal runner
        if runner is None:
            from foliaseal.presentation.qt.evidence_runner_factories import (
                build_interactive_evidence_runner,
            )

            runner = build_interactive_evidence_runner()
        return runner.run(request)

    return run


def jsonable_capture(value: Any) -> Any:
    """Convert capture and evidence values to stable JSON-compatible values."""

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {field.name: jsonable_capture(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): jsonable_capture(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable_capture(item) for item in value]
    return str(value)


def default_harness_artifacts_dir(
    *,
    summary_json_path: str | None,
    artifacts_dir: str | None,
) -> str | None:
    if artifacts_dir is not None:
        return artifacts_dir
    if summary_json_path is None:
        return None
    summary_path = Path(summary_json_path)
    return str(summary_path.with_name(f"{summary_path.stem}_artifacts"))


def default_harness_output_pdf_path(
    *,
    pdf_path: str,
    artifacts_dir: str | None,
    sign_attempt_index: int = 1,
) -> str:
    source_path = Path(pdf_path)
    if artifacts_dir is None:
        return str(source_path.with_name(source_path.stem + "-signed.pdf"))
    target_dir = Path(artifacts_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    return str(target_dir / f"{source_path.stem}_harness_signed_{sign_attempt_index:03d}.pdf")


def write_optional_text(*, target_path: str | None, content: str) -> None:
    if target_path is None:
        return
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
