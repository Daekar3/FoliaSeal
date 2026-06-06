# Extract Phase 3 signed-acceptance scenario executor

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, `foliaseal phase3-signed-acceptance-matrix` should still produce the same scenario rows inside `summary.json`, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the per-scenario signed-acceptance flow inline. The user-visible proof stays the same: each scenario still applies one preview/setup configuration, captures preview diagnostics, optionally signs one output, snapshots the resulting PDF when signing succeeds, and returns the same result payload shape. The architectural gain is that the remaining broad per-scenario seam becomes a dedicated boundary with its own tests instead of another large module-private helper in `phase3_harness.py`.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_harness_capture_assembler_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_harness_session_runner_helper_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_preview_matrix_runner_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_acceptance_matrix_runner_execplan.md` is complete.

## Progress

- [x] (2026-06-06 15:05Z) Re-read the live signed-acceptance scenario executor, the extracted matrix runner, and the focused tests to confirm the narrowest remaining Phase 3 seam.
- [x] (2026-06-06 15:22Z) Extracted `Phase3SignedAcceptanceScenarioExecutor` into `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` and reduced `_execute_signed_acceptance_scenario()` in `src/foliaseal/presentation/qt/phase3_harness.py` to a thin delegating wrapper.
- [x] (2026-06-06 15:31Z) Added `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` and moved the focused per-scenario success/no-request proofs there.
- [x] (2026-06-06 15:36Z) Ran the focused signed-acceptance scenario validation, Ruff, and `git diff --check`.
- [x] (2026-06-06 15:44Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the matrix runner extraction left one broad scenario helper in `phase3_harness.py` rather than several smaller ones.
  Evidence: `_execute_signed_acceptance_scenario()` still owns scenario application, preview refresh, preview capture, request snapshotting, backend reservation evidence, signing submission, successful-output snapshotting, and final result shaping in one function.
- Observation: the new scenario boundary did not need to own exception mapping or acceptance-expectation evaluation.
  Evidence: those responsibilities were already cleanly held by `Phase3SignedAcceptanceMatrixRunner`, so the per-scenario helper could stay focused on one scenario row from preview through optional signed-output capture.

## Decision Log

- Decision: extract the scenario executor before touching `_snapshot_successful_signed_output(...)` or other capture helpers.
  Rationale: the remaining coupling pressure is at the per-scenario workflow boundary, while the output-snapshot logic already has an extracted analogue in `phase3_harness_capture_assembler.py`. Pulling that lower-level logic apart in the same slice would widen the change unnecessarily.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` now owns the full per-scenario signed-acceptance flow: scenario application, preview refresh/capture, request snapshotting, backend reservation evidence, signing submission, successful-output snapshotting, and final result shaping for one result row. `src/foliaseal/presentation/qt/phase3_harness.py` keeps `_execute_signed_acceptance_scenario()` as a thin delegating wrapper and remains the composition root that wires the real repository callables into the executor.

The focused test shape is narrower now. `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` owns the per-scenario no-request and successful-signing proofs, while `tests/unit/test_phase3_harness.py` keeps only the thin delegation proof for `_execute_signed_acceptance_scenario()`. The matrix runner and evidence-service contract remained stable throughout the extraction.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_acceptance_scenario_executor or signed_acceptance_matrix_runner or signed_acceptance_matrix or run_signed_acceptance_evidence'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qa_signed_acceptance_evidence.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has narrow boundaries for the interactive session runner, capture assembler, preview-matrix runner, and signed-acceptance matrix runner. The remaining larger seam in `src/foliaseal/presentation/qt/phase3_harness.py` is `_execute_signed_acceptance_scenario(...)`.

That helper currently does more than one job. It applies one scenario to the live shell, refreshes the preview, snapshots request and reservation evidence, captures preview-render diagnostics, optionally executes signing, snapshots signed-output evidence when signing succeeds, and then shapes the final JSON-ready result row.

This slice must keep the scenario result schema exactly the same because the signed-acceptance matrix runner, the evidence service, and the acceptance-evidence tests all rely on those result rows and derived counters.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py`. That module should own the full per-scenario execution flow for one signed-acceptance row while keeping the low-level harness collaborators injectable.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_execute_signed_acceptance_scenario()` delegates to the new helper instead of keeping the full flow inline. The harness file should remain the composition root that wires the real repository callables into that helper and keeps the existing helper name stable for the matrix runner.

Add a focused test module, `tests/unit/test_phase3_signed_acceptance_scenario_executor.py`, that exercises the extracted helper directly. Those tests should verify at least: preview capture and request snapshot shaping, the no-request path that avoids signing, successful signing with output snapshot propagation, and result-field stability.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new signed-acceptance scenario executor explicitly and explains that `phase3_harness.py` now delegates that per-scenario flow. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` and move the per-scenario signed-acceptance flow there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new helper.
3. Add `tests/unit/test_phase3_signed_acceptance_scenario_executor.py` and trim any moved scenario-level proofs from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_acceptance_scenario_executor or signed_acceptance_matrix_runner or signed_acceptance_matrix or run_signed_acceptance_evidence'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qa_signed_acceptance_evidence.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. The signed-acceptance matrix command must still return the same scenario result rows and derived summary payloads while the per-scenario flow becomes directly testable in a dedicated helper module.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_signed_acceptance_scenario_executor.py` owns scenario application, preview refresh/capture, request snapshotting, backend reservation evidence, signing submission, successful-output snapshotting, and final result shaping for one scenario;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates that work instead of keeping the full scenario flow inline;
- the new focused scenario-executor tests pass without broad monkeypatching of unrelated harness helpers;
- the public signed-acceptance matrix path remains stable for callers such as `Phase3EvidenceService`;
- `tests/unit/test_qa_signed_acceptance_evidence.py` still passes against the unchanged summary contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the new helper import or delegation shape is wrong, restore `_execute_signed_acceptance_scenario()` first, rerun the focused tests, and then retry the extraction. Do not mix acceptance-expectation rewrites, matrix summary changes, or shell/runtime changes into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review. Do not mix unrelated preview-matrix, interactive-session, or signing-shell changes into this slice.

## Interfaces and Dependencies

The extracted helper module should end with stable names for:

- a dedicated signed-acceptance scenario executor boundary that accepts:
  - `shell`,
  - `scenario`,
  - `profile_store`,
  - `artifacts_dir`,
  - `base_input_path`,
  - `certificate_path`,
  - `passphrase`,
  - `sign_executor`,
  - injected scenario-application helper,
  - injected compatibility-surface accessor,
  - injected request snapshot helper,
  - injected reservation-evidence helper,
  - injected preview-render capture helper,
  - injected preview snapshot helper,
  - injected signing-request snapshot helper,
  - injected scenario-slug helper,
  - injected signing-result snapshot helper,
  - injected successful-output snapshot helper;
- or an equivalent typed helper object encapsulating the same collaborators.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the place that wires the real repository callables into that helper. `src/foliaseal/presentation/qt/phase3_signed_acceptance_matrix_runner.py` is a caller and contract check, not an implementation target, for this slice.

Revision note: Created on 2026-06-06 by Codex after the signed-acceptance matrix runner slice exposed the per-scenario executor as the narrowest remaining Phase 3 runtime seam.
