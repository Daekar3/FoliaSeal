# Coalesce placement keyboard autorepeat without losing the final edit


This is a living ExecPlan maintained under `/home/daekar/.codex/skills/write-execplan/PLANS.md`. Keep `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` current.


## Purpose / Big Picture


When a user holds Arrow, Shift+Arrow, Ctrl+Arrow, or Ctrl+Shift+Arrow while adjusting a signature rectangle, the rectangle must move or resize continuously without repeated expensive signing-rail work or a sustained CPU/disk spike. The first visible response remains immediate, the physical release flushes the exact final rectangle, and the whole held sequence becomes one Undo step. The installed 2026-09-07 retest showed that individual Arrow input works but holding keys during resize causes significant CPU activity; this child owns that newly discovered failure.


## Child ExecPlan Dependencies


- [x] `gui_placement_mode_focus_cancel_execplan.md` provides focus, mode, and cancellation behavior.
- [x] `gui_placement_history_recovery_execplan.md` provides viewer-owned placement history and typed runtime/AppFrame history methods.
- [x] Complete this child before `gui_placement_gate10_acceptance_execplan.md` rebuilds and retests the installed package.


## Progress


- [x] (2026-09-07) Recorded the installed held-key CPU observation.
- [x] (2026-09-07) Recorded the source callback chain and performance hypotheses from delegated review.
- [x] (2026-09-07) Added viewer-owned held-key batching with physical-release flushing and lifecycle boundaries.
- [x] (2026-09-07) Added focused Qt autorepeat, callback-counter, geometry, and one-step history tests.
- [x] (2026-09-07) Focused validation passed: 199 tests across typed-session/viewer/runtime/Gate 10/shell suites; Ruff and `git diff --check` pass.
- [x] (2026-09-07) Compliance remediation added the typed `PlacementKeyboardAdjustmentSession`, physical key/modifier boundaries, true Escape cancellation, callback-failure restoration, Ctrl/Ctrl+Shift real-Qt resize coverage, and explicit signing/removal flush seams.
- [x] (2026-09-07) Final targeted remediation added typed synthetic-release results, flush exception recovery, explicit page-navigation flushes, and a mounted production-composition counter test proving zero panel reloads during repeats and one reload at physical release.
- [x] (2026-09-07) Final navigation/certificate review added a real Qt pending-batch navigation regression and mounted production coverage with a disposable password-protected PKCS#12. Five autorepeat Ctrl-resize events caused zero panel reloads and zero PKCS#12 readiness reads; physical release caused one panel reload and four bounded readiness reads through the current shell projection.
- [x] (2026-09-07) Full validation is authoritative at 1660 passed, 20 skipped, and one existing warning; the 199-test focused suite, Ruff, and diff checks are green.
- [x] (2026-09-08) Installed package `f800e6c...` from commit `8903512c9` passed the Cinnamon/X11 held movement, Ctrl/Ctrl+Shift resize, responsiveness, one-step Undo/Redo, and sustained CPU/disk acceptance.


## Surprises & Discoveries


- Observation: a repeated adjustment currently reaches `src/foliaseal/presentation/qt/signing_workspace_runtime.py:apply_signature_rect_placement`, and may then call properties-panel `load_from_workflow`, setup/coordinator refresh, signing-action readiness, and certificate readiness/PKCS#12 parsing.
  Evidence: source tracing and delegated explorer review; measure each seam with injected counters rather than assuming every build executes every path.
- Observation: Qt marks autorepeat key events with `QKeyEvent.isAutoRepeat()` and may emit synthetic autorepeat releases.
  Evidence: Qt event contract; synthetic releases must not terminate a held batch before the physical release.
- Observation: the existing short automated X11 run did not hold a key and therefore does not disprove the human CPU report.
  Evidence: acceptance child records only a short post-placement sample.
- Observation: the first full-suite run exposed only a stale shell test double after the typed flush callback was added; updating that fake to the current builder contract restored the shell suite without a production fallback.
  Evidence: the final full suite is 1660 passed, 20 skipped, and one existing warning; the authoritative focused family is 199/199.
- Observation: external action boundaries cannot depend on focus events alone; signing submission and removal now call the viewer's public flush seam directly before mutating or submitting the draft.
  Evidence: runtime boundary test records the flush call before removal; shell submission routes through `SigningWorkspaceRuntime.flush_pending_keyboard_placement()`.
- Observation: the viewer's own next/previous navigation path is an independent action boundary; direct viewer navigation must flush even when no runtime wrapper is involved. The mounted shell projects certificate readiness four times during one final flush today, but never during autorepeat.
  Evidence: `test_real_offscreen_navigation_flushes_pending_keyboard_batch` and the configured PKCS#12 counter assertions in `test_real_offscreen_app_frame_adjust_projects_mode_and_focus`.


## Decision Log


- Decision: update visible geometry synchronously but coalesce setup, readiness, certificate, and history work until flush. Rationale: continuous movement must feel immediate while repeated rail reconciliation is the observed cost. Date/Author: 2026-09-07 / Codex.
- Decision: one physical held-key sequence is one placement-history step. Rationale: users perceive it as one edit and must not undo dozens of repeats. Date/Author: 2026-09-07 / Codex.
- Decision: use a typed lifecycle owned by the live viewer/runtime; do not add an unowned timer or compatibility fallback. Rationale: stale callbacks after widget close can lose or mutate state. Prefer no timer; if event-loop coalescing is unavoidable, it must be QObject-owned and synchronously flushed/canceled before destruction. Date/Author: 2026-09-07 / Codex.


## Outcomes & Retrospective


Source implementation, validation, fresh installation, and the installed Cinnamon/X11 acceptance are complete. The user confirmed held movement, Ctrl/Ctrl+Shift resize, responsiveness, one-step Undo/Redo, and no unacceptable sustained CPU/disk behavior for package `f800e6c...` from commit `8903512c9`.

Implementation note (2026-09-07): Arrow and resize presses now update the draft geometry and overlay synchronously without panel/readiness reconciliation. A physical non-autorepeat release invokes one typed runtime flush and commits one history step; synthetic autorepeat releases return an explicit ignored result. Mode changes, focus loss, hide, close, Undo/Redo, deletion, external edits, signing, removal, and both runtime and direct viewer page navigation flush the open batch first. Flush exceptions restore the starting geometry and surface through the existing error path without history divergence. The authoritative focused suite passes 199 tests and the full suite passes 1660 with 20 skips and one existing warning, including mounted composition coverage with a disposable configured PKCS#12: five autorepeat Ctrl-resize events caused zero certificate-readiness reads, while physical release caused four bounded reads. Installed package `f800e6c...` from commit `8903512c9` passed the final Cinnamon/X11 held-key and resource acceptance.

Final acceptance note (2026-09-08): Ctrl+Y was discussed as a possible future redo shortcut but was not added to this slice. Existing Ctrl+Shift+Z behavior remains the accepted redo path.


## Context and Orientation


`src/foliaseal/presentation/qt/viewer_widget.py` receives key/focus events and owns the overlay. `signing_workspace_runtime.py` applies placement and forwards panel/readiness/history effects. `signing_workspace_properties_panel.py` implements `load_from_workflow()` and setup-session projection. `signing_action_coordinator.py` projects signing readiness. `application/signature_properties_coordinator.py` resolves certificate configuration; its certificate readiness reader can perform PKCS#12 work. `signing_workspace_composition.py` wires these objects. `application/placement_history.py` stores accepted rectangle values, including `None` for removal.

The governing contract is `docs/SPEC.md`, `docs/SCHEMAS.md`, then `docs/UI_SPEC.md`: exact movement/resize increments, keyboard operation, cancelable placement, visible final geometry, and undoable changes. This child does not change signing schema, GUI topology, or certificate semantics.


## Change Slice


Behavior change with focused/composed tests and synchronized plan status. Temporary packages, screenshots, PDFs, certificates, and performance logs stay under `/tmp`. Do not mix layout, signing transaction, persistence, Wayland, dependency, or broad rendering changes. Remove obsolete compatibility fallbacks in touched paths instead of retaining silent no-ops.


## Plan of Work


First add a real-composition test that delivers one normal key press/release followed by many `isAutoRepeat=True` presses and a physical (`isAutoRepeat=False`) release. Instrument typed seams for `apply_signature_rect_placement`, panel `load_from_workflow`, setup/coordinator load, readiness, certificate readiness, and PKCS#12 read/parse where available. Record which calls are lightweight overlay projection and which are expensive reconciliation.

Add a typed adjustment-session seam, preferably viewer-owned, retaining starting committed rectangle, current visible rectangle, active key/modifiers, dirty state, and open-batch state. Provide operations equivalent to `begin`, `apply_delta`, `flush`, `cancel`, and `close`, with typed results distinguishing accepted geometry, no-op, canceled batch, and ignored synthetic release. Apply each delta synchronously, preserving 1-point/10-point movement and resize, boundary rules, and existing-field restrictions.

On the first non-autorepeat press, begin the batch and update visible geometry immediately. Autorepeat presses update the lightweight overlay but do not reload the panel, recompute readiness, parse certificates, or commit separate history steps. A non-autorepeat release flushes the final geometry synchronously. An autorepeat release is ignored as a boundary. Flush before another physical adjustment key, signing, remove, Undo/Redo, document replacement, mode change, focus loss, or close. A changed batch commits exactly once; unchanged or canceled batches commit nothing and preserve the redo branch. Focus/mode/close must leave no callback scheduled against a deleted widget.

Keep a single non-repeat press immediate: after its release, geometry, readiness, and history are observable synchronously, without waiting for a timer. Test key-boundary clamping and final repeated deltas so the last state cannot be lost.


## Concrete Steps


From `/home/daekar/FoliaSeal` run:

    git status --short
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_workspace_runtime.py tests/integration/test_placement_gate10.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests
    git diff --check

Record actual test names/counts and counter values in this plan. Build a fresh package only after these pass; the acceptance child records package hash and installed identity.


## Validation and Acceptance


Qt tests delivered to the focused production composition must prove that normal movement/resizing remains exact and immediate; repeated presses do not invoke expensive reconciliation once per event; synthetic autorepeat release does not flush early; physical release flushes the final geometry; one held sequence creates one history step; Undo/Redo returns exact starting/final page and rectangle; no-op/canceled sequences create no step; and focus-out, mode change, signing, removal, document replacement, and close flush/cancel safely and idempotently.

Counter tests must cover `apply_signature_rect_placement`, `load_from_workflow`, setup/coordinator refresh, signing readiness, certificate readiness, and PKCS#12 parsing when those interfaces are present. Same-page adjustment must retain no full-PDF rerender or canonical-appearance regeneration. Existing fields, pointer drag/resize, Escape, Pan, Text, handle visibility, and native text Undo must remain green.

The acceptance child must rebuild and install the exact package, then exercise a disposable PDF on Cinnamon/X11. Hold movement and resize keys long enough to expose the reported fan spin-up, release, verify final geometry and one-step Undo, and observe CPU and disk writes for approximately 30 seconds plus settling. Brief work is acceptable; sustained growth, freeze, crash, lost final delta, extra history steps, or stale callbacks fails acceptance and reopens this child.


## Idempotence and Recovery


Use fresh disposable fixtures and isolated XDG directories. Close only audit-owned processes/dialogs. Never delete user certificates, profiles, PDFs, or the installed package. If the physical release is missing, focus-out, mode change, action boundary, or close must safely flush/cancel; do not hide the failure with a global timeout. Rebuild and verify package hash before repeating HITL.


## Artifacts and Notes


Record source commit, focused command/count, callback counters, exact initial/final rectangles, history depth, package hash, installed payload identity, and CPU/disk result. Do not commit passwords, user document contents, or large logs/screenshots.


## Interfaces and Dependencies


Use existing `SignatureRect`, placement-history, runtime, properties-panel, readiness, and certificate-reader types. The typed seam must distinguish physical release, synthetic autorepeat release, focus loss, mode change, action boundary, document replacement, and close. It must not expose private viewer state to AppFrame, retain optional compatibility callbacks, add a second history, or parse certificates in the viewer.


Revision note (2026-09-07): Added after the installed Gate 10 retest showed significant CPU spin-up while holding arrow keys during resize. This child records the measured callback hypotheses, requires typed coalescing and lifecycle flush semantics, and makes installed 30-second performance evidence a prerequisite for Gate 10 completion.
