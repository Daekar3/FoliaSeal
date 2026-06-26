# Move Live Preset Save Persistence to `save_catalog`

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the live signature-preset save path persists the already-updated catalog through `save_catalog(...)` instead of routing through `SignaturePresetCatalogStore.save_preset(...)`. The visible behavior stays the same: saving a preset still writes the same JSON catalog, still preserves duplicate-name checks and selected-name state, and still persists the updated catalog to disk. A contributor can prove the slice works by running focused coordinator, storage, and schema tests and observing unchanged saved-catalog behavior while the live coordinator path now writes through `save_catalog(...)`.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signing_preset_save_assembly_execplan.md` completed coordinator-side preset assembly on the live save path.
- [ ] No child ExecPlans are required for this slice.

## Progress

- [x] (2026-06-26 10:55Z) Rechecked the repository state and confirmed the remaining live persistence seam is `_save_current_preset(...)` calling `SignaturePresetCatalogStore.save_preset(...)` after the catalog has already been updated in memory.
- [x] (2026-06-26 11:03Z) Completed the required `explorer-light` dev-loop audit and selected the next tracer bullet: persist the already-updated catalog via `save_catalog(...)` while leaving `save_preset(...)` as compatibility.
- [x] Tighten the coordinator save test so it fails if the live path still calls `SignaturePresetCatalogStore.save_preset(...)`.
- [x] Update `DefaultSignaturePropertiesCoordinator._save_current_preset(...)` to persist `self.preset_catalog` through `save_catalog(...)` instead of `save_preset(...)`.
- [x] Run focused validation and record the passing evidence here: `60 passed in 0.30s`.
- [x] Run the required architecture/spec compliance review, update docs if needed, and record the result here: compliant after doc refresh; no additional spec drift found.

## Surprises & Discoveries

- Observation: the store seam is thinner than the catalog seam because the live coordinator path already has the updated `SignaturePresetCatalog` in hand before it calls the store.
  Evidence: `_save_current_preset(...)` first computes `self.preset_catalog = self.preset_catalog.upsert_preset(preset)` and only then calls `self.preset_catalog_store.save_preset(preset)`, which reloads and rewrites the catalog through another helper layer.

## Decision Log

- Decision: leave `SignaturePresetCatalog.upsert_preset(...)` unchanged in this slice.
  Rationale: that method is the real schema/model seam. Changing it here would widen the slice into catalog API and resolved-preset shape work.
  Date/Author: 2026-06-26 / Codex

- Decision: keep `SignaturePresetCatalogStore.save_preset(...)` as a compatibility method for now.
  Rationale: the goal is only to remove it from the live coordinator path, not to delete or redesign the store API in the same tracer bullet.
  Date/Author: 2026-06-26 / Codex

## Outcomes & Retrospective

This slice is complete. The live save path now persists the already-updated catalog directly while preserving the compatibility `save_preset(...)` helper for other callers and future cleanup. Compliance review result: aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md` after the documentation refresh. Residual risk: persisting the in-memory catalog directly still leaves a small concurrency-overwrite window if another writer changes the same catalog between load and save.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. `src/foliaseal/application/signature_properties_coordinator.py` owns the live preset save command. The previous slice already moved `ResolvedSignaturePreset` assembly into `_save_current_preset(...)`. The coordinator now builds the preset, updates `self.preset_catalog` in memory with `upsert_preset(...)`, and then persists that already-updated catalog with `self.preset_catalog_store.save_catalog(self.preset_catalog)`.

`src/foliaseal/infra/config/profile_storage.py` owns the persistence adapter for the preset catalog. `save_catalog(...)` writes a full `SignaturePresetCatalog` to JSON. `save_preset(...)` is a convenience helper that reloads the catalog, upserts a resolved preset into it, then delegates back to `save_catalog(...)`. Because the live coordinator path already performed the upsert before calling the store, routing through `save_preset(...)` is now an extra persistence-facing `ResolvedSignaturePreset` seam that the live path no longer needs.

This slice narrows only that live store-write path. It must not change the preset JSON format, schema versioning, `ResolvedSignaturePreset.from_parts(...)`, workflow capture/apply helpers, delete behavior, or duplicate-name validation. Allowed generated artifacts are one application-layer behavior change, focused evidence refresh, and matching documentation/status updates.

## Plan of Work

First, tighten the coordinator save-path test so it proves the live path does not call the store’s `save_preset(...)` method anymore. The test should still assert that the saved catalog contents are correct after persistence.

Second, edit `src/foliaseal/application/signature_properties_coordinator.py`. In `_save_current_preset(...)`, after `self.preset_catalog = self.preset_catalog.upsert_preset(preset)`, call `self.preset_catalog_store.save_catalog(self.preset_catalog)` when a store exists instead of calling `save_preset(preset)`. Keep the duplicate-name validation, selected-name update, and error mapping unchanged.

Third, leave `src/foliaseal/infra/config/profile_storage.py` behavior unchanged unless a docstring or tiny compatibility note is needed later during compliance review. `save_preset(...)` should continue to exist and pass its own tests after this slice.

Finally, rerun focused coordinator, storage, and schema tests. If the compliance review finds documentation drift, update only the relevant docs after the code is stable.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Edit `tests/unit/test_signature_properties_coordinator.py` to fail if the live save path still calls `SignaturePresetCatalogStore.save_preset(...)`.
2. Edit `src/foliaseal/application/signature_properties_coordinator.py` so `_save_current_preset(...)` persists through `save_catalog(...)`.
3. Run:

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preset_storage.py tests/unit/test_config_schemas.py

   Expect all tests in those modules to pass. The tightened coordinator test should fail before the code change and pass after it.
4. Run the required architecture/spec compliance review and record whether the implementation remains aligned with `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Validation and Acceptance

Acceptance is behavior-focused. After the change:

- saving a preset through the coordinator must still persist the updated catalog,
- the persisted catalog contents must remain unchanged from the previous slice,
- the live save path must no longer depend on `SignaturePresetCatalogStore.save_preset(...)`, and
- storage-level compatibility helpers and schema tests must remain green.

Running

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preset_storage.py tests/unit/test_config_schemas.py

must succeed from the repository root.

## Idempotence and Recovery

These edits are safe to repeat because they only change one live write path and refresh focused tests. If the coordinator test fails midway, finish the persistence edit and rerun the same `pytest` command. If a shared helper becomes necessary, prefer a tiny private coordinator helper rather than widening the change into schema or storage API redesign.

## Artifacts and Notes

Expected validation transcript shape after implementation:

    $ pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signature_preset_storage.py tests/unit/test_config_schemas.py
    ...
    60 passed in 0.30s

Record the exact passing transcript and any compliance-review notes once implementation is complete.

## Interfaces and Dependencies

`DefaultSignaturePropertiesCoordinator._save_current_preset(...)` must continue to:

- build a `ResolvedSignaturePreset`,
- update `self.preset_catalog` via `upsert_preset(...)`, and
- persist the updated catalog when `self.preset_catalog_store` exists.

After this slice, persistence must happen through:

    self.preset_catalog_store.save_catalog(self.preset_catalog)

`SignaturePresetCatalogStore.save_preset(...)` must still exist unchanged at the end of this slice, but it should no longer be part of the live coordinator save path.

Revision note: Created on 2026-06-26 by Codex after the required `explorer-light` dev-loop review selected the store-write path as the next smallest persistence-facing tracer bullet.
