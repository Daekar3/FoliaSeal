# Add File > Save As and desktop shortcuts to the Qt app frame

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md` and must be maintained in accordance with that file. It is self-contained so a contributor can resume this slice from only this document and the current repository tree.

## Purpose / Big Picture

`docs/SPEC.md` requires a familiar desktop-document workflow with `File > Open`, `File > Save As`, and expected keyboard shortcuts. This slice closes that specific gap in the Qt app frame: the top-level `File` menu now exposes `Save As...`, `Open file` uses `Ctrl+O`, and `Save As...` uses `Ctrl+Shift+S`. The app frame delegates `Save As...` to the current shell’s existing `choose_output_pdf_path()` workflow so output-path policy remains in one place.

This slice is intentionally narrow. It adds one menu action, explicit shortcuts for the two file actions, and tests for those behaviors. It does not redesign menus, add recent-files support, or move save-output logic out of the shell.

The intended change slice is one behavior change commit for the menu/shortcut feature plus one documentation/status update commit only if compliance review requires it. Reworking shell save policy, adding close-document behavior, or touching unrelated signing/review flows is forbidden from mixing into this slice.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/app_frame_shell_public_seam_execplan.md` completed first so the frame already routes live interactions through public shell methods rather than private workspace hooks.
- [x] `docs/ExecPlans/document_text_selection_highlight_execplan.md` completed first so current review/save state already lives behind the shell surface and does not need to be reopened here.
- [ ] A later child ExecPlan may add broader keyboard shortcuts if the remaining desktop-convention requirements need more than `Open` and `Save As`.

## Progress

- [x] (2026-05-22T19:35:00Z) Completed the required `explorer-light` audit and fixed the slice target to `File > Save As...` plus explicit `Open` / `Save As` shortcuts.
- [x] (2026-05-22T19:38:00Z) Reviewed `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `src/foliaseal/presentation/qt/app_frame.py`, and `tests/unit/test_qt_app_frame.py` before drafting this plan.
- [x] (2026-05-22T19:50:00Z) Added `File > Save As...` routing in `src/foliaseal/presentation/qt/app_frame.py`, delegated to the current shell’s `choose_output_pdf_path()` seam, and stored the action so the frame can manage enabled state.
- [x] (2026-05-22T19:50:00Z) Added explicit `Ctrl+O` and `Ctrl+Shift+S` shortcuts on the `File` actions and extended the fake QAction surface in `tests/unit/test_qt_app_frame.py` to prove shortcut assignment.
- [x] (2026-05-22T19:50:00Z) Added app-frame tests covering `Save As...` menu presence, disabled-before-open behavior, enablement after opening a PDF, and routing to the active shell.
- [x] (2026-05-22T19:52:00Z) Focused validation passed: `pytest tests/unit/test_qt_app_frame.py`, `ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py`, and `git diff --check`.
- [x] (2026-05-22T20:02:00Z) Completed the required `explorer-light` compliance review and updated stale architecture/ExecPlan text for the new File-menu surface.
- [x] (2026-05-22T20:02:00Z) Recorded the next remaining SPEC-alignment gap after the menu/shortcut workflow and brought the ExecPlan to pre-commit final state.

## Surprises & Discoveries

- Observation: the save-path workflow already exists in the shell and is public.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py` already exposes `choose_output_pdf_path()` on the returned shell widget and the shell button uses that same method.

- Observation: the app frame currently has no shortcut plumbing at all.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` only creates `QAction` objects, connects `triggered`, and never calls `setShortcut()`.

- Observation: the frame can own menu/shortcut ergonomics without re-owning save behavior because the shell already exposes a public save-path method.
  Evidence: the implementation only added `_choose_save_as()` delegation in `app_frame.py`, and `pytest tests/unit/test_qt_app_frame.py` passed without any shell save-policy changes.

## Decision Log

- Decision: keep overwrite confirmation, default directory selection, and output-path mutation in the shell instead of re-implementing them in the app frame.
  Rationale: the shell already owns output-path policy, has tests for it, and exposes a public `choose_output_pdf_path()` seam. Duplicating that logic in the frame would create drift risk for no user benefit.
  Date/Author: 2026-05-22 / Codex

- Decision: assign `Ctrl+O` to `Open file` and `Ctrl+Shift+S` to `Save As...`.
  Rationale: these are the clearest standard desktop conventions for the required actions, and `Ctrl+Shift+S` avoids implying a full document-save workflow that does not exist independently of signing.
  Date/Author: 2026-05-22 / Codex

- Decision: disable `Save As...` until a shell is loaded, then enable it when a PDF is open.
  Rationale: this is the least surprising desktop behavior and avoids a no-op top-level menu action when there is no active document.
  Date/Author: 2026-05-22 / Codex

## Outcomes & Retrospective

Implementation now makes the `File` menu document-centric enough to match the current shell workflow: users can open a PDF, choose a signing output path through `File > Save As...`, and use standard keyboard shortcuts for both actions. `Save As...` is disabled until a shell is loaded and then delegates directly to the shell’s existing `choose_output_pdf_path()` behavior.

The compliance review found no functional bug in the slice. It only required stale doc/plan text to be updated so the app-frame menu surface is described accurately. After this slice lands, the next remaining SPEC-alignment gap in the desktop-workflow cluster is likely broader shortcut coverage only if `docs/SPEC.md` is interpreted more broadly than `Open` and `Save As`; otherwise the next higher-leverage gap is deeper signature inspection/verify ergonomics.

## Context and Orientation

The top-level Qt window lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` owns the main window, the menu bar, the placeholder when no PDF is open, and the creation of a new shell each time a PDF is opened or reopened. The current shell instance is stored as `_current_shell` and mirrored onto `window.current_shell`.

The current signing shell lives in `src/foliaseal/presentation/qt/signing_shell.py`. In this repository, the shell is the document-centric widget that owns save-output behavior, signing controls, review cards, and output-path selection. Its public `choose_output_pdf_path()` method already opens the save dialog, applies overwrite confirmation, and updates the live signing draft.

The app-frame test suite is `tests/unit/test_qt_app_frame.py`. It uses fake Qt actions, menus, dialogs, and a fake shell to validate menu installation and routing behavior without a real GUI. Those fakes currently know how to record action text and `triggered` callbacks, but they do not yet record shortcut assignment or enabled state.

This slice should not add new save logic. It should only make the top-level frame call into the current shell’s public save-path method and make the menu actions advertise standard shortcuts.

## Plan of Work

First, update the app-frame test doubles in `tests/unit/test_qt_app_frame.py`. Extend the fake action to store shortcut values and enabled-state changes so the tests can observe the new behavior. Extend the fake shell with a `choose_output_pdf_path()` method that records calls.

Second, add or update tests in `tests/unit/test_qt_app_frame.py`. Add one menu-installation test that asserts the `File` menu contains both `Open file` and `Save As...` with `Ctrl+O` and `Ctrl+Shift+S` respectively. Add one routing test that opens a PDF, triggers `Save As...`, and proves the call reached the current shell. Add one enabled-state test that proves `Save As...` starts disabled before any PDF is loaded and becomes enabled after `open_pdf_path()` succeeds.

Third, implement the app-frame changes in `src/foliaseal/presentation/qt/app_frame.py`. Extend `_install_menus()` to create and store both file actions, add a narrow `_choose_save_as()` method that delegates to the current shell’s `choose_output_pdf_path()` if available, extend `_action()` to optionally set a shortcut and initial enabled state, and update `open_pdf_path()` so the `Save As...` action becomes enabled when a shell is successfully loaded. If the frame ever returns to the placeholder path in this slice, keep `Save As...` disabled there as well.

Fourth, run focused validation, then perform the required compliance review against `docs/SPEC.md`, `docs/ARCHITECTURE.md`, and this ExecPlan. If the review finds stale architecture/status text, update the docs and rerun the focused checks before committing.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current interfaces before editing:

    sed -n '55,80p' docs/SPEC.md
    sed -n '780,1025p' src/foliaseal/presentation/qt/app_frame.py
    sed -n '1,520p' tests/unit/test_qt_app_frame.py

After updating the app-frame tests and implementation, run:

    pytest tests/unit/test_qt_app_frame.py

Then run focused lint:

    ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py

Finally ensure patch hygiene:

    git diff --check

If compliance review requires documentation changes, rerun the relevant focused checks and record the final passing commands in this plan.

## Validation and Acceptance

Acceptance is behavioral. After this change, a user using the Qt app frame must see `File > Open file` and `File > Save As...`, use `Ctrl+O` for open and `Ctrl+Shift+S` for Save As, and have `Save As...` route to the current shell’s existing save-output workflow once a PDF is open.

The proof points are:

- `tests/unit/test_qt_app_frame.py` passes and proves menu presence, shortcut assignment, action enablement, and delegation to the current shell.
- `ruff check` and `git diff --check` pass.
- No shell save-policy tests need to change because the shell still owns overwrite confirmation and output-path defaults.

This slice is complete when those proofs hold and the compliance review confirms that the top-level app-frame workflow is aligned with the `File > Save As` and “expected keyboard shortcuts” portion of `docs/SPEC.md`.

## Idempotence and Recovery

This feature is UI-only and additive. Re-running the tests and reopening PDFs should be safe and should not mutate saved document data unless a user explicitly chooses a save path through the existing shell workflow.

Implement the tests first, then the app-frame action wiring. If action enablement becomes brittle in the fake Qt environment, keep the routing and shortcut behavior intact and simplify the enabled-state logic rather than duplicating save behavior in the frame. Do not move output-path policy out of the shell in this slice.

## Artifacts and Notes

Gap evidence before the change, kept here as historical context:

    docs/SPEC.md
    - V1 requires `File > Save As` and expected keyboard shortcuts.

    src/foliaseal/presentation/qt/app_frame.py
    - previously only `File > Open file` was installed.

    src/foliaseal/presentation/qt/signing_shell.py
    - `choose_output_pdf_path()` already exists and is the correct delegation seam.

Validation evidence after implementation:

    pytest tests/unit/test_qt_app_frame.py
    - passed on 2026-05-22

    ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    - passed on 2026-05-22

    git diff --check
    - passed on 2026-05-22

## Interfaces and Dependencies

At the end of this slice, `src/foliaseal/presentation/qt/app_frame.py` should expose behavior along these lines:

    def _choose_save_as(self) -> str | None:
        ...

    def _action(
        self,
        text: str,
        callback: Callable[[], Any],
        *,
        shortcut: str | None = None,
        enabled: bool = True,
    ) -> Any:
        ...

The frame should store the `Save As...` action so `open_pdf_path()` can enable it after a successful shell load. The shell must remain the owner of `choose_output_pdf_path()`. Tests should continue using fake `QAction` objects rather than introducing a real Qt dependency.

Change note: 2026-05-22 / Codex

Created this ExecPlan from the required `explorer-light` audit for the next SPEC-alignment slice. It was later revised during compliance closeout to record the final File-menu surface, the passing review status, and the historical nature of the pre-change gap evidence.
