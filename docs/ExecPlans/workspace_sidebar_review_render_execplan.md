# Move Review And Text Rendering Into The Workspace Sidebar

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

Status: complete. The review/text rendering ownership slice is implemented, validated, and documented here as the closeout record.

## Purpose / Big Picture

This slice moved document-review and document-text widget rendering out of `SigningWorkspaceWidget` and into `SigningWorkspaceSidebar`. The visible behavior stayed the same: review headlines, signature selector state, selected-signature detail, text-search labels, selection-mode state, and button enablement all continue to render correctly, but the sidebar now owns the widget mutation for those cards.

The user-visible proof is behavior preservation with a narrower shell seam. Focused Qt tests now cover the sidebar directly, while shell smoke tests still prove that the workspace renders the same review/text state through the new ownership boundary.

## Child ExecPlan Dependencies

- [x] (2026-06-02 00:00Z) No child ExecPlans were required for this narrow rendering-ownership slice.

## Progress

- [x] (2026-06-02 00:00Z) Selected the first hybrid `1+4` top-level shell slice: move review/text render ownership from `SigningWorkspaceWidget` into `SigningWorkspaceSidebar`.
- [x] (2026-06-02 00:00Z) Implemented the sidebar-owned review/text render path and delegated the shell entrypoint to it.
- [x] (2026-06-02 00:00Z) Added focused sidebar coverage for populated review/text state, empty review state, selector recursion safety, and checkbox coverage.
- [x] (2026-06-02 00:00Z) Kept one shell smoke path so the workspace still proves the review/text render behavior end to end.
- [x] (2026-06-02 00:00Z) Ran focused validation, completed the compliance review, and confirmed that `docs/ARCHITECTURE.md` and `docs/SPEC.md` were already compliant.
- [x] (2026-06-02 00:00Z) Reviewed `README.md` for this slice and made the no-change decision because no user-facing README correction was needed.

## Surprises & Discoveries

- Observation: `SigningWorkspaceSidebar` already owned the full review/text control tree, so this was an ownership correction rather than a behavior redesign.
  Evidence: the sidebar builds `DocumentReviewControls` and `DocumentTextControls`, while `SigningWorkspaceWidget` only needed to delegate the render call once the boundary was made explicit.

- Observation: the compliance review did not find stale architecture or spec wording for this slice.
  Evidence: `docs/ARCHITECTURE.md` already described the sidebar/shell ownership split accurately enough for the implemented boundary, and `docs/SPEC.md` did not require a change.

## Decision Log

- Decision: keep `DocumentReviewWorkspaceViewerEffects` handling in the shell for this slice.
  Rationale: viewer-facing effects such as interaction mode, page jumps, and highlight overlays still belong in the shell orchestration boundary. Moving render ownership first kept the slice narrow and behavior-preserving.
  Date/Author: 2026-06-02 / Codex

- Decision: preserve the shell’s public widget aliases for review/text controls in this slice.
  Rationale: the immediate goal was to move rendering ownership, not to shrink the exported widget surface yet. Alias cleanup can happen in a later slice once the boundary is proven.
  Date/Author: 2026-06-02 / Codex

- Decision: do not change `README.md` for this closeout.
  Rationale: the compliance review found no user-facing README drift for this slice, so editing README would have been noise rather than correction.
  Date/Author: 2026-06-02 / Codex

## Outcomes & Retrospective

This slice completed the intended architectural outcome: `SigningWorkspaceSidebar` now owns the review/text widget rendering path, and `SigningWorkspaceWidget` delegates that state rendering instead of mutating the review and text cards directly. The shell still owns viewer-facing effects and higher-level orchestration around the rendered state.

The sidebar tests now provide direct coverage for the render boundary, including:

- empty review state handling
- checkbox state coverage for text-selection mode
- populated signature-selector and detail rendering
- selector recursion safety during rerenders

The focused validation passed:

- `pytest tests/unit/test_signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py` -> `93 passed`
- `ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py` -> `All checks passed!`
- `git diff --check` -> no output

The compliance review outcome was straightforward: `docs/ARCHITECTURE.md` and `docs/SPEC.md` were already compliant with this slice, so no canonical-doc edit was needed. `README.md` was reviewed and left unchanged for the same reason.

## Context and Orientation

The review/text workflow boundary lives in `src/foliaseal/application/document_review_workspace.py`. That application-layer state continues to flow through the shell as one immutable object, but `SigningWorkspaceSidebar` now owns the widget mutation for the review card and document-text card.

The shell still owns `_apply_document_review_workspace_transition(...)` and `_apply_document_review_workspace_effects(...)`, because this slice did not move viewer interaction mode changes, highlight overlays, or page-jump routing.

The key tests for the finished slice are:

- `tests/unit/test_signing_workspace_sidebar.py`
- `tests/unit/test_qt_signing_shell.py`

## Plan of Work

The implementation work is already complete and the remaining work for this document is archival only. The plan now serves as a record of what was done, what was validated, and what was intentionally left unchanged.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SigningWorkspaceSidebar` owns document-review/document-text widget mutation from `DocumentReviewWorkspaceState`
- `SigningWorkspaceWidget` delegates review/text state rendering to the sidebar instead of mutating those widgets directly
- selector recursion is still prevented during review-state rerenders
- review labels, signature selector state, detail text, text-search labels, selection-mode checkbox, and button enablement remain behaviorally unchanged
- shell viewer-effect handling for highlights, page jumps, and interaction modes remains unchanged
- focused sidebar and shell tests pass
- `docs/ARCHITECTURE.md` accurately describes the new ownership split

The acceptance criteria above were met by the focused validation run recorded in `Outcomes & Retrospective`.

## Idempotence and Recovery

This is a behavior-preserving Qt rendering refactor. Re-running the focused test commands is safe. If a future change reintroduces shell-side review/text widget mutation, the shell delegation path should be removed again rather than keeping two render owners in parallel.

## Artifacts and Notes

Important evidence captured for this slice:

- focused sidebar test results
- shell smoke test results
- the compliance finding that `docs/ARCHITECTURE.md` and `docs/SPEC.md` were already compliant
- the `README.md` no-change decision

## Interfaces and Dependencies

This slice uses the `In-process` dependency category. All state and collaborators are local Python modules plus fake-Qt widgets in the test suite.

At the end of the slice, the rendering seam looks like:

    class SigningWorkspaceSidebar:
        def apply_document_review_workspace_state(
            self,
            state: DocumentReviewWorkspaceState,
        ) -> None: ...

and the shell reduces to:

    def _apply_document_review_workspace_state(
        self,
        state: DocumentReviewWorkspaceState,
    ) -> None:
        self._sidebar.apply_document_review_workspace_state(state)

The exact helper names can shift, but the contract must remain: the sidebar owns review/text widget mutation, and the shell owns only the higher-level transition/effect routing around that rendered state.

Revision note: created on 2026-06-02 by Codex after the sidebar-owned review/text render slice was implemented and validated.
