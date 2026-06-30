# Deepen the app-frame adapter contract to return a real frame host

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, FoliaSeal still launches the same GUI window and `build_qt_app_frame()` still returns a raw `QMainWindow` for compatibility callers. The visible GUI behavior does not change.

The architectural win is that `QtAppFrameAdapter` now has an explicit frame-building contract that returns a real `FoliaSealAppFrame`, while the raw-window helper becomes a compatibility projection of that richer object. This makes the top-level adapter honest about the fact that the real behavior host is the frame, not the bare window.

## Child ExecPlan Dependencies

- [x] (2026-06-30 00:25Z) `docs/ExecPlans/app_frame_settings_snapshot_execplan.md` is complete; the raw window no longer carries app-frame state or command hooks.
- [x] (2026-06-30 00:25Z) No child ExecPlans are required for this bounded adapter-contract slice.

## Progress

- [x] (2026-06-30 00:25Z) Re-read `app_frame.py`, adapter/build/launch tests, and the current architecture notes to confirm the top-level adapter still projects only a raw window.
- [x] (2026-06-30 00:31Z) Added an explicit `QtAppFrameAdapter.create_frame()` path that returns `FoliaSealAppFrame`, and rewired `launch()` to use that frame host directly.
- [x] (2026-06-30 00:32Z) Kept `create()` and `build_qt_app_frame()` as raw-window compatibility projections and added a focused regression test for the new frame-returning adapter path.
- [x] (2026-06-30 00:36Z) Updated `docs/ARCHITECTURE.md` so the Qt presentation summary now describes `create_frame()` as the explicit frame-host contract and `build_qt_app_frame()` as the raw-window compatibility projection.
- [x] (2026-06-30 00:37Z) Ran focused validation (`pytest`, `ruff`, `git diff --check`) and completed a direct compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`.

## Surprises & Discoveries

- Observation: no current in-repo caller depends on `QtAppFrameAdapter.create()` returning the raw window except the compatibility helper `build_qt_app_frame()`.
  Evidence: repository search found `build_qt_app_frame()` as the only non-doc caller of `QtAppFrameAdapter.create()`.

- Observation: `launch_qt_app_frame()` already needed the real frame host rather than the raw window because it calls `show()` on `frame.window` and optionally opens an initial PDF through `frame.open_pdf_path(...)`.
  Evidence: `QtAppFrameAdapter.launch()` already constructed `FoliaSealAppFrame` directly instead of going through `create()`.

- Observation: the only current-state documentation drift after implementation was the Qt presentation summary in `docs/ARCHITECTURE.md`.
  Evidence: that paragraph still described the build/adapter surface only in terms of the raw window until this slice reconciled it.

## Decision Log

- Decision: add `QtAppFrameAdapter.create_frame()` and keep `create()` as the raw-window compatibility wrapper.
  Rationale: this deepens the adapter contract without breaking existing callers that still want only the raw window.
  Date/Author: 2026-06-30 / Codex

- Decision: keep `build_qt_app_frame()` returning the raw window in this slice.
  Rationale: the current tracer bullet is about making the richer host explicit, not about removing the compatibility helper all at once.
  Date/Author: 2026-06-30 / Codex

## Outcomes & Retrospective

This slice is intended to make the top-level app-frame adapter truthful about its real product: a `FoliaSealAppFrame` behavior host. The raw-window helper remains available, but it becomes a deliberate projection rather than the only exposed contract.

Focused validation passed with `17 passed` in `tests/unit/test_qt_app_frame.py`, `ruff check` reported no issues, and `git diff --check` stayed clean. The direct compliance review found no `docs/SPEC.md` conflict because the slice preserves the same GUI launch and menu behavior while only deepening the adapter contract.

## Context and Orientation

The top-level Qt application frame lives in `src/foliaseal/presentation/qt/app_frame.py`. `FoliaSealAppFrame` owns the real `QMainWindow`, top-level menus, app settings, certificate dialogs, workspace opening, and shell-port forwarding behavior. Recent slices removed the raw-window compatibility cruft, so the window is now mostly just a display container.

Even so, the adapter contract remained slightly shallow: `QtAppFrameAdapter.create()` returned only the raw window, while `QtAppFrameAdapter.launch()` separately constructed a real `FoliaSealAppFrame`. That meant the adapter already knew the frame was the true host, but only one code path admitted it.

The narrow cleanup is therefore to expose an explicit `create_frame()` contract on the adapter, use it in `launch()`, and keep `create()` and `build_qt_app_frame()` as compatibility projections for callers that only need the window object.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/app_frame.py`. Add `QtAppFrameAdapter.create_frame(...) -> FoliaSealAppFrame` that constructs and returns the real frame host using the same parameters already accepted by `create()` and `launch()`. Rewrite `create()` as a thin compatibility wrapper that returns `create_frame(...).container`. Rewrite `launch()` to call `create_frame(...)` instead of instantiating `FoliaSealAppFrame` inline.

Second, update `tests/unit/test_qt_app_frame.py`. Keep the existing `build_qt_app_frame()` compatibility test proving it still returns the raw window, and add a focused test that `QtAppFrameAdapter.create_frame()` returns a real `FoliaSealAppFrame` whose `container` and `window` are the same fake main window instance.

Third, reconcile `docs/ARCHITECTURE.md` so the Qt presentation summary no longer treats the adapter/build surface as if only the raw window mattered. It should describe the frame as the explicit behavior host and the raw-window helper as a compatibility projection.

Finally, run focused validation. If the compliance review finds only stale docs, fix them in this slice. If it reveals a real production dependency on the older shallower adapter contract, document that dependency rather than widening the slice further.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the explicit adapter frame-construction path.

       apply_patch ... on src/foliaseal/presentation/qt/app_frame.py

2. Add focused regression coverage for the richer adapter contract.

       apply_patch ... on tests/unit/test_qt_app_frame.py

3. Update `docs/ARCHITECTURE.md` and this ExecPlan after validation/compliance review.

       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/app_frame_adapter_frame_contract_execplan.md

4. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `QtAppFrameAdapter.create_frame()` returns a real `FoliaSealAppFrame`;
- `QtAppFrameAdapter.create()` and `build_qt_app_frame()` still return the raw window for compatibility callers;
- `launch_qt_app_frame()` still creates, shows, and optionally seeds the GUI the same way;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_app_frame.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/app_frame.py tests/unit/test_qt_app_frame.py
    git diff --check

Acceptance is behavioral. GUI launch and menu behavior should stay the same, but the adapter should now expose the real frame host explicitly.

## Idempotence and Recovery

This is a behavior-preserving adapter-contract cleanup. It is safe to retry. If a caller unexpectedly depended on `create()` doing something beyond returning the raw window, keep the compatibility wrapper behavior stable and add a narrowly scoped adapter method rather than collapsing back to the shallower contract.

## Artifacts and Notes

The most important final evidence for this slice will be:

- `src/foliaseal/presentation/qt/app_frame.py` defining `QtAppFrameAdapter.create_frame()` and using it in `launch()`;
- `tests/unit/test_qt_app_frame.py` proving both the richer frame path and the raw-window compatibility path;
- focused validation output showing the app-frame seam still passes;
- `docs/ARCHITECTURE.md` updated to describe the richer adapter contract accurately.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interfaces at the end of the slice should be:

    class QtAppFrameAdapter:
        def create_frame(...) -> FoliaSealAppFrame: ...
        def create(...) -> Any: ...
        def launch(...) -> int: ...

    def build_qt_app_frame(...) -> Any

`FoliaSealAppFrame` remains the real behavior host. `create_frame()` should expose that fact directly, while `create()` and `build_qt_app_frame()` remain the raw-window compatibility surface for callers that only need the display object.

Revision note: Updated on 2026-06-30 by Codex after implementation, validation, and direct compliance review to record the landed architecture reconciliation and passing focused validation evidence.
