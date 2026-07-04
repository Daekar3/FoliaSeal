# Add A Phase 3 Harness Facade Tracer Bullet For Interactive Signing Harness Runs

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice was the interim facade tracer bullet for the interactive signing harness path. It unified the harness entrypoint behind the same `Phase3Harness` shape at the time, and the later hybrid contract collapse moved the caller-facing Phase 3 contract into `Phase3EvidenceService` while leaving `Phase3Harness` as a Qt-backed adapter/composition root.

The user-visible behavior does not change. The proof is architectural and testable: preview-matrix, signed-acceptance matrix, and interactive signing-harness callers all use one request-based facade, while the existing Qt session runner, capture assembly, and report finalization boundaries remain intact.

## Child ExecPlan Dependencies

- [x] (2026-06-27 00:00Z) The preview-matrix facade tracer bullet landed in commit `dba9a8c20`.
- [x] (2026-06-27 00:00Z) The signed-acceptance facade tracer bullet landed in commit `14bf61082`.
- [x] (2026-06-27 00:00Z) No child ExecPlans are required for this bounded tracer-bullet slice.

## Progress

- [x] (2026-06-27 00:00Z) Ran the required dev-loop explorer audit and confirmed the interactive signing harness is the next bounded hybrid seam.
- [x] (2026-06-27 00:00Z) Re-read the interactive harness entrypoint, its orchestration test, and the architecture-doc touchpoints.
- [x] (2026-06-27 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-27 00:00Z) Added the facade-delegation test for interactive signing-harness runs in `tests/unit/test_phase3_harness.py`.
- [x] (2026-06-27 00:00Z) Extended `Phase3Harness` with `run_signing_harness()` in `src/foliaseal/presentation/qt/phase3_harness.py`.
- [x] (2026-06-27 00:00Z) Converted `run_phase3_signing_harness()` into a thin compatibility shim over the facade while preserving behavior and payload shape.
- [x] (2026-06-27 00:00Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan so the completed slice is documented consistently.
- [x] (2026-07-04 00:00Z) The later hybrid contract collapse retired this interim public facade surface and moved the caller-facing contract into `Phase3EvidenceService`.

## Surprises & Discoveries

- Observation: the interactive signing harness no longer owns the whole flow inline.
  Evidence: `Phase3Harness.run_signing_harness()` fronted the interactive path for this slice, and the later hybrid collapse moved the caller-facing contract into `Phase3EvidenceService`.

## Decision Log

- Decision: keep the existing Qt session runner, capture assembler, and reporting boundary intact in this slice.
  Rationale: the goal is to unify the caller-facing seam first. Moving the deeper lifecycle into a new runner module is the next, higher-risk seam and should not be mixed into this bounded facade slice.
  Date/Author: 2026-06-27 / Codex

- Decision: reuse `Phase3HarnessRequest` for the interactive path instead of introducing a second interactive-only request type.
  Rationale: the existing request fields already covered the interactive harness inputs for this interim slice. The later hybrid collapse replaced that public request type with application-layer request dataclasses consumed by `Phase3Harness`.
  Date/Author: 2026-06-27 / Codex

## Outcomes & Retrospective

Completed.

The interactive signing-harness caller surface routed through `Phase3Harness.run_signing_harness()` for this interim slice, and the added direct facade-delegation test closed the behavioral gap without changing the capture payload or report-finalization contract. The later hybrid collapse removed the old public shim surface and made `Phase3EvidenceService` the only caller-facing Phase 3 contract.

The architecture doc now records the final ownership split, so the doc set is aligned with the current implementation rather than the earlier tracer-bullet state.

## Context and Orientation

The relevant module is `src/foliaseal/presentation/qt/phase3_harness.py`. `Phase3Harness` now owns all three caller-facing verbs:

- `Phase3Harness.run_preview_matrix(...)`
- `Phase3Harness.run_signed_acceptance_matrix(...)`
- `Phase3Harness.run_signing_harness(...)`

The interactive path is still implemented by the extracted session runner in `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`, the capture assembler in `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`, and the reporting boundary in `src/foliaseal/presentation/qt/phase3_harness_reporting.py`. `run_phase3_signing_harness(...)` now delegates into the facade instead of orchestrating that flow inline.

This slice stayed narrow. It did not move the interactive lifecycle into a new module, alter the session runner contract, change the capture payload shape, or rewrite the reporting boundary. It only promoted the caller-facing interactive path into the existing `Phase3Harness` facade and kept the old free function as a shim.

The main safety net is `tests/unit/test_phase3_harness.py`. The most important existing guardrail is `test_run_phase3_signing_harness_orchestrates_session_and_reporting`, which proves the shim still drives the same orchestration and payload assembly. This slice added one direct facade-delegation test and left that end-to-end orchestration test as the compatibility proof.

## Plan of Work

First, add a red-phase test in `tests/unit/test_phase3_harness.py` for the new facade verb. The test should patch the existing top-level helper collaborators enough to keep the flow cheap, then call `Phase3Harness.run_signing_harness(...)` and assert that the expected capture/report payload emerges. It should prove the facade owns the public caller surface, not retest every internal helper separately.

Second, extend `src/foliaseal/presentation/qt/phase3_harness.py` with `Phase3Harness.run_signing_harness(...)`. Keep the existing orchestration steps in the same module and in the same order: bindings, source existence, artifacts directory resolution, page-count load, backend diagnostics, viewer/signing workflow construction, session execution, capture payload assembly, report finalization, and acceptance-summary printing.

Third, rewrite `run_phase3_signing_harness()` so it constructs `Phase3HarnessRequest` and delegates to `Phase3Harness.run_signing_harness()`. Preserve the current function signature, return type, printed output behavior, and report-writing behavior exactly so the CLI path and existing orchestration test do not change.

Fourth, run focused validation, perform the required compliance review, and update `docs/ARCHITECTURE.md` so it no longer describes the interactive signing harness as the last caller-facing entrypoint outside the facade. `docs/SPEC.md` should remain unchanged unless an unexpected user-visible behavior drift appears.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_phase3_harness.py
    docs/ExecPlans/phase3_harness_facade_interactive_execplan.md
    docs/ARCHITECTURE.md   # only if wording needs reconciliation

Suggested order:

1. Add a failing interactive-facade test.
2. Add `Phase3Harness.run_signing_harness()`.
3. Convert `run_phase3_signing_harness()` into a facade shim.
4. Re-run focused tests and hygiene.
5. Perform the required compliance review.

Run focused validation as the slice progresses:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py -k 'signing_harness or harness_facade'
    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/phase3_harness_facade_interactive_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `Phase3Harness` exposes `run_signing_harness()` in `src/foliaseal/presentation/qt/phase3_harness.py`
- `run_phase3_signing_harness()` is a thin compatibility shim over the facade
- the interactive harness capture payload, report-writing behavior, and printed summary behavior stay unchanged
- focused interactive harness tests pass
- any architecture wording affected by the new facade surface is reconciled

Observable proof is a focused test run where the new facade-delegation test fails before the change and passes after it, while the existing orchestration test for `run_phase3_signing_harness()` remains green.

## Idempotence and Recovery

This is a behavior-preserving tracer bullet and is safe to retry. If the first pass starts moving Qt session logic, capture assembly, or report finalization into new modules, stop and split that into a later ExecPlan instead of widening this one. The facade must wrap the existing interactive path, not redesign it.

## Artifacts and Notes

Capture and keep concise:

- the focused interactive-harness facade test run
- any compliance finding about whether `docs/ARCHITECTURE.md` needed to expand the facade wording to include the interactive path

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of the slice, the public shape should look approximately like:

    @dataclass(frozen=True)
    class Phase3Harness:
        deps: Phase3HarnessDependencies

        def run_preview_matrix(self, request: Phase3HarnessRequest) -> dict[str, Any]: ...
        def run_signed_acceptance_matrix(self, request: Phase3HarnessRequest) -> dict[str, Any]: ...
        def run_signing_harness(
            self,
            request: Phase3HarnessRequest,
        ) -> Phase3HarnessCapture: ...

The request object was the common caller-facing contract for this slice. The later hybrid collapse replaced that public request type with application-layer request dataclasses consumed by `Phase3Harness`, and the free function `run_phase3_signing_harness()` is no longer treated as a stable public seam.

Revision note: Created on 2026-06-27 by Codex after the required dev-loop explorer selected the next Phase 3 harness hybrid tracer bullet: move the interactive signing-harness caller surface behind the existing `Phase3Harness` facade without widening into a new session-runner or reporting refactor.
