# Remove app-frame app-settings mirroring from the window object

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still opens PDFs, preserves the same default open and output directory behavior, and still refreshes any loaded signing shell when application settings are saved. The visible GUI behavior does not change.

The architectural win is that `src/foliaseal/presentation/qt/app_frame.py` no longer mirrors `AppSettings` onto the raw Qt window object. `FoliaSealAppFrame.app_settings` remains the authoritative frame-owned state, and the live shell continues to receive updated settings through the explicit shell port. The proof is unchanged settings behavior plus focused tests that confirm the window object no longer carries `app_settings`.

## Child ExecPlan Dependencies

- [x] (2026-06-30 00:05Z) `docs/ExecPlans/app_frame_window_command_cleanup_execplan.md` is complete; the raw window no longer carries app-frame command methods.
- [x] (2026-06-30 00:05Z) No child ExecPlans are required for this bounded app-settings cleanup slice.

## Progress

- [x] (2026-06-30 00:05Z) Re-read `app_frame.py`, focused app-frame tests, and the current architecture notes to confirm the remaining `window.app_settings` state mirror.
- [x] (2026-06-30 00:09Z) Removed the `window.app_settings` assignments from app-frame initialization and app-settings refresh.
- [x] (2026-06-30 00:10Z) Rewrote focused tests to assert on frame-owned `app_settings` and on the absence of `window.app_settings`.
- [x] (2026-06-30 00:14Z) Updated `docs/ARCHITECTURE.md` so the Qt presentation summary now treats app settings as frame-owned state rather than raw-window state.
- [x] (2026-06-30 00:15Z) Ran focused validation (`pytest`, `ruff`, `git diff --check`) and completed a direct compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Surprises & Discoveries

- Observation: the remaining `window.app_settings` mirror only served focused fake-Qt tests.
  Evidence: repository search found live reads in `tests/unit/test_qt_app_frame.py`; production behavior already flows through `FoliaSealAppFrame.app_settings` and `SigningWorkspacePort.apply_app_settings(...)`.

- Observation: removing the window mirror does not affect the open-file default-directory behavior because `choose_open_pdf()` already reads `self._app_settings`.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` calls `QFileDialog.getOpenFileName()` with `self._app_settings.default_open_directory`.

- Observation: the only current-state documentation drift after implementation was the Qt presentation summary in `docs/ARCHITECTURE.md`.
  Evidence: that paragraph still described the raw window too loosely as a state carrier until this slice reconciled it.

## Decision Log

- Decision: remove the window-level settings mirror entirely instead of replacing it with another window-owned state field.
  Rationale: the frame already owns authoritative app settings state and the shell-port seam already owns runtime propagation, so the window mirror is pure compatibility cruft.
  Date/Author: 2026-06-30 / Codex

- Decision: keep the `FoliaSealAppFrame.app_settings` property as the single app-frame read surface for settings.
  Rationale: focused tests and nearby code still need one explicit owner for the loaded settings value, and the frame property already exists.
  Date/Author: 2026-06-30 / Codex

## Outcomes & Retrospective

This slice is intended to remove the last raw-window state mirror from the app frame while preserving the same settings workflow. The frame remains the state owner and the shell port remains the runtime propagation path.

Focused validation passed with `16 passed` in `tests/unit/test_qt_app_frame.py`, `ruff check` reported no issues, and `git diff --check` stayed clean. The direct compliance review found no `docs/SPEC.md` conflict because the slice preserves the same user-visible settings and file-open behavior.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns the real `QMainWindow`, the top-level menus, the workspace-open path, the settings dialog, and the forwarding behavior that applies saved settings to any loaded signing shell. Recent slices already moved workspace state, dialog inspection state, and window command hooks off the raw Qt window object.

What remains on this hybrid seam is one state mirror: `window.app_settings`. The frame sets that attribute during initialization and again when saved settings are applied. The real behavior, however, already flows through the frame-owned `_app_settings` value, the `app_settings` property, and the shell-port call `apply_app_settings(...)`.

The narrow cleanup is therefore to remove the raw-window settings mirror, keep `FoliaSealAppFrame.app_settings` as the read surface, and prove that menu-triggered settings saves still update future File/Open defaults and still propagate the new settings into any loaded shell.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Remove the `window.app_settings` assignment from `FoliaSealAppFrame.__init__` and from `_apply_app_settings()`. Do not change the frame-owned `_app_settings` field, the `app_settings` property, the settings dialog logic, or the shell-port propagation call.

Second, update `tests/unit/test_qt_app_frame.py`. Replace the assertion on `frame.window.app_settings` with assertions on `frame.app_settings` and on the absence of `window.app_settings`. Add one focused regression assertion in the menu/build coverage that the raw window object does not expose `app_settings`.

Third, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer implies that the raw window carries app-frame settings state. It should describe the frame as the owner of app settings and the shell port as the propagation seam.

Finally, run focused validation. If the compliance review finds only stale docs, fix them in this slice. If it reveals a real production dependency on `window.app_settings`, document that dependency instead of silently restoring the mirror.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Remove the window settings-state mirror.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Rewrite focused app-frame tests to the frame-owned settings state.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Update `docs/ARCHITECTURE.md` and this ExecPlan after validation/compliance review.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_settings_snapshot_execplan.md

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- saving application settings still updates future File/Open default directories;
- saving application settings still refreshes any loaded shell through the shell port;
- the frame remains the owner of `app_settings` and the raw window no longer exposes `app_settings`;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The settings workflow should work the same from a user’s perspective, but the raw window should no longer be used as an app-settings state container.

## Idempotence and Recovery

This is a behavior-preserving app-frame cleanup. It is safe to retry. If a real caller turns out to need read access to app settings after construction, expose that through an explicit frame or adapter API rather than restoring `window.app_settings`.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` no longer assigning `window.app_settings`;
- `tests/unit/test_qt_app_frame.py` proving the same settings behavior through `FoliaSealAppFrame.app_settings`;
- focused validation output showing the app-frame seam still passes;
- `docs/ARCHITECTURE.md` updated to describe the frame-owned settings state accurately.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice remain:

    class FoliaSealAppFrame:
        @property
        def app_settings(self) -> AppSettings: ...

        def show_app_settings(self) -> AppSettings | None: ...

    class SigningWorkspacePort:
        def apply_app_settings(self, settings: AppSettings) -> None: ...

The settings owner stays on `FoliaSealAppFrame`, and runtime propagation stays on `SigningWorkspacePort`. The raw window returned by `build_qt_app_frame()` should no longer carry app-settings state of its own.

Revision note: Updated on 2026-06-30 by Codex after implementation, validation, and direct compliance review to record the landed architecture reconciliation and passing focused validation evidence.
