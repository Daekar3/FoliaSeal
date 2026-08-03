# Deepen reusable signing-object management and remove obsolete internal naming

This ExecPlan is a living document and must be maintained according to
`.agents/skills/write-execplan/PLANS.md`. It is a complete one-slice DevLoop:
design migration, implementation, compatibility-cruft removal, validation,
architecture review, documentation reconciliation, nomenclature audit, and
commit closure all belong to this plan. Milestones organize the work; they are
not stopping points.

## Purpose / Big Picture

FoliaSeal users can save and reuse appearance profiles, placement profiles,
and reference-only signature presets, but the behavior is split between a
thin `SignatureProfileLibrary`, a filesystem store with per-kind CRUD helpers,
catalog mutation methods, a large signing-properties coordinator, and Qt code
that reconstructs object kinds from display-name prefixes. This makes a simple
rename or delete flow require several modules and makes dangling references,
write failures, and compatibility behavior difficult to test as one outcome.

After this slice, a typed application boundary will own reusable-object views,
resolution, save/compose, rename, delete, duplicate/overwrite policy, and
reference guards. The properties coordinator and profile-library dialog will
submit typed references and commands rather than storage calls or strings such
as `"Appearance: Name"`. The persisted catalog schema and historical storage
path remain readable. A failed catalog write will not update in-memory state,
and legacy profile input will have explicit migration coverage.

The slice also audits `phase3` nomenclature. No current reusable-object module
should acquire or retain an obsolete phase label. Stable Phase 3 evidence
commands, artifact paths, JSON keys, and acceptance DTO names are external
contracts and are not renamed in this slice; any such remaining names are
recorded as a separate migration boundary rather than silently broken.

## Child ExecPlan Dependencies

- [x] The required fresh `explorer-light` review completed on 2026-08-02.
- [x] The recommended hybrid was selected: a small typed application core
  plus a thin caller-facing adapter, with raw persistence retained below it.
- [ ] If compliance review finds a requirement that cannot be fixed within the
  reusable-object boundary, create a child compliance ExecPlan before making
  unrelated edits. No child plan is required at authoring time.

## Progress

- [x] (2026-08-02) Fresh explorer reviewed current APIs, callers, persisted
  schemas, migration behavior, compatibility aliases, and SPEC requirements.
- [x] (2026-08-02) Recorded the hybrid design and the scope of safe legacy and
  `phase3` nomenclature removal.
- [x] (2026-08-02) Created this living ExecPlan before implementation.
- [x] (2026-08-02) Added `ReusableSigningObjects`, typed references/commands,
  an in-memory repository test stand-in, and the narrow `CatalogRepository`
  protocol.
- [x] (2026-08-02) Migrated coordinator saves, compose/delete/apply flows,
  app-frame library routing, and Qt library selection to typed references.
- [x] (2026-08-02) Removed `SignatureProfileLibrary`, string-prefix parsing,
  and per-kind persistence CRUD helpers; retained only active schema aliases.
- [x] (2026-08-02) Added migration, dangling-reference, overwrite,
  reference-guard, ID-stability, non-cascade, and write-failure boundary tests.
- [x] (2026-08-03) Audited the touched reusable-object scope: no obsolete
  `phase3` names were introduced; stable Phase 3 evidence commands, DTOs,
  JSON fields, and artifact paths remain unchanged.
- [x] (2026-08-03) Completed focused validation, architecture/spec compliance
  review, README/architecture reconciliation, and diff/compile checks. The
  root agent will record commit and clean-tree/process audit results after
  commit closure.

## Surprises & Discoveries

- Observation: `SignatureProfileLibrary` is a string-dispatch facade rather
  than a domain boundary.
  Evidence: `items()`, `rename(kind, name, new_name)`, and `delete(kind, name)`
  live in `src/foliaseal/application/signature_profile_library.py`; `_operation`
  indexes a `(kind, operation)` dictionary.
- Observation: The Qt library dialog reconstructs object kinds by parsing
  display prefixes.
  Evidence: `src/foliaseal/presentation/qt/app_frame_profile_library.py`
  stores values such as `Appearance: ...`, `Placement: ...`, and `Preset: ...`.
- Observation: The persistence store mixes path policy, JSON decoding,
  legacy migration, and per-kind mutations.
  Evidence: `src/foliaseal/infra/config/profile_storage.py` contains
  `_migrate_legacy_profiles`, `load_catalog`, `save_catalog`, and save/delete/
  rename helpers.
- Observation: Legacy profile payloads are migrated in memory but are not
  canonicalized until a later mutation.
  Evidence: a `{profiles: [...]}` payload is converted by `load_catalog()` but
  no write-back occurs during the read.
- Observation: `ResolvedSignaturePreset`, `.name` properties, and several
  preset constructors are transitional compatibility surfaces.
  Evidence: `src/foliaseal/infra/config/schemas.py` and current coordinator
  callers still use them for resolution and display-state compatibility.
- Observation: The reusable-object cluster currently has no `phase3` names.
  Evidence: the explorer found Phase 3 names only in the separate evidence and
  harness contracts, so this slice must avoid introducing new phase labels and
  must document the external names left untouched.
- Observation: the full pytest suite needs a persistent terminal session rather
  than the short command-wrapper window.
  Evidence: the completed persistent run reports **1024 passed, 1 warning in
  50.42s**; the reusable-object/coordinator/Qt/storage slice reports 183
  passed, and the preview-renderer module reports 52 passed in 16.80s.

## Decision Log

- Decision: Use a typed application boundary with `view()`, `resolve()`, and a
  typed mutation command union rather than a generic string dispatcher.
  Rationale: the common caller needs a small surface, while typed references
  remove ambiguity when appearance, placement, and preset names collide.
  Date/Author: 2026-08-02 / Codex.
- Decision: Keep the historical `Signature Profiles/profiles.json` path and
  legacy read behavior in this slice.
  Rationale: the path and schema are persisted user-data contracts. Migration
  coverage and canonical write behavior can be improved without silently
  deleting or renaming user data.
  Date/Author: 2026-08-02 / Codex.
- Decision: Reduce `SignaturePresetCatalogStore` to repository responsibilities
  used by the new boundary; move policy orchestration out of the store and
  remove obsolete per-kind convenience methods after callers migrate.
  Rationale: filesystem/JSON persistence is infrastructure, while duplicate,
  overwrite, reference, and selection policy belongs in the application
  boundary.
  Date/Author: 2026-08-02 / Codex.
- Decision: Keep certificate passphrase prompting and signing-draft application
  in `SigningSetupSession` and the coordinator.
  Rationale: reusable-object persistence must not absorb certificate workflow
  or Qt concerns merely to reduce file count.
  Date/Author: 2026-08-02 / Codex.
- Decision: Remove only obsolete internal `phase3` names found in the touched
  reusable-object scope. Preserve Phase 3 evidence commands, artifact paths,
  JSON keys, and acceptance DTOs until a separate contract migration exists.
  Rationale: renaming stable evidence contracts in this slice would broaden the
  change and break documented automation without a migration path.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The final boundary is `ReusableSigningObjects` with typed refs/commands above
repository-only `SignaturePresetCatalogStore` load/save and historical-path
migration. `SignatureProfileLibrary`, string-prefix parsing, and per-kind store
CRUD are removed. The compliance child added library create/edit callbacks,
stable component IDs during preset overwrite, load-time dangling-reference
validation, appearance-less-preset rejection, and coordinator error mapping.
Partial presets retain the active certificate selection and show explicit
certificate guidance. Focused reusable-object/coordinator/session/Qt/storage
coverage is **183 passed**. Ruff, compileall, and `git diff --check` are clean.
README and `docs/ARCHITECTURE.md` now describe typed references/commands,
repository-only persistence, contextual editing, validation, partial-preset
messaging, and the historical storage path. Stable Phase 3 evidence commands,
DTOs, JSON fields, and artifact paths were intentionally preserved. Commit
hashes and final process/clean-tree audit are recorded by the root agent.

## Context and Orientation

`src/foliaseal/infra/config/schemas.py` defines immutable catalog values:
`AppearanceProfile`, `PlacementProfile`, reference-only `SignaturePreset`,
resolved preset views, and `SignaturePresetCatalog`. The catalog currently
provides lookup, upsert, rename, removal, and reference checks.

`src/foliaseal/infra/config/profile_storage.py` reads and atomically writes
the catalog at `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal/Signature Profiles/
profiles.json`. Missing or blank files produce an empty schema-version-one
catalog. A legacy `{profiles: [...]}` object is still accepted and converted
in memory.

`src/foliaseal/application/signature_profile_library.py` is the shallow
application facade used by `app_frame_profile_library.py`. It lists display
strings and dispatches rename/delete by string kind. The properties workflow
in `signature_properties_coordinator.py` and `signing_setup_session.py` also
uses the catalog store directly for save and selection flows. The Qt panel in
`signing_workspace_properties_panel.py` owns prompts and presentation state;
those responsibilities remain outside persistence.

The application boundary introduced by this plan will use local-substitutable
dependencies: tests provide an in-memory or temporary-directory repository,
while production uses the existing JSON store. “Typed reference” means a value
that carries an object ID and its known kind, so callers never infer identity
from a display label.

## Plan of Work

First add `src/foliaseal/application/reusable_signing_objects.py`. Define
`ReusableObjectKind`, typed references, typed save/rename/delete commands,
summary/view values, and a `ReusableSigningObjects` implementation. Its
public operations are `view()`, `resolve(ref)`, and `execute(command)`. It
loads a catalog, validates names and references, applies one catalog
transformation, writes through a narrow `CatalogRepository` protocol, and only
then exposes the new view. Rename preserves IDs. Deleting an appearance or
placement referenced by a preset raises the existing validation category and
leaves the catalog unchanged. Deleting a preset never cascades to components.

Next narrow `SignaturePresetCatalogStore` in
`src/foliaseal/infra/config/profile_storage.py` to raw catalog load/save,
atomic replacement, path policy, and legacy decoding. Keep the historical path
and migration parser here unless implementation shows a focused
`legacy_profile_migration.py` extraction is safer; if extracted, retain one
repository-level migration test and no application import of migration code.
Remove store CRUD helpers only after all callers use the new boundary.

Migrate `signature_properties_coordinator.py` and `signing_setup_session.py`
to consume the shared reusable-object boundary. Preserve existing
`SignaturePropertiesViewState`, password retry/cache, partial-preset behavior,
and signing-draft application. Translate selected display names to typed
references at the application edge; do not put passphrase prompts into the
repository.

Migrate `app_frame_profile_library.py`, `app_frame.py`, and the refinement
selectors in `signing_workspace_properties_panel.py` to carry typed reference
data in Qt item metadata. Remove prefix parsing and the `SignatureProfileLibrary`
facade. The dialog may retain display labels, but labels are presentation only
and never become operation identity.

Remove compatibility pieces proven unused after migration: `_operation`,
string-kind APIs, direct store CRUD calls, obsolete application exports, and
tests asserting prefix parsing or generic kind strings. Keep persisted schema
aliases and `ResolvedSignaturePreset` only where current product flows still
need them; record any remaining alias as an explicit compatibility boundary
rather than deleting it speculatively.

Add boundary tests covering empty and legacy catalogs, canonical round trips,
typed view/reference values, duplicate names with and without overwrite,
rename ID stability, component reference guards, non-cascading preset delete,
dangling-reference errors, and failed writes leaving prior state intact.
Update existing coordinator, session, dialog, and storage tests to assert
observable outcomes through the new boundary. Delete shallow facade tests once
their behavior is covered by the boundary suite.

Run a repository-wide `phase3` inventory over touched source, tests, README,
and current architecture prose. Rename any obsolete internal reusable-object
occurrences; do not rename stable evidence commands, artifact paths, JSON
fields, acceptance DTOs, or historical ExecPlan records. Record the inventory
and rationale in this plan and architecture documentation.

## Milestones

### Milestone 1: Typed catalog boundary

The new application module and repository protocol exist with in-memory tests
for view, resolve, save, rename, delete, duplicate policy, and reference guards.
Run the focused reusable-object tests and confirm the old store remains usable
until migration is complete.

### Milestone 2: Caller migration and cruft removal

The coordinator, setup session, app-frame dialog, and properties panel use
typed references and commands. Prefix parsing, direct CRUD calls, and the old
facade are gone. Run all affected Qt/application tests and verify persisted
fixtures still round-trip.

### Milestone 3: Migration, nomenclature, and compliance closure

Legacy read behavior has explicit tests, failed writes are safe, current docs
describe the new boundary, and the touched-scope `phase3` inventory is closed.
Run the full suite, lint, compile, diff checks, architecture/spec review, and
the process/temporary-artifact cleanup audit before committing.

## Concrete Steps

Run every command from `/home/daekar/FoliaSeal`.

    rg -n "SignatureProfileLibrary|SignaturePresetCatalogStore|phase3|profiles.json" src tests README.md docs/SPEC.md docs/ARCHITECTURE.md || true
    git status --short
    .venv/bin/python -m pytest -q tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_signature_preset_storage.py

After implementation, run the focused boundary suite, then:

    .venv/bin/python -m pytest -q  # 1024 passed, 1 warning in 50.42s
    .venv/bin/ruff check src tests
    .venv/bin/python -m compileall -q src tests
    git diff --check
    rg -n "kind: str|Appearance: |Placement: |Preset: |_operation\(" src tests README.md docs/ARCHITECTURE.md || true
    rg -n -i "phase3" src/foliaseal/application/signature_profile_library.py src/foliaseal/application/reusable_signing_objects.py src/foliaseal/infra/config/profile_storage.py src/foliaseal/presentation/qt/app_frame_profile_library.py tests/unit/test_signature_profile_library.py || true

The expected result is a green full suite, clean lint/compile/diff checks, no
old string-dispatch or prefix-parser references in the current reusable-object
scope, and only explicitly documented stable Phase 3 names outside that scope.

## Validation and Acceptance

Acceptance is behavioral. A temporary catalog can be loaded, an appearance and
placement can be saved, a reference-only preset can be composed, and the view
returns typed references that the Qt caller can retain without parsing labels.
Renaming changes display text but keeps the object ID and preset references.
Deleting a referenced component is rejected without changing the catalog;
deleting a preset leaves its components. A duplicate save is rejected unless
`overwrite=True`. A repository write failure leaves the prior on-disk and
in-memory catalog unchanged. A legacy `{profiles: [...]}` file loads and is
covered by a repository migration test without changing the historical path.

The focused boundary tests must pass, followed by the project’s full pytest
suite. Ruff, compileall, and `git diff --check` must pass. A compliance review
must confirm `docs/SPEC.md` requirements for separate reusable objects,
reference-only partial presets, contextual editing, and both quick selection
and dedicated library management. A documentation review must reconcile
README, `docs/ARCHITECTURE.md`, and this plan. No FoliaSeal process, dialog,
temporary certificate, or generated artifact may remain open or untracked.

## Idempotence and Recovery

All catalog mutations use load-transform-save semantics and update in-memory
state only after a successful repository write. Re-running tests uses temporary
directories and does not touch the user’s real profile directory. Do not rename
the historical storage path or delete persisted aliases without an explicit
migration test. If a migration test fails, preserve the legacy reader and stop
at the repository boundary while recording the exact payload and error.

If a partial edit leaves imports or tests broken, restore the last passing
boundary increment, update `Progress`, and continue from the next migration
step; do not reintroduce a compatibility facade merely to hide an unresolved
ownership decision.

## Artifacts and Notes

The final plan must record concise evidence such as:

    focused reusable-object tests: <N> passed
    full suite: <N> passed, <warnings if any>
    phase3 inventory: stable evidence names retained; no obsolete names in reusable-object scope
    git diff --check: clean
    process audit: no FoliaSeal/Python process

Generated artifacts under `artifacts/` remain ignored and must be cleaned after
manual checks. Historical ExecPlans remain archival records and are not edited
to rewrite their terminology.

## Interfaces and Dependencies

The application module must expose typed values equivalent to:

    class ReusableObjectKind(Enum):
        APPEARANCE = "appearance"
        PLACEMENT = "placement"
        PRESET = "preset"

    @dataclass(frozen=True)
    class ReusableObjectRef:
        kind: ReusableObjectKind
        object_id: str

    class CatalogRepository(Protocol):
        def load_catalog(self) -> SignaturePresetCatalog: ...
        def save_catalog(self, catalog: SignaturePresetCatalog) -> None: ...

    class ReusableSigningObjects:
        def view(self) -> ReusableObjectsView: ...
        def resolve(self, ref: ReusableObjectRef) -> ResolvedReusableObject: ...
        def execute(self, command: ReusableObjectCommand) -> ReusableObjectsView: ...

Commands must be typed dataclasses for save appearance, save placement, save
preset, rename, and delete. Results must contain typed references and structured
details rather than UI strings. The production repository is
`SignaturePresetCatalogStore`; tests use an in-memory or temporary-directory
implementation. `SigningSetupSession` continues to inject the certificate
passphrase prompter and apply resolved presets to `SigningDraftWorkflow`.

## Revision Notes

2026-08-02: Created after the required fresh explorer review and the selected
minimal/flexible/common-caller interface designs. The recommended hybrid is a
small typed application boundary plus a thin UI adapter, with persisted path
and stable evidence contracts preserved while obsolete reusable-object
compatibility pieces are removed.
2026-08-03: Closed the compliance child, documentation reconciliation, full
suite validation, and process audit. Final evidence: 183 focused tests and
1024 full-suite tests passed; Ruff, compileall, and diff checks are clean.
