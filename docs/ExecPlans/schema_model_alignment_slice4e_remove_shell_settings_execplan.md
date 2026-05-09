# Schema Model Alignment Slice 4E: Remove Signing Shell Settings Controls

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, app-wide default directory editing lives in one expected place: the top-level Qt app-frame `Settings > Application settings` dialog. The signing shell still consumes `AppSettings` so its save-output chooser starts in the configured default output directory, and an already-open shell still receives refreshed settings when the app-frame dialog saves. What disappears is the duplicate `Settings` group inside the signing properties panel, which currently lets users edit the same defaults from a document-specific side panel.

This matters because `docs/SPEC.md` calls for standard desktop settings/preferences behavior, and `docs/SCHEMAS.md` defines `AppSettings` as environment-level preferences rather than reusable signing behavior. Removing the duplicate side-panel editor keeps the signing shell focused on document signing while preserving the settings behavior added in Slice 4B through Slice 4D.

## Child ExecPlan Dependencies

- [x] Slice 4D app settings dialog is complete at `docs/ExecPlans/schema_model_alignment_slice4d_app_settings_dialog_execplan.md`.

## Progress

- [x] (2026-05-09T03:25Z) Created this child ExecPlan after reviewing `docs/SPEC.md`, `docs/SCHEMAS.md`, `docs/ARCHITECTURE.md`, the parent schema-alignment plan, and the relevant Qt signing shell/app-frame tests.
- [x] (2026-05-09T03:25Z) Removed the signing-shell `Settings` group, `AppSettingsControls`, `save_app_settings()`, and app-settings control loading while preserving `AppSettings` consumption.
- [x] (2026-05-09T03:25Z) Updated focused Qt shell tests so output-dialog/default-settings behavior remains covered without side-panel settings controls.
- [x] (2026-05-09T03:25Z) Updated architecture and parent ExecPlan documentation to mark the duplicate-controls debt resolved.
- [x] (2026-05-09T12:58Z) Created a local `.venv`, installed `.[dev]`, and ran focused tests, Ruff, and the full unit suite successfully.
- [x] (2026-05-09T12:58Z) Committed the completed slice as `08feda1 Remove duplicate shell settings controls`.

## Surprises & Discoveries

- Observation: before this slice, the duplicate controls were isolated to `SignaturePropertiesPanel`.
  Evidence: pre-change `src/foliaseal/presentation/qt/signing_shell.py` defined `AppSettingsControls`, built `_app_settings_controls`, inserted its container into the properties panel, implemented `save_app_settings()`, and loaded control values in `_load_app_settings_controls()`. Commit `08feda1` removed those editor-only symbols.

- Observation: the app-frame settings dialog already propagates saved settings into an open shell without requiring the shell to own editing controls.
  Evidence: `tests/unit/test_qt_app_frame.py::test_app_frame_settings_dialog_refreshes_loaded_shell_settings` verifies the app frame calls the loaded shell's app-settings update path after saving the dialog.

- Observation: this checkout initially had no local virtualenv and the system Python lacked pytest and ruff.
  Evidence: `.venv/bin/pytest` did not exist, `python` was not available, and `python3 -m pytest` / `python3 -m ruff` reported missing modules. After installing `python3.12-venv` outside Codex and running `.venv/bin/python -m pip install -e '.[dev]'`, validation succeeded.

## Decision Log

- Decision: remove the signing shell settings editor instead of hiding it behind a second option or keeping it as an advanced control.
  Rationale: `AppSettings` are app-wide preferences and the app-frame dialog is now the established top-level settings surface. A second editor in the document-specific shell creates conflicting ownership without adding a V1 capability.
  Date/Author: 2026-05-09 / Codex

- Decision: keep `app_settings` / `app_settings_store` flow on `SigningWorkspaceWidget` where needed for compatibility and settings consumption, but remove UI-driven saving from `SignaturePropertiesPanel`.
  Rationale: `SigningWorkspaceWidget` still needs an `AppSettings` value for output path defaults, while the app frame remains responsible for propagating saved settings into an open shell. The behavior to remove is side-panel editing, not settings consumption.
  Date/Author: 2026-05-09 / Codex

## Outcomes & Retrospective

At plan creation time, this slice was expected to remove one known architecture debt item: the signing shell should no longer expose duplicate default-directory controls now that the app-frame settings dialog owns them. Implementation met that bar. The side-panel editor is gone, the shell still consumes settings for the output save dialog, focused tests pass, Ruff passes, and the full unit suite passes with the existing Pillow deprecation warning in Phase 3 harness coverage.

## Context and Orientation

FoliaSeal is a Qt desktop PDF signing application. The app frame is the top-level window surface in `src/foliaseal/presentation/qt/app_frame.py`; it owns menus such as File/Open and Settings/Application settings. The signing shell is the document-specific signing workspace in `src/foliaseal/presentation/qt/signing_shell.py`; it owns certificate selection, signature presets, placement, appearance, preview, validation, and signing actions.

`AppSettings` is the persisted app-wide preferences object defined in `src/foliaseal/infra/config/schemas.py` and stored by `src/foliaseal/infra/config/app_settings_storage.py`. Its default directory fields are not part of a signature appearance, placement, certificate, or signature preset.

Before this slice, `SignaturePropertiesPanel` in `signing_shell.py` built a `Settings` group with default open/output directory line edits and a `Save settings` button. That was useful before the app frame existed, but Slice 4D added an editable app-frame settings dialog. Commit `08feda1` removed the older side-panel editor while keeping settings values available to the shell.

## Plan of Work

Edit `src/foliaseal/presentation/qt/signing_shell.py` first. Remove the `AppSettingsControls` dataclass, the `_app_settings_controls` instance creation, the layout insertion of its container, `save_app_settings()`, `_build_app_settings_controls()`, `_load_app_settings_controls()`, and the call to `_load_app_settings_controls()` from `load_from_workflow()`. Keep the `AppSettings` import and `SigningWorkspaceWidget._app_settings` field because `SigningWorkspaceWidget._default_output_dialog_path()` uses it. Keep `SigningWorkspaceWidget._handle_app_settings_change()` so `FoliaSealAppFrame` can refresh an already-open shell. Commit `08feda1` implemented these edits.

Then update `tests/unit/test_qt_signing_shell.py`. Remove the test that mutates `widget.properties_panel._app_settings_controls` and calls `save_app_settings()`. Keep or adjust the output-dialog test so it proves the shell still honors an injected `AppSettings.default_output_directory`. Commit `08feda1` removed the editor test and extended the output-dialog test with an assertion that the private settings-controls attribute is absent.

Update `docs/ARCHITECTURE.md` using the architecture-steward rule. The Qt presentation known constraints should no longer say the signing shell contains duplicate default-directory controls. The known architectural debt table should remove the duplicate-controls debt row or revise it as resolved in the change log. Update `docs/ExecPlans/schema_model_alignment_execplan.md` so the remaining unchecked item is marked complete and the retrospective says the duplicate controls were removed in Slice 4E. Commit `08feda1` completed those documentation updates.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Inspect the remaining references:

    rg -n "AppSettingsControls|_app_settings_controls|save_app_settings|_load_app_settings_controls|Save settings|Output folder|Open folder" src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

After code and test edits, run focused validation:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_app_settings_storage.py

Actual command used in this environment:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_app_settings_storage.py

Before commit, run:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

Actual commands used in this environment:

    .venv/bin/python -m ruff check .
    .venv/bin/python -m pytest -q

## Validation and Acceptance

This slice is accepted when `rg` finds no signing-shell settings editor controls or `save_app_settings()` method, while the shell still has an `app_settings` property and still uses `AppSettings.default_output_directory` for the save-output dialog.

Focused tests must show that app-frame settings editing still persists and propagates settings, and that the signing shell output chooser still starts in the configured output directory. Full lint and unit tests must pass before commit.

## Idempotence and Recovery

The change is subtractive but local to the Qt signing shell settings editor. If a focused test fails because it expected `_app_settings_controls`, update that test to exercise the app-frame settings dialog or remove it if it only protected the duplicate side-panel editor. If output-dialog behavior fails, restore only the settings-consumption path, not the removed editor.

No generated artifacts are expected. Do not edit `docs/SPEC.md` or `docs/SCHEMAS.md` because both documents are frozen without explicit user permission.

## Artifacts and Notes

No generated artifacts were expected or produced.

Validation transcript:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_app_settings_storage.py
    73 passed in 24.97s

    .venv/bin/python -m ruff check .
    All checks passed!

    .venv/bin/python -m pytest -q
    578 passed, 23 skipped, 1 warning in 231.85s (0:03:51)

Revision note: Created 2026-05-09 by Codex to close the duplicate app-settings controls debt left after Slice 4D introduced the app-frame settings dialog.

Revision note: Updated 2026-05-09 by Codex after implementation and validation; recorded removed shell settings controls, documentation updates, environment setup, and passing focused/full validation.
