# Split Reusable Signing Profiles Into Canonical Objects

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice makes the first concrete move from the old "named profile" model to the canonical reusable signing-object model in `docs/SCHEMAS.md`. After this slice, a saved signing setup no longer persists one object that directly contains both appearance and placement data. Instead, the persisted catalog has distinct `AppearanceProfile`, `PlacementProfile`, and `SignaturePreset` objects, with `SignaturePreset` storing references.

The visible behavior should remain familiar: the current Qt signing shell can still save, select, overwrite, delete, and reload named entries. The implementation value is that those entries now have the correct internal shape, so later slices can add `CertificateConfiguration` references without rewriting the storage model again.

## Child ExecPlan Dependencies

- [x] Parent plan `docs/ExecPlans/schema_model_alignment_execplan.md` exists and identifies this as Slice 1.
- [ ] No additional child ExecPlans are required for this slice.

## Progress

- [x] (2026-05-06 00:15Z) Read the current config schema tests, signature preset storage tests, signing draft workflow tests, Qt signing shell tests, and Phase 3 harness call sites that load named profile appearances.
- [x] (2026-05-06 00:35Z) Added canonical `AppearanceProfile`, `PlacementProfile`, and reference-only `SignaturePreset` schema types, plus `ResolvedSignaturePreset` for transitional shell/harness call sites.
- [x] (2026-05-06 00:39Z) Updated `SignaturePresetCatalog` and `SignaturePresetCatalogStore` so persisted JSON separates `appearance_profiles`, `placement_profiles`, and `signature_presets`.
- [x] (2026-05-06 00:42Z) Updated `SigningDraftWorkflow`, Qt shell imports/default catalog construction, and test builders to use resolved presets against the split catalog.
- [x] (2026-05-06 00:48Z) Updated focused tests and `docs/ARCHITECTURE.md`.
- [x] (2026-05-06 00:55Z) Ran focused tests and lint successfully. Full-suite validation ran and surfaced four pre-existing artifact-manifest expectation failures outside this slice.

## Surprises & Discoveries

- Observation: there is no `tests/unit/test_profile_storage.py`; the actual storage test is `tests/unit/test_signature_preset_storage.py`.
  Evidence: `sed` could not read `tests/unit/test_profile_storage.py`, while `rg` found `tests/unit/test_signature_preset_storage.py`.

- Observation: Phase 3 preview and signed matrix harnesses use `profile_name` to fetch a base appearance from the persisted catalog.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` calls `catalog.profile_named(profile_name)` and then reads `.appearance`.

- Observation: focused validation for this slice passes, but the full suite currently fails on artifact manifest expectations unrelated to schema persistence.
  Evidence: `.venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py` reported `92 passed`; `.venv/bin/pytest -q` reported `4 failed, 560 passed`, with failures in `test_phase3_harness.py` assertions about stress and signed acceptance manifests.

## Decision Log

- Decision: keep the current "Named profiles" UI label and broad workflow behavior in this slice while changing the persistence shape underneath it.
  Rationale: renaming and redesigning the GUI belongs with the later draft/UI refactor. This slice should create the correct model without expanding into a full shell redesign.
  Date/Author: 2026-05-06 / Codex

- Decision: make a saved shell entry create one `AppearanceProfile`, one optional `PlacementProfile`, and one `SignaturePreset` that references them.
  Rationale: this preserves the current user behavior of saving one named entry that can restore appearance and placement while making the persisted `SignaturePreset` reference-only.
  Date/Author: 2026-05-06 / Codex

- Decision: keep compatibility helper methods such as `profile_names()` during this slice, but make them operate on `SignaturePreset` display names.
  Rationale: many shell and harness tests currently use those names. Keeping adapter-style helpers reduces risk while still moving the stored object model to the canonical shape.
  Date/Author: 2026-05-06 / Codex

- Decision: leave Phase 3 artifact manifest expectation failures out of this slice.
  Rationale: the failing tests assert specific checked-in manifest scenario families and fixture profile markers. They are outside reusable-object persistence and should be handled as a separate artifact/evidence maintenance task.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

Slice 1 is implemented. The persisted reusable signing-object catalog now separates appearance profiles, placement profiles, and reference-only signature presets. The current Qt shell and harness-facing compatibility methods still resolve presets into appearance and placement data so existing user behavior remains intact while the storage model moves toward `docs/SCHEMAS.md`.

The main remaining gap is naming and UI cleanup: the shell still says "Named profiles" and exposes methods with profile-oriented names. That is intentional for this slice and belongs to the later draft/UI refactor in the parent schema-alignment plan.

## Context and Orientation

The current schema implementation lives in `src/foliaseal/infra/config/schemas.py`. Before this slice, `SignaturePreset` contains a full `SignatureAppearance` plus optional `SignaturePlacementDefaults`. That conflicts with `docs/SCHEMAS.md`, where `SignaturePreset` is a shallow composition object.

The current JSON store lives in `src/foliaseal/infra/config/profile_storage.py`. It writes one file named `profiles.json` under the user-visible `Signature Profiles` directory. This slice may keep that filename to avoid changing every call site, but the JSON shape must store split object lists.

The current draft workflow lives in `src/foliaseal/application/signing_draft_workflow.py`. It has `capture_signature_preset()` and `apply_signature_preset()` methods. In this slice, those methods may remain as compatibility APIs, but they must return and consume canonical reference-style presets with catalog support rather than old monolithic preset objects.

The current Qt shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. The `SignaturePropertiesPanel` owns the save/select/delete behavior for named profiles. This slice should update that panel to resolve selected presets through the split catalog.

## Plan of Work

First, update `src/foliaseal/infra/config/schemas.py` with dataclasses for `AppearanceProfile`, `PlacementProfile`, and a reference-only `SignaturePreset`. Add catalog methods for looking up profiles and resolving a preset's appearance and placement. Keep `profile_names()`, `profile_named()`, `upsert_profile()`, and `remove_profile()` as compatibility methods where they make sense, but their underlying behavior should be based on canonical objects.

Second, update `src/foliaseal/infra/config/profile_storage.py` so `SignaturePresetCatalogStore` persists the new catalog shape. Because V1 does not require backward compatibility for old local saved objects, no legacy migration is required.

Third, update `src/foliaseal/application/signing_draft_workflow.py` so capturing a named setup produces split objects through the catalog or a small helper, and applying a named setup uses resolved appearance and placement data.

Fourth, update `src/foliaseal/presentation/qt/signing_shell.py` and `src/foliaseal/presentation/qt/phase3_harness.py` so they resolve base appearances through the catalog instead of assuming `SignaturePreset` has an embedded appearance.

Fifth, update focused tests and `docs/ARCHITECTURE.md`, then run focused and broad checks.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run focused tests while iterating:

    pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py

Run broad validation before committing:

    ruff check .
    pytest -q

## Validation and Acceptance

The slice is accepted when `src/foliaseal/infra/config/schemas.py` has distinct canonical persisted objects for appearance, placement, and signature presets; `SignaturePreset` stores references only; saved Qt shell entries still round trip; and the focused tests pass. This acceptance has been met.

The architecture document must no longer describe configuration persistence as a monolithic `SignaturePreset` profile store.

Validation completed:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py
    92 passed in 3.61s

    .venv/bin/ruff check .
    All checks passed!

    .venv/bin/pytest -q
    4 failed, 560 passed, 1 warning in 35.00s

The four full-suite failures are in `tests/unit/test_phase3_harness.py` and concern artifact manifest expectations, not the schema model split.

## Idempotence and Recovery

The JSON shape may be replaced because V1 does not require compatibility with old saved profiles. If implementation fails midway, fix the code and rerun focused tests. Do not add legacy migration code unless a test proves that lack of migration blocks current repository fixtures or harness flows.

## Artifacts and Notes

Expected new persisted shape is a single catalog with lists similar to:

    appearance_profiles: [{ appearance_profile_id, display_name, appearance }]
    placement_profiles: [{ placement_profile_id, display_name, page_selection_mode, rect }]
    signature_presets: [{ signature_preset_id, display_name, appearance_profile_id, placement_profile_id }]

## Interfaces and Dependencies

No new runtime dependency is required. The work stays in the existing Python dataclass and JSON persistence stack.

Revision note: created on 2026-05-06 as the child ExecPlan for Slice 1 of schema-model alignment.
