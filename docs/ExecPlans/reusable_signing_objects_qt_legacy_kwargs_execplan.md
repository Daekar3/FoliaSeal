# Retire Qt legacy reusable-catalog inputs

This ExecPlan is a living document and must remain compliant with
`.agents/skills/write-execplan/PLANS.md`. The governing loop is
`docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`; `docs/SPEC.md` is frozen.

## Purpose / Big Picture

The production Qt signing workspace already has one canonical `ReusableSigningObjects` service,
constructed by `FoliaSealAppFrame` and transported through workspace opening and shell composition.
The low-level shell factory and the application coordinator still accept older
`preset_catalog`/`preset_catalog_store` inputs, and can construct a second service when the
canonical one is omitted. That compatibility branch keeps callers coupled to persistence-shaped
objects and leaves room for split-brain reusable-object state.

After this slice, shell and coordinator callers must supply the existing canonical
`ReusableSigningObjects` instance. The shell factory will no longer accept or synthesize from
catalog-shaped inputs; the coordinator will no longer retain its legacy catalog fields or fallback
constructor path. AppFrame remains the persistence composition root and may still accept a
`preset_catalog_store` so it can construct the one service it owns. Preset/profile JSON, selection,
save/delete/compose behavior, placement `current_page`, signing/preview behavior, CLI/JSON/artifact
contracts, and all historical phase3 names remain unchanged.

The change is observable through focused Qt/coordinator tests: a missing reusable service fails at
the boundary, a supplied service identity reaches the shell and coordinator unchanged, and all
existing preset/profile workflows continue to pass using an in-memory repository. No live GUI is
required for the boundary tests; the unchanged offscreen acceptance command provides end-to-end
evidence afterward.

## Child ExecPlan Dependencies

- [x] The reusable-object source-of-truth boundary is implemented and committed at `b3276a78b`.
- [x] The canonical `ReusableSigningObjects` identity is already threaded through
  `SigningWorkspaceEnvironment`, `OpenWorkspaceCommand`, `SigningWorkspaceBootstrap`, workspace
  composition, and the properties panel.
- [x] Scan Round 57 identified the legacy Qt/coordinator kwargs cluster at Candidate Priority
  approximately `67.2`, confidence `0.95625`.
- [x] Design Selection 57 selected the common-caller concrete-service shape at Refactor Shape
  Score `87.0`, with two independent reviews and no evidence-backed penalties.
- [x] The rendered-fit cycle is closed and generated acceptance outputs have been removed.

## Progress

- [x] (2026-08-08) Captured the clean baseline, legacy-kwarg inventory, production call path, and
  existing identity-construction sites.
- [x] (2026-08-08) Compared minimal, flexible-protocol, and common-caller designs; selected the
  required concrete `ReusableSigningObjects` boundary.
- [x] (2026-08-08) Added required-service constructor tests and test-only fixture normalizers so the
  broad historical shell/coordinator tests continue to exercise equivalent in-memory/store-backed
  behavior while production signatures are migrated.
- [x] (2026-08-08) Removed legacy catalog fields, fallback construction, and source-selection
  branches from the production shell factory and coordinator; preserved AppFrame store injection
  only. The production retirement grep is now empty for the target modules.
- [x] (2026-08-08) Added direct production identity/fail-fast assertions and centralized the
  test-only fixture normalizer in `tests/support/signing_builders.py`; no unit test imports another
  unit test for the adapter.
- [x] (2026-08-08) Focused suite passed (`216`), full suite passed (`1166`, one pre-existing
  Pillow warning), Ruff/compileall/diff/SPEC checks passed, and the offscreen acceptance command
  passed with `10` scenarios/`7` successful signings, preview parity `18/18`, and fit rejection
  `3/3`. The command-generated acceptance directory and summary were removed; unrelated pre-existing
  `artifacts/` evidence is retained.
- [ ] Reconcile final plan/parent status, commit, and complete three independent closure audits.

## Surprises & Discoveries

- Observation: The production graph already transports a required reusable service, so the shell
  fallback is not needed by AppFrame, workspace-open, harness, or composition callers.
  Evidence: `app_frame.py:287-318`, `app_frame_workspace_open.py:137-146`,
  `signing_shell_port.py:31-47,250-257`, and `signing_workspace_composition.py:127-158`.
- Observation: The low-level shell and coordinator are the remaining production source-selection
  branches; current shell tests still use both legacy keyword forms.
  Evidence: `signing_shell.py:421-455,531-564`,
  `signature_properties_coordinator.py:250-277`, and 70 `preset_catalog*=` occurrences across
  `src` and `tests` at baseline.
- Observation: AppFrame's `preset_catalog_store` is a legitimate persistence injection at the
  composition root, not a duplicate shell service source.
  Evidence: `app_frame.py:287-288` constructs `_reusable_objects` once and passes it through the
  workspace environment; it must remain outside this retirement gate.

- Observation: Migrating all 107 shell factory calls and 45 coordinator constructions one by one
  would add broad mechanical churn without changing behavior. The focused tests now use one clearly
  named test-only adapter that translates historical fixture inputs to an in-memory or supplied
  `ReusableSigningObjects`; it imports no production compatibility code.
  Evidence: `tests/support/signing_builders.py` owns the test-only adapter, while the production
  retirement grep remains empty.

## Decision Log

- Decision: Require concrete `ReusableSigningObjects` on the shell factory and coordinator rather
  than introducing a new protocol.
  Rationale: all known production callers already use the concrete service; a broader protocol would
  add public surface without a second implementation, while the existing in-memory repository and
  fake service tests still provide substitution at the boundary.
  Date/Author: 2026-08-08 / Codex and independent design reviewers.
- Decision: Retain `preset_catalog_store` only on AppFrame and its top-level adapter functions.
  Rationale: AppFrame owns persistence construction and is the one place where a repository/store is
  an appropriate dependency. Removing it there would move storage policy into a lower-level shell
  and violate ownership clarity.
  Date/Author: 2026-08-08 / Codex.
- Decision: Keep the test-only fixture normalizer in `tests/support/signing_builders.py` only for
  this bounded migration slice, with
  no production import or runtime compatibility path.
  Rationale: the focused fixture migration spans 152 direct construction/call sites; local
  normalizers keep this slice behaviorally bounded while the production retirement gate is strict.
  It is a test fixture rather than a runtime compatibility surface and has a follow-up removal gate
  after the historical fixtures are mechanically rewritten.
  Date/Author: 2026-08-08 / Codex.
- Decision: Do not rename phase3 modules, commands, DTOs, JSON keys, fixtures, or artifacts in this
  slice. The atomic migration remains governed by
  `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md`.
  Rationale: combining a contract-sensitive rename with constructor ownership removal would obscure
  parity failures and violate the one-purpose change slice.
  Date/Author: 2026-08-08 / Codex.

## Outcomes & Retrospective

Baseline commit is `bdde2f12a`. The targeted shell/coordinator files contain 14
`preset_catalog*` references, the repository has 70 legacy keyword call occurrences across source
and tests, and the relevant files are 576 lines (`signing_shell.py`) and 773 lines
(`signature_properties_coordinator.py`). Five production construction sites currently create a
`ReusableSigningObjects`; after the slice, only AppFrame and the two explicit harness composition
roots should remain, while shell/coordinator construction disappears.

The fixed six-component prediction (excluding the loop's candidate-only cohesion dimension) was
`0.72`, from component estimates navigation `.70`, change amplification `.75`, seam reduction
`.70`, boundary-test improvement `.65`, interface compression `.75`, and isolation `.80`.
Post-change measurements use the same repeatable proxies: production workflow navigation units
`6 -> 6` (AppFrame, workspace-open, shell, coordinator, service, persistence); source-selection
branches `2 -> 0`; duplicate target-pair service-construction seams `2 -> 0`; accepted production
input concepts `6 -> 2`; target production legacy references `14 -> 0`; and direct canonical
boundary-behavior coverage `.50 -> 1.00`. The helper calculation is components
`(0.00, 1.00, 1.00, 0.50, 0.666667, 1.00)`, Actual Improvement `0.65`, worst component `0.00`,
prediction accuracy `0.902778`, and the half-prediction gate passes. No component regressed beyond
`.10`.

Validation evidence: focused `216` passed; full `1,166` passed with one pre-existing Pillow
warning; Ruff, compileall, diff, and frozen-SPEC checks passed; offscreen acceptance reported
`10` scenarios/`7` successful signings, parity `18/18`, and fit rejection `3/3`. The generated
acceptance directory and summary were removed, unrelated baseline artifacts were left untouched,
and the process audit is empty. Commit ID and post-commit closure audits are recorded below when
complete.

## Context and Orientation

`FoliaSealAppFrame` in `src/foliaseal/presentation/qt/app_frame.py` is the top-level Qt composition
root. It accepts a `SignaturePresetCatalogStore`, constructs one `ReusableSigningObjects`, and puts
that service in `SigningWorkspaceEnvironment`. `WorkspaceOpenService` copies it into
`OpenWorkspaceCommand`; `SigningWorkspaceBootstrap`, `SigningWorkspaceComposition`, and
`SignaturePropertiesPanel` already require and forward it.

`SigningShellAdapter.create()` and `build_qt_signing_shell()` in
`src/foliaseal/presentation/qt/signing_shell.py` are lower-level factories. They currently accept
the canonical service plus optional legacy catalog/catalog-store inputs, reject contradictory mixes,
and construct a service when the canonical value is absent. That fallback is the target to remove.

`DefaultSignaturePropertiesCoordinator` in
`src/foliaseal/application/signature_properties_coordinator.py` has the same legacy fields and
fallback in `__post_init__`; all coordinator reads and writes already use `self.reusable_objects`
after the prior source-of-truth slice. Its direct unit tests are the main fixture migration surface.

The interactive and signed-acceptance harnesses construct their own service at explicit operation
roots (`phase3_harness_session_runner.py` and `phase3_signed_acceptance_matrix_runner.py`) and pass
it through the typed bootstrap. They are not shell-level legacy callers and must retain their
current behavior and historical names.

## Plan of Work

First add boundary tests that make the chosen contract executable. A shell/coordinator construction
without `reusable_objects` must fail immediately with the existing required-service wording. A fake
or in-memory `ReusableSigningObjects` supplied by the caller must be the exact object observed by
the composed properties panel/coordinator and the workspace bundle; no second service may be
constructed. Migrate direct coordinator tests that currently pass `preset_catalog=` to build
`ReusableSigningObjects(InMemoryCatalogRepository(catalog))`, preserving any persistence tests by
using the real `SignaturePresetCatalogStore` inside that service. Migrate direct shell tests in the
same manner, including tests that currently pass `preset_catalog_store=` or `preset_catalog=`.

Next remove `preset_catalog` and `preset_catalog_store` parameters and the fallback branch from
`SigningShellAdapter.create()` and `build_qt_signing_shell()`. Make `reusable_objects` required and
forward it unchanged. Remove now-unused catalog model/store imports from that module. Do not alter
AppFrame's top-level store parameters or its one-time service construction.

Then remove `preset_catalog`, `preset_catalog_store`, the contradictory-input guard, and fallback
construction from `DefaultSignaturePropertiesCoordinator`. Make `reusable_objects` required and
preserve all coordinator behavior through the existing snapshot/command API. Update any direct
application tests and setup-session fixtures that still construct the coordinator with legacy
catalog inputs.

Finally search the full repository. The production retirement gate is zero `preset_catalog=` or
`preset_catalog_store=` calls in `src/foliaseal/presentation/qt/signing_shell.py`,
`src/foliaseal/presentation/qt/signing_workspace_*.py`, and
`src/foliaseal/application/signature_properties_coordinator.py`. AppFrame's store parameter and
historical plan text may remain; no compatibility branch may remain in the shell or coordinator.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

1. Capture the clean baseline and focused tests:

       git status --short --branch
       rg -n "preset_catalog(_store)?" src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/signature_properties_coordinator.py
       .venv/bin/pytest -q tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py

   Baseline is commit `bdde2f12a`, with 14 target-file references and a green pre-existing focused
   suite. Do not edit `docs/SPEC.md`.

2. Add required-service and identity tests before removing fallback code. Use
   `ReusableSigningObjects(InMemoryCatalogRepository(...))` and existing fake Qt bindings. Verify
   failure messages, object identity, profile/preset selection, save/delete/compose, refresh, and
   placement `current_page` behavior.

3. Migrate all direct shell/coordinator fixtures and remove the target legacy parameters/branches.
   Run the focused shell, workspace, setup-session, reusable-object, and coordinator suites. The
   target grep must show no shell/coordinator legacy kwargs or fallback construction.

4. Run comprehensive validation:

       .venv/bin/pytest -q
       .venv/bin/ruff check src tests scripts
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       .venv/bin/python -c "from foliaseal.application.reusable_signing_objects import ReusableSigningObjects; print('reusable service import: PASS')"
       git diff --check
       git diff --exit-code -- docs/SPEC.md

5. Run unchanged offscreen acceptance:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios/`7` successful signings, preview parity `18/18`, and fit
   rejection `3/3`. Remove only `artifacts/signed_acceptance_evidence/` and
   `artifacts/phase3_signed_acceptance_evidence_summary.md`, then audit processes with:

       pgrep -af 'foliaseal|pytest|PySide|Qt' | rg -v 'bwrap|codex|pgrep' || true

6. Reconcile `docs/ARCHITECTURE.md`, this child plan, the parent plan, and the phase3 nomenclature
   plan inventory. Record exact before/after grep counts, focused/full test counts, offscreen counts,
   actual-improvement measurements, and commit IDs. Commit intentionally, then run three fresh
   independent post-commit closure audits.

## Validation and Acceptance

Acceptance requires the concrete reusable service to be mandatory on shell/coordinator boundaries,
the exact supplied identity to reach the composed panel/workspace, and no production shell or
coordinator fallback construction from a catalog. AppFrame may still construct the service from its
injected persistence store. All existing reusable-object, coordinator, Qt shell, workspace, setup,
preview, signing, and current-page behavior must remain green. No persisted JSON, CLI, DTO, artifact,
or phase3 contract may change.

The focused migration suites, full pytest suite, Ruff, compileall, CLI help, SPEC diff, import check,
offscreen matrices, generated-artifact cleanup, process audit, and three independent closure reviews
must pass. The measured Actual Improvement must be at least `.15`, and no component may regress by
more than `.10`. No production caller may bypass the required service boundary, and no shell or
coordinator `preset_catalog*` compatibility input may remain. The worktree must be clean after the
commit and generated-output cleanup.

## Idempotence and Recovery

Fixture migration is repeatable: construct a fresh in-memory repository/service for each test and
reuse existing temporary profile stores for persistence tests. If a test reveals a caller that still
needs a catalog, migrate that caller to a service at its explicit composition root; do not restore a
shell/coordinator fallback. If a custom factory fixture is genuinely external to the repository,
record it and add a narrow test-support adapter with an explicit removal gate rather than widening
the production API. If behavior diverges, keep the failing characterization test, inspect the
service snapshot/command path, and repair the migration without changing persisted schemas or
phase3 contracts.

## Artifacts and Notes

This is one behavior-preserving architecture slice. Allowed generated artifacts are only the
transient offscreen acceptance directory and summary; both must be removed before closure. The
source, tests, architecture docs, parent/child plan updates, and commit form the durable change.
Do not mix phase3 nomenclature renames, GUI redesign, schema migration, broad formatting, or new
CLI commands into this slice.

Baseline evidence:

    target shell/coordinator legacy references: 14
    src+tests legacy keyword occurrences: 70
    reusable-service construction sites: 5 (one shell fallback, one coordinator fallback, AppFrame, and two harness roots)
    full suite at baseline: 1,163 passed, 1 warning

Closure evidence (2026-08-08): target production legacy references `0`; source/test keyword
occurrences remain only in the explicitly test-only fixture adapter and AppFrame persistence
composition; full suite `1,166 passed, 1 warning`; offscreen acceptance `10/7`, parity `18/18`,
fit rejection `3/3`; generated acceptance outputs removed; no FoliaSeal/pytest/Qt process remains.

## Interfaces and Dependencies

The final production signatures must be equivalent to the following. `ReusableSigningObjects` is the
existing application service; do not create a new service locator or protocol solely for this slice.

In `src/foliaseal/presentation/qt/signing_shell.py`:

    SigningShellAdapter.create(
        *,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        reusable_objects: ReusableSigningObjects,
        ...
    ) -> Any

    build_qt_signing_shell(
        *,
        viewer_workflow: ViewerWorkflow,
        signing_workflow: SigningDraftWorkflow,
        reusable_objects: ReusableSigningObjects,
        ...
    ) -> Any

In `src/foliaseal/application/signature_properties_coordinator.py`:

    DefaultSignaturePropertiesCoordinator(
        workflow: SigningDraftWorkflow,
        ...,
        reusable_objects: ReusableSigningObjects,
    )

`SigningWorkspaceEnvironment`, `OpenWorkspaceCommand`, `SigningWorkspaceBootstrap`,
`build_signing_workspace_composition`, and `SignaturePropertiesPanel` already use the same
required service and must continue forwarding it without constructing or adapting a catalog.
`FoliaSealAppFrame` remains the only production owner that turns `SignaturePresetCatalogStore` into
the canonical service. Tests may use `InMemoryCatalogRepository` and the concrete service; no
Pillow, pyHanko, Qt, filesystem path, or persisted schema type may appear in the new boundary beyond
the existing Qt factory's widget bindings and AppFrame's explicit repository injection.

## Change Log

- 2026-08-08: Created from Scan Round 57 and Design Selection 57. Selected the common-caller
  required-concrete-service shape at Refactor Shape Score `87.0`; AppFrame persistence injection and
  the separate phase3 nomenclature migration remain explicitly out of scope.
