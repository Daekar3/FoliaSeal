# Signing workspace factory-plus-orchestrator hybrid refactor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the signing workspace will have one explicit caller-facing factory result and one deeper shell-local orchestrator. The app frame and any other production caller will continue to consume a narrow `SigningWorkspacePort`, Phase 3 will continue to consume an explicit `SigningWorkspaceTestingPort`, and the constructor-time bootstrap plus workspace-interaction execution will stop being split across `signing_shell.py`, `signing_workspace_composition.py`, `signing_workspace_runtime.py`, and ad hoc widget export mutation. The observable behavior must stay the same: opening a PDF still installs a live signing shell, Save As still works, review/text flows still work, sign readiness still stays truthful, and the Phase 3 harness still reaches the live shell only through `testing_adapter`.

The user-visible proof is the existing Qt shell tests, app-frame tests, and Phase 3 harness workspace tests all continuing to pass after the seam changes. A future `$improve-codebase-architecture` pass should then find a smaller, clearer shell-local cluster instead of the current runtime/composition/export split.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are required for this slice. The work is intentionally one pass so the public factory change, internal orchestrator extraction, tests, and documentation reconciliation land together.

## Progress

- [x] (2026-07-05 20:27Z) Re-read the live signing-shell seam, app-frame workspace-open boundary, Phase 3 harness workspace adapter, and the relevant prior ExecPlans to confirm the current architecture and constraints.
- [x] (2026-07-05 20:34Z) Wrote this ExecPlan before implementation so the remaining work can be executed and audited from a single file.
- [x] (2026-07-05 21:03Z) Implemented the public factory result change in `src/foliaseal/presentation/qt/signing_shell_port.py` and updated `src/foliaseal/presentation/qt/app_frame_workspace_open.py` to consume the returned bundle while preserving the production port seam.
- [x] (2026-07-05 21:07Z) Added `src/foliaseal/presentation/qt/signing_workspace_orchestrator.py` and moved startup bootstrap plus ordered interaction-plan delegation behind it.
- [x] (2026-07-05 21:10Z) Retargeted `signing_workspace_composition.py`, `signing_workspace_runtime.py`, and `signing_shell.py` to the orchestrator without changing the live widget exports or the explicit `testing_adapter` seam.
- [x] (2026-07-05 21:14Z) Updated focused app-frame and runtime tests for the bundle/orchestrator shape while keeping Phase 3 harness and shell contract tests unchanged at the behavior level.
- [x] (2026-07-05 21:25Z) Ran focused validation: `.venv/bin/python -m pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py` passed with `137 passed`.
- [x] (2026-07-05 21:27Z) Reconciled `docs/ARCHITECTURE.md` to the final code and updated this ExecPlan with final outcomes.

## Surprises & Discoveries

- Observation: the current code already has most of the intended public boundary. `SigningWorkspacePort` is narrow, `testing_adapter` is explicit, and `app_frame_workspace_open.py` already treats the shell as a typed composition result.
  Evidence: `src/foliaseal/presentation/qt/signing_shell_port.py`, `src/foliaseal/presentation/qt/app_frame_workspace_open.py`.

- Observation: the real remaining complexity is internal. `SigningWorkspaceRuntime.bind(...)` still acts as a late assembly sink, while `SigningWorkspaceComposition.bootstrap()` and `SigningWorkspaceCompatibilitySurface.install_widget_exports()` each own part of the startup choreography.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_composition.py`, `src/foliaseal/presentation/qt/signing_workspace_runtime.py`, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`.

- Observation: the first implementation pass introduced an import cycle because the new orchestrator imported the compatibility surface and the runtime imported the orchestrator.
  Evidence: the initial focused pytest run failed during collection with `ImportError: cannot import name 'SigningWorkspaceCompatibilitySurface' from partially initialized module ... signing_workspace_compatibility_surface.py`.

- Observation: converting the orchestrator's compatibility/shell imports to `TYPE_CHECKING` references resolved the cycle without affecting behavior or tests.
  Evidence: after the import fix, `.venv/bin/python -m pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py` reported `137 passed in 10.28s`.

## Decision Log

- Decision: keep the production `SigningWorkspacePort` narrow and stable while changing `SigningWorkspaceFactory.create(...)` to return a bundle that pairs the port with the explicit testing adapter.
  Rationale: this matches the most common caller, preserves the app-frame contract, avoids widening production APIs for Phase 3, and removes the need for callers to discover testing access through the returned widget.
  Date/Author: 2026-07-05 / Codex

- Decision: introduce a shell-local orchestrator that owns both bootstrap ordering and `WorkspaceInteractionPlan` application instead of expanding the existing ports-and-adapters surface.
  Rationale: this is the most aggressive simplification that still preserves behavior and avoids a new layer of adapter ceremony.
  Date/Author: 2026-07-05 / Codex

## Outcomes & Retrospective

The slice completed as intended. `QtSigningWorkspaceFactory` now returns a `SigningWorkspaceBundle` that pairs the existing production `SigningWorkspacePort` with the explicit testing adapter, so the app frame keeps its narrow port while the testing seam becomes explicit at the factory boundary. Internally, `SigningWorkspaceOrchestrator` now owns startup ordering and ordered interaction-plan delegation, reducing the amount of shell-local choreography split between composition, runtime, and ad hoc bootstrap code.

The focused validation target passed with `137` tests, so the public shell behavior, app-frame contract, runtime semantics, and Phase 3 harness testing seam all remained stable. The runtime still has a late `bind(...)` step, so there is still room for another architecture pass later, but the remaining cluster is smaller and clearer than before this slice.

## Context and Orientation

The current signing workspace spans several Qt presentation modules.

`src/foliaseal/presentation/qt/signing_shell_port.py` defines the typed bootstrap inputs, the narrow production `SigningWorkspacePort`, and `QtSigningWorkspaceFactory`. Today that factory returns only the production port.

`src/foliaseal/presentation/qt/app_frame_workspace_open.py` is the app-frame-facing boundary for opening a PDF. It creates `ViewerWorkflow` and `SigningDraftWorkflow`, invokes `SigningWorkspaceFactory.create(...)`, and then returns an `OpenWorkspaceOutcome` containing the production port plus a compatibility snapshot with the concrete widget and workflows.

`src/foliaseal/presentation/qt/signing_shell.py` remains the outer shell adapter. `SigningWorkspaceWidget` creates the runtime, builds the composition, installs the composition fields onto itself, and runs bootstrap.

`src/foliaseal/presentation/qt/signing_workspace_composition.py` currently owns constructor-time assembly for review, text, viewer, sidebar, action bridge, interaction bridge, runtime binding, compatibility surface, shell surface, and bootstrap order.

`src/foliaseal/presentation/qt/signing_workspace_runtime.py` is a shell-local controller with many semantic methods. It still requires a `bind(...)` call after construction, and it delegates `WorkspaceInteractionPlan` execution to `SigningWorkspaceInteractionBridge`.

`src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` installs deep widget exports such as `compat_surface`, `testing_adapter`, `refresh_viewer`, `set_signature_rect`, `current_request`, and several direct object references.

The architectural problem is not that the public port is too wide. The problem is that internal shell ownership is still split across several shallow helpers, and the constructor-time assembly plus ordered interaction execution are not hidden behind one deep module. This slice must make that internal story simpler without breaking the current shell behavior or the explicit `testing_adapter` seam.

## Plan of Work

First, update the public shell-factory contract in `src/foliaseal/presentation/qt/signing_shell_port.py`. Add a new frozen dataclass, `SigningWorkspaceBundle`, containing `port: SigningWorkspacePort` and `testing_adapter: SigningWorkspaceTestingPort`. Change `SigningWorkspaceFactory.create(...)` to return this bundle. Keep `QtSigningWorkspacePort` as the production port adapter. Update `QtSigningWorkspaceFactory.create(...)` so it still calls `build_qt_signing_shell(...)`, wraps the returned widget in `QtSigningWorkspacePort`, reads the explicit `testing_adapter` from the live widget, validates that it satisfies the expected seam, and returns the bundle.

Second, update the app-frame-facing composition path in `src/foliaseal/presentation/qt/app_frame_workspace_open.py`. `SigningWorkspaceCompositionService.compose(...)` should receive the bundle, take the widget from `bundle.port.widget()`, continue to build the same `WorkspaceCompatibilityState`, and return `OpenWorkspaceOutcome(shell_port=bundle.port, compatibility=...)`. The app frame itself should remain production-port-driven. No app-frame caller should receive the testing adapter.

Third, deepen the shell-local orchestration cluster. Add a new module, `src/foliaseal/presentation/qt/signing_workspace_orchestrator.py`, that owns two responsibilities: startup bootstrap order and workspace-interaction plan execution. It should encapsulate the current `compatibility_surface.install_widget_exports()`, `shell_surface.install_port_exports()`, initial viewer refresh, review-state load, and signing-action state load, and it should expose one method that applies `WorkspaceInteractionPlan` through the existing `SigningWorkspaceInteractionBridge`. The orchestrator should depend on already-built collaborators rather than rebuilding policy.

Fourth, re-shape `src/foliaseal/presentation/qt/signing_workspace_runtime.py` and `src/foliaseal/presentation/qt/signing_workspace_composition.py` around that orchestrator. Remove the late `bind(...)` pattern from the runtime in favor of constructor-time dependencies where practical. If full constructor injection is too noisy, use one typed dependency dataclass so runtime construction is still atomic and the old many-argument `bind(...)` sink disappears. The runtime should keep the semantic review/text/page/request verbs that the widget exports and testing adapter need, but it should no longer own workspace-interaction plan application or bootstrap sequencing directly.

Fifth, adjust `src/foliaseal/presentation/qt/signing_shell.py` so `SigningWorkspaceWidget` installs one composition result that already includes the orchestrator and the explicit testing seam. Remove obsolete shell forwarding or stored fields if they only existed to support the old split. The goal is not to delete the returned widget exports yet; the goal is to make them installed from one deeper owner and keep `signing_shell.py` focused on the outer widget lifecycle.

Sixth, keep `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` explicitly transitional but thinner in role description. It should continue to install the named `compat_surface`, `testing_adapter`, and the concrete widget exports required by tests and legacy callers, but it should delegate to the runtime and orchestrator rather than acting like a second controller. Do not widen this surface. Preserve `SigningWorkspaceTestingPort` exactly enough for Phase 3.

Seventh, update tests. `tests/unit/test_qt_app_frame.py` and `tests/unit/test_qt_app_frame_workspace_open.py` must assert the new bundle-returning factory contract while still proving the app frame only uses the narrow production port. `tests/unit/test_qt_signing_workspace_runtime.py` must be retargeted if runtime construction or responsibilities move. `tests/unit/test_qt_signing_shell.py` should continue proving the live widget exports and testing adapter behavior, but any tests that only validate the old shallow split should be rewritten to validate the deeper orchestrator boundary. `tests/unit/test_qt_phase3_harness_workspace.py` should remain green without contract changes if the testing adapter stays stable.

Finally, update `docs/ARCHITECTURE.md` so it matches the new code precisely. The Qt presentation-layer summary, repo-map rows for the shell modules, and any detailed narrative about bootstrap ordering, runtime ownership, or testing-adapter export ownership must be revised. The document must describe the final code, not the planned design.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Implement the public bundle and app-frame composition update.

       rg -n "SigningWorkspaceFactory|SigningWorkspacePort|OpenWorkspaceOutcome" src tests

2. Add the orchestrator module and retarget shell/composition/runtime ownership.

       rg -n "bootstrap|apply_workspace_interaction_plan|bind\\(" src/foliaseal/presentation/qt

3. Update focused tests as the contract changes land.

       .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py

4. Run style checks on the changed files.

       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/app_frame_workspace_open.py src/foliaseal/presentation/qt/signing_workspace_orchestrator.py src/foliaseal/presentation/qt/signing_workspace_composition.py src/foliaseal/presentation/qt/signing_workspace_runtime.py src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py

5. Reconcile architecture documentation and re-run the focused test set if doc-driven code adjustments were required.

## Validation and Acceptance

Acceptance requires all of the following to be true.

The app-frame-focused tests prove that opening a PDF still installs the concrete signing shell widget, that Save As still routes through `SigningWorkspacePort.choose_output_pdf_path()`, and that updated app settings and certificate refreshes still flow only through the production port.

The signing-shell-focused tests prove that the returned widget still exposes `compat_surface`, `testing_adapter`, the live runtime methods such as `refresh_viewer()` and `set_signature_rect(...)`, and the same sign-readiness, review, text-search, and preview behavior as before.

The runtime-focused tests prove that the deeper internal boundary still preserves panel-change refresh, page-change refresh, review/text operations, signature-rect follow-up choreography, and edge error behavior.

The Phase 3 harness workspace tests prove that the harness still depends only on `testing_adapter` and that live-shell scenario application plus request/result capture still work through that adapter.

The final focused validation command should be:

       .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py

If any test count changes because tests were consolidated or split, record the new count and the reason in `Surprises & Discoveries`.

## Idempotence and Recovery

This refactor is safe to apply incrementally because the public behavior stays stable while the internal owner changes. If a partial edit leaves the shell failing because the widget exports are missing, restore the export installation path first and then continue simplifying internals behind it. Do not revert to a broader public production port. If the testing adapter becomes temporarily unavailable, repair the explicit `widget.testing_adapter` installation rather than teaching Phase 3 to fall back to `compat_surface`.

## Artifacts and Notes

The most important artifact for this slice is the focused validation transcript showing the app-frame, shell, runtime, and Phase 3 harness tests all passing together.

    $ .venv/bin/python -m pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_qt_signing_workspace_runtime.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py
    ============================= test session starts ==============================
    collected 137 items
    ...
    ============================= 137 passed in 10.28s =============================

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/signing_shell_port.py` must define:

    @dataclass(frozen=True)
    class SigningWorkspaceBundle:
        port: SigningWorkspacePort
        testing_adapter: SigningWorkspaceTestingPort

    class SigningWorkspaceFactory(Protocol):
        def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle: ...

`src/foliaseal/presentation/qt/signing_workspace_orchestrator.py` must define one shell-local orchestrator type that owns startup bootstrap and ordered interaction-plan application. The exact helper names may vary slightly, but the boundary must be small and semantic, for example:

    class SigningWorkspaceOrchestrator:
        def bootstrap(self) -> None: ...
        def apply(self, plan: WorkspaceInteractionPlan) -> None: ...

`src/foliaseal/presentation/qt/signing_workspace_runtime.py` must depend on the orchestrator for plan application rather than owning that logic itself. The runtime should still expose semantic verbs such as `refresh_viewer()`, `search_document_text()`, `set_signature_rect(...)`, `current_request()`, and `is_sign_action_enabled()`.

`src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` must continue to expose `SigningWorkspaceTestingPort` and install `widget.testing_adapter`, because `src/foliaseal/presentation/qt/phase3_harness_workspace.py` requires that seam explicitly.

Revision note: Created on 2026-07-05 by Codex for the one-pass signing-workspace factory-plus-orchestrator hybrid refactor selected from the `$improve-codebase-architecture` comparison. Updated on 2026-07-05 after implementation, focused validation, import-cycle recovery, and architecture-document reconciliation.
