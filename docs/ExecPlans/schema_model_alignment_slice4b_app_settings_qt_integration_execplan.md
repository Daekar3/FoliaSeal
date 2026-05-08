# Schema Model Alignment Slice 4B: App Settings Qt Integration ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the first-class `AppSettings` object is no longer persistence-only. The Qt signing shell can load and save default open/output directories, and the output-file chooser uses the configured output directory as its default. This moves the app toward the SPEC requirement that signed output is chosen with a familiar file-save dialog while keeping the current shell architecture small and testable.

The user-visible behavior is intentionally narrow: users get an application-settings surface for default directories and a "Choose output..." action that opens a save-file dialog at the configured default output directory. This slice does not attempt to introduce a full `QMainWindow` menu bar because the existing signing shell is a composite widget, not the application frame.

## Child ExecPlan Dependencies

- [x] Depends on Slice 4 persistence at `docs/ExecPlans/schema_model_alignment_slice4_app_settings_execplan.md`.

## Progress

- [x] (2026-05-07 00:00Z) Created this child ExecPlan for AppSettings Qt integration.
- [x] (2026-05-07 04:38Z) Wired `AppSettings` and `AppSettingsStore` into `build_qt_signing_shell()`.
- [x] (2026-05-07 04:40Z) Added Qt shell controls for editing and persisting default open/output directories.
- [x] (2026-05-07 04:42Z) Added a testable save-output file-dialog seam that uses `AppSettings.default_output_directory`.
- [x] (2026-05-07 04:47Z) Updated `docs/ARCHITECTURE.md` and parent ExecPlan after implementation.

## Surprises & Discoveries

- Observation: The existing Qt signing shell is a `QWidget` composition surface, not a main-window/menu abstraction.
  Evidence: `build_qt_signing_shell()` returns `SigningWorkspaceWidget(...).container`, and `QtSigningWidgetBindings` does not include menu or action classes.

- Observation: The existing fake Qt binding seam made it safe to add `QFileDialog` without requiring PySide in unit tests.
  Evidence: `tests/unit/test_qt_signing_shell.py` now provides `_FakeFileDialog` and asserts the save-dialog initial path.

## Decision Log

- Decision: implement settings integration in the signing shell surface and defer a true application menu bar until an application-frame slice exists.
  Rationale: Adding menu infrastructure to a widget-only shell would mix settings behavior with a broader app-shell refactor. This slice can still make default directories real and testable.
  Date/Author: 2026-05-07 / Codex

## Outcomes & Retrospective

At slice creation time, the main risk is over-scoping into a full Qt application shell. The intended outcome is a small tested integration that proves settings persistence is consumed by UI behavior without pretending the final menu layer already exists.

Slice implementation completed that intended narrow outcome. `build_qt_signing_shell()` now accepts `app_settings` and `app_settings_store`, the shell exposes compact Settings controls for default directories, and `choose_output_pdf_path()` opens the save-file dialog with an initial path rooted at `AppSettings.default_output_directory`. The final application-frame menu and Open-file action remain intentionally outside this slice.

## Context and Orientation

The settings schema and storage implementation live in:

    src/foliaseal/infra/config/schemas.py
    src/foliaseal/infra/config/app_settings_storage.py

The Qt signing shell lives in:

    src/foliaseal/presentation/qt/signing_shell.py

The key construction path is:

    build_qt_signing_shell()
    SigningShellAdapter.create()
    SigningWorkspaceWidget.__init__()
    SignaturePropertiesPanel.__init__()

The existing shell already has test seams through `QtSigningWidgetBindings` and fake widget bindings in `tests/unit/test_qt_signing_shell.py`.

## Plan of Work

Add optional `app_settings` and `app_settings_store` parameters to the signing-shell construction path. The workspace should load settings from the explicit settings object, from the store, or from `AppSettings.default()` in that priority order.

Add compact settings controls to the shell so default output and open directories can be edited and persisted through `AppSettingsStore.save_settings()`. Keep validation in the schema object; UI code should catch validation errors and report them through the existing Qt error path.

Add a `QFileDialog.getSaveFileName()` binding to `QtSigningWidgetBindings` and a `choose_output_pdf_path()` workspace method. The method should derive a suggested filename from the current output path or input PDF stem, use `AppSettings.default_output_directory` as the initial directory, update `SigningDraftWorkflow.output_pdf_path` when the user chooses a file, and expose the method on the returned widget for harness/tests.

Update focused tests in `tests/unit/test_qt_signing_shell.py` for settings persistence and output-dialog default behavior. Then update architecture docs and parent plan status.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run focused validation while iterating:

    .venv/bin/pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_app_settings_storage.py tests/unit/test_config_schemas.py

Before committing, run:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

## Validation and Acceptance

This slice is accepted when:

- `build_qt_signing_shell()` can receive an `AppSettingsStore` and load persisted defaults.
- The Qt shell can save updated default open/output directories through `AppSettingsStore`.
- The output file chooser uses `AppSettings.default_output_directory` for its initial path.
- Focused settings and Qt shell tests pass.
- `docs/ARCHITECTURE.md` no longer describes AppSettings Qt consumption as entirely future work.

## Idempotence and Recovery

The change is additive. If tests fail, the safest recovery path is to fix the shell seam or fake bindings and rerun focused tests. No persisted backwards-compatibility behavior is required for this V1 move-fast stage.

## Artifacts and Notes

No external artifacts are required. Test evidence is the pytest and ruff output captured during this slice.
