# Deepen Viewer Interaction Coordination

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this change, the production signing shell will no longer own the core logic that translates viewer state and viewer drags into signing-placement updates. Instead, a deeper application-layer viewer-interaction session will own page-sync, selection-to-signature-rectangle translation, and page-change results, while the shell remains a Qt adapter that applies overlays, refreshes previews, and routes unrelated signing or review callbacks.

The user-visible behavior in this slice should stay the same. You should still be able to drag on the PDF page to place or resize a visible signature, change pages from the placement controls, and keep the signature overlay and readiness state in sync with the current viewer page. The gain is architectural: the remaining review/text/viewer seam gets a stable core boundary so this area can be considered tied off before moving to another architecture topic.

## Child ExecPlan Dependencies

- [ ] No child ExecPlans are planned for this slice.

## Progress

- [x] (2026-05-25 11:04 -04:00) Identified the narrow slice: extract a viewer-interaction session that owns page-sync from the viewer snapshot, selection-to-signature-rectangle translation, and page-change navigation results while leaving preview refresh, overlay application, and signing-action invalidation in the shell.
- [x] (2026-05-25 11:09 -04:00) Added `src/foliaseal/application/viewer_interaction_session.py` with placement-context and selection-placement result types plus direct boundary tests in `tests/unit/test_viewer_interaction_session.py`.
- [x] (2026-05-25 11:11 -04:00) Rewired `src/foliaseal/presentation/qt/signing_shell.py` so placement/page-sync transitions flow through the new session and a shared shell-side navigation helper instead of ad hoc shell translation methods.
- [x] (2026-05-25 11:12 -04:00) Fixed the first-pass issues: aligned the new boundary test with the existing `SignatureRect` validation message and ensured shared viewer navigation always sets the logical page index before refreshing the widget.
- [x] (2026-05-25 11:12 -04:00) Focused validation passed, architecture docs were updated, and the slice is ready for commit.

## Surprises & Discoveries

- Observation: The `dev-loop` skill still cannot use subagents in this session because new agent threads are rejected.
  Evidence: `multi_agent_v1.spawn_agent` returned `collab spawn failed: agent thread limit reached` on 2026-05-25.

- Observation: The shell had two separate viewer page-navigation paths: one from placement controls and one from review/text page jumps. They both needed the same “set logical page, refresh widget, then resync placement context and overlay” sequence.
  Evidence: `signing_shell.py` previously handled `_handle_page_change()` and `_apply_document_review_workspace_effects()` separately with overlapping page-jump logic.

## Decision Log

- Decision: Keep this slice focused on viewer-to-signing transition logic and do not pull viewer widget event handling itself out of `viewer_widget.py`.
  Rationale: The remaining high-value shell debt is not raw Qt mouse logic; it is the shell-owned translation from viewer output into signing-placement state. Moving the widget event logic now would widen the slice and mix presentation refactors with the core application boundary.
  Date/Author: 2026-05-25 / Codex

- Decision: Leave review/text workflow in `document_review_workspace.py` and do not merge it into the new viewer-interaction boundary.
  Rationale: The previous slice intentionally separated review/text transitions. The remaining viewer interaction seam should compose with that boundary, not collapse it back into one larger object.
  Date/Author: 2026-05-25 / Codex

- Decision: Keep widget refresh and overlay application in the shell even after extracting `viewer_interaction_session.py`.
  Rationale: Those are direct Qt concerns. The deeper boundary should own translation and placement semantics, not concrete widget mutation.
  Date/Author: 2026-05-25 / Codex

- Decision: Introduce a shared shell-side navigation helper instead of trying to move `viewer_widget.refresh(...)` into the application boundary.
  Rationale: The session can own logical page updates, but only the shell can safely refresh the concrete viewer widget and apply overlay effects. The helper removes duplication without violating the UI/core split.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

This slice completed the remaining high-value viewer-to-signing translation work in this architecture area. The shell no longer constructs `SignatureRect` placement state directly from a `PdfRect`, and it no longer reconstructs placement context from the viewer snapshot inline. That logic now lives behind `viewer_interaction_session.py`.

The user-visible behavior stayed stable in focused tests: dragging on the page still places a visible signature, placement-control page changes still clear signed-state messaging through the existing signing action coordinator, and review/text page jumps still refresh the viewer and preserve overlay state. The remaining shell code in this area is now clearly Qt adapter work rather than core placement logic.

## Context and Orientation

The current production signing GUI lives in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py). After the previous slice, `document_review_workspace.py` now owns review refresh, text search, text selection, and viewer-effect intents for that workflow. What remains in the shell is a different interaction seam: turning a viewer selection into a `SignatureRect`, syncing `SignaturePlacementContext` from the latest viewer snapshot, and handling page changes requested by the placement controls.

Today that logic is still spread across these shell methods:

- `refresh_viewer()`
- `_handle_viewer_selection()`
- `_handle_page_change()`
- `_sync_placement_context_from_viewer()`

`_sync_signature_overlay()` stays a shell concern because it is a direct widget effect (`set_signature_overlay(...)`). `properties_panel.refresh_preview()` also stays in the shell because preview ownership is already split into dedicated Qt modules and should not be mixed into this slice.

The viewer widget in [src/foliaseal/presentation/qt/viewer_widget.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/viewer_widget.py) already converts drag rectangles from widget coordinates into PDF coordinates through [src/foliaseal/application/viewer_workflow.py](/home/daekar/FoliaSeal/src/foliaseal/application/viewer_workflow.py). By the time the shell receives `on_selection`, it already has a `PdfRect`. That means the remaining shell logic is not about coordinate math in Qt; it is about deciding what that `PdfRect` means for the signing draft and how to keep the signing placement context aligned with the current viewer page and rotation.

The relevant shell tests are in [tests/unit/test_qt_signing_shell.py](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py). They already cover:

- a drag outside text-selection mode creating a signature rectangle,
- page changes clearing signed-state messaging,
- `refresh_viewer()` preserving readiness/flow state after preview updates.

This slice should add direct boundary tests for the new viewer-interaction session so fewer of those transitions are only proved indirectly through the shell.

## Plan of Work

Create a new application-layer module at `src/foliaseal/application/viewer_interaction_session.py`. Define a Qt-free session that depends on `ViewerWorkflow` and returns immutable results for three operations:

- refreshing placement context from the current viewer snapshot,
- translating a `PdfRect` viewer selection into a `SignatureRect`,
- handling a requested logical page change.

The session must own all validation and failure shaping for those operations. It should return enough information for the shell to decide whether to apply the resulting placement context, whether to update the draft signature rectangle, whether to refresh the viewer widget, and what error message to emit if something failed.

Do not move review/text behavior into this session. `SigningWorkspaceWidget._handle_viewer_selection()` should still ask `document_review_workspace.py` whether a drag was consumed for text selection first. Only when the review/text boundary does not consume the drag should the shell delegate to the new viewer-interaction session for signature-placement behavior.

Then rewire `src/foliaseal/presentation/qt/signing_shell.py` so that:

- `refresh_viewer()` uses the session to derive placement context instead of calling `_sync_placement_context_from_viewer()` directly,
- `_handle_viewer_selection()` uses the session to derive the `SignatureRect` for signing placement,
- `_handle_page_change()` uses the session to perform the page jump and derive the new placement context.

Keep these behaviors in the shell:

- applying the returned `SignatureRect` to `properties_panel`,
- applying `set_signature_overlay(...)`,
- refreshing the preview card,
- invalidating signing action state,
- emitting user-visible errors.

Add a new direct boundary test file that proves:

- a valid `PdfRect` selection becomes the expected `SignatureRect`,
- invalid rectangles return a stable error message instead of mutating state,
- page change returns the new placement context from the viewer snapshot,
- missing snapshots fail softly when placement context is requested.

Update [docs/ARCHITECTURE.md](/home/daekar/FoliaSeal/docs/ARCHITECTURE.md) to record the new boundary and the shell’s reduced responsibility in this area.

## Concrete Steps

All commands below must be run from `/home/daekar/FoliaSeal`.

1. Add `src/foliaseal/application/viewer_interaction_session.py` and focused tests.
2. Rewire `src/foliaseal/presentation/qt/signing_shell.py` to consume the new session.
3. Run focused tests:

       pytest tests/unit/test_viewer_interaction_session.py tests/unit/test_qt_signing_shell.py

4. Run lint checks:

       ruff check src/foliaseal/application/viewer_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_viewer_interaction_session.py tests/unit/test_qt_signing_shell.py

5. Run diff hygiene:

       git diff --check

6. Update this ExecPlan, update `docs/ARCHITECTURE.md`, complete the compliance review, and commit the slice.

Observed passing proof:

       tests/unit/test_viewer_interaction_session.py .....                      [  6%]
       tests/unit/test_qt_signing_shell.py .................................... [100%]
       ============================== 74 passed in 8.85s ==============================

## Validation and Acceptance

Acceptance is behavioral. After this slice:

- dragging on the PDF page outside text-selection mode still places a visible signature rectangle,
- placement-control page changes still navigate the viewer and keep signing readiness/results consistent,
- `refresh_viewer()` still refreshes the viewer, placement context, overlay, preview, and signing-action state,
- direct workspace/session tests prove that the shell no longer owns the core selection-to-signature and page-sync logic.
- review/text page jumps and placement-control page changes now share one shell navigation path instead of duplicating viewer refresh sequencing.

Run:

    pytest tests/unit/test_viewer_interaction_session.py tests/unit/test_qt_signing_shell.py

and expect all tests to pass. Also run the `ruff check` and `git diff --check` commands listed above.

## Idempotence and Recovery

This slice is additive and safe to retry. If the new viewer-interaction session introduces regressions, revert only the new session wiring and keep the already-extracted review/text boundary intact. Do not mix in app-frame or signing-action changes while implementing this slice.

## Artifacts and Notes

The most important evidence will be:

    - the new boundary test file for the viewer-interaction session,
    - preserved shell tests for placement/page-change behavior,
    - focused `pytest` and `ruff` transcripts,
    - the updated architecture notes for the new boundary.

## Interfaces and Dependencies

In `src/foliaseal/application/viewer_interaction_session.py`, define stable, Qt-free types for:

- one immutable outcome type for placement-context refresh,
- one immutable outcome type for selection-to-signature placement,
- one immutable outcome type for page-change handling,
- one session class that depends on `ViewerWorkflow`.

The session must expose methods for:

- deriving placement context from the current viewer snapshot,
- translating a `PdfRect` into a `SignatureRect` for the current logical page,
- performing a page jump and returning the resulting placement context.

The module may depend on repository types such as `PdfRect`, `PageBox`, `SignatureRect`, and `SignaturePlacementContext`. It must not import PySide6 or concrete widget bindings.

Revision note: created on 2026-05-25 to drive the next review/viewer architecture slice after `document_review_workspace.py` was extracted.

Revision note: updated on 2026-05-25 after implementation to record the completed slice, the shared navigation helper, the boundary-test correction, and the passing validation evidence.
