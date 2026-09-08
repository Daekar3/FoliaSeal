# Unify placement mode, keyboard focus, and drag cancellation


This is a living ExecPlan maintained under /home/daekar/.codex/skills/write-execplan/PLANS.md. Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective during execution.

## Purpose / Big Picture


A user choosing Signing → Adjust Placement must immediately be able to move or resize the completed rectangle with the keyboard. Escape during a drag must discard its preview; Escape when idle must enter Pan with the rectangle preserved and handles absent.

## Child ExecPlan Dependencies


This is the first child of gui_placement_gate10_recovery_parent_execplan.md in docs/ExecPlans/. It has no implementation prerequisite. Complete it before the history child edits the same files.

Current authoritative evidence (2026-09-08): the source and installed acceptance record is 199
focused tests, 1660 full-suite tests with 20 skipped and one existing warning, and package
`f800e6c...` from commit `8903512c9` passing Cinnamon/X11 mode, cancellation, keyboard adjustment,
history, and responsiveness checks. The earlier 276-test count below is superseded.

## Progress


- [x] (2026-09-07) Recorded user failures and inspected relevant source paths; authored plan.
- [x] (2026-09-07) Incorporated three-agent review corrections and strengthened composed-event, history and package acceptance coverage.
- [x] (2026-09-07) Reproduced the source-level failure shape: explicit mode selection did not focus the canvas, composition kept a duplicate mode value, and new drags did not acquire a mouse grab for held Escape cancellation.
- [x] (2026-09-07) Added explicit viewer focus, authoritative mode projection, mode-dependent handle rendering, and mouse-grab cleanup for canceled new drags.
- [x] (2026-09-07, superseded historical count) Added focused unit and composed offscreen Qt regressions; the then-current shared placement-focused suite passed 276 tests, including all 6 Gate 10 integration tests. The authoritative current focused count is 199.
- [x] (2026-09-07) Removed the composition keyboard-callback compatibility rebuild and made the viewer mode transition a required typed interface; shell/runtime fakes now implement the complete callback and placement-history surface.
- [x] (2026-09-08) Dependent installed Cinnamon/X11 acceptance passed for package `f800e6c...` from commit `8903512c9`; mode, cancellation, keyboard adjustment, history, and responsiveness checks are recorded by the acceptance child.

## Surprises & Discoveries


AppFrame._adjust_placement calls runtime.set_viewer_interaction_mode("signature"). That delegates to the viewer setter without explicitly requesting canvas focus. PdfPreviewWidget has keyPressEvent but no explicit focus policy in its constructor; the scroll wrapper only sets a focus proxy. Confirm actual focus with a composed Qt regression before labeling it the sole cause.

The canvas constructor defaults to signature, but composition explicitly sets the viewer to Pan during construction. This is not evidence of a startup mismatch. Later menu paths change the runtime/viewer directly while composition maintains a separate dictionary used for label/button state. Escape changes the inner viewer to Pan and emits placement_mode_cancelled, which runtime.on_viewer_interaction forwards as status. _draw_overlay draws corner handles unconditionally, although handle hit-testing is already guarded by signature mode. Thus visible handles alone cannot establish the active interaction mode.

Escape already resets _overlay_drag_handle or _drag_origin when its handler receives the event. Investigate event delivery and release-after-cancel before replacing that logic.

## Decision Log


Decision (2026-09-07): Accept source-supported review findings while rejecting overstated startup and replay claims. Rationale: composition initializes Pan, and synchronization to an identical replay target does not itself clear history. Author: Codex.

Decision (2026-09-07): Repair the existing placement contract without redesigning the signing workflow. Rationale: reported failures contradict docs/UI_SPEC.md and require focused corrections. Author: Codex.

Decision (2026-09-07): Separate behavior repair from package evidence and human acceptance. Rationale: prior isolated tests did not predict installed behavior, so completion needs composed events and rendered evidence.

Decision (2026-09-07): Treat Gate 10 viewer callbacks and mode transitions as required production interfaces. Rationale: the prior TypeError retry could silently discard keyboard callbacks, and optional getattr fallbacks could turn missing placement history into a false no-op. Fakes and builders were migrated to the current contract instead of preserving those compatibility paths.

## Outcomes & Retrospective


The source and offscreen composed regressions now cover explicit canvas focus, mode projection, handle visibility, and held-drag cancellation. The authoritative full repository suite passes 1660 tests with 20 skips and one existing warning. Installed Cinnamon/X11 acceptance passed for package `f800e6c...`; placement history remains documented by the dependent history child.

Governing-document review (2026-09-07): `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/UI_SPEC.md`
remain consistent with the implemented mode, focus, and cancellation contract; no governing-document
change is required.

The strict-interface remediation remains covered by the focused runtime/composition/viewer/AppFrame/session and signing-shell suites; the authoritative focused count is 199, the full suite is 1660 passed with 20 skips and one existing warning, and Ruff plus `git diff --check` pass. The installed Cinnamon/X11 retest passed in the dependent acceptance child.

Three-agent review corrections are incorporated. Keyboard commit-after-projection and pointer recording defects remain owned by the dependent history child; this child now owns focus delivery, authoritative mode projection, handle rendering, and cancellation lifecycle.

## Context and Orientation


Relevant files are src/foliaseal/presentation/qt/viewer_widget.py (PdfPreviewWidget keyPressEvent, mouse handlers, set_interaction_mode, _draw_overlay and ScrollablePdfViewer), signing_workspace_runtime.py (set_viewer_interaction_mode and on_viewer_interaction), signing_workspace_composition.py (selected_viewer_mode and sync_document_text_controls), and app_frame.py (_adjust_placement/_place_signature), all under that Qt directory. Tests live in tests/unit/test_qt_viewer_widget.py, test_qt_signing_workspace_runtime.py and test_qt_app_frame.py; add tests/integration/test_placement_gate10.py for production composition. A preview is uncommitted pointer geometry; accepting mouse release changes the draft.

## Change Slice


Behavior change only, with focused tests and necessary plan updates. Do not modify signing, certificate persistence, unrelated layout or generated packages in this child.

## Plan of Work


Milestone 1 adds a real Qt event regression: focus a rail text field, activate the real Adjust Placement action, and send arrows to the focused widget without directly calling keyPressEvent. Inspect QApplication.focusWidget and assert draft geometry changes. Implement explicit canvas keyboard focus policy and a command focus handoff, avoiding automatic focus theft during passive refresh.

Milestone 2 makes runtime mode state authoritative, exposed through a getter and used by composition to paint the mode label and checked tools. Route toolbar, menu and viewer Escape through one transition, including text-selection cleanup. Initialize Pan consistently. Remove the independent composition dictionary once callers migrate; do not retain a compatibility fallback. Make overlay handles and hit-testing conditional on Place and schedule repaint on mode changes.

Inventory all mode callers before removal, including signing_shell.py, signing_shell_port.py and their test doubles in the Qt package. Add a mode-change notification that refreshes the composition projection after runtime state changes; a getter alone cannot refresh the label. Update public ports only if that getter crosses their boundary. Preserve the existing signature-only hit-testing guard and test it rather than assuming it is missing.

Milestone 3 tests mouse press/move, Escape while the button remains held, then release for both new rectangles and existing-handle edits. Restore the original rectangle, remove transient guides/drag state, and prevent the later release from submitting canceled work. Idle Escape enters Pan preserving completed geometry; subsequent pointer drag pans instead of editing. Preserve editable placement on returning to Adjust.

Assert QApplication.focusWidget immediately before Escape and inspect mouse-grab ownership before cancellation, immediately afterward, and after release. Verify every acquired grab is released and the canceled release sends no placement callback. If focus correction does not deliver Escape, reproduce the remaining routing failure before adding a narrowly scoped event filter; do not install a global workaround speculatively.

## Concrete Steps


From /home/daekar/FoliaSeal:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_app_frame.py tests/integration/test_placement_gate10.py
    git diff --check

Create the named integration file before running this command. New focus and mode tests must fail on the original implementation and pass after repair. Use Qt event delivery, not direct handler calls, for the regressions.

Build its fixture through the production AppFrame/workspace construction using a disposable PDF and temporary configuration. Retain the real viewer, runtime, properties panel and SigningWorkspaceInteractionBridge; stub only unrelated external services. Invoke real actions and send Qt events to the focused widget. Assert Pan at startup, Place after menu/toolbar activation, Pan after Escape, and Text after text-selection activation. In Pan and Text the rectangle remains visible without handles; in Place handles are visible. Offscreen mouse-grab limitations must be reported and covered on X11, not counted as a passing held-drag test.

## Validation and Acceptance


Verify Enter creates/accepts; arrows move 1 point, Shift arrows 10; Ctrl arrows resize 1, Ctrl+Shift arrows 10. Focus in a text editor continues to edit text until Adjust explicitly focuses the page. Tab/Shift+Tab remain usable. Canceling a drag does not change geometry or create history. Pan label, checked tools, cursor, handle rendering and actual pointer behavior agree after every entry path and after repeated refresh. Fixed existing signature fields remain non-resizable. Real X11 rendered confirmation belongs to the acceptance child.

## Idempotence and Recovery


Inspect git status before edits and preserve unrelated changes. Use disposable fixtures and isolated configuration. Record owned process IDs and temporary paths; close owned dialogs and stop owned audit processes on success or failure. Do not terminate the user's existing session or delete user PDFs, profiles or certificates. Repeated tests should begin with fresh fixture state. If desktop access is unavailable, finish all independent checks and record the exact missing access; leave the live gate open.

## Artifacts and Notes


The source findings above were obtained by read-only inspection on 2026-09-07. Store new concise test evidence and exact reproduction steps here during execution. Keep the parent and owning child synchronized when a failure is discovered. Avoid historical test counts as claims about the current build.

## Interfaces and Dependencies


Preserve runtime.set_viewer_interaction_mode(mode: str) -> str. Add a runtime viewer_interaction_mode() -> str accessor and a narrow canvas focus operation on the viewer wrapper if needed; do not expose private preview fields to AppFrame. Keep the on_interaction string callback but handle placement_mode_cancelled centrally. Use existing PySide6; no new GUI dependency.

Revision note (2026-09-07): Created from installed Gate 2 item 10 failures and current source inspection to prevent passing low-level tests from substituting for usable placement behavior.

Revision note (2026-09-07, review wave): Incorporated validated explorer observations, strengthened production callback and rendered acceptance requirements, and rejected unsupported startup/replay conclusions. The integration test remains an intentionally new artifact.
