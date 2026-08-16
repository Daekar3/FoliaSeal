# Remove the refinement-dialog test backdoor

This ExecPlan is a living document maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` and is a behavior-preserving
architecture cleanup for the already-implemented refinement dialog.

## Purpose / Big Picture

The signing properties panel currently stores the open refinement dialog in a private
`_active_refinement_dialog` attribute only so tests can reach into its controls while a fake modal
dialog is executing. That is a test backdoor, not a product behavior: the panel already receives the
dialog's typed result when the modal interaction ends. After this slice, production code will no
longer retain or expose that private dialog state, while the five existing tests will observe the
same Apply, Cancel, and save-for-reuse behavior through an explicit test-only dialog subclass and
callback. A user can still open the refinement dialog, change appearance or placement, save reusable
objects without applying them, and cancel without mutating the live draft.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/ARCHITECTURE.md` define the contextual refinement
  dialog and typed public presentation boundaries.
- [x] `docs/ExecPlans/signature_properties_surface_hybrid_execplan.md` extracted the dialog into
  `signing_workspace_refinement_dialog.py` and records the remaining test-only state bridge.
- [x] `docs/ExecPlans/ui_appearance_editor_transaction_execplan.md` and
  `docs/ExecPlans/ui_placement_editor_transaction_execplan.md` define transactional save/cancel
  behavior that must remain unchanged.
- [x] The current implementation and tests were audited on 2026-08-16; five tests still inspect
  `SignaturePropertiesPanel._active_refinement_dialog` directly.

## Progress

- [x] (2026-08-16) Audited the private dialog-state bridge and confirmed it has no production caller;
  the only consumers are five refinement tests in `tests/unit/test_qt_signing_shell.py`.
- [x] (2026-08-16) Removed `_active_refinement_dialog` and
  `_set_active_refinement_dialog()` from
  `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` without changing the modal
  result/application path.
- [x] (2026-08-16) Migrated the five tests to an explicit test-local
  `SignatureRefinementDialog` subclass that captures `RefinementDialogState` through the existing
  callback contract.
- [x] (2026-08-16) Proved Apply, Cancel, appearance save, placement save, and preset composition
  remain transactional. Focused validation is `5 passed, 105 deselected`.
- [x] (2026-08-16) Reconciled architecture/parent/safe-links plan status and retained no dead
  refinement compatibility surface. The broader safe-links/UI parent release gates remain open.
- [x] (2026-08-16) Committed the cleanup as `12b1803cc`; the worktree and process scan were clean.

## Surprises & Discoveries

- Observation: the panel's `_active_refinement_dialog` assignment is only used by five tests;
  production callers consume `RefinementDialogResult` after `SignatureRefinementDialog.open()`.
  Evidence: `rg -n '_active_refinement_dialog' src tests` finds one panel field/setter and five test
  reads, with no other source caller.
- Observation: the dialog already exposes an `active_state_changed` callback for deterministic
  observation, so no new production state cache or widget lookup is needed.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py` emits a typed
  `RefinementDialogState` at modal start and `None` in `finally`.

## Decision Log

- Decision: remove the panel-owned cache rather than replace it with a public property or another
  hidden widget reference.
  Rationale: the cache has no user-facing meaning and makes tests depend on private panel internals;
  an explicit test-local dialog subclass can inject the already-existing observer without widening
  the production panel contract.
  Date/Author: 2026-08-16 / Codex.
- Decision: keep `RefinementDialogState` and its observer callback at the focused dialog boundary for
  tests, but do not pass the callback from the production panel.
  Rationale: the callback is a typed, narrow observation seam and removing it would force brittle
  fake-widget traversal; the unwanted compatibility surface is the panel's retained private state.
  Date/Author: 2026-08-16 / Codex.
- Decision: do not remove AppFrame dialog compatibility properties or certificate outcome
  compatibility fields in this slice.
  Rationale: current tests still consume them directly, and removing them without a separate
  migration would reduce observability rather than retire dead code.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

The panel no longer retains a private dialog bridge. The five affected tests use a test-local
`SignatureRefinementDialog` subclass to inject the dialog's existing typed
`active_state_changed` observer; production composition does not pass that observer. Apply, Cancel,
appearance save, placement save, and preset composition remain covered by the focused refinement
tests (`5 passed, 105 deselected`).

The cleanup grep is empty:

    rg -n '_active_refinement_dialog|_set_active_refinement_dialog' src tests/unit/test_qt_signing_shell.py
    (no matches)

The remaining dialog compatibility surfaces are intentional and outside this slice: AppFrame
dialog-exposure properties are retained for current tests/old callers, and certificate dialog
outcomes retain their compatibility fields for the certificate-management owner to migrate. No
broader safe-links or UI release completion is claimed.

The implementation commit is `12b1803cc` (`Clean up refinement dialog test boundaries`).

## Context and Orientation

`SignaturePropertiesPanel.open_refinement_dialog()` in
`src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` creates a
`SignatureRefinementDialog`, waits for its modal `RefinementDialogResult`, applies an accepted draft
through `SigningSetupSession`, and notifies the shell. The dialog itself is implemented in
`src/foliaseal/presentation/qt/signing_workspace_refinement_dialog.py`; its immutable
`RefinementDialogState` contains the controls needed by tests to simulate user actions. A test
backdoor means a private production attribute retained solely so tests can bypass the normal
observable boundary. Here that attribute is `_active_refinement_dialog`.

The affected tests live in `tests/unit/test_qt_signing_shell.py` and use fake Qt bindings. They set
`_FakeDialog.next_on_exec` to mutate controls while `exec()` is running. The migration must capture
the typed dialog state through an explicit test-local subclass/factory and must not inspect private
panel fields.

## Plan of Work

First, delete the `_active_refinement_dialog` initialization and the `_set_active_refinement_dialog`
method from `SignaturePropertiesPanel`. In `open_refinement_dialog()`, stop passing
`active_state_changed`; keep the existing dialog construction, result handling, state application,
and error routing unchanged.

Next, update the five refinement tests in `tests/unit/test_qt_signing_shell.py`. Import the
properties-panel module so each test can temporarily replace `SignatureRefinementDialog` with a
small subclass of the real class. The subclass injects a closure that stores the current
`RefinementDialogState` in a local holder, then delegates to the real implementation. Each fake
dialog callback (`_accept_with_changes`, `_cancel`, `_save_then_cancel`) reads that holder rather
than `widget.properties_panel._active_refinement_dialog`; it must assert the holder is populated
while the modal callback runs and becomes `None` after the modal returns where that lifecycle is
relevant. Keep all existing assertions about saved catalog contents, live-draft preservation, and
button behavior.

Finally, update `docs/ARCHITECTURE.md`, the safe-links parent plan, and this plan. State that the
dialog observer is test-local and the panel no longer retains a private dialog bridge. Do not delete
AppFrame or certificate compatibility properties whose tests still consume them; record the grep
inventory and defer those migrations to their owning plans.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n '_active_refinement_dialog|_set_active_refinement_dialog' src tests
    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k refinement_dialog
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    .venv/bin/pytest -q
    git diff --check

Before the edit, the focused command should pass while showing direct private-field reads. After the
edit, the same command should pass with no `_active_refinement_dialog` match under `src/` or the
refinement tests. The complete suite should remain green; record its exact count in `Progress` and
`Outcomes & Retrospective` rather than copying an older count.

## Validation and Acceptance

Acceptance is behavioral and architectural. The focused refinement tests must prove that Apply
changes the live setup, Cancel leaves the current setup unchanged, saving an appearance or
placement profile leaves the dialog open until Cancel and does not apply the draft, and composing a
preset from selected profiles still persists the expected references. The production panel must no
longer expose `_active_refinement_dialog` or a setter, and no test in this slice may read private
panel dialog state. Ruff, compileall, the full pytest suite, and `git diff --check` must pass. No
FoliaSeal/PySide6/pytest process or temporary audit root may remain.

## Idempotence and Recovery

The cleanup is safe to repeat because it removes only an unused state cache and changes test
observation, not dialog persistence or user data. If a test migration fails, restore only the local
test subclass/callback wiring; do not reintroduce a panel property. All tests use their existing
temporary stores, and no generated artifact is part of this change.

## Artifacts and Notes

The important proof is the focused test result plus the zero-match grep:

    $ .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py -k refinement_dialog
    .....                                                                    [100%]
    5 passed, 105 deselected

    $ rg -n '_active_refinement_dialog|_set_active_refinement_dialog' src tests/unit/test_qt_signing_shell.py
    (no matches)

The exact count may differ if the test corpus changes; update this example when recording final
evidence.

## Interfaces and Dependencies

The production interface remains `SignaturePropertiesPanel.open_refinement_dialog() -> bool` and
`SignatureRefinementDialog.open(draft) -> RefinementDialogResult`. The only test observation uses
the existing `active_state_changed: Callable[[RefinementDialogState | None], None]` constructor
callback on a test-local subclass. No new runtime dependency, persisted field, Qt signal, or public
AppFrame property is introduced.

Revision note: 2026-08-16 / Codex. Completed and committed as `12b1803cc` after the safe-links cleanup
audit found the refinement dialog cache was the only removable test-only production backdoor with no
live source consumers.
