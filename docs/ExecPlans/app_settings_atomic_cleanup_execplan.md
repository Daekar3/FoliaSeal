# App Settings Atomic Save Cleanup

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

FoliaSeal stores app-wide preferences such as the default open directory and default signed-output directory in `settings.json`. Saving those settings already uses a temporary file and an atomic replace so callers should either get the new complete JSON file or keep the old complete JSON file. After this change, a failed replace will also remove the temporary `settings.json.tmp` file, so the config directory does not retain misleading stale settings fragments after a disk or permission failure.

This is a narrow behavior-hardening and schema-compliance slice. It does not change the `AppSettings` JSON shape, GUI settings behavior, certificate storage, profile storage, or signing behavior. No generated artifacts are allowed to be committed.

## Child ExecPlan Dependencies

- [x] The schema model alignment roadmap is complete for first-class `AppSettings` persistence and Qt integration.
- [x] `CertificateCatalogStore.save_catalog()` already demonstrates the desired temp-file cleanup pattern for another JSON store.
- [x] An explorer reviewed the governing docs and identified `AppSettingsStore.save_settings()` cleanup as the next narrow compliance hardening slice.

## Progress

- [x] (2026-05-15T10:24Z) Started this dev-loop slice and confirmed the working tree was clean.
- [x] (2026-05-15T10:24Z) Reviewed `AppSettingsStore`, app settings tests, `CertificateCatalogStore`, and governing documentation references for persisted settings.
- [x] (2026-05-15T10:25Z) Created this ExecPlan.
- [x] (2026-05-15T10:26Z) Added a failing regression test proving `settings.json.tmp` is removed when replace fails.
- [x] (2026-05-15T10:27Z) Updated `AppSettingsStore.save_settings()` to clean up the temp file on write or replace failure and re-raise the original exception.
- [x] (2026-05-15T10:28Z) Ran focused tests and lint successfully.
- [x] (2026-05-15T10:30Z) Committed the first-pass slice as `e7c6464 app settings: clean temp file on failed save`.
- [x] (2026-05-15T10:31Z) Post-commit compliance review found that cleanup failure could mask the original save failure and that the architecture doc did not record the new behavior.
- [x] (2026-05-15T10:34Z) Patched cleanup-failure error semantics, added regression coverage, and updated architecture documentation.
- [x] (2026-05-15T10:35Z) Reran focused tests and lint successfully for the compliance follow-up.
- [ ] Commit the compliance follow-up.
- [ ] Rerun post-commit architectural compliance review.

## Surprises & Discoveries

- Observation: `CertificateCatalogStore.save_catalog()` already removes `certificates.json.tmp` on any write or replace failure.
  Evidence: `src/foliaseal/infra/config/certificate_storage.py` wraps `write_text()` and `replace()` in `try/except Exception`, unlinks the temp path when it exists, and re-raises.

- Observation: `AppSettingsStore.save_settings()` writes `settings.json.tmp` and replaces `settings.json` without the same cleanup guard.
  Evidence: `src/foliaseal/infra/config/app_settings_storage.py` currently calls `temp_path.write_text(...)` and `temp_path.replace(...)` directly.

- Observation: cleanup failure can mask the original save failure unless it is guarded separately.
  Evidence: post-commit compliance review noted that an `unlink()` error inside the first-pass `except Exception` block would replace the original `write_text()` or `replace()` exception, conflicting with this plan's original-error requirement.

## Decision Log

- Decision: Treat this as a behavior-hardening slice rather than a schema-shape change.
  Rationale: The governing docs already define `AppSettings` as a first-class persisted app-wide preferences object. The gap is failure cleanup around the existing persistence behavior, not a missing field or UI control.
  Date/Author: 2026-05-15 / Codex

- Decision: Mirror the existing `CertificateCatalogStore.save_catalog()` cleanup pattern instead of introducing a shared helper in this slice.
  Rationale: The immediate change is tiny and risk is lower if it follows the nearby established pattern. A shared atomic JSON writer can be considered later if more stores need the same behavior.
  Date/Author: 2026-05-15 / Codex

- Decision: Ignore temp-file cleanup errors only after a save failure has already occurred.
  Rationale: The caller needs the original save failure to understand why settings did not persist. Cleanup is best-effort hygiene; if cleanup fails, reporting that secondary error would hide the actionable cause.
  Date/Author: 2026-05-15 / Codex

## Outcomes & Retrospective

This plan is in progress. The first-pass implementation was committed, and compliance review found one follow-up bug in cleanup-failure error semantics plus one architecture documentation gap. Completion now requires the follow-up patch, validation, commit, and a clean post-commit compliance review.

## Context and Orientation

`AppSettings` is the schema object for app-wide preferences. In this repository, a schema object is a dataclass that validates and serializes the JSON shape used on disk. `AppSettings` lives in `src/foliaseal/infra/config/schemas.py` and includes `default_open_directory`, `default_output_directory`, `linux_packaging_channel`, and a free-form `ui` object. `AppSettingsStore` lives in `src/foliaseal/infra/config/app_settings_storage.py` and reads or writes `${XDG_CONFIG_HOME:-~/.config}/FoliaSeal/settings.json`.

The governing docs describe app settings as persisted JSON consumed by the Qt app frame and signing shell. `docs/ARCHITECTURE.md` says `AppSettingsStore.save_settings()` produces the `AppSettings` JSON flow and that missing or blank settings load home-directory defaults. `docs/SCHEMAS.md` defines `AppSettings` as the first-class environment-level preferences object. This slice keeps that contract but improves failure hygiene during save.

An atomic replace means writing a complete temporary file first and then replacing the destination path in one filesystem operation. If the replace fails after the temp file has been written, leaving `settings.json.tmp` behind creates stale local state. The user-visible behavior is subtle but important: after a failed settings save, the config directory should contain no stale temp file that looks like a candidate settings file.

## Plan of Work

First, add one regression test to `tests/unit/test_app_settings_storage.py`. The test should monkeypatch `pathlib.Path.replace` so it raises `OSError("replace failed")` only when the source path is named `settings.json.tmp`. It should call `AppSettingsStore.save_settings(AppSettings.default(...))`, assert the original `OSError` is raised, and assert `settings.json.tmp` does not exist afterwards. This uses the public `save_settings()` interface and mirrors the certificate storage regression test.

Second, update `src/foliaseal/infra/config/app_settings_storage.py` inside `AppSettingsStore.save_settings()`. Wrap the temp-file write and replace in a `try` block. In `except Exception`, if `temp_path.exists()`, attempt to call `temp_path.unlink()`, but catch and ignore cleanup failures before re-raising the original save exception. Do not catch only `OSError`, because write failures and replace failures should both leave a clean config directory when possible. Do not convert the exception to `ConfigValidationError`, because filesystem failure semantics should remain visible to callers.

Third, add a second regression test proving that a cleanup failure does not mask the original replace failure. Then update `docs/ARCHITECTURE.md` to record app-settings save cleanup semantics and run focused tests and lint. Update this ExecPlan with transcripts, discoveries, and final outcome.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run the focused red test after adding the regression test and before changing the store:

    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py

The new test should fail because `settings.json.tmp` still exists after the simulated replace failure.

After implementing the store cleanup, run:

    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py
    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py
    .venv/bin/python -m ruff check src/foliaseal/infra/config/app_settings_storage.py tests/unit/test_app_settings_storage.py docs/ARCHITECTURE.md

Expected final result: all focused tests pass and ruff reports `All checks passed!`.

## Validation and Acceptance

Acceptance is met when `AppSettingsStore.save_settings()` still writes human-readable sorted JSON for successful saves, still raises the original filesystem exception when replace fails, removes `settings.json.tmp` after that failure when possible, and still raises the original save exception if cleanup itself fails. The regression tests are the observable proof: one simulates replace failure through the public `save_settings()` method and verifies the temp file is gone, while the other simulates both replace and cleanup failure and verifies the reported exception is still the replace failure.

No GUI run is required for this slice because app-frame settings dialogs call the same store method and this change does not alter dialog behavior.

## Idempotence and Recovery

The code and tests are safe to rerun. The tests use pytest temporary directories and do not touch the user’s real config directory. If the implementation fails midway, rerun the focused tests after fixing the store. Do not delete or stage ignored caches or generated artifacts.

## Artifacts and Notes

Validation transcripts will be recorded here as the slice progresses.

Red regression test before implementation:

    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py
    ...F..                                                                   [100%]
    FAILED tests/unit/test_app_settings_storage.py::test_app_settings_store_removes_temp_file_when_replace_fails
    AssertionError: assert not True

Focused app-settings test after implementation:

    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py
    ......                                                                   [100%]
    6 passed in 0.10s

Focused lint after implementation:

    .venv/bin/python -m ruff check src/foliaseal/infra/config/app_settings_storage.py tests/unit/test_app_settings_storage.py
    All checks passed!

Schema and settings tests after implementation:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py
    .....................................                                    [100%]
    37 passed in 0.18s

Compliance follow-up focused app-settings test:

    .venv/bin/pytest -q tests/unit/test_app_settings_storage.py
    .......                                                                  [100%]
    7 passed in 0.13s

Compliance follow-up focused lint:

    .venv/bin/python -m ruff check src/foliaseal/infra/config/app_settings_storage.py tests/unit/test_app_settings_storage.py docs/ARCHITECTURE.md
    All checks passed!

Compliance follow-up schema and settings tests:

    .venv/bin/pytest -q tests/unit/test_config_schemas.py tests/unit/test_app_settings_storage.py
    ......................................                                   [100%]
    38 passed in 0.20s

## Interfaces and Dependencies

The only public interface changed by behavior is `AppSettingsStore.save_settings(settings: AppSettings) -> None` in `src/foliaseal/infra/config/app_settings_storage.py`. Its signature must not change. It depends only on `json`, `os`, `pathlib.Path`, and `AppSettings`.

The regression test belongs in `tests/unit/test_app_settings_storage.py` and should import no new third-party library. It may use pytest’s existing `monkeypatch` and `tmp_path` fixtures.

Revision note: Created 2026-05-15 by Codex to harden app settings atomic-save cleanup as the next schema-alignment compliance slice.

Revision note: Updated 2026-05-15 by Codex after adding the failing regression test, implementing temp cleanup, and recording focused validation.

Revision note: Updated 2026-05-15 by Codex after compliance review identified cleanup-failure exception masking and a missing architecture note.
