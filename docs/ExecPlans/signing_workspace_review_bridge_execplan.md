# Extract The Signing Workspace Review Bridge

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice is complete. The signing shell still behaves the same when document review and document text state change, but `SigningWorkspaceWidget` no longer owns the entire review/text bridge itself. `SigningWorkspaceReviewBridge` now owns review-state rendering, review-transition application, highlight clearing, highlight setting, and jump-to-page follow-up, while the shell keeps event routing and higher-level workspace composition.

That completed extraction keeps the current behavior while making the shell less responsible for another whole concept cluster. It also matches the broader `4+5` direction of turning `SigningWorkspaceWidget` into a thinner adapter over deeper helpers.

## Child ExecPlan Dependencies

- [x] (2026-06-04 21:37Z) No child ExecPlans are required for this bounded shell-internal extraction slice.

## Progress

- [x] (2026-06-04 21:37Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the shell’s document-review/text bridge rather than reopening app-frame or interaction-session design.
- [x] (2026-06-04 21:37Z) Re-read the review/text bridge cluster in `src/foliaseal/presentation/qt/signing_shell.py`, the ordered interaction plan in `src/foliaseal/application/workspace_interaction_session.py`, and the focused shell tests that guard this path.
- [x] (2026-06-04 21:40Z) Added `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` and moved the review/text bridge logic out of `SigningWorkspaceWidget` into `SigningWorkspaceReviewBridge`.
- [x] (2026-06-04 21:40Z) Updated focused shell tests and added a consumed-drag proof that document-text selection still blocks signature placement while selection mode is active.
- [x] (2026-06-04 21:40Z) Ran focused validation with `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py`, `ruff check`, and `git diff --check`; all passed.
- [x] (2026-06-04 21:52Z) Ran the architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; found stale architecture text that still implied the shell owned the whole review/text bridge.
- [x] (2026-06-04 21:52Z) Resolved the compliance finding by updating `docs/ARCHITECTURE.md` and this ExecPlan so `signing_workspace_review_bridge.py` is documented as the bridge owner and the slice is recorded as complete.
- [x] (2026-06-04 21:52Z) Updated documentation to final state.

## Surprises & Discoveries

- Observation: the review/text bridge belongs in `SigningWorkspaceReviewBridge`, not in `SigningWorkspaceWidget`.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` now owns `apply_state()`, `select_review_signature()`, `apply_transition()`, and the concrete viewer-effect handling that used to sit in the shell.

- Observation: `WorkspaceInteractionSession` already produces the correct Qt-free review transition object, so the next slice should not reopen that application boundary.
  Evidence: `ApplyReviewTransition` is already emitted from `src/foliaseal/application/workspace_interaction_session.py` when review consumes a viewer selection.

- Observation: the compliance review surfaced stale architecture prose rather than a code mismatch.
  Evidence: `docs/ARCHITECTURE.md` still described `signing_shell.py` as applying the review/text bridge directly until this documentation pass corrected it.

## Decision Log

- Decision: keep `WorkspaceInteractionSession` and `DocumentReviewWorkspaceSession` unchanged in this slice.
  Rationale: the goal is to reduce shell-local bridging logic, not to rework already-deepened application boundaries.
  Date/Author: 2026-06-04 / Codex

- Decision: prefer a new internal helper module over another nested helper object inside `signing_shell.py`.
  Rationale: this slice is meant to remove concentration from the large shell module, not just shuffle methods around inside the same file.
  Date/Author: 2026-06-04 / Codex

- Decision: update the architecture doc in the same slice once the compliance review showed stale ownership language.
  Rationale: the repository expects architecture docs to track the code as it exists, and the review/text bridge ownership had moved to `signing_workspace_review_bridge.py`.
  Date/Author: 2026-06-04 / Codex

## Outcomes & Retrospective

The review/text bridge extraction is complete and validated. The shell still behaves the same for review-consumed viewer selection, text highlight application, text highlight clearing, and review-requested page jumps, but that behavior now flows through `SigningWorkspaceReviewBridge` instead of shell-local bridge methods.

Validation already completed during the slice:

- `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py`
- `ruff check`
- `git diff --check`

The compliance review found one documentation mismatch: `docs/ARCHITECTURE.md` still implied that `signing_shell.py` owned the review/text bridge. That was resolved by updating `docs/ARCHITECTURE.md` and this ExecPlan so the helper ownership and completed status are recorded consistently.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` is still the composition root for the interactive signing workspace. Its application-layer helpers already do more than they used to:

- `src/foliaseal/application/workspace_interaction_session.py` returns ordered, Qt-free workspace interaction effects.
- `src/foliaseal/application/document_review_workspace.py` owns review refresh, text search, text selection mode, and review-consumed drag behavior.
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` owns the actual sidebar widget construction and render logic.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns the review/text bridge between the session state and the live viewer/sidebar widgets.

The shell delegates the bridge between those helpers and the live viewer/sidebar widgets for the review/text concept. The bridge includes:

- rendering `DocumentReviewWorkspaceState` into the sidebar
- applying `DocumentReviewWorkspaceTransition`
- clearing and setting text-highlight overlays on the viewer
- changing viewer interaction mode for text selection
- triggering a follow-up navigation refresh when review/text effects request a page jump

Those are coherent together and now live behind a dedicated helper without changing the rest of the shell’s composition role.

The files that matter for this slice are:

- `src/foliaseal/presentation/qt/signing_shell.py`, which coordinates the shell-side bridge integration and delegates the review/text bridge to the helper.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py`, which now owns the bridge cluster.
- `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, which already knows how to render `DocumentReviewWorkspaceState`.
- `src/foliaseal/application/workspace_interaction_session.py`, which already emits `ApplyReviewTransition` effects and must stay unchanged here.
- `tests/unit/test_qt_signing_shell.py`, which guards shell entrypoint behavior for viewer selection, page changes, and review/text UI effects.
- `docs/ARCHITECTURE.md`, which documents the shell’s current orchestration role.

In this plan, a “bridge” means the widget-facing adapter logic that converts already-computed application transitions into concrete viewer/sidebar mutations.

## Plan of Work

First, add a new internal helper module under `src/foliaseal/presentation/qt/` for the document-review/text bridge. The helper should accept the sidebar, viewer widget, document-review workspace session, workspace interaction session, and a small callback for page-jump follow-up so it can apply review state and review effects without reaching back into the whole shell object.

Second, edit `src/foliaseal/presentation/qt/signing_shell.py` so it constructs that helper and delegates `_apply_document_review_workspace_state(...)`, `_on_document_review_signature_selected(...)`, and `ApplyReviewTransition` handling to it. The shell must keep the existing public behavior methods, the ordered workspace interaction plan application, and the other non-review effects intact.

Third, update focused shell tests. Keep the entrypoint tests for viewer selection, page changes, refresh viewer, and panel-change behavior. Add or adjust a focused test that proves a review-consumed viewer drag still avoids signature placement, and one that proves the review/text bridge still applies highlight clearing and page-jump behavior correctly through the shell.

Finally, run focused validation, perform the required compliance review, update any stale docs, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the internal bridge helper and migrate the shell.

       apply_patch ... on src/foliaseal/presentation/qt/<new helper>.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused shell tests.

       apply_patch ... on tests/unit/test_qt_signing_shell.py

3. Run focused validation.

       pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice was accepted when all of the following became true:

- a dedicated internal helper owns the review/text bridge logic that used to live directly in `SigningWorkspaceWidget`
- the shell still behaves the same for review-consumed viewer selection, text highlight application, text highlight clearing, and review-requested page jumps
- `WorkspaceInteractionSession` remains unchanged and still emits the same ordered effect objects
- focused shell tests prove the bridge behavior still holds through the public shell entrypoints
- `docs/ARCHITECTURE.md` accurately describes the new helper ownership and shell split

Run:

    pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py

Then run:

    ruff check src/foliaseal/presentation/qt/<new helper>.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. No GUI flow or text is intended to change.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the helper extraction causes confusing ownership of page-jump follow-up, keep that one callback explicit rather than pushing the whole shell into the helper. Do not recover by duplicating the same review/text bridge logic in both the shell and the new helper; one owner must remain at the end of the slice.

If the extraction unexpectedly requires large new public API changes, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new internal helper module for review/text bridging
- a smaller shell-side integration surface for review/text bridging inside `src/foliaseal/presentation/qt/signing_shell.py`
- focused shell tests proving review-consumed drag and text-highlight behavior are unchanged

This section now records the completed implementation and validation state rather than a pending transcript.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the new helper should expose a stable internal adapter surface approximately like:

    class SigningWorkspaceReviewBridge:
        def apply_state(self, state: DocumentReviewWorkspaceState) -> None: ...
        def select_review_signature(self, index: int) -> None: ...
        def apply_transition(self, transition: DocumentReviewWorkspaceTransition) -> None: ...

The helper may expose smaller internal methods for viewer-effect application, but the shell should only need to delegate to the high-level bridge behavior. The shell continues to own the broader workspace interaction plan loop and all non-review effects.

Revision note: Created on 2026-06-04 by Codex for the next shell-internal tracer bullet in the same signing-workspace hybrid `4+5` direction, after the grouped sidebar surface slice was completed. Updated on 2026-06-04 after implementation, validation, and compliance-review reconciliation were finished.
