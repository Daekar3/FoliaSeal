# Add an explicit module-level app-frame host builder

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still launches the same GUI and `build_qt_app_frame()` still returns a raw `QMainWindow` for compatibility callers. The visible GUI behavior does not change.

The architectural win is that the module-level build surface now matches the adapter-level truth: there is an explicit helper that returns a real `FoliaSealAppFrame` host, and the raw-window helper becomes an intentional compatibility projection of that richer object.

## Child ExecPlan Dependencies

- [x] (2026-06-30 00:50Z) `docs/ExecPlans/app_frame_adapter_frame_contract_execplan.md` is complete; the adapter already exposes `create_frame()` as the richer host contract.
- [x] (2026-06-30 00:50Z) No child ExecPlans are required for this bounded build-helper slice.

## Progress

- [x] (2026-06-30 00:50Z) Re-read `app_frame.py`, `src/foliaseal/presentation/qt/__init__.py`, focused app-frame tests, and the current architecture notes to confirm the module-level build surface still only projected the raw window.
- [x] (2026-06-30 00:54Z) Added `build_qt_app_frame_host()` returning `FoliaSealAppFrame` and rewired `build_qt_app_frame()` into a raw-window compatibility wrapper.
- [x] (2026-06-30 00:55Z) Exported the new helper through `src/foliaseal/presentation/qt/__init__.py` and added focused regression coverage for the richer module-level contract.
- [x] (2026-06-30 01:04Z) Updated `docs/ARCHITECTURE.md` and this ExecPlan to reflect the landed build-helper contract and the raw-window compatibility projection.
- [x] (2026-06-30 01:07Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py` passed with `18 passed in 0.31s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-06-30 01:08Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; architecture text now matches the landed helper contract and the slice required no `docs/SPEC.md` change.

## Surprises & Discoveries

- Observation: `build_qt_app_frame()` itself was the only remaining module-level place that hid the real frame host behind a raw-window projection.
  Evidence: repository search found the richer adapter contract already existed as `QtAppFrameAdapter.create_frame()`, while the module-level build helper still returned only the raw window.

- Observation: exposing the richer helper did not require any CLI change because the CLI already uses `launch_qt_app_frame()`.
  Evidence: `src/foliaseal/__main__.py` imports and dispatches only `launch_qt_app_frame`.

- Observation: the compliance review for this slice reduced to architecture-text reconciliation; the frozen product spec did not require any product-facing adjustment.
  Evidence: `docs/SPEC.md` remains a product-level workflow/specification document, while the only stale statements were in `docs/ARCHITECTURE.md`'s Qt presentation summary and startup sequence.

## Decision Log

- Decision: add `build_qt_app_frame_host()` and keep `build_qt_app_frame()` as the raw-window compatibility wrapper.
  Rationale: this makes the module-level API truthful without forcing all callers to migrate in one slice.
  Date/Author: 2026-06-30 / Codex

- Decision: export the new helper through `src/foliaseal/presentation/qt/__init__.py`.
  Rationale: callers using the package-level Qt presentation exports should be able to access the richer host contract without importing the implementation module directly.
  Date/Author: 2026-06-30 / Codex

## Outcomes & Retrospective

This slice aligns the module-level build surface with the already-landed adapter truth: the real product is a `FoliaSealAppFrame` host, while the raw window remains a compatibility projection. Focused app-frame tests, Ruff, and whitespace checks all passed, and the compliance review found no remaining mismatch with the frozen product spec. The main follow-on opportunity is broader migration away from raw-window compatibility callers, but that is intentionally outside this bounded slice.

## Context and Orientation

The top-level Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` is the real behavior host: it owns the main window, menus, settings dialog, certificate dialogs, workspace-open flow, and shell-port forwarding behavior. The adapter contract was already made truthful in the previous slice by adding `QtAppFrameAdapter.create_frame()`.

The remaining shallow spot was the module-level build helper. `build_qt_app_frame()` still returned only the raw `QMainWindow`, even though the adapter now exposed the real frame host. That meant the public helper surface lagged one step behind the adapter surface.

The narrow cleanup is therefore to add `build_qt_app_frame_host()` returning `FoliaSealAppFrame`, keep `build_qt_app_frame()` as a compatibility wrapper returning `.container`, and add focused tests proving both contracts.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Add `build_qt_app_frame_host(...) -> FoliaSealAppFrame` that constructs `QtAppFrameAdapter()` and returns `adapter.create_frame(...)`. Rewrite `build_qt_app_frame()` as a thin wrapper returning `build_qt_app_frame_host(...).container`. Do not change `launch_qt_app_frame()` in this slice.

Second, update `src/foliaseal/presentation/qt/__init__.py` to export `build_qt_app_frame_host` alongside the existing app-frame helpers.

Third, update `tests/unit/test_qt_app_frame.py`. Keep the existing raw-window `build_qt_app_frame()` compatibility test, and add a focused regression test that `build_qt_app_frame_host()` returns a real `FoliaSealAppFrame` whose `container` and `window` are the same fake main window instance.

Fourth, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer treats the module-level build surface as raw-window-only. It should describe `build_qt_app_frame_host()` as the explicit host helper and `build_qt_app_frame()` as the raw-window compatibility projection.

Finally, run focused validation. If the compliance review finds only stale docs, fix them in this slice. If it reveals a real production dependency on the older shallower helper contract, document that dependency rather than widening the slice further.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the explicit module-level frame-host helper.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Export the helper and add focused regression coverage.

       apply_patch ... on src/foliaseal/presentation/qt/__init__.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Update `docs/ARCHITECTURE.md` and this ExecPlan after validation/compliance review.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_host_build_helper_execplan.md

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/__init__.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `build_qt_app_frame_host()` returns a real `FoliaSealAppFrame`;
- `build_qt_app_frame()` still returns the raw window for compatibility callers;
- package-level Qt presentation exports include the richer helper;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/__init__.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. GUI behavior should stay the same, but the module-level build surface should now expose the real frame host explicitly.

## Idempotence and Recovery

This is a behavior-preserving build-helper cleanup. It is safe to retry. If a caller unexpectedly depends on `build_qt_app_frame()` returning more than the raw window, keep that compatibility wrapper stable and add a separate narrowly scoped helper rather than collapsing the richer host contract.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` defining `build_qt_app_frame_host()` and keeping `build_qt_app_frame()` as the raw-window wrapper;
- `src/foliaseal/presentation/qt/__init__.py` exporting the richer helper;
- `tests/unit/test_qt_app_frame.py` proving both the richer host path and the raw-window compatibility path;
- focused validation output showing the app-frame seam still passes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice should be:

    def build_qt_app_frame_host(...) -> FoliaSealAppFrame
    def build_qt_app_frame(...) -> Any
    def launch_qt_app_frame(...) -> int

`build_qt_app_frame_host()` should expose the real behavior host directly, while `build_qt_app_frame()` remains the raw-window compatibility projection for callers that only need the display object.

Revision note (2026-06-30 01:04Z): Updated the living plan after landing the code slice so the progress log, retrospective, and architecture-reconciliation steps match the new `build_qt_app_frame_host()` contract instead of the older raw-window-only module helper description.
