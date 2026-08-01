# Add A Phase 3 Harness Facade Tracer Bullet For Signed-Acceptance Matrix Runs

> **Retired / superseded (2026-08-01):** This interim facade tracer bullet is historical. Signed
> acceptance now enters through the typed application orchestrator/session; `Phase3Harness` keeps
> only the Qt adapter verb and no `run_*` compatibility alias.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice was the interim signed-acceptance facade tracer bullet. It extended the `Phase3Harness` shape for the matrix runs at the time, and the later hybrid contract collapse moved the caller-facing Phase 3 contract into `Phase3EvidenceService` while leaving `Phase3Harness` as a Qt-backed adapter/composition root.

The user-visible behavior does not change. The gain is architectural and observable through tests: the same `Phase3HarnessRequest` request object and dependency bundle will drive both matrix-style harness flows, while the deeper signed-acceptance runner and executor internals stay untouched.

## Child ExecPlan Dependencies

- [x] (2026-06-27 00:00Z) The preview-matrix facade tracer bullet landed in commit `dba9a8c20`, so this follow-on seam can build on the existing `Phase3Harness`, `Phase3HarnessRequest`, and `Phase3HarnessDependencies` shape.
- [x] (2026-06-27 00:00Z) No child ExecPlans are required for this bounded tracer-bullet slice.

## Progress

- [x] (2026-06-27 00:00Z) Ran the required dev-loop explorer audit to select the next hybrid seam and confirmed the signed-acceptance matrix path is the safest continuation.
- [x] (2026-06-27 00:00Z) Re-read the current facade, signed-acceptance entrypoint, runner tests, and architecture doc touchpoints.
- [x] (2026-06-27 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-27 00:00Z) Added the signed-acceptance facade-delegation coverage in `tests/unit/test_phase3_harness.py`.
- [x] (2026-06-27 00:00Z) Extended `Phase3HarnessDependencies` and `Phase3Harness` with the signed-acceptance runner path in `src/foliaseal/presentation/qt/phase3_harness.py`.
- [x] (2026-06-27 00:00Z) Converted `run_phase3_signed_acceptance_matrix()` into a thin compatibility shim over the facade while preserving current behavior and payload shape.
- [x] (2026-06-27 00:00Z) Completed focused validation, the required compliance review, and the doc reconciliation for `docs/ARCHITECTURE.md` and this ExecPlan.
- [x] (2026-06-27 00:00Z) Reconciled docs and prepared the slice for the required commit step in the larger dev-loop.
- [x] (2026-07-04 00:00Z) The later hybrid contract collapse retired this interim public facade surface and moved the caller-facing contract into `Phase3EvidenceService`.

## Surprises & Discoveries

- Observation: the signed-acceptance matrix path is the next safest seam because its deeper lifecycle already sits behind `Phase3SignedAcceptanceMatrixRunner`.
  Evidence: `run_phase3_signed_acceptance_matrix()` in `src/foliaseal/presentation/qt/phase3_harness.py` already delegated almost entirely to `_build_phase3_signed_acceptance_matrix_runner().run(...)`, while the later hybrid collapse moved the caller-facing contract into `Phase3EvidenceService`.

## Decision Log

- Decision: extend the existing `Phase3HarnessRequest` object instead of creating a second signed-acceptance-specific request type.
  Rationale: the current signed-acceptance free function used the same caller inputs as the preview-matrix path, so reusing the existing request object kept the interim facade small and reinforced the common-caller hybrid shape. The later hybrid collapse replaced that public request type with application-layer request dataclasses consumed by `Phase3Harness`.
  Date/Author: 2026-06-27 / Codex

- Decision: keep `run_phase3_signed_acceptance_matrix()` as a compatibility wrapper in this slice.
  Rationale: existing callers and tests already target that function. This slice should deepen the public seam without widening migration scope or changing runner internals.
  Date/Author: 2026-06-27 / Codex

## Outcomes & Retrospective

The signed-acceptance matrix caller surface routed through `Phase3Harness` for this interim slice, and `run_phase3_signed_acceptance_matrix()` remained as a compatibility shim. The later hybrid collapse removed that shim from the public contract and made `Phase3EvidenceService` the only caller-facing Phase 3 surface.

The architecture document now describes the final ownership split explicitly.

## Context and Orientation

The relevant module is `src/foliaseal/presentation/qt/phase3_harness.py`. It now exposes three top-level harness entrypoints and one common facade:

- `run_phase3_signing_harness(...)`
- `run_phase3_preview_matrix(...)`
- `run_phase3_signed_acceptance_matrix(...)`
- `Phase3Harness.run_preview_matrix(...)`
- `Phase3Harness.run_signed_acceptance_matrix(...)`

The preview-matrix path already uses the new facade. The signed-acceptance path now enters through `Phase3Harness.run_signed_acceptance_matrix()`, while the legacy free function remains a compatibility shim that delegates into the same runner path. That runner lives in `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` and owns matrix-level lifecycle, per-scenario iteration, and summary shaping. The per-scenario execution path lives deeper in `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`.

This slice stayed narrow. It did not change the signed-acceptance runner internals, the scenario executor, the workspace adapter, the session runner, or the interactive signing harness path. It moved one more caller-facing matrix verb behind the `Phase3Harness` facade and kept the old free function as a shim.

The safety net is in `tests/unit/test_phase3_harness.py`, `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`, and `tests/unit/test_phase3_signed_acceptance_scenario_executor.py`. The harness test file should verify the caller-facing facade behavior and the compatibility wrapper behavior. The runner and executor tests remain the boundary proof that the deeper implementation still behaves the same.

## Plan of Work

First, add a red-phase test in `tests/unit/test_phase3_harness.py` for the new facade verb. Follow the existing preview-matrix pattern: inject a fake signed-acceptance runner through the dependency bundle, call `Phase3Harness.run_signed_acceptance_matrix(...)`, and assert that the exact request fields reach the fake runner unchanged. Add a second test proving that the default dependency bundle uses `_build_phase3_signed_acceptance_matrix_runner()`.

Second, extend `src/foliaseal/presentation/qt/phase3_harness.py`. Add a callable type alias for the signed-acceptance runner builder if that keeps the dependency typing explicit. Extend `Phase3HarnessDependencies` with `build_signed_acceptance_matrix_runner`, update `default()` to wire the real builder, and add `Phase3Harness.run_signed_acceptance_matrix(...)` that validates the required request fields and delegates to the runner.

Third, rewrite `run_phase3_signed_acceptance_matrix()` so it constructs `Phase3HarnessRequest` and delegates to `Phase3Harness.run_signed_acceptance_matrix()`. Preserve the current function signature and returned summary shape exactly so callers and tests do not need wider updates in this slice.

Fourth, run focused validation, perform the required compliance review, and update `docs/ARCHITECTURE.md` only if the architecture document still describes the facade as preview-matrix-only. `docs/SPEC.md` should stay unchanged unless an unexpected product-level requirement conflict appears.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_phase3_harness.py
    docs/ExecPlans/phase3_harness_facade_signed_acceptance_execplan.md
    docs/ARCHITECTURE.md   # only if wording needs reconciliation

Suggested order:

1. Add a failing signed-acceptance facade test.
2. Extend the dependency bundle and add `Phase3Harness.run_signed_acceptance_matrix()`.
3. Convert `run_phase3_signed_acceptance_matrix()` into a facade shim.
4. Re-run focused tests and hygiene.
5. Perform the required compliance review.

Run focused validation as the slice progresses:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py -k 'preview_matrix or signed_acceptance or harness_facade'
    .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py
    .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_scenario_executor.py
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/phase3_harness_facade_signed_acceptance_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `Phase3Harness` exposes `run_signed_acceptance_matrix()` in `src/foliaseal/presentation/qt/phase3_harness.py`
- `Phase3HarnessDependencies.default()` wires the signed-acceptance runner builder
- `run_phase3_signed_acceptance_matrix()` is a thin compatibility shim over the facade
- the signed-acceptance summary shape and caller-visible behavior stay unchanged
- focused harness, signed-acceptance runner, and signed-acceptance executor tests pass
- any architecture wording affected by the new facade surface is reconciled

Observable proof is a focused test run where the new facade test fails before the change and passes after it, while the existing `run_phase3_signed_acceptance_matrix()` delegation coverage and the deeper runner/executor suites remain green.

## Idempotence and Recovery

This is a behavior-preserving tracer bullet and is safe to retry. If the first pass starts duplicating signed-acceptance orchestration in both the facade and the compatibility wrapper, simplify it before continuing; the facade must delegate to the existing runner path rather than recreate matrix logic. If the slice starts pulling in interactive harness/session runner behavior, stop and split that wider seam into a later ExecPlan instead of widening this one.

## Artifacts and Notes

Capture and keep concise:

- the focused signed-acceptance facade test run
- any compliance finding about whether `docs/ARCHITECTURE.md` needed to expand the facade wording beyond preview-matrix-only

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of the slice, the public shape should look approximately like:

    BuildPhase3SignedAcceptanceMatrixRunner = Callable[[], Phase3SignedAcceptanceMatrixRunner]

    @dataclass(frozen=True)
    class Phase3HarnessDependencies:
        build_preview_matrix_runner: BuildPhase3PreviewMatrixRunner
        build_signed_acceptance_matrix_runner: BuildPhase3SignedAcceptanceMatrixRunner

        @classmethod
        def default(cls) -> "Phase3HarnessDependencies": ...

    @dataclass(frozen=True)
    class Phase3Harness:
        deps: Phase3HarnessDependencies

        def run_preview_matrix(self, request: Phase3HarnessRequest) -> dict[str, Any]: ...
        def run_signed_acceptance_matrix(
            self,
            request: Phase3HarnessRequest,
        ) -> dict[str, Any]: ...

The exact internal type alias spelling may vary slightly, but the end result for this slice preserved one common facade object and one common request object for both matrix-style harness flows. The later hybrid collapse replaced that public request object with application-layer request dataclasses consumed by `Phase3Harness`.

Revision note: Created on 2026-06-27 by Codex after the required dev-loop explorer selected the next Phase 3 harness hybrid tracer bullet: move the signed-acceptance matrix caller surface behind the existing `Phase3Harness` facade without widening into the interactive Qt harness path.
