# Split document review and document text workspace state into smaller boundaries

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

Status: complete. The review/text state split is implemented in code, validated by the focused test suite, and this file now serves as the closeout record.

## Purpose / Big Picture

The review-and-text portion of the signing workspace now exposes smaller state boundaries instead of one combined `DocumentReviewWorkspaceState` bag that the shell unpacks field by field. A user opening a PDF sees the same document review card, the same document-text card, the same search and selection behavior, and the same viewer drag routing, but the review/text session returns one explicit review-card state and one explicit document-text state. The shell consumes those smaller states directly instead of reaching into one mixed object for both concerns.

The visible behavior stayed the same. Users can still inspect signatures, change the selected signature, search text, toggle text-selection mode, drag to select text, clear text selection, and restore the active search summary when text-selection mode is turned off. The outcome was architectural: a smaller workspace-state boundary that moved the shell one step closer to the proposed hybrid of a narrower workspace port plus stable caller ergonomics.

## Child ExecPlan Dependencies

- [x] (2026-06-01T02:08:12Z) `docs/ExecPlans/document_review_workspace_session_execplan.md` completed first so review/text workflow transitions already lived behind one Qt-free session.
- [x] (2026-06-01T02:08:12Z) `docs/ExecPlans/workspace_interaction_session_execplan.md` completed first so the shell already delegated recurring interaction sequencing above the review/text session.
- [x] (2026-06-01T02:08:12Z) `docs/ExecPlans/signing_action_sidebar_render_execplan.md` completed first so the app-frame seam and signing-action render ownership were already narrowed and out of scope for this slice.
- [x] (2026-05-31T00:00:00Z) No child ExecPlan was needed for this slice; the work stayed within the existing review/text state split and did not require a follow-up plan.

## Progress

- [x] (2026-06-01T02:08:12Z) Completed the required `explorer-light` audit for the next hybrid `1+3` slice and fixed the target on shrinking the review/text workspace state boundary instead of reopening `app_frame.py`.
- [x] (2026-06-01T02:08:12Z) Reviewed the current combined state usage in `src/foliaseal/application/document_review_workspace.py`, `src/foliaseal/application/workspace_interaction_session.py`, and `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-06-01T02:08:12Z) Wrote this ExecPlan before implementation.
- [x] (2026-05-31T00:00:00Z) Added focused regression coverage for the smaller state boundary and verified the split against the existing unit tests.
- [x] (2026-05-31T00:00:00Z) Introduced the immutable `DocumentReviewCardState` and `DocumentTextWorkspaceState` types inside `src/foliaseal/application/document_review_workspace.py`.
- [x] (2026-05-31T00:00:00Z) Rewired the shell and focused tests to consume `state.review` and `state.document_text` directly.
- [x] (2026-05-31T00:00:00Z) Ran validation, updated `docs/ARCHITECTURE.md`, completed the compliance review, and recorded the outcome here.

## Surprises & Discoveries

- Observation: the next caller-facing seam was not in `app_frame.py`.
  Evidence: the required `explorer-light` audit found that `AppFrameShellPort` plus `_with_current_shell_port(...)` already provided the desired caller ergonomics, while the remaining architectural concentration was the mixed review/text state consumed by `SigningWorkspaceWidget`.

- Observation: the final implementation path was the nested review/text state split, not a broader shell port.
  Evidence: the completed code exposes `DocumentReviewCardState` and `DocumentTextWorkspaceState`, and the shell consumes `state.review` and `state.document_text` directly.

## Decision Log

- Decision: keep this slice focused on the review/text workspace state model rather than adding a broader shell-wide command/snapshot port.
  Rationale: the proposed hybrid architecture was still directionally correct, but the narrowest next move was to shrink an existing state boundary that the shell already consumed heavily. That improved navigability and testability without reopening every shell method at once.
  Date/Author: 2026-06-01 / Codex

- Decision: preserve current review/text behavior and public shell/app-frame contracts.
  Rationale: this was a boundary deepening refactor. The acceptance bar was unchanged behavior with a better state model, not UX churn or a new top-level port.
  Date/Author: 2026-06-01 / Codex

- Decision: represent review-card state and document-text state as explicit immutable types in the application layer.
  Rationale: the current `DocumentReviewWorkspaceState` mixed two concepts. Splitting it into named sub-state types gave the shell a smaller interface and made tests more precise without introducing Qt dependencies into the application layer.
  Date/Author: 2026-06-01 / Codex

- Decision: close this plan as documentation-only follow-up once the split was verified in code.
  Rationale: the implementation was already complete in the working tree, so the remaining work was to bring the architecture and exec-plan prose back into sync with the actual nested state boundary.
  Date/Author: 2026-05-31 / Codex

- Decision: do not change `README.md` for this closeout.
  Rationale: no concrete user-facing inconsistency was found; the mismatch was in architecture documentation, not in the user-facing description.
  Date/Author: 2026-05-31 / Codex

## Outcomes & Retrospective

The slice completed the intended architectural outcome: `DocumentReviewWorkspaceState` now composes `DocumentReviewCardState` and `DocumentTextWorkspaceState`, and the shell renders the review card from `state.review` and the document-text card from `state.document_text` directly. The public behavior stayed the same: signature inspection, search, text-selection mode, drag selection, clearing text, and search-summary restoration still work as before.

The focused tests for `tests/unit/test_document_review_workspace.py`, `tests/unit/test_workspace_interaction_session.py`, and `tests/unit/test_qt_signing_shell.py` passed, which confirmed that the new nested state boundary did not break the interaction session or the Qt shell. No compatibility shim was needed beyond the new state composition itself.

No README change was necessary because the user-facing behavior did not become inconsistent; the stale material was limited to the architecture and exec-plan prose. A later slice could still decide whether to move more widget mutation behind a sidebar helper, but that is independent of this completed state split.

## Context and Orientation

The review-and-text workflow boundary lives in `src/foliaseal/application/document_review_workspace.py`. It now exposes two immutable nested state types, `DocumentReviewCardState` and `DocumentTextWorkspaceState`, inside the wrapper `DocumentReviewWorkspaceState`. The review-card state carries the review summary, signature label list, selected signature detail, and selector enablement. The document-text state carries the search state, selection state, selection-mode flag, display source, and the status/detail strings for the text card.

The shell consumes that nested state in `src/foliaseal/presentation/qt/signing_shell.py`, inside `_apply_document_review_workspace_state(...)`. That method reads `state.review` and `state.document_text` directly when mutating the concrete document-review and document-text widgets, which removed the old flat field unpacking and made the shell boundary match the application boundary.

`src/foliaseal/application/workspace_interaction_session.py` composes the review/text session with the viewer-interaction session. Its transitions continue to carry `DocumentReviewWorkspaceTransition`, so this slice kept that interaction seam behavior-preserving while updating the state shape.

The most relevant tests are:

- `tests/unit/test_document_review_workspace.py`, which proves the session behavior itself;
- `tests/unit/test_workspace_interaction_session.py`, which builds fake `DocumentReviewWorkspaceTransition` values and exercises the new state shape;
- `tests/unit/test_qt_signing_shell.py`, which verifies that the shell still renders review/text behavior correctly;
- `tests/unit/test_qt_app_frame.py`, which remained untouched because the public shell contract did not change.

The earlier review/text session ExecPlan at `docs/ExecPlans/document_review_workspace_session_execplan.md` established the transition boundary. This slice built on that work by shrinking the state surface exposed by that session, not by replacing the session.

## Plan of Work

The implementation work added the two immutable sub-state types in `src/foliaseal/application/document_review_workspace.py`, changed `_build_state()` to construct them, and kept the existing behavior rules intact: selected-signature preservation, search-hit page jumps, text-selection-mode restore behavior, and copy-state enablement all still behaved the same.

`src/foliaseal/presentation/qt/signing_shell.py` now consumes the nested state directly. `_apply_document_review_workspace_state(...)` reads `state.review` and `state.document_text` and mutates the existing Qt widgets from those smaller units. No compatibility layer was needed.

The focused tests in `tests/unit/test_document_review_workspace.py`, `tests/unit/test_workspace_interaction_session.py`, and `tests/unit/test_qt_signing_shell.py` were updated to assert against the nested state shape and passed after the split. `tests/unit/test_qt_app_frame.py` did not need to change because the public shell contract stayed stable.

`docs/ARCHITECTURE.md` was updated after the code was green so the repository documentation now names the new `DocumentReviewCardState` / `DocumentTextWorkspaceState` split and explains that the shell consumes `state.review` and `state.document_text` directly.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Start with focused tests before editing to establish a baseline:

    pytest tests/unit/test_document_review_workspace.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py

During the red-green loop, rerun the most relevant subsets as needed. A likely narrow loop was:

    pytest tests/unit/test_document_review_workspace.py tests/unit/test_workspace_interaction_session.py -q
    pytest tests/unit/test_qt_signing_shell.py -k "document_review or document_text or search_state or selection_mode" -q

After implementation stabilized, run the full focused validation:

    pytest tests/unit/test_document_review_workspace.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py
    ruff check src/foliaseal/application/document_review_workspace.py src/foliaseal/application/workspace_interaction_session.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_document_review_workspace.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py
    git diff --check

Then run the required compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`. `docs/SCHEMAS.md` should only be revisited if the slice accidentally changed a persistent schema boundary, which it did not.

Expected success signal at the end was that the focused tests passed, lint was clean, and `git diff --check` printed nothing. That signal was observed for the completed slice.

## Validation and Acceptance

Acceptance was behavioral. The product behavior remained unchanged while the review/text state model became smaller and more explicit.

This slice was accepted when all of the following were true, and the focused test suite confirmed them:

- the review/text session returned explicit smaller state units instead of one flat mixed bag;
- the shell rendered the review card and the text card from those smaller state units;
- selected-signature preservation across refresh still worked;
- search-hit page jumps still worked;
- leaving text-selection mode still restored the active search summary and cleared highlights;
- viewer drag routing still gave the review/text session first chance before signature placement behavior resumed.

The proof came from the focused test commands in `## Concrete Steps` and the updated architecture documentation.

## Idempotence and Recovery

This slice was a behavior-preserving in-process refactor. Re-running the test commands was safe. The implementation did not need temporary compatibility properties on `DocumentReviewWorkspaceState`; the nested-state boundary was adopted directly.

No data migration or destructive operation was involved. The safe rollback path would still be to revert only the state-shape change while keeping any new boundary tests that accurately describe intended behavior.

## Artifacts and Notes

For reference, the pre-change mixed-state seam in `src/foliaseal/application/document_review_workspace.py` was:

    @dataclass(frozen=True)
    class DocumentReviewWorkspaceState:
        review_summary: DocumentReviewSummary
        review_signature_labels: tuple[str, ...]
        selected_review_signature_index: int | None
        selected_review_signature_label: str | None
        selected_review_signature_detail: str
        review_selector_enabled: bool
        text_search_state: DocumentTextSearchState
        text_selection_state: DocumentTextSelectionState
        text_selection_mode_enabled: bool
        document_text_display_source: DocumentTextDisplaySource
        document_text_status_text: str
        document_text_detail_text: str

The pre-change shell consumer in `src/foliaseal/presentation/qt/signing_shell.py` was the single `_apply_document_review_workspace_state(...)` method that mutated both review and text widgets from that one state object.

These were the primary targets for this slice.

## Interfaces and Dependencies

The finished state in `src/foliaseal/application/document_review_workspace.py` defines two stable, Qt-free immutable state types in addition to the existing transition/effects types:

- one review-card state type that owns review summary and signature-selection rendering facts;
- one document-text state type that owns search/selection rendering facts.

`DocumentReviewWorkspaceState` is now a composition of those smaller state types instead of a flat list of both concerns. `DocumentReviewWorkspaceTransition` and `WorkspaceInteractionTransition` continue to use the workspace state as before, and callers consume the nested sub-state objects rather than flat fields.

Dependencies remain `In-process`. The application layer may continue to depend on `DocumentReviewSummary`, `DocumentTextSearchState`, `DocumentTextSelectionState`, and `PdfRect`, but it remains Qt-free. The shell keeps its concrete widget mutation role for this slice, but it now renders from the smaller state boundary.

Revision note: created on 2026-06-01 after the required `explorer-light` audit for the next hybrid `1+3` slice, then closed out on 2026-05-31 after the nested-state split was verified and the architecture documentation was brought back into sync with the code.
