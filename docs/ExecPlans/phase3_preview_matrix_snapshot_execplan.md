# Migrate preview-matrix helper captures to the workspace snapshot seam

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, both preview-matrix helper paths in `phase3_harness.py` read workspace snapshots instead of calling the legacy `capture_state(...)` shim directly. Users do not see a workflow change, but the remaining preview-matrix callers align with the hybrid snapshot boundary and the only legacy methods left on the workspace port are explicit compatibility shims.

You can verify the change by running the preview-matrix focused tests and seeing that both the live-shell and headless helper paths still return the same result payload while their fake workspaces fail immediately if `capture_state(...)` is used.

## Child ExecPlan Dependencies

- [x] (2026-07-03 03:40Z) `docs/ExecPlans/phase3_harness_workspace_snapshot_execplan.md` completed the additive workspace snapshot seam used by the preview-matrix helpers.
- [x] (2026-07-03 03:40Z) `docs/ExecPlans/phase3_signed_acceptance_snapshot_execplan.md` and `docs/ExecPlans/phase3_harness_session_runner_snapshot_execplan.md` established the caller-migration pattern of consuming snapshots while preserving downstream dict payloads.
- [x] (2026-07-03 03:40Z) No child ExecPlans are required for this bounded two-helper migration.

## Progress

- [x] (2026-07-03 03:38Z) Used an `explorer-light` subagent to confirm the next safe slice is only the two preview-matrix helper call sites in `src/foliaseal/presentation/qt/phase3_harness.py`.
- [x] (2026-07-03 03:46Z) Migrated `_execute_preview_matrix_scenario()` and `_execute_headless_preview_matrix_scenario()` to `capture_snapshot(...).as_mapping()`.
- [x] (2026-07-03 03:47Z) Added focused tests that fail if the preview-matrix helpers still call `capture_state(...)`.
- [x] (2026-07-03 03:51Z) Ran focused validation, completed the compliance review, and recorded the outcome.

## Surprises & Discoveries

- Observation: the remaining preview-matrix callers do not consume `current_request` or `last_signing_result`, so converting snapshots back to dicts is safe for this slice.
  Evidence: both helper results only expose `preview_snapshot`, `preview_text`, `validation_text`, `sign_request_snapshot`, and `backend_reservation_snapshot`.
- Observation: the first test failure was only stale expected scenario slugs, not a seam regression.
  Evidence: the new tests initially expected `scenario-a` / `scenario-b`, but `_scenario_slug()` still emits `scenario_a` / `scenario_b`; updating the expectations made the focused test slice pass.

## Decision Log

- Decision: keep `capture_state()`, `current_request()`, and `last_signing_result()` on `Phase3HarnessWorkspacePort` for now.
  Rationale: removing compatibility methods in the same slice would widen scope beyond the two preview-matrix helpers and break existing fakes or documentation without additional user-visible value.
  Date/Author: 2026-07-03 / Codex

## Outcomes & Retrospective

This slice should remove the last direct preview-matrix uses of `capture_state(...)` while leaving the workspace port compatibility surface intact. Success means both live and headless preview-matrix helpers consume snapshots and the result payload remains unchanged.

Completed on 2026-07-03. Both preview-matrix helpers now consume `capture_snapshot(...).as_mapping()`, the new tests fail if either helper calls `capture_state(...)`, and the focused preview-matrix validation passed. The compliance review found no architecture or spec drift.

## Context and Orientation

The remaining preview-matrix helpers live in `src/foliaseal/presentation/qt/phase3_harness.py`. `_execute_preview_matrix_scenario()` drives the live-shell path and `_execute_headless_preview_matrix_scenario()` drives the headless path. Both functions build a workspace adapter, apply a scenario, capture preview state, and return a result row used by the preview-matrix runner.

The workspace boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. It already exposes `capture_snapshot(...) -> Phase3HarnessWorkspaceSnapshot`, and that snapshot object can be converted back to the existing dict payload with `as_mapping()`.

The focused tests live in `tests/unit/test_phase3_harness.py`. This file already covers preview-matrix helpers and is the right place to add fake workspaces that raise if `capture_state(...)` is used.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness.py`. In both preview-matrix helper functions, replace the direct `workspace.capture_state(...)` call with `workspace.capture_snapshot(...)` followed by `as_mapping()`. Keep the returned result-row shape exactly the same.

Second, edit `tests/unit/test_phase3_harness.py`. Add one focused test for the live preview-matrix helper and one for the headless helper. Each fake workspace should implement `capture_snapshot(...)`, record the `Phase3HarnessCaptureCommand`, and raise if `capture_state(...)` is called.

Finally, run focused validation. If the compliance review finds only stale documentation wording, fix it in this slice. Do not remove compatibility methods from the workspace port here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the preview-matrix helpers, focused tests, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py
       apply_patch ... on tests/unit/test_phase3_harness.py
       apply_patch ... on docs/ExecPlans/phase3_preview_matrix_snapshot_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py -k 'preview_matrix or run_phase3_preview_matrix'
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `_execute_preview_matrix_scenario()` and `_execute_headless_preview_matrix_scenario()` consume `capture_snapshot(...)`;
- both helper results remain behaviorally unchanged;
- focused tests fail if `capture_state(...)` is used and pass after the migration;
- focused lint and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py -k 'preview_matrix or run_phase3_preview_matrix'

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The preview-matrix helpers should still return the same result-row fields, but they should now obtain that data from the structured snapshot seam rather than the legacy dict shim.

## Idempotence and Recovery

This is a narrow caller migration and is safe to retry. If a test fails, prefer fixing the fake workspace or the snapshot-to-dict adaptation rather than reintroducing `capture_state(...)`.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_harness.py` consuming `capture_snapshot(...)` in both preview-matrix helpers;
- focused tests in `tests/unit/test_phase3_harness.py` that fail if `capture_state(...)` is used;
- focused test and lint output passing after the migration.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of the slice, both preview-matrix helper functions should follow this pattern:

    snapshot = workspace.capture_snapshot(
        Phase3HarnessCaptureCommand(...)
    )
    capture = snapshot.as_mapping()

The workspace port itself should remain unchanged in this slice; compatibility methods stay available for later removal work.
