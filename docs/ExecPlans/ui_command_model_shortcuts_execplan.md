# Desktop command model and shortcuts

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

This child establishes the typed Edit registry and native Cut, Copy, Paste, and Select All for the
currently focused `QLineEdit` or `QTextEdit`, using Ctrl+X, Ctrl+C, Ctrl+V, and Ctrl+A. The existing
focus-sensitive Undo/Redo boundary remains unchanged: native editors own their local text history,
while viewer or placement focus routes Undo/Redo to the public placement-history boundary. The same
Select All action now delegates to the completed document-selection child when no native text editor
owns focus; Help is implemented by its separate packaged-support child. This is a
bounded increment toward UI_SPEC section 7 and acceptance scenario 8.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current implementation and write failing focused tests for the File command foundation.
- [x] (2026-08-09) Implement the typed File command registry and lifecycle application/Qt path.
- [x] (2026-08-09) Review migrated compatibility and phase3 product cruft; no retirement condition in the command-model seams was met, so no unrelated removal was mixed into this slice.
- [x] (2026-08-09) Run focused, regression, and real-Qt validation; record evidence and clean up.
- [x] (2026-08-09) Historical broad completion gate superseded by dependency-ordered command slices;
  each completed increment now reconciles its owning architecture/status records and commit evidence.
- [x] (2026-08-09) Loop 5: add typed View Previous Page and Next Page commands through the public
  session port; keep Fit/zoom/search/history commands deferred until their truthful seams exist.
- [x] (2026-08-09) Loop 5 compliance fixes: synchronize boundary capability after viewer-owned
  navigation, use explicit registry lookup, and prove Page Up/Page Down single-dispatch behavior.
- [x] (2026-08-09) Removed the unused per-menu definition lookup helpers after confirming there
  were no remaining repository callers; `command_definition()` is now the sole frame lookup.
- [x] (2026-08-09) Loop 5 architecture/status documentation updated; the command-model child remains
  open for the deferred menus and signed-state policy.
- [x] (2026-08-09) Loop 8: migrated the existing Settings actions to the shared typed command
  registry with unique mnemonics, stable IDs/object names, Qt descriptions, and callback-routing
  coverage. Edit, Signing, and remaining View commands remain deferred until truthful
  behavior seams exist.
- [x] (2026-08-09) Loop 8 focused validation passed (`44 passed`), full validation passed
  (`1185 passed, 20 skipped, 1 warning`), and the bounded launch audit cleaned its isolated root
  with no lingering FoliaSeal/PySide6 process; the launch remains limited by the local
  `SingleInstanceUnavailable` endpoint error.
- [x] (2026-08-09) Architecture and parent-plan status documentation were reconciled; the bounded
  Settings outcome is ready for commit while the broader child remains open.
- [x] (2026-08-09) Re-audited the remaining raw actions against UI_SPEC: Select Text is currently
  under Edit but belongs under View, and Copy is currently raw but belongs under Edit.
- [x] (2026-08-09) Add red registry/menu-topology tests for typed Select Text and Copy.
- [x] (2026-08-09) Implement the two typed definitions and preserve existing enablement/check state
  and public maintenance-port callback routing; Copy is selection-sensitive and owns Ctrl+C.
- [x] (2026-08-09) Focused validation passed (`165 passed`), full validation passed (`1193 passed,
  20 skipped, 1 warning`), Ruff and diff checks passed, and the real-Qt no-document menu test
  passed; the bounded launch remains limited by the known local QLocalServer endpoint error.
- [x] (2026-08-09) Kept unsupported Undo/Redo/Cut/Paste/Help/Signing commands out while the
  existing truthful View seams were incrementally migrated.
- [x] (2026-08-10) Added the typed View zoom command child: Zoom In/Out use `Ctrl++`/`Ctrl+-`,
  Reset Zoom is a real menu action without a conflicting shortcut, and all three route through the
  public session port while reusing the existing clamped viewer zoom policy.
- [x] (2026-08-10) Selected the next truthful command increment: expose the existing internal-link
  history through View Back/Forward with `Alt+Left`/`Alt+Right`, routed through the public session
  port and synchronized from `WorkspaceActionState`.
- [x] (2026-08-10) Implemented typed View Back/Forward definitions, frame actions, public-port
  callbacks, and capability/status synchronization for open, internal navigation, Back, Forward,
  replacement, and close.
- [x] (2026-08-10) Added fake-frame and real offscreen Qt coverage for disabled initial state,
  shortcut dispatch, Back→Forward transitions, and branch-clears-Forward behavior.
- [x] (2026-08-10) Reconciled `docs/ARCHITECTURE.md` and the parent compliance plan; the architecture
  row now records the typed registry, public session-port routing, and capability/status projection.
- [x] (2026-08-10) Full validation passed (`1437 passed, 20 skipped, 1 warning`), focused command
  and real-Qt coverage passed (`63 passed`), Ruff/pip/diff checks passed, and the bounded GUI audit
  exited at the known isolated `SingleInstanceUnavailable` endpoint before frame creation. No
  matching FoliaSeal/PySide6/pytest process remained and the owned temporary root was removed.
- [x] (2026-08-10) Committed the Back/Forward increment as `168124466`.
- [x] (2026-08-10) Selected the initial truthful Signing increment: add a Signing menu with
  Signature Library and Sign and save; placement commands were deferred until their public seam.
- [x] (2026-08-10) Added the Signing menu definitions/actions and corrected Sign and save enablement
  to use the public `can_submit_sign_request()` readiness capability rather than mere workspace-open
  state; readiness-changing runtime events refresh the menu action and active signing disables it.
- [x] (2026-08-10) Implemented and validated the Signing menu, reconciled architecture/status
  documentation, ran the bounded GUI audit, cleaned owned resources, and committed this increment as
  `64bef66b2`.
- [x] (2026-08-10) Selected the next truthful Signing increment: expose Place Signature, Adjust
  Placement, and Remove Placement over the existing runtime placement behavior, with fixed unsigned
  fields remaining non-editable.
- [x] (2026-08-10) Added typed placement command definitions, public session capabilities/actions,
  truthful frame enablement/status synchronization, focused and real offscreen action coverage, and
  fixed-field protection through the runtime boundary.
- [x] (2026-08-10) Fresh-scan selected the next truthful command increment: Edit Undo and Redo over
  the existing placement-history seam. Native QLineEdit undo/redo remains authoritative when a text
  editor owns focus; placement history is used only for viewer/placement focus.
- [x] (2026-08-10) Added red/green command, focus-routing, capability, and real offscreen menu tests;
  implemented the public session/runtime boundary and synchronized action state after mutations and
  lifecycle clearing.
- [x] (2026-08-10) Added direct viewer `PlacementHistory` public-method coverage and native text
  editor Redo coverage; the focused command/viewer/runtime/session/offscreen set is `112 passed`.
- [x] (2026-08-10) Reconciled architecture/status documentation for the public Undo/Redo boundary,
  focus-sensitive native text routing, and placement-history semantics. Full validation is `1443
  passed, 20 skipped, 1 warning`; the bounded GUI audit exits at `SingleInstanceUnavailable`, with
  no matching processes or temporary audit root remaining. Commit and remaining command-family
  status remain the parent handoff gates.
- [x] (2026-08-10) Fresh-scan selected native-editor Cut, Copy, Paste, and Select All as the next truthful
  Edit increment; viewer Select All remains integrated here, while packaged Help is owned by its
  completed support child.
- [x] (2026-08-10) Added typed native Edit definitions, focus-sensitive state projection, native
  editor callbacks, selection/clipboard signal synchronization, and fake/real offscreen coverage.
- [x] (2026-08-10) Reconciled architecture/status documentation; focused validation passed (`65 passed`),
  full validation passed (`1449 passed, 20 skipped, 1 warning`), and `git diff --check`/Ruff passed.
  The bounded GUI launch remains limited by the known isolated `SingleInstanceUnavailable` endpoint
  error and requires no lingering process or temporary audit root.
- [x] (2026-08-10) Reconciled the completed viewer Select All child into the shared Edit command
  contract; native editor precedence remains at AppFrame, and the no-native-editor path now uses
  the public workspace session port for current-page document text. Packaged Help is owned by its
  completed support child.
- [x] (2026-08-10) Reconciled the viewer keyboard contract with UI_SPEC §8: Page Up/Page Down
  remain page-relative commands, while only `Ctrl+Home`/`Ctrl+End` jump to the first/last page and
  bare Home/End pass through to the focused widget hierarchy. The navigation child owns the
  implementation and its fake/real Qt evidence; this parent remains open for unrelated deferred
  command families and release gates.

## Surprises & Discoveries

- Observation: command enablement is currently distributed across frame and workspace action-state
  code; this child must establish one typed command model with keyboard-equivalent actions.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: a newly opened workspace has a suggested output path before the user has accepted
  one, so File > Save must explicitly enter Save As before submitting the signing request.
  Evidence: `SigningWorkspaceCompositionService` seeds `SigningDraftWorkflow.output_pdf_path` with
  `suggest_signed_output_path`; the frame now consumes the typed
  `has_explicit_output_pdf_path()` seam before Save.
- Observation: PySide6 `QAction` has no portable `setAccessibleName()` API. File actions therefore
  use normative mnemonic text plus Qt-supported tooltip/status-tip descriptions and stable object
  names; real-Qt integration coverage verifies those properties.
- Observation: the existing session port exposes previous/next page navigation, and Loop 5 adds the
  frame's typed View menu. The viewer's reset zoom is not equivalent to UI_SPEC's Fit Page, so this
  loop does not register a misleading fit command.
  Evidence: `SigningWorkspaceSessionPort.go_to_previous_page()` and
  `go_to_next_page()` route through `SigningShellAdapter`; the typed View definitions now live in
  `VIEW_COMMAND_DEFINITIONS` and are mapped by `command_definition()`.
- Observation: Settings already had five concrete frame callbacks, so those actions could be
  migrated without inventing behavior; Help, Signing, and the full Edit menu do not yet have
  complete truthful seams.
  Evidence: Loop 8 explorer review and the resulting `SETTINGS_COMMAND_DEFINITIONS` registry.
- Observation: Select Text and Copy are concrete, tested frame callbacks but bypass the typed
  registry and are mounted under the wrong menus relative to UI_SPEC §7.
  Evidence: `FoliaSealAppFrame._install_menus()` and explorer review dated 2026-08-09.
- Observation: internal-link history already has a complete application/runtime/session-port seam,
  but the app-frame View menu has no actions or enabled-state projection for it.
  Evidence: `SigningWorkspaceRuntime.go_back_link()`/`go_forward_link()`, the corresponding
  `SigningWorkspaceSessionPort` methods, and the current `VIEW_COMMAND_DEFINITIONS` registry.
- Observation: the correct disabled-state behavior is capability-based rather than simply
  workspace-open: Back is enabled only after an internal destination is visited, Forward is enabled
  only after going back, and a new internal navigation clears Forward.
  Evidence: `ViewerLinkHistory` and `SigningWorkspaceRuntime.can_go_back_link()`/
  `can_go_forward_link()`.
- Observation: a real offscreen app-frame test can exercise the production `QAction` shortcut and
  workspace-host mount without requiring a display-backed FoliaSeal launch by injecting a QWidget
  shell factory that implements the public session/maintenance ports.
  Evidence: `tests/integration/test_gui_launch_no_document.py::test_real_qt_view_history_actions_dispatch_through_open_workspace`.
- Observation: UI_SPEC requires all five Signing commands, and placement actions must remain
  capability-driven because existing unsigned signature fields have fixed page and geometry.
  Evidence: `SigningWorkspaceSessionPort.can_place_signature_placement()`,
  `.can_adjust_signature_placement()`, `.can_remove_signature_placement()`, and the runtime's
  `signature_field_name` guard.
- Observation: the existing `WorkspaceActionState.save_enabled` intentionally means only
  workspace-open for File Save, which is too broad for a dedicated Signing-menu command. The menu
  action therefore needs a separate public readiness capability while File Save keeps its established
  path-selection/readiness-flow behavior.
  Evidence: the compliance review found an unready Sign and save action enabled immediately after
  open; `SigningWorkspaceSessionPort.can_submit_sign_request()` now projects `preview().can_submit`.
- Observation: native Cut, Copy, Paste, and Select All are dependency-ready at the AppFrame edge because
  `_focused_text_editor()` already identifies the only widgets that may own these operations.
  Evidence: the current frame routes Undo/Redo through the same focus seam, while the viewer's public
  selection API has no current-page “select all extractable text” operation. This slice must therefore
  keep the new commands disabled without a focused native editor and leave viewer Select All to a
  later document-selection child.

## Decision Log

- Decision: honor SPEC.md product scope, SCHEMAS.md persistent-object semantics, and UI_SPEC.md interaction wording in that order.
  Rationale: the repository explicitly defines those authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep this change limited to one observable desktop command model and shortcuts outcome.
  Rationale: narrow commits make GUI regressions and recovery auditable.
  Date/Author: 2026-08-09 / Codex
- Decision: Loop 2 delivers the typed File registry and complete File lifecycle only; Edit, View,
  Signing, Settings, and Help command entries remain owned by their named follow-up children.
  Rationale: those commands depend on viewer, signing-rail, support, and library surfaces that are
  not yet complete, while File lifecycle routing is independently testable now.
  Date/Author: 2026-08-09 / Codex
- Decision: File Save asks for an explicit output path on first use, then routes subsequent Save
  activations through the existing signing confirmation seam.
  Rationale: this preserves UI_SPEC's first-Save-as rule without duplicating signing policy in the
  frame.
  Date/Author: 2026-08-09 / Codex
- Decision: implement View Previous Page and Next Page as the next command-model increment, using
  Page Up/Page Down and the public session port; defer Fit Page, Fit Width, exact zoom, Find,
  Document Signatures, and Back/Forward until their public behavior seams are available.
  Rationale: these two commands already have real application behavior and can be proven without
  inventing disabled or misleading actions for unfinished viewer features.
  Date/Author: 2026-08-09 / Codex
- Decision: migrate the existing Settings callbacks into the typed registry as the final bounded
  command-model increment, while leaving unsupported Edit/Signing/Help placeholders out of the UI.
  Rationale: each migrated Settings action has a concrete frame boundary and can expose stable
  keyboard metadata; adding commands without behavior would violate UI_SPEC's truthful-action rule.
  Date/Author: 2026-08-09 / Codex
- Decision (superseded): register only Select Text and Copy in this increment, moving Select Text to View and
  keeping Copy in Edit; do not add unsupported editing or signing placeholders.
  Rationale: both actions already have real maintenance-port behavior and state projection, while
  Undo/Redo/Cut/Paste/Select All, Help, Signing, and advanced View commands lacked complete truthful
  seams. A typed correction improves UI_SPEC compliance without overstating capability.
  Date/Author: 2026-08-09 / Codex
- Decision: add only View Back and Forward in the current command-model increment, using the
  existing internal-link history callbacks and `Alt+Left`/`Alt+Right`; do not add browser history,
  page-history aliases, or placeholder commands.
  Rationale: UI_SPEC §7 explicitly requires Back/Forward, and the repository already owns a
  document-internal history boundary with observable capability methods. Keeping the actions tied
  to that boundary avoids misleading users about browser navigation or unrelated page movement.
  Date/Author: 2026-08-10 / Codex
- Decision (superseded): add only `Signature Library` and `Sign and save` to a new typed Signing
  menu increment; leave placement commands out until a public seam exists.
  Rationale: this was the bounded decision before the placement seam was added.
  Date/Author: 2026-08-10 / Codex
- Decision: add Place Signature, Adjust Placement, and Remove Placement in UI_SPEC order, routing
  mode changes/removal through `SigningWorkspaceSessionPort` and disabling all placement mutations
  for fixed unsigned signature fields.
  Rationale: the runtime already owns these behaviors and can expose truthful capability methods
  without moving geometry policy into AppFrame.
  Date/Author: 2026-08-10 / Codex
- Decision: add Cut, Copy, Paste, and Select All for a focused native `QLineEdit` or `QTextEdit`,
  using Ctrl+X, Ctrl+C, Ctrl+V, and Ctrl+A; do not claim viewer Select All in this slice.
  Rationale: Qt already owns the correct text-edit semantics and the frame has a tested focus seam,
  while viewer Select All requires a new current-page extraction/highlight capability. Keeping the
  commands disabled outside native text editors is more truthful than exposing a no-op or partial
  viewer command.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The File command foundation is implemented but this child is not complete: a novice can open a PDF,
choose an explicit output path on first Save, invoke signing through subsequent Save, choose Save As,
close the workspace, or exit the application. Focused and real-Qt checks are green (`35 passed` for
the app-frame/state/integration slice; `142 passed` including shell regressions). Loop 5 adds a
typed View menu with Previous Page and Next Page, Page Up/Page Down shortcuts, boundary-aware
enablement, public session-port routing, and callback synchronization after viewer-owned navigation.
The offscreen Qt shortcut test proves exactly one transition per key. Loop 8 also migrates the five
existing Settings callbacks into `SETTINGS_COMMAND_DEFINITIONS`, including unique mnemonics, stable
object names, Qt descriptions, and trigger-routing tests. The remaining gap is the rest of the
UI_SPEC command registry and its parent scenario evidence: Help content/actions and remaining View
behavior remain deferred to their owning viewer/document/support children. The current increment
wires document-internal Back/Forward, completes all five Signing actions, and adds focus-sensitive
  Undo/Redo over native text-editor and placement histories; browser navigation, viewer Select All,
  Help, and other unsupported command families remain out of scope. The native-editor Cut/Copy/Paste/
  Select All increment now has focused and real offscreen coverage. Final evidence for the prior
  increment is `1443 passed, 20 skipped, 1 warning` for the
full suite and `112 passed` for focused command/viewer/runtime/session/offscreen coverage; the
bounded launch returned `gui_rc=1` with
`SingleInstanceUnavailable`, then left no matching process or temporary root.

## Context and Orientation

The relevant code is app_frame.py; Qt action/menu construction; signing_shell ports; command-state tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “phase3” names identify
legacy evidence/harness infrastructure and must not appear in ordinary product-facing UI or new
primary contracts; production backend/evidence imports may be renamed only after a neutral migration
proves the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named implementation modules,
focused tests, bounded local evidence, and the minimum docs/status corrections needed to keep the
repository truthful. Do not mix unrelated architecture scans, V2 features, broad evidence
rebaselines, or packaging changes unless this slice explicitly requires them.

## Plan of Work

Extend the existing typed registry rather than introducing parallel raw `_action()` definitions.
For this increment, add `VIEW_BACK` and `VIEW_FORWARD` definitions with stable IDs, `Alt+Left` and
`Alt+Right` shortcuts, unique mnemonics, and accessible descriptions. Add matching action fields in
`FoliaSealAppFrame`, create them in the View menu, and route activation through
`SigningWorkspaceSessionPort.go_back_link()` and `go_forward_link()`. Extend
`WorkspaceActionState` and its open/closed constructors with `back_link_enabled` and
`forward_link_enabled`; update the frame synchronization method to query the session-port
capabilities after workspace open, link activation, Back/Forward, page navigation, replacement, and
close. Preserve the public session-port boundary and do not add commands whose behavior is not
implemented. Keep the earlier Select Text/Copy and zoom behavior unchanged except where list-based
tests must include the new actions.

For the current increment, add `SIGNATURE_LIBRARY` and `SIGN_AND_SAVE` definitions with stable IDs,
truthful menu text, accessible descriptions, and no shortcut unless an established shortcut already
exists. Add a `SIGNING_COMMAND_DEFINITIONS` tuple and include it in `ALL_COMMAND_DEFINITIONS`. In
`FoliaSealAppFrame._install_menus()`, create a Signing menu after View and before Settings; route
Signature Library to `show_reusable_object_library()` and Sign and save to `_save_document()`. The
library command remains enabled with the existing frame policy, including no-document launch, while
Sign and save mirrors the current Save action's output-path, confirmation, and session boundary with
its separate readiness/transaction gate. Place Signature and Adjust Placement use the existing public
signature interaction-mode command with distinct capability gates, and Remove Placement uses a public
session action that clears only editable visible-signature placement. Fixed unsigned signature-field
targets remain disabled for all placement mutations. Preserve all File/View/Settings ordering
contracts and update menu tests to use menu titles or typed action lookup where practical.

For the Undo/Redo increment, add `UNDO` and `REDO` to `AppFrameCommandId` and place them first in
`EDIT_COMMAND_DEFINITIONS` with `Ctrl+Z` and `Ctrl+Shift+Z`. Add public capability and action methods
to `SigningWorkspaceSessionPort`, `QtSigningWorkspaceSessionPort`, and
`SigningWorkspaceRuntime`; the runtime delegates to the viewer's existing `PlacementHistory` and
applies the restored rectangle through the existing typed placement callback. Add
`undo_placement_enabled` and `redo_placement_enabled` to `WorkspaceActionState`, and synchronize
them after placement edits, panel changes, undo/redo, open/close, discard, and successful signing.
At the frame edge, inspect the current Qt application focus before routing: if the focus widget
exposes native `undo()`/`redo()` and is a text editor, invoke that method and derive enablement from
its `isUndoAvailable()`/`isRedoAvailable()` state; otherwise route through the session port. This
keeps numeric fields' local editing history separate from document-placement history and avoids
private widget reach-through from the app frame.

For the current native-edit increment, add `CUT`, `COPY`, `PASTE`, and `SELECT_ALL` to
`AppFrameCommandId` and append them to `EDIT_COMMAND_DEFINITIONS` in UI_SPEC order around Copy.
Use Ctrl+X, Ctrl+C, Ctrl+V, and Ctrl+A, unique mnemonic text, stable object names, and truthful Qt
tooltip/status descriptions. Add frame action fields and callbacks that call only the focused editor's
native `cut()`, `copy()`, `paste()`, or `selectAll()` method. Extend edit-action synchronization so
these actions are enabled only when a focused editor exposes the corresponding capability
(`hasSelectedText` for Cut/Copy, `canPaste` where available, and any native editor for Select All);
refresh on focus, selection, and clipboard changes; and disable them when focus leaves a native
editor. Do not add a workspace-port method or a viewer fallback. Add fake-Qt unit tests for
disabled/no-editor state, enablement, menu dispatch, signal-driven transitions, and focus changes,
plus a real offscreen Qt test that drives menu actions and native keyboard shortcuts against a
`QLineEdit` and verifies observable text/clipboard behavior without touching placement history.

## Milestones

Milestone 1 inventories frame actions and writes red command-state tests. Milestone 2 centralizes
Select Text and Copy metadata and menu routing through the frame boundary. Milestone 3 verifies
menu/enablement parity in focused and real-Qt tests and records the remaining unsupported command
families as deferred. Milestone 4 adds internal-link Back/Forward to the same registry, proves
capability transitions (visit → Back → Forward and branch-clears-Forward), and runs the real
offscreen menu/action test. The parent command-model acceptance remains open until all named menus
have their owning slices and scenario evidence. Milestone 5 adds the two supported Signing actions,
proves no-document Library availability and readiness-aware Sign and save enablement/routing, and
runs a real offscreen menu-topology test. Milestone 6 adds Place Signature, Adjust Placement, and
Remove Placement over the public placement seam, proves fixed-field protection and truthful state
transitions, and runs the real offscreen Signing-menu test. Milestone 7 adds Edit Undo/Redo, proves
focus-sensitive native-text versus placement-history routing and capability transitions, and runs a
real offscreen menu/action test that creates, mutates, undoes, and redoes a placement.
Milestone 8 adds native-editor Cut, Paste, and Select All, proves focus-sensitive enablement and
  shortcut dispatch against a real `QLineEdit`, and records packaged Help as a separate completed
remaining dependency gaps.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e '_install_menus|_command_action|text_selection|copy_selected|SIGNING_COMMAND_DEFINITIONS|VIEW_COMMAND_DEFINITIONS|EDIT_COMMAND_DEFINITIONS' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_command_model.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_app_frame_workspace_action_state.py tests/integration/test_gui_launch_no_document.py
    .venv/bin/pytest -q tests/unit/test_placement_history.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_signing_workspace_session_port.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py -k 'cut or paste or select_all'
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_gui_launch_no_document.py -k 'edit or text'
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_gui_launch_no_document.py tests/integration/test_view_navigation_shortcuts.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_gui_launch_no_document.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check.

## Validation and Acceptance

Acceptance for this increment is behavioral: View Select Text, Back, and Forward plus Edit Copy are
defined by the one typed registry, appear in the normative menus, retain correct document-dependent
enablement/check state, and reach their existing public ports exactly once. Back is disabled until an
internal link creates history; Back moves to the prior internal destination and enables Forward;
Forward returns to the next destination; a new internal destination after Back clears Forward. File,
View page/zoom actions, and Settings remain green under their prior contracts. The full child
acceptance remains open for Help, remaining View behavior, signed-state policy,
and parent scenario requirements. Record final focused/full test counts, Ruff, diff checks,
and the real-Qt menu/action evidence; the display-backed audit remains environment-limited by the
known QLocalServer/`SingleInstanceUnavailable` failure. The Signing increment is complete: the menu
exposes all five commands in UI_SPEC order, keeps Library available with no document, enables Place
only for a new editable placement, enables Adjust/Remove only for an existing editable placement,
protects fixed unsigned fields, and disables placement actions during active signing. Sign and save
remains readiness/transaction gated; production Qt action routing and state transitions are covered
by the focused and real offscreen tests.

For the Undo/Redo increment, Edit presents Undo and Redo before Copy with the stated shortcuts.
With a placement-focused viewer, creating or moving a placement enables Undo, Ctrl+Z restores the
previous rectangle (or no placement), and Ctrl+Shift+Z restores the newer rectangle; the menu
actions update after every operation. With a focused numeric `QLineEdit`, the same shortcuts call
the line edit's native undo/redo and do not alter the placement rectangle. Changing non-placement
setup, opening or closing a document, discarding a draft, or successfully signing clears placement
history and disables both actions. The new focused tests must fail before the boundary exists and
pass afterward; full regression, Ruff, diff checks, and offscreen lifecycle cleanup must remain
green.

For the native-edit increment, Edit presents Cut, Copy, Paste, and Select All with Ctrl+X, Ctrl+C,
Ctrl+V, and Ctrl+A. With a focused `QLineEdit` containing selected text, Cut removes the selection
and places it on the native clipboard, Paste inserts clipboard text, and Select All selects the full
editor value. The same actions are enabled/disabled from the editor's native capability state and
dispatch through the menu while native keyboard shortcuts retain Qt's built-in editor semantics.
With the viewer, a button, or no native editor focused, Cut/Paste/Select All remain disabled and do not mutate placement or
document-selection state. Viewer Select All is explicitly not claimed by this increment.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, keyboard/menu input sequence and observed File action state, evidence path and
cleanup result, and compatibility grep proof. Loop 2 evidence is the offscreen real-Qt integration
assertion for File labels, shortcuts, tooltip/status descriptions, mnemonic text, and no-document
enablement; Loop 5 adds `tests/integration/test_view_navigation_shortcuts.py`, whose offscreen
QTest Page Down/Page Up sequence produced exactly one page transition and one render per key. The
Loop 8 Settings focused pass is `44 passed`; the prior Select Text/Copy increment's focused pass was
`165 passed`. The Back/Forward and Signing increments record their focused results and red-to-green
registry/state tests, along with the final full-suite count, Ruff, and diff results. The current
Signing focused command was `.venv/bin/pytest -q tests/unit/test_qt_app_frame.py
tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_signing_workspace_session_port.py
tests/integration/test_gui_launch_no_document.py` (`112 passed`), including production QAction
Undo/Redo and Place/Adjust/Remove routing. The
bounded `foliaseal gui` launch remains environment-limited because QLocalServer cannot claim its
isolated endpoint (`Unknown error 1`/`SingleInstanceUnavailable`), and the audit found no lingering
FoliaSeal/PySide6 processes after cleanup.

The contributing UI_SPEC scenarios are 3 (create/adjust/remove/undo/restore one placement) and 8
(keyboard-only signing workflow); this increment changes command behavior but adds no new SVG, so
the evidence record explicitly uses the existing command-model topology drawings without a new
SVG artifact.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Native-editor evidence recorded for this increment: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
tests/integration/test_gui_launch_no_document.py -k native_edit` passed (`1 passed`), the combined
app-frame/state/offscreen set passed (`65 passed`), and the full suite passed (`1449 passed, 20
skipped, 1 warning`). The real test covers Edit menu Cut/Copy/Paste/Select All, clipboard empty/nonempty
transitions, and Ctrl+A/C/X/V observable selection, clipboard, and text behavior; keyboard Select All
is validated by the resulting Qt selection rather than an overridden `selectAll()` call count.

## Idempotence and Recovery

Use temporary sibling outputs and isolated configuration for repeatable tests. If implementation
fails halfway, keep the source PDF and unsigned draft intact, terminate owned processes, remove only
this slice's generated artifacts, and update Progress with completed and remaining work. Re-running
the tests must not mutate user data or resurrect retired compatibility code.

## Artifacts and Notes

Record concise command output, focused screenshots/JSON under ignored artifacts/ when useful, and
the exact files changed. Do not commit generated PDFs, private keys, passwords, or machine-local
absolute paths.

## Interfaces and Dependencies

Use existing typed application workflows and public Qt ports rather than private child-widget
reach-through. The final interface must be exercised by tests/unit/test_qt_app_frame.py,
tests/unit/test_app_frame_workspace_action_state.py, tests/integration/test_gui_launch_no_document.py,
and the command-state assertions added for Settings. The Undo/Redo increment additionally requires
tests/unit/test_placement_history.py, tests/unit/test_qt_signing_workspace_runtime.py, and
tests/unit/test_signing_workspace_session_port.py. `QtSigningWorkspaceSessionPort` must expose
`can_undo_placement()`, `can_redo_placement()`, `undo_placement()`, and `redo_placement()`;
`SigningWorkspaceRuntime` must provide the corresponding typed methods and leave placement
application/history ownership in the viewer boundary.
The native-edit increment keeps Cut/Copy/Paste/Select All at the `FoliaSealAppFrame` edge: the frame
queries `_focused_text_editor()`, subscribes to native selection/clipboard changes, and calls only the
focused editor's native `cut()`, `copy()`, `paste()`, or `selectAll()` methods. No new
`SigningWorkspaceSessionPort` method is allowed for this increment; viewer Select All will require a
separate typed document-text-selection contract.
Any compatibility workspace adapter retained temporarily must have a named consumer and a retirement
condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_command_model_shortcuts_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-09 / Codex
Recorded the Loop 8 Settings-registry migration and narrowed remaining command-model work to
existing truthful Edit/Signing/Help/View seams rather than placeholder actions.
Revision note: 2026-08-09 / Codex
Selected the next bounded correction: typed View Select Text and Edit Copy registration with
existing callback/state behavior; unsupported command families remain deferred.
Revision note: 2026-08-10 / Codex
Selected the next bounded correction: typed View Back/Forward actions over the existing internal-link
history seam, with Alt+Left/Alt+Right shortcuts and capability-driven enablement. Browser history and
unsupported command families remain excluded.
Revision note: 2026-08-10 / Codex
Selected the next bounded correction: add typed Signing-menu Signature Library and Sign and save
commands over existing frame/session callbacks. Place Signature, Adjust Placement, and Remove
Placement remain excluded until a single public placement-command seam exists.
Revision note: 2026-08-10 / Codex
Selected the next bounded correction: add typed Place Signature, Adjust Placement, and Remove
Placement commands over the existing runtime placement behavior, with public capability gates that
keep fixed unsigned signature-field targets protected.
Revision note: 2026-08-10 / Codex
Selected the next bounded correction: add focus-sensitive typed Edit Undo/Redo over the existing
placement-history seam. Native text-editor undo remains local to the focused editor; viewer and
placement focus use the public workspace session boundary. This closes the direct UI_SPEC command
gap without adding unsupported editing commands.
Revision note: 2026-08-10 / Codex
Fresh compliance audit selected the next dependency-ready native-editor Edit increment: Cut, Copy,
Paste, and Select All over the existing `_focused_text_editor()` seam with Ctrl+X/Ctrl+C/Ctrl+V/Ctrl+A.
Selection and clipboard signals now keep action state current; the real offscreen test validates menu
dispatch and observable native keyboard behavior. Viewer Select All was subsequently implemented in
`ui_document_select_all_execplan.md` over the public document-selection contract, preserving native
editor precedence; final release scenario evidence remains explicitly deferred, while packaged Help
is implemented and validated by `ui_help_support_execplan.md`.
