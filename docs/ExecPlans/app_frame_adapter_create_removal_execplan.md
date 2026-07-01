# Remove the adapter-level raw-window compatibility constructor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still launches the same GUI and `build_qt_app_frame()` still returns a raw `QMainWindow` for compatibility callers. The visible GUI behavior does not change.

The architectural win is that `QtAppFrameAdapter` itself stops advertising two different construction truths. The adapter will expose only the real `FoliaSealAppFrame` host through `create_frame()` and `launch()`, while the module-level `build_qt_app_frame()` helper remains the single intentional raw-window compatibility projection.

## Child ExecPlan Dependencies

- [x] (2026-06-30 01:20Z) `docs/ExecPlans/app_frame_host_build_helper_execplan.md` is complete; the module-level build surface already exposes `build_qt_app_frame_host()` and keeps `build_qt_app_frame()` as the compatibility wrapper.
- [x] (2026-06-30 01:20Z) No child ExecPlans are required for this bounded adapter-cleanup slice.

## Progress

- [x] (2026-06-30 01:20Z) Re-read `src/foliaseal/presentation/qt/app_frame.py`, focused app-frame tests, and architecture notes to confirm `QtAppFrameAdapter.create()` is now redundant with `create_frame(...).container`.
- [x] (2026-06-30 01:24Z) Removed `QtAppFrameAdapter.create()` and kept the remaining adapter and module-level contracts coherent.
- [x] (2026-06-30 01:24Z) Added focused regression coverage proving the adapter no longer exposes the raw-window compatibility constructor while host and module-level helper paths still work.
- [x] (2026-06-30 01:27Z) Updated `docs/ARCHITECTURE.md` and this ExecPlan to reflect the narrowed compatibility surface.
- [x] (2026-06-30 01:28Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py` passed with `19 passed in 0.31s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-06-30 01:29Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; architecture text now matches the narrowed adapter contract and the slice required no `docs/SPEC.md` change.

## Surprises & Discoveries

- Observation: repository search found no in-repo caller of `QtAppFrameAdapter.create()`.
  Evidence: `rg` over `src/` and `tests/` found `create_frame()` coverage and module-level `build_qt_app_frame()` callers, but no direct use of `QtAppFrameAdapter.create()`.

- Observation: launch behavior is already host-based.
  Evidence: `QtAppFrameAdapter.launch()` already constructs the frame through `create_frame()` and then opens the initial PDF path on the host object.

- Observation: the compliance review reduced to architecture-text reconciliation; the frozen product spec did not require any product-facing update.
  Evidence: `docs/SPEC.md` remains a product-level workflow document, while the only stale statement was in `docs/ARCHITECTURE.md`'s Qt presentation summary.

## Decision Log

- Decision: remove `QtAppFrameAdapter.create()` without changing `build_qt_app_frame()`.
  Rationale: the adapter should tell one architectural truth, but the module-level raw-window helper is still the narrower compatibility seam we intentionally preserved in the previous slice.
  Date/Author: 2026-06-30 / Codex

## Outcomes & Retrospective

This slice leaves only one raw-window compatibility projection in the app-frame surface. Focused app-frame tests, Ruff, and whitespace checks all passed, and the compliance review found no remaining mismatch with the frozen product spec. The main follow-on opportunity is to keep shrinking raw-window compatibility at the module boundary, but that is intentionally outside this bounded slice.

Revision note (2026-06-30 01:27Z): Updated the living plan after landing the code and architecture changes so the progress log and retrospective match the adapter becoming host-only while `build_qt_app_frame()` remains the one compatibility wrapper.

## Context and Orientation

The top-level Qt app frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` is the real behavior host. It owns the `QMainWindow`, menu wiring, settings and certificate dialogs, workspace-open flow, and shell-port forwarding behavior.

`QtAppFrameAdapter` is the late-import factory that loads PySide6 bindings and constructs the host. In the last slice, the adapter gained `create_frame()` and the module gained `build_qt_app_frame_host()`. That made the richer host contract explicit, but one extra compatibility layer remained inside the adapter itself: `QtAppFrameAdapter.create()` still returned the raw window by calling `create_frame(...).container`.

The current module-level compatibility helper `build_qt_app_frame()` is enough for raw-window callers. Keeping the adapter-level raw-window constructor as well means the adapter still presents two different construction stories. This narrow cleanup removes that adapter method, keeps `create_frame()` as the only adapter construction surface, keeps `launch()` unchanged in behavior, and leaves `build_qt_app_frame()` as the only compatibility projection.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Remove the `QtAppFrameAdapter.create()` method entirely. Do not change `create_frame()`, `launch()`, `build_qt_app_frame_host()`, or `build_qt_app_frame()` except if a tiny adjacent docstring tweak is needed to keep the public surface description accurate.

Second, update `tests/unit/test_qt_app_frame.py`. Keep the existing coverage that `QtAppFrameAdapter.create_frame()` returns a real `FoliaSealAppFrame`, that `build_qt_app_frame_host()` returns a real host, and that `build_qt_app_frame()` still returns the raw window. Add one focused regression assertion that `QtAppFrameAdapter` no longer exposes a `create` attribute, so the adapter contract cannot drift back into a split host/window API silently.

Third, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer claims that `QtAppFrameAdapter.create()` remains a raw-window compatibility projection. The architecture text should say that the adapter exposes the real host through `create_frame()` and `launch()`, while `build_qt_app_frame()` remains the module-level raw-window compatibility helper.

Finally, run focused validation. If the compliance review finds only stale architecture wording, fix it in this slice. If it reveals a real caller that still depends on `QtAppFrameAdapter.create()`, stop and document that dependency rather than widening the slice into a migration.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Remove the adapter-level raw-window constructor and add focused coverage.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py
       apply_patch ... on tests/unit/test_qt_app_frame.py

2. Reconcile architecture and update this living ExecPlan.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_adapter_create_removal_execplan.md

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `QtAppFrameAdapter` no longer exposes `create()`;
- `QtAppFrameAdapter.create_frame()` still returns a real `FoliaSealAppFrame`;
- `build_qt_app_frame_host()` still returns a real `FoliaSealAppFrame`;
- `build_qt_app_frame()` still returns the raw window for compatibility callers;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. GUI launch and build behavior should stay the same, but the adapter should no longer expose a parallel raw-window constructor.

## Idempotence and Recovery

This is a behavior-preserving cleanup. It is safe to retry. If a real compatibility caller for `QtAppFrameAdapter.create()` appears during review, restore that method only long enough to document the dependency and split a follow-on migration slice, rather than widening this change into a broader app-frame API redesign.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` exposing only `create_frame()` and `launch()` on `QtAppFrameAdapter`;
- `tests/unit/test_qt_app_frame.py` proving the adapter no longer exposes `create()` while the host and module-level builder paths remain valid;
- `docs/ARCHITECTURE.md` describing `build_qt_app_frame()` as the only remaining raw-window compatibility projection;
- focused validation output showing the app-frame seam still passes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice should be:

    class QtAppFrameAdapter:
        def create_frame(...) -> FoliaSealAppFrame
        def launch(...) -> int

    def build_qt_app_frame_host(...) -> FoliaSealAppFrame
    def build_qt_app_frame(...) -> Any

`QtAppFrameAdapter` should be host-based only. `build_qt_app_frame()` remains the one compatibility helper for callers that only need the raw display object.
