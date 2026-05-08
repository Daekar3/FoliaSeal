# Schema Model Alignment Slice 4D: App Settings Dialog ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Qt app-frame Settings menu opens an editable app-wide settings dialog instead of an informational message. Users can edit the default open and signed-output directories from the expected top-level Settings menu, and the frame uses those saved values immediately for later Open-file and signing-shell construction.

This is still not a complete preferences system. It is the narrow replacement for the placeholder Settings action introduced in Slice 4C.

## Child ExecPlan Dependencies

- [x] Depends on Slice 4C at `docs/ExecPlans/schema_model_alignment_slice4c_app_frame_open_file_execplan.md`.

## Progress

- [x] (2026-05-07 00:00Z) Created this child ExecPlan for the app-frame settings dialog slice.
- [x] (2026-05-07 05:27Z) Added a modal settings dialog owned by `app_frame.py`.
- [x] (2026-05-07 05:28Z) Saved default open/output directories through `AppSettingsStore`.
- [x] (2026-05-07 05:29Z) Refreshed the app frame and current shell with updated settings.
- [x] (2026-05-07 05:31Z) Added focused unit tests.
- [x] (2026-05-07 05:34Z) Updated architecture and parent ExecPlan.

## Surprises & Discoveries

- Observation: the signing shell already has settings controls, so the app-frame dialog can share the same persisted `AppSettings` contract without adding a new schema.
  Evidence: Slice 4B added settings controls backed by `AppSettingsStore.save_settings()`.

- Observation: saving settings from the dialog needs to update already-open signing shells, not just future Open-file defaults.
  Evidence: `FoliaSealAppFrame._apply_app_settings()` updates the frame, exposed window attribute, current shell attribute, and current shell workspace when available.

## Decision Log

- Decision: keep this dialog limited to default open/output directories.
  Rationale: those are the settings currently required by SPEC and already modeled by `AppSettings`; expanding into general preferences would be speculative.
  Date/Author: 2026-05-07 / Codex

## Outcomes & Retrospective

At slice creation time, acceptance requires the Settings menu to persist edited default directories and remove the known architecture debt that the action is informational only.

Slice implementation met that acceptance bar. The Settings/Application settings menu now opens an editable dialog, saves through `AppSettingsStore`, updates future Open-file defaults, and refreshes currently loaded shell settings when practical. The remaining UX cleanup is duplicate default-directory controls in the signing shell.

## Context and Orientation

Relevant files:

    src/foliaseal/presentation/qt/app_frame.py
    tests/unit/test_qt_app_frame.py
    src/foliaseal/infra/config/app_settings_storage.py
    docs/ARCHITECTURE.md

## Plan of Work

Extend `QtAppFrameBindings` with dialog/form/line-edit/push-button classes. Add a small `AppSettingsDialog` helper that owns the dialog widgets, validates by constructing `AppSettings`, persists through `AppSettingsStore`, and reports validation/storage failures through `QMessageBox.warning()`.

Change `FoliaSealAppFrame.show_app_settings()` to open this dialog. When settings are saved, update `self._app_settings`, the exposed `window.app_settings`, and the current shell/workspace settings if a document is already open.

Update tests to cover menu action behavior, persistence, open-dialog defaults after save, and current-shell propagation.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused validation:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_app_settings_storage.py

Before committing:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

## Validation and Acceptance

This slice is accepted when:

- Settings/Application settings opens an editable dialog rather than only showing an informational message.
- Saving the dialog writes `AppSettingsStore`.
- Later File/Open calls use the updated default open directory.
- Future signing shell construction uses the updated default output directory.
- Existing loaded shell settings are refreshed when practical.
- Focused tests, lint, and the full unit suite pass.

## Idempotence and Recovery

The change is additive within the app frame. If validation fails, fix the dialog seam and fake bindings; do not alter the settings schema.

## Artifacts and Notes

No generated artifacts are expected.
