# Remove Obsolete Signature Preset Profile Aliases

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `.agents/skills/write-execplan/PLANS.md` and is a child plan of `docs/ExecPlans/schema_model_alignment_execplan.md`.

## Purpose / Big Picture

This slice removes obsolete compatibility methods and private aliases that still call a `SignaturePreset` a "profile". After this change, in-repository code will no longer expose `profile_names()`, `profile_named()`, `upsert_profile()`, `remove_profile()`, `save_profile()`, `delete_profile()`, `save_current_profile()`, or `delete_current_profile()` for signature preset behavior. Future work can use the canonical `SignaturePreset`, `AppearanceProfile`, and `PlacementProfile` vocabulary without confusing compatibility surfaces.

The user-visible signing behavior should not change. The shell should still save, select, overwrite, delete, and reload signature presets. This is an API cleanup and architectural-drift reduction slice.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice3c_preset_terminology_execplan.md` moved primary catalog, store, shell, test, and harness callers to preset-oriented names.

## Progress

- [x] (2026-05-07 04:00Z) Confirmed the worktree is clean and the next parent-plan task is auditing/removing remaining profile compatibility wrappers.
- [x] (2026-05-07 04:01Z) Inspected remaining profile-oriented methods and verified in-repo callers use canonical preset names except for private shell dirty-state calls.
- [x] (2026-05-07 04:05Z) Removed profile-oriented compatibility wrappers from `SignaturePresetCatalog` and `SignaturePresetCatalogStore`.
- [x] (2026-05-07 04:06Z) Removed profile-oriented compatibility aliases from `SignaturePropertiesPanel`.
- [x] (2026-05-07 04:06Z) Renamed remaining private shell dirty-state helper calls to preset terminology.
- [x] (2026-05-07 04:10Z) Updated architecture and parent/child ExecPlan documentation.
- [x] (2026-05-07 04:08Z) Ran focused validation and lint successfully.
- [x] (2026-05-07 04:12Z) Ran the full test suite successfully.
- [x] (2026-05-07 04:13Z) Committed the completed slice as `7931bfddc refactor: remove signature preset profile aliases`.

## Surprises & Discoveries

- Observation: After Slice 3C, old catalog/store profile methods have no in-repo callers.
  Evidence: repository search only finds their definitions and documentation notes, while tests and harnesses use `preset_names()`, `preset_named()`, `upsert_preset()`, `save_preset()`, and `delete_preset()`.

- Observation: Some profile terminology is correct and must remain.
  Evidence: `appearance_profile_named()` and `placement_profile_named()` are canonical lookup methods for `AppearanceProfile` and `PlacementProfile`, not signature preset compatibility wrappers.

- Observation: Focused validation and lint are green after removing the obsolete aliases.
  Evidence: `.venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_test_support.py` reported `92 passed in 3.38s`, and `.venv/bin/ruff check .` reported `All checks passed!`.

- Observation: Full-suite validation remains green after removing the aliases.
  Evidence: `.venv/bin/pytest -q` reported `585 passed, 1 warning in 33.89s`.

## Decision Log

- Decision: Remove compatibility wrappers instead of deprecating them further.
  Rationale: The user explicitly accepted move-fast-and-break-things behavior for V1 and does not require backward compatibility for saved/local code. Keeping aliases now creates avoidable confusion.
  Date/Author: 2026-05-07 / Codex

- Decision: Keep the historical `profile_storage.py`, `PROFILE_DIRECTORY_NAME`, and `default_signature_profiles_directory()` names in this slice.
  Rationale: Those names are tied to file/module path and historical storage location, not call-site behavior. Renaming them would be a broader file-path/module migration and is lower leverage than removing callable compatibility aliases.
  Date/Author: 2026-05-07 / Codex

## Outcomes & Retrospective

The implementation removed obsolete compatibility aliases for signature preset operations. The remaining legitimate "profile" names refer to real `AppearanceProfile`, `PlacementProfile`, `TrustProfile`, storage path history, or other non-preset concepts.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. `SignaturePresetCatalog` lives in `src/foliaseal/infra/config/schemas.py` and already has canonical methods named `preset_names()`, `preset_named()`, `upsert_preset()`, and `remove_preset()`. `SignaturePresetCatalogStore` lives in `src/foliaseal/infra/config/profile_storage.py` and already has canonical `save_preset()` and `delete_preset()` methods. The Qt signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py` and already uses "Signature presets" UI labels and canonical public methods.

This slice should not remove `AppearanceProfile`, `PlacementProfile`, `TrustProfile`, `PdfCompatibilityProfile`, or related legitimate profile concepts.

## Plan of Work

First, remove the compatibility alias methods `profile_names()`, `profile_named()`, `upsert_profile()`, and `remove_profile()` from `SignaturePresetCatalog` in `src/foliaseal/infra/config/schemas.py`. Leave `appearance_profile_named()` and `placement_profile_named()` unchanged.

Second, remove `save_profile()` and `delete_profile()` from `SignaturePresetCatalogStore` in `src/foliaseal/infra/config/profile_storage.py`.

Third, remove `save_current_profile()`, `delete_current_profile()`, `_mark_profile_dirty()`, `_show_profile_error()`, and the `_profile_controls` compatibility attribute from `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py`. Update remaining private calls from `_mark_profile_dirty()` to `_mark_signature_preset_dirty()`.

Fourth, update documentation to say the old profile wrappers have been removed rather than remain as compatibility methods.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

Focused validation:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_test_support.py

Before committing:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

Expected output is all focused tests passing, ruff reporting `All checks passed!`, and the full suite passing.

Output observed on 2026-05-07:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_signature_preset_storage.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_test_support.py
    92 passed in 3.38s

    .venv/bin/ruff check .
    All checks passed!

    .venv/bin/pytest -q
    585 passed, 1 warning in 33.89s

## Validation and Acceptance

This slice is accepted when repository search finds no obsolete signature preset profile wrapper definitions or call sites: `profile_names()`, `profile_named()`, `upsert_profile()`, `remove_profile()`, `save_profile()`, `delete_profile()`, `save_current_profile()`, and `delete_current_profile()` should not exist in `src/` or tests except in historical ExecPlan prose if explicitly framed as old state.

Behavior remains accepted only if the Qt shell signature preset save/select/delete tests still pass.

## Idempotence and Recovery

The changes are source, tests if needed, and documentation only. No generated artifacts should be committed. If a hidden in-repo caller surfaces during validation, migrate it to the canonical preset method instead of restoring the alias.

## Artifacts and Notes

No generated artifacts are part of this slice.

## Interfaces and Dependencies

At the end of this slice, the canonical signature preset operation surface should be:

- `SignaturePresetCatalog.preset_names()`
- `SignaturePresetCatalog.preset_named(name)`
- `SignaturePresetCatalog.upsert_preset(preset)`
- `SignaturePresetCatalog.remove_preset(name)`
- `SignaturePresetCatalogStore.save_preset(preset)`
- `SignaturePresetCatalogStore.delete_preset(name)`
- `SignaturePropertiesPanel.save_current_signature_preset()`
- `SignaturePropertiesPanel.delete_current_signature_preset()`

No new third-party dependencies are needed.

Revision note: created on 2026-05-07 to remove obsolete profile aliases left after Slice 3C's preset terminology migration.

Revision note: updated on 2026-05-07 after implementation to record removed compatibility aliases, documentation updates, and focused validation evidence.

Revision note: updated on 2026-05-07 after commit to record commit `7931bfddc` in the progress checklist.
