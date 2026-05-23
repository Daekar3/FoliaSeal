# Extract production signing-workspace sidebar

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [.agents/skills/write-execplan/PLANS.md](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the production GUI should stop looking like “the harness shell with a real launcher.” Opening a PDF in `foliaseal gui` should present a document-centric workspace with the viewer on the left and a dedicated production sidebar on the right, rather than stacking the `Signing flow`, `Document review`, and `Document text` cards across the top like a staging rail. The observable result is a meaningfully different product layout without removing the current review/search/signing capabilities needed for `docs/SPEC.md`.

## Child ExecPlan Dependencies

- [x] (2026-05-23 17:51Z) No child ExecPlans are required for this first production-sidebar slice.

## Progress

- [x] (2026-05-23 17:51Z) Audited the current production shell and confirmed that the app frame is thin while `SigningWorkspaceWidget` still owns the harness-era staged control rail.
- [x] (2026-05-23 17:51Z) Captured the intended refactor slice in this ExecPlan before editing code.
- [x] (2026-05-23 17:58Z) Extracted `signing_workspace_sidebar.py` to own the production sidebar chrome for status/actions, document review, document text, and the scrolled properties panel host.
- [x] (2026-05-23 17:59Z) Recomposed `SigningWorkspaceWidget` to use a document-left / sidebar-right layout instead of the old top staged rail.
- [x] (2026-05-23 18:00Z) Kept review, text-search, output-path, and sign-result capabilities intact behind the new sidebar boundary.
- [x] (2026-05-23 18:01Z) Updated focused shell tests to assert the new composition through stable behavior plus a small number of meaningful structural checks.
- [x] (2026-05-23 18:05Z) Ran validation and completed local `docs/` closeout updates. Commit remains the final remaining step.

## Surprises & Discoveries

- Observation: The visible production problem is not that harness-specific buttons leaked into `foliaseal gui`; it is that the real app still uses the same shell composition pattern as the harness, just without the harness capture controls.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` loads `build_qt_signing_shell(...)` directly, and `SigningWorkspaceWidget` still adds `Signing flow`, `Document review`, and `Document text` cards above the main viewer/properties row.

- Observation: The smallest effective product-facing change did not require deleting review/search/sign behavior; moving those controls into the sidebar was enough to break the old harness-era visual structure while keeping the current feature set.
  Evidence: Focused shell tests stayed green after recomposition, and the top-level fake-Qt layout now contains one main row with two peers instead of multiple support cards stacked above the viewer.

## Decision Log

- Decision: Treat the current top-row `Signing flow` / `Document review` / `Document text` composition as production-layout debt, not just internal code debt.
  Rationale: The user-visible complaint is about the app feeling like the old harness. Simply moving code into smaller helpers without changing composition would not change the product.
  Date/Author: 2026-05-23 / Codex

- Decision: Keep existing review/search/signing functionality in this slice and change composition first.
  Rationale: `docs/SPEC.md` still needs those capabilities. The right first move is to stop presenting them in a harness-era staged rail while preserving behavior.
  Date/Author: 2026-05-23 / Codex

- Decision: Let the new sidebar own the scrolled signature-properties host in addition to the action/review/text panels.
  Rationale: Keeping the properties scroll outside the sidebar would have preserved the old split between “real editing area” and “extra support chrome.” Pulling the properties host into the sidebar makes the visible right column a cohesive product surface.
  Date/Author: 2026-05-23 / Codex

## Outcomes & Retrospective

This slice achieved the intended visual change without cutting features. The production shell now reads as a document workspace with a right-side sidebar, not as an acceptance-style rail above the viewer. The new `signing_workspace_sidebar.py` boundary reduces some composition pressure inside `signing_shell.py`, but the shell is still a large orchestration module. The next architectural move should target the remaining workspace orchestration responsibilities rather than re-opening preview layout again.

## Context and Orientation

The real top-level GUI now launches from `src/foliaseal/presentation/qt/app_frame.py`, but once a PDF is opened the central widget comes from `src/foliaseal/presentation/qt/signing_shell.py`. The main production class in that module is `SigningWorkspaceWidget`. Right now it still builds the workspace by creating three read-only/support cards (`Signing flow`, `Document review`, `Document text`), placing them at the top of the shell, and then placing the viewer and signature-properties editor below them in a second row.

That structure made sense while the shell was primarily an engineering acceptance surface because the top cards summarized workflow state and inspection details for repeated manual QA runs. In the production app, though, it reads as staging UI rather than a cohesive desktop workspace. The product still needs the same underlying behavior:

- placing a signature on the document,
- configuring signing properties,
- reviewing existing signatures,
- searching/selecting document text,
- choosing an output path,
- signing,
- reopening the signed output.

The relevant files are:

- `src/foliaseal/presentation/qt/signing_shell.py` for the current shell composition and stable shell surface.
- `src/foliaseal/presentation/qt/app_frame.py` for how the production app hosts the shell.
- `tests/unit/test_qt_signing_shell.py` for fake-Qt shell behavior coverage.
- `docs/ARCHITECTURE.md` for the current statement that `signing_shell.py` is still a large concentration point and that future deepening should target workspace composition.

## Plan of Work

Create a new Qt presentation helper module that owns the non-viewer sidebar chrome for the production shell. This helper should own the action/status panel, the document-review panel, and the document-text panel, plus the stable widgets/callback wiring those sections need. It should hide widget construction and section layout from `SigningWorkspaceWidget`, but it should not reimplement signing semantics or review logic.

Then update `SigningWorkspaceWidget` so its primary visible structure becomes a two-pane composition: the viewer on the left and a right-side sidebar containing the signature-properties editor plus the extracted production support panels. The flow-summary labels should move into the action/status area instead of being their own top-level rail. Keep the existing public shell behavior surface intact as much as possible so callers and tests do not need a broad migration.

Finally, update tests to verify the new composition through stable behavior and a few structural assertions that are actually meaningful to the production layout, rather than preserving the old “top rail above main row” assumptions.

## Concrete Steps

From `/home/daekar/FoliaSeal`, implement and validate this slice with:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_sidebar.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Manual acceptance on a desktop session after code changes:

    .venv/bin/foliaseal gui --pdf-path "/path/to/example.pdf"

Expected observable behavior: the viewer occupies the left side; the right side is a cohesive production sidebar rather than top-stacked workflow/review/search cards above the viewer.

## Validation and Acceptance

Acceptance is behavioral:

- `pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` passes.
- The shell still supports review, text search/selection, choose-output, sign, and reopen behavior through the existing surface.
- The visible composition is no longer the old staged rail above the main row.
- `ruff check ...` and `git diff --check` pass.

## Idempotence and Recovery

The edits are safe to repeat. If the new sidebar boundary causes test regressions, the shell can be restored by keeping the old public method surface and moving composition incrementally instead of changing behavior and layout simultaneously. The slice should not change persisted data or signing semantics.

## Artifacts and Notes

Key post-change evidence:

    pytest tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    93 passed

Focused structural proof in the fake-Qt shell test now asserts:

    - the top-level shell layout has one main row
    - the main row has exactly two peers: viewer and sidebar
    - the properties scroll and action buttons belong to the sidebar container

## Interfaces and Dependencies

At the end of this slice, the code should expose:

- a new production-sidebar helper module under `src/foliaseal/presentation/qt/` that owns sidebar widget construction and refresh surfaces for action/status, document review, and document text;
- `SigningWorkspaceWidget` as the orchestrator that composes viewer + properties panel + sidebar and routes workflow events into those boundaries;
- unchanged or minimally changed shell public methods for review/text/sign interactions so callers and tests can keep using the shell through its stable surface.

Dependencies are `Local-substitutable`: the refactor is entirely in-process Qt composition plus fake Qt bindings in tests.

Revision note: created on 2026-05-23 to drive the first production-shell composition refactor that removes the harness-era staged control rail from the real GUI. Updated after implementation to record the completed sidebar extraction, validation evidence, and the decision to let the sidebar own the scrolled properties host.
