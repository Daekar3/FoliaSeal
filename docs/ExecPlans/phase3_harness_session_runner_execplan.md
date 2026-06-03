# Separate Interactive Harness Execution From Capture Assembly

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the interactive Phase 3 harness will still behave the same for users, but the Qt session will no longer directly assemble the final capture object. Instead, one session-runner boundary will return raw execution state and a separate capture assembler will own the final stable `Phase3HarnessCapture`.

That matters because later contributors will be able to test interactive-harness orchestration and capture assembly separately instead of patching the whole path at once.

## Child ExecPlan Dependencies

- [ ] `docs/ExecPlans/phase3_reporting_boundary_execplan.md` must be complete first, because this slice assumes the report-finalization boundary already exists.

## Progress

- [ ] Begin after the reporting-boundary slice lands.

## Surprises & Discoveries

- Observation: fill this section as the slice proceeds.
  Evidence: add concise test output or code references.

## Decision Log

- Decision: no decisions recorded yet.
  Rationale: this plan has not been implemented yet.
  Date/Author: 2026-06-03 / Codex

## Outcomes & Retrospective

This slice has not started yet.

## Context and Orientation

Today, `run_phase3_signing_harness()` in `src/foliaseal/presentation/qt/phase3_harness.py` owns both interactive session behavior and the assembly inputs for the final capture. It creates the application window, wires shell callbacks, tracks signed runs and captured states, and also determines the final payload that feeds the evidence contract and report output.

The reporting-boundary child plan will separate the post-session reporting work, but that still leaves the interactive execution path itself too wide. This child plan narrows that seam by introducing a session-runner result that contains the raw information needed for final capture assembly without yet being the final saved capture object.

## Plan of Work

Introduce a session-runner result type in `src/foliaseal/presentation/qt/phase3_harness.py` or a sibling module under `src/foliaseal/presentation/qt/`. That type should contain the raw state accumulated during the interactive run: sign requests, signed runs, error messages, interaction counts, captured states, and the final preview/request/backend snapshots.

Refactor `run_phase3_signing_harness()` so it delegates the interactive Qt lifecycle to one session-runner helper and then passes the session result into the existing reporting/capture-finalization boundary. Preserve all public behavior and output schemas.

Add direct tests for the session-runner boundary if they can be written with fake Qt bindings. Otherwise, keep the new tests at the smallest stable helper boundary available and leave only one high-level interactive harness smoke test.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Expected edit surfaces:

    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_phase3_harness.py
    docs/ExecPlans/phase3_harness_session_runner_execplan.md
    docs/ExecPlans/phase3_evidence_service_program_execplan.md

## Validation and Acceptance

This slice is accepted when the interactive Qt session returns a smaller raw result boundary, final capture assembly no longer depends on inline local variables from the Qt loop, and the focused harness tests still pass with unchanged output behavior.

## Idempotence and Recovery

Keep the old and new session paths from coexisting longer than necessary. If migration requires a temporary adapter, document it and remove it in the same slice before closing the plan.

## Artifacts and Notes

Forbidden changes for this slice:

- changes to JSON/schema shape,
- changes to signed-acceptance matrix counters,
- unrelated CLI parser changes.

## Interfaces and Dependencies

This slice should introduce an explicit session-runner result type and a corresponding runner function or class. The dependency category remains `Local-substitutable` because the behavior is still driven by Qt doubles and in-memory Python state in tests.

Revision note: created on 2026-06-03 as child plan 2 of the Phase 3 evidence-service program.
