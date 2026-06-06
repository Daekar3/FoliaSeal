# Extract Phase 3 text geometry helper

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 runtime should keep the same preview text-geometry behavior, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the text-geometry helper cluster inline. The user-visible proof stays the same: preview diagnostics still project source bounds correctly, detect rendered text bounds and line bounds correctly, reject border-like noise, and use the reference-envelope fallback when available. The architectural gain is one dedicated boundary for Phase 3 text geometry instead of keeping this multi-function detection concept embedded in the large harness file.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_image_comparison_helper_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_signed_output_render_snapshotter_execplan.md` is complete.

## Progress

- [x] (2026-06-07 00:25Z) Re-read the remaining preview/output helper cluster and chose the preview text-geometry helpers as the next coherent extracted boundary.
- [x] (2026-06-07 00:42Z) Extracted `Phase3TextGeometryHelper` into `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py` and reduced the harness helpers to thin delegating wrappers.
- [x] (2026-06-07 00:55Z) Added `tests/unit/test_phase3_text_geometry_helper.py` and moved the direct projection/content-detection proofs there.
- [x] (2026-06-07 01:01Z) Ran the focused validation, Ruff, and `git diff --check`.
- [x] (2026-06-07 01:08Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the text-geometry helper is a better seam than a single detection wrapper because projection, candidate filtering, line grouping, and reference-label fallback all participate in one stable preview-analysis contract.
  Evidence: `_capture_preview_render(...)` consumes projected source bounds, content bounds, line bounds, and the reference fallback as one analysis bundle, while the direct tests exercise those pieces together.

## Decision Log

- Decision: extract the whole text-geometry helper cluster together rather than only the `detect_text_*` wrappers.
  Rationale: the wrappers alone are too shallow; the real seam is the combined projection and candidate-analysis logic that reconstructs preview text geometry.
  Date/Author: 2026-06-07 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py` now owns the shared preview text-geometry primitives that Phase 3 preview diagnostics and signed-output parity rely on: source-to-preview bounds projection, rendered-text content and line detection, candidate filtering, reference-envelope restriction, and reference-label fallback capture. `src/foliaseal/presentation/qt/phase3_harness.py` keeps thin wrapper helpers and remains the composition root that wires this boundary into the broader Phase 3 runtime.

The focused test shape is narrower now. `tests/unit/test_phase3_text_geometry_helper.py` owns the direct projection and content-detection proofs, while the existing higher-level harness and signed-output render tests continue to verify the unchanged geometry contract through their real callers.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_text_geometry_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_render_snapshotter.py -k 'text_geometry_helper or project_content_bounds_to_preview or detect_text_content_bounds_in_preview or analyze_capture_state_transitions or signed_output_render_snapshotter'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_text_geometry_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_text_geometry_helper.py tests/unit/test_phase3_signed_output_render_snapshotter.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has extracted boundaries for image comparison, sign-time diagnostics, appearance snapshotting, output snapshotting, output render analysis, and the harness session/matrix flows. The remaining lower-level harness-owned seams are narrower, but `phase3_harness.py` still carries the preview text-geometry helper cluster inline.

That cluster currently owns:

- projection of source content bounds into preview coordinates,
- content-bounds and line-bounds detection wrappers,
- shared candidate-pixel analysis and border-noise filtering,
- reference-envelope restriction,
- reference-label fallback capture for text bounds.

Those helpers feed preview diagnostics and signed-output parity. This slice must keep their behavior stable because the preview-render tests rely on the exact bounds and error semantics they produce.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py`. That module should own the shared text-geometry behavior while keeping the underlying text-raster-analysis functions and Qt capture collaborators injectable.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_project_content_bounds_to_preview()`, `_detect_text_content_bounds_in_preview()`, `_detect_text_line_bounds_in_preview()`, `_detect_text_geometry_in_preview()`, `_reference_text_content_bounds()`, and the closely-related candidate/filter helpers delegate to the new helper instead of keeping the logic inline. The harness file should remain the composition root that wires the helper into preview capture and signed-output analysis.

Add a focused test module, `tests/unit/test_phase3_text_geometry_helper.py`, that exercises the extracted helper directly. Keep the higher-level preview-capture tests in place, but let them rely on the now-thin wrappers.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new text-geometry helper explicitly and explains that `phase3_harness.py` now delegates the shared preview text-geometry primitives there. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py` and move the shared text-geometry helpers there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new helper.
3. Add `tests/unit/test_phase3_text_geometry_helper.py` and reduce the moved direct geometry proofs from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_text_geometry_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_render_snapshotter.py -k 'text_geometry_helper or project_content_bounds_to_preview or detect_text_content_bounds_in_preview or analyze_capture_state_transitions or signed_output_render_snapshotter'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_text_geometry_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_text_geometry_helper.py tests/unit/test_phase3_signed_output_render_snapshotter.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. The text-geometry outputs must keep the same bounds and error semantics while their shaping becomes directly testable in one dedicated helper.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_text_geometry_helper.py` owns the shared text-geometry helpers;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates those helpers instead of keeping the full logic inline;
- the new focused helper tests pass;
- higher-level preview-capture and signed-output render tests still pass against the unchanged geometry contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the helper import or delegation shape is wrong, restore the harness-local text-geometry helpers first, rerun the focused tests, and then retry the extraction. Do not mix deeper preview-policy or text-analysis-algorithm rewrites into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review.

## Interfaces and Dependencies

The extracted helper module should end with a stable name for:

- a dedicated Phase 3 text-geometry helper boundary that owns:
  - bounds projection,
  - content-bounds and line-bounds detection,
  - candidate-pixel analysis,
  - border-stroke filtering,
  - reference-envelope restriction,
  - reference-label fallback capture.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the composition root that wires the helper into preview capture and signed-output parity flows.

Revision note: Created on 2026-06-07 by Codex after the image-comparison helper slice exposed the preview text-geometry cluster as the next coherent Phase 3 seam.
