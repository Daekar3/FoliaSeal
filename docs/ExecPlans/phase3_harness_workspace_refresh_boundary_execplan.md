# Extend the Phase 3 harness workspace boundary with viewer priming refresh

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 signed-acceptance matrix runner will still open a live signing shell, prime the viewer before scenario iteration, and produce the same signed-output summary artifacts. The visible harness output does not change.

The architectural win is that viewer priming will stop being a direct `compat_surface(shell).refresh_viewer()` call in `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`. Instead, the existing `src/foliaseal/presentation/qt/phase3_harness_workspace.py` boundary will grow one tiny verb, `refresh_viewer()`, so the runner can ask the workspace to do that priming without knowing shell anatomy. The user-visible proof is focused test coverage and unchanged signed-acceptance runner behavior.

## Child ExecPlan Dependencies

- [x] (2026-06-22 22:32Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the workspace boundary already owns scenario mutation for live and headless harness paths.
- [x] (2026-06-22 22:32Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the same boundary already owns current-request, last-signing-result, and raw capture reads.
- [x] (2026-06-22 22:32Z) No child ExecPlans are required for this narrow viewer-priming slice.

## Progress

- [x] (2026-06-22 22:32Z) Re-read the current harness workspace boundary, the signed-acceptance matrix runner, the live workspace builders in `phase3_harness.py`, the existing runner tests, and the current architecture wording.
- [x] (2026-06-22 22:32Z) Completed the required `explorer-light` dev-loop audit and fixed the next slice at one viewer-priming refresh verb, not a broader harness cleanup.
- [x] (2026-06-22 22:36Z) Added `refresh_viewer()` to `Phase3HarnessWorkspacePort`, implemented it in the Qt adapter as the private compatibility-surface refresh, and implemented it in the headless adapter as a no-op.
- [x] (2026-06-22 22:36Z) Rewired the signed-acceptance matrix runner to depend on the existing workspace builder instead of a direct `compat_surface` accessor for viewer priming, and removed the now-unused `_shell_compat_surface` helper from `phase3_harness.py`.
- [x] (2026-06-22 22:36Z) Added focused tests proving the runner uses the workspace boundary and that the Qt/headless adapters handle `refresh_viewer()` safely.
- [x] (2026-06-22 22:37Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-22 22:37Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the deeper boundary ownership so the workspace boundary now explicitly owns signed-acceptance viewer priming refresh.
- [x] (2026-06-22 22:37Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; no corrective follow-on was required.
- [x] (2026-08-16) Historical publication marker closed; implementation commit `612a11a7b` is recorded above and this plan is archival.

## Surprises & Discoveries

- Observation: the harness workspace boundary already owns richer behavior than the signed-acceptance matrix runner still acknowledges.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_workspace.py` already owns `apply_scenario(...)`, `current_request()`, `last_signing_result()`, and `capture_state(...)`, while `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` still reaches out to `compat_surface(shell).refresh_viewer()` directly.

- Observation: the signed-acceptance per-scenario executor already depends on the workspace builder, so the matrix runner is the remaining outlier.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` wires `build_workspace=_build_preview_matrix_qt_workspace` into `Phase3SignedAcceptanceScenarioExecutor`, but `_build_phase3_signed_acceptance_matrix_runner()` still passes `compat_surface=_shell_compat_surface`.

- Observation: centralizing the refresh action did not require moving the event pump into the workspace boundary.
  Evidence: the focused regression set stayed green when `QtPhase3HarnessWorkspaceAdapter.refresh_viewer()` only delegated to the compatibility-surface refresh and both callers kept their existing `QApplication.processEvents()` calls, preserving timing without double-pumping.

## Decision Log

- Decision: keep this third tracer bullet limited to one viewer-priming verb on the existing workspace boundary.
  Rationale: the explorer audit found a single remaining direct compatibility-surface call in the matrix runner. Pulling in broader harness or shell cleanup would widen the blast radius without improving the chosen seam proportionally.
  Date/Author: 2026-06-22 / Codex

- Decision: make the headless workspace implementation of `refresh_viewer()` a deliberate no-op.
  Rationale: headless preview-matrix execution has no live Qt viewer to prime, but the shared boundary remains clearer if both adapters implement the same verb.
  Date/Author: 2026-06-22 / Codex

## Outcomes & Retrospective

Implementation, focused validation, architecture-doc reconciliation, and compliance review are complete. The workspace boundary now owns viewer priming refresh in addition to scenario, request, result, and capture behavior, and the signed-acceptance matrix runner no longer reaches directly to `compat_surface` for its pre-scenario refresh.

The slice stayed narrow as intended. It did not absorb broader signed-acceptance lifecycle behavior, session-runner concerns, or compatibility-surface cleanup beyond the single direct refresh call. The remaining work is only the final commit.

## Context and Orientation

The Phase 3 harness is FoliaSeal’s evidence runner for preview-matrix and signed-acceptance scenarios. In this repository, “Phase 3” means opening PDFs, applying controlled signing scenarios, capturing preview and signed-output evidence, and writing summary payloads for QA and acceptance checks. The harness code is intentionally split: `src/foliaseal/presentation/qt/phase3_harness.py` is the top-level composition root, `src/foliaseal/presentation/qt/phase3_harness_workspace.py` is the narrow workspace boundary, and `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` owns one full signed-acceptance matrix sweep.

The workspace boundary already knows how to talk to either a live Qt shell or a headless `SigningDraftWorkflow`. It owns applying scenarios, reading the current request and last signing result, and capturing preview state. What it does not yet own is one earlier step in the matrix-runner lifecycle: priming the live viewer immediately after the shell is shown.

Today that priming still happens directly inside `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` through `self.compat_surface(shell).refresh_viewer()`. A “compatibility surface” here means the broad widget-export object attached to `shell.compat_surface`. It exists mainly for harnesses and tests, but it is intentionally broad and still reveals shell anatomy. This slice reduces one more dependency on that broad surface by teaching the narrower workspace boundary to own the same refresh action.

The relevant tests live in `tests/unit/test_phase3_signed_acceptance_matrix_runner.py` and `tests/unit/test_qt_phase3_harness_workspace.py`. The runner test currently asserts refresh through a fake compatibility surface. After this slice it should instead prove that a fake workspace built from the shell receives `refresh_viewer()`. The workspace-boundary tests should gain explicit proof that `QtPhase3HarnessWorkspaceAdapter.refresh_viewer()` delegates to the compatibility surface and that the headless adapter safely no-ops.

## Plan of Work

First, extend `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Add `refresh_viewer()` to `Phase3HarnessWorkspacePort`. In `QtPhase3HarnessWorkspaceAdapter`, implement it as the current `compat.refresh_viewer()` call plus the existing optional `QApplication.processEvents()` pump if needed to preserve the current priming semantics. Then call that new method from `apply_scenario(...)` instead of inlining the final refresh and event pump. In `HeadlessPhase3HarnessWorkspaceAdapter`, add a no-op implementation so both adapters satisfy the same contract without inventing fake headless viewer behavior.

Second, edit `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` so the runner depends on a workspace builder instead of `compat_surface`. Replace the `CompatSurface` type alias and dataclass field with a builder that returns `Phase3HarnessWorkspacePort` for a given shell and profile store. After showing the window, build the workspace once and call `workspace.refresh_viewer()` before `app.processEvents()`. Keep the shell object itself as the value passed into per-scenario execution so the rest of the signed-acceptance flow remains unchanged in this slice.

Third, edit `src/foliaseal/presentation/qt/phase3_harness.py` so `_build_phase3_signed_acceptance_matrix_runner()` passes `_build_preview_matrix_qt_workspace` into the runner. Remove `_shell_compat_surface` from this call path if it becomes unused, but do not touch unrelated harness builders or execution flows.

Fourth, update the focused tests. In `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`, replace the fake compatibility-surface assertion with a fake workspace builder that records `refresh_viewer()` calls. In `tests/unit/test_qt_phase3_harness_workspace.py`, add one test proving the Qt adapter’s `refresh_viewer()` delegates to `compat.refresh_viewer()` and one test proving the headless adapter’s `refresh_viewer()` is a safe no-op. Keep the tests narrow; they should not widen into scenario, capture, or session-runner behavior already covered elsewhere. This is the implementation that landed.

Finally, run focused validation. After the code is green, update `docs/ARCHITECTURE.md` and this ExecPlan so the architecture notes now say that `phase3_harness_workspace.py` also owns the viewer-priming refresh used by the signed-acceptance matrix runner. Then run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. If the review finds a mismatch, fix only that mismatch inside this slice and record the decision here before creating one narrow commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Extend the harness workspace boundary with viewer priming refresh and migrate the matrix runner off `compat_surface`.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py

2. Add focused tests for the new verb and the runner boundary change.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_phase3_signed_acceptance_matrix_runner.py

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun the focused validation commands if code or tests change during reconciliation.

5. Run the architectural compliance review, address any findings inside this slice only, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the signed-acceptance matrix runner still primes the live viewer before scenario iteration and still produces the same summary payload behavior for the same scenarios;
- `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` no longer calls `compat_surface(shell).refresh_viewer()` directly;
- `Phase3HarnessWorkspacePort` owns `refresh_viewer()` for both live-shell and headless adapters;
- the Qt adapter delegates that refresh to the compatibility surface privately, while the headless adapter safely no-ops;
- no broader scenario, capture, session-runner, or compatibility-surface cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The same signed-acceptance scenarios must still run, but one more direct dependency on the broad compatibility surface must disappear from the matrix runner.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt harness code. It is safe to retry. If the new boundary causes failures, keep `refresh_viewer()` on the workspace boundary and move only the missing event pump or shell-local refresh into the Qt adapter; do not reintroduce `compat_surface(shell)` access into the matrix runner.

If a test fails because the runner still needs a different workspace constructor signature, adapt the builder wiring in `phase3_harness.py` rather than widening the runner back into shell anatomy. If a compliance review suggests absorbing more of the signed-acceptance lifecycle, record that as a follow-up and keep this slice centered on viewer priming only.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a deeper `src/foliaseal/presentation/qt/phase3_harness_workspace.py` module that owns viewer priming refresh in addition to scenario, request, result, and capture behavior;
- a slimmer `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` that no longer knows about `compat_surface`;
- focused tests proving both the workspace refresh verb and the runner’s new workspace-builder dependency;
- focused validation output showing the runner and workspace tests still pass.

Validation evidence after implementation:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
    92 passed, 1 warning in 1.49s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the public workspace boundary should stay close to:

    class Phase3HarnessWorkspacePort(Protocol):
        def refresh_viewer(self) -> None: ...
        def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...
        def capture_state(self, command: Phase3HarnessCaptureCommand) -> dict[str, Any]: ...

`QtPhase3HarnessWorkspaceAdapter.refresh_viewer()` should call the compatibility surface privately and preserve the event-pump semantics needed by the live Qt shell path. `HeadlessPhase3HarnessWorkspaceAdapter.refresh_viewer()` should be a no-op. `Phase3SignedAcceptanceMatrixRunner` should depend on a builder shaped like:

    BuildWorkspace = Callable[[Any, SignaturePresetCatalogStore], Phase3HarnessWorkspacePort]

or the equivalent keyword-based callable already used in `phase3_harness.py`. This slice must not add new scenario, capture, or session-lifecycle methods beyond the single `refresh_viewer()` verb.

Revision note: Created on 2026-06-22 by Codex as the next `dev-loop` tracer bullet on the selected Phase 3 harness workspace-boundary hybrid. The slice intentionally removes only the remaining direct viewer-priming dependency on `compat_surface` from the signed-acceptance matrix runner.
