# Extract The Signing Workspace Runtime Controller

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice keeps the live signing workspace behavior the same while moving the last broad event-routing and lifecycle junction out of `src/foliaseal/presentation/qt/signing_shell.py`. After this change, the workspace composition helper should receive one typed shell-internal runtime/controller instead of today’s callback bundle, and the shell should stop being the place where viewer selection, page changes, panel changes, interaction-plan dispatch, placement-context application, overlay sync, and shell-edge error/status handling are all replayed separately. Users should still be able to drag a signature rectangle, search/select text, refresh the viewer, sign, and run the Phase 3 harness exactly as before.

## Child ExecPlan Dependencies

- [x] (2026-06-05 20:18Z) No child ExecPlans are required for this bounded orchestration-extraction slice.

## Progress

- [x] (2026-06-05 20:10Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the remaining callback-heavy orchestration bundle into a typed shell-internal runtime/controller.
- [x] (2026-06-05 20:14Z) Re-read the current shell callback cluster, the composition-builder signature, and the focused shell/app-frame/harness tests that cover viewer routing and current-shell behavior.
- [x] (2026-06-05 20:31Z) Added `signing_workspace_runtime.py` and moved viewer/panel/page event routing, interaction-plan dispatch, placement-context application, overlay sync, and shell-edge error/status handling into `SigningWorkspaceRuntime`.
- [x] (2026-06-05 20:37Z) Updated `signing_workspace_composition.py` so it accepts one typed runtime/controller, wires the viewer/panel/sidebar callback family through it, and binds the runtime to the sessions, bridges, viewer widget, and result label created during composition.
- [x] (2026-06-05 20:43Z) Kept the live shell methods and compatibility seams stable while removing the old `_handle_*`, placement-context, overlay-sync, and shell-edge routing helpers from `signing_shell.py`.
- [x] (2026-06-05 20:49Z) Added focused runtime/controller tests in `tests/unit/test_qt_signing_workspace_runtime.py` and kept the existing shell subset green.
- [x] (2026-06-05 20:56Z) Ran focused validation with the runtime/controller tests, shell subset, app-frame smoke subset, `ruff check`, and `git diff --check`.
- [x] (2026-06-05 21:02Z) Completed the required architectural/spec compliance review; the only follow-up was doc reconciliation for `docs/ARCHITECTURE.md` and this ExecPlan.
- [x] (2026-06-05 21:09Z) Updated documentation to final state and closed the slice.

## Surprises & Discoveries

- Observation: The remaining shallow seam is now the callback-heavy composition boundary rather than another surface or widget-ownership cluster.
  Evidence: `build_signing_workspace_composition(...)` still receives a large shell-owned callback bundle for viewer selection, page changes, panel changes, placement-context application, interaction-plan dispatch, and shell-edge error/status forwarding even after the recent composition/surface extractions.
- Observation: the cleanest extraction point was a bindable runtime/controller, not a constructor-only dependency object.
  Evidence: the runtime needs collaborators that do not exist until `build_signing_workspace_composition(...)` finishes constructing the workspace sessions, bridges, viewer widget, and result label, so the slice bound those collaborators after composition instead of reintroducing a wide callback bundle.
- Observation: the first compliance gap after implementation was documentation drift only.
  Evidence: the compliance review matched the code and tests to the intended runtime/controller boundary, and only flagged stale ownership text in `docs/ARCHITECTURE.md` plus incomplete closeout state in this ExecPlan.

## Decision Log

- Decision: extract one typed runtime/controller rather than introducing a generic event bus or command framework.
  Rationale: the remaining problem is one coherent shell-local orchestration concept, not a need for a repo-wide dispatch system. A concrete runtime/controller is the smallest deep-module move that fits the current code.
  Date/Author: 2026-06-05 / Codex

- Decision: keep the live shell widget contract and module-level compatibility seams stable in this slice.
  Rationale: this tracer bullet is about internal orchestration ownership. Changing the app-frame port, harness compatibility surface, or shell monkeypatch seams at the same time would widen the review surface for little architectural gain.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

The slice landed as a narrow behavior-preserving extraction. `SigningWorkspaceRuntime` now owns the shell-local runtime/controller responsibilities for viewer selection, viewer errors/interactions, panel changes, page changes, review-signature page-jump follow-up, interaction-plan dispatch, placement-context application, signature-overlay sync, and shell-edge error/status handling. `build_signing_workspace_composition(...)` now accepts that runtime as one typed collaborator, wires the viewer/panel/sidebar callback family through it, and binds it to the sessions, bridges, viewer widget, and result label created during composition. `signing_shell.py` no longer owns the old `_handle_*` orchestration cluster inline.

The public shell behavior stayed stable for the focused app-frame and shell callers exercised in this slice. The main architectural gain is that the last broad shell-local callback family is now explicit and named instead of being spread across `signing_shell.py` helpers and a wide composition-builder signature.

Focused validation evidence:

- `.venv/bin/python -m pytest tests/unit/test_qt_signing_workspace_runtime.py` -> `5 passed`
- `.venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'viewer_selection_uses_workspace_interaction_session_entrypoint or page_change_uses_workspace_interaction_session_entrypoint or refresh_viewer_uses_workspace_interaction_session_entrypoint or refresh_viewer_reports_refresh_error_through_interaction_bridge or set_signature_rect_uses_explicit_panel_refresh_transition'` -> `5 passed, 89 deselected`
- `.venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'save_as_action_enables_after_open_and_routes_to_current_shell or choose_open_pdf or reopens_signed_output_from_shell_callback'` -> `2 passed, 23 deselected`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/signing_workspace_runtime.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` -> clean
- `git diff --check` -> clean

Retrospective: the bind/install step was the right compromise for this slice. It kept the runtime concrete and typed, avoided inventing a generic event bus, and let the shell keep its stable outer surface while the composition builder shed the last wide orchestration callback family.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` has already been narrowed substantially. Constructor-time assembly now lives in `src/foliaseal/presentation/qt/signing_workspace_composition.py`; the narrow production port lives in `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py`; the broad harness/testing access lives in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`; and signing-action, review/text, interaction-plan, and properties-panel behavior all have their own helpers.

What still remains broad is the shell-owned runtime/orchestration cluster. In this plan, “runtime/controller” means the shell-local object that should own:

- viewer-selection routing into `WorkspaceInteractionSession.select_in_viewer(...)`;
- panel-change routing into `WorkspaceInteractionSession.refresh_after_panel_change()`;
- page-change routing into `WorkspaceInteractionSession.change_page(...)`;
- viewer-error and viewer-interaction forwarding into the shell error/status edges;
- interaction-plan execution through `SigningWorkspaceInteractionBridge`;
- placement-context application back into `SigningDraftWorkflow`;
- signature-overlay sync against the concrete viewer widget;
- sign-result text updates for shell-level error reporting.

Today those responsibilities are spread across:

- `src/foliaseal/presentation/qt/signing_shell.py`, especially the `_handle_viewer_selection`, `_handle_viewer_error`, `_handle_viewer_interaction`, `_handle_panel_change`, `_handle_page_change`, `_sync_signature_overlay`, `_apply_placement_context_result`, `_apply_workspace_interaction_plan`, `_emit_error`, and `_set_sign_result_text` helpers;
- `src/foliaseal/presentation/qt/signing_workspace_composition.py`, whose builder still takes a large callback bundle for those shell-owned behaviors.

The key files for this slice are:

- `src/foliaseal/presentation/qt/signing_workspace_runtime.py`, the new helper module to add in this slice;
- `src/foliaseal/presentation/qt/signing_shell.py`, which should stop owning the broad `_handle_*` cluster and instead construct/install the runtime;
- `src/foliaseal/presentation/qt/signing_workspace_composition.py`, which should receive the typed runtime instead of the large event-routing callback bundle;
- `tests/unit/test_qt_signing_shell.py`, which already covers viewer-selection/page-change/refresh routing and should remain the main shell smoke proof;
- `tests/unit/test_qt_signing_workspace_runtime.py`, a new focused runtime/controller boundary suite to add in this slice;
- `docs/ARCHITECTURE.md`, which currently describes the shell as the remaining orchestration/lifecycle boundary and must be updated if this cluster moves.

This slice must stay narrow. It may move the remaining shell-local orchestration into a typed runtime/controller, update focused tests, and reconcile docs. It must not redesign the production port, the compatibility surface, the app-frame contract, or the harness/service surfaces that were just stabilized.

## Plan of Work

First, add a new shell-local helper module, `src/foliaseal/presentation/qt/signing_workspace_runtime.py`, that owns the remaining shell orchestration cluster. That module should expose a typed class with explicit methods for the concrete viewer/panel/page callbacks and the lifecycle/effect helpers they require. It should be constructed by the shell and later bound to the collaborators created during composition.

Second, edit `src/foliaseal/presentation/qt/signing_workspace_composition.py` so the composition builder accepts the runtime/controller as one collaborator instead of taking the current callback family for viewer selection, viewer errors, viewer interactions, panel changes, page changes, interaction-plan dispatch, placement-context application, and overlay sync.

Third, edit `src/foliaseal/presentation/qt/signing_shell.py` so it creates the runtime/controller, passes it into the composition builder, and removes the old `_handle_*` orchestration helpers that the runtime now owns. The shell should keep the public methods and the compatibility seams stable.

Fourth, add focused unit tests for the runtime/controller and keep the existing shell/app-frame subset green. The runtime tests should verify routing and shell-edge behavior directly without going through the entire shell widget.

Finally, run focused validation, perform the required compliance review, reconcile `docs/ARCHITECTURE.md` and this ExecPlan, and commit the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the runtime/controller helper and migrate the shell orchestration cluster.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_runtime.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_composition.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Add focused tests for the extracted runtime/controller and adjust shell tests only where the assertion point changes.

       apply_patch ... on tests/unit/test_qt_signing_workspace_runtime.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

3. Run focused validation.

       .venv/bin/python -m pytest tests/unit/test_qt_signing_workspace_runtime.py
       .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'viewer_selection_uses_workspace_interaction_session_entrypoint or page_change_uses_workspace_interaction_session_entrypoint or refresh_viewer_uses_workspace_interaction_session_entrypoint or refresh_viewer_reports_refresh_error_through_interaction_bridge or set_signature_rect_uses_explicit_panel_refresh_transition'
       .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'save_as_action_enables_after_open_and_routes_to_current_shell or choose_open_pdf or reopens_signed_output_from_shell_callback'
       .venv/bin/ruff check src/foliaseal/presentation/qt/signing_workspace_runtime.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the remaining shell-local orchestration cluster lives in a dedicated typed runtime/controller helper;
- `signing_workspace_composition.py` receives that runtime/controller instead of the current broad callback family for viewer/panel/page routing and interaction-plan/effect helpers;
- the public shell widget contract stays stable for the app frame, focused shell tests, and the compatibility surface;
- viewer-selection, page-change, refresh-viewer, and explicit signature-rect behavior still work the same;
- `docs/ARCHITECTURE.md` accurately describes the runtime/controller as the owner of the remaining shell-local orchestration cluster.

Run:

    .venv/bin/python -m pytest tests/unit/test_qt_signing_workspace_runtime.py
    .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'viewer_selection_uses_workspace_interaction_session_entrypoint or page_change_uses_workspace_interaction_session_entrypoint or refresh_viewer_uses_workspace_interaction_session_entrypoint or refresh_viewer_reports_refresh_error_through_interaction_bridge or set_signature_rect_uses_explicit_panel_refresh_transition'
    .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'save_as_action_enables_after_open_and_routes_to_current_shell or choose_open_pdf or reopens_signed_output_from_shell_callback'

Then run:

    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_workspace_runtime.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The user-visible signing workspace, app-frame wiring, and harness behavior should not change; the architectural improvement is that the last broad shell-local orchestration junction is now explicit and isolated.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the runtime/controller needs collaborators that are created later during composition, prefer a bind/install step on the runtime rather than pushing the callback bundle back into the composition builder. Do not recover by introducing a generic command bus; keep the extracted object concrete and typed.

If shrinking the shell unexpectedly requires changing the production port or compatibility surface, stop and defer that to a later slice rather than widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new shell-local runtime/controller module with focused unit tests;
- a visibly smaller `signing_shell.py` orchestration cluster;
- a reduced callback surface in `build_signing_workspace_composition(...)`;
- focused shell tests proving the live behavior stayed intact.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the boundary should look approximately like:

    class SigningWorkspaceRuntime:
        def bind(... ) -> None: ...
        def on_viewer_selection(self, pdf_rect: PdfRect) -> None: ...
        def on_viewer_error(self, message: str) -> None: ...
        def on_viewer_interaction(self, name: str) -> None: ...
        def on_panel_change(self) -> None: ...
        def on_page_change(self, page_number: int) -> None: ...
        def on_document_review_signature_selected(self, index: int) -> None: ...
        def apply_workspace_interaction_plan(self, plan: WorkspaceInteractionPlan) -> None: ...
        def apply_placement_context(self, placement_context: SignaturePlacementContext | None) -> None: ...
        def sync_signature_overlay(self) -> None: ...
        def emit_error(self, message: str) -> None: ...

The exact method names can vary slightly, but the composition builder must take one typed runtime/controller instead of the current large family of shell-owned orchestration callbacks.

Revision note: Created on 2026-06-05 by Codex for the next signing-workspace hybrid `4+5` tracer bullet after the shell-surface compatibility split.
