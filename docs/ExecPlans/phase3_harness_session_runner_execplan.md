# Separate Interactive Harness Execution From Capture Assembly

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice is complete. The interactive Phase 3 harness still behaves the same for users, but the Qt session now returns `Phase3HarnessSessionResult` from `_run_phase3_harness_session()`, and `_build_phase3_harness_capture_payload()` converts that raw session state into the capture payload consumed by report finalization.

That matters because later contributors will be able to test interactive-harness orchestration and capture assembly separately instead of patching the whole path at once.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_reporting_boundary_execplan.md` was complete first, so this slice could assume the report-finalization boundary already existed.

## Progress

- [x] The session-runner boundary landed in `src/foliaseal/presentation/qt/phase3_harness.py`.

## Surprises & Discoveries

- Observation: `phase3_harness.py` now splits interactive session collection from capture payload assembly.
  Evidence: `Phase3HarnessSessionResult`, `_run_phase3_harness_session()`, and `_build_phase3_harness_capture_payload()` are present in `src/foliaseal/presentation/qt/phase3_harness.py`.

## Decision Log

- Decision: keep report finalization in `phase3_harness_reporting.py` and only move interactive session/raw payload assembly into `phase3_harness.py`.
  Rationale: that keeps the reporting boundary pure while making the interactive harness path smaller and testable.
  Date/Author: 2026-06-03 / Codex

## Outcomes & Retrospective

This slice is complete. The interactive harness now has an explicit session-runner result boundary, and report finalization remains isolated behind `phase3_harness_reporting.py`.

## Context and Orientation

Now, `run_phase3_signing_harness()` in `src/foliaseal/presentation/qt/phase3_harness.py` delegates the interactive Qt lifecycle to `_run_phase3_harness_session()`. That helper creates the application window, wires shell callbacks, tracks signed runs and captured states, and returns `Phase3HarnessSessionResult`, which `_build_phase3_harness_capture_payload()` uses to assemble the raw payload for report finalization.

The reporting-boundary child plan already separated the post-session reporting work. This child plan finishes the remaining seam by keeping the interactive execution path focused on raw session state and by moving capture payload assembly out of the Qt loop.

## Plan of Work

`Phase3HarnessSessionResult` now lives in `src/foliaseal/presentation/qt/phase3_harness.py`. It contains the raw state accumulated during the interactive run: sign requests, signed runs, error messages, interaction counts, captured states, and the final preview/request/backend snapshots.

`run_phase3_signing_harness()` now delegates the interactive Qt lifecycle to `_run_phase3_harness_session()` and then passes the session result through `_build_phase3_harness_capture_payload()` into the existing reporting/capture-finalization boundary. Public behavior and output schemas remain unchanged.

Direct tests can exercise the session-runner boundary through fake Qt bindings, and the existing harness tests cover the new helper split.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Expected edit surfaces:

    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_phase3_harness.py
    docs/ExecPlans/phase3_harness_session_runner_execplan.md
    docs/ExecPlans/phase3_evidence_service_program_execplan.md

## Validation and Acceptance

This slice is accepted. The interactive Qt session now returns a smaller raw result boundary, final capture assembly no longer depends on inline local variables from the Qt loop, and the focused harness tests still pass with unchanged output behavior.

## Idempotence and Recovery

The migration is complete, so there is no temporary adapter to keep around.

## Artifacts and Notes

Forbidden changes for this slice:

- changes to JSON/schema shape,
- changes to signed-acceptance matrix counters,
- unrelated CLI parser changes.

## Interfaces and Dependencies

This slice introduced an explicit session-runner result type and a corresponding runner function. The dependency category remains `Local-substitutable` because the behavior is still driven by Qt doubles and in-memory Python state in tests.

Revision note: created on 2026-06-03 as child plan 2 of the Phase 3 evidence-service program.
