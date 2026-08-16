# Move the live Phase 3 preview-capture helper behind the workspace boundary

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness will still emit the same preview-image artifacts, analysis-image artifacts, text/stamp/debug overlays, preview geometry bounds, and preview-capture diagnostics as before. No visible harness behavior changes.

The architectural win is that the last live Qt preview-capture helper that reads shell-private anatomy will move behind `phase3_harness_workspace.py`. The workspace boundary will then own the remaining live shell extraction path for preview state, instead of leaving one private helper in `phase3_harness.py` to reach into `properties_panel.preview_controls`.

## Child ExecPlan Dependencies

- [x] (2026-06-11 13:08Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the workspace boundary already owns preview-matrix scenario mutation.
- [x] (2026-06-11 13:08Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the workspace boundary already owns request/result/capture reads.
- [x] (2026-06-11 13:08Z) `docs/ExecPlans/phase3_harness_signed_acceptance_workspace_execplan.md` is complete; the signed-acceptance executor already consumes workspace-derived scenario state.
- [x] (2026-06-11 13:08Z) No child ExecPlan is required for this next narrow slice on the same hybrid seam.

## Progress

- [x] (2026-06-11 12:58Z) Re-read the current workspace boundary, the remaining live preview-capture helper, and the focused tests that still prove it directly from `phase3_harness.py`.
- [x] (2026-06-11 13:05Z) Ran the required `explorer-light` dev-loop pass and fixed the next slice boundary: move the live preview-capture helper behind `phase3_harness_workspace.py` without widening the public port.
- [x] (2026-06-11 13:08Z) Wrote this ExecPlan and fixed the implementation target at the last live shell-anatomy read path on the same workspace-boundary hybrid.
- [x] (2026-06-11 13:18Z) Moved the live preview-capture shell extraction path behind the workspace boundary and kept the payload shape unchanged by delegating the lower-level payload builder back into `phase3_harness.py`.
- [x] (2026-06-11 13:21Z) Moved the direct helper tests out of `test_phase3_harness.py` and proved the same payload from the workspace side in `test_qt_phase3_harness_workspace.py`.
- [x] (2026-06-11 13:24Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-11 13:37Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the implemented ownership split.
- [x] (2026-06-11 13:35Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; the only finding was a stale ExecPlan status entry, which has now been corrected. No code changes were required.
- [x] (2026-08-16) Historical publication marker closed; implementation commit `7602aa623` is recorded above and this plan is archival.

## Surprises & Discoveries

- Observation: after the preview-matrix, session-runner, and signed-acceptance slices, the remaining live-shell leak on this hybrid is smaller than expected.
  Evidence: the explorer and local search found no remaining direct `compat_surface` / `properties_panel._workflow` reads in the reviewed seam except the live preview-capture helper path still rooted in `phase3_harness.py`.

- Observation: the actual coupling is not the preview-analysis math but the shell-to-preview-controls extraction.
  Evidence: the current `_capture_preview_render(...)` helper in `phase3_harness.py` only reaches through shell anatomy at the start, then spends the rest of its body shaping image captures and geometry facts from already-extracted preview controls.

- Observation: the workspace boundary did not need a new public verb for this slice.
  Evidence: `QtPhase3HarnessWorkspaceAdapter.capture_state()` already owned the correct public hook; only the internal live preview-capture implementation had to move.

## Decision Log

- Decision: keep this slice centered on the live Qt preview-capture helper only.
  Rationale: this is the smallest remaining anatomy leak on the same hybrid seam. Pulling in headless capture, session-runner changes, or matrix-runner changes would broaden the slice unnecessarily.
  Date/Author: 2026-06-11 / Codex

- Decision: move shell extraction into the workspace module while leaving the lower-level render payload builder in `phase3_harness.py`.
  Rationale: the user asked for simplicity and for cutting cruft. The real architecture problem is ownership of live shell anatomy, not the location of every low-level preview-analysis helper. Keeping the payload math in place avoids a much larger churn while still concentrating shell reads behind the workspace boundary.
  Date/Author: 2026-06-11 / Codex

- Decision: do not widen `Phase3HarnessWorkspacePort`.
  Rationale: the existing `capture_state(...)` verb is already sufficient. The helper move should happen behind that interface, not by adding more public methods.
  Date/Author: 2026-06-11 / Codex

## Outcomes & Retrospective

Implementation, focused validation, documentation reconciliation, and compliance review are complete. The slice moved the live Qt preview-capture shell extraction path behind `phase3_harness_workspace.py`, kept the lower-level preview-analysis payload builder in `phase3_harness.py`, and moved the direct helper tests to the workspace test module.

The resulting design keeps `Phase3HarnessWorkspacePort` unchanged, preserves preview artifact naming and payload keys, and leaves headless preview, signed-acceptance executor ownership, and matrix-runner ownership untouched. The only compliance finding was that this ExecPlan had not yet been updated to reflect the completed work; that documentation issue is now resolved.

## Context and Orientation

The Phase 3 harness is the repository’s Qt-backed evidence runner for signing preview and signed-output acceptance. The workspace seam for that harness lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Earlier slices moved scenario mutation, request/result reads, raw capture-state reads, and signed-acceptance executor state reads behind that boundary.

One private helper still sits outside the seam: the live preview-capture path in `src/foliaseal/presentation/qt/phase3_harness.py`. In plain terms, “live preview capture” means the code path that reads the live preview widgets, copies canonical preview images into the artifacts directory, computes text/stamp geometry facts, and writes optional debug overlays. That helper still reaches into `properties_panel.preview_controls` and `_canonical_preview_render_backend`, which are concrete shell details.

The goal of this slice is not to redesign preview capture. The goal is to make the workspace boundary the only owner of “how do I read the live shell to capture preview artifacts?” while keeping the payload keys, artifact naming, and downstream expectations unchanged. The most relevant files are `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, `tests/unit/test_phase3_harness.py`, and `tests/unit/test_qt_phase3_harness_workspace.py`.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Add a workspace-owned live preview-capture helper that performs the shell extraction step: read the compatibility surface, reach the properties panel, read `preview_controls`, and fetch `_canonical_preview_render_backend`. That helper should then delegate to an injected lower-level payload builder so the heavy preview-analysis logic stays intact.

Second, edit `src/foliaseal/presentation/qt/phase3_harness.py`. Replace the current shell-anatomy preview helper with a lower-level payload builder that no longer accepts `shell`; it should accept the already-extracted preview controls and render backend. Update the Qt workspace builders to pass a partial application of the new workspace-owned helper so `QtPhase3HarnessWorkspaceAdapter.capture_state()` continues to emit the exact same payload.

Third, move the direct helper coverage into `tests/unit/test_qt_phase3_harness_workspace.py`. Those tests should still prove GUI-preview preservation, bordered analysis-preview generation, and use of analysis-space bounds for raster detection, but they should now do so from the workspace side. Remove the direct private-helper tests from `tests/unit/test_phase3_harness.py`.

Fourth, run focused validation, update `docs/ARCHITECTURE.md` and this ExecPlan, and perform the required compliance review. If a mismatch appears, fix only the mismatch inside this slice and keep the boundary narrow.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Move the live preview-capture shell extraction path behind the workspace boundary.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py

2. Move the direct helper coverage to the workspace test module.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_phase3_harness.py

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun the focused validation commands if any code or tests changed during reconciliation.

5. Run the architectural compliance review, address any findings inside this slice only, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the live preview-capture path no longer reads shell-private anatomy from `phase3_harness.py`;
- `QtPhase3HarnessWorkspaceAdapter.capture_state()` still emits the same render-capture payload keys and artifact naming for the same preview inputs;
- the GUI-preview preservation and analysis-space detection tests now live with the workspace boundary instead of the top-level harness module;
- `Phase3HarnessWorkspacePort` is unchanged, and no session lifecycle or sign-submit verbs are added;
- headless capture, signed-acceptance executor ownership, and matrix-runner ownership remain unchanged.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The same preview artifacts and geometry facts must still be produced after the move.

## Idempotence and Recovery

This is a behavior-preserving refactor inside local harness code. It is safe to retry. If the move breaks tests, keep the workspace-owned shell extraction path and repair only the injected lower-level payload builder until the payload shape matches again.

If a mismatch appears in artifact naming or payload keys, treat that as a regression and fix it immediately in this slice. Do not paper over it by changing downstream tests or summary code to accept a different shape.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a workspace-owned live preview-capture helper in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`;
- a smaller `src/foliaseal/presentation/qt/phase3_harness.py` that no longer owns the live shell extraction path for preview capture;
- moved tests in `tests/unit/test_qt_phase3_harness_workspace.py` proving the same render-capture payload;
- focused validation output showing the workspace tests and affected harness tests still pass.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the Qt workspace builder should use a preview-capture handoff close to:

    capture_preview_render=partial(
        capture_qt_preview_render,
        build_preview_render_capture_payload=_build_qt_preview_render_capture_payload,
    )

The workspace helper should own the live shell extraction step:

    compat = _compat_surface(shell)
    properties_panel = compat.properties_panel
    return build_preview_render_capture_payload(
        preview_controls=properties_panel.preview_controls,
        canonical_preview_render_backend=getattr(
            properties_panel,
            "_canonical_preview_render_backend",
            None,
        ),
        ...
    )

The lower-level payload builder in `phase3_harness.py` must keep the current payload keys and artifact naming. This slice must not modify `Phase3HarnessWorkspacePort`, `Phase3SignedAcceptanceScenarioExecutor`, or `Phase3SignedAcceptanceMatrixRunner`.

Revision note: Created on 2026-06-11 by Codex for the next `dev-loop` implementation slice on the selected Phase 3 harness workspace-boundary hybrid.
Revision note: Updated on 2026-06-11 after implementation and focused validation to record the moved live preview-capture helper, migrated tests, and resolved compliance note about stale plan status.
