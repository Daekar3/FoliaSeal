# Desktop command model and shortcuts

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, the two already-supported text commands use the same typed command registry as
File, View, and Settings: View contains a checkable Select Text action, and Edit contains Copy. The
commands retain their existing public workspace callbacks and state synchronization, so keyboard
and menu users see the correct topology without inventing unsupported editing features. This is a
bounded increment toward UI_SPEC section 7 and acceptance scenarios 1 and 8; the broader command
corpus remains open for its owning viewer, signing, and support plans.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are the frozen governing contracts.
- [x] docs/ExecPlans/ui_launch_no_document_execplan.md

## Progress

- [x] (2026-08-09) Audit the current implementation and write failing focused tests for the File command foundation.
- [x] (2026-08-09) Implement the typed File command registry and lifecycle application/Qt path.
- [x] (2026-08-09) Review migrated compatibility and phase3 product cruft; no retirement condition in the command-model seams was met, so no unrelated removal was mixed into this slice.
- [x] (2026-08-09) Run focused, regression, and real-Qt validation; record evidence and clean up.
- [ ] (2026-08-09) Update relevant architecture/status documentation, complete the remaining command menus, then commit the whole child outcome.
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
  coverage. Edit, Signing, Help, and the remaining View commands remain deferred until truthful
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
- [ ] (2026-08-09) Commit the remaining command-model child outcome after the owning View zoom,
  search, and fit increments are reconciled; keep unsupported Undo/Redo/Cut/Paste/Help/Signing/
  Back/Forward commands out until truthful seams exist.
- [x] (2026-08-10) Added the typed View zoom command child: Zoom In/Out use `Ctrl++`/`Ctrl+-`,
  Reset Zoom is a real menu action without a conflicting shortcut, and all three route through the
  public session port while reusing the existing clamped viewer zoom policy.

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
- Decision: register only Select Text and Copy in this increment, moving Select Text to View and
  keeping Copy in Edit; do not add unsupported editing or signing placeholders.
  Rationale: both actions already have real maintenance-port behavior and state projection, while
  Undo/Redo/Cut/Paste/Select All, Help, Signing, and advanced View commands lack complete truthful
  seams. A typed correction improves UI_SPEC compliance without overstating capability.
  Date/Author: 2026-08-09 / Codex

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
UI_SPEC command registry and its parent scenario evidence: focus-sensitive Edit actions,
Signing-menu topology, Help content/actions, and Fit/zoom/search/signature/history commands remain
deferred to their owning viewer/document/support children.

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

Extend the existing typed registry rather than introducing parallel raw `_action()` definitions. Add
`VIEW_SELECT_TEXT` and `EDIT_COPY` definitions with stable IDs, truthful Qt descriptions, and
unique menu mnemonics. In `FoliaSealAppFrame._install_menus()`, route Select Text through the
existing `_toggle_text_selection_mode_from_action()` callback under View and Copy through
`_copy_selected_text_from_action()` under Edit. Keep action enablement/check state projected by
`WorkspaceActionState` and preserve the public maintenance port. Do not add commands whose behavior
is not implemented.

## Milestones

Milestone 1 inventories frame actions and writes red command-state tests. Milestone 2 centralizes
Select Text and Copy metadata and menu routing through the frame boundary. Milestone 3 verifies
menu/enablement parity in focused and real-Qt tests and records the remaining unsupported command
families as deferred. The parent command-model acceptance remains open until all named menus have
their owning slices and scenario evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e '_install_menus|_command_action|text_selection|copy_selected|VIEW_COMMAND_DEFINITIONS|EDIT_COMMAND_DEFINITIONS' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_command_model.py
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_app_frame_workspace_action_state.py tests/integration/test_gui_launch_no_document.py
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

Acceptance for this increment is behavioral: View Select Text and Edit Copy are defined by the one
typed registry, appear in the normative menus, retain correct document-dependent enablement/check
state, and reach their existing public maintenance-port callbacks exactly once. File, View
Previous/Next Page, and the five Settings actions remain green under their prior contracts. First
Save must choose a path before submitting. The full child acceptance remains open for focus-sensitive
Edit, Signing, Help,
remaining View, signed-state policy, and parent scenario requirements. The focused regression suite
passed (`165 passed`), shared-code changes keep the full suite green (`1193 passed, 20 skipped,
1 warning`), and real-Qt no-document evidence records the visible command state and cleanup. A
display-backed audit remains environment-limited by the known xcb/QLocalServer failures.

## Evidence Record

Before checking this child in the parent, record the governing UI_SPEC requirement, exact focused
test command/result, keyboard/menu input sequence and observed File action state, evidence path and
cleanup result, and compatibility grep proof. Loop 2 evidence is the offscreen real-Qt integration
assertion for File labels, shortcuts, tooltip/status descriptions, mnemonic text, and no-document
enablement; Loop 5 adds `tests/integration/test_view_navigation_shortcuts.py`, whose offscreen
QTest Page Down/Page Up sequence produced exactly one page transition and one render per key. The
Loop 8 Settings focused pass is `44 passed`; this increment's focused pass is `165 passed` and the
registry test was red before implementation and green afterward. The full suite is `1193 passed,
20 skipped, 1 warning`; Ruff and diff checks pass. The
bounded `foliaseal gui` launch remains environment-limited because QLocalServer cannot claim its
isolated endpoint (`Unknown error 1`/`SingleInstanceUnavailable`), and the audit found no lingering
FoliaSeal/PySide6 processes after cleanup.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

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
and the command-state assertions added for Settings.
workspace surface. Any compatibility adapter retained temporarily must have a named consumer and a
retirement condition recorded in this plan.

Revision note: 2026-08-09 / Codex
Created as child ui_command_model_shortcuts_execplan.md of the approved SPEC/UI_SPEC compliance breakdown.
Revision note: 2026-08-09 / Codex
Recorded the Loop 8 Settings-registry migration and narrowed remaining command-model work to
existing truthful Edit/Signing/Help/View seams rather than placeholder actions.
Revision note: 2026-08-09 / Codex
Selected the next bounded correction: typed View Select Text and Edit Copy registration with
existing callback/state behavior; unsupported command families remain deferred.
