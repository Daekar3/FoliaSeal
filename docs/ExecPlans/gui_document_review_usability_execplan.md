# GUI document review usability

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user who opens a PDF in the FoliaSeal GUI will be able to discover page navigation immediately from visible controls rather than by guessing keyboard shortcuts. They will be able to see what page they are on, move forward and backward through the document, and keep the review flow anchored to standard desktop expectations. This matters because the signing experience cannot be trusted if the document review experience is already failing at the first basic task.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice narrow to visible page-review controls and related status only.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan from the live GUI walkthrough and the current viewer/signing shell code.
- [x] (2026-07-08 14:29Z) Added visible previous/next page controls and a `Page X of Y` status label to the `Document review` panel in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`.
- [x] (2026-07-08 14:29Z) Reused the existing viewer workflow state as the source of truth and wired the sidebar buttons through the existing viewer widget navigation entrypoints from `src/foliaseal/presentation/qt/signing_workspace_composition.py`.
- [x] (2026-07-08 14:29Z) Added focused page-navigation coverage to `tests/unit/test_qt_signing_shell.py` and extended the fake viewer widget to support the new navigation path.
- [x] (2026-07-08 14:29Z) Ran focused validation: `99 passed` in `tests/unit/test_qt_signing_shell.py`; `ruff check` passed for the touched files.
- [x] (2026-07-10 18:42Z) Reworked the first-pass placement after live user feedback: page navigation now belongs in a compact toolbar above the left document viewer rather than inside the right `Document review` card.
- [x] (2026-07-10 18:44Z) Re-ran focused validation after the left-pane toolbar relocation and editable page-jump wiring: `99 passed` in `tests/unit/test_qt_signing_shell.py`; focused `page_navigation` coverage and `ruff check` both passed.
- [x] (2026-07-10 18:44Z) Reconciled `docs/ARCHITECTURE.md` with the final viewer-toolbar placement and rechecked the slice against `docs/SPEC.md` page-navigation requirements.
- [x] (2026-07-10 18:55Z) Validated the live GUI manually with the user against `artifacts/preview_sweep_assets/sweep_fixture.pdf`; follow-up sizing feedback was incorporated and revalidated in the live app.

## Surprises & Discoveries

- Observation: the repository already has page navigation behavior in the viewer, but it is effectively hidden from the GUI user.
  Evidence: `src/foliaseal/presentation/qt/viewer_widget.py` handles `PageDown`, `PageUp`, `Home`, and `End`, while the live user could not find any page-navigation controls in the app itself.

- Observation: the truthful page-status label could not safely depend on button clicks alone because keyboard navigation already changes the live page outside the sidebar.
  Evidence: the viewer widget already performs hidden keyboard navigation internally, so the slice added a post-navigation interaction signal (`navigation_changed`) and a shell-local page-status refresh callback instead of inventing duplicate page state.

- Observation: moving visible page navigation into the review card solved discoverability but still failed the expected desktop UX because the controls were detached from the document they affect.
  Evidence: the live user review on 2026-07-10 explicitly rejected the right-pane placement and specified a compact top-of-viewer toolbar with previous, editable page number, total-pages readout, and next.

## Decision Log

- Decision: keep this plan limited to visible page navigation and page status, not zoom control redesign or broader document-review changes.
  Rationale: the immediate spec failure is discoverability of page navigation. Expanding the slice would make it harder to land and verify.
  Date/Author: 2026-07-08 / Codex

- Decision: place the new page controls in the existing `Document review` panel rather than adding a new toolbar or viewer chrome in this slice.
  Rationale: the sidebar review panel is already the narrowest visible shell seam for document-review affordances, and using it kept the slice product-visible without expanding into a larger frame-layout redesign.
  Date/Author: 2026-07-08 / Codex

- Decision: supersede the first-pass right-pane placement and move page navigation into a compact toolbar above the left document viewer.
  Rationale: page navigation is a viewer-local affordance, and the user needs it physically adjacent to the document surface to match standard PDF desktop expectations and support direct page-number entry.
  Date/Author: 2026-07-10 / Codex

- Decision: keep `ViewerWorkflow.session.current_page` and `page_count` as the only source of truth for page status.
  Rationale: the code already had hidden keyboard navigation and shell-local logical-page helpers; adding a second page tracker would have created drift risk immediately.
  Date/Author: 2026-07-08 / Codex

## Outcomes & Retrospective

This slice is complete. The final implementation uses a compact toolbar above the viewer with previous/next arrows, editable page-number entry, and total-pages readout, all backed by `ViewerWorkflow.session.current_page` and `page_count` as the only page-state source of truth. A small follow-up tightened the arrow-button and page-field widths after live user review so the toolbar reads like standard desktop viewer chrome instead of a stretched form row.

The remaining work is outside this slice: text-selection mode, staged workflow guidance, certificate/preset clarity, and broader shell reduction still remain in their own child plans.

## Context and Orientation

The live GUI is launched through `src/foliaseal/__main__.py` and the top-level frame in `src/foliaseal/presentation/qt/app_frame.py`. When a PDF is opened, the app constructs a signing workspace whose left side is the document viewer and whose right side is the sidebar built in `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`. The actual page rendering and keyboard navigation behavior live in `src/foliaseal/presentation/qt/viewer_widget.py` and the viewer workflow collaborators beneath it.

Today, the user can zoom with the mouse wheel and can likely navigate pages with hidden keyboard bindings, but visible page-navigation controls have either been absent or misplaced. `docs/SPEC.md` explicitly requires that V1 support page navigation as part of the GUI workflow. This plan fixes the discoverability and placement gap without changing deeper signing behavior.

## Plan of Work

Add a small, clearly visible page-navigation cluster as a compact toolbar above the left document viewer rather than burying it in the right sidebar or an unrelated settings area. The safest implementation is to reuse the existing viewer navigation behavior instead of inventing a second page-state source.

Inspect `src/foliaseal/presentation/qt/signing_workspace_composition.py`, `src/foliaseal/presentation/qt/signing_shell.py`, and `src/foliaseal/presentation/qt/viewer_widget.py` to determine the narrowest point where a viewer-local toolbar can be added. Define explicit UI controls for previous page, editable current page number, total-pages readout, and next page. If the current workspace already has access to the page count and logical page index through `ViewerWorkflow` or `SigningWorkspaceRuntime`, use those values directly; do not create a duplicate page tracker.

Once the controls exist, wire them to the existing viewer navigation entrypoints and derive status from `ViewerWorkflow.session.current_page` and `page_count`. The implementation must ensure that clicking the new buttons updates the rendered page and status text, and that keyboard navigation continues to keep the visible status in sync. Use a narrow shell-local refresh callback for the label instead of adding a second page-state model.

Update the focused tests under `tests/unit/` that cover the shell/viewer widget so the new controls are asserted explicitly, including Enter-to-jump behavior from the page input. Add a manual validation step using `foliaseal gui` on `artifacts/preview_sweep_assets/sweep_fixture.pdf`.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the relevant viewer and sidebar modules.

       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_sidebar.py
       sed -n '1,260p' src/foliaseal/presentation/qt/viewer_widget.py
       sed -n '1,240p' src/foliaseal/presentation/qt/signing_shell.py

2. Implement visible page controls and status in the workspace UI, then update or add focused tests.

       rg -n "page_next|page_previous|logical_page_index|current_page|page_count" src/foliaseal/presentation/qt tests/unit

3. Run the focused test suites you change.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_viewer_widget.py

   Current evidence from the first pass:

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py
       99 passed in 11.78s

       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_sidebar.py src/foliaseal/presentation/qt/signing_workspace_runtime.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/viewer_widget.py tests/unit/test_qt_signing_shell.py
       All checks passed!

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: visible page controls are present above the document viewer, and the current page can be changed with either the arrow buttons or direct page-number entry without needing hidden keyboard knowledge.

## Validation and Acceptance

Acceptance is behavioral. Launch the GUI on `artifacts/preview_sweep_assets/sweep_fixture.pdf`. The user should immediately see page navigation affordances above the document viewer and a truthful current-page readout. Clicking next and previous should visibly change the page and keep the status text truthful. Typing a valid page number and pressing Enter should jump there. Keyboard page navigation, if still supported, must continue to keep the same visible status in sync.

Run the focused Qt unit tests that cover the touched shell/sidebar/viewer code. They should fail before the new controls or wiring exist and pass after.

## Idempotence and Recovery

This slice should be implemented additively. If an initial control placement feels wrong, move the controls without changing the underlying navigation wiring. If the manual validation reveals duplicated page state or drift between the label and the rendered page, stop and consolidate around the existing viewer workflow state rather than adding yet another page tracker.

## Artifacts and Notes

The motivating spec requirement is:

    docs/SPEC.md:83

The key evidence of the current failure is:

    .tmp/gui_ux_review_2026-07-08.md

## Interfaces and Dependencies

Use the existing viewer workflow and shell-local runtime where possible. The implementation should expose explicit previous-page and next-page actions, editable page-number entry, and a truthful total-pages readout in the workspace UI. Avoid creating a second navigation model. Prefer updating existing shell surface dataclasses if new controls need to be exposed for testing.

Revision note: 2026-07-08 / Codex
Created this plan as the first document-usability slice after the live GUI review showed that page navigation existed in code but not in a discoverable product form.
