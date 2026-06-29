# Move app-frame dialog inspection off the window object

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still opens the same Settings and certificate dialogs from the same top-level menu actions, and the dialogs still behave the same for users. The visible GUI behavior does not change.

The architectural win is that `src/foliaseal/presentation/qt/app_frame.py` no longer mirrors test-inspection state onto `window.settings_dialog` and `window.certificate_*_dialog`. Instead, the frame owns a typed dialog-compatibility snapshot and exposes it through frame properties. The proof is unchanged menu/dialog behavior plus focused app-frame tests that inspect `FoliaSealAppFrame` instead of monkey-patched window attributes.

## Child ExecPlan Dependencies

- [x] (2026-06-28 21:30Z) `docs/ExecPlans/app_frame_window_backdoor_cleanup_execplan.md` is complete; the private `window._foliaseal_app_frame` backdoor has already been removed.
- [x] (2026-06-28 21:30Z) No child ExecPlans are required for this bounded dialog-snapshot slice.

## Progress

- [x] (2026-06-28 21:30Z) Re-read `app_frame.py`, `app_frame_certificate_management.py`, `tests/unit/test_qt_app_frame.py`, and the current architecture notes to confirm the remaining window-level compatibility writes.
- [x] (2026-06-28 21:36Z) Added a frame-owned `AppFrameDialogCompatibilityState` snapshot and moved settings/certificate dialog inspection state off the window object.
- [x] (2026-06-28 21:37Z) Rewrote focused app-frame tests to inspect frame-owned dialog properties instead of `window.settings_dialog` and `window.certificate_*_dialog`.
- [x] (2026-06-28 21:42Z) Updated `docs/ARCHITECTURE.md` so the Qt presentation summary now describes the frame-owned dialog snapshot instead of window-level dialog mirrors.
- [x] (2026-06-28 21:43Z) Ran focused validation (`pytest`, `ruff`, `git diff --check`) and completed a direct compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Surprises & Discoveries

- Observation: the existing certificate dialog boundary already returns an explicit compatibility payload, so the app-frame cleanup only needed a new frame-owned host for that state.
  Evidence: `src/foliaseal/presentation/qt/app_frame_certificate_management.py` already defines `CertificateDialogCompatibilityState` and returns it in `CertificateDialogOutcome`.

- Observation: the remaining dialog inspection writes were limited to focused fake-Qt tests.
  Evidence: repository search found the live references in `tests/unit/test_qt_app_frame.py`; no production caller depended on `window.settings_dialog` or `window.certificate_*_dialog`.

- Observation: the only current-state documentation drift after implementation was the Qt presentation paragraph in `docs/ARCHITECTURE.md`.
  Evidence: that paragraph still described the fake-Qt compatibility surface as living on `window` until this slice reconciled it.

## Decision Log

- Decision: move dialog inspection state to a frame-owned snapshot instead of deleting the inspection surface outright.
  Rationale: focused tests still need a stable way to inspect the last dialog objects, and moving that state onto `FoliaSealAppFrame` is the narrowest durable step.
  Date/Author: 2026-06-28 / Codex

- Decision: leave the callable window method hooks such as `window.show_app_settings` for a later slice.
  Rationale: the current hybrid seam is about removing window state mirroring, not redesigning the external window command surface.
  Date/Author: 2026-06-28 / Codex

## Outcomes & Retrospective

This slice is intended to remove the last explicit window-level dialog state mirrors from the app frame while preserving the same dialog behavior. The frame becomes the owner of dialog inspection state, and fake-Qt tests shift to the frame-owned properties.

Focused validation passed with `16 passed` in `tests/unit/test_qt_app_frame.py`, `ruff check` reported no issues, and `git diff --check` stayed clean. The direct compliance review found no `docs/SPEC.md` conflict because the slice preserves the same menu and dialog behavior for users.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. It owns the real `QMainWindow`, top-level menus, workspace opening, Save As routing, and app-settings propagation into the live shell port. Recent slices already moved live workspace state off `window.current_*` and removed the `_foliaseal_app_frame` backdoor.

What remains on the same hybrid seam is explicit dialog inspection state written onto the Qt window object. `show_app_settings()` currently writes the constructed dialog to `window.settings_dialog`, and certificate menu actions call into `app_frame_certificate_management.py`, which returns a `CertificateDialogCompatibilityState` that `app_frame.py` mirrors onto `window.certificate_import_dialog`, `window.certificate_creation_dialog`, and `window.certificate_management_dialog`.

Those window attributes exist only so fake-Qt tests in `tests/unit/test_qt_app_frame.py` can inspect the last dialog objects and verify parentage or field defaults. Production behavior does not depend on those writes. The narrow cleanup is therefore to keep the inspection surface but move its ownership onto the frame itself through a typed snapshot and frame properties.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Add a small typed dataclass for the frame-owned dialog snapshot, for example `AppFrameDialogCompatibilityState`, with slots for the settings dialog and the three certificate dialogs. Store one snapshot on `FoliaSealAppFrame`, expose it through a `dialog_compatibility` property plus focused convenience properties such as `settings_dialog` and `certificate_creation_dialog`, and remove the corresponding `window.*_dialog` writes.

Second, keep the existing certificate dialog boundary in `src/foliaseal/presentation/qt/app_frame_certificate_management.py` unchanged. `app_frame.py` should still consume `CertificateDialogCompatibilityState`, but it should merge the returned compatibility data into the frame-owned snapshot rather than mirroring it onto the window.

Third, update `tests/unit/test_qt_app_frame.py` to inspect `frame.settings_dialog`, `frame.certificate_import_dialog`, `frame.certificate_creation_dialog`, and `frame.certificate_management_dialog`. Preserve the same behavior checks for titles, field defaults, dialog parentage, and settings propagation.

Fourth, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer claims that the remaining fake-Qt compatibility surface lives on `window`. It should describe the frame as owning both the workspace snapshot and the dialog inspection snapshot while still exposing window method hooks for now.

Finally, run focused validation. If the compliance review finds only stale docs, fix them in this slice. If it reveals a real production dependency on the removed window dialog attributes, document that dependency instead of reintroducing the mirror silently.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Move the dialog inspection state behind the frame.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Rewrite focused app-frame tests to the frame-owned dialog properties.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Update `docs/ARCHITECTURE.md` and this ExecPlan after validation/compliance review.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_dialog_snapshot_execplan.md

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- opening the application settings or certificate dialogs still returns the same dialog results and parentage behavior;
- focused fake-Qt tests can inspect the last dialogs through frame-owned properties instead of `window.settings_dialog` and `window.certificate_*_dialog`;
- `src/foliaseal/presentation/qt/app_frame.py` no longer writes those dialog objects onto the window;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The user-visible menus and dialogs should work the same, but the inspection state should now be frame-owned.

## Idempotence and Recovery

This is a behavior-preserving app-frame cleanup. It is safe to retry. If a real runtime caller turns out to depend on the old window dialog attributes, introduce an explicit frame or adapter inspection API for that use case rather than restoring untyped window mirroring.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` owning a typed dialog snapshot instead of writing `window.settings_dialog` and `window.certificate_*_dialog`;
- `tests/unit/test_qt_app_frame.py` proving the same behavior through frame-owned dialog properties;
- focused validation output showing the app-frame seam still passes;
- `docs/ARCHITECTURE.md` updated to describe the frame-owned dialog snapshot accurately.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The key interfaces at the end of the slice should be:

    @dataclass(frozen=True)
    class AppFrameDialogCompatibilityState:
        settings_dialog: Any | None = None
        certificate_import_dialog: Any | None = None
        certificate_creation_dialog: Any | None = None
        certificate_management_dialog: Any | None = None

    class FoliaSealAppFrame:
        @property
        def dialog_compatibility(self) -> AppFrameDialogCompatibilityState: ...

        @property
        def settings_dialog(self) -> Any | None: ...

        @property
        def certificate_creation_dialog(self) -> Any | None: ...

`src/foliaseal/presentation/qt/app_frame_certificate_management.py` should keep returning `CertificateDialogCompatibilityState`; the only ownership change in this slice is where that compatibility state is stored and exposed after the frame receives it.

Revision note: Updated on 2026-06-28 by Codex after implementation, validation, and direct compliance review to record the landed architecture reconciliation and passing focused validation evidence.
