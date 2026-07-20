# Phase 3 harness gateway hybrid refactor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the Phase 3 harness will expose a small, explicit gateway surface for its three real use cases: interactive capture, preview matrix, and signed-acceptance matrix. A caller will still be able to run the same Phase 3 flows and observe the same JSON, checklist, and signed-output evidence, but the implementation will stop depending on a loose builder/callback mesh spread across multiple helper modules. Instead, the harness will keep a minimal public gateway while moving its internal collaboration onto typed dependency bundles and narrower ports. The result should be easier to navigate, easier to test at the boundary, and ready for another architecture pass without reopening the same seam.

The user-visible proof is behavior preservation. Running the existing focused Phase 3 harness tests should still pass, interactive harness capture should still finalize the same evidence contract fields, and both matrix flows should still emit stable summaries while the codebase surface becomes more coherent.

## Child ExecPlan Dependencies

- [x] No child ExecPlans are required. This slice should land in one pass across the full Phase 3 harness seam.

## Progress

- [x] (2026-07-07 04:16Z) Re-read the accepted hybrid recommendation: minimal explicit gateway outside, typed internal ports inside.
- [x] (2026-07-07 04:23Z) Completed the required dev-loop explorer pass for the implementation slice and captured the exact file set, invariants, and sequence.
- [x] (2026-07-07 04:29Z) Wrote this ExecPlan before implementation.
- [x] (2026-07-07 04:58Z) Introduced the typed internal dependency bundle and gateway surface in `src/foliaseal/presentation/qt/phase3_harness.py`.
- [x] (2026-07-07 05:03Z) Threaded typed ports/dependencies through the workspace adapter, session runner, preview-matrix runner, signed-acceptance matrix runner, and signed-acceptance scenario executor.
- [x] (2026-07-07 05:11Z) Preserved the existing evidence payload contract while retargeting the focused Phase 3 tests to the new seam.
- [x] (2026-07-07 05:22Z) Ran focused validation and reconciled `docs/ARCHITECTURE.md`.
- [x] (2026-07-07 05:35Z) Completed the required compliance review, architecture reconciliation, and commit flow in `23bcb0547` (`refactor: route phase 3 harness through typed gateway ports`).

## Surprises & Discoveries

- Observation: the current harness is already split into helper modules, but the public seam is still effectively a builder/callback composition root in `phase3_harness.py`.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` still owns `_build_phase3_harness_session_runner()`, `_build_phase3_harness_capture_assembler()`, `_build_phase3_preview_matrix_runner()`, `_build_phase3_signed_acceptance_matrix_runner()`, and the interactive orchestration path.

- Observation: the highest-risk parts of the seam are not public method names by themselves; they are the evidence payload fields, artifact naming, and Qt timing behaviors around viewer refresh and `processEvents()`.
  Evidence: explorer-light implementation scout on 2026-07-07 highlighted `backend_reservation_snapshot`, `signed_runs`, `captured_states`, `evidence_*` fields, `timestamping_mode`, `sign_success` timing, and artifact basename stability as critical invariants.

## Decision Log

- Decision: implement the accepted hybrid rather than any pure design variant.
  Rationale: the hybrid keeps the public surface small and explicit while avoiding a large ports-and-adapters explosion at the outer API. It matches the repo’s current maturity better than the more flexible or fully generic designs.
  Date/Author: 2026-07-07 / Codex

- Decision: keep the existing public verbs conceptually intact while replacing the internal builder/callback mesh with typed dependency bundles and narrower ports.
  Rationale: this preserves current caller semantics and test intent while deepening the module behind a smaller boundary.
  Date/Author: 2026-07-07 / Codex

- Decision: treat the evidence payload as an externalized contract for this slice.
  Rationale: changing JSON/checklist fields, artifact naming, or signed-run timing would widen the slice into evidence compatibility work instead of architecture cleanup.
  Date/Author: 2026-07-07 / Codex

## Outcomes & Retrospective

The hybrid landed as intended. `Phase3Harness` now presents explicit `capture()`, `preview_matrix()`, and `signed_acceptance_matrix()` verbs while keeping `run_*` wrappers for compatibility, and the internal wiring now passes through typed dependency bundles instead of a loose builder/callback mesh. Focused Phase 3 harness tests still pass without changing the evidence payload contract.

The most important follow-up from the compliance review was architectural documentation, not code fixes. `docs/SPEC.md` remained unchanged, the independent review found no spec regression, and the only stale contract description was in `docs/ARCHITECTURE.md`, which now reflects the typed gateway/runner split and the unchanged evidence payload boundary.

The required commit was `23bcb0547`; the former unchecked publication marker was stale rather than a remaining implementation or review task.

## Context and Orientation

This plan covers the Phase 3 harness seam in `src/foliaseal/presentation/qt/`. In this repository, “Phase 3 harness” means the set of Qt-backed and headless helpers that generate acceptance evidence for preview sweeps, signed-output sweeps, and interactive signing capture. The key files are:

`src/foliaseal/presentation/qt/phase3_harness.py` is the current public gateway and also the current composition root. It defines `Phase3Harness`, `Phase3HarnessDependencies`, interactive capture orchestration, default builders, and many lower-level helper functions. That makes it the main shallow seam.

`src/foliaseal/presentation/qt/phase3_harness_workspace.py` is the scenario-and-capture boundary for both live-shell and headless flows. It should remain the place where preview scenario mutation and workspace snapshot capture live, but it should stop depending on callback-shaped assembly from the outer gateway.

`src/foliaseal/presentation/qt/phase3_harness_session_runner.py` owns the interactive Qt lifecycle and callback cluster for one manual harness run. It currently depends on callback collaborators such as `build_qt_signing_shell`, `build_workspace`, and `default_harness_output_pdf_path`.

`src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`, `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`, and `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` own the two matrix flows and one per-scenario signed-output execution step. They are already partially extracted, but they still receive raw function collaborators rather than a typed internal seam.

`src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` and `src/foliaseal/presentation/qt/phase3_harness_reporting.py` are the least desirable places to churn in this slice. They already represent deeper boundaries around payload assembly and report finalization. Prefer to keep their emitted payload contracts stable even if their constructors or collaborator types are tightened.

The focused tests live under `tests/unit/` and are currently white-box heavy. `test_phase3_harness.py` locks in many private helper seams. `test_phase3_harness_session_runner.py`, `test_qt_phase3_harness_workspace.py`, `test_phase3_preview_matrix_runner.py`, `test_phase3_signed_acceptance_matrix_runner.py`, and `test_phase3_signed_acceptance_scenario_executor.py` exercise the current callback-driven seam. This plan should replace as much callback-shape testing as practical with boundary-oriented gateway and runner tests, but it should not widen into a complete rewrite of all harness tests.

`docs/SPEC.md` is frozen and must not change. `docs/ARCHITECTURE.md` must be updated at the end so it describes the final gateway and internal seam accurately.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness.py`. Replace the current builder-focused `Phase3HarnessDependencies` shape with a typed dependency bundle that still supports the three public verbs but stops exporting raw construction callables as the main abstraction. Keep the accepted hybrid shape: a minimal explicit gateway for `capture`, `preview_matrix`, and `signed_acceptance_matrix`, backed by typed internal dependencies and thin compatibility helpers where necessary. Preserve the existing request DTOs from the application layer and the existing `Phase3HarnessCapture` result type.

Second, thread that dependency bundle into the internal collaborators. Update `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` so it receives typed collaborators instead of the current callback cluster where practical. Update `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`, `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`, and `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` to consume typed internal dependencies instead of raw builder functions. Update `src/foliaseal/presentation/qt/phase3_harness_workspace.py` only as needed to support the new seam without weakening its current testing-adapter preference or live/headless behavior.

Third, keep `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` and `src/foliaseal/presentation/qt/phase3_harness_reporting.py` as stable as possible. If constructors or collaborator types need tightening, do that, but do not change the payload fields, checklist semantics, or summary-writing behavior unless forced by the new seam.

Fourth, update the focused tests. Start with `tests/unit/test_phase3_harness.py` because it currently locks in the old gateway shape and private builders. Then update the runner and workspace tests so they assert on the new typed seam rather than the old builder/callback mesh. Keep the evidence-oriented assertions intact: timestamps, artifact names, preview snapshots, signed-run bundles, and final report fields must still behave the same.

Finally, update `docs/ARCHITECTURE.md` to describe the new Phase 3 harness gateway and internal seam. Leave `docs/SPEC.md` unchanged. Then run the required compliance review through explorer-light and fix any resulting seam mismatches before the commit step.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Reconfirm the current harness seam before edits:

       rg -n "Phase3HarnessDependencies|_build_phase3_harness_|Phase3PreviewMatrixRunner|Phase3SignedAcceptanceMatrixRunner|Phase3HarnessSessionRunner" \
         src/foliaseal/presentation/qt/phase3_harness.py \
         src/foliaseal/presentation/qt/phase3_harness_session_runner.py \
         src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py \
         src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py \
         src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py

2. Implement the gateway and typed internal dependencies, then retarget the focused Phase 3 tests.

3. Run focused lint and tests:

       .venv/bin/python -m ruff check \
         src/foliaseal/presentation/qt/phase3_harness.py \
         src/foliaseal/presentation/qt/phase3_harness_workspace.py \
         src/foliaseal/presentation/qt/phase3_harness_session_runner.py \
         src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py \
         src/foliaseal/presentation/qt/phase3_harness_reporting.py \
         src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py \
         src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py \
         src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py \
         tests/unit/test_phase3_harness.py \
         tests/unit/test_qt_phase3_harness_workspace.py \
         tests/unit/test_phase3_harness_session_runner.py \
         tests/unit/test_phase3_harness_capture_assembler.py \
         tests/unit/test_phase3_harness_reporting.py \
         tests/unit/test_phase3_preview_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_scenario_executor.py \
         docs/ARCHITECTURE.md

       .venv/bin/python -m pytest -q \
         tests/unit/test_phase3_harness.py \
         tests/unit/test_qt_phase3_harness_workspace.py \
         tests/unit/test_phase3_harness_session_runner.py \
         tests/unit/test_phase3_harness_capture_assembler.py \
         tests/unit/test_phase3_harness_reporting.py \
         tests/unit/test_phase3_preview_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_scenario_executor.py

4. If the seam change causes fallout in adjacent Phase 3 or evidence-service paths, expand validation to:

       .venv/bin/python -m pytest -q \
         tests/unit/test_phase3_evidence_service.py \
         tests/unit/test_phase3_signed_output_snapshotter.py \
         tests/unit/test_phase3_signed_output_render_snapshotter.py

5. Run `git diff --check` before the compliance review and before the commit step.

## Validation and Acceptance

Acceptance requires all of the following.

The public Phase 3 gateway exposes the same three user-meaningful verbs after the refactor: interactive capture, preview matrix, and signed-acceptance matrix. A caller should no longer need to understand private builders or callback wiring to use the harness.

The evidence contract remains stable. Focus especially on `backend_reservation_snapshot`, `signed_runs`, `captured_states`, `evidence_contract_version`, `acceptance_tier`, `gate_verdict`, `interaction_counts`, and final signing-result fields. Artifact names and capture indices must remain stable enough that the focused tests do not need evidence-schema rewrites.

The live-shell paths still prefer `testing_adapter`, still refresh the viewer in the same order, and still preserve `sign_success`-driven signed-run capture timing. Signed-acceptance mode must still honor `timestamping_mode` and the dummy timestamper path.

The required focused validation is:

       .venv/bin/python -m pytest -q \
         tests/unit/test_phase3_harness.py \
         tests/unit/test_qt_phase3_harness_workspace.py \
         tests/unit/test_phase3_harness_session_runner.py \
         tests/unit/test_phase3_harness_capture_assembler.py \
         tests/unit/test_phase3_harness_reporting.py \
         tests/unit/test_phase3_preview_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_scenario_executor.py

and

       .venv/bin/python -m ruff check ...

The dev-loop is not complete until an explorer-light compliance review confirms that the first pass aligns with `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and the relevant docs in `docs/`.

## Idempotence and Recovery

This is a behavior-preserving architecture slice. It is safe to rerun the focused tests and lint commands repeatedly. If the refactor breaks the gateway midway, restore the three public verbs first and then re-thread the typed dependency bundle beneath them. If runner refactors start changing evidence payloads or artifact names, stop and preserve the old payload contract before continuing; changing the contract would widen the slice into evidence migration work.

If a partial edit breaks only one matrix flow, keep the other two public verbs intact and fix the affected runner in isolation. Do not delete generated artifacts or broaden the slice into new QA asset generation. Keep `docs/SPEC.md` untouched throughout.

## Artifacts and Notes

The most important artifacts for this slice will be the focused validation transcript and the compliance-review summary. Add concise excerpts here after implementation.

Expected evidence shape to preserve:

    capture.preview_snapshot
    capture.sign_request_snapshot
    capture.backend_reservation_snapshot
    capture.signed_runs
    capture.captured_states
    capture.evidence_contract_version
    capture.acceptance_tier
    capture.gate_verdict

Expected validation transcript shape after completion:

    $ .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py ...
    <all focused tests pass>

    $ .venv/bin/python -m ruff check ...
    All checks passed!

## Interfaces and Dependencies

At the end of this slice, the Phase 3 harness should follow the accepted hybrid:

The public boundary in `src/foliaseal/presentation/qt/phase3_harness.py` should remain small and explicit. It should expose three meaningful verbs for the three supported run types rather than one generic mode switch or many raw builder entrypoints.

The internal collaboration should be typed. The exact names can vary, but the code should end with a typed dependency bundle and narrower runner collaborators instead of the current raw builder/callback mesh. A reasonable end state is approximately:

    @dataclass(frozen=True)
    class Phase3HarnessGateway:
        deps: Phase3HarnessDeps

        def capture(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture: ...
        def preview_matrix(self, request: Phase3MatrixRequest) -> dict[str, Any]: ...
        def signed_acceptance_matrix(self, request: Phase3MatrixRequest) -> dict[str, Any]: ...

    @dataclass(frozen=True)
    class Phase3HarnessDeps:
        workspace: ...
        session_runner: ...
        capture_assembler: ...
        reporting: ...
        preview_matrix_runner: ...
        signed_acceptance_runner: ...

The key constraints are more important than the exact spelling:

- public callers should see a minimal explicit gateway;
- internal modules should depend on typed collaborators, not raw function meshes;
- Qt-specific behavior should remain behind the session/workspace side of the seam;
- payload and evidence semantics should remain unchanged.

Revision note: Created on 2026-07-07 by Codex for the one-pass dev-loop implementation of the accepted Phase 3 harness gateway hybrid refactor.

Revision note: 2026-07-19 / Codex
Reconciled the stale compliance-and-commit checkbox with the already-landed `23bcb0547` commit and its documented architecture review.
