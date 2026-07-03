# Migrate signed-acceptance execution to the workspace snapshot seam

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the signed-acceptance executor reads one structured workspace snapshot instead of separately probing the current request and then asking for a legacy dict capture. Users do not see a workflow change, but this makes the executor follow the new hybrid boundary more directly and reduces one remaining compatibility caller.

You can verify the change by running the signed-acceptance executor tests and seeing that the result payload is unchanged while the fake workspace is exercised through `capture_snapshot(...)` instead of `current_request()` plus `capture_state(...)`.

## Child ExecPlan Dependencies

- [x] (2026-07-02 02:40Z) `docs/ExecPlans/phase3_harness_workspace_snapshot_execplan.md` completed the additive workspace snapshot seam that this caller migration depends on.
- [x] (2026-07-02 02:40Z) No child ExecPlans are required for this bounded single-caller migration.

## Progress

- [x] (2026-07-02 02:39Z) Used an `explorer-light` subagent to compare the remaining caller sites and confirm the signed-acceptance executor is the smallest safe next migration.
- [x] (2026-07-02 02:43Z) Migrated `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` to `capture_snapshot(...)`.
- [x] (2026-07-02 02:43Z) Updated `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` to prove the executor no longer depends on `current_request()` or `capture_state(...)`.
- [x] (2026-07-02 02:47Z) Ran focused validation, completed the compliance review, and recorded the outcome.

## Surprises & Discoveries

- Observation: the session runner is still a larger follow-up seam because it mixes sign-success callbacks, manual capture state, and final-state fallback.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` still reads `last_signing_result()`, `current_request()`, and `capture_state(...)` at multiple points.
- Observation: the architecture doc still attributed preview refresh ownership to the executor even though the matrix runner performs that step before invoking the executor.
  Evidence: `docs/ARCHITECTURE.md` described executor-owned preview refresh while `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` calls `workspace.refresh_viewer()` before scenario execution.

## Decision Log

- Decision: migrate only `Phase3SignedAcceptanceScenarioExecutor.run()` in this slice and leave `Phase3HarnessSessionRunner` untouched.
  Rationale: the executor has a single request/capture read pair and can switch to one `capture_snapshot(...)` call without widening the change into interactive session control.
  Date/Author: 2026-07-02 / Codex

## Outcomes & Retrospective

This slice should leave the signed-acceptance result payload unchanged while removing one caller from the legacy probe-plus-dict path. Success means `Phase3SignedAcceptanceScenarioExecutor` can build its output from `Phase3HarnessWorkspaceSnapshot` and the remaining compatibility methods stay available for other callers.

Completed on 2026-07-02. The executor now reads one workspace snapshot and no longer depends on `current_request()` or `capture_state(...)`. Focused tests, lint, and whitespace checks all passed. The compliance review found one stale architecture ownership line around preview refresh; that wording was corrected in this slice.

## Context and Orientation

The relevant runtime file is `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`. That module owns one signed-acceptance scenario row: it applies the scenario, builds a workspace adapter, captures preview state, optionally submits a signing request, and shapes the result payload for the matrix runner.

The workspace boundary it consumes lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. That boundary now exposes `capture_snapshot(...) -> Phase3HarnessWorkspaceSnapshot`, where the snapshot object contains both the current signing request and the preview capture payload. The older compatibility methods `current_request()` and `capture_state(...)` still exist, but they are no longer the preferred path for new caller logic.

The focused unit tests for this executor live in `tests/unit/test_phase3_signed_acceptance_scenario_executor.py`. Those tests already prove result shaping and are the right place to make the caller migration observable by using a fake workspace that only supports `capture_snapshot(...)`.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`. Replace the separate `workspace.current_request()` and `workspace.capture_state(...)` reads with one `workspace.capture_snapshot(...)` call. Use `snapshot.current_request` for the later signing branch and use the snapshot fields directly when assembling `result` and the signed-output comparison call.

Second, edit `tests/unit/test_phase3_signed_acceptance_scenario_executor.py`. Extend the fake workspace so it returns a `Phase3HarnessWorkspaceSnapshot` and records the capture command passed into `capture_snapshot(...)`. Make `current_request()` and `capture_state(...)` fail fast if called so the migration is enforced by the test.

Finally, run focused validation. If the compliance review finds documentation drift, update the affected docs in this slice. Do not migrate `phase3_harness_session_runner.py` here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the executor, focused tests, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py
       apply_patch ... on tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       apply_patch ... on docs/ExecPlans/phase3_signed_acceptance_snapshot_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `Phase3SignedAcceptanceScenarioExecutor` reads preview and request state from `capture_snapshot(...)`;
- the executor no longer needs `workspace.current_request()` or `workspace.capture_state(...)`;
- the returned result payload remains behaviorally unchanged for both preview-only and successful-signing test cases;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_scenario_executor.py

Then run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py
    git diff --check

Acceptance is behavioral. The result payload keys and values used by the signed-acceptance matrix should stay the same, but the caller should now consume the structured workspace snapshot directly.

## Idempotence and Recovery

This is a narrow caller migration and is safe to retry. If a test fails, prefer fixing the fake workspace or the snapshot-field wiring rather than reintroducing the legacy `current_request()` or `capture_state(...)` calls.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` reading `capture_snapshot(...)`;
- `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` proving the executor does not fall back to legacy workspace methods;
- focused test and lint output passing after the migration.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interface at the end of the slice should be:

    class Phase3SignedAcceptanceScenarioExecutor:
        def run(...) -> dict[str, Any]:
            ...

Inside `run(...)`, the workspace interaction should use:

    snapshot = workspace.capture_snapshot(
        Phase3HarnessCaptureCommand(...)
    )
    request = snapshot.current_request

The executor should continue returning the same result payload shape expected by the matrix runner, including `preview_snapshot`, `preview_text`, `validation_text`, `sign_request_snapshot`, `backend_reservation_snapshot`, and the signed-output comparison fields.
