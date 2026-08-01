# Add A Phase 3 Harness Facade Tracer Bullet For Preview Matrix Runs

> **Retired / superseded (2026-08-01):** This tracer-bullet facade was later removed. Preview
> callers use the typed application orchestrator/session, while `Phase3Harness.preview_matrix()`
> remains only the Qt execution adapter entrypoint.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness will expose the first public tracer bullet of the proposed deep-module facade: a `Phase3Harness` object with a small request dataclass and a `run_preview_matrix()` verb. The current free function `run_phase3_preview_matrix()` will remain available, but it will become a thin compatibility shim over the new facade instead of being the primary orchestration surface.

The user-visible behavior does not change. The proof is architectural: current callers still get the same summary payload, but tests can start targeting one explicit harness facade instead of a pile of top-level free functions and private builders.

## Child ExecPlan Dependencies

- [x] (2026-06-27 00:00Z) No child ExecPlans are required for this bounded tracer-bullet slice.

## Progress

- [x] (2026-06-27 00:00Z) Re-read the current Phase 3 harness entrypoints, runners, workspace adapters, evidence wrapper, and current tests around preview-matrix delegation.
- [x] (2026-06-27 00:00Z) Used the required `explorer-light` dev-loop audit to choose the first hybrid slice: add the facade only for preview-matrix runs and keep existing free-function callers as shims.
- [x] (2026-06-27 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-27 00:00Z) Added a red-phase facade-delegation test for the new request/dependency bundle in `tests/unit/test_phase3_harness.py`, observed the expected import failure before implementation, and kept the test as the new regression check.
- [x] (2026-06-27 00:00Z) Implemented `Phase3HarnessRequest`, `Phase3HarnessDependencies`, and `Phase3Harness.run_preview_matrix()` in `src/foliaseal/presentation/qt/phase3_harness.py`.
- [x] (2026-06-27 00:00Z) Converted `run_phase3_preview_matrix()` into a thin compatibility shim over the facade while preserving current behavior and payload shape.
- [x] (2026-06-27 00:00Z) Ran focused validation, completed the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan, and recorded the result here.
- [x] (2026-06-27 00:00Z) Reconciled `docs/ARCHITECTURE.md` for the new caller-facing facade seam and prepared the slice for the required commit step in the larger dev-loop.

## Surprises & Discoveries

- Observation: the safest tracer bullet is the preview-matrix path, not the interactive harness path.
  Evidence: the preview-matrix free function in `phase3_harness.py` already delegates almost entirely to `Phase3PreviewMatrixRunner`, while the interactive harness path still bundles Qt app/window lifecycle, callback capture, report writing, and signed-run evidence assembly.

- Observation: the only documentation drift introduced by the slice was at the caller-facing surface, not the workflow contract.
  Evidence: `docs/SPEC.md` did not describe the internal harness entrypoint shape, but `docs/ARCHITECTURE.md` still described `phase3_harness.py` only as top-level entrypoints/composition helpers and needed explicit mention of `Phase3HarnessRequest` plus `Phase3Harness.run_preview_matrix()`.

## Decision Log

- Decision: limit the first facade slice to `run_preview_matrix()`.
  Rationale: this creates the new public shape with the least blast radius and avoids dragging the brittle Qt session/workspace seams into the first commit.
  Date/Author: 2026-06-27 / Codex

- Decision: keep `run_phase3_preview_matrix()` as a compatibility wrapper in this slice.
  Rationale: existing callers and tests already target that function. The facade should deepen the seam without forcing a wide migration in the tracer bullet.
  Date/Author: 2026-06-27 / Codex

## Outcomes & Retrospective

The slice landed as planned. `phase3_harness.py` now exposes a small `Phase3Harness` facade with a request object and injectable preview-matrix runner builder, while `run_phase3_preview_matrix()` remains a compatibility wrapper over the new facade. The runner internals, signed-acceptance path, session runner, and workspace adapters were left unchanged.

Focused validation stayed green after the refactor:

- `tests/unit/test_phase3_harness.py -k 'preview_matrix or harness_facade'`
- `tests/unit/test_phase3_preview_matrix_runner.py`
- `ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py`
- `git diff --check`

Compliance review result:

- `docs/SPEC.md`: no change needed; this slice did not alter user-visible behavior or the governing workflow contract.
- `docs/ARCHITECTURE.md`: updated to reflect the new caller-facing facade tracer bullet and preserve an accurate map of the remaining Phase 3 harness split.
- This ExecPlan: reconciled with the completed work and validation evidence.

## Context and Orientation

The relevant module is `src/foliaseal/presentation/qt/phase3_harness.py`. Today it still acts as the composition root and user-facing surface for all three Phase 3 harness modes:

- `run_phase3_signing_harness(...)`
- `run_phase3_preview_matrix(...)`
- `run_phase3_signed_acceptance_matrix(...)`

Those functions are thin in different ways, but the preview-matrix path is the cleanest tracer bullet. It already builds one specialized runner through `_build_phase3_preview_matrix_runner()` and then delegates the real work to `Phase3PreviewMatrixRunner.run(...)` in `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`.

The broader hybrid proposal is to replace the current free-function sprawl with a deep module that has:

- a common caller-facing harness object
- a small request dataclass
- a dependency bundle for injectable collaborators
- mode-specific verbs instead of generic untyped helper calls

This slice must not widen into the interactive Qt session runner in `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`, the workspace adapters in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, or the signed-acceptance orchestration in `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` and `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`.

The focused safety net is in `tests/unit/test_phase3_harness.py` and `tests/unit/test_phase3_preview_matrix_runner.py`. The first should prove the facade delegates correctly and preserves the compatibility wrapper behavior. The second remains the boundary test for the underlying runner implementation.

## Plan of Work

First, add a red-phase test in `tests/unit/test_phase3_harness.py` that constructs a facade dependency bundle with a fake preview-matrix runner and asserts that `Phase3Harness.run_preview_matrix()` passes the right request fields through. This should be a behavior test of the new facade, not a test of private builder names.

Second, add the new types to `src/foliaseal/presentation/qt/phase3_harness.py`:

- `Phase3HarnessRequest`
- `Phase3HarnessDependencies`
- `Phase3Harness`

The dependency bundle should have a `default()` constructor that wires the existing preview-matrix runner builder into the facade without changing the runner internals. The facade should expose only `run_preview_matrix()` in this tracer bullet unless adding placeholder verbs is materially cleaner and still low-risk.

Third, rewrite `run_phase3_preview_matrix()` so it constructs the facade and delegates to `Phase3Harness.run_preview_matrix()`. Preserve the current function signature and returned summary shape exactly so callers do not change in this slice.

Fourth, run focused tests, perform the required compliance review, and update documentation only if the architecture doc needs to acknowledge the new facade as the caller-facing harness surface. If the architecture doc can already describe the code accurately without change, leave it alone and update only this ExecPlan.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_phase3_harness.py
    docs/ExecPlans/phase3_harness_facade_preview_matrix_execplan.md
    docs/ARCHITECTURE.md   # only if wording needs reconciliation

Suggested order:

1. Add a failing facade-delegation test.
2. Add the request/dependencies/facade types.
3. Convert `run_phase3_preview_matrix()` into a facade shim.
4. Re-run focused tests and hygiene.
5. Perform the required compliance review.

Run focused validation as the slice progresses:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py -k 'preview_matrix'
    .venv/bin/python -m pytest -q tests/unit/test_phase3_preview_matrix_runner.py
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/phase3_harness_facade_preview_matrix_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- a new `Phase3Harness` facade exists in `phase3_harness.py`
- the facade exposes a request-based `run_preview_matrix()` path
- `run_phase3_preview_matrix()` is a thin compatibility shim over that facade
- the preview-matrix summary shape and caller-visible behavior stay unchanged
- focused harness and preview-matrix runner tests pass
- any architecture wording affected by the new facade is reconciled

Observable proof is a focused test run where the new facade test fails before the change and passes after it, while the existing `run_phase3_preview_matrix()` delegation coverage and preview-matrix runner boundary tests remain green.

## Idempotence and Recovery

This is a behavior-preserving tracer bullet and is safe to retry. If the first pass creates a second orchestration path instead of a thin facade over the existing runner, simplify it before continuing; do not keep duplicated preview-matrix orchestration in both the facade and the old free function. If the change starts dragging in session runner or workspace adapter semantics, stop and split that into a later ExecPlan instead of widening this slice.

## Artifacts and Notes

Capture and keep concise:

- the focused preview-matrix facade test run
- any compliance finding about whether `docs/ARCHITECTURE.md` needs to mention the new facade

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of the slice, the public shape should look approximately like:

    @dataclass(frozen=True)
    class Phase3HarnessRequest:
        pdf_path: str
        certificate_path: str = "demo-cert.p12"
        passphrase: str = "demo-passphrase"
        scenario_manifest_path: str | None = None
        artifacts_dir: str | None = None

    @dataclass(frozen=True)
    class Phase3HarnessDependencies:
        build_preview_matrix_runner: Callable[[], Phase3PreviewMatrixRunner]

        @classmethod
        def default(cls) -> "Phase3HarnessDependencies": ...

    @dataclass(frozen=True)
    class Phase3Harness:
        deps: Phase3HarnessDependencies

        def run_preview_matrix(self, request: Phase3HarnessRequest) -> dict[str, Any]: ...

The exact field set may grow slightly if needed to preserve the current preview-matrix call contract, but the contract should stay simple and request-based. The old top-level function remains as a compatibility wrapper in this tracer bullet.

Revision note: Created on 2026-06-27 by Codex after the required dev-loop explorer selected the first Phase 3 harness hybrid tracer bullet: a preview-matrix-only facade over the existing runner path.
