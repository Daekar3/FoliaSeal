"""Pure reporting helpers for Phase 3 harness captures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from foliaseal.application.qa_evidence_contract import EvidenceContractEvaluation


@dataclass(frozen=True)
class Phase3HarnessReportRequest:
    """Inputs needed to finalize one harness capture after Qt execution ends."""

    capture_payload: dict[str, Any]
    summary_json_path: str | None
    checklist_results_path: str
    checklist_template_path: str


@dataclass(frozen=True)
class Phase3HarnessReportResult:
    """Finalized harness capture plus the rendered checklist text."""

    capture: Any
    contract: EvidenceContractEvaluation
    checklist_results: str


def finalize_phase3_harness_report(
    request: Phase3HarnessReportRequest,
    *,
    contract_evaluator,
    capture_factory,
    checklist_renderer,
    text_writer,
) -> Phase3HarnessReportResult:
    """Finalize the saved evidence payload for one interactive harness run."""

    payload = dict(request.capture_payload)
    contract = contract_evaluator(payload)
    capture = capture_factory(
        capture_payload=payload,
        contract=contract,
        summary_json_path=request.summary_json_path,
        checklist_results_path=request.checklist_results_path,
        checklist_results_written=bool(request.checklist_results_path),
    )
    text_writer(target_path=request.summary_json_path, content=capture.to_json() + "\n")
    checklist_results = checklist_renderer(
        capture,
        checklist_template_path=request.checklist_template_path,
    )
    text_writer(target_path=request.checklist_results_path, content=checklist_results)
    return Phase3HarnessReportResult(
        capture=capture,
        contract=contract,
        checklist_results=checklist_results,
    )
