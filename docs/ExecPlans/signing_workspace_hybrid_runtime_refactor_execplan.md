# Deepen Signing Workspace Runtime And Retire Compatibility Cruft

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `/.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the signing workspace will expose one deeper runtime/controller seam for interaction, review/text, and shell-local workflow operations instead of splitting them across `signing_workspace_runtime.py`, `signing_workspace_compatibility_surface.py`, and direct `SigningWorkspaceWidget` forwarding. The visible behavior must stay the same: viewer selections still route through `WorkspaceInteractionSession`, panel/page changes still refresh the correct ordered effects, document review and document text still work from the sidebar, Phase 3 still uses `testing_adapter`, and the app frame still sees the same narrow production shell port.

The user-visible proof is unchanged shell behavior with a simpler internal architecture. A contributor can verify the result by running the focused Qt workspace tests and Phase 3 harness workspace tests and observing that the shell still supports review/text navigation, rect placement, preview refresh, and harness scenario application without relying on the old broad compatibility surface as the main live API.

## Child ExecPlan Dependencies

- [ ] No child ExecPlans are required for this slice. This parent plan covers the full one-pass refactor.

## Progress

- [x] (2026-07-05 15:10Z) Re-read the `dev-loop`, `improve-codebase-architecture`, and `write-execplan` skill instructions plus `PLANS.md`.
- [x] (2026-07-05 15:12Z) Re-checked live repo state for the signing workspace runtime, compatibility surface, composition wiring, shell forwarding, tests, and architecture/spec references.
- [x] (2026-07-05 15:17Z) Collected a required `explorer-light` report confirming that `SigningWorkspaceRuntime` is still shallow, `SigningWorkspaceCompatibilitySurface` still owns most of the shell API, and Phase 3 already depends on `testing_adapter` instead of `compat_surface`.
- [x] (2026-07-05 15:47Z) Deepened `SigningWorkspaceRuntime` so it now owns review/text, page/rect, current-request, and shell-local workflow verbs that were previously spread across the compatibility surface.
- [x] (2026-07-05 15:49Z) Reduced `SigningWorkspaceCompatibilitySurface` to a thin widget-export/testing owner while preserving `testing_adapter` as the sanctioned harness seam.
- [x] (2026-07-05 15:50Z) Updated composition and shell wiring so widget exports and shell forwarding now delegate to the deeper runtime/controller.
- [x] (2026-07-05 15:58Z) Replaced the shallow runtime tests with runtime-focused boundary coverage and added order-sensitive assertions for the non-notifying signature-rect and harness-priming choreography.
- [x] (2026-07-05 15:59Z) Ran targeted unit tests and reached green: `tests/unit/test_qt_signing_workspace_runtime.py`, `tests/unit/test_qt_phase3_harness_workspace.py`, and the focused `tests/unit/test_qt_signing_shell.py` subset.
- [x] (2026-07-05 16:06Z) Reconciled `docs/ARCHITECTURE.md` to describe runtime ownership and the thinner compatibility/testing seam.
- [x] (2026-07-05 16:11Z) Collected two post-implementation compliance reviews; both found the slice behavior-safe and SPEC-compliant, with only the remaining broad widget export surface called out as the next architecture seam.
- [x] (2026-07-05 16:12Z) Recorded final outcomes and the next follow-on opportunity for a subsequent `$improve-codebase-architecture`.

## Surprises & Discoveries

- Observation: The repo has already crossed the important harness boundary. `phase3_harness_workspace.py` now rejects compat-surface-only shells and requires `testing_adapter`, so the remaining compatibility surface is mostly shell/test legacy rather than active harness architecture.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_workspace.py` raises `TypeError("Phase 3 harness shells must expose 'testing_adapter'.")` when `testing_adapter` is absent.

- Observation: `SigningWorkspaceRuntime` binds collaborators that it does not actually use yet, which is a strong signal that the runtime extraction stopped halfway through the deepening move.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_runtime.py` stores `_viewer_interaction_session` and `_document_review_workspace`, but the live verbs still live in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`.

- Observation: `build_qt_signing_shell()` returns the concrete widget, not the wrapper object that owns the Python methods.
  Evidence: Removing widget export rebinding made the returned `_CloseAwareWidget` lose methods such as `refresh_viewer()` and `signature_rect()` until the compatibility surface was restored as a thin export owner over runtime methods.

- Observation: The Phase 3 harness is already aligned with the intended end state.
  Evidence: `tests/unit/test_qt_phase3_harness_workspace.py` stayed green because it depends on `testing_adapter`, not on `compat_surface`.

## Decision Log

- Decision: Keep `WorkspaceInteractionSession` unchanged as the application policy core for this slice.
  Rationale: The architectural friction is in the presentation-layer split between runtime, compatibility exports, and shell forwarding, not in the ordered-effect application boundary itself. Reopening the app boundary would broaden the slice without helping spec compliance.
  Date/Author: 2026-07-05 / Codex

- Decision: Preserve `testing_adapter` as the only supported live-shell harness seam while shrinking or removing broader `compat_surface` exports from the main shell API.
  Rationale: This matches `docs/SPEC.md`'s preference for replacement over compatibility layers and aligns with the existing Phase 3 harness contract.
  Date/Author: 2026-07-05 / Codex

- Decision: Treat this as one behavior-preserving refactor slice with mixed change classes.
  Rationale: The primary change class is behavior-preserving architecture change, but targeted tests and architecture-doc updates must move with it to keep the seam understandable and verifiable in one pass.
  Date/Author: 2026-07-05 / Codex

## Outcomes & Retrospective

The refactor landed as intended. `SigningWorkspaceRuntime` is now the deep shell-local owner of the live interaction, review/text, page/rect, current-request, and shell-edge behavior, while `SigningWorkspaceCompatibilitySurface` has been reduced to widget export installation plus the explicit `testing_adapter` seam. Focused runtime, shell, and Phase 3 harness tests passed after the change, and `docs/ARCHITECTURE.md` now describes the runtime/controller ownership accurately.

The remaining debt is intentional and narrow: the returned widget still publishes a broad exported method family because `build_qt_signing_shell()` returns the widget itself. That is the next plausible simplification seam for a future `$improve-codebase-architecture`, but it no longer blocks the interaction/runtime cluster from being a coherent deep module.

## Context and Orientation

The signing workspace lives in `src/foliaseal/presentation/qt/signing_shell.py`, but that file is no longer supposed to own the detailed interaction choreography. Constructor-time assembly already lives in `src/foliaseal/presentation/qt/signing_workspace_composition.py`. The application-layer policy for viewer selection, page changes, panel-change follow-up, and viewer refresh follow-up lives in `src/foliaseal/application/workspace_interaction_session.py` as `WorkspaceInteractionSession`. That policy returns a `WorkspaceInteractionPlan`, which is an ordered list of effects such as review-transition application, viewer refresh, placement-context application, signature-rectangle application, overlay sync, preview refresh, signing-action reload, signing-action invalidation, and error emission.

Today the presentation layer still splits responsibility in a shallow way:

- `src/foliaseal/presentation/qt/signing_workspace_runtime.py` owns only viewer/panel/page event routing, interaction-plan dispatch, placement-context application, overlay sync, and shell-edge error/status handling.
- `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` still owns document review refresh, document-text search/navigation/copy/selection-mode operations, logical page accessors, signature-rectangle shell helpers, timestamp/certificate-selection/current-request reads, and broad widget export installation.
- `src/foliaseal/presentation/qt/signing_workspace_shell_surface.py` owns the narrow production app-frame verbs such as `apply_app_settings`, `choose_output_pdf_path`, `refresh_certificate_configurations`, `submit_sign_request`, and `open_signed_output`.
- `src/foliaseal/presentation/qt/phase3_harness_workspace.py` now depends on `testing_adapter`, which is already a narrow harness/testing seam layered over the compatibility surface.

The architectural goal is to deepen the runtime/controller module so the live shell behavior is owned by one coherent shell-local boundary instead of being split between runtime and compatibility helpers. “Deepen” here means shrinking the public surface area a caller must understand while increasing the amount of internal coordination hidden behind that surface. This is an in-process dependency category: all collaborators are local Python objects, not remote services.

## Plan of Work

First, reshape `src/foliaseal/presentation/qt/signing_workspace_runtime.py` into the chosen hybrid boundary. Keep its explicit verbs, but make it the owner of all shell-local interaction and workspace workflow operations that are currently spread across the compatibility surface. The runtime should own:

- viewer selection, page change, panel change, review-signature selection, viewer refresh, and review jump follow-up;
- document review refresh and document-text search/navigation/copy/selection-mode operations;
- logical page get/set operations;
- shell-local signature-rectangle application entrypoints that must preserve the explicit `refresh_after_panel_change()` follow-up behavior;
- timestamp-required and current-request reads/writes that are needed for the testing seam;
- shell-edge result/error/status display behavior.

Second, introduce or formalize a narrow ports adapter inside the presentation layer. `SigningWorkspaceInteractionBridge` already owns ordered-effect execution; this slice should let the runtime depend on a smaller adapter boundary for “apply a plan”, “refresh preview”, “sync overlay”, “read/write result text or status”, and any remaining shell-local effect application. Avoid inventing a generic command bus. Keep explicit verbs and hide choreography, not semantics.

Third, collapse `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`. It should stop being the main home for live shell verbs. Reduce it to the smallest compatibility/testing export owner that is still justified. `testing_adapter` must remain supported because `phase3_harness_workspace.py` depends on it. If `compat_surface` is still exported, it should be clearly secondary and thin, not the place where real shell behavior lives. Delete dead collaborator fields and forwarding methods when the runtime fully owns the behavior.

Fourth, update `src/foliaseal/presentation/qt/signing_workspace_composition.py` so composition wires the deeper runtime, narrower compatibility/testing surface, and existing shell surface correctly. The composition root must still bootstrap viewer refresh, initial review load, and signing-action reload in the same order unless the tests show a better behavior-preserving order. `src/foliaseal/presentation/qt/signing_shell.py` should then forward to the new owners with less direct shell-surface leakage.

Fifth, update tests. `tests/unit/test_qt_signing_workspace_runtime.py` should become the main boundary test suite for the deeper runtime/controller. Tests in `tests/unit/test_qt_signing_shell.py` that merely prove the shell forwards into the old shallow split can be replaced or narrowed once runtime boundary coverage exists. Keep the behavior assertions that matter: selection ordering, page-change behavior, panel-change behavior, signature-rect sequencing, review/text actions, readiness truthfulness, and the dedicated `testing_adapter` contract used by `tests/unit/test_qt_phase3_harness_workspace.py`.

Finally, update `docs/ARCHITECTURE.md` to describe the deeper runtime/controller ownership and the reduced compatibility surface. Do not update `docs/SPEC.md` unless the behavior truly changes, because this slice is intentionally behavior-preserving and SPEC is frozen.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Inspect the live runtime, compatibility, composition, shell, and harness seams before editing:

       sed -n '1,220p' src/foliaseal/presentation/qt/signing_workspace_runtime.py
       sed -n '1,340p' src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       sed -n '1,340p' src/foliaseal/presentation/qt/signing_workspace_composition.py
       sed -n '240,340p' src/foliaseal/presentation/qt/phase3_harness_workspace.py

   Expect to see that runtime owns only a subset of the live shell verbs while the compatibility surface still exports many of them.

2. Edit the runtime, compatibility surface, composition root, and shell forwarding files so runtime owns the live shell-local verbs and compatibility becomes thin.

3. Refresh or replace the focused runtime and shell tests so they assert behavior at the runtime boundary instead of overfitting to the old shallow split.

4. Run the focused test suites:

       pytest tests/unit/test_qt_signing_workspace_runtime.py
       pytest tests/unit/test_qt_phase3_harness_workspace.py
       pytest tests/unit/test_qt_signing_shell.py -k "workspace_runtime or compatibility_surface or testing_adapter or viewer_selection or page_change or refresh_viewer or set_signature_rect or document_text"

   Expect all selected tests to pass. If any fail, update both the implementation and this ExecPlan's living sections with the discovery.

5. Reconcile architecture documentation:

       rg -n "signing_workspace_runtime|compatibility_surface|testing_adapter|workspace interaction" docs/ARCHITECTURE.md

   Update the relevant ownership summaries and change log entries to match the implemented runtime/controller seam.

## Validation and Acceptance

Acceptance is behavioral.

- Runtime boundary tests must prove that `SigningWorkspaceRuntime` now owns the interaction and review/text verbs that previously lived on the compatibility surface.
- Shell tests must still prove that viewer selections route through `WorkspaceInteractionSession.select_in_viewer(...)`, page changes route through `WorkspaceInteractionSession.change_page(...)`, viewer refresh executes ordered effects in order, and direct `set_signature_rect(...)` still drives `refresh_after_panel_change()` while viewer-selection placement does not.
- Phase 3 harness workspace tests must still pass with `testing_adapter` as the supported live-shell harness seam.
- `docs/ARCHITECTURE.md` must describe the runtime/controller as the deeper shell-local owner and must stop implying that the compatibility surface is the main live behavior home.

The slice is complete when the runtime boundary is deeper, the compatibility surface is materially smaller or thinner, the tests are green, and the architecture doc matches the code.

## Idempotence and Recovery

This refactor is safe to rerun because it is local to Python source, tests, and documentation. Re-running the test commands is idempotent. If an intermediate edit breaks the shell test surface, use the focused tests above to recover behavior before broadening the scope. Do not remove `testing_adapter` during recovery; it is the stable harness seam for this slice.

## Artifacts and Notes

Key expected outcomes to preserve while refactoring:

    widget.viewer_widget.emit_selection(...) still updates preview/readiness without routing back through the generic panel-change callback.

    widget.set_signature_rect(...) still applies the non-notifying rect path and then explicitly performs the panel-change follow-up through `WorkspaceInteractionSession.refresh_after_panel_change()`.

    phase3_harness_workspace.py still reaches the live shell through `testing_adapter`, not through `compat_surface`.

## Interfaces and Dependencies

At the end of the slice, these boundaries must exist conceptually even if exact helper names shift slightly:

- `WorkspaceInteractionSession` remains the Qt-free application policy object in `src/foliaseal/application/workspace_interaction_session.py`.
- `SigningWorkspaceRuntime` in `src/foliaseal/presentation/qt/signing_workspace_runtime.py` is the shell-local runtime/controller. It must expose explicit verbs for live workspace behavior rather than a generic `dispatch(...)`.
- A narrow presentation-layer ports adapter remains responsible for applying ordered interaction plans and other concrete Qt-side effects. `SigningWorkspaceInteractionBridge` may continue to own ordered-effect execution, but the runtime must become the caller-facing owner of the behavior.
- `SigningWorkspaceTestingPort` remains the supported harness/testing seam for live-shell Phase 3 work.
- `SigningWorkspaceShellSurface` remains the narrow app-frame-facing production shell port and should not re-absorb the broader workspace workflow behavior being consolidated here.

Revision note: Created on 2026-07-05 to drive the one-pass hybrid runtime/controller refactor selected after the architecture exploration loop. The plan intentionally covers implementation, testing, and architecture-doc reconciliation in one slice so the repo is ready for a subsequent `$improve-codebase-architecture` pass.
