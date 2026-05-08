# Add AppSettings Persistence

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document follows `.agents/skills/write-execplan/PLANS.md` and is a child plan of `docs/ExecPlans/schema_model_alignment_execplan.md`.

## Purpose / Big Picture

This slice adds first-class persisted `AppSettings` so FoliaSeal has a canonical place for global application preferences such as default open and output directories. After this change, code can load settings from a dedicated settings JSON file and get home-directory defaults when no settings file exists.

This slice deliberately stops at persistence. It does not yet wire Qt file-open/save dialogs or a Settings menu to this store. That UI integration should be a follow-up slice so this change remains narrow and reviewable.

## Child ExecPlan Dependencies

- [x] Slice 1 through Slice 3D of `docs/ExecPlans/schema_model_alignment_execplan.md` aligned reusable signing-object, certificate, draft, and preset terminology enough that settings can be added without mixing concerns.

## Progress

- [x] (2026-05-07 04:16Z) Confirmed the worktree is clean and the parent ExecPlan's next unfinished task is Slice 4 AppSettings persistence.
- [x] (2026-05-07 04:17Z) Inspected `docs/SCHEMAS.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, existing config stores, and tests for settings/default-directory behavior.
- [x] (2026-05-07 04:20Z) Added `AppSettings` schema tests and storage tests.
- [x] (2026-05-07 04:21Z) Implemented `AppSettings` in `src/foliaseal/infra/config/schemas.py`.
- [x] (2026-05-07 04:22Z) Added `AppSettingsStore` in `src/foliaseal/infra/config/app_settings_storage.py`.
- [x] (2026-05-07 04:24Z) Updated architecture and parent/child ExecPlan documentation.
- [x] (2026-05-07 04:23Z) Ran focused validation and lint successfully.
- [x] (2026-05-07 04:26Z) Ran the full test suite successfully.
- [x] (2026-05-07 04:28Z) Committed the completed slice as `64a47d9e4 feat: add app settings persistence`.

## Surprises & Discoveries

- Observation: No `AppSettings` implementation exists yet.
  Evidence: repository search finds `AppSettings` only in `docs/SCHEMAS.md` and parent planning/docs, not in source code.

- Observation: `docs/SPEC.md` requires the default output directory to be home unless the user changes a global app setting.
  Evidence: the Output Behavior section says the app should use an explicit save dialog and that the default output directory is the user's home directory unless changed globally.

- Observation: Focused validation and lint are green after adding settings persistence.
  Evidence: `.venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py` reported `33 passed in 0.06s`, and `.venv/bin/ruff check .` reported `All checks passed!`.

- Observation: Full-suite validation remains green after adding AppSettings persistence.
  Evidence: `.venv/bin/pytest -q` reported `594 passed, 1 warning in 34.29s`.

## Decision Log

- Decision: Store AppSettings under XDG config, not XDG data.
  Rationale: Signature preset and certificate stores use XDG data because they own reusable objects and managed files. `AppSettings` stores preferences, so `${XDG_CONFIG_HOME:-~/.config}/FoliaSeal/settings.json` is the more accurate Linux location.
  Date/Author: 2026-05-07 / Codex

- Decision: Keep this slice persistence-only.
  Rationale: The Settings menu and file-dialog integration are user-facing UI behavior and should have their own tests. Adding the schema/store first creates a clean dependency for that slice.
  Date/Author: 2026-05-07 / Codex

## Outcomes & Retrospective

Implemented a tested settings object and store. A missing or blank settings file loads defaults with both default directories set to the user's home directory. Saving settings produces human-readable JSON and reloading reconstructs the same object. Qt Settings menu and file-dialog integration remains future work.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. Canonical persisted object dataclasses live in `src/foliaseal/infra/config/schemas.py`. Existing config stores live beside it: `profile_storage.py` persists `SignaturePresetCatalog`, and `certificate_storage.py` persists `CertificateCatalog`.

`docs/SCHEMAS.md` defines `AppSettings` with `schema_version`, `default_output_directory`, `default_open_directory`, `linux_packaging_channel`, and an optional `ui` object. The same document says `default_output_directory` defaults to the user home directory until explicitly changed.

## Plan of Work

First, add tests to `tests/unit/test_config_schemas.py` for `AppSettings.default()`, round-tripping through `to_dict()` / `from_dict()`, preserving an optional `ui` mapping, and rejecting malformed directory strings or non-object `ui` values.

Second, add `tests/unit/test_app_settings_storage.py` for a new `AppSettingsStore`. Test XDG config directory resolution, missing-file defaults, human-readable JSON saving/reloading, and invalid JSON errors.

Third, implement `AppSettings` in `src/foliaseal/infra/config/schemas.py`. It should be a frozen dataclass with `schema_version`, `default_output_directory`, `default_open_directory`, `linux_packaging_channel`, and `ui`. It should provide `default(home_directory=None)`, `from_dict()`, and `to_dict()`.

Fourth, implement `src/foliaseal/infra/config/app_settings_storage.py` with `APP_SETTINGS_FILENAME = "settings.json"`, `default_app_settings_directory()`, and `AppSettingsStore` methods `default()`, `load_settings()`, and `save_settings()`.

Fifth, update `docs/ARCHITECTURE.md` and the parent ExecPlan so they say AppSettings persistence exists while Qt menu/file-dialog integration remains pending.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

Focused validation:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py

Before committing:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

Expected output is all focused tests passing, ruff reporting `All checks passed!`, and the full test suite passing.

Output observed on 2026-05-07:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py
    33 passed in 0.06s

    .venv/bin/ruff check .
    All checks passed!

    .venv/bin/pytest -q
    594 passed, 1 warning in 34.29s

## Validation and Acceptance

This slice is accepted when `AppSettings.default()` returns home-directory defaults, `AppSettingsStore.load_settings()` returns defaults for a missing/blank file, settings save/reload round-trips through JSON, invalid JSON raises `ConfigValidationError`, docs reflect the new store, and the full suite remains green.

It is not accepted if AppSettings is mixed into the signature preset catalog, certificate catalog, or draft workflow.

## Idempotence and Recovery

The changes are source, tests, and documentation only. No generated artifacts should be committed. Re-running tests is safe because storage tests use pytest `tmp_path`.

## Artifacts and Notes

No generated artifacts are part of this slice.

## Interfaces and Dependencies

At the end of this slice, these interfaces should exist:

- `AppSettings.default(home_directory: Path | str | None = None) -> AppSettings`
- `AppSettings.from_dict(payload: dict[str, Any]) -> AppSettings`
- `AppSettings.to_dict() -> dict[str, Any]`
- `default_app_settings_directory(app_name: str = "FoliaSeal") -> Path`
- `AppSettingsStore.default(app_name: str = "FoliaSeal") -> AppSettingsStore`
- `AppSettingsStore.load_settings() -> AppSettings`
- `AppSettingsStore.save_settings(settings: AppSettings) -> None`

No new third-party dependencies are needed.

Revision note: created on 2026-05-07 to add first-class AppSettings persistence as schema-alignment Slice 4.

Revision note: updated on 2026-05-07 after implementation to record the AppSettings schema, AppSettingsStore, architecture updates, and focused validation evidence.

Revision note: updated on 2026-05-07 after commit to record commit `64a47d9e4` in the progress checklist.
