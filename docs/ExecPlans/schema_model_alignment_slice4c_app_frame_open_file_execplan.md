# Schema Model Alignment Slice 4C: Qt App Frame Open File ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal has a small Qt application-frame wrapper with familiar menu actions instead of only a standalone signing widget. The app frame owns standard File/Open and Settings entry points, creates viewer/signing workflows when the user opens a PDF, and passes `AppSettings` into the existing signing shell.

The user-visible outcome is not a finished desktop application. The goal is to establish the missing application-frame seam so future work can put certificate management, settings dialogs, and other top-level GUI features in the right place instead of continuing to crowd the signing-properties widget.

## Child ExecPlan Dependencies

- [x] Depends on Slice 4B at `docs/ExecPlans/schema_model_alignment_slice4b_app_settings_qt_integration_execplan.md`.

## Progress

- [x] (2026-05-07 00:00Z) Created this child ExecPlan for the application-frame Open-file slice.
- [x] (2026-05-07 05:08Z) Added a Qt app-frame module and exported builder.
- [x] (2026-05-07 05:10Z) Added File/Open behavior that uses `AppSettings.default_open_directory`.
- [x] (2026-05-07 05:11Z) Added a Settings menu entry that exposes where app-wide settings live until a full settings dialog is implemented.
- [x] (2026-05-07 05:13Z) Added focused unit tests with fake Qt bindings.
- [x] (2026-05-07 05:17Z) Updated architecture and parent ExecPlan.

## Surprises & Discoveries

- Observation: Existing Phase 2 and Phase 3 harnesses already define the correct QtPdf page-count loading pattern.
  Evidence: `_load_page_count()` in `src/foliaseal/presentation/qt/phase3_harness.py` loads a `QPdfDocument` and reads `pageCount()`.

- Observation: The app-frame wrapper can be tested without PySide by injecting bindings and a shell builder.
  Evidence: `tests/unit/test_qt_app_frame.py` uses `QtAppFrameBindings`, fake Qt classes, and a fake shell builder to verify menus, open-file defaults, workflow creation, and error reporting.

## Decision Log

- Decision: create a new app-frame wrapper rather than turning `signing_shell.py` into a `QMainWindow`.
  Rationale: the signing shell is already a large composite widget. The correct boundary is a thin frame that owns menus and delegates document-specific work to the existing shell.
  Date/Author: 2026-05-07 / Codex

- Decision: seed a new signing draft from the opened PDF with an output path in the configured output directory and empty certificate material.
  Rationale: opening a PDF should be possible before certificate selection. The existing draft validation prevents signing until certificate and placement requirements are satisfied.
  Date/Author: 2026-05-07 / Codex

## Outcomes & Retrospective

At slice creation time, this is intended as a scaffold with real behavior, not a complete app-shell redesign. The acceptance bar is a tested frame that can use a standard Open-file dialog, build the existing signing shell for the selected document, and keep app settings as the source of default directories.

Slice implementation met that acceptance bar. `build_qt_app_frame()` now exposes a `QMainWindow` wrapper with File/Open and Settings menu actions. Opening a PDF uses the settings-backed open directory, creates viewer/signing workflows, and embeds the existing signing shell with the output path seeded from the settings-backed output directory. The Settings action is intentionally informational for this slice; a dedicated settings dialog remains future work.

## Context and Orientation

Relevant files:

    src/foliaseal/presentation/qt/signing_shell.py
    src/foliaseal/presentation/qt/__init__.py
    src/foliaseal/application/viewer_workflow.py
    src/foliaseal/application/viewer_session.py
    src/foliaseal/infra/render/qt_backend.py
    src/foliaseal/infra/config/app_settings_storage.py

The app frame should call `build_qt_signing_shell()` rather than duplicating signing UI behavior.

## Plan of Work

Create `src/foliaseal/presentation/qt/app_frame.py` with a dynamic Qt binding dataclass, an app-frame class, and a `build_qt_app_frame()` helper. The frame should:

- construct a `QMainWindow`
- add File/Open and Settings/Application settings menu actions
- load settings from an injected or default `AppSettingsStore`
- use `QFileDialog.getOpenFileName()` with `AppSettings.default_open_directory`
- load page count with `QPdfDocument`
- create `ViewerWorkflow`, `ViewerSession`, and `SigningDraftWorkflow`
- set the existing signing shell as the central widget

Add focused unit tests with fake Qt classes so behavior can be verified without PySide.

Update `docs/ARCHITECTURE.md` and the parent ExecPlan after implementation.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Focused validation:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py tests/unit/test_app_settings_storage.py

Before committing:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

## Validation and Acceptance

This slice is accepted when:

- `build_qt_app_frame()` returns a main window with File/Open and Settings menu actions.
- Opening a PDF uses the configured default open directory.
- A selected PDF creates a signing shell whose draft output path defaults to `AppSettings.default_output_directory / "<stem>-signed.pdf"`.
- The app frame reports Open-file errors through the existing Qt warning/status path.
- Focused tests, lint, and the full unit suite pass.

## Idempotence and Recovery

The change is additive. If the app-frame tests fail, fix the new wrapper or fake bindings; do not change the signing shell unless a constructor contract is missing.

## Artifacts and Notes

No generated artifacts are expected.
