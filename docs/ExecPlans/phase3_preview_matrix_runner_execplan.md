# Extract Phase 3 preview matrix runner

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, `foliaseal phase3-preview-matrix` should still produce the same `summary.json` artifact and scenario results, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the preview-matrix loop, error handling, and summary writing inline. The user-visible proof stays the same: the command still loads one manifest, executes one headless scenario runner per case, writes the same summary payload, and returns the same summary structure. The improvement is architectural: contributors will be able to test the preview-matrix runtime seam at a dedicated boundary instead of patching more module-private harness helpers.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_harness_capture_assembler_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_harness_session_runner_helper_execplan.md` is complete.

## Progress

- [x] (2026-06-05 22:44Z) Re-read the live preview-matrix path in `src/foliaseal/presentation/qt/phase3_harness.py`, the Phase 3 evidence service, and the focused tests to confirm the narrowest remaining matrix-side seam.
- [x] (2026-06-05 22:52Z) Extracted `Phase3PreviewMatrixRunner` into `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` and reduced `run_phase3_preview_matrix()` to a thin delegating wrapper.
- [x] (2026-06-05 22:57Z) Added `tests/unit/test_phase3_preview_matrix_runner.py`, replaced the old loop-level harness proofs with a thin wrapper test, and reran the focused preview-matrix validation plus Ruff and `git diff --check`.
- [x] (2026-06-05 23:04Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and confirmed the slice stays documentation-complete without `docs/SPEC.md` changes.

## Surprises & Discoveries

- Observation: `run_phase3_preview_matrix()` is now the narrowest remaining Phase 3 runtime seam because it still owns manifest loading, scenario iteration, scenario-level exception mapping, summary shaping, and JSON artifact writing in one function.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` around `run_phase3_preview_matrix()`.

- Observation: The public harness wrapper could stay fully stable because the extracted runner boundary only needed the existing helper family injected into it.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py::run_phase3_preview_matrix()` still exposes the same keyword-only interface and now just delegates through `_build_phase3_preview_matrix_runner()`.

- Observation: The previous preview-matrix tests in `tests/unit/test_phase3_harness.py` were testing loop ownership more than the public entrypoint.
  Evidence: They monkeypatched `_execute_headless_preview_matrix_scenario()` directly and never needed the rest of the harness module; after extraction, that coverage moved cleanly into `tests/unit/test_phase3_preview_matrix_runner.py`.

## Decision Log

- Decision: Extract the preview-matrix runner before the signed-acceptance matrix path.
  Rationale: It is the smaller seam. It stays headless, avoids the larger signed-output workflow, and deepens the same Phase 3 `3+4` hybrid without widening into acceptance-evidence orchestration.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

This slice is complete. The headless preview-matrix loop now lives in `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`, while `src/foliaseal/presentation/qt/phase3_harness.py` remains the top-level public entrypoint and composition root for the real manifest loader, scenario executor, error mapping, and JSON normalization helpers.

The result matches the purpose of the slice: users still run the same preview-matrix command and get the same summary payload and `summary.json` artifact, but contributors now have a dedicated preview-matrix runner boundary and a focused test file for it.

The main remaining Phase 3 runtime pressure is no longer the preview-only loop. The next good seam is the signed-acceptance matrix path, which still owns the larger Qt-backed matrix lifecycle and output-summary assembly inline.

## Context and Orientation

The Phase 3 harness in `src/foliaseal/presentation/qt/phase3_harness.py` now has separate boundaries for interactive session running and capture assembly, but the preview-matrix path still lives inline. `run_phase3_preview_matrix()` currently validates the source PDF, loads the manifest, loops over scenarios, catches scenario exceptions, computes summary counters, and writes `summary.json` itself.

That path is already conceptually narrower than signed acceptance because it is headless and preview-only. It does not need the interactive Qt shell or the signed-output validation path. That makes it the right tracer-bullet follow-on seam: one helper can own the headless preview-matrix runtime while the top-level harness entrypoint remains stable for the CLI and `Phase3EvidenceService`.

This slice must not redesign signed-acceptance workflows, report rendering, or the public Phase 3 service surface. It should only move the preview-matrix runtime loop and summary writing behind a dedicated helper boundary.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py`. That module should own the preview-matrix loop and summary-writing behavior for one run. Keep scenario execution and other harness-specific details injectable so tests can fake them without patching module-private helpers in `phase3_harness.py`.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `run_phase3_preview_matrix()` delegates to the new helper instead of keeping the full loop inline. The harness file should remain the place that wires the real manifest loader, scenario executor, diagnostic summarizer, and JSON normalization into the helper.

Add a focused test module, `tests/unit/test_phase3_preview_matrix_runner.py`, that exercises the extracted runner directly. Remove or simplify the current preview-matrix loop tests in `tests/unit/test_phase3_harness.py` so the broad harness test file stops owning that boundary coverage. Keep a thin wrapper proof in the harness tests only if needed to show the public entrypoint still delegates correctly.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new preview-matrix runner helper explicitly and explains that `phase3_harness.py` now delegates the preview-only matrix loop to it. Keep `docs/SPEC.md` unchanged unless the implementation reveals a documented behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` and move the preview-matrix loop ownership there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new runner.
3. Add `tests/unit/test_phase3_preview_matrix_runner.py` and trim the old preview-matrix loop proofs from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_preview_matrix or preview_matrix_runner'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_preview_matrix_runner.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. `run_phase3_preview_matrix()` must still return the same summary structure and write the same `summary.json` payload, while the preview-matrix runtime loop becomes directly testable at the new helper module.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` owns manifest loading, scenario iteration, exception-to-result mapping, counter shaping, and summary writing for preview-only runs;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates that work instead of keeping the full preview-matrix loop inline;
- the new focused preview-matrix runner tests pass without broad monkeypatching of unrelated harness helpers;
- the public `run_phase3_preview_matrix()` entrypoint remains stable for callers such as `Phase3EvidenceService`;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the new helper module import or delegation shape is wrong, restore `run_phase3_preview_matrix()` first, rerun the focused tests, and then retry the extraction. Do not mix signed-acceptance matrix or evidence-service changes into this slice.

## Artifacts and Notes

Focused validation transcript after implementation:

    $ .venv/bin/python -m pytest tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_preview_matrix or preview_matrix_runner'
    ======================= 4 passed, 89 deselected in 0.42s =======================

    $ .venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_preview_matrix_runner.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

The extracted helper module should end with stable names for:

- a dedicated preview-matrix runner boundary that accepts:
  - `pdf_path`,
  - `certificate_path`,
  - `passphrase`,
  - `scenario_manifest_path`,
  - `artifacts_dir`,
  - injected manifest loader,
  - injected headless scenario executor,
  - injected error-result builder,
  - injected diagnostic-summary builder,
  - injected JSON-normalization helper;
- or an equivalent typed helper object encapsulating the same collaborators.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the place that wires the real repository callables into that helper. `src/foliaseal/application/phase3_evidence_service.py` is a caller, not an implementation target, for this slice.

Revision note: Created on 2026-06-05 by Codex after the session-runner slice exposed the preview-only matrix loop as the narrowest remaining matrix-side runtime seam. Updated on 2026-06-05 after implementation to record the extracted `phase3_preview_matrix_runner.py` boundary, focused validation, and final documentation reconciliation.
