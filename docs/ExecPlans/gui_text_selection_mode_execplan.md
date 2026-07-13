# GUI text selection mode

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a user will be able to intentionally enter document text-selection mode, see the cursor and UI state change, select text from the PDF, and copy that selection. This closes a direct spec gap and removes one of the most confusing “looks interactive but does nothing” experiences in the current GUI.

## Child ExecPlan Dependencies

- [x] (2026-07-08 13:56Z) This child has no further child ExecPlans. Keep the slice focused on text-selection mode, cursor/state feedback, and copy behavior.

## Progress

- [x] (2026-07-08 13:56Z) Wrote this ExecPlan from the live GUI walkthrough and the current text-selection controls in the sidebar and viewer code.
- [x] (2026-07-08 14:16Z) Recorded user product guidance that the normal-versus-text-selection mode switch should be an icon-labeled button, ideally in a toolbar if one exists or is introduced, with `Edit` menu fallback as the secondary location if no suitable toolbar home is available.
- [x] (2026-07-10 18:58Z) Confirmed through an explorer-light review that the text-selection backend path already works; the remaining slice is primarily product-surface work around command placement, cursor feedback, and visible mode signaling.
- [x] (2026-07-10 18:58Z) Chose the product-facing mode host for this slice: add a checkable `Edit` menu command and demote the sidebar checkbox to a hidden state mirror instead of introducing a brand-new toolbar in the same slice.
- [x] (2026-07-10 19:08Z) Added a checkable `Edit > Text selection mode` action at the app-frame level, extended the live shell port with `set_document_text_selection_mode(...)`, and reset the action state when workspaces are opened or cleared.
- [x] (2026-07-10 19:08Z) Updated the viewer to change cursor shape between signature-placement and text-selection modes, and hid the old sidebar checkbox while keeping it as an internal state mirror for the existing review-bridge render path.
- [x] (2026-07-10 19:14Z) Fixed the hidden-checkbox re-entry hazard found during compliance review by suppressing callback echo during programmatic checkbox sync in `signing_workspace_sidebar.py`.
- [x] (2026-07-10 19:14Z) Added focused tests for menu/action wiring, cursor feedback, hidden-checkbox behavior, and preservation of existing text-selection flows.
- [x] (2026-07-10 19:14Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan with the implemented behavior after compliance review.
- [x] (2026-07-10 19:41Z) Validated the repaired text-selection flow in the live GUI and incorporated follow-up UX fixes: single-click clear, toolbar-hosted select/copy actions, and correct selection/copy alignment.
- [x] (2026-07-11 00:12Z) Replaced the temporary text toolbar buttons with repo-owned SVG icons, verified tooltips, re-ran focused tests, and revalidated the live GUI with the user.

## Surprises & Discoveries

- Observation: the existing control is already product-suspicious even before the functional bug, because it uses a passive checkbox for what is really a viewer interaction mode.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_sidebar.py` labels the mode control as `Select text`, implemented as a checkbox next to copy/clear buttons.

- Observation: the user explicitly wants the mode switch to read like a classic desktop command, not like a form checkbox embedded in a review panel.
  Evidence: the live review feedback was that mode switching should use an icon-labeled button and may belong in a toolbar or, failing that, an `Edit` menu between `File` and `Settings`.

- Observation: the actual selection/copy/clear pipeline is already present; the slice does not need a new document-text backend.
  Evidence: explorer-light review on 2026-07-10 traced the working selection path through `document_review_workspace.py`, `signing_workspace_review_bridge.py`, and the existing focused tests in `tests/unit/test_qt_signing_shell.py` and `tests/unit/test_document_review_workspace.py`.

- Observation: there is no existing toolbar host in either the signing shell or the app frame.
  Evidence: explorer-light review found only `File` and `Settings` menus in `src/foliaseal/presentation/qt/app_frame.py` and no `QToolBar` in the signing-shell composition path.

## Decision Log

- Decision: leave room to replace the checkbox with a stronger affordance if the implementation work shows that a toggle button or segmented mode control is clearer.
  Rationale: the frozen spec cares about working text selection and desktop clarity, not about preserving the current checkbox shape.
  Date/Author: 2026-07-08 / Codex

- Decision: treat a toolbar-hosted icon-labeled mode button as the preferred target interaction, with an `Edit` menu command as the fallback if no suitable toolbar location exists in the current shell.
  Rationale: this matches the user’s explicit desktop-UX preference and better reflects an interaction mode change than a passive checkbox in the `Document text` panel.
  Date/Author: 2026-07-08 / Codex

- Decision: use a checkable `Edit` menu command as the primary user-facing control in this slice, and keep the sidebar checkbox only as a hidden state mirror for existing shell state/render wiring.
  Rationale: there is no current toolbar host to reuse without broadening scope, while the app frame can add `Edit` cleanly and route the toggle through the existing shell port/runtime path.
  Date/Author: 2026-07-10 / Codex

## Outcomes & Retrospective

The slice is complete and manually validated. Text-selection mode now has both a top-level desktop command through `Edit > Text selection mode` and compact viewer-toolbar actions for mode toggle and copy. The viewer cursor changes with the active interaction mode, single-click clears the current selection, and the old sidebar checkbox/buttons no longer act as the primary user surface. The selection/copy backend path stayed intact; the work remained a product-surface repair rather than a deeper application-layer rewrite.

The main correction after the first pass came from the compliance review: keeping the hidden checkbox as a pure mirror required suppressing callback re-entry during state sync. A second correction came from live GUI review, which showed that coordinate conversion and selection rendering had to be repaired before the mode could be called usable. After those fixes and the final icon pass, the implementation remained narrow and aligned with the existing review/text workflow architecture.

## Context and Orientation

Document text review in FoliaSeal is split conceptually into two adjacent features. Search lets the user find occurrences of text and move between matches. Text selection lets the user directly select arbitrary text in the viewer and copy it. The current shell exposes both in the `Document text` panel built by `src/foliaseal/presentation/qt/signing_workspace_sidebar.py`, while the viewer-side logic and selection overlays live in `src/foliaseal/presentation/qt/viewer_widget.py` and the application/infra text-selection boundaries described in `docs/ARCHITECTURE.md`.

The live review found that the `Select text` checkbox does not visibly change the cursor and does not enable obvious text selection from the user’s perspective. `docs/SPEC.md` explicitly requires that the V1 GUI support selecting and copying document text. This plan fixes both the behavior and the UX signaling.

## Plan of Work

Start by tracing the current text-selection mode path from the `Document text` sidebar controls through the shell runtime and into the viewer widget. Identify where the interaction mode is stored, where cursor shape could be changed, and how selected-text state is surfaced back to the shell for enablement of copy and clear actions. The likely touch points are `signing_workspace_sidebar.py`, `signing_workspace_runtime.py`, `viewer_widget.py`, and whichever selection adapter currently backs the application-layer `document_text_selection` boundary.

Choose a clear product behavior before coding. The user must be able to tell when the mouse is in text-selection mode instead of signature-placement mode. Prefer an icon-labeled button in a toolbar location if the current shell can support it cleanly. If a toolbar home is not yet available without derailing the slice, add a classic `Edit` menu command as the fallback location rather than preserving the current checkbox. Record the chosen behavior in the `Decision Log`.

Implement the viewer-side mode feedback first: cursor shape, interaction-mode state, and any necessary suppression of signature-placement interactions while text-selection mode is active. Then implement or repair the actual selection path so dragging across text produces a selection that can be copied and cleared through the existing controls. The copy and clear buttons must reflect real selection state rather than remain disabled forever or appear active without effect.

Add focused tests that prove the mode changes, selection state transitions, and copy/clear enablement. Manual validation must use the live GUI on a representative PDF containing selectable text.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the relevant shell, runtime, and viewer files.

       sed -n '380,470p' src/foliaseal/presentation/qt/signing_workspace_sidebar.py
       sed -n '1,260p' src/foliaseal/presentation/qt/signing_workspace_runtime.py
       sed -n '1,260p' src/foliaseal/presentation/qt/viewer_widget.py

2. Trace the current text-selection boundary and test coverage.

       rg -n "text_selection|select_mode|copy_selected|clear_selected|interaction mode" src/foliaseal tests/unit

3. Implement the chosen mode control and viewer feedback, then run focused tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_viewer_widget.py

4. Validate manually in the live GUI.

       .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf

   Expected result: entering text-selection mode is obvious, the cursor changes appropriately, dragging selects text, and the copy/clear controls act on real selection state.

## Validation and Acceptance

Acceptance is behavioral. In the live GUI, the user must be able to enter a clear text-selection mode, visibly get a text-selection cursor or equivalent explicit mode cue, drag over text in the PDF, and then use `Copy selection` and `Clear selection` successfully. Signature-placement interactions must not continue to fire while text-selection mode is active.

Run the focused unit tests around the touched shell and viewer code. Add or update tests so they demonstrate the before/after difference in mode feedback and selection behavior.

## Idempotence and Recovery

Treat this slice as a behavior repair, not a broad redesign. If the first attempt at wiring real text selection reveals that the current checkbox control is the root of the confusion, it is acceptable to replace it in the same slice as long as the scope stays on text-selection mode itself. If selection cannot be made reliable without deeper viewer rework, stop, document the blocker in this plan, and split a narrower follow-up rather than burying the issue.

## Artifacts and Notes

The motivating spec requirement is:

    docs/SPEC.md:86

The user-facing failure evidence is:

    .tmp/gui_ux_review_2026-07-08.md

## Interfaces and Dependencies

Use the existing text-selection application boundary rather than inventing new selection logic in the shell. The final GUI must expose a clear interaction-mode control, a viewer-side mode cue, and working copy/clear behavior. Keep the viewer and shell in sync through the existing runtime/session boundaries where possible.

Revision note: 2026-07-11 / Codex
Updated the plan after live validation, follow-up UX repairs, and the final icon-toolbar polish so the living document now reflects the completed slice instead of the initial menu-only first pass.
