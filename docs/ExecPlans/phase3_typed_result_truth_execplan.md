# Preserve failure truth in typed Phase 3 evidence results

> **Historical / incorporated (2026-08-01):** The typed-result decisions in this child plan are
> now implemented in `phase3_evidence_core.py`; references to legacy raw service wrappers describe
> the pre-cleanup state and are not active API guidance.

This ExecPlan is a child of `docs/ExecPlans/phase3_evidence_gateway_signed_scenario_hybrid_execplan.md` and is maintained according to `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Typed Phase 3 matrix results must tell callers the same truth as the serialized evidence. A signed matrix containing scenario error rows must never be reported as passed merely because its acceptance counters are zero. Aggregate signed-evidence rows must also preserve a custom runner-provided `summary_json_path`, so in-memory and nonstandard artifact adapters remain testable.

## Child ExecPlan Dependencies

- [x] The parent hybrid slice and its lifecycle/artifact ports are complete.
- [x] The required architecture/spec compliance review identified the two gaps addressed here.

## Progress

- [x] (2026-07-31) Confirmed the signed normalization branch ignores `error_scenario_count` and that aggregate rows reconstruct summary paths.
- [x] (2026-07-31) Added regression tests for scenario-error truth and custom summary paths; both failed before the implementation fix.
- [x] (2026-07-31) Implemented the smallest application-service fixes without changing raw summary schemas or CLI behavior.
- [x] (2026-07-31) Ran focused Phase 3 evidence/gateway/matrix validation (23 passed), the full suite (1,011 passed with one pre-existing Pillow deprecation warning), and Ruff (clean); release-fidelity counters remain the parent's recorded eight-scenario baseline.
- [x] (2026-07-31) Updated the parent plan, README, and architecture document with the corrected contract and validation evidence.

## Surprises & Discoveries

- Observation: Preview typed normalization already checks `error_scenario_count`, but signed normalization only checks acceptance expectations and critical counters.
  Evidence: `src/foliaseal/application/phase3_evidence_service.py::_normalize_matrix_result()`.
- Observation: The signed runner now publishes an authoritative summary path, but aggregate evidence rows derive `artifacts_dir / summary.json` instead of reading that field.
  Evidence: `_matrix_summary_row()` in the same service module.

## Decision Log

- Decision: Add only the missing error-row and summary-path checks; do not redesign the gateway or introduce another orchestrator.
  Rationale: both fixes are local contract corrections discovered by compliance review, and all existing compatibility surfaces must remain unchanged.
  Date/Author: 2026-07-31 / Codex.

## Outcomes & Retrospective

The typed signed result now reports nonzero scenario-error counts as failures, and aggregate matrix rows preserve a runner-provided authoritative summary path while retaining the legacy fallback. Focused Phase 3 evidence/gateway/matrix validation passed (23 tests), the full suite passed (1,011 tests with one pre-existing Pillow deprecation warning), and Ruff is clean. The parent plan retains the previously captured release-fidelity counters (eight scenarios, six signings, two intentional rejections, zero acceptance failures).

## Context and Orientation

`Phase3EvidenceService.signed_acceptance_matrix_result()` converts a raw signed-matrix mapping into `Phase3MatrixResult`. The mapping includes `error_scenario_count`, acceptance expectation fields, critical zero-valued counters, `artifacts_dir`, and usually `summary_json_path`. `run_signed_acceptance_evidence()` converts each matrix mapping into `Phase3SignedAcceptanceMatrixResult` through `_matrix_summary_row()`. Existing CLI output and JSON fields are compatibility contracts and must not be renamed or removed.

## Plan of Work

In `src/foliaseal/application/phase3_evidence_service.py`, include nonzero `error_scenario_count` in signed typed-result errors and require it to be zero for `passed=True`. Reuse the existing error style used for critical counters. Make `_matrix_summary_row()` prefer a non-empty `summary_json_path` from the runner summary, falling back to `artifacts_dir / summary.json` only for legacy runners.

In `tests/unit/test_phase3_evidence_service.py`, add a signed typed-result regression with zero critical counters and one scenario error, asserting `passed` is false and the error names the scenario-error count. Add an aggregate-evidence regression whose fake runner returns a custom summary path and assert that path is retained in the typed matrix row.

Update the parent plan's progress, surprises, decision log, and outcomes with the findings and final test evidence.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_phase3_evidence_service.py
    .venv/bin/ruff check src/foliaseal/application/phase3_evidence_service.py tests/unit/test_phase3_evidence_service.py
    .venv/bin/pytest -q

Then rerun the parent plan's two offscreen release-fidelity matrix commands and verify the same eight-scenario counters and no leaked processes/windows.

## Validation and Acceptance

Acceptance requires a signed typed result with `error_scenario_count=1` to be `passed=False`, an aggregate row to retain a custom `summary_json_path`, all existing service/gateway/CLI tests to remain green, and both release-fidelity matrices to retain their prior counters and artifact contracts.

## Idempotence and Recovery

The changes are additive and safe to rerun. Do not rewrite generated evidence into the repository. If a regression fails, compare only the typed normalization and aggregate-row path selection; do not weaken the serialized compatibility contract.

## Artifacts and Notes

Generated matrix summaries remain under `/tmp/foliaseal-evidence-hybrid-preview` and `/tmp/foliaseal-evidence-hybrid-signed`. No generated PDFs or PNGs are tracked.

## Interfaces and Dependencies

The public interfaces remain unchanged. `_normalize_matrix_result()` and `_matrix_summary_row()` are internal helpers; their corrected behavior must preserve `Phase3MatrixResult`, `Phase3SignedAcceptanceMatrixResult`, raw mappings, and CLI output shapes.

## Revision Note

2026-07-31 / Codex: Created after the independent SPEC compliance review found that typed signed results could hide scenario errors and aggregate rows could discard custom authoritative summary paths.

2026-07-31 / Codex: Implemented both corrections and verified the focused Phase 3 evidence/gateway/matrix tests (23 passed), the full suite (1,011 passed with one pre-existing Pillow deprecation warning), and Ruff. The parent release-fidelity baseline remains unchanged and is recorded there.
