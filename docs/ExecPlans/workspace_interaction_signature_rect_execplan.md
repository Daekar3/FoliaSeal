# Decouple Signature-Rect Application From Panel Change Callbacks

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, `SigningWorkspaceWidget` will no longer rely on `SignaturePropertiesPanel`'s generic `on_change` callback to finish internal signature-rectangle application flows. Direct shell rect-setting and viewer-selection placement will explicitly apply their follow-up transition through `WorkspaceInteractionSession`, which keeps the remaining viewer/placement seam on the same explicit interaction boundary as the prior slice.

The visible behavior should stay the same. Dragging in the viewer should still place a visible-signature rectangle, direct shell rect-setting should still refresh placement context and signing readiness, and preview/overlay state should remain correct. The change is architectural: the shell no longer hides this behavior behind a panel callback.

## Child ExecPlan Dependencies

- [x] (2026-05-30 13:38Z) No child ExecPlans are required for this bounded follow-up slice.

## Progress

- [x] (2026-05-30 13:38Z) Reviewed `src/foliaseal/presentation/qt/signing_shell.py`, the workspace-interaction boundary, and focused shell tests to confirm that signature-rect application still depended on `SignaturePropertiesPanel._notify_change()`.
- [x] (2026-05-30 13:38Z) Wrote this ExecPlan and fixed the slice boundary at: internal signature-rect application only. Preview rendering, direct workflow mutation outside `set_signature_rect(...)`, and broader shell/sidebar composition remain out of scope.
- [x] (2026-05-30 13:43Z) Added a non-notifying `SignaturePropertiesPanel.set_signature_rect(...)` path for shell-internal callers while preserving default notifying behavior for external callers.
- [x] (2026-05-30 13:43Z) Routed `SigningWorkspaceWidget.set_signature_rect(...)` and workspace-interaction transitions through the non-notifying path, then explicitly applied the correct follow-up transition from `WorkspaceInteractionSession`.
- [x] (2026-05-30 13:44Z) Added focused shell tests proving direct rect-setting uses `refresh_after_panel_change()` explicitly and viewer-selection placement no longer reaches that path indirectly.
- [x] (2026-05-30 13:45Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-30 13:46Z) Ran the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, updated docs, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: The prior interaction-session slice left one indirect shell sequencing path behind, because `WorkspaceInteractionTransition.signature_rect` still called back into `SignaturePropertiesPanel.set_signature_rect(...)`, and that method always triggered `on_change`.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` currently ends `SignaturePropertiesPanel.set_signature_rect(...)` with `self._notify_change()`, and `_handle_panel_change()` delegates to `WorkspaceInteractionSession.refresh_after_panel_change()`.

## Decision Log

- Decision: Preserve `notify=True` as the default behavior on `SignaturePropertiesPanel.set_signature_rect(...)`.
  Rationale: only shell-internal rect application should stop depending on the callback; direct external callers such as focused tests and the Phase 3 harness should not silently lose their existing behavior in this narrow slice.
  Date/Author: 2026-05-30 / Codex

## Outcomes & Retrospective

Implemented result:

- internal signature-rect application in the shell no longer depends on the panel's generic `on_change` callback
- direct shell rect-setting now explicitly applies `WorkspaceInteractionSession.refresh_after_panel_change()`
- viewer-selection placement applies its returned rect without looping back into that same panel-change path
- default notifying behavior remains available for direct panel callers such as focused tests and the Phase 3 harness
- focused validation evidence:
  - `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py -q` -> `124 passed`
  - `ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py` -> passed
  - `git diff --check` -> passed

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` contains two relevant layers. `SignaturePropertiesPanel` is the visible-signature editor and preview adapter. `SigningWorkspaceWidget` is the higher shell that owns the viewer, review/text workspace, signing action coordinator, and `WorkspaceInteractionSession`.

The recent workspace-interaction refactor introduced `src/foliaseal/application/workspace_interaction_session.py`, which returns plain transition data for viewer selection, page changes, document-text jumps, panel-change follow-up, and viewer-refresh follow-up. Most of the shell now applies those transitions explicitly. One exception remains: internal rect application still reaches `WorkspaceInteractionSession.refresh_after_panel_change()` indirectly by calling `SignaturePropertiesPanel.set_signature_rect(...)`, which always emits its generic `on_change` callback.

This slice removes that last internal callback dependency without changing the public shell behavior.

## Plan of Work

First, change `SignaturePropertiesPanel.set_signature_rect(...)` in `src/foliaseal/presentation/qt/signing_shell.py` to accept a keyword-only `notify` flag that defaults to `True`. The method should still mutate the workflow, toggle placement controls, and reload panel state exactly as before. It should only emit `_notify_change()` when `notify` is true.

Second, update the shell-owned rect application paths in the same file. `SigningWorkspaceWidget.set_signature_rect(...)` should call the non-notifying panel path and then explicitly apply `WorkspaceInteractionSession.refresh_after_panel_change()`. `_apply_workspace_interaction_transition(...)` should also use the non-notifying rect path when a transition already carries the intended follow-up behavior.

Third, add focused shell tests in `tests/unit/test_qt_signing_shell.py` that prove the new sequencing. One test should spy on `WorkspaceInteractionSession.refresh_after_panel_change()` during `widget.set_signature_rect(...)`. Another should prove viewer-selection placement still works without calling `refresh_after_panel_change()` indirectly.

Finally, run focused validation, update `docs/ARCHITECTURE.md`, record final outcomes here, and commit the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Edit the shell, tests, and docs.

       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/workspace_interaction_signature_rect_execplan.md

2. Run focused validation.

       pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py -q
       ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
       git diff --check

3. Review compliance against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`. If a mismatch appears, update the code or docs, rerun validation, and record the fix here.

4. Commit the implementation once the slice is clean.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- direct shell rect-setting explicitly uses `WorkspaceInteractionSession.refresh_after_panel_change()`
- viewer-selection placement does not rely on the panel callback to reach that same follow-up path
- direct panel callers still keep their default notify behavior
- focused shell tests pass
- `docs/ARCHITECTURE.md` describes the remaining workspace-interaction seam accurately

Run:

    pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py -q

Then run:

    ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    git diff --check

Acceptance is behavior-preserving. There is no intended product-surface change in this slice.

## Idempotence and Recovery

This is a narrow, behavior-preserving refactor inside the Qt shell. It is safe to retry. The `notify` parameter is additive and defaults to the existing behavior, so backing out the internal non-notifying callers is straightforward if a regression appears.

## Artifacts and Notes

The most important evidence for this slice will be:

- a focused shell test proving `set_signature_rect(...)` explicitly uses `refresh_after_panel_change()`
- a focused shell test proving viewer-selection placement does not call that path indirectly
- a clean `pytest` run for the affected interaction/setup modules
- a clean `ruff check`
- a clean `git diff --check`

These transcripts should be recorded back into this ExecPlan as work completes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the relevant signatures should look approximately like:

    class SignaturePropertiesPanel:
        def set_signature_rect(
            self,
            signature_rect: SignatureRect | None,
            *,
            notify: bool = True,
        ) -> None: ...

    class SigningWorkspaceWidget:
        def set_signature_rect(...) -> SignatureRect: ...
        def _apply_workspace_interaction_transition(...) -> None: ...

Revision note: Created on 2026-05-30 by Codex for the follow-up slice that removes remaining internal signature-rect callback coupling after the initial workspace-interaction refactor.

Revision note: Updated on 2026-05-30 by Codex after implementation and validation to record the finished non-notifying rect path, focused shell coverage, and clean compliance state.
