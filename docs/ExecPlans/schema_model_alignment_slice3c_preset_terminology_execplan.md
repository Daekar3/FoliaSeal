# Rename Remaining Profile-Oriented Preset Terminology

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `.agents/skills/write-execplan/PLANS.md` and is a child plan of `docs/ExecPlans/schema_model_alignment_execplan.md`.

## Purpose / Big Picture

This slice removes the most misleading remaining "profile" terminology from code paths that actually operate on canonical `SignaturePreset` objects. After this change, the Qt signing shell should show and call them "Signature presets", the catalog/store should expose canonical preset methods, and tests should exercise the canonical names. Old profile-oriented method names may remain only as narrow compatibility wrappers, not as the primary implementation path.

The user-visible behavior should remain equivalent: saved reusable signing setups can still be saved, selected, overwritten, deleted, and reloaded. The observable improvement is that the UI and code now match the product vocabulary from `docs/SCHEMAS.md` closely enough that future work can add separate `AppearanceProfile` and `PlacementProfile` UX without fighting an overloaded "named profile" label.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice1_profiles_execplan.md` split reusable appearance, placement, and preset persistence.
- [x] `docs/ExecPlans/schema_model_alignment_slice3_draft_references_execplan.md` added canonical draft apply/capture methods.
- [x] `docs/ExecPlans/schema_model_alignment_slice3b_certificate_selection_execplan.md` wired certificate configurations into the shell.

## Progress

- [x] (2026-05-06 23:41Z) Confirmed the parent ExecPlan's next unfinished work is reducing remaining profile-terminology compatibility aliases.
- [x] (2026-05-06 23:44Z) Inspected remaining profile-oriented APIs in `SignaturePresetCatalog`, `SignaturePresetCatalogStore`, `SigningDraftWorkflow`, Qt shell controls, tests, and harness code.
- [x] (2026-05-06 23:00Z) Added canonical preset catalog/store methods while preserving deprecated profile aliases.
- [x] (2026-05-06 23:00Z) Renamed Qt signing shell controls and public methods from profile-oriented names to preset-oriented names.
- [x] (2026-05-06 23:01Z) Updated tests and harness call sites to use canonical preset names.
- [x] (2026-05-06 23:01Z) Removed no-longer-used draft workflow compatibility aliases for old profile method names.
- [x] (2026-05-06 23:03Z) Updated architecture and parent/child ExecPlan documentation.
- [x] (2026-05-06 23:04Z) Ran focused validation, lint, and the full test suite successfully.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: At the start of this slice, the canonical catalog data shape was already `signature_presets`, but primary method names still said `profile`.
  Evidence: `src/foliaseal/infra/config/schemas.py` defines `signature_presets` but exposes `profile_names()`, `profile_named()`, `upsert_profile()`, and `remove_profile()`.

- Observation: At the start of this slice, the Qt shell's user-facing group was still "Named profiles" and button/error text still said "profile".
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` builds a `q_group_box("Named profiles")`, has `save_current_profile()`, and emits "Profile error" messages.

- Observation: Some uses of "profile" are canonical and must not be renamed in this slice.
  Evidence: `AppearanceProfile`, `PlacementProfile`, `TrustProfile`, `PdfCompatibilityProfile`, and preview stress fixture profile names are distinct concepts and should remain unchanged.

- Observation: Focused and full-suite validation remain green after the terminology migration.
  Evidence: focused validation reported `105 passed in 4.23s`, `.venv/bin/ruff check .` reported `All checks passed!`, and full validation reported `585 passed, 1 warning in 37.00s`.

## Decision Log

- Decision: Add canonical preset methods and keep old profile methods as wrappers for this slice.
  Rationale: The project is allowed to break saved data, but there may still be direct local test/harness callers using old method names. Wrapper aliases reduce churn while moving primary implementation and tests to the canonical surface.
  Date/Author: 2026-05-06 / Codex

- Decision: Rename the Qt shell control object to preset terminology, but keep a private compatibility attribute only if tests or harnesses still need it.
  Rationale: The shell is the main user-facing source of vocabulary drift. The canonical path should be preset-oriented, while compatibility should be visibly transitional.
  Date/Author: 2026-05-06 / Codex

- Decision: Do not rename storage directory constants or on-disk `Signature Profiles/profiles.json` in this slice.
  Rationale: The parent plan already records that the historical storage path remains. Renaming the directory is a separate persistence-location change and would be noisy without improving the immediate API/UI vocabulary.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

Implemented the behavior-preserving terminology migration. The primary catalog/store methods, Qt shell methods, Qt shell labels, tests, and harness lookups now use "signature preset" terminology where they mean reusable signing setup. `AppearanceProfile`, `PlacementProfile`, and other legitimate profile concepts remain unchanged. Old catalog/store profile methods remain only as compatibility wrappers.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. Reusable signing-object schemas live in `src/foliaseal/infra/config/schemas.py`. The `SignaturePresetCatalog` currently stores three arrays: `appearance_profiles`, `placement_profiles`, and `signature_presets`. A `SignaturePreset` is the canonical composition object that references a certificate configuration, appearance profile, and placement profile.

The store for this catalog lives in `src/foliaseal/infra/config/profile_storage.py`. Its class is already named `SignaturePresetCatalogStore`, but the file and method names still talk about profiles because the original implementation treated a preset as a named appearance profile.

The Qt signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. Before this slice, its `SignaturePropertiesPanel` exposed "Named profiles" controls. Those controls saved and selected resolved `SignaturePreset` values, so this slice renamed them to "Signature presets".

Some profile terms are intentionally correct and out of scope: `AppearanceProfile` means saved visual appearance, `PlacementProfile` means saved placement, `TrustProfile` means validation trust settings, and `PdfCompatibilityProfile` means PDF version policy.

## Plan of Work

First, update `src/foliaseal/infra/config/schemas.py` so `SignaturePresetCatalog` exposes `preset_names()`, `preset_named()`, `upsert_preset()`, and `remove_preset()` as the primary methods. The old `profile_names()`, `profile_named()`, `upsert_profile()`, and `remove_profile()` methods should remain as compatibility aliases that delegate to the new methods.

Second, update `src/foliaseal/infra/config/profile_storage.py` so `SignaturePresetCatalogStore` exposes `save_preset()` and `delete_preset()` as the primary methods. Keep `save_profile()` and `delete_profile()` as compatibility wrappers. Update docstrings and error messages to describe signature presets rather than named appearance profiles.

Third, update `src/foliaseal/presentation/qt/signing_shell.py`. Rename the control dataclass and internal fields to preset terminology, change user-facing labels to "Signature presets", change button/error text to "preset", and update logic to call the canonical catalog/store methods. Public shell methods should become `save_current_signature_preset()` and `delete_current_signature_preset()`. If old method aliases are retained, they should be short compatibility wrappers.

Fourth, update tests and harness call sites to use the new names. Tests should assert "Signature preset error" and "Current signature setup" instead of profile-specific UI text where applicable. Harness code should call `preset_named()` rather than `profile_named()`.

Fifth, remove `SigningDraftWorkflow.capture_signature_preset()` and `apply_signature_preset()` if `rg` shows no remaining callers after test updates. If any external harness still depends on them, leave them as compatibility aliases and update architecture docs to call that out.

Sixth, update `docs/ARCHITECTURE.md`, this child ExecPlan, and the parent schema-alignment ExecPlan to describe the reduced terminology drift and any aliases that remain.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

Focused iteration should run:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_test_support.py

Before committing, run:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

Expected successful output is all focused tests passing, ruff reporting `All checks passed!`, and the full pytest suite passing.

Output observed on 2026-05-06:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_signing_draft_workflow.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_test_support.py
    105 passed in 4.23s

    .venv/bin/ruff check .
    All checks passed!

    .venv/bin/pytest -q
    585 passed, 1 warning in 37.00s

## Validation and Acceptance

This slice is accepted when the shell's saved reusable signing setup UI uses "Signature preset" wording, primary catalog/store APIs use `preset_*` names, internal tests and harnesses use canonical names, and all existing save/select/delete behavior remains covered and green.

Profile-oriented aliases may remain only as compatibility wrappers. They must not be the primary implementation path in the Qt shell or tests changed by this slice.

## Idempotence and Recovery

The changes are source, tests, and documentation only. No generated artifacts should be committed. If renaming causes broad churn, preserve behavior first by keeping aliases and move tests incrementally to canonical names. Re-running tests is safe.

## Artifacts and Notes

No generated artifacts are part of this slice.

## Interfaces and Dependencies

At the end of this slice, these interfaces should exist:

- `SignaturePresetCatalog.preset_names() -> tuple[str, ...]`
- `SignaturePresetCatalog.preset_named(name: str) -> ResolvedSignaturePreset`
- `SignaturePresetCatalog.upsert_preset(preset: ResolvedSignaturePreset) -> SignaturePresetCatalog`
- `SignaturePresetCatalog.remove_preset(name: str) -> SignaturePresetCatalog`
- `SignaturePresetCatalogStore.save_preset(preset: ResolvedSignaturePreset) -> SignaturePresetCatalog`
- `SignaturePresetCatalogStore.delete_preset(name: str) -> SignaturePresetCatalog`
- `SignaturePropertiesPanel.save_current_signature_preset() -> ResolvedSignaturePreset | None`
- `SignaturePropertiesPanel.delete_current_signature_preset() -> SignaturePresetCatalog | None`

No new third-party dependencies are needed.

Revision note: created on 2026-05-06 to keep schema-alignment Slice 3C focused on preset terminology and compatibility-alias reduction.

Revision note: updated on 2026-05-06 after implementation to record canonical preset APIs, Qt shell terminology changes, alias removal in the draft workflow, documentation updates, and validation evidence.
