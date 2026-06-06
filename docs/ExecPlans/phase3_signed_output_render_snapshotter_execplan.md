# Extract Phase 3 signed-output render snapshotter

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, Phase 3 signed-output render analysis should keep the same payload shape, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the large `_snapshot_signed_output_render(...)` flow inline. The user-visible proof stays the same: successful signed-output evidence still captures page renders, signature crops, normalized crops, comparison images, text-detection output, annotation-rect parity, appearance-layer comparison, and the final `preview_vs_signed_output_passed` verdict. The architectural gain is a dedicated boundary for signed-output render analysis instead of one more large harness-local helper.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_signed_output_snapshotter_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_acceptance_scenario_executor_execplan.md` is complete.

## Progress

- [x] (2026-06-06 16:52Z) Re-read `_snapshot_signed_output_render(...)` and the focused tests to confirm it as the next narrowest Phase 3 seam.
- [x] (2026-06-06 17:14Z) Extracted `Phase3SignedOutputRenderSnapshotter` into `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py` and reduced `_snapshot_signed_output_render()` in `src/foliaseal/presentation/qt/phase3_harness.py` to a thin delegating wrapper.
- [x] (2026-06-06 17:28Z) Added `tests/unit/test_phase3_signed_output_render_snapshotter.py` and moved the focused render-snapshot proofs there.
- [x] (2026-06-06 17:34Z) Ran the focused render-snapshot validation, Ruff, and `git diff --check`.
- [x] (2026-06-06 17:42Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the render-snapshot seam is broad mostly because it coordinates many already-existing helper boundaries.
  Evidence: `_snapshot_signed_output_render(...)` mostly composes page rendering, rect projection, crop normalization, text detection, appearance snapshotting, parity comparison, and artifact writing rather than inventing new low-level algorithms inline.
- Observation: the existing render-snapshot tests were already narrow enough to move almost directly onto the new helper.
  Evidence: the focused parity/normalization/transparency tests only had to switch from the harness wrapper to the dedicated render snapshotter boundary plus one thin harness delegation proof.

## Decision Log

- Decision: extract the render-snapshot orchestrator before touching the lower-level image-analysis helpers.
  Rationale: the orchestration seam is already broad and directly testable. Pulling apart `_signed_output_appearance_snapshot(...)`, `_render_signed_annotation_appearance_direct(...)`, or the text-detection helpers in the same slice would widen the change unnecessarily.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py` now owns the signed-output render-analysis workflow for one successful output. `src/foliaseal/presentation/qt/phase3_harness.py` keeps `_snapshot_signed_output_render()` as a thin delegating wrapper and remains the composition root that wires the real repository callables into the helper.

The focused test shape is narrower now. `tests/unit/test_phase3_signed_output_render_snapshotter.py` owns the output parity, analysis-surface normalization, and transparent-page compositing proofs, while `tests/unit/test_phase3_harness.py` keeps only the thin delegation proof for `_snapshot_signed_output_render()`. The shared signed-output snapshotter and evidence-service contract remained stable throughout the extraction.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_output_render_snapshotter or snapshot_signed_output_render or signed_output_snapshotter or run_signed_acceptance_evidence'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has extracted boundaries for matrix orchestration, scenario execution, and successful-output evidence shaping. The remaining large render-analysis seam is `_snapshot_signed_output_render(...)` in `src/foliaseal/presentation/qt/phase3_harness.py`.

That helper currently owns the full signed-output render-analysis workflow for one successful output: page rendering, direct-appearance rendering, annotation-rect projection, crop extraction, normalization to preview analysis size, text detection, appearance snapshotting, parity comparison, and side-by-side artifact writing.

This slice must keep the returned render-snapshot payload exactly the same because the shared signed-output snapshotter, the evidence contract, and the existing harness tests rely on those fields.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py`. That module should own the render-analysis workflow for one signed output while keeping the many lower-level harness collaborators injectable.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_snapshot_signed_output_render()` delegates to the new helper instead of keeping the full flow inline. The harness file should remain the composition root that wires the real repository callables into that helper.

Add a focused test module, `tests/unit/test_phase3_signed_output_render_snapshotter.py`, that exercises the extracted helper directly. Those tests should verify at least: output parity capture, normalization to the analysis surface, transparent-page compositing over white, and the stable result fields already covered by the current harness tests.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new render snapshotter explicitly and explains that `phase3_harness.py` now delegates that render-analysis flow. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py` and move the signed-output render-analysis orchestration there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new helper.
3. Add `tests/unit/test_phase3_signed_output_render_snapshotter.py` and reduce the moved render-snapshot proofs from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py -k 'signed_output_render_snapshotter or snapshot_signed_output_render or signed_output_snapshotter or run_signed_acceptance_evidence'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py src/foliaseal/presentation/qt/phase3_signed_output_snapshotter.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_render_snapshotter.py tests/unit/test_phase3_signed_output_snapshotter.py tests/unit/test_qa_signed_acceptance_evidence.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. The signed-output render snapshot payload must keep the same fields and meanings while its orchestration becomes directly testable in a dedicated helper.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_signed_output_render_snapshotter.py` owns the signed-output render-analysis workflow for one successful output;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates that work instead of keeping the full flow inline;
- the new focused render-snapshot tests pass without broad unrelated harness monkeypatching;
- the shared signed-output snapshotter and evidence-service contract still pass against the unchanged payload contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the helper import or delegation shape is wrong, restore `_snapshot_signed_output_render()` first, rerun the focused tests, and then retry the extraction. Do not mix deeper appearance-analysis rewrites or evidence-service surface changes into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review.

## Interfaces and Dependencies

The extracted helper module should end with stable names for:

- a dedicated signed-output render snapshotter boundary that accepts:
  - `output_pdf_path`,
  - `page_index`,
  - `preview_snapshot`,
  - `preview_text`,
  - `output_visible_appearance_snapshot`,
  - `artifacts_dir`,
  - `artifact_basename`,
  - injected render backend factory,
  - injected direct-appearance renderer,
  - injected rect/parser helpers,
  - injected crop/normalization helpers,
  - injected text-detection helpers,
  - injected preview/signed appearance snapshot helpers,
  - injected comparison and artifact-writing helpers;
- or an equivalent typed helper object encapsulating the same collaborators.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the composition root that wires the real repository callables into that helper.

Revision note: Created on 2026-06-06 by Codex after the shared signed-output snapshotter slice exposed render-analysis orchestration as the next narrowest Phase 3 seam.
