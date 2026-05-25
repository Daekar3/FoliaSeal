# Deepen Document Review and Text Interaction Workflow

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this change, the production signing shell will no longer own most of the state machine for document review, document text search, and text-selection mode. A deeper application-layer workspace session will own those transitions and will return plain state plus viewer-effect intents. This matters because FoliaSeal is a signing-and-review product per [docs/SPEC.md](/home/daekar/FoliaSeal/docs/SPEC.md): review/search/select behavior is part of the primary product flow, and it should live behind a stable core boundary rather than inside Qt event plumbing.

The user-visible behavior in this slice should stay the same. You should still be able to open a PDF, inspect embedded signatures, search document text, toggle text-selection mode, drag to select text, copy search hits or selected text, and leave text-selection mode without losing the active search summary. The main observable outcome is architectural: the shell becomes a thinner adapter over a deeper workspace-session boundary, and the tests move away from shell-owned transition details.

## Child ExecPlan Dependencies

- [ ] No child ExecPlans are planned for this slice.

## Progress

- [x] (2026-05-25 10:03 -04:00) Identified the narrow slice: introduce one deeper review/text workspace session that owns review refresh, selected-signature preservation, search navigation, text-selection mode transitions, and viewer-effect intents, while leaving signature placement and raw Qt widget rendering outside.
- [x] (2026-05-25 10:08 -04:00) Added `src/foliaseal/application/document_review_workspace.py` with immutable workspace state, transition, and viewer-effect types plus a Qt-free session that composes the existing review, search, and selection helpers.
- [x] (2026-05-25 10:09 -04:00) Rewired `src/foliaseal/presentation/qt/signing_shell.py` so the shell now renders review/text state from the workspace session and applies viewer effects at the Qt edge.
- [x] (2026-05-25 10:09 -04:00) Added direct boundary coverage in `tests/unit/test_document_review_workspace.py` for selected-signature preservation, current-hit page jumps, text-selection highlight effects, and search-state restoration after disabling selection mode.
- [x] (2026-05-25 10:10 -04:00) Fixed the first-pass regressions: removed an eager duplicate inspector call from session construction and added a selector-update guard in the shell to prevent fake-Qt review selector recursion.
- [x] (2026-05-25 10:10 -04:00) Validation passed, architecture docs were updated, and the slice is ready for commit.

## Surprises & Discoveries

- Observation: The `dev-loop` skill in this session requires subagents, but the current agent subsystem rejects new spawns because the thread limit is already reached.
  Evidence: `multi_agent_v1.spawn_agent` returned `collab spawn failed: agent thread limit reached` on 2026-05-25.

- Observation: Constructing the new workspace session with an eager review inspection caused one extra `inspect()` call during shell startup.
  Evidence: `tests/unit/test_qt_signing_shell.py::test_signing_shell_shows_document_review_summary_from_injected_inspector` failed because the fake inspector saw two calls instead of one.

- Observation: Re-rendering the review selector through fake Qt controls caused recursive `currentIndexChanged` handling unless selector updates were guarded.
  Evidence: `tests/unit/test_qt_signing_shell.py` initially failed with `RecursionError` in `_apply_document_review_workspace_state()` when `setCurrentIndex()` synchronously emitted `currentIndexChanged`.

## Decision Log

- Decision: Keep this first slice narrow by moving review/text workflow transitions behind one session boundary, but do not move signature placement into that boundary yet.
  Rationale: Signature placement shares the same viewer surface, but it belongs to the signing workflow rather than the review workflow. Pulling it in now would enlarge the slice and make compliance harder to judge.
  Date/Author: 2026-05-25 / Codex

- Decision: Continue the dev loop locally without subagents when the subagent tool is unavailable.
  Rationale: The skill requires subagents, but the environment refused new threads. The correct fallback is to preserve the same process shape locally rather than block the slice.
  Date/Author: 2026-05-25 / Codex

- Decision: Keep the new review/text boundary in the application layer rather than Qt presentation even though it returns viewer-effect intents.
  Rationale: The product requirement is UI/core separation. Returning plain viewer-effect data preserves that separation while still letting the shell remain the concrete widget adapter.
  Date/Author: 2026-05-25 / Codex

- Decision: Preserve the current mixed label behavior for the document-text card instead of normalizing it in this slice.
  Rationale: The current product behavior intentionally restores search labels after leaving text-selection mode and otherwise reflects the most recent search-or-selection action. Changing that display policy would widen the slice from architecture refactor into UX behavior change.
  Date/Author: 2026-05-25 / Codex

## Outcomes & Retrospective

The slice achieved its intended architectural goal. The shell no longer owns most of the review/text transition policy; `document_review_workspace.py` now owns review refresh, selected-signature preservation, search current-hit navigation, text-selection mode state, selection highlight intents, and restoring search state when text-selection mode is disabled.

The visible product behavior remained stable in focused tests. Search still jumps to the current hit page, text selection still produces highlight overlays and copyable text, and review selection still preserves the selected signature across refresh when labels still match.

The remaining gap is that `SigningWorkspaceWidget` still applies the viewer effects and still branches to signature placement when the review/text session does not consume a viewer drag. That is acceptable for this slice and leaves a clean next step if we later want to deepen the shared viewer-interaction boundary.

## Context and Orientation

The current production signing GUI is assembled in [src/foliaseal/presentation/qt/signing_shell.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/signing_shell.py). Inside `SigningWorkspaceWidget`, the shell currently constructs three separate review/search helpers:

- `DocumentReviewInspector` from [src/foliaseal/application/document_review.py](/home/daekar/FoliaSeal/src/foliaseal/application/document_review.py), which inspects embedded signatures and returns a plain-language summary plus per-signature drill-in text.
- `DocumentTextSearchSession` from [src/foliaseal/application/document_text_search.py](/home/daekar/FoliaSeal/src/foliaseal/application/document_text_search.py), which owns one query, all matches, current-hit navigation, and copy-current-hit behavior.
- `DocumentTextSelectionSession` from [src/foliaseal/application/document_text_selection.py](/home/daekar/FoliaSeal/src/foliaseal/application/document_text_selection.py), which owns one arbitrary viewer drag selection and the current selected text/highlight rectangles.

Those three helpers are already deeper than raw Qt widgets, but the shell still owns the transitions between them. Today the shell decides when to restore search state after leaving text-selection mode, how to preserve the selected review signature across refreshes, when to jump the viewer to the current text match, when to set or clear text highlight overlays, and whether a viewer drag means “select text” or “place signature.” That logic is concentrated in `SigningWorkspaceWidget.refresh_document_review()`, `search_document_text()`, `next_document_text_match()`, `previous_document_text_match()`, `set_document_text_selection_mode()`, `_handle_document_text_selection()`, `_sync_document_review_signature_detail()`, `_on_document_review_signature_selected()`, `_apply_document_text_state()`, `_apply_document_text_selection_state()`, and `_show_document_text_match()`.

The viewer widget itself lives in [src/foliaseal/presentation/qt/viewer_widget.py](/home/daekar/FoliaSeal/src/foliaseal/presentation/qt/viewer_widget.py). It exposes imperative widget methods such as `set_interaction_mode("signature" | "text")`, `set_text_highlight_overlay(...)`, and `clear_text_highlight_overlay()`. Those are Qt-facing effects and should stay outside the deeper core boundary. The new boundary must therefore return viewer-effect intents using repository types such as `PdfRect`, not Qt objects.

The existing shell tests in [tests/unit/test_qt_signing_shell.py](/home/daekar/FoliaSeal/tests/unit/test_qt_signing_shell.py) cover the visible behavior we must preserve. The most relevant tests are the document review selector tests, the document text search tests, the text-selection mode tests, and the search-restoration regression when text-selection mode is disabled.

## Plan of Work

Create a new application-layer module at `src/foliaseal/application/document_review_workspace.py`. Define one workspace session that composes the existing `DocumentReviewInspector`, `DocumentTextSearchSession`, and `DocumentTextSelectionSession`. The new module must expose immutable UI-facing state and explicit viewer-effect intents. The state must cover the current review summary, the current selected review signature label or detail, the current text-search state, the current text-selection state, and whether text-selection mode is enabled. The effect model must cover page jumps, interaction-mode changes, and text highlight overlay updates or clears.

Keep the module Qt-free. It may depend on repository types such as `PdfRect`, `DocumentReviewSummary`, `DocumentTextSearchState`, and `DocumentTextSelectionState`, but it must not import PySide6 or widget bindings.

Then rewire `SigningWorkspaceWidget` in `src/foliaseal/presentation/qt/signing_shell.py` to own a single instance of the new workspace session. Replace the direct review/text session calls with calls into the new workspace session. The shell must become a renderer and effect applier for this area: apply returned labels and button states to sidebar widgets, apply returned viewer effects through `self._viewer_widget`, and keep copy-to-clipboard behavior at the shell edge.

Do not change the current visible product behavior. `refresh_document_review()` must still update the review card. `search_document_text()`, `next_document_text_match()`, and `previous_document_text_match()` must still jump the viewer to the current match. `set_document_text_selection_mode(False)` must still clear highlight overlay and restore the current search summary. A viewer drag in text-selection mode must still create a selected-text highlight; a viewer drag outside text-selection mode must still fall back to signature placement behavior already owned by the signing workflow.

Add a new boundary test file for the workspace session. Cover the shell-owned transitions that are currently hardest to trust: preserving the selected signature across review refreshes, restoring search state after disabling text-selection mode, applying highlight effects when a selection exists, and emitting page-jump effects for current-hit search navigation. Update the shell tests only enough to assert the Qt wiring remains correct rather than re-testing the session internals.

Finally, update [docs/ARCHITECTURE.md](/home/daekar/FoliaSeal/docs/ARCHITECTURE.md) to record the new workspace-session boundary and the shell’s reduced responsibility for document review/text interactions.

## Concrete Steps

All commands below must be run from `/home/daekar/FoliaSeal`.

1. Add the new application-layer workspace session module and its tests.
2. Rewire `src/foliaseal/presentation/qt/signing_shell.py` to consume the session.
3. Run focused tests:

       pytest tests/unit/test_document_review_workspace.py tests/unit/test_qt_signing_shell.py

4. Run lint checks:

       ruff check src/foliaseal/application/document_review_workspace.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review_workspace.py tests/unit/test_qt_signing_shell.py

5. Run diff hygiene:

       git diff --check

6. After implementation, update this ExecPlan, update `docs/ARCHITECTURE.md`, perform the compliance review, and commit the slice.

Expected proof points include:

       tests/unit/test_document_review_workspace.py ....                        [  5%]
       tests/unit/test_qt_signing_shell.py ..................................... [100%]
       ============================== 73 passed in 8.95s ==============================

## Validation and Acceptance

Acceptance is behavioral. After this slice:

- Running the new workspace-session tests proves that document review refresh, selected-signature preservation, text-search navigation, selection-mode transitions, and viewer-effect intents are correct through one application boundary.
- Running the shell tests proves that the Qt shell still shows the same review/search/select behavior through the public widget surface.
- The regression where disabling text-selection mode restores the active search summary must still pass.
- The regression where the selected review signature stays selected across a refresh when labels still match must still pass.
- The viewer must still jump to the correct page for current text matches, and text selection must still drive highlight overlay effects.
- The shell must no longer own the preservation logic for selected review signatures or the search-state restoration rule after disabling text-selection mode.

## Idempotence and Recovery

This slice is additive and safe to retry. Re-running the test commands is idempotent. If the new workspace session causes regressions, revert only the new session wiring and keep the existing application search/selection/review helpers intact; they are already stable subcomponents and should not be removed in this slice. Avoid mixing unrelated signing-action or preview refactors into this work.

## Artifacts and Notes

The most important evidence will be:

    - the new boundary test file for the workspace session,
    - the narrowed shell tests proving only Qt wiring,
    - the focused `pytest` and `ruff` transcripts,
    - the updated architecture notes describing the new boundary.

## Interfaces and Dependencies

In `src/foliaseal/application/document_review_workspace.py`, define stable, Qt-free types for the deeper boundary. The exact names may evolve slightly during implementation, but the module must end with:

- one immutable state type representing the combined review/text workspace state,
- one immutable transition type representing the next state plus viewer effects,
- one immutable effect type representing page-jump, interaction-mode, and text-highlight intents,
- one session class that composes:
  - `DocumentReviewInspector`,
  - `DocumentTextSearchSession`,
  - `DocumentTextSelectionSession`.

The session must expose methods for:

- loading the initial state,
- refreshing document review,
- selecting one review signature by index,
- searching document text,
- moving to next/previous text match,
- toggling text-selection mode,
- handling one viewer drag for text selection,
- clearing selected text,
- returning copy text for the current search hit or current selection.

The session may depend on `PdfRect` from `src/foliaseal/application/coordinate_transform.py`, and it must return enough information for the shell to decide when to fall back to signature placement outside the review/text workflow.

Revision note: created on 2026-05-25 to drive the first refactor slice for the proposed review/text interaction hybrid boundary after the signing action coordinator extraction.

Revision note: updated on 2026-05-25 after implementation to record the completed slice, the selector-recursion fix, and the passing validation evidence.
