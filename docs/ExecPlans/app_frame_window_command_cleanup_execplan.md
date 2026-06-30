# Remove app-frame window command monkey-patching

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still opens PDFs, shows the same menus, opens the same dialogs, and launches the same Qt window. The visible GUI behavior does not change.

The architectural win is that `src/foliaseal/presentation/qt/app_frame.py` stops monkey-patching command methods such as `open_file`, `open_pdf_path`, and `show_app_settings` onto the raw Qt window object. `FoliaSealAppFrame` remains the explicit API for those actions, while `build_qt_app_frame()` continues returning a plain `QMainWindow` for display. The proof is unchanged menu and launch behavior plus focused tests that confirm the raw window no longer carries those ad hoc command hooks.

## Child ExecPlan Dependencies

- [x] (2026-06-29 00:05Z) `docs/ExecPlans/app_frame_dialog_snapshot_execplan.md` is complete; the remaining test-inspection state already lives on the frame rather than on the window object.
- [x] (2026-06-29 00:05Z) No child ExecPlans are required for this bounded window-command cleanup slice.

## Progress

- [x] (2026-06-29 00:05Z) Re-read `app_frame.py`, focused app-frame tests, and the current architecture notes to confirm the remaining window command monkey-patching.
- [x] (2026-06-29 00:09Z) Removed the `window.open_file`, `window.open_pdf_path`, `window.show_app_settings`, and `window.show_certificate_*` monkey-patching from `app_frame.py`.
- [x] (2026-06-29 00:10Z) Added focused regression assertions proving the raw window no longer exposes those command hooks.
- [x] (2026-06-29 00:14Z) Updated `docs/ARCHITECTURE.md` so the Qt presentation summary now treats the raw window as a display container rather than an ad hoc command host.
- [x] (2026-06-29 00:15Z) Ran focused validation (`pytest`, `ruff`, `git diff --check`) and completed a direct compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Surprises & Discoveries

- Observation: repository callers already use `FoliaSealAppFrame` methods or menu actions directly; no current in-repo code reads the window command hooks.
  Evidence: repository search only found the six command-attribute assignments in `src/foliaseal/presentation/qt/app_frame.py`.

- Observation: `window.app_settings` remains a separate compatibility/state concern from the removed command hooks.
  Evidence: the settings tests still inspect `frame.window.app_settings`, while no tests or code use the removed callable window attributes.

- Observation: the only current-state documentation drift after implementation was the Qt presentation summary in `docs/ARCHITECTURE.md`.
  Evidence: that paragraph still described the returned window loosely enough to imply command-surface ownership until this slice reconciled it.

## Decision Log

- Decision: remove the window command hooks entirely instead of replacing them with another window-owned command object in this slice.
  Rationale: no in-repo caller depends on those hooks, and `FoliaSealAppFrame` already provides the explicit API for open/settings/certificate actions.
  Date/Author: 2026-06-29 / Codex

- Decision: keep `window.app_settings` for now.
  Rationale: the current hybrid seam is about command-method monkey-patching, not about the remaining app-settings state exposure.
  Date/Author: 2026-06-29 / Codex

## Outcomes & Retrospective

This slice is intended to remove the last window-level command-method monkey-patching from the app frame while preserving the same top-level menu and launch behavior. The window becomes a plainer display object, and the frame remains the explicit behavior host.

Focused validation passed with `16 passed` in `tests/unit/test_qt_app_frame.py`, `ruff check` reported no issues, and `git diff --check` stayed clean. The direct compliance review found no `docs/SPEC.md` conflict because the slice preserves the same user-visible menu, dialog, and launch behavior.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` owns the real `QMainWindow`, installs the File and Settings menus, opens PDFs through `WorkspaceOpenService`, manages certificate and settings dialogs, and forwards Save As, app-settings propagation, and certificate refresh through the active shell port.

Recent slices already moved live workspace state and dialog inspection state off the raw Qt window object. The remaining window-level compatibility seam is six callable attributes assigned during frame initialization: `window.open_file`, `window.open_pdf_path`, `window.show_app_settings`, `window.show_certificate_creation`, `window.show_certificate_import`, and `window.show_certificate_management`.

Those methods are not part of the real Qt surface; they are monkey-patched convenience hooks. Repository search shows no current in-repo caller depends on them. The narrow cleanup is therefore to remove those assignments, keep `FoliaSealAppFrame` itself as the explicit API, and prove that menu wiring plus the launch path still behave the same.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py` and remove the six window command assignments from `FoliaSealAppFrame.__init__`. Do not change the actual frame methods such as `choose_open_pdf()`, `open_pdf_path()`, `show_app_settings()`, or the certificate dialog methods; menus and launch helpers should continue to call those frame methods directly.

Second, update `tests/unit/test_qt_app_frame.py`. In the menu-installation coverage, add assertions that the fake window no longer has those monkey-patched command attributes. In the `build_qt_app_frame()` coverage, add a regression assertion that the returned raw window remains a plain top-level window without those extra command hooks. Keep the existing menu-trigger, settings, certificate, and launch behavior checks intact.

Third, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer implies that the window object itself carries an ad hoc command surface. It should describe `FoliaSealAppFrame` as the behavior host and the returned `QMainWindow` as the display container.

Finally, run focused validation. If the compliance review finds only stale docs, fix them inside this slice. If it reveals a real production dependency on the removed window command hooks, document that dependency rather than silently restoring the monkey-patching.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Remove the window command monkey-patching.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Add focused regression assertions.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Update `docs/ARCHITECTURE.md` and this ExecPlan after validation/compliance review.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_window_command_cleanup_execplan.md

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the menu actions still open the same settings and certificate dialogs and still route through the frame methods;
- the Qt launch path still creates, shows, and optionally seeds the window with an initial PDF;
- the raw window returned by `build_qt_app_frame()` no longer exposes the ad hoc command hooks;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The app should work the same from a user’s perspective, but the raw window should no longer be an improvised command object.

## Idempotence and Recovery

This is a behavior-preserving cleanup in the Qt presentation layer. It is safe to retry. If a real caller turns out to need command-style access after construction, introduce an explicit frame or adapter API for that use case rather than restoring arbitrary methods on the raw window.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` no longer assigning command methods onto `window`;
- `tests/unit/test_qt_app_frame.py` proving the raw window lacks those hooks while menu behavior still works;
- focused validation output showing the app-frame seam still passes;
- `docs/ARCHITECTURE.md` updated to describe the narrower window surface accurately.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice remain:

    class FoliaSealAppFrame:
        def choose_open_pdf(self) -> str | None: ...
        def open_pdf_path(self, pdf_path: str | Path) -> Any | None: ...
        def show_app_settings(self) -> AppSettings | None: ...
        def show_certificate_creation(self) -> Any | None: ...

    def build_qt_app_frame(...) -> Any

`build_qt_app_frame()` should still return the concrete window object for display, but that object should no longer be extended with ad hoc command methods. The behavior surface lives on `FoliaSealAppFrame` and on the menu wiring, not on the raw window.

Revision note: Updated on 2026-06-29 by Codex after implementation, validation, and direct compliance review to record the landed architecture reconciliation and the passing focused validation evidence.
