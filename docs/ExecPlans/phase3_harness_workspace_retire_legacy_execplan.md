# Retire legacy Phase 3 workspace probe methods

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the public Phase 3 harness workspace boundary exposes only the scenario-application, viewer-refresh, and snapshot-returning capture behavior that the runtime actually uses. Users do not see a workflow change, but the Phase 3 harness no longer carries dead compatibility probe methods on its workspace port.

You can verify the change by running the focused workspace and harness tests and seeing that the runtime callers still pass while the direct workspace tests no longer depend on `current_request()`, `last_signing_result()`, or `capture_state()`.

## Child ExecPlan Dependencies

- [x] (2026-07-03 04:02Z) `docs/ExecPlans/phase3_harness_workspace_snapshot_execplan.md` established `Phase3HarnessWorkspaceSnapshot` and `capture_snapshot(...)`.
- [x] (2026-07-03 04:02Z) `docs/ExecPlans/phase3_signed_acceptance_snapshot_execplan.md`, `docs/ExecPlans/phase3_harness_session_runner_snapshot_execplan.md`, and `docs/ExecPlans/phase3_preview_matrix_snapshot_execplan.md` migrated all Phase 3 runtime callers to `capture_snapshot(...)`.
- [x] (2026-07-03 04:02Z) No child ExecPlans are required for this bounded port-retirement slice.

## Progress

- [x] (2026-07-03 03:59Z) Used an `explorer-light` subagent to confirm the runtime no longer depends on `current_request()`, `last_signing_result()`, or `capture_state()` on `Phase3HarnessWorkspacePort`.
- [x] (2026-07-03 04:08Z) Removed the legacy probe methods from `src/foliaseal/presentation/qt/phase3_harness_workspace.py`.
- [x] (2026-07-03 04:10Z) Updated direct workspace/harness tests to align with the snapshot-only port.
- [x] (2026-07-03 04:14Z) Reconciled `docs/ARCHITECTURE.md`, ran focused validation, and recorded the compliance result.

## Surprises & Discoveries

- Observation: the shell-level compatibility surface still exposes `current_request()` and `last_signing_result()`, but that is a separate boundary from the Phase 3 workspace port.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` and `src/foliaseal/presentation/qt/signing_shell.py` still expose those methods, while the Phase 3 runtime callers no longer use them through `Phase3HarnessWorkspacePort`.
- Observation: the only post-patch validation issue was a single line-length violation in the live adapter request assignment.
  Evidence: `ruff check` flagged one `E501` in `phase3_harness_workspace.py`; wrapping the conditional expression fixed it and the full focused validation set then passed.

## Decision Log

- Decision: retire the methods only from `Phase3HarnessWorkspacePort` and the Phase 3 workspace adapters, not from the broader signing-shell compatibility surface.
  Rationale: the signing-shell surface is a wider compatibility contract with its own tests and callers; pulling it into this slice would widen scope beyond the Phase 3 harness boundary cleanup.
  Date/Author: 2026-07-03 / Codex

## Outcomes & Retrospective

This slice should leave the runtime behavior unchanged while making the Phase 3 workspace contract smaller and more honest. Success means the port exposes only `refresh_viewer()`, `apply_scenario(...)`, and `capture_snapshot(...)`, and all focused harness tests continue to pass.

Completed on 2026-07-03. The Phase 3 workspace port now exposes only `refresh_viewer()`, `apply_scenario(...)`, and `capture_snapshot(...)`; the runtime callers remained green; and the focused compliance review found no architecture or spec drift beyond keeping this plan current.

## Context and Orientation

The main file is `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. It defines `Phase3HarnessWorkspacePort`, `QtPhase3HarnessWorkspaceAdapter`, `HeadlessPhase3HarnessWorkspaceAdapter`, and the shared `Phase3HarnessWorkspaceSnapshot`. Earlier slices migrated every runtime caller to `capture_snapshot(...)`, but the port still publicly exposes `current_request()`, `last_signing_result()`, and `capture_state(...)`.

The direct workspace tests live in `tests/unit/test_qt_phase3_harness_workspace.py`. Those tests still assert the removed methods explicitly, so they must be rewritten to validate snapshot content instead of probe methods.

Several other focused tests use fake workspaces that still define the removed methods only to assert they are not called. Those tests should be trimmed so their fake workspaces match the smaller real port.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Remove `current_request()`, `last_signing_result()`, and `capture_state()` from `Phase3HarnessWorkspacePort` and from both workspace adapter classes. Inline the request/result reads into `capture_snapshot(...)` using the existing `snapshot_current_draft_request(...)` helper for headless mode and the testing surface for live-shell mode.

Second, edit the focused tests. In `tests/unit/test_qt_phase3_harness_workspace.py`, remove direct assertions against the retired methods and keep coverage centered on `capture_snapshot(...)` plus the standalone `snapshot_current_draft_request(...)` helper. In `tests/unit/test_phase3_harness.py`, `tests/unit/test_phase3_harness_session_runner.py`, and `tests/unit/test_phase3_signed_acceptance_scenario_executor.py`, delete fake workspace methods that no longer belong to the port.

Third, update `docs/ARCHITECTURE.md` so the Phase 3 workspace boundary no longer advertises compatibility request/result reads or `capture_state()` as public entry points. Leave `docs/SPEC.md` unchanged.

Finally, run focused validation and the compliance review. Do not widen this slice into `signing_workspace_compatibility_surface.py` or `signing_shell.py`.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the workspace boundary, focused tests, architecture notes, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_phase3_harness.py
       apply_patch ... on tests/unit/test_phase3_harness_session_runner.py
       apply_patch ... on tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/phase3_harness_workspace_retire_legacy_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `Phase3HarnessWorkspacePort` no longer exposes `current_request()`, `last_signing_result()`, or `capture_state()`;
- both workspace adapters still return the same snapshot payload from `capture_snapshot(...)`;
- all focused tests pass without depending on the removed port methods;
- focused lint and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py
    git diff --check

Acceptance is behavioral. The runtime callers should continue to work through `capture_snapshot(...)`, and the Phase 3 workspace boundary should become smaller without changing user-visible harness output.

## Idempotence and Recovery

This is a narrow API-retirement slice and is safe to retry. If a test fails, prefer restoring the needed snapshot-derived assertion rather than reintroducing the removed workspace methods.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_harness_workspace.py` exposing only snapshot-based capture on the Phase 3 workspace port;
- focused tests passing without direct calls to the retired methods;
- architecture text no longer presenting the retired methods as part of the public Phase 3 workspace contract.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of the slice, `Phase3HarnessWorkspacePort` should look like:

    class Phase3HarnessWorkspacePort(Protocol):
        def refresh_viewer(self) -> None: ...
        def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...
        def capture_snapshot(
            self, command: Phase3HarnessCaptureCommand
        ) -> Phase3HarnessWorkspaceSnapshot: ...

The separate signing-shell compatibility surface is explicitly out of scope.
