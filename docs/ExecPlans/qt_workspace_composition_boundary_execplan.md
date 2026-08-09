# Deepen the Qt Workspace Composition Boundary

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is the child implementation plan selected by the
architecture-improvement loop for the `qt-workspace-composition-boundary` candidate.

## Purpose / Big Picture

Opening a PDF currently requires the signing shell, its composition helper, its factory, and its
controller to coordinate a large list of widgets, application services, sessions, and callbacks.
After this slice, the production factory will pass one existing `SigningWorkspaceBootstrap` into a
typed Qt-local composition boundary. That boundary will assemble one workspace, bind its collaborators,
bootstrap it exactly once, and return the existing four-capability `SigningWorkspaceBundle`.

The user-visible signing workflow must not change. The architectural improvement is that the app
frame and future GUI work no longer need to know the internal widget graph or callback ordering. The
result is observable through direct composition tests, unchanged workspace behavior tests, the full
test suite, and the offscreen signed-acceptance evidence command.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` is the frozen product contract.
- [x] `docs/UI_SPEC.md` is the frozen interface and interaction contract.
- [x] `docs/ARCHITECTURE.md` documents the existing workspace ports and lifecycle owner.
- [x] `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md` records Scan Round 59 and
  Design Selection 59.

## Progress

- [x] (2026-08-09) Selected the common-caller composition shape after three design reports and two
  independent reviews.
- [x] (2026-08-09) Recorded the clean baseline `f6a3ed3fc`, current parameter/call-site counts, and
  predicted improvement proxies.
- [x] (2026-08-09) Incorporated the pre-implementation lifecycle review: the shell controller remains
  the installation/bootstrap/close delegate, while composition owns assembly and local cleanup.
- [x] (2026-08-09) Added the typed Qt-local request/context, semantic host-actions adapter, and
  composition-owned runtime construction.
- [x] (2026-08-09) Moved production factory construction behind the new composition boundary; the
  old shell builder is now only a delegating test/legacy adapter.
- [x] (2026-08-09) Added direct build-once/partial-cleanup tests and factory boundary assertions;
  normal shell close now invokes composition cleanup.
- [x] (2026-08-09) Recorded the retirement grep for remaining direct builder callers.
- [x] (2026-08-09) Focused and full validation passed; offscreen evidence was attempted with a
  bounded timeout and produced no output/artifacts before timing out in this environment.
- [x] (2026-08-09) Reconciled `docs/ARCHITECTURE.md`, this plan, and the parent loop plan; commit
  remains the final gate for this slice.

## Surprises & Discoveries

- Observation: The typed `SigningWorkspaceBootstrap` and `SigningWorkspaceBundle` already exist, but
  the factory expands the bootstrap into a keyword dictionary and the widget expands it again into
  a 34-argument composition call.
  Evidence: `signing_shell_port.py:244-264`, `signing_shell.py:179-258`, and
  `signing_workspace_composition.py:120-156`.
- Observation: `SigningWorkspaceLifecycle` already owns cross-workspace compose/mount/dispose/publish
  ordering.
  Evidence: `signing_workspace_lifecycle.py` and its failure-cleanup tests. The new composition
  boundary must not duplicate that responsibility.
- Observation: Direct Qt shell tests use the large `build_qt_signing_shell` seam extensively.
  Evidence: `tests/unit/test_qt_signing_shell.py` contains many construction calls and patches the
  viewer-builder seam. The old helper therefore needs an explicit migration/retirement criterion,
  not an unannounced deletion.
- Observation: Disposal is currently split across the close-aware root widget,
  `SigningWorkspaceShellController`, `QtWorkspaceView`, and
  `SignaturePropertiesPanel.dispose()`.
  Evidence: `signing_shell.py`, `signing_workspace_shell_controller.py`, and
  `signing_shell_port.py` each guard part of the close path. The composition slice must delegate
  through this chain rather than create a second cross-workspace disposal owner.
- Observation: `QtSigningWorkspaceFactory` currently gets dynamic bindings indirectly through
  `SigningShellAdapter`; removing the old builder from the production path without a replacement
  would create a circular-import or runtime-binding regression.
  Evidence: `signing_shell.py` loads `PySide6` lazily in `SigningShellAdapter._load_bindings()`, while
  `signing_shell_port.py` imports `build_qt_signing_shell`.

## Decision Log

- Decision: Keep `SigningWorkspaceBootstrap`, `SigningWorkspaceBundle`, and all four public bundle
  ports unchanged.
  Rationale: They are already the stable application/frame/harness contract and changing them would
  broaden the slice without reducing the construction graph.
  Date/Author: 2026-08-09 / architecture loop.
- Decision: Select the common-caller optimized composition request/context shape rather than the
  flexible variation-record design.
  Rationale: The current production path has one real composition variant; additional variation
  records would be speculative public surface. Proven test substitutions remain internal seams.
  Date/Author: 2026-08-09 / architecture loop.
- Decision: Keep cross-workspace replacement in `SigningWorkspaceLifecycle` and one-workspace
  assembly/bootstrap/disposal in the composition object.
  Rationale: This preserves the existing compose → mount → dispose-old → publish invariant and avoids
  creating a generic workspace manager.
  Date/Author: 2026-08-09 / architecture loop.
- Decision: Keep `SigningWorkspaceShellController` as the existing installation/bootstrap/close
  delegate during this slice. The new composition object owns construction and partial-build cleanup;
  the controller remains the single caller of the assembled record's bootstrap and close path.
  Rationale: The controller already proves one-time bootstrap and the close-aware widget/Qt view
  chain already proves idempotent disposal. Moving both responsibilities at once would create a
  second lifecycle owner and broaden the slice.
  Date/Author: 2026-08-09 / architecture loop after pre-implementation review.
- Decision: Keep `build_qt_signing_shell()` as a thin test/legacy adapter for the large existing Qt
  shell suite, but remove it from the production factory path and record its retirement criterion.
  Rationale: The direct shell suite has hundreds of calls and patches this seam; deleting it without
  equivalent migration would weaken coverage. The new composition boundary must still absorb the
  implementation rather than delegate back to the old builder.
  Date/Author: 2026-08-09 / architecture loop after pre-implementation review.
- Decision: Do not rename `phase3` commands, DTOs, JSON fields, fixtures, or artifact paths in this
  slice.
  Rationale: That is a separate atomic contract migration tracked by its own ExecPlan.
  Date/Author: 2026-08-09 / architecture loop.

## Outcomes & Retrospective

To be completed after implementation and independent evaluation. Record the final commit, focused
and full validation, measured improvement, retirement grep, offscreen evidence, cleanup audit, and
any remaining composition debt here.

## Context and Orientation

`src/foliaseal/presentation/qt/signing_shell_port.py` defines the application-facing
`SigningWorkspaceBootstrap`, `SigningWorkspaceFactory`, and `SigningWorkspaceBundle`. The bootstrap
contains one document viewer workflow, one signing draft workflow, app settings, reusable signing
objects, optional repositories/material ports, and outer-edge callbacks. The bundle exposes only
maintenance, session, testing, and opaque view capabilities.

`src/foliaseal/presentation/qt/signing_shell.py` owns the concrete Qt facade. Its
`SigningWorkspaceWidget.__init__` creates a root widget/runtime and passes a large callback and
collaborator list to `build_signing_workspace_composition()`.

`src/foliaseal/presentation/qt/signing_workspace_composition.py` currently constructs the viewer,
review/text sessions, properties panel, sidebar, action/review/interaction bridges, shell surface,
testing adapter, orchestrator, and runtime binding. It returns a broad internal
`SigningWorkspaceComposition` record.

`src/foliaseal/presentation/qt/signing_workspace_shell_controller.py` installs the composition onto
the public shell facade, bootstraps once, and delegates close. `SigningWorkspaceLifecycle` in the
same package owns replacement of one workspace with another and must remain the cross-workspace
lifecycle owner.

Existing tests use fake Qt bindings and workflow/repository stand-ins. The central behavior to
preserve is opening a PDF, navigating/reviewing it, placing and previewing a signature, signing or
reporting failure, refreshing settings/reusable objects, and disposing the shell safely.

## Architecture Selection Record

Selected candidate: `qt-workspace-composition-boundary`, Candidate Priority `71.7/100`, dependency
category local-substitutable.

Selected shape: Design C, common-caller optimized typed composition request/context with an internal
host-actions adapter. The three-entry conceptual surface is:

    composition = QtSigningWorkspaceComposition.from_request(request)
    composition.bootstrap()
    bundle = composition.bundle

`QtSigningWorkspaceFactory.create(bootstrap)` is the only production caller that constructs the
request and publishes the bundle. The internal composition owns one workspace instance's assembly,
bootstrap ordering, and idempotent disposal. `SigningWorkspaceLifecycle` remains responsible for
mounting, replacement, old-widget disposal, and active-handle publication.

The reviewed design records were:

- Design A, minimal object: author `86.5`; reviewers treated it as valid only if it absorbs the old
  builder rather than wrapping a large shallow parameter bag.
- Design B, flexible finite variation/host-actions records: author `86.5`; rejected for speculative
  variation surface and lower dominant-caller simplicity.
- Design C, selected: author `90.5`; reviewer scores produced median dimensions
  `(4.5, 5.0, 4.5, 4.25, 5.0, 4.5, 5.0)` and BaseShapeScore `92.25`, with no penalties.

The selected interface must not add a service locator, generic manager, arbitrary factory registry,
raw widget exports, or infrastructure/persistence types beyond the existing bootstrap.

## Scope and Migration Inventory

In scope are `signing_shell.py`, `signing_workspace_composition.py`, `signing_shell_port.py`,
`signing_workspace_shell_controller.py` only where required by the new boundary, focused workspace
tests, `docs/ARCHITECTURE.md`, this plan, and the architecture parent plan.

The implementation must:

1. Add a typed Qt-local composition request/context and a concrete composition object.
2. Move the current construction and callback choreography behind that object; merely wrapping the
   34-argument builder is not sufficient. The existing shell controller may continue to install and
   bootstrap the assembled record while this child keeps one disposal chain.
3. Make the factory translate one unchanged bootstrap into the composition, bootstrap it once, and
   return the unchanged bundle.
4. Keep the shell facade and its user-visible methods behaviorally compatible.
5. Provide an internal, narrow host-actions adapter for current shell verbs rather than passing a
   dozen independent callback parameters through the composition.
6. Add direct tests before removing or narrowing the old construction seam.

The old `build_qt_signing_shell` helper may remain temporarily as an internal/test adapter only if
it delegates to the new boundary and its exact retirement condition is recorded. The old
`build_signing_workspace_composition` function must not remain the production construction path.

Out of scope are changes to `docs/SPEC.md`, `docs/UI_SPEC.md`, persisted schemas, CLI names/arguments,
JSON/fixture/artifact contracts, signing semantics, the Signature Library UI, broad GUI redesign, or
cross-workspace app-frame lifecycle.

## Behavior Preservation Map

- `COMP-001` — Factory construction: `QtSigningWorkspaceFactory.create(bootstrap)` returns one
  bundle with maintenance/session/testing/view capabilities. Existing evidence: app-frame factory
  tests. Replacement: direct factory/composition boundary test with bundle identity assertions.
- `COMP-002` — Bootstrap ordering: runtime binding and collaborator publication precede one-time
  orchestrator bootstrap. Existing evidence: shell-controller tests. Replacement: composition test
  with an ordered fake orchestrator and repeated-bootstrap assertion.
- `COMP-003` — Failure cleanup: a partial composition does not publish a bundle and disposes owned
  candidate resources. Existing evidence: lifecycle/controller cleanup tests. Replacement: direct
  composition failure/disposal test.
- `COMP-004` — Bundle routing: maintenance/session/testing/view methods retain their current
  behavior and no raw child widget enters the bundle. Existing evidence: port, harness, and shell
  tests. Replacement: retain these tests and add a bundle-shape/opaque-view assertion.
- `COMP-005` — User workflow: viewer refresh/navigation, text search/selection, placement, preview,
  signing, result handling, settings refresh, and reusable-object refresh remain unchanged.
  Existing evidence: `test_qt_signing_shell.py`, runtime, action, preview, and app-frame suites.
  Replacement: existing behavior suites remain green; no shallow test is deleted without equivalent
  boundary coverage.
- `COMP-006` — Cross-workspace lifecycle: compose/mount/publish/dispose ordering and idempotent close
  remain in `SigningWorkspaceLifecycle`. Existing evidence: lifecycle/host tests. Replacement:
  retain the full lifecycle suite and assert the factory remains a single-workspace constructor.

## Baseline Measurements and Predicted Improvement

Baseline commit: `f6a3ed3fc`.

Measured proxies before implementation:

- The shell widget constructor has 19 parameters including `self` (18 collaborators after `self`).
- `build_signing_workspace_composition()` has 34 keyword parameters and 12 callback-style verbs.
- `signing_shell_port.py` contains a factory keyword dictionary that repeats 12 bootstrap values.
- The construction path crosses the shell, composition helper, shell controller, port/factory, and
  lifecycle modules before the bundle is published.
- Direct shell construction is repeated throughout `tests/unit/test_qt_signing_shell.py`, while no
  direct composition-boundary test owns assembly/bootstrap/disposal behavior.
- The suite currently collects 1,169 tests after adding two direct composition-boundary tests.

Predicted normalized component improvements (0 means none, 1 means the proxy is substantially
resolved) are navigation `0.50`, change amplification `0.45`, seam-risk reduction `0.50`, boundary
test improvement `0.45`, interface compression `0.60`, cohesion `0.50`, and dependency isolation
`0.40`. The predicted weighted improvement is approximately `0.49`.

Post-implementation proxy evidence:

- Navigation units: `5 -> 4` (the production path no longer includes the factory keyword-expansion
  seam), reduction `0.20`.
- Change-amplification units: `3 -> 1` for a fixed construction change (factory, shell constructor,
  and builder body become one typed composition boundary), reduction `0.667`.
- Internal seam count: `3 -> 1` (34-argument builder, 12 callback list, and repeated factory kwargs
  become one request plus one finite host-actions record), reduction `0.667`.
- Boundary behavior coverage: `0.00 -> 0.67` across the six preservation-map behaviors; direct
  composition tests cover build-once and partial cleanup, while factory/controller/lifecycle and
  existing shell suites exercise the remaining routing/order behaviors through the new path.
- Public surface units: `3 -> 2` (factory create plus typed request; the legacy helper is test-only),
  reduction `0.333`.
- Production boundary bypasses: `1 -> 0`; `QtSigningWorkspaceFactory` no longer imports or calls
  `build_qt_signing_shell`.

Using `scripts/architecture_metrics.py improvement` with those raw counts gives component values
`(navigation 0.20, change 0.667, seam 0.667, boundary tests 0.67, interface 0.333, isolation 1.0)`
and Actual Improvement `0.574`. No component regressed; this exceeds the `0.15` acceptance gate.

## Refactor Acceptance Contract

Hard gates:

- `SigningWorkspaceBootstrap`, `SigningWorkspaceBundle`, `SigningWorkspacePort`,
  `SigningWorkspaceSessionPort`, `SigningWorkspaceTestingPort`, and `WorkspaceViewPort` retain their
  existing fields and behavior.
- `QtSigningWorkspaceFactory.create()` is the only production composition entry and returns only a
  fully composed, bootstrapped bundle.
- The old 34-argument builder is absorbed or made private; it is not called by production factory
  code. No new generic manager, service locator, registry, or arbitrary callback dictionary exists.
- `SigningWorkspaceLifecycle` remains the only owner of cross-workspace mount/replacement/dispose
  ordering.
- No raw child widgets, storage paths, concrete certificate stores, or infrastructure DTOs leak
  through the composition request or bundle.
- Existing current-page placement, preview/signing behavior, CLI/JSON/artifact contracts, and the
  frozen SPEC/UI_SPEC content remain unchanged.
- Boundary tests cover construction, ordering, failure cleanup, idempotence, bundle shape, and fake
  substitution before any old shallow test is removed.

Validation commands:

    .venv/bin/ruff check .
    .venv/bin/python -m compileall -q src tests
    .venv/bin/python -m pytest -q <focused composition/workspace tests>
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence
    .venv/bin/python -m pytest -q
    git diff --check

The focused and full suites must pass with no new warnings; the offscreen evidence must report the
existing acceptance/parity/fit-rejection success counters, and no FoliaSeal/Python/Qt/test process
or generated acceptance output may remain after cleanup. SPEC/UI_SPEC hashes must remain unchanged
from the baseline for this implementation slice.

## Plan of Work

First define the composition request/context and internal host-actions adapter at the Qt edge without
changing the application bootstrap or public bundle. Then move the current builder body into the
composition object's private assembly method. The composition must create the runtime, sessions,
widgets, bridges, shell surface, testing adapter, and orchestrator, bind the runtime, install the
facade, and expose a one-time bootstrap/dispose lifecycle.

Next change `QtSigningWorkspaceFactory.create()` to delegate the unchanged bootstrap through the
shell adapter, where the composition is built and the existing controller bootstraps it once before
the bundle is returned. Reduce `SigningWorkspaceWidget.__init__` to outer Qt container setup and
composition delegation. Keep `SigningWorkspaceShellController` and
`QtWorkspaceView` as internal lifecycle collaborators; do not duplicate their idempotent behavior.

Add direct boundary tests for success, ordering, repeated bootstrap, partial-build cleanup,
idempotent disposal, bundle identity, and fake bindings/host actions. Migrate only the direct callers
needed to make the factory the production path. If the old helper remains for tests, make it a thin
delegator and record its exact retirement grep in this plan.

Finally update the architecture map and parent ledger with the actual ownership, measurements,
validation transcripts, cleanup audit, and commit. Do not mix Signature Library work, UI redesign,
phase3 renaming, or README changes into this child.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`. Before editing, confirm `git status --short` is clean
and record the baseline commit. During implementation, keep generated evidence under an exact
temporary/ignored directory and remove it after each run.

After each logical migration, run the focused workspace boundary tests. Before completion run Ruff,
compileall, the focused suite, the offscreen evidence command, the full suite, `git diff --check`,
and process/artifact audits. If a test exposes a callback-order regression, fix the composition
boundary and add the behavior to `COMP-002` rather than weakening the test.

## Validation and Acceptance

Acceptance is behavioral: opening a representative PDF through the app-frame factory still mounts a
usable workspace; navigation, review, placement, preview, signing, settings refresh, and close all
behave as before; a failed composition leaves no published partial workspace; repeated bootstrap and
close are harmless; harness callers receive the same typed bundle; and offscreen signed evidence
passes without residual processes or artifacts.

The architecture acceptance additionally requires that a maintainer changing workspace construction
can edit one typed composition boundary rather than coordinating the old 34-argument helper,
factory keyword dictionary, and widget constructor independently. Re-run the baseline proxy counts
and record Actual Improvement. Accept only if Actual Improvement is at least `0.15` and no component
regresses by more than `0.10`.

## Idempotence and Recovery

The composition constructor must fail without publishing a bundle. Explicitly disposable partial
resources (currently the properties-panel preview lifecycle) are registered and disposed exactly
once; Qt child widgets remain owned by their parent container. The live shell close path invokes the
composition's idempotent cleanup, while the shell controller remains the fallback destruction guard.
Repeated `bootstrap()` and `dispose()` calls are no-ops after the first successful operation.
Existing workspace replacement remains recoverable through
`SigningWorkspaceLifecycle`; do not use resets or destructive cleanup commands. Generated evidence
may be removed only from the exact run directory created for this plan.

## Artifacts and Notes

Keep generated matrix output outside Git. Record concise focused/full test counts, offscreen counters,
SPEC/UI_SPEC hash checks, retirement grep, process audit, and before/after proxy counts in this plan
and the parent plan. Do not commit PDFs, credentials, screenshots, or matrix run directories.

## Interfaces and Dependencies

The required public production call remains:

    bundle = QtSigningWorkspaceFactory().create(bootstrap)

The composition request/context and internal host-actions adapter are Qt-presentation concerns. They
may depend on `SigningWorkspaceBootstrap`, dynamic Qt bindings, current application workflows, and
approved fake seams. They must not depend on a global registry or expose concrete persistence,
certificate, or child-widget types to the app-frame/harness bundle. The composition must return the
existing `SigningWorkspaceBundle` and use the existing `SigningWorkspaceShellController` and
`QtWorkspaceView` lifecycle behavior rather than introducing a second replacement owner.

## Outcomes & Retrospective (completed 2026-08-09)

Implementation is complete pending the repository commit gate. `QtSigningWorkspaceFactory.create()`
now delegates one unchanged bootstrap to `SigningShellAdapter.create_from_bootstrap()`. The typed
`QtSigningWorkspaceCompositionRequest` and `QtSigningWorkspaceHostActions` hide the widget graph and
callback choreography; `QtSigningWorkspaceComposition` owns runtime construction, build-once behavior,
idempotent bootstrap/disposal, and partial-build cleanup. The shell controller still owns publication
and the one-time assembled-record bootstrap, and `SigningWorkspaceLifecycle` remains the only
cross-workspace replacement owner.

The independent compliance review initially found that composition disposal was not connected to
normal shell close. That finding was fixed by storing the composition boundary on the shell and routing
the close-aware widget through it; the existing controller destruction guard remains idempotent. The
review found no import cycle, SPEC/UI_SPEC change, bundle-port change, production bypass, or behavior
regression. `build_qt_signing_shell()` remains exported solely for the large direct shell-test suite;
retirement condition: `rg -n "build_qt_signing_shell" src tests` must show only the compatibility
adapter, package lazy export, and tests before it is deleted.

Validation completed: focused workspace/composition/AppFrame/shell suites `141 passed`; full suite
`1150 passed, 19 skipped, 1 warning`; Ruff and compileall passed. The bounded offscreen acceptance
command was attempted with `QT_QPA_PLATFORM=offscreen` and a 30-second timeout; it timed out without
writing a summary or leaving processes/artifacts, so its acceptance counters remain an
external-environment limitation rather than a claimed pass. `git diff --check` remains the final
commit gate.
