# Migrate the interactive harness session runner to the workspace snapshot seam

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the interactive Phase 3 harness session runner reads one structured workspace snapshot whenever it needs current preview or signing state. Users do not see a workflow change, but the interactive runner stops reaching into the workspace through separate `current_request()`, `last_signing_result()`, and `capture_state(...)` compatibility methods.

You can verify the change by running the dedicated session-runner tests and seeing that the runner still returns the same raw session payload while the fake workspace fails immediately if any legacy probe method is used.

## Child ExecPlan Dependencies

- [x] (2026-07-03 03:10Z) `docs/ExecPlans/phase3_harness_workspace_snapshot_execplan.md` completed the additive workspace snapshot seam this runner migration depends on.
- [x] (2026-07-03 03:10Z) `docs/ExecPlans/phase3_signed_acceptance_snapshot_execplan.md` completed the first caller migration and confirmed the compatibility pattern for passing `snapshot.as_mapping()` into legacy downstream consumers.
- [x] (2026-07-03 03:10Z) No child ExecPlans are required for this bounded interactive-runner migration.

## Progress

- [x] (2026-07-03 03:08Z) Used an `explorer-light` subagent to confirm the session runner is the next safe caller migration and that preview-matrix callers should stay out of this slice.
- [x] (2026-07-03 03:16Z) Migrated `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` to use `capture_snapshot(...)` for manual, sign-time, and final capture reads.
- [x] (2026-07-03 03:16Z) Updated `tests/unit/test_phase3_harness_session_runner.py` to fail if the runner calls `current_request()`, `last_signing_result()`, or `capture_state(...)`.
- [x] (2026-07-03 03:23Z) Reconciled `docs/ARCHITECTURE.md` for the session-runner ownership wording and recorded validation/compliance results.

## Surprises & Discoveries

- Observation: the session runner is the first remaining caller that still uses all three compatibility reads in one control path.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` still calls `workspace.last_signing_result()`, `workspace.current_request()`, and `workspace.capture_state(...)` in the sign-success, manual-capture, and final-capture branches.
- Observation: the first validation failure was in the fake-workspace test harness, not in the production runner seam.
  Evidence: `tests/unit/test_phase3_harness_session_runner.py` initially tried to inspect a non-existent `shell._workspace`; storing the fake workspace explicitly fixed the failure and the focused test then passed.

## Decision Log

- Decision: keep `Phase3HarnessCaptureAssembler` unchanged and feed it `snapshot.as_mapping()` from the runner.
  Rationale: the assembler is already the stable dict-consuming boundary for raw session evidence, so changing it here would widen the slice without reducing risk.
  Date/Author: 2026-07-03 / Codex

- Decision: defer the `phase3_harness.py` preview-matrix `capture_state(...)` callers to a later loop.
  Rationale: those call sites live on a separate execution path and would mix interactive runner migration with matrix-path refactoring.
  Date/Author: 2026-07-03 / Codex

## Outcomes & Retrospective

This slice should remove the interactive runner from the legacy probe path while preserving the existing raw session payload and evidence assembly behavior. Success means the runner consumes snapshots directly, the assembler still receives dict-shaped state, and all user-visible harness outputs remain stable.

Completed on 2026-07-03. The session runner now consumes `Phase3HarnessWorkspaceSnapshot`, adapts snapshots back to dicts only where the capture assembler still expects them, and no longer calls `current_request()`, `last_signing_result()`, or `capture_state(...)` directly. Focused tests, lint, and whitespace checks all passed, and the compliance review found no architecture or spec drift beyond this plan needing status updates.

## Context and Orientation

The runtime file is `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`. That module owns the interactive Qt harness session: it builds the window and toolbar, listens for sign/error/status callbacks from the live shell, captures manual and final state, and returns `Phase3HarnessSessionResult` for later evidence assembly.

The workspace boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. It already exposes `capture_snapshot(...) -> Phase3HarnessWorkspaceSnapshot`, where the snapshot object contains the current request, last signing result, preview snapshot, preview text, validation text, and backend reservation evidence. The older `current_request()`, `last_signing_result()`, and `capture_state(...)` methods still exist only as compatibility helpers.

The downstream assembler lives in `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`. It still expects dict-shaped session states, so the runner should convert each snapshot back to the legacy mapping form with `snapshot.as_mapping()` before storing it or handing it to the assembler.

The focused enforcement test lives in `tests/unit/test_phase3_harness_session_runner.py`. That test currently fakes the legacy workspace probe methods, so it must be tightened so those methods raise if the runner still uses them.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`. Introduce a helper that calls `workspace.capture_snapshot(...)` for one capture operation and returns the structured snapshot. Use that helper in the sign-success path, the manual capture button path, and the final-state capture path. When the runner needs dict-shaped state for `signed_runs`, `captured_states`, or `final_state`, convert the snapshot with `as_mapping()`. When the runner needs `capture_request` or `last_signing_result`, read those fields from the final snapshot instead of probing the workspace separately.

Second, edit `tests/unit/test_phase3_harness_session_runner.py`. Convert the fake workspace to implement `capture_snapshot(...)` and record the commands it receives. Make `current_request()`, `last_signing_result()`, and `capture_state(...)` raise assertions so the test proves the migration happened. Keep the test expectations around artifact basenames, returned session payload, and success gating intact.

Third, update `docs/ARCHITECTURE.md` so the session-runner section describes snapshot consumption rather than separate probe reads. Leave `docs/SPEC.md` untouched unless behavior changes, which this slice should avoid.

Finally, run focused validation. If the compliance review finds only stale architecture wording, fix it in this slice. Do not migrate the preview-matrix callers in `phase3_harness.py` here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the session runner, focused test, architecture notes, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_session_runner.py
       apply_patch ... on tests/unit/test_phase3_harness_session_runner.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/phase3_harness_session_runner_snapshot_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py
       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_harness_session or run_phase3_signing_harness_orchestrates_session_and_reporting'
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_session_runner.py tests/unit/test_phase3_harness_session_runner.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `Phase3HarnessSessionRunner` no longer calls `workspace.current_request()`, `workspace.last_signing_result()`, or `workspace.capture_state(...)`;
- the runner uses `capture_snapshot(...)` for sign-time, manual, and final capture reads;
- `Phase3HarnessCaptureAssembler` still receives dict-shaped state via `snapshot.as_mapping()`;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py

Then run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_harness_session or run_phase3_signing_harness_orchestrates_session_and_reporting'
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_session_runner.py tests/unit/test_phase3_harness_session_runner.py
    git diff --check

Acceptance is behavioral. The returned `Phase3HarnessSessionResult` should still contain the same manual capture, final capture, and signed-run bundle data, but the runner should now obtain that state from one structured snapshot seam.

## Idempotence and Recovery

This is a narrow caller migration and is safe to retry. If a test fails, prefer fixing the fake workspace or the snapshot-to-dict adaptation inside the runner instead of reintroducing the legacy compatibility methods.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` consuming `capture_snapshot(...)`;
- `tests/unit/test_phase3_harness_session_runner.py` proving the runner no longer uses legacy workspace probes;
- focused test and lint output passing after the migration.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interaction inside `Phase3HarnessSessionRunner.run()` should become:

    snapshot = workspace.capture_snapshot(
        Phase3HarnessCaptureCommand(...)
    )

    captured_state = snapshot.as_mapping()

At the end of the slice, `Phase3HarnessSessionResult.captured_states` and `final_state` should remain dict-shaped for compatibility, while `capture_request` and `last_signing_result` should be sourced from the final snapshot object rather than separate workspace probe methods.
