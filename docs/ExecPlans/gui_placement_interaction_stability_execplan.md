# Stabilize placement adjustment, performance, and keyboard affordance

Current acceptance correction (2026-09-08): The Gate 10 recovery family repaired the earlier
installed failures. Package `f800e6c...` from commit `8903512c9` passed the installed Cinnamon/X11
HITL checks for keyboard adjustment, held-key movement/resizing, consistent exit to Pan, pointer
Undo/Redo, Undo of removal, responsiveness, and sustained CPU/disk behavior. Earlier implementation/
test evidence below remains historical; the active repair and retest owner is
[Placement Gate 10 recovery family](gui_placement_gate10_recovery_parent_execplan.md).
Signing and reopening/verification remain user-reported passes.

Status reconciliation (2026-09-07): This plan is historical for the earlier placement stability and
resource-spike work. Its remaining Gate 2 interaction implementation and retest responsibilities are
owned by the [Gate 10 recovery family](gui_placement_gate10_recovery_parent_execplan.md). The source
implementation now has focused/composed coverage, including typed keyboard autorepeat batching; the
earlier exact package/X11 launch evidence predates that final repair. The final package/install and
rendered human interaction acceptance are recorded in the Gate 10 family. Do not execute this plan as
a competing implementation loop.

Acceptance handoff (2026-09-08): The Gate 10 family recorded package `f800e6c...` from commit
`8903512c9` and the user's successful Cinnamon/X11 HITL retest. The final source has 199 focused
tests and a 1660-test full-suite result with 20 skips and one existing warning. Configured disposable
PKCS#12 counter coverage proves readiness reads are deferred during repeats and bounded at physical
release. The old plan is now historical and requires no further implementation work.

This ExecPlan is a living document and must remain self-contained under
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is Child 3 of
`docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md`.

## Purpose / Big Picture

After this slice, pointer and keyboard users can enter Place mode, create one visible placement,
adjust it from the Signing menu, move or resize it with the documented keys, cancel unfinished work,
remove/undo/restore it, and return to Pan without a crash. Pointer placement will not perform sustained
redundant work that pegs a CPU core during ordinary dragging.

This slice addresses the observed `Adjust Placement` crash, high CPU during pointer placement, and the
human inability to discover the keyboard path. It does not change placement persistence schemas,
signature rendering, or the frozen PDF-first topology.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md`, `docs/UI_SPEC.md`, and `docs/SCHEMAS.md` are available and authoritative.
- [x] `docs/ExecPlans/ui_placement_editor_transaction_execplan.md` defines reusable fixed-page profile
  semantics; this child owns the active document placement interaction only.
- [x] `docs/ExecPlans/ui_pointer_signature_placement_execplan.md` and existing viewer/history tests
  provide the placement behavior baseline.
- [x] `docs/ExecPlans/gui_hitl_defect_recovery_parent_execplan.md` records the observed crash/performance
  evidence.
- [x] Child 1 or Child 2 is not required. The Gate 10 acceptance child superseded this historical dependency.

## Progress

- [x] (2026-08-20) Confirmed `Adjust Placement` is registered as
  `AppFrameCommandId.ADJUST_PLACEMENT` and routed by `AppFrame._adjust_placement()` to
  `SigningWorkspaceRuntime.set_viewer_interaction_mode("signature")`.
- [x] (2026-08-20) Confirmed `viewer_widget.py` already contains Enter, Escape, arrow, Ctrl-arrow,
  Delete, Ctrl-Z/Ctrl-Shift-Z, and keyboard recovery hooks.
- [x] (2026-08-20) Explorer review confirmed the command-boundary tests live in
  `tests/unit/test_qt_app_frame.py`; there is no standalone `tests/unit/test_qt_signing_action_boundary.py`.
- [x] (2026-08-20) Isolate the lifecycle seam as the AppFrame-to-session viewer-mode boundary and add
  controlled handling for a known disposed viewer wrapper; live-viewer success still requires HITL.
- [x] (2026-08-20) Add command-boundary and viewer regression tests for disposed-viewer recovery and
  duplicate pointer positions.
- [x] (2026-08-20) Coalesce duplicate pointer geometry updates before scheduling repaint; preserve
  synchronous final release and one history step per drag.
- [x] (2026-08-20) Expose the existing keyboard contract in the live Place-mode guidance and retain
  the accurate Place tooltip.
- [x] (2026-08-20) Run focused validation: 224 AppFrame/shell/viewer tests passed.
- [x] Run the final full-suite/package and human acceptance checks in Child 4; final evidence is recorded in the Gate 10 acceptance child.
- [x] (2026-08-20) Reconcile parent/release documentation and commit the completed implementation slice;
  final package and human acceptance remain tracked in Child 4.
- [x] (2026-09-04, superseded historical status) Placement-only panel updates now skip canonical preview
  regeneration; the viewer-selection regression proves zero preview refreshes
  and preserves the explicit placement interaction plan. Full suite and lint
  validation pass; installed placement acceptance was pending at this historical checkpoint and is closed by the Gate 10 family.
- [x] (2026-09-04) New installed HITL evidence reproduced an immediate resource
  spike after rectangle release. Explorer review traced the remaining synchronous
  work to `SigningWorkspaceRuntime.apply_signature_rect_placement()`, which
  unconditionally reloads and rerenders the visible PDF even for same-page
  placement.
- [x] (2026-09-04) Removed the redundant same-page viewer refresh and retained
  navigation plus one widget refresh only for cross-page placement. Focused
  coverage proves same-page placement performs zero PDF refreshes while
  cross-page placement performs one; full validation reports `1617 passed, 20
  skipped, 1 warning`.
- [x] Rebuild and repeat the installed placement/edit retest; the final Gate 10 package/install/HITL result is recorded in the acceptance child.
- [x] (2026-09-04) HITL then reported sustained 1.8–1.9 MiB/s writes and high
  CPU after rectangle release followed by profile selection. No FoliaSeal PID or
  new coredump remained when inspected; the write pattern matches repeated
  canonical-preview temp-file generation.
- [x] (2026-09-04) Added a panel resize size/reentrancy guard so replacing a
  preview pixmap cannot recursively regenerate an unchanged canonical preview.
  Focused shell/runtime tests pass; a rebuilt package and live retest remain
  required.
- [x] (2026-09-04) Live observation proved the first guard was insufficient:
  PID `1281291` sustained roughly 66–69% CPU, wrote about 5.9 MiB in 3 seconds
  and about 53 MiB in 5 seconds, and created fresh canonical-preview directories.
  Resize reflow now reuses the existing canonical render state and never invokes
  PDF generation; full validation reports `1618 passed, 20 skipped, 1 warning`.
- [x] Rebuild/install this stronger correction and repeat the live placement/profile-selection gate; the final Gate 10 package/install/HITL result supersedes this historical checkpoint.
- [x] (2026-09-05) The installed package matched the resize-reflow correction but
  still regenerated the same canonical preview every ~2 seconds. Added a
  preview/layout-key cache at `_update_preview_controls()` so identical requests
  reuse the existing snapshot regardless of callback origin. Full suite remains
  green (`1618 passed, 20 skipped, 1 warning`).
- [x] Rebuild/install the render-key correction and reobserve the live workflow;
  the correction was present in the installed executable but was insufficient.
- [x] (2026-09-05) The render-key package was installed and verified, but the
  live placement/profile sequence still reached 84–86% CPU, wrote roughly
  6.5 MiB every 3 seconds, and created fresh canonical-preview directories.
  The process then self-terminated; coredump PID `1826521` is `SIGABRT` in
  QtPdf while a `QTimer::timeout` callback constructs `QPdfDocument`.
- [x] (2026-09-05) The remaining loop is outside pointer geometry itself:
  the optional 100-ms transaction poller reloads signing readiness even while
  idle; once a rectangle and Single Left appearance exist, readiness invokes
  the workflow fit validator, whose default raster path creates a fresh QtPdf
  document on each tick. The next correction must make idle polling a no-op and
  retain updates only for an active signing transaction.
- [x] (2026-09-05) The typed idle-poll guard is implemented in the working tree:
  coordinator activity is exposed through the action boundary, and idle bridge
  polls no longer reload readiness. Focused regression coverage was added for
  idle and active polling; package rebuild is complete and installed retest is
  recorded below.
- [x] (2026-09-05) Rebuilt the distributable with the timer guard (bundle SHA-256
  `1a153dd7...`; package SHA-256 `57587617...`). Installation and live placement
  acceptance completed on Cinnamon/X11: CPU stayed ~3.1–3.4%, process I/O was
  unchanged, and no new FoliaSeal coredump appeared during a 9-second
  rectangle + Single Left observation.

## Surprises & Discoveries

- Observation: the menu command and runtime mode setter are intentionally small, so the crash may be
  caused by a stale viewer/session port, a disposed widget, or an overlay state transition rather than
  by the command definition itself.
  Evidence: `AppFrame._adjust_placement()` only calls `_with_current_session_port` and
  `set_viewer_interaction_mode("signature")`; runtime then requires the active viewer widget.
- Observation: the viewer already implements the keyboard contract but does not guarantee that a first
  user will discover it from the visible shell.
  Evidence: `viewer_widget.py::keyPressEvent` handles Enter/Escape/arrows/Ctrl-arrow/Delete/Undo, while
  the human tester reported “Not sure how.”
- Observation: pointer placement sends interaction callbacks and repaints while dragging, so a 100%
  CPU observation needs a bounded measurement before selecting a timer or render optimization.
  Evidence: `viewer_widget.py` processes drag/move/snap updates and calls `update()` during placement.
- Observation: the available offscreen harness can prove the disposed-wrapper boundary and duplicate
  pointer-update suppression, but cannot certify a live mounted viewer’s successful Adjust Placement
  transition or sustained X11 CPU behavior.
  Evidence: the focused tests use the existing fake session/viewer seams; the display-backed session is
  an explicit Child 4/HITL gate.
- Observation: the first placement-stability correction suppressed the canonical
  signature preview but left a full viewer refresh in the runtime placement
  command. That refresh is unnecessary when the rectangle is drawn on the page
  already visible and is the strongest current explanation for the live spike.
  Evidence: `apply_signature_rect_placement()` calls `viewer.refresh(navigation=True)`
  unconditionally; `ViewerWorkflow.render_current_page()` performs both raster
  rendering and geometry loading, and the Qt backend creates a fresh `QPdfDocument`
  for each operation.
- Observation: after the same-page/viewer and preview-resize/cache corrections,
  the live spike persisted because the 100-ms transaction timer independently
  recalculates readiness while idle. This path is triggered only once a complete
  rectangle + horizontal image-stamp appearance makes fit validation perform a
  QtPdf raster render, which explains the user-visible timing.

## Decision Log

- Decision: capture and test the crash before altering command routing.
  Rationale: changing a thin command because it is the visible entry point could mask a lifecycle bug
  and break unrelated commands.
  Date/Author: 2026-08-20 / Codex.
- Decision: preserve the existing key contract from UI_SPEC §8: Enter creates/accepts, arrows move,
  Shift accelerates, Ctrl-arrow resizes, Delete removes, Escape cancels/returns to Pan, and Ctrl-Z/
  Ctrl-Shift-Z undo/redo.
  Rationale: the contract is already governing behavior; this slice makes it reliable and discoverable.
  Date/Author: 2026-08-20 / Codex.
- Decision: optimize only measured redundant work and never make placement asynchronous in a way that
  changes visible geometry ordering or undo semantics.
  Rationale: one drag must remain one history step, and the on-page overlay must stay aligned with the
  current draft.
  Date/Author: 2026-08-20 / Codex.
- Decision: do not hide Adjust Placement after a placement exists; make it safe and keep its enablement
  truthful.
  Rationale: the command is an explicit recovery path required by the user and UI_SPEC.
  Date/Author: 2026-08-20 / Codex.
- Decision: skip viewer reload/rasterization when applying a placement on the
  currently visible page; retain the refresh only when placement changes the
  visible page.
  Rationale: pointer release already has the rendered page and overlay update;
  same-page reload is redundant and crosses the native QtPdf load boundary that
  caused the observed resource spike. Cross-page keyboard/programmatic placement
  still needs navigation and exactly one fresh page render.
  Date/Author: 2026-09-04 / Codex.

## Outcomes & Retrospective

This historical slice established the same-page rendering and idle-poll corrections for the earlier
resource-spike investigation, with its last recorded Cinnamon/X11 observation showing bounded CPU/I/O.
The later Gate 10 recovery family owns the remaining interaction and history acceptance. Do not treat
the historical package observation or source tests here as proof of the current installed binary's
keyboard, cancellation, or Undo/Redo behavior.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame_command_model.py` defines the typed command and accessible
menu text. `src/foliaseal/presentation/qt/app_frame.py` creates the QAction and calls `_place_signature`,
`_adjust_placement`, and `_remove_placement` through the active session-port boundary.
`src/foliaseal/presentation/qt/signing_workspace_runtime.py` validates modes, selects the active viewer,
and exposes placement capability. `signing_workspace_composition.py` wires viewer mode buttons and
callbacks. `src/foliaseal/presentation/qt/viewer_widget.py` owns the actual PDF overlay, mouse drag,
keyboard events, snapping, repaints, and `PlacementHistory` commits. The application workflow receives
placement changes through the signing workspace port and must remain the source of truth.

## Plan of Work

First reproduce the crash from a real display-backed session and from an offscreen test harness. Record
the exact traceback, active document/session state, and whether the crash occurs only after pointer
placement or after any completed placement. Add a failing test that opens a fixture, creates a placement,
invokes the AppFrame command, and asserts the active viewer remains mounted in signature mode. Add a
second test for repeated Adjust/Place/Pan/Adjust and one for closing/reopening the document between
command enablement and invocation.

Repair the owner identified by the traceback. The safe boundary must treat a missing/disposed session or
viewer as a no-op with a status message, and a live viewer must enter signature mode without replacing
the draft or clearing history. The action’s enablement must continue to use `can_adjust_signature_placement`.
Avoid broad `except Exception` around the viewer; convert only known lifecycle absence into a controlled
result and let unexpected errors fail tests with a traceback.

For CPU behavior, instrument a bounded drag over the disposable fixture using a monotonic timer or
existing render counters. Determine whether repeated `refresh`, PDF rasterization, snap calculation, or
Qt repaint dominates. Coalesce only duplicate updates that cannot change the visible final rectangle;
keep final pointer release synchronous, keep one history commit per drag, and ensure Escape reverts to
the drag origin. Add a regression assertion for bounded callback/render count rather than a brittle CPU
percentage threshold, plus a documented local observation of the original and corrected behavior.

Finally, make the keyboard path discoverable. The visible mode label should state the essential keys or
point to the existing Keyboard Shortcuts/Help surface; Place and Adjust actions need accurate accessible
names and tooltips. Add offscreen focus tests proving the viewer receives Enter/arrows/Ctrl-arrow/Delete/
Escape and that the resulting state/status explains what happened.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`.

    rg -n "ADJUST_PLACEMENT|_adjust_placement|set_viewer_interaction_mode|keyPressEvent|PlacementHistory|mouseMoveEvent" src/foliaseal/presentation/qt tests/unit
    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_composition.py tests/unit/test_qt_viewer_widget.py tests/unit/test_placement_history.py
    .venv/bin/ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_command_model.py src/foliaseal/presentation/qt/signing_workspace_runtime.py src/foliaseal/presentation/qt/viewer_widget.py tests/unit

After implementation, run:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_composition.py tests/unit/test_qt_viewer_widget.py tests/unit/test_placement_history.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src
    git diff --check

Run the bounded real X11 audit with a unique title and disposable configuration. Create a placement,
choose Signing → Adjust Placement repeatedly, use keyboard movement and resizing, press Escape during a
drag, undo/redo, and remove/restore. Keep only the exact child process and audit root for cleanup.

## Validation and Acceptance

The child passes when:

- Adjust Placement never crashes after pointer placement, keyboard placement, document open/close, or
  repeated mode transitions.
- A missing active session/viewer leaves the command safely disabled or reports a recoverable status;
  it never dereferences a disposed widget.
- Pointer create/drag/resize/cancel commits one history step per drag, keeps the overlay aligned, and
  does not show sustained redundant render work in the bounded measurement.
- Enter, arrows, Shift, Ctrl-arrow, Ctrl-Shift-arrow, Delete, Escape, Ctrl-Z, and Ctrl-Shift-Z produce
  the UI_SPEC behavior and are discoverable from the visible mode guidance or Help.
- Focused tests, full suite, Ruff, compileall, and diff checks pass.

The installed/live-viewer portions were closed by the Gate 10 acceptance child on 2026-09-08; this
historical plan does not reopen them.

## Idempotence and Recovery

Use the existing fixture and isolated Qt settings roots. If a crash occurs, preserve the traceback and
close only the unique FoliaSeal process started for the audit. Do not kill Orca or unrelated desktop
windows. If a performance probe hangs, terminate it by its recorded PID and remove only its temporary
root. Keep any optimization behind a focused test so it can be reverted without touching placement
schemas or persisted user data.

## Artifacts and Notes

The commit may contain only placement command/viewer/runtime source, focused tests, this plan, and narrow
status documentation. Do not commit profiler dumps, screenshots containing PDF contents, or temporary
logs. Preserve a concise safe evidence record with the original traceback (redacted of paths if needed),
render/update counts, and keyboard state transitions.

## Interfaces and Dependencies

Use `AppFrameCommandId.ADJUST_PLACEMENT`, `SigningWorkspaceRuntime`, `SigningShellPort`,
`ViewerWidget.set_interaction_mode`, `PlacementHistory`, and the existing signing workspace callbacks.
The viewer may expose a narrow diagnostic counter or interaction result for tests, but the application
workflow remains the owner of the active `SignatureRect`. Do not bypass the session-port boundary from
AppFrame or duplicate placement state in the menu action.

## Revision Note

Revised on 2026-08-20 after the required explorer review to point at the existing AppFrame command
tests and remove the nonexistent standalone command-boundary test filename.
