# Remove the remaining `compat_surface` harness fallback

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the live Phase 3 harness reaches the signing workspace through one explicit non-production seam: `testing_adapter`. The shell may still export `compat_surface` for broader legacy plumbing, but the harness boundary will no longer consume it.

The user-visible behavior is unchanged for the real app and the real harness. The architectural win is that the harness workspace stops carrying a transitional compatibility fallback and depends only on the explicit testing contract introduced in the previous slices. You can see the result by running the focused Phase 3 workspace tests and observing that they pass with `testing_adapter`-backed fakes only.

## Child ExecPlan Dependencies

- [x] (2026-07-02 00:19Z) `docs/ExecPlans/signing_workspace_testing_port_execplan.md` introduced the explicit `SigningWorkspaceTestingPort`.
- [x] (2026-07-02 00:19Z) `docs/ExecPlans/signing_workspace_raw_shell_fallback_removal_execplan.md` removed the raw-shell fallback and left `compat_surface` as the last transitional harness path.
- [x] (2026-07-02 00:19Z) No child ExecPlans are required for this bounded follow-up slice.

## Progress

- [x] (2026-07-02 00:19Z) Re-read the current seam after `200030d3f` and confirmed that `phase3_harness_workspace.py` still prefers `testing_adapter` but falls back to `compat_surface`.
- [x] (2026-07-02 00:20Z) Used an `explorer-light` subagent to confirm no non-test `src/` callers still depend on the harness-side `compat_surface` fallback.
- [x] (2026-07-02 00:28Z) Removed the `compat_surface` branch from `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, deleted the unused compatibility wrapper, and tightened the contract error to require `testing_adapter`.
- [x] (2026-07-02 00:31Z) Updated `tests/unit/test_qt_phase3_harness_workspace.py` so its live-shell fakes expose `testing_adapter` instead of `compat_surface`, and replaced the old fallback assertion with explicit failure coverage for `compat_surface`-only shells.
- [x] (2026-07-02 00:34Z) Reconciled `docs/ARCHITECTURE.md` so the harness boundary is described as `testing_adapter`-only.
- [x] (2026-07-02 00:37Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py` passed with `108 passed in 10.48s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-07-02 00:43Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; the slice is compliant, and the only follow-up was correcting one stale sentence in this living ExecPlan.

## Surprises & Discoveries

- Observation: after the raw-shell fallback removal, the only remaining in-repo consumers of the harness-side compatibility path are focused tests in `tests/unit/test_qt_phase3_harness_workspace.py`.
  Evidence: the explorer found no non-test `src/` readers of `compat_surface` through the harness boundary; current matches are concentrated in the test file.

- Observation: `compat_surface` is still intentionally exported by `SigningWorkspaceCompatibilitySurface`, but that is separate shell plumbing, not a required harness dependency.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` still installs both `widget.compat_surface` and `widget.testing_adapter`.

- Observation: removing the fallback did not change the focused pass count because the slice mostly retargeted test doubles instead of adding a new execution path.
  Evidence: the focused workspace/shell suite still passed with `108 passed in 10.48s`.

## Decision Log

- Decision: remove the harness-side `compat_surface` fallback now, but keep the shell’s exported `compat_surface` untouched in this slice.
  Rationale: this narrows the harness dependency without reopening the broader compatibility-export cleanup, which is a separate seam.
  Date/Author: 2026-07-02 / Codex

## Outcomes & Retrospective

This slice should leave the harness on one explicit non-production seam while preserving the shell’s broader compatibility exports for other legacy callers. Success means the Phase 3 workspace boundary no longer knows how to adapt `compat_surface`, and the focused tests prove the explicit testing seam is sufficient.

## Context and Orientation

The live Phase 3 harness workspace boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. It owns `QtPhase3HarnessWorkspaceAdapter`, which applies preview scenarios, captures preview state, and reads current request/result from the live signing workspace. After this slice, `_testing_surface(shell)` resolves only `shell.testing_adapter` and rejects any shell that does not expose that explicit testing seam.
The explicit testing seam is defined in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` as `SigningWorkspaceTestingPort`. The concrete shell installs a `SigningWorkspaceTestingAdapter` as `widget.testing_adapter` during composition. The shell still exports `compat_surface` for broader legacy plumbing, but the harness no longer consumes it.

The work in this slice was therefore test-heavy. `tests/unit/test_qt_phase3_harness_workspace.py` was retargeted from `compat_surface`-only fakes to `testing_adapter` fakes so the boundary could delete the last compatibility branch. `tests/unit/test_qt_signing_shell.py` remained focused on the shell exports themselves; it still has value because the shell continues to install both `compat_surface` and `testing_adapter`.

`docs/ARCHITECTURE.md` now describes the harness boundary as `testing_adapter`-only, which matches the stricter seam implemented here.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Remove the `_CompatibilityTestingPort` class if it becomes unused, delete the `compat_surface` branch in `_testing_surface(shell)`, and tighten the `TypeError` to require `testing_adapter` specifically. The live adapter should now operate only against the explicit `SigningWorkspaceTestingPort`.

Second, edit `tests/unit/test_qt_phase3_harness_workspace.py`. Replace the compat-surface fakes with minimal `testing_adapter` fakes in the scenario-application, request/result capture, and preview-render tests. Replace the old compat-fallback test with a failure test that proves a `compat_surface`-only shell is rejected.

Third, update `docs/ARCHITECTURE.md`. The repo map, the detailed narrative section, the `phase3_harness_workspace.py` row, and the known-debt note should all say that the harness boundary is `testing_adapter`-only. Keep the compatibility-surface row intact, because the shell still exports it for broader legacy plumbing.

Finally, run focused validation and the compliance review. If the review finds only stale wording, fix it in this slice. If it finds a non-test live caller still depending on `compat_surface`, stop and document that before widening the work.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the harness boundary, focused tests, architecture notes, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/signing_workspace_testing_adapter_only_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py
       git diff --check

   Observed result:

       108 passed in 10.48s
       All checks passed!

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `QtPhase3HarnessWorkspaceAdapter` requires `testing_adapter` and no longer adapts `compat_surface`;
- the focused live-shell tests use `testing_adapter` fakes only;
- a `compat_surface`-only fake shell is rejected explicitly;
- `docs/ARCHITECTURE.md` no longer claims the harness boundary falls back to `compat_surface`;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavioral. The live harness should still apply scenarios and capture preview state through the explicit testing seam, and any fake shell that still offers only `compat_surface` should fail fast.

## Idempotence and Recovery

This is a behavior-preserving refactor for real shells and an intentional contract tightening for tests and legacy fakes. It is safe to retry. If a test breaks after the fallback is removed, repair the fake by adding `testing_adapter`; do not restore the harness-side `compat_surface` branch.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_harness_workspace.py` resolving only `testing_adapter`;
- focused tests in `tests/unit/test_qt_phase3_harness_workspace.py` using `testing_adapter` fakes;
- architecture notes reflecting the stricter seam;
- validation output showing the focused suite still passes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interface remains:

    class SigningWorkspaceTestingPort(Protocol):
        properties_panel: SignaturePropertiesPanel
        def signature_appearance(...) -> SignatureAppearance | None
        def set_timestamp_required(...) -> None
        def apply_signature_rect_placement(...) -> None
        def refresh_viewer(...) -> None
        def current_request(...) -> SigningRequest | None
        def last_signing_result(...) -> SigningResult | None

At the end of this slice, the live harness boundary depends only on:

    shell.testing_adapter

The broader `compat_surface` export remains installed on the shell, but the harness no longer consumes it.
