# Move app-frame workspace compatibility state off the window object

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, opening a PDF in FoliaSeal still installs the live signing workspace, enables `File > Save As...`, and supports reopening the signed output through the app frame. The visible GUI behavior does not change.

The architectural win is that `src/foliaseal/presentation/qt/app_frame.py` now owns one narrow snapshot of the current workspace state on `FoliaSealAppFrame` and exposes `current_workspace`, `current_shell`, `current_viewer_workflow`, and `current_signing_workflow` from that snapshot. The app frame no longer mirrors the active workspace onto `window.current_shell`, `window.current_viewer_workflow`, or `window.current_signing_workflow`. The user-visible proof is unchanged open/save/reopen behavior plus focused app-frame tests that assert on frame-owned state.

## Child ExecPlan Dependencies

- [x] (2026-06-29 00:22Z) `docs/ExecPlans/app_frame_shell_port_execplan.md` is complete; the app frame already depends on an explicit `SigningWorkspacePort` for production behavior.
- [x] (2026-06-29 00:22Z) `docs/ExecPlans/phase3_harness_testing_adapter_execplan.md` is complete; the harness side of the hybrid seam already moved to an explicit testing adapter.
- [x] (2026-06-29 00:22Z) No child ExecPlans are required for this bounded app-frame snapshot slice.

## Progress

- [x] (2026-06-28) Re-read `app_frame.py`, `app_frame_workspace_open.py`, `test_qt_app_frame.py`, the current architecture doc, and the prior hybrid-seam notes.
- [x] (2026-06-28) Kept `WorkspaceCompatibilityState`, stored it on the frame, removed the `window.current_*` writes, and rewrote tests to the frame-owned state.
- [x] (2026-06-28) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the landed seam.
- [x] (2026-06-28) Recorded the validation and compliance status for the landed app-frame snapshot slice.

## Surprises & Discoveries

- Observation: the open-workspace seam already returns exactly the state needed for a frame-owned snapshot.
  Evidence: `src/foliaseal/presentation/qt/app_frame_workspace_open.py` already defines `WorkspaceCompatibilityState(shell_widget, viewer_workflow, signing_workflow)` and returns it in `OpenWorkspaceOutcome`.

- Observation: the frame-owned snapshot is the right long-term host for the compatibility payload.
  Evidence: `FoliaSealAppFrame` now stores `WorkspaceCompatibilityState` on `_current_workspace` and exposes derived read access through frame properties instead of window-level compatibility attributes.

## Decision Log

- Decision: keep `WorkspaceCompatibilityState` as the frame-owned snapshot object.
  Rationale: the current open-workspace seam already returns a suitable typed snapshot, so the narrowest durable move is to store that object on the frame and expose frame properties from it.
  Date/Author: 2026-06-28 / Codex

- Decision: keep `_foliaseal_app_frame` as a separate follow-on concern.
  Rationale: it is a distinct compatibility backdoor and not required for the landed snapshot seam.
  Date/Author: 2026-06-28 / Codex

## Outcomes & Retrospective

This slice is implemented. `FoliaSealAppFrame` now owns `_current_workspace`, derives `current_workspace`, `current_shell`, `current_viewer_workflow`, and `current_signing_workflow` from that snapshot, and keeps the live workspace port as the behavior seam. `open_pdf_path()` stores `outcome.compatibility`, installs the shell widget as the central widget, and preserves the open/save/reopen behavior while removing the `window.current_*` mirror.

## Validation and Compliance Status

- Focused app-frame tests in `tests/unit/test_qt_app_frame.py` now assert on frame-owned state instead of `window.current_*`.
- `docs/ARCHITECTURE.md` has been reconciled with the landed snapshot seam.
- `docs/SPEC.md` does not require changes for this slice.
- The compatibility payload remains in `WorkspaceCompatibilityState`; no `SigningWorkspacePort` redesign was needed.
- The only remaining compatibility exposure called out for possible follow-on review is `_foliaseal_app_frame`.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns the main window, menu actions, settings and certificate dialogs, and the transition from the placeholder label to the active signing workspace. When `open_pdf_path()` succeeds, it asks `WorkspaceOpenService` for an `OpenWorkspaceOutcome`, stores the shell port privately, stores the compatibility snapshot on the frame, installs the shell widget as the central widget, and enables `File > Save As...`.

The narrow open-workspace boundary already exists in `src/foliaseal/presentation/qt/app_frame_workspace_open.py`. Its `WorkspaceCompatibilityState` dataclass contains only the concrete shell widget plus the `ViewerWorkflow` and `SigningDraftWorkflow` created for the opened PDF. That object is returned in `OpenWorkspaceOutcome` so the frame can own the snapshot and expose typed frame properties from it.

In this repository, a “frame-owned workspace snapshot” means the app frame itself stores the active workspace compatibility state and exposes it through frame properties or one typed `current_workspace` property. It does not mean introducing a new service layer or changing how the production shell port behaves. The production port remains responsible for Save As, live settings propagation, and certificate refresh. This slice only narrows how the app frame holds and exposes the active workspace state.

The relevant tests are in `tests/unit/test_qt_app_frame.py`. They assert on `frame.current_shell`, `frame.current_workspace`, and the derived workflow accessors instead of `frame.window.current_*`. The production behavior to preserve is: opening a PDF installs the shell widget, reopening the signed output still returns the live shell widget, and settings/save-as flows still route through the shell port.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Replace the frame’s parallel `_current_viewer_workflow` and `_current_signing_workflow` fields with one `_current_workspace` field typed as `WorkspaceCompatibilityState | None`, or an equivalent frame-owned wrapper if that reads better. Keep `_current_shell_port` as the behavior seam. Add frame properties for the current shell widget and current signing workflow if tests or nearby code need them, but source them from the frame-owned snapshot instead of window attributes.

Second, update initialization and the open path in `app_frame.py`. Remove the `window.current_shell`, `window.current_viewer_workflow`, and `window.current_signing_workflow` placeholder assignments from `__init__`. In `open_pdf_path()`, store `outcome.compatibility` on the frame, install `outcome.compatibility.shell_widget` as the central widget, and return that widget exactly as before. Do not change the `SigningWorkspacePort` behavior path or the `WorkspaceOpenService` return shape in this slice.

Third, update `tests/unit/test_qt_app_frame.py`. Rewrite the current assertions to use frame-owned state, for example `frame.current_shell`, `frame.current_workspace`, or `frame.current_signing_workflow`, depending on the final property names. Preserve the same behavior checks for central-widget installation, reopen callback behavior, Save As enablement, and error handling. Keep the tests focused on the app-frame seam; do not broaden them into shell internals.

Fourth, reconcile `docs/ARCHITECTURE.md` so it no longer describes `app_frame.py` as the compatibility-exposure edge for `window.current_shell`, `window.current_viewer_workflow`, and `window.current_signing_workflow`. The doc should instead describe the frame as owning the active workspace snapshot itself while continuing to use the shell port for behavior.

Finally, run focused validation and the required compliance review. If the review finds only stale docs, fix those docs inside this slice. If it finds more runtime compatibility state than `window.current_*`, record that as the next follow-on slice rather than widening this one.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Move active workspace state behind the frame and remove the `window.current_*` mirror.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Rewrite focused app-frame tests to the frame-owned snapshot/properties.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan, rerun validation if needed, then run the compliance review and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- opening a PDF still installs the shell widget as the central widget and enables `File > Save As...`;
- reopening the signed output still returns the currently installed shell widget;
- the app frame still exposes enough typed current-workspace state for focused tests and nearby code without using `window.current_shell`, `window.current_viewer_workflow`, or `window.current_signing_workflow`;
- those three `window.current_*` attributes are no longer initialized or written by `app_frame.py`;
- no shell-port redesign, app settings behavior change, or `_foliaseal_app_frame` cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The app should still open, save, and reopen PDFs the same way, but the current workspace state should now live on the frame instead of on `window.current_*`.

## Idempotence and Recovery

This is a behavior-preserving refactor in local Qt presentation code. It is safe to retry. If a test fails because it still expects a `window.current_*` attribute, move that assertion to the corresponding frame-owned property instead of reintroducing the window mirror.

If the frame ends up needing multiple separate properties for readability, derive them from one stored compatibility snapshot rather than restoring parallel mutable fields. If `_foliaseal_app_frame` turns out to be unused, record that as the next slice unless removing it is required to keep this implementation coherent.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` owning the active workspace compatibility snapshot itself;
- `tests/unit/test_qt_app_frame.py` proving the same behavior without `window.current_*` assertions;
- focused validation output showing the app-frame seam still passes;
- an updated `docs/ARCHITECTURE.md` that describes the new frame-owned state.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

In the landed implementation, `WorkspaceOpenService` keeps returning:

    @dataclass(frozen=True)
    class WorkspaceCompatibilityState:
        shell_widget: Any
        viewer_workflow: ViewerWorkflow
        signing_workflow: SigningDraftWorkflow

`FoliaSealAppFrame` should then own a field shaped like:

    self._current_workspace: WorkspaceCompatibilityState | None

and expose any needed read access through frame properties, for example:

    @property
    def current_workspace(self) -> WorkspaceCompatibilityState | None: ...

    @property
    def current_shell(self) -> Any | None: ...

    @property
    def current_signing_workflow(self) -> SigningDraftWorkflow | None: ...

The exact property set may vary, but the state must come from the frame-owned snapshot, not from `window.current_*`. This slice did not widen `SigningWorkspacePort` or redesign `WorkspaceOpenOutcome`.

Revision note: Updated on 2026-06-28 by Codex to reflect the landed app-frame workspace snapshot seam, where `FoliaSealAppFrame` owns `_current_workspace`, derives the `current_*` accessors from it, and no longer mirrors the workspace onto `window.current_*`.
