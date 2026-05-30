# Extract A Workspace Interaction Session Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

After this slice, the shell will no longer hand-sequence the recurring interaction transitions for viewer selection, page changes, viewer refreshes, and panel-change follow-up. Those sequences will be owned by one explicit application-layer `WorkspaceInteractionSession` that composes the existing review/text workspace and viewer-interaction helpers.

The user-visible behavior should stay the same. Viewer selection should still route to either text selection or signature placement, page changes should still refresh navigation and invalidate signing readiness, and viewer refreshes should still resync placement context, overlays, preview, and signing-action state. The observable change is architectural: more of the shell’s transition-heavy interaction behavior should be testable at one boundary instead of through fake Qt widgets.

## Child ExecPlan Dependencies

- [x] (2026-05-30 02:47Z) No child ExecPlans are required for this bounded first slice.

## Progress

- [x] (2026-05-30 02:47Z) Reviewed `src/foliaseal/presentation/qt/signing_shell.py`, `src/foliaseal/application/viewer_interaction_session.py`, `src/foliaseal/application/document_review_workspace.py`, and the relevant shell tests to confirm the shell still owns too much interaction sequencing.
- [x] (2026-05-30 02:47Z) Wrote this ExecPlan and fixed the slice boundary at: selection, page-change, panel-change, and viewer-refresh sequencing only. Preview rendering and direct `set_signature_rect(...)` mutation remain outside this slice.
- [x] (2026-05-30 02:35Z) Added a workspace-interaction session boundary with explicit verbs for viewer selection, page change, document-text jump navigation, panel-change follow-up, and viewer-refresh follow-up.
- [x] (2026-05-30 02:35Z) Migrated the shell to use one transition applier instead of hand-sequencing these flows in multiple methods.
- [x] (2026-05-30 02:35Z) Added direct boundary tests for the new session and focused shell delegation tests.
- [x] (2026-05-30 02:35Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-30 02:35Z) Ran the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, then addressed the remaining architecture-doc gap.
- [x] (2026-05-30 02:35Z) Updated documentation, including this ExecPlan, to final state.
- [ ] Commit the slice as one narrow architecture change.

## Surprises & Discoveries

- Observation: `SignaturePropertiesPanel.set_signature_rect(...)` still triggers shell follow-up through its `on_change` callback, so viewer-selection placement still produces one layer of indirect shell sequencing even after introducing a higher interaction boundary.
  Evidence: `SignaturePropertiesPanel.set_signature_rect()` still ends with `self._notify_change()`, which drives `SigningWorkspaceWidget._handle_panel_change()`.

- Observation: the shell test surface needed to spy on the class boundary instead of the returned close-aware widget, because the session is owned by `SigningWorkspaceWidget`, not by the exported container widget.
  Evidence: the first focused run failed when tests tried to access `widget._workspace_interaction_session`; moving those spies to `WorkspaceInteractionSession` methods fixed the issue without code changes.

## Decision Log

- Decision: keep direct `set_signature_rect(...)` mutation out of this slice.
  Rationale: that method sits partly inside viewer/placement behavior and partly inside panel/update behavior; the immediate high-value seam is the recurring transition choreography around it.
  Date/Author: 2026-05-30 / Codex

## Outcomes & Retrospective

Implemented result:

- the shell delegates selection/page/refresh/panel transition logic to one interaction session
- direct tests cover the new boundary without driving fake Qt widgets for each transition rule
- the shell becomes a thinner effect applier for these flows
- `SPEC.md` and `ARCHITECTURE.md` behavior remains intact
- focused validation evidence:
  - `pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py -q` -> `122 passed`
  - `ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py` -> passed
  - `git diff --check` -> passed

## Context and Orientation

The shell currently repeats variants of the same pattern:

- decide which lower-level interaction helper owns an event
- update current placement context
- sync the signature overlay
- refresh the viewer and/or preview
- invalidate or reload signing-action state

That happens in:

- `_handle_viewer_selection()`
- `_handle_page_change()`
- `_handle_panel_change()`
- `refresh_viewer()`
- the document-text jump branch inside `_apply_document_review_workspace_effects()`

The lower-level helpers already exist, but the shell still owns the transition choreography between them.

## Plan of Work

First, add a new Qt-free `WorkspaceInteractionSession` above the existing `ViewerInteractionSession` and `DocumentReviewWorkspaceSession`. It should expose explicit verbs for:

- `select_in_viewer(...)`
- `change_page(...)`
- `refresh_navigation_to_page_index(...)`
- `refresh_after_panel_change()`
- `refresh_after_viewer_refresh()`

Second, migrate the shell to use that session and one transition-applier helper instead of hand-writing these sequences in multiple places.

Third, add direct boundary tests and focused shell delegation tests.

Finally, run focused validation, review compliance, update docs, and commit the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Edit the interaction session, the shell, and focused tests.

       apply_patch ... on src/foliaseal/application/workspace_interaction_session.py
       apply_patch ... on src/foliaseal/application/__init__.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on tests/unit/test_workspace_interaction_session.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

2. Run focused validation.

       pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
       ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
       git diff --check

3. Run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`. If the review finds a mismatch, update this ExecPlan, implement the fix, and repeat validation before committing.

4. Update documentation and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- viewer selection, page change, panel-change follow-up, and viewer-refresh follow-up go through `WorkspaceInteractionSession`
- the shell no longer hand-sequences those flows in multiple methods
- direct boundary tests cover the new session behavior
- focused shell tests still pass
- `docs/ARCHITECTURE.md` describes the new interaction boundary accurately

Run:

    pytest tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py

Then run:

    ruff check src/foliaseal/application/workspace_interaction_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_workspace_interaction_session.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    git diff --check

Acceptance is behavior-preserving. There is no intended product-surface change in this slice.

## Idempotence and Recovery

This is a behavior-preserving refactor in local application/Qt presentation code. It is safe to retry. If the first slice proves broader than expected, keep the interaction session and migrate one flow at a time behind it, starting with viewer selection and page changes.

## Artifacts and Notes

The most important evidence for this slice will be:

- the focused `pytest` result covering the new interaction-session tests plus affected shell tests
- a clean `ruff check`
- a clean `git diff --check`
- the updated `docs/ARCHITECTURE.md` description of the interaction boundary

These transcripts should be recorded back into this ExecPlan as work completes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the interaction seam should look approximately like:

    class WorkspaceInteractionSession(Protocol):
        def select_in_viewer(...) -> WorkspaceInteractionTransition: ...
        def change_page(...) -> WorkspaceInteractionTransition: ...
        def refresh_navigation_to_page_index(...) -> WorkspaceInteractionTransition: ...
        def refresh_after_panel_change(...) -> WorkspaceInteractionTransition: ...
        def refresh_after_viewer_refresh(...) -> WorkspaceInteractionTransition: ...

Revision note: Created on 2026-05-30 by Codex for the first implementation slice of the workspace-interaction hybrid.
