# Retire the Qt signing-workspace compatibility bridge

This ExecPlan is a living document and must remain compliant with
`.agents/skills/write-execplan/PLANS.md`. The architecture-loop parent is
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.

## Purpose / Big Picture

The signing shell already publishes a typed `SigningWorkspaceBundle` with separate maintenance,
primary-session, testing, and lifecycle-view capabilities. The remaining
`SigningWorkspaceCompatibilitySurface` still installs a large family of dynamic widget attributes
and also owns the testing adapter that the evidence harness consumes. This makes a historical widget
backdoor look like a production API and forces the harness to construct a raw shell, wrap it again,
and retain compatibility knowledge.

After this slice, app-frame and harness callers will create one typed workspace bundle from a
`SigningWorkspaceBootstrap`; the Phase 3 workspace will require that bundle and will not accept a
bare shell fallback. The testing adapter will be independently constructed from explicit runtime,
panel, and result-reader dependencies. A Qt-local legacy installer will preserve existing widget
attribute names and destruction behavior during this migration window, but no bundle or harness
contract will expose `compat_surface`. Existing visible signing, page navigation, preview, evidence,
CLI, JSON, and artifact behavior will remain unchanged. The user-visible proof is the unchanged
offscreen acceptance matrix plus tests showing a single shared bundle and no compatibility access in
the production/harness graph.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` remains frozen and unchanged.
- [x] `SigningWorkspaceBundle`, `SigningWorkspaceFactory`, and typed session/testing ports exist in
  `src/foliaseal/presentation/qt/signing_shell_port.py`.
- [x] The reusable-service threading slice is closed at commit `7c21d4fc2` and the clean baseline is
  commit `658586222`.
- [x] Scan Round 52 and Design Selection 53 selected the constrained A+C hybrid at shape score
  approximately `90.75`, exceeding the best valid base by `5.75` points.

## Progress

- [x] (2026-08-06) Captured baseline compatibility/export counts and the three independent scan
  reports.
- [x] (2026-08-06) Compared minimal, flexible, and common-caller shapes with two independent
  reviews; selected the constrained A+C hybrid.
- [x] (2026-08-06) Completed focused construction-graph review of the interactive runner, signed
  acceptance callers, preview capture, and mandatory bootstrap settings.
- [x] (2026-08-06) Extracted the standalone testing adapter and idempotent Qt-local legacy export
  installer while preserving widget identity, dynamic names, live result timing, and panel disposal.
- [x] (2026-08-06) Added typed factory/bundle construction paths to interactive and signed-acceptance
  runners; the shared bundle is reused by the harness workspace adapter and scenario executor.
- [x] (2026-08-06) Migrated boundary wiring and retained the raw shell only as an explicit transitional
  fallback for existing characterization tests and low-level Qt edges.
- [x] (2026-08-06) Focused suites and the full suite pass: `1,142 passed, 1 warning`; Ruff and
  compile checks pass.
- [x] Migrated the typed workspace factory/bundle into the first-party interactive and signed
  acceptance construction paths; the legacy raw-shell fallback remains only for compatibility tests
  and low-level Qt edges and is recorded as the next retirement gate.
- [x] Migrated boundary wiring and preserved compatibility characterization coverage.
- [x] Added explicit signed-scenario regression coverage proving the exact typed bundle reaches both
  scenario mutation and capture; existing adapter/installer lifecycle characterization remains green.
- [x] Ran focused/full/offscreen validation, removed generated artifacts/processes, reconciled parent
  and architecture docs, committed the slice, and completed the fresh three-explorer closure scan.

## Surprises & Discoveries

- Observation: `SigningWorkspaceCompatibilitySurface` is constructed in composition and consumed by
  the orchestrator only to install widget exports, while `build_qt_signing_workspace_bundle()` already
  requires `testing_adapter`.
  Evidence: `signing_workspace_composition.py:424-443`, `signing_workspace_orchestrator.py:31-57`,
  and `signing_shell_port.py:233-243`.
- Observation: Phase 3 currently constructs a raw shell, builds a workspace adapter from that shell,
  and separately wraps the shell into a bundle.
  Evidence: `phase3_harness_session_runner.py:165-179` and the optional `shell` path in
  `phase3_harness_workspace.py:205-222`.
- Observation: the action bridge updates `widget.last_signing_result`; snapshots must read a live
  result reader rather than a value captured when the adapter is constructed.
  Evidence: `signing_workspace_compatibility_surface.py:67-75` and
  `signing_workspace_action_bridge.py` state updates.
- Observation: `ViewerSession.current_page` is already the authoritative page state. This slice
  must not move or reset it while replacing the shell construction seam.
- Observation: raw-shell construction remains in the signed-acceptance matrix/scenario executors,
  preview-capture helpers, and the interactive runner; `QtHarnessLifecycle.attach_shell()` is the
  intentionally retained low-level Qt lifecycle edge.
  Evidence: `phase3_signed_acceptance_matrix_runner.py`, `phase3_signed_acceptance_scenario_executor.py`,
  `phase3_harness.py`, `phase3_harness_workspace.py`, and `phase3_harness_session_runner.py`.
- Observation: `SigningWorkspaceBootstrap.app_settings` is mandatory even though current Phase 3
  callers receive the default indirectly from `build_qt_signing_shell()`.
  Evidence: `signing_shell_port.py` and the current Phase 3 runner dependency construction.

## Decision Log

- Decision: Use the typed `SigningWorkspaceBundle` as the only dominant app-frame/harness contract.
  Rationale: it already separates maintenance, primary workflow, testing, and lifecycle view
  capabilities and removes the need for callers to know widget internals.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: Split the testing adapter from a Qt-local `LegacyWidgetExports` installer instead of
  deleting every dynamic attribute in the same migration.
  Rationale: current shell tests and legacy direct widget callers still assert names and identity;
  the installer preserves them while making the typed adapter independently testable and giving the
  compatibility layer an explicit removal gate. No new caller may depend on the installer.
  Date/Author: 2026-08-06 / Codex and design reviewers.
- Decision: Preserve injectable failure-stage hooks while changing Phase 3 construction.
  Rationale: session-runner tests verify lifecycle cleanup when shell/workspace creation fails; the
  new typed factory dependency must retain equivalent fake injection and close-on-error behavior.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename any `phase3` module, command, DTO, JSON key, fixture, or artifact in this
  slice.
  Rationale: `phase3_nomenclature_retirement_execplan.md` is the separate atomic contract migration;
  mixing it here would make behavior and naming failures indistinguishable.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

The implementation is complete at commit `468e9e4be` (with the initial seam split recorded at
`e8e9c99f4`). The focused inventory
now reports 157 compatibility/export/factory construction references (including characterization
tests and the documented transitional fallbacks) and 20 broader `compat_surface` or
`install_widget_exports` references. The testing adapter no longer stores a compatibility-surface
back-reference; the installer is idempotent and owns dynamic assignments. Interactive and signed
acceptance production paths create one typed bundle and reuse it through the harness seam, including
scenario mutation and capture.
Measured validation is `1,143 passed, 1 warning`, Ruff clean, compileall clean, and diff-check clean.
The provisional component proxies are navigation `.55`, change amplification `.72`, seam reduction
`.78`, boundary-test improvement `.76`, interface compression `.66`, cohesion `.68`, and isolation
`.82`, for Actual Improvement approximately `.70`; no observed component regressed beyond `.10`.
The raw-shell fallback remains explicitly bounded for characterization tests and low-level Qt edges;
it is the next retirement gate, not a hidden caller contract. Offscreen evidence passed with signed
acceptance `10/7`, preview parity `18/18`, and fit rejection `3/3`; the generated summary and matrix
trees were removed after the audit.

## Context and Orientation

`signing_workspace_composition.py` builds the viewer, properties panel, runtime, bridges, shell
surface, and orchestrator. `SigningWorkspaceCompatibilitySurface` currently receives those objects,
constructs `SigningWorkspaceTestingAdapter` from explicit runtime, panel, and live-result-reader
dependencies, and delegates `install_widget_exports()` to the Qt-local legacy installer. The
`SigningWorkspaceOrchestrator.bootstrap()` call remains the bootstrap-order owner before
refresh/review/action state initialization. `signing_shell.py` exposes both
`testing_adapter` and historical `compat_surface` properties. `signing_shell_port.py` adapts the
widget into `SigningWorkspaceBundle`; the bundle's `testing` capability is the supported harness
boundary.

The Phase 3 interactive and signed-acceptance runners receive a typed factory path and create one
`SigningWorkspaceBundle`; the bundle view is mounted and reused for workspace construction, scenario
mutation, and capture. When the typed factory is intentionally absent, characterization tests retain
the low-level raw-shell fallback. `QtPhase3HarnessWorkspaceAdapter` therefore accepts either a typed
bundle or that explicitly bounded fallback. The target is a
single typed factory call returning one bundle, with the raw-shell adapter retained only at the
low-level Qt edge until all direct tests are migrated.

## Plan of Work

First create a standalone `SigningWorkspaceTestingAdapter` in
`signing_workspace_compatibility_surface.py` or a focused neighboring module. Its constructor must
accept `runtime: SigningWorkspaceRuntime`, `properties_panel: SignaturePropertiesPanel`, and
`last_signing_result: Callable[[], SigningResult | None]`. It must implement the existing
`SigningWorkspaceTestingPort` methods, use a narrow `SigningWorkspaceTestingPanelAdapter`, and pass
the live result-reader value into `runtime.snapshot(...)`. It must not hold a compatibility-surface
back-reference.

Next create a Qt-local `SigningWorkspaceLegacyWidgetExports` installer with explicit construction
inputs for the raw widget, runtime, shell surface, properties panel, viewer/navigation/scroll/sidebar
objects, and the standalone testing adapter. Its `install()` method may assign the historical
attributes and callbacks, connect `destroyed` to idempotent panel disposal, and initialize
`last_signing_result`; it must be the only module that owns those dynamic assignments. If a temporary
`SigningWorkspaceCompatibilitySurface` facade remains for direct legacy tests, it must delegate to
the installer and adapter, be marked transitional in docs, and have no new production or harness
caller.

Then change `SigningWorkspaceComposition` and `SigningWorkspaceShellController` to publish the typed
testing adapter and installer/bootstrap callback separately. `SigningWorkspaceOrchestrator.bootstrap()`
should invoke the narrow installer/bootstrap callback, then retain the existing refresh-viewer,
review-state, and action-state ordering. `SigningWorkspaceBundle` must continue exposing only
maintenance, session, testing, and view capabilities; it must not gain a compatibility field.

Migrate the Phase 3 construction seam. Add a typed dependency such as
`create_workspace: Callable[[SigningWorkspaceBootstrap], SigningWorkspaceBundle]` to
`Phase3HarnessSessionRunnerDeps`, construct one `SigningWorkspaceBootstrap` with the existing
callbacks/service/executor, call the factory once, mount `bundle.view.mount_target()`, and build the
workspace adapter from that same bundle. Preserve injectable failure hooks and close the lifecycle on
factory or adapter errors. Update `QtPhase3HarnessWorkspaceAdapter` to require a bundle and remove
the raw-shell fallback after its boundary tests are migrated. Update composition helpers and signed /
interactive harness tests to provide complete fake bundles. Keep `build_qt_signing_workspace_bundle`
as a low-level Qt adapter only where direct shell tests still require it.

Focused construction review refinement: the migration must also cover the signed-acceptance matrix
and scenario executors, live-evidence and preview-matrix workspace builders, and
`capture_qt_preview_render`. These callers must receive the typed bundle rather than a raw shell.
`SigningWorkspaceBootstrap.app_settings` is mandatory, so the new factory dependency must provide
the same default `AppSettings` source currently supplied indirectly by `build_qt_signing_shell()`.
Keep raw QWidget access only at `QtHarnessLifecycle.attach_shell()` and the low-level Qt factory
adapter; no Phase 3 workspace adapter may retain a raw-shell fallback.

Finally migrate tests from compat-surface assertions to standalone installer/adapter boundary tests,
retaining a small characterization test for the transitional legacy aliases. Add tests proving one
factory call yields shared bundle identity, the panel/result reader reaches testing snapshots, the
destroyed signal disposes the panel once, bare shells are rejected by harness adapters, and no
app-frame/phase3 module imports or accesses `compat_surface`.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Capture the baseline and focused tests:

       git status --short --branch
       rg -n "compat_surface|install_widget_exports|build_qt_signing_workspace_bundle\\(|build_workspace\\(|build_qt_signing_shell" src/foliaseal/presentation/qt tests
       .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_qt_app_frame_workspace_open.py

   The baseline is clean at `658586222`; the grep must show the transitional surface and duplicate
   harness construction, and the focused tests should pass before edits.

2. Implement the standalone adapter and installer, then run their focused tests. Expected result is
   that testing behavior and widget aliases remain unchanged while the adapter can be instantiated
   with fake runtime/panel/result-reader objects without a compatibility-surface object.

3. Migrate the typed factory/bundle path and Phase 3 workspace/session runner. Run the focused harness
   and shell suites after each seam change; a bare shell passed to `QtPhase3HarnessWorkspaceAdapter`
   must now fail with the explicit typed-bundle error, while a fake bundle exercises refresh, scenario,
   snapshot, and lifecycle cleanup.

4. Run the complete validation set:

       .venv/bin/pytest -q
       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       .venv/bin/python -c "import foliaseal.presentation.qt.signing_shell_port, foliaseal.presentation.qt.phase3_harness_workspace; print('Qt bundle import isolation: PASS')"
       git diff --check

5. Run the unchanged offscreen evidence command:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and
   fit rejection `3/3`. Remove `artifacts/phase3_signed_acceptance_evidence_summary.md`, any explicit
   temporary matrix roots, and verify no FoliaSeal/Python/Qt process remains.

6. Verify the retirement and contract gates:

       rg -n "compat_surface|install_widget_exports" src/foliaseal/presentation/qt/app_frame*.py src/foliaseal/presentation/qt/phase3_* || true
       git diff --exit-code -- docs/SPEC.md

   Any remaining matches must be limited to the documented Qt-local installer/facade, low-level shell
   edge, dedicated compatibility characterization tests, and architecture/plan rationale. The typed
   factory path must not build a raw shell first or wrap a second shell; compatibility fallbacks are
   only permitted when the typed factory is intentionally absent.

## Validation and Acceptance

Acceptance requires one typed workspace identity from the factory through view, maintenance, session,
and testing capabilities, with the harness using the same bundle exactly once. Production and Phase 3
callers may not import or access `compat_surface`; the only remaining dynamic export code must be the
Qt-local installer/facade with an explicit grep-based retirement condition. The testing adapter must
read the current signing result through its injected reader, preserve current-page semantics, and
retain panel preview/capture behavior. Lifecycle bootstrap ordering and destroyed-to-panel disposal
must remain idempotent. Full tests, Ruff, import isolation, CLI help, offscreen matrices, SPEC diff,
process cleanup, and generated-summary removal must pass. The measured Actual Improvement must be at
least `.15` with no component regression beyond `.10`.

## Idempotence and Recovery

The migration is additive until boundary tests pass. If a fake harness fails during factory creation,
close the lifecycle exactly once and preserve the failure-stage test before changing the contract. Do
not delete dynamic aliases until all direct consumers are migrated and the retirement grep is clean.
Do not rename phase3 contracts, delete profile data, or change `ViewerSession.current_page`. If the
typed factory migration proves too broad, retain the low-level shell adapter while completing the
standalone adapter/installer boundary and record the exact remaining caller in this plan; do not add
another compatibility layer.

## Artifacts and Notes

Only the transient signed-evidence summary and explicit temporary matrix directories may be generated;
remove them before commit. No `docs/SPEC.md` or phase3 CLI/DTO/JSON/fixture/artifact contract may change.
Closure evidence must include the compatibility grep, one-bundle identity test, focused/full counts,
offscreen counts, SPEC diff, process audit, and the final commit IDs.

## Interfaces and Dependencies

The stable public capability remains:

    class SigningWorkspaceBundle:
        maintenance: SigningWorkspacePort
        session: SigningWorkspaceSessionPort
        testing: SigningWorkspaceTestingPort
        view: WorkspaceViewPort

The new seam-local adapter is:

    class SigningWorkspaceTestingAdapter:
        def __init__(
            self,
            *,
            runtime: SigningWorkspaceRuntime,
            properties_panel: SignaturePropertiesPanel,
            last_signing_result: Callable[[], SigningResult | None],
        ) -> None: ...

The harness factory dependency is:

    CreateWorkspace = Callable[[SigningWorkspaceBootstrap], SigningWorkspaceBundle]

No service locator, generic manager, widget-bearing bundle field, Qt type in application modules, or
new phase3 compatibility alias is allowed. The installer may depend on Qt-local shell objects because
it is explicitly the legacy edge; the typed adapter and bundle remain the testable caller boundary.

## Change Log

- 2026-08-06: Created from Scan Round 52 and Design Selection 53. Selected constrained A+C hybrid to
  make typed bundle construction the dominant caller path while isolating, then retiring, the dynamic
  Qt compatibility exports without changing frozen evidence contracts.
- 2026-08-06: Corrected the first implementation pass after closure review: typed factory runners no
  longer pre-build a raw shell and create a second one; signed scenario mutation now receives the
  same bundle used for capture; compatibility wrappers omit optional bundle keywords for legacy fake
  callers. Full suite and offscreen acceptance were rerun successfully.
