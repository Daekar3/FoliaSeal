# Desktop command model and shortcuts

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

This child now records the complete typed desktop command model required by UI_SPEC section 7 and
the keyboard portions of acceptance scenario 8. The registry covers File, Edit, View, Signing,
Settings, and Help. `FoliaSealAppFrame` turns those definitions into Qt actions, while public
workspace/session ports and focused editor boundaries own behavior and capability state. Native
editors retain local text history; viewer and placement focus route Undo/Redo through placement
history; document Select All, Pan, navigation, zoom, search, review, signing, settings, and Help
route through their owning typed seams. The remaining project work is release/display acceptance,
not additional command-model behavior.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current implementation and write failing focused tests for the File command foundation.
- [x] (2026-08-09) Implement the typed File command registry and lifecycle application/Qt path.
- [x] (2026-08-09) Review migrated compatibility and acceptance product cruft; no retirement condition in the command-model seams was met, so no unrelated removal was mixed into this slice.
- [x] (2026-08-09) Run focused, regression, and real-Qt validation; record evidence and clean up.
- [x] (2026-08-09) Historical broad completion gate superseded by dependency-ordered command slices;
  each completed increment now reconciles its owning architecture/status records and commit evidence.
- [x] (2026-08-09) Historical Loop 5 increment: add typed View Previous Page and Next Page
  commands through the public session port; Fit/zoom/search/history were deferred at that time and
  were completed by later owning slices.
- [x] (2026-08-09) Loop 5 compliance fixes: synchronize boundary capability after viewer-owned
  navigation, use explicit registry lookup, and prove Page Up/Page Down single-dispatch behavior.
- [x] (2026-08-09) Removed the unused per-menu definition lookup helpers after confirming there
  were no remaining repository callers; `command_definition()` is now the sole frame lookup.
- [x] (2026-08-09) Historical Loop 5 architecture/status documentation update; the child remained
  open then for menus and signed-state policy that later increments completed.
- [x] (2026-08-09) Historical Loop 8 increment: migrated existing Settings actions to the shared
  typed registry with unique mnemonics, stable IDs/object names, Qt descriptions, and callback
  routing. Edit, Signing, and remaining View commands were deferred at that time and were completed
  by later truthful seams.
- [x] (2026-08-09) Loop 8 focused validation passed (`44 passed`), full validation passed
  (`1185 passed, 20 skipped, 1 warning`), and the bounded launch audit cleaned its isolated root
  with no lingering FoliaSeal/PySide6 process; the launch remains limited by the local
  `SingleInstanceUnavailable` endpoint error.
- [x] (2026-08-09) Historical architecture and parent-plan status reconciliation; the bounded
  Settings outcome was ready for commit while the broader child remained open at that time.
- [x] (2026-08-09) Re-audited the remaining raw actions against UI_SPEC: Select Text is currently
  under Edit but belongs under View, and Copy is currently raw but belongs under Edit.
- [x] (2026-08-09) Add red registry/menu-topology tests for typed Select Text and Copy.
- [x] (2026-08-09) Implement the two typed definitions and preserve existing enablement/check state
  and public maintenance-port callback routing; Copy is selection-sensitive and owns Ctrl+C.
- [x] (2026-08-09) Focused validation passed (`165 passed`), full validation passed (`1193 passed,
  20 skipped, 1 warning`), Ruff and diff checks passed, and the real-Qt no-document menu test
  passed; the bounded launch remains limited by the known local QLocalServer endpoint error.
- [x] (2026-08-09) Historical guardrail: kept commands without truthful seams out while View was
  incrementally migrated; later slices added every required command with a truthful boundary.
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
- [x] (2026-08-10) Historical initial Signing increment: add Signature Library and Sign and save;
  placement commands were deferred until their public seam and were completed by the next slice.
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
- [x] (2026-08-10) Historical reconciliation of architecture/status documentation for the public Undo/Redo boundary,
  focus-sensitive native text routing, and placement-history semantics. Full validation is `1443
  passed, 20 skipped, 1 warning`; the bounded GUI audit exits at `SingleInstanceUnavailable`, with
  no matching processes or temporary audit root remaining. Commit and remaining command-family
  status were then the parent handoff gates; the command-model closeout has since completed them.
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
  implementation and its fake/real Qt evidence; unrelated release gates remain with the parent.
- [x] (2026-08-15) Implemented the typed View → Pan command over the existing public
  `set_viewer_interaction_mode("pan")` seam. The frame owns registry metadata and open-workspace
  enablement; the runtime clears text-selection mode and preserves placement state. Focused red→green
  tests prove one exact `"pan"` transition, and the production offscreen AppFrame test proves text-mode
  exit and unchanged placement through the published workspace ports.
- [x] (2026-08-16) Audited the live registry, AppFrame wiring, public session/runtime seams, focused
  tests, and architecture records. All UI_SPEC command families are implemented; no additional
  command behavior is selected. The remaining work was stale status wording and parent/architecture
  reconciliation.
- [x] (2026-08-16) Reconciled this child’s purpose, outcomes, validation, and historical deferred
  wording; recorded current focused/full evidence and the display-backed acceptance limitation.

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
- Observation (pre-implementation, 2026-08-10): UI_SPEC §7/§8 listed View → Pan, but the typed
  registry and frame exposed every neighboring View command except Pan; the public session port and
  runtime already implemented the mode transition.
  Evidence: explorer audit of `docs/UI_SPEC.md`, `app_frame_command_model.py`, and
  `set_viewer_interaction_mode()`.
- Observation: the existing viewer already owns Pan/Place interaction state, so the missing command
  is an AppFrame registry/action gap rather than a new viewer behavior. Routing it through the
  session port also lets the runtime clear text-selection mode without duplicating mode state in the
  frame.
  Evidence: `SigningWorkspaceSessionPort.set_viewer_interaction_mode()`,
  `SigningWorkspaceRuntime.set_viewer_interaction_mode()`, and the real viewer interaction-mode
  tests reviewed for this slice.
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
  `_focused_text_editor()` already identifies the only widgets that may own native editing operations.
  Evidence: the current frame routes those actions through Qt editor methods, while the no-editor
  Select All path now delegates to the completed public document-selection contract. This child
  preserves native-editor precedence and does not duplicate viewer selection policy.

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
- Decision: add View → Pan as a typed, no-shortcut command immediately before Select Text, route it
  through `SigningWorkspaceSessionPort.set_viewer_interaction_mode("pan")`, and enable it only when
  a workspace is open. Do not make it checkable or maintain a second frame-side interaction-mode
  value.
  Rationale: UI_SPEC requires Pan, the public runtime seam already owns the transition and text-mode
  exit, and the frame has no truthful current-mode query. A non-checkable action avoids stale state
  while preserving completed placement geometry across mode changes.
  Date/Author: 2026-08-10 / Codex
- Decision: close this child as a complete command-model plan after reconciling all later command
  increments into one current registry description; do not add a new behavior slice here.
  Rationale: every UI_SPEC §7 command family now has a live definition and owning behavior seam, so
  further implementation would duplicate existing code. Display-backed and release acceptance are
  parent-owned gates.
  Date/Author: 2026-08-16 / Codex

## Outcomes & Retrospective

The typed command model is complete. `ALL_COMMAND_DEFINITIONS` contains the full File/Edit/View/
Signing/Settings/Help families, and AppFrame routes each action through an existing public behavior
seam or the focused native-editor contract. Focused tests cover registry metadata, menu topology,
shortcuts, enablement, callback routing, placement history, document selection, Help, and real
offscreen AppFrame behavior. The closeout command/AppFrame/session/launch run passed `81 tests`; the
broader prior command/runtime/offscreen evidence was `112 passed`. The latest full regression is
`1535 passed, 20 skipped, 1 warning`. The bounded `foliaseal gui` audit
still exits before frame creation when the isolated QLocalServer endpoint cannot be claimed, and a
display-backed human audit remains open in the release/evidence plans. Those are independent
environment/release gates, not missing command behavior.

## Context and Orientation

The relevant code is app_frame.py; Qt action/menu construction; signing_shell ports; command-state tests. FoliaSeal is a Python/Qt Linux PDF signing application. The
product flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. This slice must preserve the V1 anti-goals: no tabs,
printing, general PDF editing, cloud workflow, broad trust administration, or multiple pending
signatures.

The words “compatibility surface” mean an adapter kept only for old callers. “acceptance” names identify
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

For the current Pan increment, add `PAN` to `AppFrameCommandId` and insert its View definition
before Select Text with the accessible name `Pan the PDF document`, mnemonic `Pa&n` (unique within
View), and no
invented shortcut. Add the corresponding `_pan_action` field and View-menu action in
`src/foliaseal/presentation/qt/app_frame.py`, route `_pan_view()` through the public session port
with the literal mode `"pan"`, and enable it from `WorkspaceActionState.workspace_open`. Do not
touch viewer geometry or add a duplicate interaction-mode model at the frame edge.

## Milestones

The historical milestones built the command model incrementally: File lifecycle first, then View
navigation/zoom/history, Settings, Signing and placement, focus-sensitive Edit operations, document
Select All, packaged Help, and finally View Pan. Each increment added a typed definition, a truthful
owning seam, focused tests, and real offscreen Qt coverage. Earlier milestones intentionally recorded
commands as deferred until those seams existed; those statements are historical and no longer define
the current registry.

The final milestone is this closeout. It verifies that `ALL_COMMAND_DEFINITIONS` contains every
UI_SPEC §7 command family, reconciles the child/parent/architecture records, records current focused
and full-suite evidence, and preserves explicit environment qualifiers for display-backed and
privileged release gates. It does not add a new QAction or change runtime behavior.

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
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/integration/test_gui_launch_no_document.py tests/integration/test_view_navigation_shortcuts.py -k 'pan or view_command or text_selection'
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

The implementation milestones used focused tests and offscreen Qt walkthroughs. The current
closeout records those results and preserves the separate display-backed HITL requirement; it must
not turn an offscreen run into a claim about human visual acceptance. Record the exact test commands,
counts, environment limitation, and cleanup result.

## Validation and Acceptance

Acceptance is now the complete command surface: every command required by UI_SPEC §7 appears in the
typed registry, is mounted in its normative menu, and has a truthful callback/capability boundary.
Focused and offscreen tests prove metadata, shortcuts, routing, state changes, native-editor
precedence, placement-history behavior, document selection, signing readiness, Help, and lifecycle
clearing. The command child does not claim display-backed accessibility, two-process launch, or
privileged package installation; those remain parent/release gates.

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
With the viewer, a button, or no native editor focused, Cut/Paste remain disabled and do not mutate
placement or document-selection state; Select All delegates to the completed current-page
document-selection boundary when no native editor owns focus. The separate document-selection child
owns that viewer behavior, while this child owns native-editor precedence.

For the completed Pan behavior, a no-document frame exposes a disabled `AppFrameCommandId.PAN`
action. With an open workspace, the action calls the session port exactly once with `"pan"`; the
runtime leaves completed placement geometry unchanged and turns off document text-selection mode.
The focused and real offscreen tests prove this without requiring a display-backed GUI.

## Evidence Record

The closeout evidence is the governing UI_SPEC requirement, exact focused test command/result,
keyboard/menu input sequence and observed action state, evidence path and cleanup result, and
compatibility grep proof. Loop 2 evidence is the offscreen real-Qt integration
assertion for File labels, shortcuts, tooltip/status descriptions, mnemonic text, and no-document
enablement; Loop 5 adds `tests/integration/test_view_navigation_shortcuts.py`, whose offscreen
QTest Page Down/Page Up sequence produced exactly one page transition and one render per key. The
Loop 8 Settings focused pass is `44 passed`; the prior Select Text/Copy increment's focused pass was
`165 passed`. The Back/Forward and Signing increments record their focused results and red-to-green
registry/state tests, along with the final full-suite count, Ruff, and diff results. The closeout
command was `.venv/bin/pytest -q tests/unit/test_qt_app_frame.py
tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_signing_workspace_session_port.py
tests/integration/test_gui_launch_no_document.py` (`81 passed`), including production QAction
Undo/Redo and Place/Adjust/Remove routing. The
bounded `foliaseal gui` launch remains environment-limited because QLocalServer cannot claim its
isolated endpoint (`Unknown error 1`/`SingleInstanceUnavailable`), and the audit found no lingering
FoliaSeal/PySide6 processes after cleanup.

The contributing UI_SPEC scenarios are 3 (create/adjust/remove/undo/restore one placement) and 8
(keyboard-only signing workflow). This closeout changes no source behavior and adds no SVG or other
generated artifact; it records the existing command-model tests and preserves the separate
display-backed evidence requirement.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Native-editor evidence recorded for this increment: `QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q
tests/integration/test_gui_launch_no_document.py -k native_edit` passed (`1 passed`), the combined
app-frame/state/offscreen set passed (`65 passed`), and the full suite passed (`1449 passed, 20
skipped, 1 warning`). The real test covers Edit menu Cut/Copy/Paste/Select All, clipboard empty/nonempty
transitions, and Ctrl+A/C/X/V observable selection, clipboard, and text behavior; keyboard Select All
is validated by the resulting Qt selection rather than an overridden `selectAll()` call count.

Pan evidence for this increment records the focused AppFrame registry/action result (`2 passed`),
focused runtime transition/retention result (`2 passed`), and production offscreen AppFrame result
(`1 passed`). Together they cover the no-document disabled state, exact one-call `"pan"` transition,
text-mode exit, and unchanged placement rectangle; the cleanup audit passed. No new SVG is needed;
the existing View topology artifact remains the governing visual reference.

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
tests/unit/test_signing_workspace_session_port.py. `QtSigningWorkspaceSessionPort` exposes
`can_undo_placement()`, `can_redo_placement()`, `undo_placement()`, and `redo_placement()`;
`SigningWorkspaceRuntime` must provide the corresponding typed methods and leave placement
application/history ownership in the viewer boundary.
The native-edit increment keeps Cut/Copy/Paste/Select All at the `FoliaSealAppFrame` edge for native
editors: the frame queries `_focused_text_editor()`, subscribes to native selection/clipboard changes,
and calls only the focused editor's native methods. The no-editor Select All path is now delegated to
the separate typed document-text-selection contract owned by the document-selection child.
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
Revision note: 2026-08-10 / Codex
Selected the next dependency-ready command increment: typed View → Pan over the existing public
viewer-interaction mode boundary. The frame owns only registry metadata/action enablement; runtime
owns mode transitions and text-mode clearing, and no shortcut or duplicate mode state is introduced.
