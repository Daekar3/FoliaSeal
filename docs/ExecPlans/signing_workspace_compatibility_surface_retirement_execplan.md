# Retire the Qt Signing-Workspace Compatibility Surface

This ExecPlan is a living document maintained according to
`.agents/skills/write-execplan/PLANS.md`. It is the selected child of
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md` and must be completed as one
implementation slice: code, boundary tests, full validation, architecture reconciliation, cleanup,
and commit are all part of the same outcome.

## Purpose / Big Picture

The real signing shell already has typed maintenance, session, testing, and lifecycle-view ports,
but a transitional compatibility module still assigns about 35 public attributes and callbacks to
the Qt widget at runtime. Those aliases make child widgets and implementation methods look like a
second public API and force tests/harness code to know how the shell is assembled. After this slice,
the shell will expose only declared behavior/properties, the harness will consume the existing typed
`SigningWorkspaceBundle`, and the compatibility surface/legacy exporter will be gone. A user sees no
workflow change: opening, placing, previewing, signing, reviewing, searching, and closing a document
continue to work, while the same behavior is proven through the typed bundle and offscreen evidence.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` is frozen and must remain byte-for-byte unchanged.
- [x] `docs/ARCHITECTURE.md` documents `SigningWorkspaceBundle`, the typed testing/session ports,
  and the existing transitional compatibility debt.
- [x] The prior bundle/threading slices are closed at `63ae6f10a`; the current tree is clean on
  `main` and the production `ReusableSigningObjects` boundary is canonical.
- [x] Scan Round 58 and Design Selection 58 selected the strict common-caller bundle design at
  Refactor Shape Score `90.5`, with no evidence-backed penalties.

## Progress

- [x] (2026-08-08) Fresh three-explorer scan identified the compatibility-export cluster at
  Candidate Priority `72.512812` and confirmed the typed testing/session ports are available.
- [x] (2026-08-08) Three designs and two independent reviews were completed; strict common-caller
  bundle construction was selected at Shape Score `90.5`.
- [x] (2026-08-08) Captured baseline counts, behavior-preservation map, production callers, and
  exact retirement gates before editing.
- [x] (2026-08-08) Moved the testing adapter to the explicit
  `signing_workspace_testing_adapter.py` seam, deleted the compatibility surface/export installer,
  and replaced dynamic callback aliases with declared shell properties/methods.
- [x] (2026-08-08) Made bundle construction explicit and removed raw-shell/child-widget fallbacks
  from harness, session, matrix, preview, and scenario adapters; migrated all affected fakes and
  characterization tests.
- [x] (2026-08-08) Completed focused/full/offscreen validation, measured improvement, reconciled
  architecture/parent plans, audited processes/artifacts, and committed the complete slice.

## Surprises & Discoveries

- Observation: The prior slice already removed the `compat_surface` fallback from the harness
  workspace, but `QtPhase3HarnessWorkspaceAdapter` still accepts `shell` and constructs a bundle
  when `workspace` is absent.
  Evidence: `phase3_harness_workspace.py:204-222`.
- Observation: `QtSigningWorkspaceSessionPort` reaches into `shell_widget.viewer_navigation_controls`
  instead of receiving a navigation capability.
  Evidence: `signing_shell_port.py:220-228`; the shell already has explicit page-navigation behavior
  through its runtime/controller.
- Observation: The legacy installer owns the only `destroyed`-signal connection that disposes the
  properties panel, while the close-aware widget also disposes on close.
  Evidence: `signing_workspace_compatibility_surface.py:143-146` and
  `signing_shell.py:220-230`. Disposal must move to one idempotent shell/controller owner before
  deleting the installer.
- Observation: Existing shell tests intentionally inspect declared-looking child properties such as
  `properties_panel`, `viewer_widget`, and `sidebar_surface`; those are retained as explicit Qt-edge
  properties where behavior/tests require them, while runtime callback aliases are removed.
  Evidence: `tests/unit/test_qt_signing_shell.py:789-2906`.
- Observation: `viewer_navigation_controls` is a UI-controls dictionary, not a session capability;
  its buttons do not implement page navigation or zoom methods.
  Evidence: `signing_workspace_composition.py:324-334` and the viewer methods in
  `viewer_widget.py:800+`.
- Decision: Add declared shell methods that delegate page navigation to the viewer/runtime page
  callbacks and reset zoom through the viewer widget, then have the session port call those methods.
  This preserves current-page semantics without retaining a child-control lookup.
  Date/Author: 2026-08-08 / Codex and implementation-context review.
- Observation: First-party acceptance/session/preview callers still accept an optional raw shell and
  reconstruct a bundle when no typed workspace is supplied.
  Evidence: `phase3_harness.py:_build_live_evidence_workspace`,
  `phase3_harness_session_runner.py`, `phase3_signed_acceptance_matrix_runner.py`,
  `phase3_signed_acceptance_scenario_executor.py`, and `phase3_harness_workspace.py`.
- Decision: Migrate every first-party caller and fake to receive the existing
  `SigningWorkspaceBundle`; remove optional `shell` parameters and AttributeError/raw-shell
  fallbacks in the same slice. No compatibility branch may move to another module.
  Date/Author: 2026-08-08 / Codex and implementation-context review.

## Decision Log

- Decision: Use the existing `SigningWorkspaceBundle` as the only AppFrame/harness contract and do
  not add a nested capability registry or generic workspace manager.
  Rationale: the bundle already separates maintenance, primary session, testing, and lifecycle view;
  adding another aggregate would be speculative and could become a service locator.
  Date/Author: 2026-08-08 / Codex and independent reviewers.
- Decision: Keep `SigningWorkspaceTestingAdapter` as a typed, explicit Qt-edge property while
  removing `SigningWorkspaceCompatibilitySurface`, `SigningWorkspaceLegacyWidgetExports`, and all
  runtime callback assignments.
  Rationale: `SigningWorkspaceTestingPort` is an established non-production seam consumed by the
  harness; retaining the declared adapter property preserves that contract without retaining the
  broad compatibility facade.
  Date/Author: 2026-08-08 / Codex.
- Decision: Add explicit shell methods for page navigation and make `QtSigningWorkspaceSessionPort`
  call those methods rather than reading `viewer_navigation_controls` from the shell object.
  Rationale: navigation is real session behavior, while the child-control lookup is a compatibility
  leak. Page state remains owned by `ViewerSession.current_page`.
  Date/Author: 2026-08-08 / Codex.
- Decision: Require `workspace: SigningWorkspaceBundle` in `QtPhase3HarnessWorkspaceAdapter` and
  remove its bare-shell fallback; make `build_qt_signing_workspace_bundle` require an explicit typed
  `testing_adapter` and never use `getattr` to discover it.
  Rationale: all first-party harness callers now have a typed bundle path, and a missing capability
  should fail at composition rather than silently reintroduce compatibility behavior.
  Date/Author: 2026-08-08 / Codex.
- Decision: Preserve public CLI commands, Phase3 DTOs, JSON fields, fixture/artifact paths, current
  page semantics, preview/signing behavior, and close/dispose idempotence. Do not rename phase3
  modules in this slice; that remains the separate nomenclature child plan.
  Rationale: those are external or behavior contracts and mixing them would make regressions
  indistinguishable from compatibility retirement.
  Date/Author: 2026-08-08 / Codex.

## Outcomes & Retrospective

Implementation completed in commit `34e0e4a8e` (2026-08-08).
The compatibility module and dynamic alias assignments were deleted rather than left unused. The
typed `SigningWorkspaceBundle` is now the only first-party harness/session contract; the shell facade
owns declared visual properties and navigation verbs, while `SigningWorkspaceTestingAdapter` is the
sole live testing seam.

Validation evidence:

- Focused compatibility/harness/AppFrame/session suites: `225 passed`.
- Full suite: `1156 passed, 11 skipped, 1 pre-existing Pillow deprecation warning`.
- Ruff, compileall, CLI help, typed-bundle imports, `git diff --check`, and frozen-SPEC diff passed.
- Offscreen `phase3-signing-acceptance-evidence`: signed acceptance `10 scenarios / 7 successful
  signings`, preview parity `18 / 18`, fit rejection `3 / 3`; generated outputs were removed.
- Retirement grep across `src` and `tests`: zero `compat_surface`, legacy exporter, installer, or
  compatibility-module references; zero dynamic widget assignments. The shell controller's private
  collaborator installation is deliberate composition wiring, not a public alias. The only remaining
  `shell: Any` occurrence is the intentional opaque `QtWorkspaceView` lifecycle adapter.
- Process audit after the offscreen run found no FoliaSeal, Python, PySide, Qt, or pytest processes.

Conservative repeated proxy measurements changed navigation `6 -> 4`, coordinated-change units
`5 -> 4`, seam count `4 -> 1` (the remaining Qt lifecycle edge), public-surface units `6 -> 3`,
boundary behavior coverage `.50 -> .90`, and production bypass count `4 -> 1`. Using the fixed
architecture-loop rubric, the component improvements are navigation `.33`, change amplification
`.40`, seam reduction `.75`, boundary-test improvement `.40`, interface compression `.50`,
cohesion `.45`, and isolation `.85`, for weighted Actual Improvement approximately `.53` versus
predicted `.65375`; prediction accuracy is approximately `.81x`. No component regressed beyond
`-.10`, and the `.15` acceptance threshold is exceeded. Remaining historical `phase3` names are
governed by `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md`; no new aliases were added.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_workspace_composition.py` builds the viewer, properties panel,
runtime, action/review bridges, shell surface, and orchestrator for one live PDF. It currently builds
`SigningWorkspaceCompatibilitySurface`, which creates a testing adapter and a legacy exporter. The
orchestrator calls the exporter before refresh/review/action bootstrap. The shell controller then
copies composition objects onto `SigningWorkspaceWidget`, and `signing_shell.py` exposes a few
properties over those objects.

`src/foliaseal/presentation/qt/signing_shell_port.py` defines the stable bundle:
`SigningWorkspaceBundle(maintenance, session, testing, view)`. `QtSigningWorkspaceFactory.create()`
currently builds a shell and then adapts it by reading `shell_widget.testing_adapter`; the session
adapter also reads `shell_widget.viewer_navigation_controls`. This plan changes those reads to
explicit declared inputs/methods while keeping the bundle fields and protocol methods stable.

`src/foliaseal/presentation/qt/phase3_harness_workspace.py` applies named scenarios and captures
preview state through `workspace.testing`; it must receive a bundle directly and never reconstruct
one from a raw shell. `tests/unit/test_qt_signing_shell.py`,
`tests/unit/test_qt_phase3_harness_workspace.py`, `tests/unit/test_signing_shell_port.py`,
`tests/unit/test_qt_app_frame.py`, `tests/unit/test_qt_app_frame_workspace_open.py`, and Phase 3
session/matrix tests are the behavior-preservation surface.

## Architecture Selection Record

The selected candidate is `signing-workspace-compatibility-surface-retirement`, Candidate Priority
`72.512812`, confidence `0.9825`, local-substitutable dependency category. The selected design is
strict common-caller Design C, Shape Score `90.5`.

The exact public contract at completion is:

    @dataclass(frozen=True)
    class SigningWorkspaceBundle:
        maintenance: SigningWorkspacePort
        session: SigningWorkspaceSessionPort
        testing: SigningWorkspaceTestingPort
        view: WorkspaceViewPort

    class SigningWorkspaceFactory(Protocol):
        def create(self, bootstrap: SigningWorkspaceBootstrap) -> SigningWorkspaceBundle: ...

`SigningWorkspaceTestingAdapter` remains an explicit Qt-edge implementation of
`SigningWorkspaceTestingPort`; its constructor remains
`(*, runtime, properties_panel, last_signing_result)`. `SigningWorkspaceCompatibilitySurface` and
`SigningWorkspaceLegacyWidgetExports` are deleted. No public bundle field may contain a raw QWidget,
compatibility surface, or untyped capability registry. `QtSigningWorkspaceSessionPort` calls declared
shell navigation methods (`go_to_previous_page()`, `go_to_next_page()`, `reset_zoom_view()`) rather
than inspecting child controls.

Design A scored `86.5` and was rejected because it leaves the construction graph less explicit and
does not prove one bundle identity across every harness caller as directly as C. Design B scored
`80.0` and was rejected for nested capability ceremony and speculative optional capability surface.
The selected C shape has no service-locator, generic-manager, infrastructure-leak, or compatibility
penalty; its migration risk is represented in the conservative feasibility score.

## Scope and Migration Inventory

Production modules to change are `signing_workspace_compatibility_surface.py`,
`signing_workspace_composition.py`, `signing_workspace_orchestrator.py`,
`signing_workspace_shell_controller.py`, `signing_shell.py`, `signing_shell_port.py`, and
`phase3_harness_workspace.py`, `signing_workspace_action_bridge.py`, and the interactive lifecycle
cleanup in `phase3_harness_session_runner.py`. First-party callers to migrate include the AppFrame workspace-open
path, `QtSigningWorkspaceFactory`, `_build_live_evidence_workspace`,
`QtPhase3HarnessWorkspaceAdapter`, `capture_qt_preview_render`, interactive and signed-acceptance
session runners, matrix/scenario executors, and preview capture helpers. Tests to migrate include shell/export characterization,
workspace adapter fakes, shell-port factory tests, AppFrame workspace tests, and Phase 3 session/
matrix tests.

The old public/dynamic entry points retired in this slice are `compat_surface`,
`SigningWorkspaceLegacyWidgetExports`, `install_widget_exports`, and widget callback assignments
for runtime/shell methods. The declared `testing_adapter` property and existing shell behavior
methods remain because they are the established typed testing/session edge, not dynamic aliases.

Allowed generated changes are only the temporary offscreen acceptance summary/matrix directories;
they must be deleted before closure. Forbidden mixed work includes phase3 module/CLI/DTO renames,
persisted schema migration, signing-policy changes, GUI redesign, broad formatting, or new CLI
commands. No compatibility shim may be added in another module.

## Behavior Preservation Map

- `B1` bootstrap order: composition bootstrap still refreshes the viewer, applies document review
  state, and reloads action state in the same order. Existing orchestrator tests remain the evidence;
  add a direct order assertion after removing the installer call.
- `B2` typed bundle identity: AppFrame/workspace-open, factory, view, maintenance, session, and
  testing all refer to one bundle/adapter instance. Add identity assertions to shell-port and
  AppFrame workspace tests.
- `B3` testing scenario behavior: appearance, timestamp, rectangle placement, refresh, event-pump,
  current request, and last signing result remain equivalent through `SigningWorkspaceTestingPort`.
  Existing `test_qt_phase3_harness_workspace.py` scenarios plus new fake-port boundary tests cover it.
- `B4` preview capture: panel preview refresh, validation text, render capture, and cleanup retain
  their existing payloads and artifact paths. Existing preview capture tests remain; add an explicit
  adapter-to-bundle capture assertion.
- `B5` page navigation/current page: previous/next/reset zoom delegate through declared session
  methods and never reset `ViewerSession.current_page`. Existing shell navigation tests and a session
  port fake test cover it.
- `B6` lifecycle: close and Qt destroyed paths dispose the properties panel exactly once, and the
  active workspace view remains idempotently disposable. Existing shell/lifecycle tests plus a new
  disposal-count assertion cover it.
- `B7` external evidence contracts: CLI names, JSON/DTO fields, fixtures, artifact paths, signing
  outcomes, and acceptance counts remain unchanged. Full suite and offscreen matrix are required.

## Baseline Measurements and Predicted Improvement

Baseline commit is `63ae6f10a`, clean on `main`. Repeatable raw counts are:

- `compat_surface` references across `src` and `tests`: `9`;
- `install_widget_exports` references across `src` and `tests`: `2`;
- `SigningWorkspaceLegacyWidgetExports` references: `2`;
- dynamic `widget.<name> = ...` assignments in the compatibility module: `35`;
- raw-shell/fallback references in the harness/port cluster: `35`;
- `build_qt_signing_workspace_bundle` call/definition references: `9`.

For the fixed improvement rubric, the pre-change proxy values are navigation units `6` (AppFrame,
workspace-open, shell, composition, compatibility surface, harness adapter), coordinated-change
units `5` (composition, orchestrator, shell controller, shell port, harness), seam count `4`
(installer, shell property delegation, bundle `getattr`, harness fallback), public-surface units `6`
(compat surface, legacy exporter, dynamic aliases, testing adapter, raw-shell fallback, bundle
adapter), boundary behavior coverage `0.50` for typed bundle/compatibility removal, and production
bypass count `4` (dynamic exporter, compat property, bundle discovery, harness fallback).

Predicted component improvements are navigation `.50`, change amplification `.60`, seam reduction
`.75`, boundary-test improvement `.40`, interface compression `.75`, and boundary isolation `.90`;
the fixed weighted Predicted Improvement is approximately `.65375`. No component may regress below
`-.10`, and accepted Actual Improvement must be at least `.15`.

## Plan of Work

First move `SigningWorkspaceTestingAdapter` and `SigningWorkspaceTestingPanelAdapter` into a focused
module such as `signing_workspace_testing_adapter.py`, preserving their public methods and live
result-reader behavior. Update imports and add direct adapter boundary tests. This keeps the testing
contract independent of the compatibility facade before deletion.

Next change composition and orchestration. Replace the `compatibility_surface` field with the typed
testing adapter, remove `install_widget_exports()` from bootstrap while preserving refresh/review/
action ordering, and move panel disposal to one idempotent shell/controller hook. The shell controller
must publish explicit private collaborator fields used by declared shell properties, not assign public
callback aliases.

Then remove the compatibility facade and dynamic exporter. Add/retain declared Qt-edge properties
only for genuine visual inspection used by existing shell tests (`properties_panel`, `viewer_widget`,
`viewer_navigation_controls`, `sidebar`, `sidebar_surface`, and scroll/container access where
needed). Runtime and shell actions remain ordinary `SigningWorkspaceWidget` methods. The target
grep for `compat_surface`, `SigningWorkspaceLegacyWidgetExports`, and `install_widget_exports` in
production source must be empty.

Update `signing_shell_port.py`: `build_qt_signing_workspace_bundle` receives the explicit typed
testing adapter (or calls a declared shell `testing_adapter` property, never `getattr`), and
`QtSigningWorkspaceSessionPort` delegates page navigation to shell methods. Update
`QtSigningWorkspaceFactory.create()` to make one bundle and pass that same bundle to all harness
callers.

Finally remove the optional `shell` parameter from `QtPhase3HarnessWorkspaceAdapter`, migrate the
interactive/signed acceptance/preview callers and fakes to provide a bundle, and delete the raw-shell
fallback. Keep `QtWorkspaceView` as the only opaque QWidget lifecycle adapter. Update architecture
documentation and this plan with exact measured outcomes. The separate
`docs/ExecPlans/phase3_nomenclature_retirement_execplan.md` remains the next atomic naming slice;
this implementation must not create new `phase3` aliases while it preserves existing external names.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

1. Record baseline grep/counts and run the focused suites before editing:

       rg -n "compat_surface|install_widget_exports|SigningWorkspaceLegacyWidgetExports" src tests
       .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_signing_shell_port.py tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py

   The clean baseline should show the dynamic exporter and the focused tests should pass.

2. Extract the testing adapter, migrate composition/orchestrator/controller ownership, and run the
   adapter, shell, and orchestrator tests. Verify bootstrap order and panel disposal before deleting
   the old module.

3. Delete the compatibility surface/exporter, replace dynamic aliases with declared shell methods or
   properties, update bundle/session adapters, and migrate every raw-shell/fallback caller. Run the
   focused harness, shell-port, AppFrame, and Phase 3 tests after each seam change.

4. Run the complete checks:

       .venv/bin/pytest -q
       .venv/bin/ruff check src tests scripts
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       .venv/bin/python -c "from foliaseal.presentation.qt.signing_shell_port import SigningWorkspaceBundle; from foliaseal.presentation.qt.phase3_harness_workspace import QtPhase3HarnessWorkspaceAdapter; print('typed bundle imports: PASS')"
       git diff --check
       git diff --exit-code -- docs/SPEC.md

5. Run the unchanged headless acceptance command:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect `10` scenarios/`7` successful signings, preview parity `18/18`, and fit rejection `3/3`.
   Remove only the command-generated acceptance directory and summary, then audit for
   `foliaseal|pytest|PySide|Qt` processes.

6. Run the retirement gates:

       rg -n "compat_surface|SigningWorkspaceLegacyWidgetExports|install_widget_exports" src tests
       rg -n "getattr\([^)]*testing_adapter|workspace: .*None|shell: Any" src/foliaseal/presentation/qt/signing_shell_port.py src/foliaseal/presentation/qt/phase3_harness_workspace.py

   The first command may match only historical ExecPlans; it must not match live source/tests. The
   second command must show no dynamic testing-adapter discovery or raw-shell workspace fallback.

## Validation and Acceptance

Behavioral acceptance means a real shell still opens and closes, page navigation preserves
`ViewerSession.current_page`, the signing setup/preview/action flow behaves as before, and the
offscreen signed-acceptance command reports the same scenario counts and parity. Architectural
acceptance additionally requires one typed bundle identity, no compatibility module/import/installer
in live source, no dynamic widget callback assignments, no raw-shell fallback in the harness, and no
private child-widget reads in the session port. Focused and full tests, Ruff, compileall, CLI help,
import isolation, frozen-SPEC diff, offscreen evidence, process cleanup, and generated-output cleanup
must all pass. The measured Actual Improvement must meet the fixed `.15` minimum with no component
regression beyond `.10` and no unresolved major review finding.

## Idempotence and Recovery

The migration is safe to repeat from a clean checkout. Keep the adapter extraction additive until
direct boundary tests pass; only then delete the compatibility module and update imports. If a caller
fails because it expects a dynamic alias, migrate it to a declared shell method/property or the typed
bundle; do not restore an alias or add a re-export. If disposal tests fail, centralize the idempotent
close/destroy guard in the shell controller and rerun lifecycle tests. If an offscreen command writes
artifacts, remove the exact generated paths after recording the summary and leave unrelated baseline
artifacts untouched.

## Artifacts and Notes

Only transient offscreen acceptance outputs may change. The durable evidence is the focused/full test
output, retirement grep, measured improvement calculation, architecture-doc update, and commit. Do
not edit `docs/SPEC.md`, rename phase3 modules, change persisted schemas, or leave Qt/Python processes
or dialog windows running.

## Interfaces and Dependencies

The dependency category is local-substitutable. Qt-facing adapters may depend on PySide6 widgets,
viewer controls, and existing rendering/signing collaborators; `SigningWorkspaceBundle`, its ports,
and `SigningWorkspaceTestingPort` remain Qt-neutral contracts. The testing adapter constructor is:

    SigningWorkspaceTestingAdapter(
        *,
        runtime: SigningWorkspaceRuntime,
        properties_panel: SignaturePropertiesPanel,
        last_signing_result: Callable[[], SigningResult | None],
    ) -> SigningWorkspaceTestingPort

The factory contract remains:

    QtSigningWorkspaceFactory.create(
        bootstrap: SigningWorkspaceBootstrap,
    ) -> SigningWorkspaceBundle

`QtPhase3HarnessWorkspaceAdapter` must accept `workspace: SigningWorkspaceBundle` as a required
keyword and must not accept `shell` as a fallback. `QtSigningWorkspaceSessionPort` must use declared
shell methods for navigation. `QtWorkspaceView` remains the only opaque lifecycle view and owns
idempotent close/delete-later behavior.

## Revision Notes

2026-08-08: Created from Scan Round 58 and Design Selection 58. The plan supersedes the older
transitional bridge plan for the next slice: compatibility is now deleted rather than preserved in a
second installer, while the typed testing adapter and public bundle contracts remain stable.
