# Re-anchor Phase 3 signed-acceptance scenario execution on the workspace boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the signed-acceptance matrix will still produce the same per-scenario preview snapshot, preview text, validation text, signing-request snapshot, backend-reservation snapshot, signing result, and signed-output evidence as before. The visible harness outputs do not change.

The architectural gain is narrower ownership: `phase3_signed_acceptance_scenario_executor.py` will stop reaching through `compat_surface` and `properties_panel._workflow` to rebuild preview and request state. Instead, it will ask the existing `phase3_harness_workspace.py` boundary for the current request and raw capture-state bundle, just like the preview-matrix and session-runner paths already do.

## Child ExecPlan Dependencies

- [x] (2026-06-11 12:24Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the preview-scenario mutation boundary exists and is required before this slice.
- [x] (2026-06-11 12:24Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the workspace boundary already owns current-request and raw capture-state reads used by this slice.
- [x] (2026-06-11 12:24Z) No child ExecPlan is required for this third tracer bullet on the same hybrid seam.

## Progress

- [x] (2026-06-11 12:18Z) Re-read the current workspace boundary, signed-acceptance scenario executor, signed-acceptance runner wiring, and focused tests.
- [x] (2026-06-11 12:22Z) Ran the required `explorer-light` dev-loop pass and fixed the next slice boundary: signed-acceptance scenario execution should consume workspace-derived request/capture state instead of `compat_surface` and `_workflow`.
- [x] (2026-06-11 12:24Z) Wrote this ExecPlan and fixed the implementation target at the smallest signed-acceptance leak closure on the same workspace-boundary hybrid.
- [x] (2026-06-11 12:31Z) Updated the signed-acceptance scenario executor to consume a workspace boundary instead of direct shell anatomy reads, and rewired `phase3_harness.py` to reuse the existing live workspace builder.
- [x] (2026-06-11 12:33Z) Reworked the focused executor tests so signed-acceptance scenario state is proved through a fake workspace boundary instead of a fake properties panel.
- [x] (2026-06-11 12:36Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-11 12:44Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the implemented ownership split.
- [x] (2026-06-11 12:45Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; the review found no issues and no corrective follow-on was required.
- [ ] Create the git commit for the finished slice.

## Surprises & Discoveries

- Observation: after the preview-matrix and session-runner slices, the main remaining live-shell leak on this hybrid is the signed-acceptance scenario executor.
  Evidence: `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` still calls `compat.properties_panel.refresh_preview()`, `preview_text()`, `validation_text()`, and `snapshot_current_draft_request(compat.properties_panel._workflow)` directly.

- Observation: the workspace boundary already owns every read the executor needs except the final sign submission.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_workspace.py` already exposes `current_request()` and `capture_state(...)`, both of which shape the same preview/request/backend evidence that the executor currently rebuilds inline.

- Observation: the signed-acceptance executor did not need any new workspace port verb after all.
  Evidence: reusing `current_request()` plus `capture_state(...)` was sufficient once the executor switched from direct shell reads to a workspace-builder dependency.

## Decision Log

- Decision: keep this slice centered on the signed-acceptance scenario executor only.
  Rationale: that is the smallest remaining leak on the same hybrid seam. Pulling in runner changes, reporting, or signed-output snapshotting would broaden the slice unnecessarily.
  Date/Author: 2026-06-11 / Codex

- Decision: keep signing submission and successful-output snapshotting inside `Phase3SignedAcceptanceScenarioExecutor`.
  Rationale: the workspace boundary should own reads from the live shell, not the act of executing a sign request or shaping signed-output evidence. Those responsibilities already belong to the executor and its collaborators.
  Date/Author: 2026-06-11 / Codex

- Decision: prefer wiring the executor to a workspace-builder callable over widening `Phase3HarnessWorkspacePort` unless a missing behavior is discovered during implementation.
  Rationale: the current port already exposes the needed state. Reusing it keeps the new slice small and avoids inventing another harness-specific helper interface.
  Date/Author: 2026-06-11 / Codex

## Outcomes & Retrospective

Implementation, focused validation, documentation reconciliation, and compliance review are complete. The slice re-anchored `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` on the existing `phase3_harness_workspace.py` boundary so signed-acceptance scenario execution now consumes workspace-derived preview/request/backend state instead of reading `compat_surface` and `properties_panel._workflow` directly.

The resulting design still keeps signing submission and successful-output snapshotting inside the signed-acceptance executor, keeps `phase3_harness.py` as the composition root, and does not mix in session-runner, reporting, or compatibility-surface cleanup work. No corrective iteration was needed after the compliance pass.

## Context and Orientation

The Phase 3 harness is the repository’s signing-evidence runner. For signed-acceptance scenarios, it opens a live signing shell, applies a preview scenario, captures preview evidence, executes a real sign attempt, and then snapshots the signed output. The relevant files are `src/foliaseal/presentation/qt/phase3_harness.py`, which is the composition root for the harness helpers; `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, which now owns scenario mutation plus request/result/capture reads; and `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`, which owns one signed-acceptance scenario row from preview capture through optional signed-output capture.

The current design is uneven. The preview-matrix path and interactive session runner already ask the workspace boundary for scenario state, but the signed-acceptance scenario executor still reaches through shell-private anatomy. In this repository, “shell-private anatomy” means details like `compat_surface`, `properties_panel`, and `properties_panel._workflow` that are implementation details of the live Qt signing shell. Those reads are not supposed to be spread across multiple harness modules.

The workspace boundary already exposes two stable behaviors the executor needs. `current_request()` returns the live `SigningRequest` represented by the current workflow state, and `capture_state(...)` returns the preview snapshot, preview text, validation text, signing-request snapshot, and backend-reservation snapshot/error bundle for the current live state. This slice will reuse those behaviors rather than rebuilding them in the executor.

The tests that currently prove this seam live in `tests/unit/test_phase3_signed_acceptance_scenario_executor.py`, `tests/unit/test_qt_phase3_harness_workspace.py`, and `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`. The executor tests still use a fake shell with a fake properties panel, which is exactly the coupling this slice should remove.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`. Replace the direct `compat_surface`, request-snapshot, backend-reservation, and preview-refresh dependencies with one narrow workspace-builder dependency that returns a `Phase3HarnessWorkspacePort` for the live shell. After `apply_preview_matrix_scenario(...)` runs, the executor should build the workspace, read `request = workspace.current_request()`, and call `workspace.capture_state(...)` with a `Phase3HarnessCaptureCommand` using the scenario artifact basename. It should then assemble the result dictionary from that capture payload. The executor should still rewrite the request for matrix-specific input/output/certificate paths, call `sign_executor.execute(...)`, and, on success, delegate to `snapshot_successful_signed_output(...)`.

Second, update `src/foliaseal/presentation/qt/phase3_harness.py` so `_build_phase3_signed_acceptance_scenario_executor()` injects the existing Qt workspace builder rather than the older direct preview/request helpers. The simplest path is to reuse the same workspace-construction logic already used by the live preview-matrix path, so the signed-acceptance executor and preview-matrix executor share one live-shell read boundary.

Third, update `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` to use a fake workspace boundary instead of a fake properties panel. The tests should prove that the executor consumes `current_request()` and `capture_state(...)`, preserves preview-only behavior when the request is missing, and still rewrites the request plus merges signed-output snapshots on successful sign execution. If the workspace boundary needs one more focused test to lock the scenario-state shape the executor depends on, add that in `tests/unit/test_qt_phase3_harness_workspace.py`. Only touch `tests/unit/test_phase3_signed_acceptance_matrix_runner.py` if the wiring contract changes.

Fourth, run focused validation, then update `docs/ARCHITECTURE.md` and this ExecPlan so the repository accurately documents the deeper workspace-boundary ownership. After that, run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. If a mismatch appears, fix only the mismatch inside this slice, rerun validation, and then create one narrow commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-anchor signed-acceptance scenario state reads on the workspace boundary.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py only if a tiny shared helper or type is needed

2. Update focused tests for the new executor boundary.

       apply_patch ... on tests/unit/test_phase3_signed_acceptance_scenario_executor.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py if an extra boundary test is needed
       apply_patch ... on tests/unit/test_phase3_signed_acceptance_matrix_runner.py only if executor wiring changes leak into the runner contract

3. Run focused validation for the new executor boundary and affected harness code.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun the focused validation commands if any code or tests changed during reconciliation.

5. Run the architectural compliance review, address any findings inside this slice only, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the signed-acceptance scenario executor no longer reads `compat_surface`, `properties_panel`, or `properties_panel._workflow` directly to assemble preview/request/backend state;
- the signed-acceptance scenario result still includes the same preview snapshot, preview text, validation text, signing-request snapshot, backend-reservation snapshot, signing result, and optional signed-output evidence as before;
- the workspace boundary, not a fake properties panel, proves the executor’s preview-only and successful-sign paths in focused tests;
- signing submission and successful-output snapshotting remain in `Phase3SignedAcceptanceScenarioExecutor`, not in the workspace boundary;
- no interactive-session-runner refactor, no reporting refactor, and no broad compatibility-surface cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The signed-acceptance matrix must still report the same per-scenario evidence for the same inputs after the refactor.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local harness code. It is safe to retry. If the executor fails after moving to the workspace boundary, keep the boundary wiring in place and add the missing read behavior to the workspace-side implementation rather than pushing preview/request assembly back into the executor.

If tests fail because the executor still depends on one more preview-state detail, prefer pulling that detail from `capture_state(...)` or a tiny shared helper instead of widening the public port arbitrarily. If a compliance review suggests pushing sign submission into the workspace boundary, record that as a follow-up and keep this slice limited to state-read ownership only.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a smaller `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` that no longer reads shell anatomy directly for preview/request/backend state;
- updated harness wiring in `src/foliaseal/presentation/qt/phase3_harness.py` that reuses the existing live workspace builder;
- focused executor tests that use a fake workspace port instead of a fake properties panel;
- focused validation output showing the executor tests, workspace tests, matrix-runner tests, and affected harness tests still pass.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the signed-acceptance executor should depend on a workspace-builder shape close to:

    BuildHarnessWorkspace = Callable[[Any, Any], Phase3HarnessWorkspacePort]

and should use the existing workspace boundary roughly as:

    workspace = build_workspace(shell=shell, profile_store=profile_store)
    request = workspace.current_request()
    capture = workspace.capture_state(
        Phase3HarnessCaptureCommand(
            request=request,
            artifacts_dir=str(artifacts_dir),
            artifact_basename=artifact_basename,
            capture_index=1,
            capture_kind="signed_acceptance_preview",
        )
    )

The executor must keep the current result-row shape. `snapshot_signing_result_payload(...)` and `snapshot_successful_signed_output(...)` remain executor dependencies. This slice must not add sign-submit methods, matrix-loop methods, or report-finalization methods to `Phase3HarnessWorkspacePort`.

Revision note: Created on 2026-06-11 by Codex for the third `dev-loop` implementation slice on the selected Phase 3 harness workspace-boundary hybrid.
Revision note: Updated on 2026-06-11 after implementation and focused validation to record the signed-acceptance executor re-anchor, the moved tests, and the clean compliance review.
