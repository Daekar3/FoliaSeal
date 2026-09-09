# Add Ctrl+Y as an alternate Redo shortcut

This ExecPlan is a living document. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` current as work proceeds. The plan follows the repository's ExecPlan requirements in `/home/daekar/.codex/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

Users who instinctively use the familiar `Ctrl+Y` Redo shortcut should be able to redo the same edit that currently responds to `Ctrl+Shift+Z`. After this slice, `Edit > Redo` continues to display `Ctrl+Shift+Z` as its primary shortcut, while `Ctrl+Y` is accepted as an alternate. Both shortcuts must reach the same existing, focus-sensitive Redo command: a focused native text editor keeps ownership of its own text history, and viewer/placement focus routes through the existing placement-history session boundary. A user can observe the result by making a placement edit, undoing it, and pressing either shortcut once to restore it; the keyboard-shortcuts help surface must list both bindings.

This is a narrow behavior and documentation slice. It must not introduce a second Redo action, callback, shortcut object, history owner, placement-history path, or direct viewer history implementation.

## Child ExecPlan Dependencies

- [x] Gate 10 placement history and keyboard interaction recovery are complete and provide the existing typed Redo boundary.
- [x] The installed Gate 10 acceptance confirms `Ctrl+Shift+Z` and one-step placement Redo behavior before this alias is added.
- [x] The implementation and focused regression tests in this plan are complete.
- [x] Governing documentation and historical acceptance-plan notes are reconciled.
- [x] Final full-suite, documentation, and cleanup validation is complete.

This plan has no child plans. The implementation worker must finish the complete slice in this file before requesting final review or commit.

## Progress

- [x] (2026-09-08) Confirmed the existing authoritative command registry, AppFrame Redo callback, focus-sensitive routing, viewer keyboard fallback, and keyboard-help generator.
- [x] (2026-09-08) Recorded the decision to keep `Ctrl+Shift+Z` primary/menu-visible and add `Ctrl+Y` only as an alternate binding.
- [x] (2026-09-08) Added typed command metadata for one primary shortcut plus alternate shortcuts without changing unrelated command definitions.
- [x] (2026-09-08) Applied both shortcuts to the single Redo `QAction` using Qt's multi-shortcut API, while retaining the primary shortcut for menu display and compatibility with test doubles.
- [x] (2026-09-08) Extended the viewer's direct placement-key fallback so `Ctrl+Y` invokes the same existing Redo branch exactly once.
- [x] (2026-09-08) Added TDD coverage for metadata, real/fake QAction shortcut registration, native-editor routing, viewer placement routing, and help discoverability.
- [x] (2026-09-08) Focused Qt/app-frame/viewer/accessibility validation passed: `151 passed`.
- [x] (2026-09-08) Added explicit public-behavior coverage proving plain `Y` and `Ctrl+Shift+Y` do not dispatch Redo in either viewer placement focus or the application-frame action path.
- [x] (2026-09-08) Compliance review evidence recorded: `151` focused tests passed; the authoritative full suite reported `1665 passed, 20 skipped, 1 warning`; the previously transient preview-parity failures did not reproduce.
- [x] (2026-09-08) Updated `docs/UI_SPEC.md`, `docs/ARCHITECTURE.md`, and the Gate 10 acceptance status note to describe the accepted alias accurately.
- [x] (2026-09-08) Focused/full tests, Ruff, diff checks, and offscreen Qt shortcut acceptance completed; the audit left no owned temporary process or dialog.
- [x] (2026-09-08) Recorded final evidence and retrospective; the focused commit remains delegated to the commit worker.
- [x] (2026-09-08) Added real offscreen production-composition coverage that opens the Keyboard Shortcuts dialog, verifies one visible Redo entry with both bindings, and closes it cleanly.

## Surprises & Discoveries

- Observation: the application already has one typed `AppFrameCommandId.REDO`, one AppFrame callback (`_redo_edit`), and one menu action. The command definition currently stores only the primary string `Ctrl+Shift+Z`.
  Evidence: `src/foliaseal/presentation/qt/app_frame_command_model.py`, `src/foliaseal/presentation/qt/app_frame.py`, and the existing AppFrame command tests.
- Observation: `viewer_widget.py` independently handles `Ctrl+Z` and treats `Ctrl+Shift+Z` as Redo when the viewer owns placement focus.
  Evidence: the viewer key-press branch checks `Key_Z`, Control, and Shift before calling its existing `PlacementHistory.redo()` path.
- Observation: the keyboard-shortcuts dialog is generated from command definitions, so adding an alternate binding to the definition is necessary for help discoverability; editing help text alone would create two sources of truth.
  Evidence: `src/foliaseal/presentation/qt/support_dialogs.py:shortcut_text()` iterates `ALL_COMMAND_DEFINITIONS`.
- Observation: native editor routing is decided inside the existing AppFrame Redo callback, while the viewer fallback is only relevant when the canvas receives the event.
  Evidence: `FoliaSealAppFrame._redo_edit()` inspects focused `QLineEdit`/`QTextEdit` capability before delegating to the workspace session; `viewer_widget.py` owns canvas key events.
- Observation: the real offscreen frame and viewer tests confirm the ordered action bindings, native editor `Ctrl+Y` redo, disabled-action no-op, and viewer placement `Ctrl+Y` redo through the existing history path.
  Evidence: `tests/integration/test_gui_launch_no_document.py` and `tests/integration/test_view_navigation_shortcuts.py`.

## Decision Log

- Decision: preserve `Ctrl+Shift+Z` as the primary and menu-visible Redo shortcut, and accept `Ctrl+Y` as an alternate.
  Rationale: it preserves the established Linux/Qt convention and existing documentation while accommodating the user's learned cross-platform convention.
  Date/Author: 2026-09-08 / Codex.
- Decision: represent the alias in the typed command definition and derive QAction/help metadata from that definition.
  Rationale: the command registry is the authoritative application-frame surface; deriving both the QAction bindings and help text prevents drift.
  Date/Author: 2026-09-08 / Codex.
- Decision: use one `QAction` with multiple shortcuts and extend the existing viewer fallback rather than adding a `QShortcut`, second action, or second callback.
  Rationale: one action preserves menu enablement, focus-sensitive routing, accessibility metadata, and one history owner; a second shortcut object could dispatch around those policies or invoke Redo twice.
  Date/Author: 2026-09-08 / Codex.
- Decision: treat `Ctrl+Y` as Redo only with the Control modifier and do not reinterpret unrelated `Y` or shifted variants in the viewer fallback.
  Rationale: the alias must be predictable and must not steal ordinary text/document input; native editors remain governed by the existing AppFrame focus policy.
  Date/Author: 2026-09-08 / Codex.

## Outcomes & Retrospective

Completed files are `src/foliaseal/presentation/qt/app_frame.py`,
`src/foliaseal/presentation/qt/app_frame_command_model.py`,
`src/foliaseal/presentation/qt/support_dialogs.py`,
`src/foliaseal/presentation/qt/viewer_widget.py`, their focused tests, and the governing/status
documentation named above. Focused validation passed 151 tests; the authoritative full suite passed
1665 tests with 20 skips and one warning. The real offscreen KeyboardShortcutsDialog smoke passed
(`test_real_qt_keyboard_accessibility_and_support_surfaces`, 1 passed in 0.38s) and showed the
single Redo line `Redo: Ctrl+Shift+Z (alternate: Ctrl+Y)`. `Ctrl+Shift+Z` remains unchanged and menu-visible;
`Ctrl+Y` reaches the same Redo operation, native editor history remains separate from placement
history, the help surface lists both bindings, and no second action/history owner was introduced.
Offscreen/real-Qt source acceptance passed; installed-package acceptance is not claimed for this
shortcut-only follow-on because the Gate 10 installed history path was already accepted and this
slice did not rebuild or install a package.

## Context and Orientation

FoliaSeal's top-level Qt window is implemented in `src/foliaseal/presentation/qt/app_frame.py`. It creates one `QAction` per typed `AppFrameCommandId`, attaches the callback, applies the command's displayed shortcut and accessibility metadata, and projects enablement from `WorkspaceActionState`. `AppFrameCommandId.REDO` and its definition live in `src/foliaseal/presentation/qt/app_frame_command_model.py` inside `EDIT_COMMAND_DEFINITIONS`; its current primary shortcut is `Ctrl+Shift+Z`.

`FoliaSealAppFrame._redo_edit()` is the sole application-frame Redo callback. It first checks whether a native `QLineEdit` or `QTextEdit` owns focus and invokes that editor's native `redo()` when available. Otherwise it calls `SigningWorkspaceSessionPort.redo_placement()`, which reaches the viewer-owned `PlacementHistory`. Do not expose or duplicate that history in this slice.

`src/foliaseal/presentation/qt/viewer_widget.py` receives key events when the viewer has placement focus. Its existing `Ctrl+Z`/`Ctrl+Shift+Z` branch directly replays the viewer-owned placement history because the canvas may receive key events without the top-level QAction being the event consumer. Extend that branch's alias handling carefully, preserving the existing pending keyboard-adjustment flush and overlay synchronization.

`src/foliaseal/presentation/qt/support_dialogs.py` builds the local Keyboard Shortcuts dialog from `ALL_COMMAND_DEFINITIONS`. Its output is user-facing and must show both Redo bindings, with `Ctrl+Shift+Z` clearly identified as primary or first and `Ctrl+Y` identified as alternate. `docs/UI_SPEC.md` is the governing user-interface contract. `docs/ARCHITECTURE.md` records the command/action/history boundary and must explain the alias without changing ownership. The Gate 10 and keyboard-repeat ExecPlans previously described Ctrl+Y as a future opportunity; their status notes now point to this completed follow-on without changing their historical acceptance evidence.

The authoritative behavior hierarchy remains `docs/SPEC.md` for product scope, `docs/SCHEMAS.md` for domain/persistence semantics, and `docs/UI_SPEC.md` for interface realization. This slice changes neither signing schemas nor PDF output.

## Change Slice

The primary change class is a behavior change: add one alternate Redo keyboard binding through the existing command/action and viewer seams. A synchronized documentation/status update is required because the governing UI contract and historical Gate 10 notes currently say the alias is deferred. No generated artifact, package payload, signing schema, persistence format, PDF renderer, GUI topology, or unrelated shortcut may change.

Forbidden scope includes adding a second Redo QAction or QShortcut, moving or duplicating `PlacementHistory`, changing `Ctrl+Shift+Z`, changing Undo, altering text-editor history semantics, broad command-registry refactors, renaming unrelated shortcuts, or retaining silent compatibility fallbacks that hide a broken required action interface. Temporary test PDFs or screenshots belong only under `/tmp` and must be removed after validation.

## Plan of Work

First inspect the current typed command-definition and QAction seams, including all fake QAction test doubles. Extend the definition model with an explicit alternate-shortcut representation that remains empty for every existing command and sets only Redo's alternate to `Ctrl+Y`. Keep the existing `shortcut` field or an equivalent primary field so current menu rendering and callers continue to see `Ctrl+Shift+Z` first. Make the representation typed and deterministic rather than parsing a display string.

Update `FoliaSealAppFrame._action()`/`_command_action()` in `src/foliaseal/presentation/qt/app_frame.py` so the single Redo QAction receives the ordered shortcut list through `QAction.setShortcuts`: primary first, alternate second. Preserve the primary shortcut's normal menu display and existing fake-binding behavior; update the minimal fake QAction surface to record multiple shortcuts. Do not create another action or callback. Add a real Qt assertion that `action.shortcut().toString()` remains `Ctrl+Shift+Z` and that `action.shortcuts()` contains `Ctrl+Shift+Z` followed by `Ctrl+Y`.

Update `src/foliaseal/presentation/qt/viewer_widget.py` so the direct placement fallback recognizes `Ctrl+Y` as Redo and calls the exact same existing flush/history/apply/overlay path as `Ctrl+Shift+Z`. Require Control, avoid treating ordinary `Y` as a command, preserve the existing Shift+Z behavior, and ensure one event produces one replay. Add real event tests for both shortcuts with the viewer focused; verify that each changes placement once and that no extra history step is created.

Update `shortcut_text()` in `support_dialogs.py` to derive a compact, unambiguous line from the typed definition, for example `Redo: Ctrl+Shift+Z (alternate: Ctrl+Y)`. Keep all other help lines unchanged. Add a focused help-dialog test proving both bindings are present and that there is only one Redo line.

Update governing and status documentation. In `docs/UI_SPEC.md`, document `Ctrl+Y` as an alternate Redo binding while retaining `Ctrl+Shift+Z` as the primary/menu-visible shortcut and preserving focus-sensitive native-editor versus placement routing. In `docs/ARCHITECTURE.md`, update the command/action and viewer-history boundary and its decision/status log. In the relevant Gate 10/history ExecPlans, replace the former “future Ctrl+Y opportunity” status with the actual implementation and validation evidence; do not rewrite historical acceptance scope beyond this alias. Review README/help package content only if an existing shortcut list is duplicated there; do not add a second manual source of truth.

Use test-first development: add failing tests for command metadata and shortcut registration, then implement the narrow production change; add failing real/offscreen tests for native-editor and viewer placement routing, then implement or adjust only the required seam. Preserve existing command enablement tests and prove disabled Redo remains disabled for both bindings. Verify that a focused native editor's `Ctrl+Y` calls native `redo()` and never calls placement Redo; verify that viewer placement focus routes through the existing placement history and never calls a native editor.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Establish a clean baseline without modifying user changes:

       git status --short
       rg -n "REDO|Ctrl\\+Shift\\+Z|setShortcut|setShortcuts|shortcut_text" src tests docs

   If unrelated changes are present, preserve them and keep this slice's edits isolated.

2. Add/update tests before implementation. At minimum cover the command definition's primary/alternate metadata, fake QAction registration, real Qt menu/action shortcut ordering, help text, native-editor routing, viewer placement routing, disabled-state behavior, and unchanged `Ctrl+Shift+Z` behavior. Run the smallest relevant tests and record the expected pre-change failures.

3. Implement the typed metadata and single-action multi-shortcut registration in `app_frame_command_model.py` and `app_frame.py`. Update only the test double methods needed to model Qt's `setShortcuts` and shortcut inspection.

4. Implement the viewer fallback alias in `viewer_widget.py`, reusing the existing placement Redo branch and pending-adjustment boundary. Do not add another history call path.

5. Update `support_dialogs.py` and the governing/status documentation named above. Run `git diff --check` and inspect the diff for accidental broad changes.

6. Run focused validation:

       QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/integration/test_gui_launch_no_document.py tests/integration/test_placement_gate10.py
       .venv/bin/pytest -q tests/integration/test_accessibility_acceptance.py
       .venv/bin/ruff check src tests
       git diff --check

   The focused suite must pass, including the new alias tests. The real Qt assertions must show the primary shortcut first and the alternate present; no test may require a second Redo action.

7. Run the complete repository suite:

       .venv/bin/pytest -q

   Expect the complete suite to pass with only the repository's already-known skips/warnings. If a failure reveals a stale test double or documentation assertion, update the narrow test seam and record the discovery in `Surprises & Discoveries`; do not add a production fallback that weakens the typed contract.

8. Perform an available GUI smoke check using the built/current development application or an offscreen production composition. Open a disposable PDF, make a placement edit, undo it, focus the viewer, and press `Ctrl+Y`; confirm the rectangle is restored once. Repeat with `Ctrl+Shift+Z`. Focus a native text editor, create/undo text, and confirm `Ctrl+Y` redoes text without changing placement. Open Help > Keyboard Shortcuts and confirm both Redo bindings are visible. Clean up the disposable document, window, dialogs, and any owned process.

9. Before commit, re-read this plan and update every Progress item, all evidence, the retrospective, and the revision note at the bottom. The documentation worker must reconcile architecture and status documents, and the commit worker must create one focused commit containing this behavior plus its necessary evidence/documentation updates.

## Validation and Acceptance

Acceptance is behavioral and boundary-focused:

- `Edit > Redo` remains one menu action with primary displayed shortcut `Ctrl+Shift+Z`; its Qt shortcut list contains exactly the ordered primary and alternate bindings `Ctrl+Shift+Z`, `Ctrl+Y`.
- `Ctrl+Shift+Z` continues to redo the existing native-editor or placement history operation exactly once.
- `Ctrl+Y` invokes that same callback/action exactly once. With a focused `QLineEdit` or `QTextEdit`, native text Redo is used and placement history is untouched. With viewer/placement focus, placement Redo is used and native editor history is untouched.
- A disabled Redo action remains disabled regardless of which alias the user attempts; no shortcut bypasses command enablement or lifecycle policy.
- The viewer's direct canvas fallback accepts `Ctrl+Y` only as the placement Redo alias and preserves flush, overlay, history, and error behavior of `Ctrl+Shift+Z`.
- The keyboard-shortcuts help surface lists one Redo entry containing both bindings, with the primary first and the alternate clearly labeled.
- `docs/UI_SPEC.md`, `docs/ARCHITECTURE.md`, and affected ExecPlan status/evidence no longer claim that Ctrl+Y is unimplemented; no governing document contradicts the new behavior.
- Focused tests, the full suite, Ruff, and `git diff --check` pass. The GUI smoke check leaves no FoliaSeal process or dialog owned by the audit.

Do not claim installed-package acceptance unless a fresh package containing this change is built, installed, and exercised. If installation requires interactive `sudo`, record that as a HITL gate and stop only at that exact external action after all source and automated work is complete.

## Idempotence and Recovery

The change is additive and safe to rerun. Repeated test runs use temporary stores and disposable PDFs under `/tmp`; do not modify the user's signing library or documents. If a test or smoke launch leaves an application process or dialog, identify the process created by the audit and close it cleanly before continuing. Never kill an unrelated user FoliaSeal instance.

If the implementation causes duplicate Redo events, first inspect QAction shortcut context and the viewer's direct event path; remove the duplicate dispatch at the seam rather than adding debouncing or a second state store. If a native editor receives the wrong action, preserve the existing `_redo_edit()` focus test and correct only action context/routing. If the help output drifts, derive it from the typed command definition instead of hand-editing a second list.

Rollback is limited to reverting this slice's focused commit after preserving test/documentation evidence. Do not reset or discard unrelated working-tree changes.

## Artifacts and Notes

Record concise evidence here as it becomes available. Expected examples are:

    Real QAction shortcut ordering: ['Ctrl+Shift+Z', 'Ctrl+Y']
    Keyboard help line: Redo: Ctrl+Shift+Z (alternate: Ctrl+Y)
    Focused tests: <actual passed count>
    Full suite: <actual passed/skipped/warning summary>

No generated package, screenshot, PDF, certificate, or persistent user data belongs in this source slice. Any temporary runtime evidence must remain outside the repository under `/tmp` and be cleaned up.

## Interfaces and Dependencies

The implementation must preserve these interfaces and ownership rules:

- `AppFrameCommandDefinition` remains the typed source of command metadata. Add an explicit ordered alternate-shortcut field or equivalent typed representation; do not encode aliases in the display text.
- `AppFrameCommandId.REDO` remains the only Redo command identifier.
- `FoliaSealAppFrame._redo_edit()` remains the only application-frame Redo callback and continues to route native editor versus placement history by focus.
- The single Redo QAction remains created through `_command_action()` and `_action()`; use Qt's `QAction.setShortcuts` for the ordered list and retain the primary `setShortcut`/display behavior as required by the binding adapter.
- `SigningWorkspaceSessionPort.redo_placement()` and `viewer_widget.py`'s existing `PlacementHistory.redo()` path remain the only placement Redo interfaces.
- `shortcut_text()` must consume the same typed command metadata used to register the QAction.
- No new dependency or library is required. Use the existing PySide6 Qt bindings, test doubles, pytest, and Ruff configuration.

The expected final public behavior is one Redo command with two keyboard sequences, not two commands with one sequence each.

## Revision Note

Created 2026-09-08 to capture the user's approved Ctrl+Y Redo-alias decision as a complete, independently executable slice. The plan explicitly retains `Ctrl+Shift+Z` as primary, requires one authoritative action/callback/history owner, covers native-editor and viewer routing, and includes help and governing-document reconciliation.
