# Thread the canonical reusable-signing service through the Qt workspace

This ExecPlan is a living document and must remain compliant with
`.agents/skills/write-execplan/PLANS.md`. The parent loop state is
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`.

## Purpose / Big Picture

The application frame already creates one `ReusableSigningObjects` service for the reusable-object
library, but the active signing workspace still transports `preset_catalog` and
`preset_catalog_store` through several Qt constructors. The properties panel then constructs another
service around the same store. That duplication makes the GUI harder to follow and allows a library
refresh and an active signing panel to observe different service instances.

After this slice, AppFrame owns one service for the lifetime of the workspace environment and passes
that exact object through `OpenWorkspaceCommand`, `SigningWorkspaceBootstrap`, the shell factory,
workspace composition, and `SignaturePropertiesPanel` into
`DefaultSignaturePropertiesCoordinator`. Production Qt code no longer accepts or forwards reusable
catalog/store persistence objects. Existing test and headless-harness builders may retain a one-way
legacy adapter temporarily, but they cannot combine it with the canonical service and they must have a
grep-verifiable retirement condition. Profile JSON, stable IDs, signing behavior, phase3 command/DTO/
JSON/artifact contracts, and certificate repository/material-port threading remain unchanged.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` is frozen and unchanged.
- [x] `ReusableSigningObjects` owns the immutable snapshot/index/compose boundary from
  `docs/ExecPlans/reusable_catalog_source_of_truth_execplan.md`.
- [x] AppFrame already constructs `self._reusable_objects` at
  `src/foliaseal/presentation/qt/app_frame.py:287-289`.
- [x] Scan Round 46 and Design Selection 48 selected this bounded seam at approximately Priority
  `64`, with confidence about `.94`.

## Progress

- [x] (2026-08-06) Reconfirmed clean baseline commit `356b97eed`, the workspace graph, production
  callers, harness callers, tests, and phase3 contract boundaries.
- [x] (2026-08-06) Captured Scan Round 46 evidence and selected the constrained direct-service shape.
- [x] (2026-08-06) Compared minimal, protocol/resource, and common-caller designs; selected Design C
  at reviewed shape score approximately `88`.
- [x] (2026-08-06) Add `reusable_objects` to the environment, open command, bootstrap, shell/factory/widget,
  composition, and panel, forwarding the same object identity without reconstruction.
- [x] (2026-08-06) Remove production Qt `preset_catalog`/`preset_catalog_store` transport and migrate harness/test
  builders to explicit services or isolated one-way adapters.
- [x] (2026-08-06) Add identity, fake-boundary, shared-refresh, import-firewall, and missing-service tests while
  preserving existing signing/phase3 evidence behavior.
- [x] (2026-08-06) Run focused/full validation, offscreen evidence, SPEC/import/process audits, and
  reconcile docs. Commit and the three fresh post-commit explorers remain the closure gate.
- [x] (2026-08-06) Incorporated the post-commit audit: required service fields are now non-optional,
  first-party acceptance harness callers construct the service explicitly, and panel-to-coordinator
  identity is asserted directly.

## Surprises & Discoveries

- Observation: AppFrame and the reusable-object library already share one concrete service, but the
  active workspace graph does not receive it.
  Evidence: `app_frame.py:287-289,313-318` creates/passes only `preset_catalog_store`; the library
  receives `_reusable_objects` separately.
- Observation: the service can be silently rebuilt by the coordinator when the panel receives a store.
  Evidence: `signature_properties_coordinator.py:268-277`.
- Observation: low-level shell tests call `build_qt_signing_shell(..., preset_catalog_store=store)`.
  Evidence: `tests/unit/test_qt_signing_shell.py` around the direct builder tests. These are explicit
  compatibility edges, not permission to leave persistence types in production graph signatures.
- Observation: phase3 harnesses use the shell builder but their public commands and evidence files are
  frozen. They must construct/pass a service without changing command or serialized contracts.

## Decision Log

- Decision: Thread the concrete `ReusableSigningObjects` identity directly instead of introducing a
  broad service context or registry.
  Rationale: the existing service is application-owned, local-substitutable, and already has the
  exact behavior the panel needs. A context would create hidden dependencies; a new protocol would
  duplicate an abstraction without current variation.
  Date/Author: 2026-08-06 / Codex.
- Decision: Make production environment/bootstrap/service fields required, while keeping low-level
  builder adapters only where existing tests or harnesses still need them.
  Rationale: a nullable production field would preserve the duplicate-service failure mode. Explicit
  missing-service failures are easier to diagnose, and test-edge adapters can be removed when the
  retirement grep is clean.
  Date/Author: 2026-08-06 / Codex.
- Decision: Keep certificate catalog/repository/material-port threading unchanged.
  Rationale: this slice owns reusable signing objects only; certificate-source mismatch and placement
  profile semantics are separately ranked follow-ups. Mixing them would broaden the migration and
  obscure phase3 acceptance evidence.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename phase3 modules, commands, DTOs, JSON keys, fixtures, or artifacts in this
  service-threading slice. The separate `phase3_nomenclature_retirement_execplan.md` is the one-slice
  atomic migration plan for replacing that label across implementation names, CLI/docs, tests, and
  contracts; it must be executed as a dedicated follow-up rather than leaving mixed aliases here.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

Implementation is closed at commit `7c21d4fc2`. Baseline evidence was 12 production
Qt transport sites forwarding `preset_catalog`/`preset_catalog_store` across eight modules, one
AppFrame-owned service that did not reach the active panel, and 45 focused reusable/coordinator/
workspace tests from the prior slice. Measured results are one identity from AppFrame through the
workspace bootstrap to the properties coordinator, zero legacy transport in the production workspace
modules, explicit required-service typing plus missing-service guards at open/factory/composition/
panel/widget boundaries, 206 focused tests passing, and 1,142 full tests passing with one pre-existing
Pillow deprecation warning.
Ruff, compileall, Qt import isolation, CLI help, diff-check, and the offscreen acceptance matrices all
pass (`10/7`, `18/18`, `3/3`). The qualitative improvement is accepted at `.48` predicted with no
observed regression over `.10`; the phase3 nomenclature migration remains a separately governed
atomic one-slice plan. Three final closure explorers found no blocker; they confirmed a clean worktree,
unchanged SPEC, no product processes, and the documented low-level shell compatibility edge as the
only remaining legacy seam.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` is the composition root: it owns the profile store,
certificate store, material port, and `ReusableSigningObjects`. `SigningWorkspaceEnvironment` in
`signing_workspace_host.py` creates an `OpenWorkspaceCommand` in `app_frame_workspace_open.py`.
`SigningWorkspaceBootstrap` in `signing_shell_port.py` reaches the shell factory; the shell factory
and `SigningWorkspaceWidget` call `build_signing_workspace_composition()`; that function creates
`SignaturePropertiesPanel`, which creates the application coordinator.

The current graph passes a profile store through all those layers. The target graph passes only the
already-constructed `ReusableSigningObjects` service. Qt owns widgets and event wiring; the service
owns reusable catalog snapshots, typed refs, duplicate/reference policy, composition, and persistence.
The service is borrowed, not disposed, when a workspace closes. Certificate repositories and the
`CertificateSigningMaterialPort` continue through their existing application-owned ports.

## Plan of Work

Add a required `reusable_objects: ReusableSigningObjects` field to
`SigningWorkspaceEnvironment`, `OpenWorkspaceCommand`, and `SigningWorkspaceBootstrap`. Their
`command_for()`, `open_workspace()`, and factory `create()` methods must forward the same object
unchanged. Add the keyword to `SigningShellAdapter.create()`, `build_qt_signing_shell()`,
`SigningWorkspaceWidget`, and `build_signing_workspace_composition()`. The composition function passes
the object to `SignaturePropertiesPanel`, which passes it to the coordinator.

At AppFrame's environment construction, pass `self._reusable_objects` instead of only
`self._preset_catalog_store`. Remove `preset_catalog` and `preset_catalog_store` from production Qt
function signatures and imports in `app_frame_workspace_open.py`, `signing_workspace_host.py`,
`signing_shell_port.py`, `signing_workspace_composition.py`, `signing_shell.py`, and
`signing_workspace_properties_panel.py`. The coordinator receives the canonical service and therefore
does not rebuild one. The low-level shell adapter remains the sole explicit compatibility edge until
the nomenclature plan's atomic migration removes its historical callers.

Where direct builder tests or phase3 harnesses still call a low-level shell builder with a store,
retain a narrow deprecated adapter at that edge: if `reusable_objects` is absent, construct exactly
one `ReusableSigningObjects` from the provided store or in-memory catalog; if both are supplied, raise
the existing canonical/legacy conflict error. Do not let the adapter cross into environment/bootstrap
production fields. Migrate first-party harness callers to construct the service explicitly wherever
that does not change their public command or artifact contract.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

1. Capture baseline transport and tests:

       git status --short
       rg -n "preset_catalog(_store)?" src/foliaseal/presentation/qt
       .venv/bin/pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_signing_workspace_host.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py

   The checkout must be clean, the grep must show the duplicated transport, and the focused tests
   must pass before edits.
2. Thread the service identity through environment, command, bootstrap, factory, widget, composition,
   and panel. Add fake/spy tests asserting `id(app_frame._reusable_objects)` reaches the panel
   coordinator unchanged and that a workspace replacement does not dispose the service.
3. Migrate production callers and preserve explicit low-level compatibility only at test/harness
   edges. Add import-firewall checks proving the listed Qt modules no longer import
   `infra.config.profile_storage` or annotate `SignaturePresetCatalogStore`.
4. Run focused tests, the complete suite, static checks, CLI help, and import isolation:

       .venv/bin/pytest -q tests/unit/test_qt_app_frame_workspace_open.py tests/unit/test_signing_workspace_host.py tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_reusable_signing_objects.py
       .venv/bin/pytest -q
       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       .venv/bin/python -c "import foliaseal.presentation.qt.app_frame_workspace_open, foliaseal.presentation.qt.signing_shell_port, foliaseal.presentation.qt.signing_workspace_composition, foliaseal.presentation.qt.signing_workspace_properties_panel; print('Qt import isolation: PASS')"
       git diff --check
5. Run the unchanged offscreen acceptance command:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and
   fit rejection `3/3`. Remove its generated summary, audit processes, and verify
   `git diff --exit-code -- docs/SPEC.md`.
6. Update `docs/ARCHITECTURE.md`, this plan, and the parent with measured grep/test counts and the
   compatibility retirement gate. Commit source/tests/docs intentionally, then run three fresh
   independent explorer-light scans against the clean commit.

## Validation and Acceptance

Acceptance requires one object-identity chain: AppFrame service -> environment -> open command ->
bootstrap -> shell/factory/widget -> composition -> panel -> coordinator. Production Qt modules may
not accept or forward `preset_catalog` or `preset_catalog_store`, and no second
`ReusableSigningObjects` may be constructed on that path. Test fakes may omit `_repository`, catalog
models, and persistence paths. Workspace close/reopen leaves the shared service usable; a library save
followed by panel refresh sees the same names, and a panel save followed by library view sees the same
snapshot. Existing signing, reusable-object, Qt, phase3 evidence, JSON, CLI, and `current_page`
behavior remain green. Full tests, static/import checks, offscreen matrices, SPEC diff, process audit,
and generated-summary cleanup must pass. The low-level `SigningShellAdapter`/`build_qt_signing_shell`
edge is the only documented compatibility exception: it may synthesize one service when invoked
directly by an old harness with a store/catalog, and rejects mixed inputs; production workspace
boundaries are strict. Actual Improvement must be at least `.15` with no component regression beyond
`.10` before accepting the cycle.

## Idempotence and Recovery

Threading fields and forwarding changes are repeatable. If a builder receives both a service and legacy
store, fail explicitly and migrate the caller; never silently create a second service. If a Qt test
fails, inspect the captured identity and restore only test-local temporary stores. Do not modify
phase3 serialized artifacts or delete user profile data. If concrete coupling proves harmful, record
the evidence and use the one permitted design redesign toward the narrow application protocol; do not
introduce a service locator.

## Artifacts and Notes

No generated artifact may change except the transient signed-evidence summary, which must be deleted
before commit. Phase3 source names, CLI output, DTOs, JSON keys, fixtures, and artifact paths are
frozen. Closure evidence should include:

       production transport grep: 0 legacy kwargs outside explicit compatibility edges
       identity test: app-frame service is panel/coordinator service
       signed_acceptance_matrix: PASS (10 scenarios, 7 successful signings)
       signed_preview_parity_matrix: PASS (18 scenarios, 18 successful signings)
       signed_fit_rejection_matrix: PASS (3 scenarios, 0 successful signings)

## Interfaces and Dependencies

Use the existing application class; do not add a service locator or broad context:

    class SigningWorkspaceEnvironment:
        reusable_objects: ReusableSigningObjects

    class OpenWorkspaceCommand:
        reusable_objects: ReusableSigningObjects

    class SigningWorkspaceBootstrap:
        reusable_objects: ReusableSigningObjects

    def build_qt_signing_shell(
        ..., *, reusable_objects: ReusableSigningObjects, ...
    ) -> Any: ...

    class SignaturePropertiesPanel:
        def __init__(self, *, reusable_objects: ReusableSigningObjects, ...) -> None: ...

All these fields borrow the same service identity. The only persistence dependency remains inside the
service's `CatalogRepository`; Qt modules import the application service type, not
`SignaturePresetCatalogStore`. Certificate repository/material ports remain unchanged. A compatibility
builder may accept old store/catalog kwargs only when no canonical service is supplied, and its removal
condition is an `rg`-verifiable absence of those kwargs from production Qt callers.

## Change Log

- 2026-08-06: Created from Scan Round 46 and Design Selection 48. Selected constrained direct-service
  threading; explicitly rejected broad service contexts, service locators, phase3 renames, and
  production persistence/store transport.
