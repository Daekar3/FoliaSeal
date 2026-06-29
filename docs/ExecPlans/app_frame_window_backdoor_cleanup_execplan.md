# Remove the unused app-frame window backdoor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still opens PDFs, shows the same top-level menus and settings dialogs, and routes Save As, settings propagation, and certificate refresh through the same production seams. The visible GUI behavior does not change.

The architectural gain is that `src/foliaseal/presentation/qt/app_frame.py` stops attaching a private backdoor reference from the Qt window back to the frame object, and it removes a dead private settings-dialog cache that no longer carries behavior. The result is a narrower, more intentional app-frame surface with less legacy compatibility cruft.

## Child ExecPlan Dependencies

- [x] (2026-06-28 21:05Z) `docs/ExecPlans/app_frame_workspace_snapshot_execplan.md` is complete; the frame already owns the live workspace snapshot and no longer needs the old `window.current_*` mirror.
- [x] (2026-06-28 21:05Z) No child ExecPlans are required for this bounded cleanup slice.

## Progress

- [x] (2026-06-28 21:05Z) Re-read `app_frame.py`, `test_qt_app_frame.py`, `docs/ARCHITECTURE.md`, and the recent app-frame hybrid-seam ExecPlans to confirm the remaining legacy hooks.
- [x] (2026-06-28 21:12Z) Removed the unused `window._foliaseal_app_frame` attachment and the dead `_settings_dialog` cache from `app_frame.py`.
- [x] (2026-06-28 21:13Z) Added a focused regression assertion proving the window no longer exposes `_foliaseal_app_frame`.
- [x] (2026-06-28 21:18Z) Updated `docs/ARCHITECTURE.md` so the current Qt presentation description no longer claims `_foliaseal_app_frame` is a supported app-frame compatibility surface.
- [x] (2026-06-28 21:19Z) Ran focused validation (`pytest`, `ruff`, `git diff --check`) and completed a direct compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Surprises & Discoveries

- Observation: `_foliaseal_app_frame` no longer has live call sites in production code or tests.
  Evidence: `rg -n "_foliaseal_app_frame" src tests docs` only found the assignment in `src/foliaseal/presentation/qt/app_frame.py` plus architecture and ExecPlan text.

- Observation: `window.settings_dialog` remains the intentional compatibility surface for app-frame tests, while the private `_settings_dialog` field no longer drives behavior.
  Evidence: `show_app_settings()` returns the dialog result and writes `window.settings_dialog`, while `_settings_dialog` had no reads in the repository search.

- Observation: the only current-state documentation drift after the code cleanup was the architecture paragraph for the Qt presentation layer.
  Evidence: `docs/ARCHITECTURE.md` still listed `_foliaseal_app_frame` as part of the frame-owned compatibility surface until this slice reconciled it.

## Decision Log

- Decision: remove only the unused frame backdoor and dead private cache in this slice.
  Rationale: that keeps the change narrow and behavior-preserving while still paying down real app-frame legacy cruft on the same hybrid seam.
  Date/Author: 2026-06-28 / Codex

- Decision: keep `window.settings_dialog` and the `window.certificate_*_dialog` attributes for now.
  Rationale: focused tests still inspect those explicit dialog references, and they are separate compatibility decisions from the unused frame backdoor.
  Date/Author: 2026-06-28 / Codex

## Outcomes & Retrospective

This slice removes two leftover app-frame compatibility artifacts that no longer contribute to behavior: the `QMainWindow` no longer carries a `_foliaseal_app_frame` pointer, and `FoliaSealAppFrame` no longer stores a private `_settings_dialog` copy. The frame continues to own the live workspace snapshot and the shell port, while explicit dialog compatibility attributes remain unchanged.

Focused validation passed with `16 passed` in `tests/unit/test_qt_app_frame.py`, `ruff check` reported no issues, and `git diff --check` stayed clean. The direct compliance review found no `docs/SPEC.md` conflict because the slice is internal-only and preserves the same user-visible app-frame behavior.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` owns the real `QMainWindow`, installs the File and Settings menus, opens PDFs through `WorkspaceOpenService`, stores the live `WorkspaceCompatibilityState` snapshot on the frame, and forwards Save As, app-settings propagation, and certificate refresh through the explicit `SigningWorkspacePort`.

The recent hybrid seam removed `window.current_shell`, `window.current_viewer_workflow`, and `window.current_signing_workflow` in favor of frame-owned properties. After that slice, the remaining suspicious compatibility artifact was `window._foliaseal_app_frame`, a private pointer from the Qt window back to the frame object. Repository search shows no remaining code or tests that read it. The same search also shows that `self._settings_dialog` became dead state once tests and callers standardized on `window.settings_dialog`.

The focused regression surface is `tests/unit/test_qt_app_frame.py`. Those tests use fake Qt bindings and verify user-visible behavior such as menu installation, settings dialog access, Save As enablement, and open/reopen flows. The goal is to keep those behaviors unchanged while proving the unused backdoor is gone.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Remove the `_settings_dialog` field declaration and the `self._settings_dialog = dialog` assignment in `show_app_settings()`. Remove the `self.window._foliaseal_app_frame = self` compatibility write from initialization. Do not alter the explicit `window.settings_dialog` or `window.certificate_*_dialog` attributes in this slice.

Second, update `tests/unit/test_qt_app_frame.py` with one narrow regression assertion that `frame.window` no longer exposes `_foliaseal_app_frame`. Keep the existing behavior assertions for menus, settings dialogs, and shell routing intact.

Third, reconcile `docs/ARCHITECTURE.md` so the app-frame description no longer claims that `_foliaseal_app_frame` is part of the frame snapshot or supported compatibility surface. If the architecture text mentions a broader compatibility cleanup opportunity, keep that as a follow-on recommendation rather than broadening this slice.

Finally, run focused validation. If the compliance check finds only stale docs, fix the docs inside this slice. If it reveals a real runtime dependency on `_foliaseal_app_frame`, stop and document that dependency rather than reintroducing the backdoor silently.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Remove the unused backdoor and dead cache.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Add a focused regression assertion.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Update the architecture doc and this ExecPlan after validation/compliance review.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_window_backdoor_cleanup_execplan.md

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- opening a PDF still installs the shell widget and enables `File > Save As...`;
- the settings dialog still remains reachable through `window.settings_dialog` for the current fake-Qt tests;
- `src/foliaseal/presentation/qt/app_frame.py` no longer writes `window._foliaseal_app_frame`;
- `src/foliaseal/presentation/qt/app_frame.py` no longer stores an unread private `_settings_dialog` cache;
- focused app-frame tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The user-facing app-frame flow should remain unchanged, but the unused window backdoor should be gone.

## Idempotence and Recovery

This is a behavior-preserving cleanup in Qt presentation code. It is safe to retry. If a test or manual caller unexpectedly depended on `_foliaseal_app_frame`, restore only enough explicit API surface on `FoliaSealAppFrame` or `QtAppFrameAdapter` to satisfy that real use case instead of reintroducing an untyped private window backdoor.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` no longer assigning `window._foliaseal_app_frame` or `_settings_dialog`;
- `tests/unit/test_qt_app_frame.py` proving the window no longer exposes `_foliaseal_app_frame`;
- focused validation output showing the app-frame behavior still passes;
- `docs/ARCHITECTURE.md` updated to remove the stale compatibility claim.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

No public signatures need to widen. The important remaining interfaces stay:

    class FoliaSealAppFrame:
        @property
        def current_workspace(self) -> WorkspaceCompatibilityState | None: ...

        @property
        def current_shell(self) -> Any | None: ...

        def show_app_settings(self) -> AppSettings | None: ...

        def open_pdf_path(self, pdf_path: str | Path) -> Any | None: ...

The intentional compatibility surface in this slice is limited to explicit window attributes such as `window.settings_dialog` and `window.certificate_*_dialog`. The untyped private `window._foliaseal_app_frame` backdoor is removed rather than replaced.

Revision note: Updated on 2026-06-28 by Codex after implementation, validation, and direct compliance review to record the landed architecture reconciliation and the passing focused validation evidence.
