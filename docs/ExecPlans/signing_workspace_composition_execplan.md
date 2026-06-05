# Extract The Signing Workspace Composition Cluster

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice keeps the signing workspace behavior unchanged while moving the remaining constructor-time composition cluster out of `src/foliaseal/presentation/qt/signing_shell.py` and into a dedicated helper module. After this change, `build_qt_signing_shell()` should still return the same concrete shell widget and the app frame and tests should still drive the same live contract, but `SigningWorkspaceWidget.__init__` should stop being the place where the whole session graph, bridge graph, and viewer/sidebar assembly are wired together inline.

The user-visible outcome is stability, not new product behavior: opening a PDF, using `Save As...`, dragging a signature rectangle, refreshing the viewer, and searching document text should all behave the same. The observable improvement is architectural: a smaller shell constructor with a dedicated owner for workspace assembly.

## Child ExecPlan Dependencies

- [x] (2026-06-05 04:34Z) No child ExecPlans are required for this bounded composition-extraction slice.

## Progress

- [x] (2026-06-05 04:32Z) Completed the required `explorer-light` audit and fixed the next slice to extracting the remaining workspace composition/assembly cluster from `SigningWorkspaceWidget.__init__`.
- [x] (2026-06-05 04:34Z) Re-read the live shell constructor, the current architecture debt note, and the focused shell/app-frame tests covering bootstrap ordering, interaction entrypoints, and current-shell routing.
- [x] (2026-06-05 09:54Z) Added `signing_workspace_composition.py` and moved the session graph, bridge graph, viewer/sidebar assembly, and bootstrap ordering out of `signing_shell.py` while preserving the same live shell contract.
- [x] (2026-06-05 10:00Z) Restored the `build_qt_pdf_viewer_widget` compatibility export so the focused shell tests could continue monkeypatching the viewer-construction seam through `signing_shell.py`.
- [x] (2026-06-05 10:06Z) Confirmed that no focused test assertions needed to move; the existing shell and app-frame subsets already proved the composition boundary stayed behaviorally stable.
- [x] (2026-06-05 10:22Z) Ran focused validation with the shell subset, app-frame subset, `ruff check`, and `git diff --check`.
- [x] (2026-06-05 10:22Z) Completed the required architectural/spec compliance review and reconciled the remaining doc drift plus stale duplicated panel-helper block in `signing_shell.py`.
- [x] (2026-06-05 10:22Z) Updated documentation to final state and prepared the slice for commit.

## Surprises & Discoveries

- Observation: The focused shell tests still patch `signing_shell_module.build_qt_pdf_viewer_widget`, so moving viewer construction directly into the composition helper broke the existing compatibility seam until the builder was injected and the shell-level export was preserved.
  Evidence: The focused shell subset failed until `build_signing_workspace_composition(...)` accepted `viewer_widget_builder` and `signing_shell.py` restored `build_qt_pdf_viewer_widget = _build_qt_pdf_viewer_widget`.

- Observation: `signing_shell.py` still carried a dead duplicate of the panel-local helper block even after `SignaturePropertiesPanel` moved into `signing_workspace_properties_panel.py`.
  Evidence: The compliance review found `SignaturePresetControls`, `CertificateConfigurationControls`, `PreviewControls`, `_QtCertificatePassphrasePrompter`, and the related preview/control helper functions still defined in `signing_shell.py` with no remaining live references outside that stale block.

## Decision Log

- Decision: keep the concrete shell widget, shell methods, and app-frame-facing contract stable in this slice.
  Rationale: this tracer bullet is about who assembles the collaborator graph, not about changing how the app frame or tests call into the live shell.
  Date/Author: 2026-06-05 / Codex

- Decision: extract composition before attempting any deeper shell-orchestration redesign.
  Rationale: the remaining live concentration is the constructor graph itself; smaller method-level refactors would not materially reduce the shell’s review scope, while a deeper policy rewrite would be too large for one dev-loop.
  Date/Author: 2026-06-05 / Codex

- Decision: preserve the shell-level `build_qt_pdf_viewer_widget` compatibility export and inject the viewer builder into the new composition helper instead of moving that import fully behind the helper boundary.
  Rationale: the current focused shell tests intentionally monkeypatch the builder through `signing_shell.py`, and this slice is about constructor ownership rather than changing the observable patch surface for tests.
  Date/Author: 2026-06-05 / Codex

- Decision: remove the stale duplicate panel-helper block from `signing_shell.py` instead of carrying it forward as compatibility baggage.
  Rationale: the helpers now live in `signing_workspace_properties_panel.py`, the shell no longer references the duplicate definitions, and leaving them in place would keep the composition slice architecturally noncompliant even though behavior stayed stable.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

This slice landed as a behavior-preserving extraction. `src/foliaseal/presentation/qt/signing_workspace_composition.py` now owns the constructor-time session graph, bridge graph, viewer/sidebar assembly, and bootstrap ordering for one workspace instance, while `SigningWorkspaceWidget.__init__` now stays focused on the outer shell state, root widget/layout creation, composition installation, and lifecycle edge behavior.

Focused validation passed:

- `.venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'shows_state_driven_flow_summary or viewer_selection_uses_workspace_interaction_session_entrypoint or page_change_uses_workspace_interaction_session_entrypoint or refresh_viewer_uses_workspace_interaction_session_entrypoint or refresh_viewer_applies_ordered_workspace_effects or refresh_viewer_reports_refresh_error_through_interaction_bridge or set_signature_rect_uses_explicit_panel_refresh_transition'` -> `7 passed, 86 deselected`
- `.venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'choose_open_pdf or reopens_signed_output_from_shell_callback or save_as_action_enables_after_open_and_routes_to_current_shell'` -> `2 passed, 23 deselected`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_composition.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py` -> clean
- `git diff --check` -> clean

The first compliance pass found two mismatches: `docs/ARCHITECTURE.md` still described constructor-time composition as shell-owned, and `signing_shell.py` still carried stale duplicated properties-panel helpers. Those were reconciled in-place without widening the slice or requiring a child ExecPlan.

Final state is compliant with `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell.py` is still the composition root for the production signing workspace. Recent slices already extracted most of the coherent behavior clusters:

- `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` owns the Qt properties-panel implementation.
- `src/foliaseal/presentation/qt/signing_workspace_review_bridge.py` owns review/text bridge rendering and transition application.
- `src/foliaseal/presentation/qt/signing_workspace_interaction_bridge.py` owns `WorkspaceInteractionPlan` execution.
- `src/foliaseal/presentation/qt/signing_workspace_action_bridge.py` owns shell-facing signing-action dialog and state glue.
- `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` owns the compatibility export block and the app-frame/test-facing shell verbs.

What still remains concentrated in `SigningWorkspaceWidget.__init__` is the constructor-time composition cluster. In this plan, “composition cluster” means the code that:

- creates the viewer interaction session, document review workspace, and workspace interaction session;
- constructs the viewer widget, properties panel, sidebar, bridges, shell surface, and signing-action coordinator/boundary graph;
- wires callbacks between those pieces;
- assembles the viewer/sidebar layout;
- runs the initial bootstrap ordering for refresh, review load, and signing-action state load.

The key files for this slice are:

- `src/foliaseal/presentation/qt/signing_shell.py`, which should stay the outer Qt entrypoint and concrete shell widget class;
- `src/foliaseal/presentation/qt/signing_workspace_composition.py`, the new helper module to add in this slice;
- `tests/unit/test_qt_signing_shell.py`, which already proves state-driven bootstrap, interaction entrypoints, refresh behavior, and explicit signature-rect follow-up behavior;
- `tests/unit/test_qt_app_frame.py`, which proves the top-level frame still routes `Save As...` and related current-shell flows through the live shell;
- `docs/ARCHITECTURE.md`, which currently states that `signing_shell.py` still concentrates top-level workspace composition and orchestration and must be updated if this slice lands.

This slice must stay narrow. It may move composition/assembly ownership and the docs/tests needed to prove that move, but it must not redesign the app-frame contract, the shell-surface contract, the bridges, the sidebar, the properties panel, or the underlying setup/review/signing policies.

## Plan of Work

First, add a new shell-local helper module under `src/foliaseal/presentation/qt/` that owns workspace composition. That helper should build the session graph, viewer widget, properties panel, sidebar, bridges, shell surface, and the viewer/sidebar row layout, and it should expose a typed result object that the shell can install and bootstrap.

Second, edit `src/foliaseal/presentation/qt/signing_shell.py` so `SigningWorkspaceWidget.__init__` computes only the few truly outer-edge values it should still own, constructs the close-aware root widget and outer layout, delegates the composition build to the new helper, installs the returned collaborators, and then triggers the returned bootstrap sequence. The shell should remain the Qt edge for viewer callbacks, error/status emission, overlay syncing, and the public shell methods.

Third, keep focused tests green. Prefer not to widen test changes unless the new helper boundary needs a small ownership-specific assertion.

Finally, run the focused validation commands, do the required compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`, update docs to describe the new composition helper, and record the final result here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the composition helper module and migrate constructor assembly.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_composition.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py

2. Update focused tests only if the extraction changes what should be asserted directly.

       apply_patch ... on tests/unit/test_qt_signing_shell.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Run focused validation.

       .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'shows_state_driven_flow_summary or viewer_selection_uses_workspace_interaction_session_entrypoint or page_change_uses_workspace_interaction_session_entrypoint or refresh_viewer_uses_workspace_interaction_session_entrypoint or refresh_viewer_applies_ordered_workspace_effects or refresh_viewer_reports_refresh_error_through_interaction_bridge or set_signature_rect_uses_explicit_panel_refresh_transition'
       .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'choose_open_pdf or reopens_signed_output_from_shell_callback or save_as_action_enables_after_open_and_routes_to_current_shell'
       .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_composition.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
       git diff --check

4. Run the required compliance review, reconcile docs if needed, and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- a dedicated shell-local helper owns the session graph, bridge graph, viewer/sidebar assembly, and bootstrap ordering instead of `SigningWorkspaceWidget.__init__` keeping that cluster inline;
- `build_qt_signing_shell()` still returns the same concrete shell widget and the shell/app-frame contract stays unchanged;
- viewer selection, page change, refresh-viewer, explicit signature-rect application, and current-shell save-as routing still behave the same;
- the already-extracted helper modules remain the owners of their existing responsibilities and are not widened again in this slice;
- `docs/ARCHITECTURE.md` accurately describes the new composition helper and tightens the remaining `signing_shell.py` debt note.

Run:

    .venv/bin/python -m pytest tests/unit/test_qt_signing_shell.py -k 'shows_state_driven_flow_summary or viewer_selection_uses_workspace_interaction_session_entrypoint or page_change_uses_workspace_interaction_session_entrypoint or refresh_viewer_uses_workspace_interaction_session_entrypoint or refresh_viewer_applies_ordered_workspace_effects or refresh_viewer_reports_refresh_error_through_interaction_bridge or set_signature_rect_uses_explicit_panel_refresh_transition'
    .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py -k 'choose_open_pdf or reopens_signed_output_from_shell_callback or save_as_action_enables_after_open_and_routes_to_current_shell'

Then run:

    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/signing_workspace_composition.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. No user-facing GUI flow, labels, or shell/widget contract should change in this slice.

## Idempotence and Recovery

This is a behavior-preserving extraction. It is safe to retry. If the composition helper becomes awkward for one or two callbacks, keep the callback signatures stable and centralize the awkward wiring inside the helper rather than spreading assembly logic back through the shell. Do not recover by leaving half the graph build inline in the shell and half in the helper long-term; one composition helper should remain the owner at the end of the slice.

If the extraction unexpectedly requires changing the app-frame port, the shell-surface contract, or the behavior ownership of the panel/bridge helpers, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

The most important evidence for this slice will be:

- a new shell-local composition module with a typed result object;
- a visibly smaller `SigningWorkspaceWidget.__init__` in `src/foliaseal/presentation/qt/signing_shell.py`;
- focused shell/app-frame tests proving the bootstrap order and current-shell routing stayed intact.

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, `src/foliaseal/presentation/qt/signing_workspace_composition.py` should expose one typed result object plus one builder function. The exact names may vary slightly, but the boundary should look approximately like:

    @dataclass(frozen=True)
    class SigningWorkspaceComposition:
        viewer_interaction_session: ViewerInteractionSession
        document_review_workspace: DocumentReviewWorkspaceSession
        workspace_interaction_session: WorkspaceInteractionSession
        viewer_widget: Any
        properties_panel: SignaturePropertiesPanel
        sidebar: SigningWorkspaceSidebar
        review_bridge: SigningWorkspaceReviewBridge
        signing_action_coordinator: SigningActionCoordinator
        signing_action_boundary: SigningActionBoundary
        action_bridge: SigningWorkspaceActionBridge
        interaction_bridge: SigningWorkspaceInteractionBridge
        shell_surface: SigningWorkspaceShellSurface
        main_row: Any

        def bootstrap(self) -> None: ...

    def build_signing_workspace_composition(...) -> SigningWorkspaceComposition: ...

The builder may still accept shell-owned callback functions and live app-settings accessors. The point of the slice is ownership and concentration reduction, not changing the behavior model.

Revision note: Created on 2026-06-05 by Codex for the next signing-workspace hybrid `4+5` tracer bullet after the shell-surface extraction slice. Updated to final implementation state on 2026-06-05 after extracting `signing_workspace_composition.py`, reconciling the shell compatibility seam for the viewer builder, and removing stale duplicated panel helpers from `signing_shell.py`.
