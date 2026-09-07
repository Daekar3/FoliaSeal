# Restore reliable placement adjustment, cancellation, and history


This is a living ExecPlan maintained under /home/daekar/.codex/skills/write-execplan/PLANS.md. Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective during execution.

## Purpose / Big Picture


The user must be able to adjust an existing signature rectangle, cancel an unfinished drag, leave Place mode, undo and redo edits, and restore a removed placement. This family repairs installed GUI Gate 2 item 10. Gate 1 and Gate 2 items 1–9, 11 and 12 remain user-reported passes; do not require those to be repeated wholesale or claim this family is already accepted.

## Child ExecPlan Dependencies


Execute gui_placement_mode_focus_cancel_execplan.md first, gui_placement_history_recovery_execplan.md second, and gui_placement_gate10_acceptance_execplan.md last, all in docs/ExecPlans/. The history work touches the same viewer/runtime files as mode work, so execute serially. The acceptance child requires both behavior children.

## Progress


- [x] (2026-09-07) Recorded user failures and inspected relevant source paths; authored plan.
- [x] (2026-09-07) Incorporated three-agent review corrections and strengthened composed-event, history and package acceptance coverage.
- [ ] Reproduce the scoped failures and record baseline evidence.
- [ ] Complete the milestones and regression validation below.
- [ ] Reconcile dependent plans and record remaining acceptance honestly.

## Surprises & Discoveries


The September 7 user report establishes keyboard adjustment and Escape during a held-button drag as failures. Idle Escape leaves apparent placement behavior while the tip says Pan. Mouse handles and Remove Placement work, but Undo of handle edits and removal is unavailable; Redo is blocked by Undo failure. Unattempted applicable tests are Not tested, never N/A.

Source inspection confirms missing explicit focus setup, separate canvas and composition mode values, unconditional handle painting, and destructive history synchronization paths. These are evidence-backed defects or hazards, not a complete reproduced causal chain for every installed symptom. No live reproduction or installed binary identity verification was performed while writing this family.

Review refined the evidence: pointer edits use notify=False and bypass panel recording; keyboard callbacks project new geometry before the local history commit. Composition initializes Pan correctly, while later menu/Escape transitions can leave stale control projections. Synchronizing an identical Undo/Redo target does not itself clear history; trace secondary notifications for remaining losses.

## Decision Log


Decision (2026-09-07): Accept source-supported review findings while rejecting overstated startup and replay claims. Rationale: composition initializes Pan, and synchronization to an identical replay target does not itself clear history. Author: Codex.

Decision (2026-09-07): Repair the existing placement contract without redesigning the signing workflow. Rationale: reported failures contradict docs/UI_SPEC.md and require focused corrections. Author: Codex.

Decision (2026-09-07): Separate behavior repair from package evidence and human acceptance. Rationale: prior isolated tests did not predict installed behavior, so completion needs composed events and rendered evidence.

## Outcomes & Retrospective


Planning and source investigation are complete. Implementation, reproduction tests, package verification and new acceptance are pending. This document does not certify a fix.

Three-agent review corrections are incorporated. Keyboard commit-after-projection and pointer recording defects now guide regression coverage; focus delivery still needs reproduction. All implementation and installed acceptance remain pending.

## Context and Orientation


The viewer is built by src/foliaseal/presentation/qt/viewer_widget.py, runtime callbacks by signing_workspace_runtime.py, controls by signing_workspace_composition.py, and menus by app_frame.py in the same directory. src/foliaseal/application/placement_history.py stores prior SignatureRect values (page index and PDF-point geometry), including None for removal. Governing authority is docs/SPEC.md, docs/SCHEMAS.md, then docs/UI_SPEC.md for interaction realization. UI_SPEC requires Pan by default, visible completed rectangles in all modes, handles only in Place, cancelable drag previews, exact keyboard movement and undoable changes.

## Change Slice


Documentation/status update is the present slice. Future behavior commits belong to the first two children; generated package/evidence updates belong to the third. Temporary logs, screenshots, PDFs and packages may be generated under /tmp; never commit certificates, user documents, package binaries, or bulk generated reports.

## Plan of Work


Milestone 1 completes mode/focus/cancellation through the first child and proves actual Qt event delivery. Milestone 2 completes the second child and proves one history step per accepted edit through the full runtime callbacks. Milestone 3 executes the acceptance child against a fresh package on Cinnamon/X11, records rendered and behavioral evidence, and obtains the bounded human retest. Carry unresolved failures into the owning child and continue repair; a test-suite pass is not final GUI acceptance.

## Concrete Steps


Run the focused commands in both behavior children, then the acceptance child. From /home/daekar/FoliaSeal run:

    git status --short
    .venv/bin/pytest -q
    git diff --check

Expect tests to pass without new failures; record actual counts rather than copying historical counts.

## Validation and Acceptance


The whole family is complete only when real menu activation, keyboard move/resize, held-button Escape, idle Escape to Pan, pointer edit Undo/Redo, and Remove/Undo succeed in the composed application and the installed retest has an explicit result. Retain user-reported signing passes and record any new signing regression separately.

Also require creation Undo/Redo, Delete and menu removal separately, native-text versus canvas Undo routing, Pan/Place/Text handle visibility, released mouse grabs after cancellation, no delayed commit on release, and unchanged refreshes preserving history. Verify installed payload bytes and running-process identity before HITL. Preserve same-page performance through callback counts and bounded live observation. The children contain the concrete procedures; the older stability plan is historical evidence for this gate.

## Idempotence and Recovery


Inspect git status before edits and preserve unrelated changes. Use disposable fixtures and isolated configuration. Record owned process IDs and temporary paths; close owned dialogs and stop owned audit processes on success or failure. Do not terminate the user's existing session or delete user PDFs, profiles or certificates. Repeated tests should begin with fresh fixture state. If desktop access is unavailable, finish all independent checks and record the exact missing access; leave the live gate open.

## Artifacts and Notes


The source findings above were obtained by read-only inspection on 2026-09-07. Store new concise test evidence and exact reproduction steps here during execution. Keep the parent and owning child synchronized when a failure is discovered. Avoid historical test counts as claims about the current build.

## Interfaces and Dependencies


Use existing Qt and placement contracts. No persistence migration, dependency upgrade, timestamp/signing redesign, or GUI topology change is authorized by this family.

Revision note (2026-09-07): Created from installed Gate 2 item 10 failures and current source inspection to prevent passing low-level tests from substituting for usable placement behavior.

Revision note (2026-09-07, review wave): Incorporated validated explorer observations, strengthened production callback and rendered acceptance requirements, and rejected unsupported startup/replay conclusions. The integration test remains an intentionally new artifact.
