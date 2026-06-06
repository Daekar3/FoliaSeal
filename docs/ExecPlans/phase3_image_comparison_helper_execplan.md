# Extract Phase 3 image comparison helper

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 runtime should keep the same preview/output comparison behavior, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the shared image-comparison helper cluster inline. The user-visible proof stays the same: transition diagnostics still compute the same crop-change ratios, and signed-output parity still computes the same normalized change ratio, aspect-ratio delta, and side-by-side comparison artifact. The architectural gain is one dedicated boundary for Phase 3 image comparison instead of leaving the same concept split between the harness and the signed-output render snapshotter seam.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_signed_output_render_snapshotter_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_sign_time_diagnostics_snapshotter_execplan.md` is complete.

## Progress

- [x] (2026-06-06 23:45Z) Re-read the remaining Phase 3 lower-level helper cluster and chose the shared image-comparison helpers as the next coherent extracted boundary.
- [x] (2026-06-06 23:57Z) Extracted `Phase3ImageComparisonHelper` into `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py` and reduced the harness helpers to thin delegating wrappers.
- [x] (2026-06-07 00:06Z) Added `tests/unit/test_phase3_image_comparison_helper.py` with focused comparison-ratio and side-by-side overlay proofs.
- [x] (2026-06-07 00:10Z) Ran the focused validation, Ruff, and `git diff --check`.
- [x] (2026-06-07 00:16Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and prepared the slice for commit.

## Surprises & Discoveries

- Observation: the image-comparison helper is used in two distinct flows, which makes it a better seam than a render-snapshotter-only local extraction.
  Evidence: `_analyze_capture_state_transitions(...)` still uses `_image_crop_change_ratio(...)`, while `Phase3SignedOutputRenderSnapshotter` already depends on normalized change ratio, aspect-ratio delta, and side-by-side artifact writing.

## Decision Log

- Decision: extract the whole image-comparison helper cluster together rather than only the normalized comparison path.
  Rationale: crop hashing, flattening, raw comparison, normalized comparison, aspect-ratio delta, and comparison-overlay writing form one cohesive image-comparison boundary and already serve more than one caller.
  Date/Author: 2026-06-06 / Codex

## Outcomes & Retrospective

This slice completed successfully. `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py` now owns the shared image-comparison primitives that both Phase 3 transition diagnostics and signed-output parity rely on: crop hashing, preview flattening, raw and normalized change ratios, aspect-ratio delta, and side-by-side comparison artifact writing. `src/foliaseal/presentation/qt/phase3_harness.py` keeps thin wrapper helpers and remains the composition root that wires this boundary into the broader Phase 3 runtime.

The focused test shape is narrower now. `tests/unit/test_phase3_image_comparison_helper.py` owns the direct crop-change-ratio and side-by-side artifact proofs, while the existing higher-level harness and signed-output render tests continue to verify the unchanged comparison contract through their real callers.

Focused validation that passed for this slice:

- `.venv/bin/python -m pytest tests/unit/test_phase3_image_comparison_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_render_snapshotter.py -k 'image_comparison_helper or analyze_capture_state_transitions or signed_output_render_snapshotter'`
- `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_image_comparison_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_image_comparison_helper.py tests/unit/test_phase3_signed_output_render_snapshotter.py`
- `git diff --check`

## Context and Orientation

The Phase 3 runtime now has extracted boundaries for session running, matrix execution, output snapshotting, output render analysis, appearance snapshotting, and sign-time diagnostics. The remaining lower-level harness-owned seams are narrower, but `phase3_harness.py` still carries the preview/output image-comparison helper cluster inline.

That cluster currently owns:

- preview crop hashing,
- preview flattening to white,
- raw crop change ratio,
- normalized crop change ratio,
- aspect-ratio delta,
- side-by-side comparison artifact writing.

Those helpers are consumed by both transition diagnostics and signed-output parity. This slice must keep their behavior stable because the signed-output render snapshotter and transition-diagnostics tests rely on their outputs.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py`. That module should own the shared image-comparison behavior while keeping the underlying PIL dependencies local to the helper.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so `_image_crop_sha256()`, `_flatten_preview_image_to_white()`, `_image_crop_change_ratio()`, `_normalized_image_crop_change_ratio()`, `_aspect_ratio_delta()`, and `_write_side_by_side_comparison()` delegate to the new helper instead of keeping the logic inline. The harness file should remain the composition root that wires the extracted helper into other Phase 3 boundaries.

Add a focused test module, `tests/unit/test_phase3_image_comparison_helper.py`, that exercises the extracted helper directly. Keep the higher-level transition and signed-output tests in place, but let them rely on the now-thin wrappers.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 runtime section names the new image-comparison helper explicitly and explains that `phase3_harness.py` now delegates the shared preview/output comparison primitives there. Keep `docs/SPEC.md` unchanged unless implementation reveals an actual behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py` and move the shared image-comparison helpers there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new helper.
3. Add `tests/unit/test_phase3_image_comparison_helper.py` with direct proofs for the extracted helper.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_image_comparison_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_output_render_snapshotter.py -k 'image_comparison_helper or analyze_capture_state_transitions or signed_output_render_snapshotter'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_image_comparison_helper.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_image_comparison_helper.py tests/unit/test_phase3_signed_output_render_snapshotter.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. The image comparison outputs must keep the same values and artifact semantics while their shaping becomes directly testable in one dedicated helper.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_image_comparison_helper.py` owns the shared image-comparison helpers;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates those helpers instead of keeping the full logic inline;
- the new focused helper tests pass;
- transition-diagnostics and signed-output render tests still pass against the unchanged comparison contract;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the helper import or delegation shape is wrong, restore the harness-local helpers first, rerun the focused tests, and then retry the extraction. Do not mix deeper text-detection or parity-policy changes into this slice.

## Artifacts and Notes

The primary allowed change class for the implementation commit is internal architecture only. Documentation/status updates may follow if required by the compliance review.

## Interfaces and Dependencies

The extracted helper module should end with a stable name for:

- a dedicated Phase 3 image-comparison helper boundary that owns:
  - crop hashing,
  - white-background flattening,
  - raw crop change ratio,
  - normalized crop change ratio,
  - aspect-ratio delta,
  - side-by-side comparison artifact writing.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the composition root that wires the helper into transition diagnostics and signed-output parity flows.

Revision note: Created on 2026-06-06 by Codex after the sign-time diagnostics slice exposed the shared image-comparison helper cluster as the next coherent Phase 3 seam.
