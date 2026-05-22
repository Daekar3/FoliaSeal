# Narrow the app-frame to signing-shell public seam

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can resume the slice from only this file and the current repository tree.

## Purpose / Big Picture

FoliaSeal's app frame already opens PDFs, owns application settings, and refreshes certificate configuration state after certificate-management actions. After this change, those interactions should use explicit public shell methods instead of reaching through broad or private shell seams. A contributor can prove the slice worked by running focused app-frame and shell tests and seeing that application-settings saves still affect the shell's output-path behavior while certificate-management flows still refresh the visible certificate selector.

This slice is intentionally narrow. It does not try to decompose the entire signing shell or remove all white-box shell tests. It only tightens the contract between `app_frame.py` and `signing_shell.py` so app settings and certificate refresh use stable, public shell entrypoints.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/signature_properties_coordinator_execplan.md` completed first so signing-properties reconciliation already has its own application-layer boundary.
- [x] `docs/ExecPlans/signature_preview_lifecycle_execplan.md` completed first so canonical preview lifecycle is already outside the app-frame seam.
- [x] `docs/ExecPlans/signature_preview_layout_execplan.md` completed first so preview geometry/layout ownership is already outside this slice.
- [ ] A later child ExecPlan may further simplify `SigningWorkspaceWidget` and remove more shell-surface exposure after this public seam is in place.

## Progress

- [x] (2026-05-22T22:05:00Z) Completed the required `explorer-light` audit and fixed the next ExecPlan C slice to app-settings sync plus certificate-refresh public entrypoints only.
- [x] (2026-05-22T22:13:00Z) Reviewed `app_frame.py`, `signing_shell.py`, focused tests, and the prior ExecPlans before drafting this plan.
- [x] (2026-05-22T22:28:00Z) Added public `SigningWorkspaceWidget.apply_app_settings()` and exposed it on the returned shell widget.
- [x] (2026-05-22T22:31:00Z) Rewired `FoliaSealAppFrame._apply_app_settings()` to use the public shell method and removed the private `_signing_workspace` fallback from both settings sync and certificate refresh.
- [x] (2026-05-22T22:35:00Z) Updated `tests/unit/test_qt_app_frame.py` to prove the public app-settings seam with a fake shell method instead of a fabricated private workspace hook.
- [x] (2026-05-22T22:39:00Z) Ran focused validation successfully: `pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py` (`78 passed`), focused `ruff check`, and `git diff --check`.
- [x] (2026-05-22T22:46:00Z) Completed the required `explorer-light` compliance review. No code defects remained; only this ExecPlan needed completion-state updates.

## Surprises & Discoveries

- Observation: the app frame already has a public certificate-refresh shell seam, but it still keeps a private fallback.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` first calls `shell.refresh_certificate_configurations()` and then falls back to `shell._signing_workspace.refresh_certificate_configurations()`.

- Observation: the app-settings path is currently private-only.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` updates `shell.app_settings` as a widget attribute and then reaches through `shell._signing_workspace._handle_app_settings_change()` to update the live workspace state used by `choose_output_pdf_path()`.

- Observation: the focused seam change did not require any `tests/unit/test_qt_signing_shell.py` edits beyond keeping its existing behavior green.
  Evidence: after the public seam landed, the focused regression set still passed with `78 passed` across `test_qt_app_frame.py` and `test_qt_signing_shell.py`.

## Decision Log

- Decision: Keep this as one ExecPlan rather than splitting app-settings sync and certificate-refresh cleanup apart.
  Rationale: Both behaviors belong to the same app-frame-to-shell contract, touch the same two production files, and share the same test surface in `tests/unit/test_qt_app_frame.py`.
  Date/Author: 2026-05-22 / Codex

- Decision: Do not broaden this slice into removing all remaining `_signing_workspace` test access from `tests/unit/test_qt_signing_shell.py`.
  Rationale: That would be a larger presentation cleanup with a different risk profile. This slice is only about the app-frame seam.
  Date/Author: 2026-05-22 / Codex

- Decision: Expose app-settings propagation as a public shell method instead of treating `widget.app_settings` as the live contract.
  Rationale: `choose_output_pdf_path()` and related behavior depend on `SigningWorkspaceWidget._app_settings`, so a widget attribute alone is not the actual source of truth. A public method keeps the contract explicit and updates both internal and exposed state together.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

This slice is now implemented. `FoliaSealAppFrame` depends on explicit shell methods for live app-settings updates and certificate-refresh actions, and it no longer reaches through `_signing_workspace` from the app-frame layer.

The change stayed narrow as intended. The production edits were confined to `app_frame.py` and `signing_shell.py`, the test change stayed in `test_qt_app_frame.py`, and the focused regression surface remained green without broader shell churn.

The remaining debt is now clearer. The app-frame/shell contract is less brittle than before, but `signing_shell.py` is still a large composition module and many shell tests still inspect widget-private state. Those are follow-on concerns for a later ExecPlan C child slice, not failures of this seam cleanup.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns the main window, menus, application-settings dialog, certificate-management dialogs, and PDF-opening flow. When a PDF is opened, the app frame constructs a signing shell by calling `build_qt_signing_shell()` and stores the returned widget as the current shell.

The signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. The main in-process object there is `SigningWorkspaceWidget`, which owns the viewer workflow, signing draft workflow, properties panel, summary cards, output-path chooser, and signing execution callbacks. The shell also exposes selected methods and state on the returned widget object so callers and tests can interact with it.

Before this slice, the app frame had two seam problems. First, `_apply_app_settings()` set a shell widget attribute and then reached through `shell._signing_workspace._handle_app_settings_change()` to update the live workspace state. Second, `_refresh_shell_certificate_configurations()` already called the public `shell.refresh_certificate_configurations()` method, but it also kept a fallback that reached through `shell._signing_workspace.refresh_certificate_configurations()`. This slice removed both private reach-throughs.

The focused regression surface is in `tests/unit/test_qt_app_frame.py`. The key test is `test_app_frame_settings_dialog_refreshes_loaded_shell_settings()`, which now proves settings propagation by using a fake public shell method while preserving the user-visible effect: saving application settings updates the shell's default output directory behavior. Existing certificate create/import/manage tests continue to assert that `refresh_certificate_configurations()` is called on the shell and still pass without any private fallback.

## Plan of Work

First, update `src/foliaseal/presentation/qt/signing_shell.py`. Add a public method on `SigningWorkspaceWidget` with a name like `apply_app_settings()` that accepts an `AppSettings` instance and updates the live workspace state used by output-path selection. It should replace the current private `_handle_app_settings_change()` role, update `self._app_settings`, and keep `self.widget.app_settings` synchronized so tests and callers still see the current settings on the widget. The returned shell widget should expose this new public method just as it already exposes `refresh_certificate_configurations()`, `choose_output_pdf_path()`, and related entrypoints.

Second, update `src/foliaseal/presentation/qt/app_frame.py`. In `_apply_app_settings()`, after updating the app frame's own `_app_settings` and `window.app_settings`, call the new public shell method if the shell exists. Remove the private `_signing_workspace` lookup and the call to `_handle_app_settings_change()`. In `_refresh_shell_certificate_configurations()`, keep the public `refresh_certificate_configurations()` call and remove the fallback that reaches through `_signing_workspace`.

Third, update `tests/unit/test_qt_app_frame.py`. Extend `_FakeShell` so it has a public app-settings method that records the received settings and the visible output-directory effect. Rewrite `test_app_frame_settings_dialog_refreshes_loaded_shell_settings()` so it proves the app frame uses that public shell seam rather than a fabricated private workspace object. Keep the existing certificate-refresh tests intact unless they need minor fake updates because the fallback path no longer exists.

Fourth, update documentation if compliance review finds stale text. In the completed slice, that included this ExecPlan plus small status updates in `docs/ARCHITECTURE.md` and the older coordinator ExecPlan so future contributors can see that the app-frame/shell public seam is now in place.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current seam before editing:

    sed -n '998,1025p' src/foliaseal/presentation/qt/app_frame.py
    sed -n '1860,2080p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '972,1010p' tests/unit/test_qt_app_frame.py

After editing, run the focused regression set for this seam:

    pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

Then run focused lint for the touched files:

    ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires doc changes, rerun the relevant focused checks and record the final passing commands here.

## Validation and Acceptance

Acceptance is behavioral. After the change, saving application settings through the app-frame dialog must still update the live shell's output-path defaults through a public shell method, and certificate create/import/manage flows must still refresh certificate configurations through the public shell method only.

The focused test proof is:

    pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py

The important observations are:

- `test_app_frame_settings_dialog_refreshes_loaded_shell_settings` proves the app frame calls the public shell seam and that the saved default output directory becomes visible to the live shell state.
- existing certificate-management tests still observe exactly one call to `refresh_certificate_configurations()` on the shell after refresh-worthy operations.
- shell tests that exercise `choose_output_pdf_path()` still pass, proving the live workspace uses the updated settings state rather than a stale widget-only copy.

Focused lint and `git diff --check` must also pass before the slice is complete.

## Idempotence and Recovery

This refactor is safe to repeat because it is purely a seam cleanup. The public methods can be added first while leaving the old private path in place temporarily; then the app frame can be switched to the public seam; then the fallback and private hook can be removed once tests pass. If a test fails because a fake shell is missing the new public method, add that method to the fake rather than reintroducing private reach-through.

If the app-settings path stops updating output defaults, inspect `SigningWorkspaceWidget.choose_output_pdf_path()` and `_default_output_dialog_path()` to ensure they still read `self._app_settings`, not only `widget.app_settings`. That is the main state-synchronization risk in this slice.

## Artifacts and Notes

Current seam evidence after the change:

    src/foliaseal/presentation/qt/app_frame.py
    - _apply_app_settings() updates frame state, then calls shell.apply_app_settings().
    - _refresh_shell_certificate_configurations() uses only shell.refresh_certificate_configurations().

    src/foliaseal/presentation/qt/signing_shell.py
    - SigningWorkspaceWidget already owns the live _app_settings used by output-path selection.
    - The returned shell widget now exposes both apply_app_settings() and refresh_certificate_configurations() as public app-frame entrypoints.

    tests/unit/test_qt_app_frame.py
    - app-settings propagation now uses a fake public shell method instead of a fabricated private workspace object.

Expected validation evidence after implementation:

    pytest tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
    78 passed

    ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_app_frame.py tests/unit/test_qt_signing_shell.py
    All checks passed!

    git diff --check
    <no output>

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/signing_shell.py` should expose a public shell method with this role:

    class SigningWorkspaceWidget:
        def apply_app_settings(self, settings: AppSettings) -> None: ...

The returned shell widget should expose that method directly, for example:

    self.widget.apply_app_settings = self.apply_app_settings

`src/foliaseal/presentation/qt/app_frame.py` should depend only on:

- `shell.apply_app_settings(settings)` for live shell settings sync
- `shell.refresh_certificate_configurations()` for certificate-refresh propagation

It should not depend on:

- `shell._signing_workspace`
- `shell._signing_workspace._handle_app_settings_change()`
- `shell._signing_workspace.refresh_certificate_configurations()`

The fake shell in `tests/unit/test_qt_app_frame.py` should implement the same public contract so the app-frame seam is tested without depending on signing-shell internals.

Change note: 2026-05-22 / Codex

Created this ExecPlan from the `explorer-light` recommendation for Issue `#51` ExecPlan C. Updated it after implementation and compliance review to record the completed public app-frame-to-shell seam cleanup, passing focused validation, and the remaining follow-on debt.
