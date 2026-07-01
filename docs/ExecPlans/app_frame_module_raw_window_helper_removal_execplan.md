# Remove the module-level raw-window app-frame helper

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still launches the same GUI through `launch_qt_app_frame()`. No user-visible workflow changes.

The architectural win is that the Qt app-frame surface becomes fully host-based. The public construction API will expose only `FoliaSealAppFrame` through `build_qt_app_frame_host()` and the launch helper, instead of still carrying one final module-level helper that projects the host back down to a raw `QMainWindow`.

## Child ExecPlan Dependencies

- [x] (2026-06-30 01:39Z) `docs/ExecPlans/app_frame_adapter_create_removal_execplan.md` is complete; `QtAppFrameAdapter` is already host-based and no longer exposes its own raw-window compatibility constructor.
- [x] (2026-06-30 01:39Z) No child ExecPlans are required for this bounded module-surface cleanup.

## Progress

- [x] (2026-06-30 01:39Z) Re-read `src/foliaseal/presentation/qt/app_frame.py`, package exports, focused app-frame tests, and current architecture notes to confirm `build_qt_app_frame()` is the last remaining raw-window compatibility projection.
- [x] (2026-06-30 01:42Z) Removed `build_qt_app_frame()` and the package-level export while keeping host and launch behavior unchanged.
- [x] (2026-06-30 01:42Z) Updated focused regression coverage to prove the raw-window helper is gone and the host/launch paths still work.
- [x] (2026-06-30 01:45Z) Updated `docs/ARCHITECTURE.md` and this ExecPlan to reflect the fully host-based module surface.
- [x] (2026-06-30 01:47Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py` passed with `19 passed in 0.31s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-06-30 01:48Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; architecture text now matches the fully host-based module surface and the slice required no `docs/SPEC.md` change.

## Surprises & Discoveries

- Observation: repository search found no in-repo production caller of `build_qt_app_frame()`.
  Evidence: `rg` over `src/` found `launch_qt_app_frame()` as the real runtime entrypoint; the remaining direct code reference to `build_qt_app_frame()` was its own focused test.

- Observation: the project specification explicitly prefers cleaner architecture over compatibility layers during V1.
  Evidence: `docs/SPEC.md` says compatibility with previously saved objects is not a V1 priority and that architecture should favor clarity and replaceability over preserving existing module boundaries.

- Observation: the compliance review reduced to architecture-text reconciliation and package-surface cleanup; the frozen product spec did not require any product-facing change.
  Evidence: `docs/SPEC.md` remains a product-level workflow document, while the stale references were limited to `docs/ARCHITECTURE.md`, package exports, and the focused app-frame regression test.

## Decision Log

- Decision: remove `build_qt_app_frame()` instead of deprecating it in place.
  Rationale: there is no in-repo production caller, the host-based surface already exists, and V1 guidance favors removing legacy compatibility layers when the cleaner model is ready.
  Date/Author: 2026-06-30 / Codex

## Outcomes & Retrospective

This slice eliminates the last raw-window app-frame construction seam. Focused app-frame tests, Ruff, and whitespace checks all passed, and the compliance review found no remaining mismatch with the frozen product spec. The module surface is now fully host-based, with `launch_qt_app_frame()` as the runtime entrypoint and `build_qt_app_frame_host()` as the direct construction helper.

Revision note (2026-06-30 01:45Z): Updated the living plan after landing the code and architecture changes so the progress log and retrospective match the fully host-based module surface.

## Context and Orientation

The top-level Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` is the real behavior host. It owns the `QMainWindow`, menu wiring, settings dialog, certificate dialogs, workspace-open flow, and shell-port forwarding behavior.

The adapter and launch surfaces are already aligned with that truth. `QtAppFrameAdapter.create_frame()` returns `FoliaSealAppFrame`, `build_qt_app_frame_host()` returns `FoliaSealAppFrame`, and `launch_qt_app_frame()` launches the real host.

One compatibility artifact remains: `build_qt_app_frame()` still returns `build_qt_app_frame_host(...).container`, which exposes only the raw `QMainWindow`. Repository search shows that no current production path uses that helper, and the package-level Qt exports still re-export it. This narrow cleanup removes that helper and its export, updates the tests that were proving the old compatibility projection, and reconciles the architecture text to the fully host-based module surface.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Remove the `build_qt_app_frame(...) -> Any` helper entirely. Do not change `build_qt_app_frame_host()` or `launch_qt_app_frame()`.

Second, edit `src/foliaseal/presentation/qt/__init__.py` and remove `build_qt_app_frame` from both the import list and `__all__`.

Third, update `tests/unit/test_qt_app_frame.py`. Replace the old raw-window helper coverage with a focused regression assertion that the module no longer exposes `build_qt_app_frame`. Keep the host-construction and launch coverage intact.

Fourth, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer lists `build_qt_app_frame()` as a main entry point or as a remaining compatibility projection. The architecture text should say that `build_qt_app_frame_host()` and `QtAppFrameAdapter.create_frame()` expose the real host directly, while `launch_qt_app_frame()` remains the supported runtime entrypoint.

Finally, run focused validation. If the compliance review finds only stale architecture wording, fix it in this slice. If a real caller appears unexpectedly, stop and document that dependency rather than widening the slice into a migration project.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Remove the last raw-window helper and update focused regression coverage.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py
       apply_patch ... on src/foliaseal/presentation/qt/__init__.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

2. Reconcile architecture and update this living ExecPlan.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_module_raw_window_helper_removal_execplan.md

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/__init__.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `build_qt_app_frame()` no longer exists in `app_frame.py`;
- `foliaseal.presentation.qt` no longer exports `build_qt_app_frame`;
- `build_qt_app_frame_host()` still returns a real `FoliaSealAppFrame`;
- `launch_qt_app_frame()` still works with the focused fake-Qt tests;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/__init__.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. The GUI launch path should stay the same, but the module should no longer advertise a raw-window construction helper.

## Idempotence and Recovery

This is a behavior-preserving cleanup. It is safe to retry. If a real caller of `build_qt_app_frame()` appears during review, restore the helper only long enough to document the dependency and split a follow-on migration slice rather than widening this change.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` exposing only `build_qt_app_frame_host()` and `launch_qt_app_frame()` as the module-level app-frame helpers;
- `src/foliaseal/presentation/qt/__init__.py` no longer exporting `build_qt_app_frame`;
- `tests/unit/test_qt_app_frame.py` proving the raw-window helper is gone while host and launch paths remain valid;
- `docs/ARCHITECTURE.md` describing the fully host-based module surface;
- focused validation output showing the app-frame seam still passes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice should be:

    def build_qt_app_frame_host(...) -> FoliaSealAppFrame
    def launch_qt_app_frame(...) -> int

The Qt app-frame module should expose host-based construction only. Raw `QMainWindow` access should remain an internal property of the host object, not a separate public construction path.
