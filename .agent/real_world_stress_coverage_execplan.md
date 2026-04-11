# Real-World Stress Coverage ExecPlan

## Objective

Add a first-class realistic-content stress layer to the preview-matrix and harness workflow so
automation can catch the same obvious layout failures that appear immediately in manual review.

## Decisions

- Use anonymized-but-equivalent long-field values instead of user-specific strings.
- Keep the existing manifests as baseline structural sweeps.
- Add new stress manifests rather than mutating the historical baseline corpus.
- Introduce the stress fixture source as a runtime module, not a test-only helper, so the matrix
  runner and harness can resolve it directly from manifests.
- Treat missing preview render artifacts in saved harness captures as an evidence-contract defect.
- Do not change layout policy in this slice; this work is about content realism and evidence
  integrity first.

## Implementation

- Added `src/foliaseal/application/qa_preview_stress_fixtures.py` with:
  - `stress_visible_appearance_v1`
  - anonymized long-field overrides for common name, email, title, company, location, and reason
  - a helper to apply the fixture profile to a `SignatureAppearance`
- Extended `src/foliaseal/presentation/qt/phase3_harness.py` to accept a manifest-level
  `fixture_profile` override through `appearance_overrides`
- Added `scripts/generate_preview_stress_manifests.py` to generate:
  - `artifacts/preview_sweep_assets/single_line_full_matrix_stress.json`
  - `artifacts/preview_sweep_assets/multi_line_full_matrix_stress.json`
  - `artifacts/preview_sweep_assets/wrapped_block_full_matrix_stress.json`
- Expanded tests to cover:
  - stress fixture profile application
  - stress manifest presence and required family variants
  - capture-state preservation of render artifacts and diagnostics
  - evidence-contract rejection of saved captures that omit preview artifacts
- Tightened text instrumentation so reference-render loss only counts as clipping when the live
  preview also shows real edge contact or overlap

## Verification

- Focused checks:
  - `ruff check` on the new stress fixture module, harness, evidence contract, tests, and manifest
    generator
  - focused pytest on `test_phase3_harness.py` and `test_preview_stress_fixtures.py`
- Full matrix rechecks executed:
  - baseline `single_line`, `multi_line`, `wrapped_block`
  - stress `single_line`, `multi_line`, `wrapped_block`

## Findings

- Baseline matrices remain structurally green.
- Stress matrices are now first-class and immediately exposed remaining green-path regressions:
  - `single_line`: `150` signable text-clipping risks
  - `multi_line`: `18` signable text-clipping risks
  - `wrapped_block`: `15` signable text-clipping risks
- Stress matrices also produced rejected-path diagnostic coverage that was previously invisible:
  - `single_line`: `680` rejected text-clipping risks
  - `multi_line`: `264` rejected text-clipping risks and `18` rejected stamp edge-touch warnings
  - `wrapped_block`: `423` rejected text-clipping risks and `324` rejected stamp edge-touch
    warnings

## Follow-up

- The methodology gap is now closed enough to trust the new stress findings.
- The next execplan should remediate the remaining stress green-path regressions cluster by
  cluster, starting with:
  - `single_line` top/bottom label-bearing stress cases
  - `multi_line` left/right balanced medium-density cases
  - `wrapped_block` top/bottom sparse named cases at `10pt`
