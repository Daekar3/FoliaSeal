# Reconcile architecture documentation for the workspace snapshot boundary

This child ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is part of the parent
`docs/ExecPlans/signing_workspace_runtime_snapshot_hybrid_execplan.md` and must be completed before
the parent slice is committed.

## Purpose / Big Picture

The code and tests now use an immutable `SigningWorkspaceSnapshot` for live diagnostic and Phase 3
reads, but `docs/ARCHITECTURE.md` still describes the older piecemeal compatibility-read path. This
child plan updates the governing architecture map and README so a future contributor sees the same
production-port, transitional-compatibility, and snapshot ownership that the code implements.

## Child ExecPlan Dependencies

- [x] Parent runtime snapshot implementation and focused/full validation are complete.
- [x] (2026-07-30) Architecture-steward documentation pass and both compliance reviews rerun.

## Progress

- [x] (2026-07-30) Initial architecture compliance review: FAIL on stale Phase 3 compatibility-read wording; code and SPEC checks passed.
- [x] (2026-07-30) Updated `docs/ARCHITECTURE.md`, README, and the parent plan with snapshot and ownership boundaries.
- [x] (2026-07-30) Ran whitespace checks and focused validation after documentation changes.
- [x] (2026-07-30) Reran independent architecture/spec reviews: PASS; the stale wording finding is resolved.

## Surprises & Discoveries

- Observation: the mismatch is documentation-only; the snapshot implementation and Phase 3 schema
  are already correct.
  Evidence: the first review passed code/SPEC checks and failed only on architecture wording.

## Decision Log

- Decision: Update the existing Phase 3 and signing-workspace sections instead of adding a second
  competing architecture description.
  Rationale: one canonical description prevents future drift and keeps the change narrow.
  Date/Author: 2026-07-30 / Codex.

## Outcomes & Retrospective

Updated `README.md`, `docs/ARCHITECTURE.md`, and the parent ExecPlan to name
`SigningWorkspaceSnapshot`, `SigningWorkspaceDiagnosticsPort`, and `SigningWorkspaceTestingPort`,
to keep `SigningWorkspacePort` narrow, to mark `compat_surface` transitional, and to document Phase
3 snapshot consumption. The initial architecture review failed for stale compatibility-read wording;
the architecture/spec rerun passed after this documentation pass. Focused workspace/runtime/harness
tests and `git diff --check` passed.

2026-07-30 outcome: Updated `README.md`, `docs/ARCHITECTURE.md`, and the parent ExecPlan to name
`SigningWorkspaceSnapshot`, `SigningWorkspaceDiagnosticsPort`, and `SigningWorkspaceTestingPort`,
to keep `SigningWorkspacePort` narrow, to mark `compat_surface` as transitional, and to document
Phase 3 snapshot consumption. The initial architecture review was FAIL for stale compatibility-read
wording; after this pass the architecture/spec reviews are PASS. Focused workspace/runtime/harness
tests and `git diff --check` pass. The documentation child and parent slice are committed on
`main`; the final post-amend worktree, process, and window audit is clean.

## Context and Orientation

The relevant implementation files are `signing_workspace_diagnostics.py`,
`signing_workspace_runtime.py`, `signing_workspace_testing_port.py`,
`signing_workspace_compatibility_surface.py`, and `phase3_harness_workspace.py`. The production
`SigningWorkspacePort` remains small and app-frame-facing. The compatibility surface owns legacy
widget exports and constructs the explicit testing adapter. The adapter exposes a neutral immutable
snapshot; the Qt Phase 3 workspace consumes that snapshot for current request, appearance, and last
signing result reads while preserving `Phase3HarnessWorkspaceSnapshot` JSON keys.

## Plan of Work

Use the architecture-steward skill to update `docs/ARCHITECTURE.md` with the new diagnostics module,
snapshot ownership, testing-port relationship, and Phase 3 capture flow. Replace wording that says
the harness performs callable/attribute compatibility reads with wording that identifies the snapshot
as the primary live-state read and compatibility exports as transitional only. Update README with a
short description of the hybrid boundary if its architecture section omits the snapshot. Add the
implementation and review evidence to the parent ExecPlan and this child plan.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    git diff --check
    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py

Then rerun both explorer-light compliance reviews against `docs/ARCHITECTURE.md`, `docs/SPEC.md`,
and all changed files. Record their results here and in the parent plan.

## Validation and Acceptance

Acceptance requires architecture documentation to name `SigningWorkspaceSnapshot` and its neutral
diagnostic/testing boundary, describe the small production port as unchanged, describe
`compat_surface` as transitional, and describe Phase 3 as consuming the snapshot for live state.
Focused tests and `git diff --check` must pass, and both compliance reviews must report PASS.

## Idempotence and Recovery

Documentation edits are additive and safe to repeat. Do not change runtime code to make wording fit;
if a review finds a real behavioral mismatch, return to the parent plan and record a new decision.

## Artifacts and Notes

Only README, `docs/ARCHITECTURE.md`, the parent plan, and this child plan are documentation artifacts.
No generated PDFs, images, or matrix directories belong in this child commit.

## Interfaces and Dependencies

The child documents these existing interfaces without changing them: `SigningWorkspacePort`,
`SigningWorkspaceDiagnosticsPort`, `SigningWorkspaceTestingPort`, `SigningWorkspaceSnapshot`, and
`Phase3HarnessWorkspaceSnapshot`. The architecture-steward skill is required for the architecture
document update.

## Revision Note

2026-07-30 / Codex: Created after the first architecture compliance review found stale Phase 3
compatibility-read wording. The child is documentation-only and blocks the parent commit until the
governing docs and independent reviews agree with the implementation.
