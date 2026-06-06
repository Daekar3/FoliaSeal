# Extract Phase 3 signed-acceptance matrix runner

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, `foliaseal phase3-signed-acceptance-matrix` should still produce the same `summary.json` artifact, the same scenario results, and the same acceptance-expectation fields, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the signed-acceptance matrix loop inline. The user-visible proof stays the same: the command still loads one manifest, drives one Qt-backed signing shell across the manifest scenarios, writes the same summary payload, and returns the same summary structure. The improvement is architectural: contributors will be able to test the signed-acceptance matrix runtime seam at a dedicated boundary instead of patching more module-private harness helpers.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_harness_capture_assembler_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_harness_session_runner_helper_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_preview_matrix_runner_execplan.md` is complete.

## Progress

- [x] (2026-06-06 00:20Z) Re-read the live signed-acceptance matrix path, the preview-matrix runner, the Phase 3 evidence service, and the focused tests to confirm the narrowest remaining Phase 3 runtime seam.
- [x] (2026-06-06 01:05Z) Extracted `Phase3SignedAcceptanceMatrixRunner` into `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` and reduced `run_phase3_signed_acceptance_matrix()` to a thin delegating wrapper in `src/foliaseal/presentation/qt/phase3_harness.py`.
- [x] (2026-06-06 01:18Z) Added `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`, moved the loop-level signed-matrix proofs there, and kept only a thin delegation check in `tests/unit/test_phase3_harness.py`.
- [x] (2026-06-06 01:24Z) Ran the focused signed-acceptance validation, Ruff, and `git diff --check`.
- [x] (2026-06-06 01:34Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and committed the slice.

## Surprises & Discoveries

- Observation: the signed-acceptance matrix path is now the last large inline Phase 3 runtime loop in `phase3_harness.py`.
  Evidence: `run_phase3_signed_acceptance_matrix()` still owns manifest loading, `timestamping_mode` validation, Qt shell/bootstrap lifecycle, scenario iteration, exception mapping, summary shaping, acceptance-expectation evaluation, and `summary.json` writing in one function.
- Observation: the existing signed-acceptance summary contract was broad enough that the runner extraction had to keep acceptance-expectation evaluation, timestamping-mode propagation, and summary-file writing together instead of splitting only the scenario loop.
  Evidence: `Phase3EvidenceService.run_signed_acceptance_matrix()` and `tests/unit/test_qa_signed_acceptance_evidence.py` continue to rely on the returned summary counters, `acceptance_expectations` fields, and persisted `summary.json` shape.
- Observation: the harness-level test no longer needed to own loop behavior once the runner existed; a thin delegation check was sufficient at the public entrypoint.
  Evidence: focused loop/error/summary assertions moved into `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`, while `tests/unit/test_phase3_harness.py` kept only the wrapper-level delegation proof for `run_phase3_signed_acceptance_matrix()`.

## Decision Log

- Decision: Extract the signed-acceptance matrix runner before any deeper per-scenario signing rewrite.
  Rationale: this is the narrowest remaining runtime seam with the largest payoff. The caller-facing service verb is already explicit, while `_execute_signed_acceptance_scenario()` is a likely later seam and would widen this slice unnecessarily.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` now owns the signed-acceptance matrix-level lifecycle: manifest loading, `timestamping_mode` validation, fresh-shell scenario iteration, scenario-level exception mapping, summary shaping, acceptance-expectation evaluation, and `summary.json` writing. `src/foliaseal/presentation/qt/phase3_harness.py` keeps `run_phase3_signed_acceptance_matrix()` as a thin delegating wrapper and remains the composition root that wires the real collaborators into the runner.

The focused test shape is narrower now. `tests/unit/test_phase3_signed_acceptance_matrix_runner.py` owns the loop-level runtime proofs, including exception mapping, acceptance fields, and summary writing, while `tests/unit/test_phase3_harness.py` keeps only a thin delegation check for the public harness entrypoint. The caller-facing service verb in `src/foliaseal/application/phase3_evidence_service.py` remained stable throughout the extraction.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_acceptance_matrix or signed_acceptance_matrix_runner or run_signed_acceptance_evidence'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_qa_signed_acceptance_evidence.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has three narrower boundaries already in place. `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` owns interactive capture-payload shaping, `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` owns the interactive Qt callback cluster, and `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` owns the headless preview-only scenario loop.

The remaining large inline runtime seam is `run_phase3_signed_acceptance_matrix()` in `src/foliaseal/presentation/qt/phase3_harness.py`. That function does more than one job. It validates the source PDF and manifest, interprets `timestamping_mode`, builds a signing executor, creates a Qt shell, loops through signed-acceptance scenarios, maps scenario exceptions into result rows, computes summary counters, evaluates manifest acceptance expectations, and writes `summary.json`.

In this plan, a “signed-acceptance matrix runner” means the code that owns one complete signed-output scenario sweep and returns the summary dictionary currently returned by `run_phase3_signed_acceptance_matrix()`. The top-level harness function should remain stable for callers such as `src/foliaseal/application/phase3_evidence_service.py`.

This slice must keep the current summary schema exactly the same. In particular, the following fields must remain stable because the evidence service and its tests rely on them: `timestamping_mode`, `acceptance_expectations`, `acceptance_expectations_passed`, `acceptance_expectation_errors`, the various failure counters from `_signed_matrix_diagnostic_summary(...)`, and the scenario-level `results`.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py`. That module should own the full signed-acceptance matrix loop and summary writing for one run. Keep the low-level scenario execution function, acceptance-expectation evaluator, manifest loader, Qt bindings loader, and JSON normalization helper injectable so tests can fake them without patching module-private helpers in `phase3_harness.py`.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `run_phase3_signed_acceptance_matrix()` delegates to the new helper instead of keeping the full loop inline. The harness file should remain the place that wires the real repository callables into that helper and keeps the public function signature stable.

Add a focused test module, `tests/unit/test_phase3_signed_acceptance_matrix_runner.py`, that exercises the extracted runner directly. Those tests should verify at least: loop-level success counting, exception mapping through `_preview_matrix_error_result(...)`, `timestamping_mode` validation and propagation, acceptance-expectation fields in the returned summary, and `summary.json` writing. Simplify the old loop-level harness proofs in `tests/unit/test_phase3_harness.py` so the broad harness file only proves the public wrapper still delegates correctly.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new signed-acceptance matrix runner explicitly and explains that `phase3_harness.py` now delegates that matrix loop. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` and move the signed-acceptance matrix loop ownership there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new runner.
3. Add `tests/unit/test_phase3_signed_acceptance_matrix_runner.py` and trim the old loop-level harness proofs from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_acceptance_matrix or signed_acceptance_matrix_runner or run_signed_acceptance_evidence'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_qa_signed_acceptance_evidence.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. `run_phase3_signed_acceptance_matrix()` must still return the same summary structure and write the same `summary.json` payload, while the signed-acceptance runtime loop becomes directly testable at the new helper module.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` owns manifest loading, `timestamping_mode` validation, Qt shell/bootstrap lifecycle, scenario iteration, exception-to-result mapping, summary shaping, acceptance-expectation evaluation, and summary writing for signed-acceptance runs;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates that work instead of keeping the full loop inline;
- the new focused signed-acceptance runner tests pass without broad monkeypatching of unrelated harness helpers;
- the public `run_phase3_signed_acceptance_matrix()` entrypoint remains stable for callers such as `Phase3EvidenceService`;
- `tests/unit/test_qa_signed_acceptance_evidence.py` still passes against the unchanged summary contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the new helper module import or delegation shape is wrong, restore `run_phase3_signed_acceptance_matrix()` first, rerun the focused tests, and then retry the extraction. Do not mix evidence-service, signed-evidence wrapper, or per-scenario signing-logic rewrites into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is behavior change in the internal architecture only. Documentation/status updates may follow if required by the compliance review. Do not mix unrelated preview-matrix, interactive-session, or signing-shell changes into this slice.

## Interfaces and Dependencies

The extracted helper module should end with stable names for:

- a dedicated signed-acceptance matrix runner boundary that accepts:
  - `pdf_path`,
  - `certificate_path`,
  - `passphrase`,
  - `scenario_manifest_path`,
  - `artifacts_dir`,
  - injected Qt bindings loader,
  - injected page-count loader,
  - injected manifest loader,
  - injected signing-executor builder,
  - injected shell builder,
  - injected scenario executor,
  - injected error-result builder,
  - injected diagnostic-summary builder,
  - injected acceptance-expectation evaluator,
  - injected JSON-normalization helper;
- or an equivalent typed helper object encapsulating the same collaborators.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the place that wires the real repository callables into that helper. `src/foliaseal/application/phase3_evidence_service.py` and `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` are callers and contract checks, not implementation targets, for this slice.

Revision note: Created on 2026-06-06 by Codex after the preview-matrix slice exposed the signed-acceptance matrix loop as the narrowest remaining runtime seam in the Phase 3 hybrid.
