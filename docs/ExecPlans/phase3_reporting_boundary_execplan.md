# Extract A Pure Phase 3 Reporting Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice is complete: `run_phase3_signing_harness()` still launches the same interactive Qt harness and emits the same evidence outputs, but report finalization now lives behind `src/foliaseal/presentation/qt/phase3_harness_reporting.py`. A contributor can see one explicit reporting boundary that takes raw capture payload data and handles evidence-contract evaluation, capture construction, checklist rendering, and file writes without needing to follow the full Qt session path.

The user-visible proof is unchanged behavior with a smaller seam: the same checklist Markdown, the same saved JSON, the same contract verdicts, and the same CLI validation path.

## Child ExecPlan Dependencies

- [x] (2026-06-03 03:01Z) No child ExecPlans are required for this first slice.

## Progress

- [x] (2026-06-03 03:01Z) Investigated the Phase 3 harness seam and chose reporting extraction as the first safe slice.
- [x] (2026-06-03 03:01Z) Wrote this ExecPlan before implementation.
- [x] Introduce a pure reporting helper boundary that finalizes a harness capture from raw payload data.
- [x] Route `run_phase3_signing_harness()` through that helper without changing `Phase3HarnessCapture` JSON/schema shape.
- [x] Add direct tests for the new reporting helper boundary and keep the existing harness and CLI validation behavior green.
- [x] Run compliance review and reconcile docs if needed.

## Surprises & Discoveries

- Observation: the reporting boundary is already mostly pure even though it is embedded in the harness function.
  Evidence: contract evaluation, `Phase3HarnessCapture` construction, JSON writing, and checklist Markdown writing happen after the interactive Qt session has already ended.

- Observation: the extracted reporting module now gives the harness a direct boundary that can be tested without the interactive Qt session path.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_reporting.py` centralizes finalization, and `tests/unit/test_phase3_harness_reporting.py` exercises it directly.

## Decision Log

- Decision: do not move matrix summary shaping, signed-acceptance evidence orchestration, or CLI routing in this slice.
  Rationale: the first slice should prove the reporting boundary with minimal behavioral risk and no schema churn.
  Date/Author: 2026-06-03 / Codex

- Decision: preserve `Phase3HarnessCapture` and `build_phase3_checklist_results_markdown()` semantics exactly.
  Rationale: both are already covered heavily by tests and are referenced from the documented acceptance workflow.
  Date/Author: 2026-06-03 / Codex

## Outcomes & Retrospective

This slice is complete. The reporting boundary now lives in `src/foliaseal/presentation/qt/phase3_harness_reporting.py`, the Qt harness delegates to it after raw state collection, and the saved evidence shape remains unchanged.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` currently defines `Phase3HarnessCapture`, `build_phase3_checklist_results_markdown()`, and `run_phase3_signing_harness()`. The harness function launches the Qt shell, tracks sign requests and captured states, assembles a dictionary payload describing the run, and then delegates report finalization to `src/foliaseal/presentation/qt/phase3_harness_reporting.py`.

`src/foliaseal/presentation/qt/phase3_harness_reporting.py` now owns the pure reporting seam for Phase 3 harness captures. It defines `Phase3HarnessReportRequest`, `Phase3HarnessReportResult`, and `finalize_phase3_harness_report()`, evaluates the evidence contract, materializes `Phase3HarnessCapture`, writes the summary JSON, renders checklist Markdown, writes the checklist file, and returns the finalized capture plus rendered checklist text for the harness to summarize.

The architectural problem is not the existence of the harness function. The problem is that execution and reporting are fused. A later contributor who only wants to change reporting semantics or contract-evaluation wiring still has to reason through the interactive harness path. This slice separates those concerns without changing the observable outputs.
The direct test surface now sits on `tests/unit/test_phase3_harness_reporting.py`, which can exercise report finalization without the interactive Qt session path.

## Plan of Work

Create a new pure helper module under `src/foliaseal/presentation/qt/` for Phase 3 harness reporting. That helper should define a small request/result boundary for “finalize this raw capture payload.” It must accept the raw payload, the summary/checklist target paths, and injected callables for contract evaluation, checklist rendering, capture construction, and text writing. It should return a result object that contains the finalized `Phase3HarnessCapture` and the rendered checklist Markdown.

In `src/foliaseal/presentation/qt/phase3_harness.py`, extract the existing payload-to-capture logic into a small capture-construction helper, then replace the inline reporting tail in `run_phase3_signing_harness()` with one call into the new reporting helper. Keep the CLI-style console prints in the harness function for now; they are part of execution presentation, not the pure reporting boundary.

Add direct unit tests for the reporting helper so the first boundary test no longer needs to monkeypatch the entire interactive harness path. Keep the existing checklist, evidence-contract, capture-serialization, and CLI validation tests passing.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/phase3_harness.py
    src/foliaseal/presentation/qt/phase3_harness_reporting.py
    tests/unit/test_phase3_harness.py
    tests/unit/test_phase3_harness_reporting.py
    docs/ExecPlans/phase3_reporting_boundary_execplan.md
    docs/ExecPlans/phase3_evidence_service_program_execplan.md

Run focused validation:

    pytest tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_main_cli.py
    ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_reporting.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_main_cli.py
    git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `run_phase3_signing_harness()` no longer performs contract evaluation and artifact writing inline.
- one explicit reporting helper finalizes raw payload data into `Phase3HarnessCapture` and checklist output.
- `Phase3HarnessCapture.to_json()` output remains unchanged.
- `build_phase3_checklist_results_markdown()` behavior remains unchanged.
- `foliaseal phase3-harness-validate` still routes through the same contract evaluator and keeps the same pass/fail behavior.
- the focused harness, reporting, and CLI tests pass.

## Idempotence and Recovery

This is a behavior-preserving refactor. It is safe to retry. If a first pass leaves both the old inline report finalization and the new helper path active, remove the duplicate inline path before continuing. Do not keep two capture-finalization implementations in parallel.

## Artifacts and Notes

The forbidden changes for this slice are:

- changing the `Phase3HarnessCapture` JSON/schema shape,
- changing matrix summary schemas or counters,
- changing CLI command names or parser wiring.

The allowed change classes are behavior-preserving architecture change plus documentation/status updates for this slice only.

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/phase3_harness_reporting.py` must define a small reporting seam with stable request/result types and one finalization function. The exact internal names can vary, but the boundary must look like “finalize a raw harness payload into a capture plus rendered checklist,” with injected callables for contract evaluation and file writing so direct tests can use fakes.

The dependency categories are:

- `In-process` for payload shaping, contract evaluation, and result assembly.
- `Local-substitutable` for optional filesystem writes through injected writer callables.

Revision note: created on 2026-06-03 as child plan 1 of the Phase 3 evidence-service program.
