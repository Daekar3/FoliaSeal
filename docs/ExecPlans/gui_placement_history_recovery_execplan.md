# Preserve placement history across edits, removal, and UI refresh


This is a living ExecPlan maintained under /home/daekar/.codex/skills/write-execplan/PLANS.md. Update Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective during execution.

## Purpose / Big Picture


Mouse edits and Remove Placement must immediately enable Undo. Undo must restore exact prior geometry or the removed rectangle, and Redo must restore the accepted change. Text editing retains its own undo history.

## Child ExecPlan Dependencies


This is the second child of gui_placement_gate10_recovery_parent_execplan.md. First complete gui_placement_mode_focus_cancel_execplan.md to stabilize focus and mode, then extend its composed Qt regression.

## Progress


- [x] (2026-09-07) Recorded user failures and inspected relevant source paths; authored plan.
- [x] (2026-09-07) Incorporated three-agent review corrections and strengthened composed-event, history and package acceptance coverage.
- [x] (2026-09-07) Reproduced the history-loss ordering in the composed callback path.
- [x] (2026-09-07) Completed the history milestones and focused regression validation.
- [x] (2026-09-07) Removed optional viewer-history fallbacks from runtime and shell ports; all current fakes expose the required placement-history methods.
- [x] (2026-09-07) Removed the remaining AppFrame session-history fallback; active workspaces now satisfy the typed capability contract directly and the app-frame/dependent integration tests pass 86 tests.
- [x] (2026-09-07) Reconciled the parent and acceptance child; installed package verification and bounded human acceptance remain explicitly open.

## Surprises & Discoveries


PlacementHistory.synchronize clears both stacks when incoming geometry differs. PdfPreviewWidget.set_signature_overlay calls it during projection of model state. Pointer _apply_overlay_drag_selection calls the selection callback without an explicit local history commit. Runtime.on_panel_change records changed rectangles, but clears history on equal rectangles. Runtime.remove_signature_placement calls apply_keyboard_placement(None), sharing the history-replay route. These paths can reset or bypass user-edit history; trace their actual callback order before choosing a repair.

Review traced pointer selection through src/foliaseal/application/workspace_interaction_session.py: ApplySignatureRect defaults to notify=False, bypassing on_panel_change recording, then overlay synchronization adopts the new geometry. Keyboard move/resize calls the runtime callback before its local commit; that callback synchronizes the new rectangle first, erasing prior history and making the subsequent commit a no-op. These are concrete ordering defects. Menu removal and Delete use different entry paths and need separate composed coverage. Undo/Redo first update history.current, so synchronizing an identical replay target does not itself clear history; test secondary panel notifications rather than claiming replay necessarily fails at synchronize.

AppFrame._sync_edit_history_actions deliberately prefers native text-editor history when a text editor owns focus. A disabled menu is therefore not by itself proof that the placement stack is empty. Tests must distinguish stored history from focus-sensitive action routing.

Implementation evidence (2026-09-07): projection now updates the visible overlay without adopting or clearing history; explicit adoption is reserved for existing-field lifecycle setup. Pointer selections commit once after the ordered interaction plan, keyboard edits commit after projection, and removal records None once before replaying the draft change. Unchanged panel refreshes no longer clear either stack. The shell forwards placement history capabilities to the AppFrame session port. Real offscreen Qt coverage proves handle cancellation, Pan cancellation, AppFrame pointer edit Undo/Redo, menu removal Undo/Redo, Delete Undo, explicit lifecycle reset, and same-page no-rerender behavior. The shared placement-focused suite passes 276 tests and the full repository suite passes 1646 tests with 20 skips and one existing warning; installed acceptance remains open.

## Decision Log


Decision (2026-09-07): Accept source-supported review findings while rejecting overstated startup and replay claims. Rationale: composition initializes Pan, and synchronization to an identical replay target does not itself clear history. Author: Codex.

Decision (2026-09-07): Repair the existing placement contract without redesigning the signing workflow. Rationale: reported failures contradict docs/UI_SPEC.md and require focused corrections. Author: Codex.

Decision (2026-09-07): Separate behavior repair from package evidence and human acceptance. Rationale: prior isolated tests did not predict installed behavior, so completion needs composed events and rendered evidence.

Decision (2026-09-07): Keep placement history on the typed viewer/session contract. Rationale: returning the draft unchanged when a viewer lacks an undo method hides an integration defect and makes Gate 10 appear accepted while doing nothing. The runtime and shell port now call the required methods directly.

Decision (2026-09-07): Apply the same strict contract at AppFrame action projection. Rationale: Undo/Redo enablement must not silently degrade when an active fake or production session omits required capability methods.

## Outcomes & Retrospective


Planning, implementation and focused regression validation are complete. Installed package verification and the bounded human acceptance pass remain pending; this document does not certify the installed GUI until those gates pass.

The strict interface cleanup is validated by the shared placement-focused suite (276 passed), the full repository suite (1646 passed, 20 skipped, one existing warning), plus Ruff and `git diff --check`. Installed package verification and the bounded human acceptance pass remain open.

Governing-document review (2026-09-07): `docs/SPEC.md`, `docs/SCHEMAS.md`, and `docs/UI_SPEC.md`
remain consistent with viewer-owned placement history, focus-sensitive Edit Undo/Redo, and explicit
lifecycle clearing; no governing-document change is required.

Three-agent review corrections are incorporated. Keyboard commit-after-projection, pointer recording, explicit lifecycle adoption and no-op refresh behavior now have focused coverage. The acceptance child owns fresh installed payload identity and rendered Cinnamon/X11 verification; this child does not certify those external gates.

## Context and Orientation


The history implementation is src/foliaseal/application/placement_history.py. The viewer owns its instance and exposes record_signature_edit, undo_signature_placement and redo_signature_placement. Runtime in src/foliaseal/presentation/qt/signing_workspace_runtime.py applies geometry through properties-panel callbacks and sync_signature_overlay; composition wires these callbacks. app_frame.py queries capabilities and routes Edit commands. Inspect tests/unit/test_placement_history.py, tests/unit/test_qt_viewer_widget.py, tests/unit/test_qt_signing_workspace_runtime.py and tests/unit/test_qt_app_frame.py. History means a sequence of accepted document-placement values, including None, not reusable library saves.

## Change Slice


Behavior change with regressions and scoped documentation. No generated package refresh, signing transaction changes, broad viewer refactor or legacy compatibility adapters.

## Plan of Work


Milestone 1 instruments callback ordering within a test, using the real viewer/runtime/panel composition. Record history before/after pointer release, overlay synchronization, panel notification, menu removal and history replay. Prove a failing user sequence; do not stop after a PlacementHistory unit test passes.

Extend tests/integration/test_placement_gate10.py created by the first child; it is an intentional new artifact, not a pre-existing test. Retain the real SigningWorkspaceInteractionBridge and WorkspaceInteractionSession so notify=False and projection callbacks actually run. Require the accepted-edit sequence to be mutation acceptance, exactly one history commit, model/overlay projection without history clearing, then action-enablement refresh. Record callback order for pointer, keyboard, menu removal and Delete. A rejected edit must not enter history.

Milestone 2 establish explicit operations for accepting a user edit, replaying Undo/Redo, projecting state, and resetting at a lifecycle boundary. Keep one history owner; retain the existing viewer-owned PlacementHistory unless composed evidence requires moving it. Commit accepted pointer, keyboard, numeric, profile-application and menu-removal changes exactly once before a projection can erase the previous value. Replay changes without committing a new edit or destroying the redo branch. Replace equal-geometry notification resets with explicit setup/lifecycle reset calls. Overlay repaint and readiness refresh must not mutate history.

Milestone 3 update action enablement after accepted edits and replay. Keep native text undo isolated; moving focus to the canvas exposes placement history. Test new-edit-after-Undo invalidates Redo, duplicate/no-op updates do not create steps, one long pointer drag creates one step, and canceled drags create none. Reset on Open/Close, setup replacement, successful signing and discard as required by UI_SPEC; placement-profile application within the current editing session must remain undoable rather than accidentally treated as setup replacement.

Trace and name each actual lifecycle entry point in the test evidence before changing resets, including the successful-signing callback in signing_workspace_action_bridge.py and workspace replacement through AppFrame. Do not substitute incidental overlay synchronization for explicit reset tests. Assert native text Undo affects only text; after canvas focus, both Edit menu actions and shortcuts affect placement history.

## Concrete Steps


From /home/daekar/FoliaSeal:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_placement_history.py tests/unit/test_qt_viewer_widget.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_app_frame.py tests/integration/test_placement_gate10.py
    git diff --check

Run the existing profile-editor coverage if profile application changes. Record the failing-before/passing-after composed test and actual counts.

## Validation and Acceptance


Create A, drag to B, Undo to exact A, Redo to exact B, Remove to None, Undo to B, Redo to None. Assert application draft, visible overlay and menu enablement agree at every step. Repeat with keyboard edits and unchanged panel/readiness refreshes between actions. Repeat numeric/profile edits. Confirm canceled edits preserve the prior redo branch and no-op callbacks preserve both stacks. Preserve same-page placement performance: geometry changes must not trigger full PDF rerender or canonical appearance regeneration.

Also undo initial creation from A to None and redo to A; test one keyboard event produces exactly one step, and test Delete independently from menu removal. Insert unchanged panel/readiness refreshes between every mutation and replay. Assert zero full-PDF refresh and canonical-appearance regeneration calls for same-page edits using counters around the real callbacks; preserve the existing cross-page navigation behavior.

## Idempotence and Recovery


Inspect git status before edits and preserve unrelated changes. Use disposable fixtures and isolated configuration. Record owned process IDs and temporary paths; close owned dialogs and stop owned audit processes on success or failure. Do not terminate the user's existing session or delete user PDFs, profiles or certificates. Repeated tests should begin with fresh fixture state. If desktop access is unavailable, finish all independent checks and record the exact missing access; leave the live gate open.

## Artifacts and Notes


The source findings above were obtained by read-only inspection on 2026-09-07. Store new concise test evidence and exact reproduction steps here during execution. Keep the parent and owning child synchronized when a failure is discovered. Avoid historical test counts as claims about the current build.

## Interfaces and Dependencies


Retain PlacementHistory.commit, undo, redo and clear contracts where possible. Explicitly distinguish adoption/reset from render-only overlay projection; rename or remove misleading synchronization paths and update every caller. Preserve runtime can_undo_placement/can_redo_placement and undo_placement/redo_placement as the menu interface. Do not add parallel histories or persistent history schemas.

Revision note (2026-09-07): Created from installed Gate 2 item 10 failures and current source inspection to prevent passing low-level tests from substituting for usable placement behavior.

Revision note (2026-09-07, review wave): Incorporated validated explorer observations, strengthened production callback and rendered acceptance requirements, and rejected unsupported startup/replay conclusions. The integration test remains an intentionally new artifact.

Revision note (2026-09-07, implementation): Completed the single viewer-owned history path for pointer, keyboard, panel, removal, undo/redo and explicit lifecycle adoption. Added composed offscreen pointer history coverage and focused regressions. Installed acceptance remains with the acceptance child.
