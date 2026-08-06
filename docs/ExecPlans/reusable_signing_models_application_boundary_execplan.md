# Application-Owned Reusable Signing Models and Persistence Boundary

This ExecPlan records the sixth architecture-improvement slice. It is a living, self-contained
implementation record and must remain consistent with `.agents/skills/write-execplan/PLANS.md`.
The frozen product contract is `docs/SPEC.md`; this slice does not edit it.

## Purpose

Move reusable signing-object model ownership out of the mixed 1,633-line infrastructure schema
module. The application layer must own reusable-object identity, reference invariants, catalog
operations, and repository protocols. The infrastructure edge must own JSON, filesystem paths,
atomic writes, and any explicitly retained historical-reader migration. This reduces application
navigation and prevents new workflow code from importing persistence DTOs while preserving the
current signing-shell behavior.

The same slice records the next atomic nomenclature migration for the obsolete `phase3` label. The
rename is intentionally not performed piecemeal here: established CLI commands, DTO names, JSON
keys, fixture versions, and artifact paths are external contracts. Their complete inventory and
replacement mapping are maintained in `docs/ExecPlans/phase3_nomenclature_retirement_execplan.md`.

## Baseline and evidence

- Baseline before implementation: clean `main` after the five accepted architecture cycles; the
  current scan identified `infra/config/schemas.py` (1,633 LOC) as a mixed settings/certificate/
  reusable-object module and found five application modules importing its DTOs.
- Independent scan priority: approximately 64--67/100, confidence approximately 0.86--0.97;
  dimensions `(NF, CA, SR, TG, IC, CC, MR, BU)` were approximately
  `(4.5, 4.5, 4, 4.5, 4, 4.5, 3, 3.5)`. The candidate is locally substitutable with fake
  repositories and existing application tests.
- Design review: minimal submodule relocation scored 83/100 but retained application-to-infra
  ownership; the flexible ports/adapters design was stronger but over-broad. The selected
  constrained hybrid is one application model module plus the existing repository port and one
  infrastructure JSON adapter. Certificate extraction and broad CLI/phase rename work are out of
  scope.
- Predicted improvement: at least 0.20 from reduced mixed-module navigation, application import
  isolation, and deleted duplicate schema implementation. The measurement uses the parent-loop
  six-component proxy; no component may regress by more than 0.10.

## Target shape

`src/foliaseal/application/reusable_signing_models.py` owns:

- `PlacementProfileRect`, `AppearanceProfile`, `PlacementProfile`, `SignaturePreset`,
  `ResolvedSignaturePreset`, and `SignaturePresetCatalog`;
- stable IDs, display-name lookup, reference validation, upsert/rename/delete policy, and
  `ReusableObjectValidationError`;
- the existing mapping projection required by the persistence adapter during this migration.

`src/foliaseal/application/reusable_signing_objects.py` owns the application command/view boundary
and `CatalogRepository` protocol. `signature_properties_coordinator.py` depends on that protocol,
not on a concrete profile-store class. `src/foliaseal/infra/config/profile_storage.py` is the only
JSON/path/atomic-write adapter and may read the historical `{profiles: [...]}` shape only while it
is a documented current storage migration. No application module imports reusable model classes
from `infra.config.schemas`.

The old duplicate reusable model block, duplicate codecs, and infrastructure re-exports are removed
from `infra/config/schemas.py`. Existing tests/builders now import the canonical application models;
there is no second compatibility implementation.

## Behavior map and invariants

| Existing behavior | New owner | Acceptance proof |
|---|---|---|
| Stable IDs and display names | application models/catalog | model round-trip and reusable-object tests |
| Current-page placement defaults and rectangle values | application models | coordinator/workflow suites |
| Preset appearance/placement reference validation | application catalog | dangling-reference tests and constructor validation |
| Save/overwrite/rename/delete policy | `ReusableSigningObjects` + catalog | reusable-object/coordinator suites |
| `Signature Profiles/profiles.json` path and atomic replacement | profile-store adapter | storage tests and diff review |
| Historical `{profiles: [...]}` input migration | profile-store adapter only | legacy storage test |
| JSON keys and schema version | model mapping projection + adapter | catalog round-trip test |
| `ResolvedSignaturePreset.view()/resolve()/execute()` callers | existing application workflow ports | focused and full tests |

Stable IDs, persisted JSON keys, error categories, current-page semantics, output behavior, and
public CLI/DTO/artifact contracts must not change in this slice. The removed component `.name`
aliases are not part of the canonical application contract; `ResolvedSignaturePreset.name` remains
because it is the application-facing selected-preset display projection.

## Implementation steps (one complete slice)

1. Add the application-owned reusable model module without Qt, Pillow, PyHanko, or infra imports.
2. Migrate reusable-object service, coordinator, draft workflow, and profile storage imports to the
   canonical module; type the coordinator's injected profile repository as `CatalogRepository`.
3. Remove the duplicate reusable model, codec, and re-export implementations from
   `infra/config/schemas.py`; update test builders and callers to the canonical application module.
4. Add round-trip and subprocess import-isolation coverage. Preserve existing focused tests rather
   than replacing them with shallow construction tests.
5. Reconcile `docs/ARCHITECTURE.md`, this plan, the parent architecture-loop plan, and the phase3
   nomenclature plan. Record the exact remaining phase3 external-contract inventory and mapping;
   do not add a piecemeal alias or rename.
6. Run focused tests, full Ruff, full pytest, CLI parser/help checks, and preview/signed acceptance
   matrices. Remove all temporary directories and audit FoliaSeal/Python processes before commit.

## Validation and acceptance

Required checks:

```text
.venv/bin/ruff check src tests scripts
.venv/bin/pytest -q
.venv/bin/python -m foliaseal --help
QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --help
QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --help
```

The focused reusable-model, storage, coordinator, draft-workflow, and import-isolation tests must
pass. The preview matrix must retain eight scenarios and zero error rows. The signed matrix must
retain six successful signings, two matched intentional rejections, zero cryptographic/annotation/
preview-output failures, and `acceptance_expectations_passed=True`. `docs/SPEC.md` must be byte-for-
byte unchanged, `git diff --check` must pass, and `git status --short` must be empty after commit.

## Phase3 nomenclature retirement handoff

The atomic rename plan remains active and is deliberately separate from this model-boundary slice.
Its current contract classes are:

- internal Python modules/symbols: candidates for `acceptance`, `preview_matrix`,
  `signed_acceptance`, or `interactive_harness` names;
- public commands: `phase3-signing-*` names remain frozen until parser, README, tests, scripts,
  and release evidence migrate together;
- serialized fields, `phase3_fidelity_v1`, fixture paths, and artifact paths: unchanged until an
  explicit versioned reader/writer migration is approved;
- historical documentation and handoffs: annotate provenance, do not rewrite immutable evidence.

The next nomenclature slice must begin with a complete `rg -ni` inventory, create a per-occurrence
mapping table, perform one atomic rename, delete old shims, run the full acceptance matrices, and
leave no active `phase3` implementation references except explicitly listed external contracts.

## Status

- [x] Scan evidence and design selection recorded.
- [x] Canonical application model module added and application callers migrated.
- [x] Duplicate reusable schema implementation removed from infrastructure.
- [x] Boundary tests, focused validation, and architecture reconciliation completed.
- [x] Full suite, CLI help, release matrices, process cleanup, and import-boundary audit completed;
  the implementation commit closes the slice.

Revision note: created 2026-08-06 for the post-cycle-5 persisted-schema-boundary slice.
