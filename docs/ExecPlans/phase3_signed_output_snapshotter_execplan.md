# Extract Phase 3 signed-output snapshotter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, Phase 3 signed-output evidence should keep the same JSON payload shape, but the successful-output snapshot logic will stop being duplicated across `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`. The user-visible proof stays the same: successful signing still yields the same output-signature snapshot, verification snapshot, visible-appearance snapshot, signed-output render snapshot, and preview-vs-output comparison fields. The architectural gain is one shared boundary for signed-output evidence shaping instead of two near-identical helper clusters.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_harness_capture_assembler_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_acceptance_matrix_runner_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_acceptance_scenario_executor_execplan.md` is complete.

## Progress

- [x] (2026-06-06 15:58Z) Re-read the remaining signed-output evidence seam and confirmed the duplication between `phase3_harness.py` and `phase3_harness_capture_assembler.py`.
- [x] (2026-06-06 16:15Z) Extracted `Phase3SignedOutputSnapshotter` into `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py` and rewired both the harness and the capture assembler to use it.
- [x] (2026-06-06 16:24Z) Added `tests/unit/test_phase3_signed_output_snapshotter.py` and reduced the harness-level ownership proof to a thin wrapper/delegation check.
- [x] (2026-06-06 16:31Z) Ran the focused signed-output validation, Ruff, and `git diff --check`.
- [x] (2026-06-06 16:38Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the duplication was broader than just one helper name.
  Evidence: both `phase3_harness.py` and `phase3_harness_capture_assembler.py` carried the same preview-vs-output comparison projection and the same successful-output snapshot aggregation shape.
- Observation: the shared snapshotter also simplified the capture-assembler fallback path.
  Evidence: the final-output fallback branch in `build_capture_payload()` now reuses the same successful-output aggregation boundary instead of reconstructing its own subset of that logic inline.

## Decision Log

- Decision: extract one shared signed-output snapshotter before touching lower-level render-analysis helpers.
  Rationale: the duplication seam is already clear and directly reusable by both the per-scenario signed-acceptance flow and the interactive harness capture assembler. Pulling apart `_snapshot_signed_output_render(...)` itself in this slice would widen the change unnecessarily.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py` now owns the shared successful-output evidence bundle and the compact preview-vs-output comparison projection. Both `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` now delegate to that helper instead of carrying duplicate output-snapshot logic.

The focused test shape is narrower now. `tests/unit/test_phase3_signed_output_snapshotter.py` owns the shared successful-output and comparison-projection proofs, while `tests/unit/test_phase3_harness.py` keeps only a thin delegation proof for `_snapshot_successful_signed_output()`. The signed-acceptance scenario executor and evidence-service contract remained stable throughout the extraction.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_output_snapshotter or signed_acceptance_scenario_executor or snapshot_successful_signed_output or run_signed_acceptance_evidence'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qa_signed_acceptance_evidence.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has narrower boundaries for matrix orchestration and per-scenario signed-acceptance execution, but signed-output evidence shaping is still duplicated. `phase3_harness.py` keeps `_snapshot_successful_signed_output(...)` and `_signed_output_preview_comparison_snapshot(...)`, while `phase3_harness_capture_assembler.py` carries the same logic internally for signed runs and fallback final-output evidence.

This slice must keep the signed-output payload shape exactly the same because the evidence contract, harness JSON, and multiple harness tests rely on these fields.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py`. That module should own the successful-output evidence bundle and the derived preview-vs-output comparison projection while keeping the lower-level output/verification/render collaborators injectable.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_snapshot_successful_signed_output(...)` delegates to the new helper instead of keeping the full aggregation inline. Update `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` so it uses the same helper for signed-run bundles and fallback final-output capture payload assembly.

Add a focused test module, `tests/unit/test_phase3_signed_output_snapshotter.py`, that exercises the extracted helper directly. Those tests should verify at least: successful-output field shaping, preview-vs-output comparison projection, and the `None` render-snapshot path.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new snapshotter explicitly and explains that both the harness and the capture assembler delegate signed-output evidence shaping to it. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py` and move the shared successful-output snapshot logic there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` to delegate to the new helper.
3. Add `tests/unit/test_phase3_signed_output_snapshotter.py` and keep only a thin harness-level delegation proof where appropriate.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_output_snapshotter or signed_acceptance_scenario_executor or snapshot_successful_signed_output or run_signed_acceptance_evidence'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qa_signed_acceptance_evidence.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. Successful signed-output evidence must keep the same field names and meanings while one shared boundary becomes the owner of that shaping logic.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py` owns successful-output evidence aggregation and preview-vs-output comparison projection;
- `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` delegate to that helper instead of carrying duplicate logic;
- the new focused snapshotter tests pass without broad harness monkeypatching;
- the signed-acceptance scenario executor and harness evidence flows still pass against the unchanged payload contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the helper import or delegation shape is wrong, restore the duplicated helpers first, rerun the focused tests, and then retry the extraction. Do not mix deeper render-analysis changes or evidence-service surface changes into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review.

## Interfaces and Dependencies

The extracted helper module should end with stable names for:

- a dedicated signed-output snapshotter boundary that accepts:
  - `output_file`,
  - `page_index`,
  - `preview_snapshot`,
  - `preview_text`,
  - `trust_policy`,
  - `artifacts_dir`,
  - `artifact_basename`,
  - injected embedded-signature counter,
  - injected output-signature snapshotter,
  - injected output-verification snapshotter,
  - injected visible-appearance snapshotter,
  - injected signed-output render snapshotter;
- and an exported helper for projecting the compact preview-vs-output comparison view from the fuller render snapshot.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the composition root that wires the real repository callables into that helper.

Revision note: Created on 2026-06-06 by Codex after the signed-acceptance scenario slice exposed shared signed-output evidence shaping as the next narrowest Phase 3 seam.
