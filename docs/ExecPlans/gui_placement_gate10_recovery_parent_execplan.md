# Restore reliable placement adjustment, cancellation, and history


This is a living ExecPlan maintained under /home/daekar/.codex/skills/write-execplan/PLANS.md. Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective during execution.

## Purpose / Big Picture


The user must be able to adjust an existing signature rectangle, cancel an unfinished drag, leave Place mode, undo and redo edits, and restore a removed placement. This family repairs installed GUI Gate 2 item 10. Gate 1 and Gate 2 items 1–9, 11 and 12 remain user-reported passes; do not require those to be repeated wholesale or claim this family is already accepted.

## Child ExecPlan Dependencies


Execute gui_placement_mode_focus_cancel_execplan.md first, gui_placement_history_recovery_execplan.md second, gui_placement_keyboard_repeat_performance_execplan.md third, and gui_placement_gate10_acceptance_execplan.md last, all in docs/ExecPlans/. The history and autorepeat work touch the same viewer/runtime files as mode work, so execute serially. The acceptance child requires all three behavior children.

## Progress


- [x] (2026-09-07) Recorded user failures and inspected relevant source paths; authored plan.
- [x] (2026-09-07) Incorporated three-agent review corrections and strengthened composed-event, history and package acceptance coverage.
- [x] (2026-09-07) Reproduced the scoped history-loss callback ordering and completed the history child implementation.
- [x] (2026-09-07) Completed mode/focus/cancellation implementation and composed Qt regressions; the authoritative Gate 10 focused suite passes 199 tests.
- [x] (2026-09-07) Completed strict Gate 10 interface cleanup: composition preserves all keyboard callbacks, viewer mode transitions are required, and runtime/shell placement history no longer degrades to optional no-ops. Focused suites pass 147 and 113 tests respectively.
- [x] (2026-09-07) Completed AppFrame history contract cleanup: Edit action enablement now calls the required session capability methods directly; focused app-frame and dependent integration tests pass 86 tests.
- [x] (2026-09-07) Added the keyboard autorepeat performance child after installed acceptance exposed significant CPU spin-up while holding adjustment keys during resize; package acceptance now requires its callback counters, lifecycle tests, and fresh installed observation.
- [x] (2026-09-07) Implemented held-key preview coalescing: arrow and resize repeats update only the draft/overlay, physical release performs one runtime reconciliation and one history commit, and synthetic releases are ignored. Focused source and real Qt autorepeat tests pass; fresh package/install and the user-reported sustained-resource observation remain with acceptance.
- [x] (2026-09-07) Completed autorepeat compliance remediation: typed adjustment-session results now distinguish accepted/no-op/flush/cancel/close/ignored release, Escape restores the batch start without history, physical key/modifier boundaries flush before a new sequence, callback failures restore model state, Ctrl/Ctrl+Shift resize and mounted composition counters have real-Qt coverage, and signing/removal/direct viewer navigation invoke the public flush boundary. Targeted validation is 199 passed, including a configured disposable PKCS#12 counter path; fresh package/install remains with acceptance.
- [ ] Complete the installed acceptance milestone. The user installed the exact package and installed-byte identity now matches the fresh payload. A bounded display-backed launch rendered a disposable PDF and placement overlay with no short-interval CPU spike; human Adjust, cancellation, mode, and history acceptance remains open.
- [x] (2026-09-07) Reconciled the behavior children and older stability plan; authoritative validation is 199 focused tests and 1660 full-suite tests with 20 skips and one existing warning. Only fresh package rebuild/install and rendered Cinnamon/X11 human acceptance remain open.

## Surprises & Discoveries


The September 7 user report establishes keyboard adjustment and Escape during a held-button drag as failures. Idle Escape leaves apparent placement behavior while the tip says Pan. Mouse handles and Remove Placement work, but Undo of handle edits and removal is unavailable; Redo is blocked by Undo failure. Unattempted applicable tests are Not tested, never N/A.

Initial source inspection identified missing explicit focus setup, separate canvas and composition mode values, unconditional handle painting, and destructive history synchronization paths. Those implementation findings are now addressed and covered by composed tests; fresh installed binary identity and rendered human acceptance remain external requirements.

Review refined the evidence: pointer edits use notify=False and bypass panel recording; keyboard callbacks project new geometry before the local history commit. Composition initializes Pan correctly, while later menu/Escape transitions can leave stale control projections. Synchronizing an identical Undo/Redo target does not itself clear history; trace secondary notifications for remaining losses.

History child implementation evidence (2026-09-07): viewer projection no longer clears history, pointer and removal operations commit exactly once, keyboard replay remains projection-only, unchanged panel refreshes preserve both stacks, and the shell forwards placement history capabilities to AppFrame. Focused real-Qt coverage includes existing-handle cancellation, Pan cancellation, AppFrame pointer edit Undo/Redo, menu removal Undo/Redo, Delete Undo, lifecycle reset and same-page render counters. Installed acceptance remains open.

Strict-interface remediation evidence (2026-09-07): the composition now invokes the current viewer builder contract once, without a TypeError retry that strips keyboard callbacks. Runtime and shell-port Gate 10 history methods call required typed methods directly. Fakes were migrated to implement those callbacks and history operations. Ruff and `git diff --check` pass; installed acceptance remains open.

AppFrame contract evidence (2026-09-07): `_sync_edit_history_actions` now invokes the typed session `can_undo_placement()` and `can_redo_placement()` methods directly whenever a workspace is active. The final optional-method fallback was removed so a missing history implementation cannot silently disable Gate 10. The app-frame and dependent integration tests pass 86 tests; installed acceptance remains open.

Keyboard autorepeat finding (2026-09-07): individual Arrow adjustment passed the installed retest, but holding adjustment keys during resize caused significant CPU activity. Read-only tracing identifies `apply_signature_rect_placement`, properties-panel `load_from_workflow`, setup/coordinator refresh, signing readiness, and possibly PKCS#12 readiness parsing as repeated-work candidates. The autorepeat child owns measurement and repair; no performance claim is made until its counters and installed observation pass.

Governing-document review (2026-09-07): `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/UI_SPEC.md` were reviewed against the implementation and this family. No governing-document change is required: the repaired source follows the existing Pan/Place/Text, keyboard-focus, cancelable-drag, visible-overlay, and undoable-placement contract. The remaining discrepancy is evidence status for the installed GUI, which stays in the acceptance child.

## Decision Log


Decision (2026-09-07): Accept source-supported review findings while rejecting overstated startup and replay claims. Rationale: composition initializes Pan, and synchronization to an identical replay target does not itself clear history. Author: Codex.

Decision (2026-09-07): Repair the existing placement contract without redesigning the signing workflow. Rationale: reported failures contradict docs/UI_SPEC.md and require focused corrections. Author: Codex.

Decision (2026-09-07): Separate behavior repair from package evidence and human acceptance. Rationale: prior isolated tests did not predict installed behavior, so completion needs composed events and rendered evidence.

Decision (2026-09-07): Remove compatibility fallbacks that can turn Gate 10 defects into silent no-ops. Rationale: the production viewer and shell already implement the current contract; preserving absent-method retries hid missing callbacks and history. Test doubles now implement the same interface.

Decision (2026-09-07): Enforce the required session history capability at the AppFrame boundary. Rationale: action enablement must surface an incomplete workspace contract instead of converting it into disabled Undo/Redo actions. Author: Codex.

## Outcomes & Retrospective


Mode/focus/cancellation, placement history, and keyboard autorepeat implementation plus composed regressions are complete in the current source tree. Authoritative validation passes 199 focused tests and 1660 full-suite tests with 20 skips and one existing warning. The configured disposable PKCS#12 coverage proves readiness reads are deferred during repeats and bounded at flush. Only a fresh package rebuild/install and rendered Cinnamon/X11 human acceptance remain before Gate 2 item 10 can close.

Three-agent review corrections are incorporated. Keyboard commit-after-projection, pointer recording, explicit focus, authoritative mode projection, cancellation, AppFrame forwarding and same-page render preservation now have composed coverage. The acceptance child remains the sole owner of fresh package identity and rendered Cinnamon/X11 retest.

## Context and Orientation


The viewer is built by src/foliaseal/presentation/qt/viewer_widget.py, runtime callbacks by signing_workspace_runtime.py, controls by signing_workspace_composition.py, and menus by app_frame.py in the same directory. src/foliaseal/application/placement_history.py stores prior SignatureRect values (page index and PDF-point geometry), including None for removal. Governing authority is docs/SPEC.md, docs/SCHEMAS.md, then docs/UI_SPEC.md for interaction realization. UI_SPEC requires Pan by default, visible completed rectangles in all modes, handles only in Place, cancelable drag previews, exact keyboard movement and undoable changes.

## Change Slice


Behavior work is complete for both implementation children; generated package/evidence updates and bounded human retest remain with the acceptance child. Temporary logs, screenshots, PDFs and packages may be generated under /tmp; never commit certificates, user documents, package binaries, or bulk generated reports.

## Plan of Work


Milestone 1 completes mode/focus/cancellation through the first child and proves actual Qt event delivery. Milestone 2 completes the second child and proves one history step per accepted edit through the full runtime callbacks. Milestone 3 coalesces keyboard autorepeat work while preserving exact final geometry, lifecycle safety, readiness/certificate correctness, and one-step history. Milestone 4 executes the acceptance child against a fresh package on Cinnamon/X11, records rendered and behavioral evidence, and obtains the bounded human retest. Carry unresolved failures into the owning child and continue repair; a test-suite pass is not final GUI acceptance.

## Concrete Steps


Run the focused commands in both behavior children, then the acceptance child. From /home/daekar/FoliaSeal run:

    git status --short
    .venv/bin/pytest -q
    git diff --check

Expect tests to pass without new failures; record actual counts rather than copying historical counts.

## Validation and Acceptance


The whole family is complete only when real menu activation, keyboard move/resize, held-button Escape, idle Escape to Pan, pointer edit Undo/Redo, and Remove/Undo succeed in the composed application; repeated held-key adjustment has bounded callback work and one-step history; and the installed retest has an explicit result including the 30-second CPU/disk observation. Retain user-reported signing passes and record any new signing regression separately.

Also require creation Undo/Redo, Delete and menu removal separately, native-text versus canvas Undo routing, Pan/Place/Text handle visibility, released mouse grabs after cancellation, no delayed commit on release, unchanged refreshes preserving history, autorepeat synthetic-release handling, focus/mode/close flushes, and no lost final state. Verify installed payload bytes and running-process identity before HITL. Preserve same-page performance through callback counts and bounded live observation. The children contain the concrete procedures; the older stability plan is historical evidence for this gate.

## Idempotence and Recovery


Inspect git status before edits and preserve unrelated changes. Use disposable fixtures and isolated configuration. Record owned process IDs and temporary paths; close owned dialogs and stop owned audit processes on success or failure. Do not terminate the user's existing session or delete user PDFs, profiles or certificates. Repeated tests should begin with fresh fixture state. If desktop access is unavailable, finish all independent checks and record the exact missing access; leave the live gate open.

## Artifacts and Notes


The source findings above were obtained by read-only inspection on 2026-09-07. Store new concise test evidence and exact reproduction steps here during execution. Keep the parent and owning child synchronized when a failure is discovered. Avoid historical test counts as claims about the current build.

## Interfaces and Dependencies


Use existing Qt and placement contracts. No persistence migration, dependency upgrade, timestamp/signing redesign, or GUI topology change is authorized by this family.

Revision note (2026-09-07): Created from installed Gate 2 item 10 failures and current source inspection to prevent passing low-level tests from substituting for usable placement behavior.

Revision note (2026-09-07, review wave): Incorporated validated explorer observations, strengthened production callback and rendered acceptance requirements, and rejected unsupported startup/replay conclusions. The integration test remains an intentionally new artifact.
