# Deepen the reusable-signing catalog boundary

This ExecPlan is a living document. It is maintained according to `.agents/skills/write-execplan/PLANS.md`.
The parent loop plan is `docs/ExecPlans/architecture_improvement_loop_parent_execplan.md`; this child
plan is self-contained so a new contributor can execute the entire slice from the current checkout.

## Purpose / Big Picture

The signing-properties coordinator currently accepts several overlapping catalog inputs, keeps a
cached `SignaturePresetCatalog`, writes through `ReusableSigningObjects`, and reaches into that
service's private repository during refresh. A name can therefore be checked against one catalog
while a write is made to another. Tests also construct the coordinator with only a catalog and
silently trigger the host's XDG/home filesystem default.

After this slice, `ReusableSigningObjects` is the single owner of reusable-object catalog reads,
indexes, duplicate policy, composition, and persistence. The coordinator asks that boundary for one
immutable snapshot or one intent-level operation and never reads a persisted catalog or private
repository. Saving or composing a preset validates and persists against one catalog state and
returns the committed state. Existing preset JSON, stable IDs, overwrite behavior, placement
`current_page` semantics, signing behavior, Qt state, and CLI/evidence contracts remain unchanged.
The old constructor arguments remain only as one-way, explicitly retired adapters at the boundary;
they are not authoritative state and cannot be combined with a canonical `ReusableSigningObjects`
instance.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` is frozen and unchanged by this slice.
- [x] `docs/ARCHITECTURE.md` records `ReusableSigningObjects` as the reusable-object policy boundary.
- [x] `src/foliaseal/application/reusable_signing_objects.py` already owns typed commands, atomic
  repository writes, stable IDs, reference guards, and an in-memory repository stand-in.
- [x] The previous managed-material slice is committed at `f6d06f25d` and the checkout is clean at
  plan start.

## Progress

- [x] (2026-08-06) Reconfirmed the clean baseline `f6d06f25d`, frozen SPEC, architecture ledger,
  coordinator callers, reusable-object service, and existing boundary tests.
- [x] (2026-08-06) Completed Scan Round 43 and selected this cluster at Candidate Priority about
  `69.0` with confidence `0.951875`.
- [x] (2026-08-06) Compared minimal, flexible, and common-caller designs; selected Design C,
  indexed immutable snapshot plus atomic compose, at a reviewed shape score about `84`.
- [x] (2026-08-06) Added the immutable snapshot/index and intent-level reusable-object operations;
  boundary tests cover snapshot reuse/refresh, name resolution, atomic composition, and failed
  component validation before persistence.
- [x] (2026-08-06) Migrated `DefaultSignaturePropertiesCoordinator` reads and writes to the service
  boundary; `self.preset_catalog`, `_reusable_catalog()`, and private `_repository` reach-through are
  no longer used by production code.
- [x] (2026-08-06) Kept legacy constructor inputs as one-way adapters, rejected contradictory
  canonical/legacy sources, and moved the XDG/home fallback construction into the repository adapter.
- [x] (2026-08-06) Migrated the stale setup-session assertion to the new reusable-object boundary
  and added no-path, fake-boundary, and conflict-source tests.
- [x] (2026-08-06) Focused validation passes (`43` reusable/coordinator tests); the full suite passes
  (`1141` tests, one pre-existing Pillow warning). Ruff, compileall, CLI help, import isolation,
  SPEC diff, and process audit pass.
- [x] (2026-08-06) Offscreen evidence passes signed acceptance `10/7`, preview parity `18/18`, and
  fit rejection `3/3`; the generated summary was removed and no product process remains.
- [ ] Reconcile final measurements/docs, commit the complete slice, run three fresh post-commit
  explorers, and record the next ranked candidate in the parent plan.

## Surprises & Discoveries

- Observation: the coordinator's preset reads and writes already use the same `ReusableSigningObjects`
  command policy for mutations, but direct reads bypass it.
  Evidence: `_save_current_preset()` and `_compose_signature_preset()` read `self.preset_catalog`
  before calling `reusable_objects.execute()` in `src/foliaseal/application/signature_properties_coordinator.py:500-584`.
- Observation: `_reusable_catalog()` reaches into `getattr(self.reusable_objects, "_repository")`.
  Evidence: `signature_properties_coordinator.py:642-652`.
- Observation: many coordinator tests pass only `certificate_catalog=` or `preset_catalog=` and
  thereby invoke default path composition even though they test UI state rather than filesystem I/O.
  Evidence: 65 legacy catalog keyword uses across `tests/unit` and application callers at baseline;
  the no-store factory now lives in `InMemoryCertificateCatalogRepository.for_catalog()`.
- Observation: the common-caller design must avoid a generic query registry; only operations required
  by current coordinator workflows are admitted to the public boundary.
  Evidence: two independent design reviews penalized speculative query surfaces.

## Decision Log

- Decision: Select an indexed immutable snapshot plus atomic `compose_preset` operation instead of
  exposing the full persisted catalog.
  Rationale: it hides schema/persistence details, makes dominant coordinator workflows intent-level,
  and prevents duplicate/reference checks from observing a different catalog than the write.
  Date/Author: 2026-08-06 / Codex.
- Decision: Keep `view()` and `resolve()` as compatibility delegates for one dated migration window,
  but make them read the same internal snapshot and record their removal gate in this plan.
  Rationale: existing application/test callers use them, while a sudden rename would mix migration
  noise with the source-of-truth refactor. They must not expose the repository or a mutable catalog.
  Date/Author: 2026-08-06 / Codex.
- Decision: Legacy `preset_catalog` and `preset_catalog_store` constructor arguments are adapters
  only when `reusable_objects` is absent; contradictory canonical-plus-legacy inputs raise a clear
  configuration error.
  Rationale: silently choosing one source preserves the split-brain bug. A one-way adapter keeps the
  Qt migration bounded and has an observable retirement condition: no `rg` matches for those kwargs
  outside the compatibility constructor tests and no production caller passes them.
  Date/Author: 2026-08-06 / Codex.
- Decision: Move the no-store certificate fallback factory out of the coordinator without changing
  certificate material semantics.
  Rationale: the coordinator must not know XDG/home path policy; the repository adapter can own its
  deterministic in-memory fallback. This is composition cleanup in the same constructor seam, not a
  new certificate-resolution architecture.
  Date/Author: 2026-08-06 / Codex.
- Decision: Do not rename `phase3` modules, commands, DTOs, JSON keys, fixtures, or artifacts here.
  Rationale: `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md` governs that atomic external
  contract migration; mixing it into this slice would make rollback and acceptance ambiguous.
  Date/Author: 2026-08-06 / Codex.

## Outcomes & Retrospective

The implementation is complete pending commit and post-commit rescan. It removed coordinator
catalog/private-repository references from `16` baseline occurrences to `5` compatibility-constructor
occurrences, moved XDG/home path policy out of the coordinator, and grew the reusable/coordinator
focused boundary from `38` baseline tests to `43`. The full suite is `1141` passed with one
pre-existing Pillow warning. Conservative component measurements are navigation `.58`, change
amplification `.57`, seam reduction `.62`, boundary-test improvement `.68`, interface compression
`.56`, cohesion `.61`, and isolation `.72`, for weighted Actual Improvement approximately `.62`
versus predicted `.55`; no component regressed beyond `-.10`. The remaining compatibility arguments
are one-way adapters with explicit removal criteria; no phase3 contract changed.

## Context and Orientation

`src/foliaseal/application/reusable_signing_objects.py` is the application boundary around reusable
appearance profiles, placement profiles, and signature presets. It receives a small
`CatalogRepository`, loads an immutable `SignaturePresetCatalog`, applies typed commands such as
`SavePreset` and `DeleteObject`, and saves only after validation. `view()` projects display names and
stable typed references; `resolve()` returns a fully resolved preset or profile; `execute()` performs
the atomic write.

`src/foliaseal/application/signature_properties_coordinator.py` owns signing workflow selection and
validation. Its constructor still accepts legacy `preset_catalog` and `preset_catalog_store` inputs
only to build one `ReusableSigningObjects` adapter when no canonical service is supplied; it rejects
canonical-plus-legacy combinations and retains no authoritative catalog mirror. All reusable reads,
selection, duplicate checks, composition, and writes go through the service snapshot/command API.
Certificate catalog inputs remain a separate boundary, and the no-store fallback is now built by
`InMemoryCertificateCatalogRepository.for_catalog()` rather than by coordinator XDG/home logic.

`src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` forwards the existing optional
constructor inputs into the coordinator. `src/foliaseal/application/reusable_signing_models.py`
defines immutable profiles, presets, stable IDs, and catalog validation. The persisted JSON codec in
`src/foliaseal/infra/config` must not change. Tests live primarily in
`tests/unit/test_reusable_signing_objects.py` and `tests/unit/test_signature_properties_coordinator.py`.

## Plan of Work

First add application-owned immutable snapshot types in `reusable_signing_objects.py`. A
`ReusableCatalogSnapshot` contains the existing `ReusableObjectsView` plus private immutable indexes
for typed reference lookup; it does not expose a repository, path, or persistence catalog to callers.
Provide `snapshot()` for the current committed state and `refresh()` for exactly one repository load.
Provide `resolve_name(kind, name)` and `resolve_preset_selection(preferred_name, selected_id)` so
selection, partial-preset notices, and certificate-display lookup use one service-owned snapshot.
Provide `ensure_name_available(kind, name, overwrite)` for duplicate checks and
`compose_preset(name, appearance_name, placement_name, certificate_configuration_id, overwrite)` so
name normalization, component lookup, duplicate policy, stable IDs, one `SavePreset` command, and
post-write state are one operation. `execute()` remains the general typed command entrypoint but
updates and returns the new snapshot. `view()` and `resolve()` delegate to the snapshot during the
retirement window.

Then migrate the coordinator. It must obtain names from one `snapshot()` result in `load()`, resolve
selected presets through `resolve_preset_selection()`, and use `resolve_name()` or typed refs for
apply/notice/display-name paths. `_save_current_preset()` uses `ensure_name_available()` followed by
the existing command; `_compose_signature_preset()` calls `compose_preset()` and uses its returned
selection. `_refresh_catalogs()` calls the certificate store once and `reusable_objects.refresh()`
once. Delete `self.preset_catalog`, `_reusable_catalog()`, and all private repository introspection.

Finally make constructor compatibility one-way. If `reusable_objects` is supplied, reject any
`preset_catalog` or `preset_catalog_store` input. Otherwise construct one `ReusableSigningObjects`
from the store or the in-memory catalog adapter and never retain the input as authoritative state.
Move the no-store certificate fallback into an explicit factory/classmethod on the in-memory
certificate repository so `signature_properties_coordinator.py` no longer imports
`default_certificate_managed_dir` or `Path`. Preserve `CertificateCatalogRepository` protocol
behavior and material-port construction.

## Concrete Steps

Run every command from `/home/daekar/FoliaSeal`.

1. Capture baseline evidence before editing:

       git status --short
       rg -n "self\\.preset_catalog|_reusable_catalog|_repository|default_certificate_managed_dir" src/foliaseal/application/signature_properties_coordinator.py
       .venv/bin/pytest -q tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_properties_coordinator.py

   The checkout must be clean, the grep must show the split-brain references, and the focused tests
   must pass before migration.
2. Add snapshot/index/query/compose behavior and contract tests. Verify repository call counts,
   immutable snapshot behavior, duplicate/overwrite semantics, missing component rejection without
   save, stable IDs, `current_page` placement, failed-save retention, and post-write state.
3. Migrate coordinator and panel construction. Add tests with a fake reusable service that has no
   `_repository` or `SignaturePresetCatalog` attribute; assert all load/apply/compose/refresh paths
   still produce the same view state and established error strings. Add conflicting legacy/canonical
   constructor tests and hostile `XDG_DATA_HOME`/home tests proving no coordinator path lookup.
4. Run focused tests, then the complete suite and static checks:

       .venv/bin/pytest -q tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_workspace_properties_panel.py
       .venv/bin/pytest -q
       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m foliaseal --help
       git diff --check

   Preserve the existing Pillow warning only; do not weaken assertions to obtain a green run.
5. Run unchanged headless acceptance and clean its generated summary:

       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence

   Expect signed acceptance `10` scenarios with `7` successful signings, preview parity `18/18`, and
   fit rejection `3/3`. Remove only the generated summary and any temporary roots. Confirm
   `git diff --exit-code -- docs/SPEC.md`, import isolation, and no product process with:

       ps -eo pid=,comm= | awk '$2 ~ /^(python|python3|FoliaSeal|foliaseal|PySide|Qt)$/ {print}'
6. Reconcile `docs/ARCHITECTURE.md`, this child plan, and the parent plan. Record measured before/after
   grep counts and boundary-test counts. Commit source/tests/docs intentionally, then run three fresh
   independent explorer-light scans against the clean commit and record their next candidate.

## Validation and Acceptance

The slice is accepted only when all of the following are true. The coordinator has no live reads of
`SignaturePresetCatalog`, no `_repository` access, and no XDG/home path import. Reusable-object
queries and mutations use one service-owned immutable snapshot; a duplicate or missing component
fails before repository save; a successful compose returns the committed preset and refreshed names;
an injected fake service without persistence attributes can drive the coordinator; and contradictory
legacy/canonical construction is rejected. Existing tests for stable IDs, reference guards, duplicate
protection, failed writes, `current_page`, saved/manual certificate behavior, and Qt view state remain
green. The full suite, Ruff, compileall, CLI help, offscreen matrices, SPEC diff, import firewall,
process audit, and diff check pass. The generated evidence summary is absent and the worktree is
clean after commit. Actual Improvement must be at least `.15`, with no component regression beyond
`.10`; otherwise continue the same plan rather than accepting the slice.

## Idempotence and Recovery

All repository changes are additive until the coordinator migration is green. Snapshot construction
and in-memory repository tests are repeatable. If a persistence test fails, inspect the saved catalog
and restore only the temporary test directory; do not delete user data. If a compatibility caller
still supplies conflicting inputs, preserve the explicit rejection and migrate that caller rather
than silently selecting a source. If the new design proves infeasible, record the evidence and return
to the parent design ledger for the single permitted redesign attempt; do not leave two authoritative
catalog paths.

## Artifacts and Notes

The only generated artifact permitted during acceptance is the existing signed-evidence summary,
which must be removed before commit. No phase3 source, CLI, DTO, JSON, fixture, or artifact name may
change. Useful closure evidence includes:

       focused: <boundary and coordinator tests> passed
       full: <existing suite count> passed, one pre-existing Pillow warning
       signed_acceptance_matrix: PASS (10 scenarios, 7 successful signings)
       signed_preview_parity_matrix: PASS (18 scenarios, 18 successful signings)
       signed_fit_rejection_matrix: PASS (3 scenarios, 0 successful signings)

## Interfaces and Dependencies

In `src/foliaseal/application/reusable_signing_objects.py`, define application-owned immutable
records and methods with these stable meanings:

    @dataclass(frozen=True)
    class PresetSelection:
        name: str
        ref: ReusableObjectRef
        preset: ResolvedSignaturePreset

    class ReusableSigningObjects:
        def snapshot(self) -> ReusableCatalogSnapshot: ...
        def refresh(self) -> ReusableCatalogSnapshot: ...
        def resolve_name(self, kind: ReusableObjectKind, name: str) -> ReusableObjectRef | None: ...
        def resolve_preset_selection(
            self, *, preferred_name: str | None, selected_id: str | None
        ) -> PresetSelection | None: ...
        def ensure_name_available(
            self, kind: ReusableObjectKind, name: str, *, overwrite: bool
        ) -> None: ...
        def compose_preset(
            self, *, name: str, appearance_name: str,
            placement_name: str | None, certificate_configuration_id: str | None,
            overwrite: bool,
        ) -> PresetSelection: ...
        def execute(self, command: ReusableObjectCommand) -> ReusableCatalogSnapshot: ...

`ReusableCatalogSnapshot` must expose only immutable `ReusableObjectsView` data and typed lookup
methods; it must not expose `SignaturePresetCatalogStore`, `CatalogRepository`, filesystem paths, or
mutable persistence state. Existing `view()` and `resolve()` may remain as dated delegates until the
retirement grep is satisfied. `CatalogRepository` remains the only persistence dependency, with
`InMemoryCatalogRepository` used for deterministic tests and `SignaturePresetCatalogStore` used in
production. The certificate material port and all phase3 CLI/evidence contracts remain unchanged.

## Change Log

- 2026-08-06: Created from Scan Round 43 and Design Selection 44. Selected the common-caller
  indexed-snapshot/atomic-compose shape; explicitly kept phase3 nomenclature out of scope and made
  legacy constructor inputs one-way adapters with a retirement gate.
