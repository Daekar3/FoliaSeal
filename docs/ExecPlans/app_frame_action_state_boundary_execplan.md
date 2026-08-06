# Centralize App-Frame Workspace Action State

This ExecPlan is a living document and must be maintained according to
`.agents/skills/write-execplan/PLANS.md`. It is one bounded implementation slice from the parent
architecture loop. The purpose is to make the app frame's menu state a small, testable policy
boundary without changing the workspace lifecycle or the user's signing workflow.

## Purpose / Big Picture

After this change, opening a PDF, closing it, and toggling text-selection mode will still produce
the same GUI behavior, but one Qt-free immutable value will describe the complete workspace action
state. `FoliaSealAppFrame` will apply that value at the QAction edge instead of repeating four
independent setter sequences. A human can verify this by opening a PDF in the existing GUI or by
running the app-frame tests: Save As, text selection, and Copy selected text become enabled only for
an active workspace; closing restores the disabled placeholder state; a failed replacement leaves
the old workspace and its actions unchanged.

## Child ExecPlan Dependencies

- [x] `docs/ARCHITECTURE.md` and `docs/SPEC.md` are available and were checked during Scan Round 32.
- [x] `SigningWorkspaceHost` and `SigningWorkspaceLifecycle` already provide atomic open/replace/
  close behavior; this plan must not duplicate that lifecycle.
- [x] Design Selection 33 in the parent selected the constrained immutable projection shape.
- [x] (2026-08-06) Implemented the projection, app-frame application method, and boundary tests;
  focused tests pass (`30`).
- [x] (2026-08-06) Full suite passes (`1,121 passed, 1 warning`); Ruff, compileall, CLI help, and
  diff checks pass.
- [x] (2026-08-06) Reconciled architecture documentation and explicitly kept phase3 migration out
  of scope; compliance review and commit closure remain.
- [x] (2026-08-06) Offscreen evidence reports signed acceptance `10/7`, preview parity `18/18`, and
  fit rejection `3/3`; generated summary removed, SPEC diff empty, and no product processes remain.
- [ ] Commit closure and fresh post-commit explorer rescan.

## Progress

- [x] (2026-08-06) Confirmed the current seam: `open_pdf_path()` sets four QAction properties after
  host success, while `_set_placeholder()` repeats the inverse sequence.
- [x] (2026-08-06) Confirmed failure semantics: host open failures emit one error and leave the
  previously published workspace and action state unchanged; close is idempotent.
- [x] (2026-08-06) Added the Qt-free immutable state module and pure constructors/transitions.
- [x] (2026-08-06) Replaced duplicated app-frame action-state sequences with one projection
  application method; QAction mutation remains at the frame edge.
- [x] (2026-08-06) Added boundary and integration tests, including failed replacement and toggle
  result behavior.
- [x] (2026-08-06) Reconciled architecture documentation and this plan; phase3 symbols and paths
  were not renamed.
- [x] (2026-08-06) Focused validation passed (28 tests); full validation passed (1,119 tests).
  `ruff check`, `python -m compileall -q src`, and `git diff --check` also passed.
- [ ] Run offscreen acceptance evidence, cleanup, process audit, and SPEC diff check.
- [ ] Commit the complete slice and run a fresh three-explorer post-commit scan.

## Surprises & Discoveries

- Observation: `SigningWorkspaceHost` already owns candidate composition, mount, publication, and
  disposal, including atomic replacement and idempotent close.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_lifecycle.py` publishes only after
  candidate mount succeeds and disposes the previous handle afterward.
- Observation: the shell's `SigningActionState` is unrelated signing-panel policy.
  Evidence: no `WorkspaceActionState` exists; the new name must remain app-frame-specific.
- Observation: `choose_open_pdf()` returns the selected path even when `open_pdf_path()` fails.
  Evidence: `tests/unit/test_qt_app_frame.py` covers the selection path; this plan does not alter it.
- Observation: a candidate mount failure preserves the previous projection, while a placeholder
  mount failure after host close leaves the previous action projection in place because the closed
  projection is applied only after a successful mount.
  Evidence: app-frame tests cover both exceptions and assert the prior immutable identity remains;
  lifecycle tests independently prove candidate disposal and previous-workspace preservation.
  This preserves the pre-existing ordering and is recorded for a future explicit error-state slice.

## Decision Log

- Decision: Use a frozen stdlib-only `WorkspaceActionState` record with five booleans: workspace
  open, Save As enabled, text-selection enabled, text-selection checked, and copy enabled.
  Rationale: it compresses the repeated policy while keeping Qt QAction mutation and lifecycle at
  the presentation edge; no heavy dependency can leak into the boundary.
  Date/Author: 2026-08-06 / Codex.
- Decision: Keep `SigningWorkspaceHost`, `SigningWorkspacePort`, maintenance routing, placeholder
  mounting, and error reporting unchanged.
  Rationale: a new coordinator would create a second lifecycle owner and increase failure risk.
  Date/Author: 2026-08-06 / Codex and independent design reviewers.
- Decision: Do not include the phase3 nomenclature migration in this slice.
  Rationale: the separate inventory spans CLI names, DTOs, serialized keys, fixtures, artifacts,
  and historical references and must be versioned atomically.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

Implementation outcome (2026-08-06): the app frame now consumes the frozen, Qt-free
`WorkspaceActionState` projection and applies its four QAction fields in one method. The
`SigningWorkspaceHost` lifecycle and maintenance-port routing remain unchanged, and the separate
phase3 nomenclature migration remains out of scope. Focused tests passed 30/30 and the full suite
passed 1,121/1,121; `ruff check`, `python -m compileall -q src`, and `git diff --check` passed.
Architecture documentation was reconciled to record projection policy versus QAction mutation
ownership and the unchanged host lifecycle. Offscreen acceptance evidence passed signed acceptance
`10/7`, preview parity `18/18`, and fit rejection `3/3`; the generated summary was removed, the
SPEC diff is empty, and the process audit found no FoliaSeal/Python/Qt process. Intentional commit
closure and the fresh post-commit explorer rescan remain.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` composes the top-level Qt window. Its
`open_pdf_path()` calls `SigningWorkspaceHost.open()` and then enables Save As, text selection, and
copy actions. `close_workspace()` calls host close and `_set_placeholder()`, which mounts the
"Open a PDF to begin signing." label and disables those actions. `_toggle_text_selection_mode_from_action()`
and `_copy_selected_text_from_action()` route through the active workspace's maintenance port.

The new module belongs at
`src/foliaseal/presentation/qt/app_frame_workspace_action_state.py`, but it must import only
`dataclasses` and ordinary typing primitives. It is a projection, meaning a pure value that records
what the frame should display; it must not know about Qt, the host, widgets, files, or signing
workflows.

## Plan of Work

First add the projection module. Define:

    @dataclass(frozen=True)
    class WorkspaceActionState:
        workspace_open: bool
        save_as_enabled: bool
        text_selection_enabled: bool
        text_selection_checked: bool
        copy_selected_text_enabled: bool

Also define `workspace_action_state_closed() -> WorkspaceActionState`,
`workspace_action_state_open() -> WorkspaceActionState`, and
`workspace_action_state_with_selection_result(state: WorkspaceActionState, checked: bool) ->
WorkspaceActionState`. Constructors must return new immutable values and must not mutate their input.
The open value has `workspace_open=True`, Save As/text/copy enabled, and selection unchecked. The
closed value has all five fields false. The selection-result function changes only the checked flag
and preserves the other four fields; callers must use it only for an active workspace.

Next update `FoliaSealAppFrame` to hold the current projection, initialized to the closed value.
Add one private `_apply_workspace_action_state(state)` method that stores the value and applies its
four action fields to the existing QAction objects. Replace the four setter calls after successful
`_workspace_host.open()` with the open projection. Replace the reset calls in `_set_placeholder()`
with the closed projection, after the label mount succeeds. In the toggle callback, replace only the
checked field using the pure transition when the maintenance port returns a bool. Keep the existing
individual setters only if a focused search proves an external test or internal caller still needs
one; otherwise retire them and record their removal here. Do not change host calls, exception text,
return values, action routing, or compatibility properties.

Add unit tests for the projection's exact open/closed values, frozen immutability, and selection
transition. Extend app-frame tests to assert the projection after construction, successful open,
failed replacement, toggle, and repeated close. Preserve existing action-routing assertions and
add an assertion that a failed replacement does not change the action values. Add an import-firewall
test that importing the projection does not load PySide6, Pillow, PyHanko, or filesystem adapters.

Update `docs/ARCHITECTURE.md` to state that the app frame owns Qt mutation while the Qt-free
`WorkspaceActionState` projection owns the action-state policy, and that the workspace host remains
the sole lifecycle owner. Update this plan and the parent ledger with actual measurements and the
decision not to touch phase3 nomenclature.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

1. Implement the module and app-frame migration with `apply_patch`; run the new focused tests first.
2. Run `python -m pytest -q tests/unit/test_app_frame_workspace_action_state.py tests/unit/test_qt_app_frame.py`.
3. Run `python -m pytest -q`, `ruff check src tests`, `python -m compileall -q src`, and CLI help
   commands from `pyproject.toml`; expect the full suite to remain green with no new warnings.
4. Run the existing offscreen signed-acceptance, preview-parity, and fit-rejection evidence
   commands used by the parent loop. Record their exact PASS counts and remove their explicit
   temporary roots afterward.
5. Run `git diff --check`, verify `git diff -- docs/SPEC.md` is empty, audit
   `pgrep -af 'FoliaSeal|foliaseal|python|PySide|qt'`, and remove only the named temporary roots.
6. Ask a worker-light agent to reconcile `docs/ARCHITECTURE.md`, then ask a worker-light agent to
   use `$write-git-commit` for the intentional source/test/docs/plan files. Confirm `git status`
   is clean and record the commit hash.
7. Spawn three fresh explorer-light agents for the post-commit scan and either select the next
   qualifying seam or record two below-threshold confirmations.

## Validation and Acceptance

The slice is accepted only when all projection and app-frame tests pass, the full suite and static
checks pass, offscreen evidence preserves signed acceptance `10` scenarios (`7` successful and `3`
intentional rejections), preview parity `18/18`, and fit rejection `3/3`, with no crypto,
annotation, or mismatch failures. Failed replacement must preserve the old shell, action values,
and single warning; close twice must dispose once and leave all actions disabled. The projection
module must be importable without Qt/Pillow/PyHanko/filesystem imports. No critical/major review
finding may remain, Actual Improvement must be at least `.15`, no component may regress below `-.10`,
and the worktree must be clean with no FoliaSeal/Python/Qt processes or temporary evidence roots.

## Idempotence and Recovery

The projection constructors and tests are safe to run repeatedly. If an integration test fails,
keep the failing test and update `Surprises & Discoveries`; compare the old four setter sequence with
the projection fields before changing behavior. Never catch new exceptions or alter host lifecycle
to make the tests pass. If documentation or commit work fails, leave source validation evidence in
this plan and retry that milestone; do not delete unrelated files.

## Artifacts and Notes

Allowed changes are the new projection module, `app_frame.py`, focused tests, architecture/docs,
and this parent/child ledger. Generated evidence may live only under explicit `/tmp` roots named in
the validation transcript and must be removed before commit. The separate
`phase3_nomenclature_retirement_execplan.md` remains the only allowed home for phase3 rename work.

## Interfaces and Dependencies

The projection has no runtime dependency beyond Python's standard library. `FoliaSealAppFrame` is
the sole consumer and remains responsible for QAction calls (`setEnabled`, `setChecked`).
`SigningWorkspaceHost` remains the sole owner of lifecycle publication/disposal. The maintenance
`SigningWorkspacePort` remains the sole route for text-selection and copy operations. No new public
CLI, persisted key, Qt signal, or compatibility alias may be introduced.

## Revision Note

Created 2026-08-06 after Scan Round 32 and Design Selection 33. This plan deliberately separates
the bounded action-state projection from the larger atomic phase3 nomenclature migration.
