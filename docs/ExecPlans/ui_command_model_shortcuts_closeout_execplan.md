# Close the completed desktop command model

This ExecPlan is a living document maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK documentation/status slice under
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

The desktop command model is already implemented, but its child plan and one architecture debt
row still describe commands as deferred. That mismatch makes the project look less complete than it
is and can cause a later agent to duplicate existing behavior. This slice will reconcile the
command-model plan, parent plan, and architecture record with the live typed registry and its tests.
The observable result is a truthful repository map: a reviewer can inspect the command registry and
run the focused command tests without finding contradictory “unsupported” claims. This is a
documentation/status change only; no new command behavior belongs in this slice.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing contracts.
- [x] `docs/ExecPlans/ui_command_model_shortcuts_execplan.md` contains the implemented command
  families and current validation evidence.
- [x] Explorer audit of the live command registry, AppFrame wiring, public session port, runtime,
  tests, and architecture debt was completed before this plan was written.

## Progress

- [x] (2026-08-16) Confirmed that File, Edit, View, Signing, Settings, and Help command families
  are present in the typed registry and routed through live frame/runtime seams.
- [x] (2026-08-16) Rewrite stale purpose, outcomes, deferred-command, and acceptance wording in the child plan.
- [x] (2026-08-16) Reconcile the parent child marker and architecture debt/history rows without claiming that
  display-backed GUI or release acceptance is complete.
- [x] (2026-08-16) Run focused/full validation, clean generated artifacts, and confirm the worktree
  is ready for the documentation/compliance commit. Focused command/AppFrame/session/launch coverage
  passed `81`; the full suite passed `1535 passed, 20 skipped, 1 warning`; Ruff, compileall, and
  `git diff --check` passed.
- [x] (2026-08-16) Committed the four-file documentation/status closeout as `4a0fd494d`; the
  worktree is clean and no FoliaSeal, PySide6, or pytest process remains.

## Surprises & Discoveries

- Observation: the child plan's historical deferred-command text is contradicted by current source.
  Evidence: `app_frame_command_model.py` defines all required UI_SPEC menu families, while AppFrame
  and the public workspace session port route those actions and project their state.
- Observation: command-model closeout does not close release acceptance. Evidence: the parent still
  records display-backed GUI, accessibility, package, and nomenclature gates separately.

## Decision Log

- Decision: perform a status/documentation closeout rather than add another command increment.
  Rationale: adding behavior would duplicate complete live seams and increase regression risk.
  Date/Author: 2026-08-16 / Codex.
- Decision: retain historical progress entries, but label them as historical and make the current
  outcome authoritative. Rationale: ExecPlans are an audit trail as well as an execution guide.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The command-model child is now marked complete with current focused/full evidence. The parent marks
that child complete while retaining independent release and display-backed gates. No source behavior,
generated artifact, or compatibility surface changed.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame_command_model.py` owns typed command identifiers,
definitions, menu ordering, shortcuts, and descriptions. `src/foliaseal/presentation/qt/app_frame.py`
turns those definitions into Qt actions and applies capability state. The public workspace/session
ports and `signing_workspace_runtime.py` own behavior such as navigation, placement history, native
editor actions, document selection, Pan, and signing readiness. Focused unit and offscreen Qt tests
prove those routes. The parent plan is the authoritative dependency map; its final release gates
remain open after this closeout.

## Plan of Work

First, update the command-model child’s purpose, outcomes, validation, and current progress so they
describe the complete File/Edit/View/Signing/Settings/Help registry. Preserve historical entries,
but explicitly mark superseded decisions as historical rather than current requirements.

Next, update the parent command-model marker and the architecture debt/history rows. Record the
current focused/full validation and the known environment limits (`SingleInstanceUnavailable` and
display-backed acceptance) without converting those limits into behavioral claims.

Finally, run the focused command/AppFrame tests, the full suite, Ruff, compile checks, and diff
validation. Remove only temporary outputs created by validation, then commit the documentation/status
change.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    rg -n "deferred|unsupported|remaining command|not complete" docs/ExecPlans/ui_command_model_shortcuts_execplan.md docs/ARCHITECTURE.md
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_app_frame_workspace_action_state.py tests/integration/test_gui_launch_no_document.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check

Expected validation is green; the full suite count must be recorded from the actual run rather than
copied from an older plan entry.

## Validation and Acceptance

Acceptance is that every command required by UI_SPEC §7 appears in the typed registry, has a live
route or truthful capability boundary, and is described as implemented in the child and parent
plans. Focused tests must pass, the full regression must pass, and no source or test process may
remain. Display-backed GUI and privileged package acceptance remain explicitly outside this status
closeout.

## Idempotence and Recovery

The edits are documentation-only and safe to repeat. If a validation command generates temporary
fixtures, keep them outside the repository or remove them before commit. If a wording change is
found to overclaim display-backed acceptance, restore the environment qualifier and rerun diff and
plan-link checks.

## Artifacts and Notes

Record the focused command test count, full-suite count, and final commit hash (`4a0fd494d`) in the
child plan, parent plan, and architecture history. Do not commit ignored QA PDFs, certificates,
screenshots, or temporary package roots.

## Interfaces and Dependencies

This slice must not change Python interfaces. Its evidence depends on the existing typed command
registry, `FoliaSealAppFrame`, `SigningWorkspaceSessionPort`, `SigningWorkspaceRuntime`, and their
focused/offscreen tests. The next behavioral slice must be selected from another still-open child
after this status reconciliation.

Revision note: 2026-08-16 / Codex
The explorer audit found no missing command behavior, so this plan was used to close stale status
claims instead of duplicating the registry. Current validation is recorded above; display-backed and
release acceptance remain parent-owned gates.
