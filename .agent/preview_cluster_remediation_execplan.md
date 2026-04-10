# ExecPlan: Preview Cluster Remediation After Text Instrumentation

## Objective

Use the new rendered-text instrumentation to eliminate the remaining preview
matrix clusters without reintroducing mode switches, compact branches, or
layout-specific typography semantics.

The implementation must:

- make `single_line left/right` stop claiming obviously clipped text is safe
- improve rendered-text detection so the harness measures full glyph extents
  instead of only the darkest baseline pixels
- rerun the unattended matrices until the residual clusters reflect real layout
  problems rather than instrumentation or preview-container seams

## Problem Statement

After the rendered-text instrumentation and coordinate fixes, the residual
matrix failures are now concentrated:

- `single_line`: large signable clipping cluster, dominated by horizontal
  `left/right` scenarios
- `multi_line`: tiny `left / 8.5pt / border 1.0 / no label` cluster
- `wrapped_block`: moderate `8.5pt` dense-content cluster

Inspection shows these are not all the same class of problem:

1. `single_line left/right` is a real product-policy bug.
   The backend still allows clipped no-wrap horizontal text to sign.

2. `multi_line` and `wrapped_block` are still affected by text detection that
   under-recognizes anti-aliased glyph edges in the preview PNG. The current
   detector often identifies only the darkest baseline pixels, which shrinks the
   measured text-content bounds.

## Implementation Plan

1. Tighten backend fit acceptance for `single_line left/right`.
   - Treat horizontal `single_line` like the user sees it: one line, no wrap,
     and no signable clipping.
   - Preserve the existing bounded rounding-seam correction where it is already
     documented for stacked layouts.
   - Do not add a new threshold or replacement tolerance.

2. Improve rendered-text extraction for anti-aliased glyphs.
   - Expand candidate detection beyond exact text-color matching so the harness
     includes gray anti-aliased edge pixels for black text on white backgrounds.
   - Keep the detector tied to actual preview pixels, not another geometry
     model.
   - Avoid reintroducing the old whole-widget false positives.

3. Revalidate the three family matrices.
   - `single_line`
   - `multi_line`
   - `wrapped_block`
   - Compare post-fix summaries against the current cluster baselines and keep
     iterating only if the output still reflects instrumentation artifacts.

4. Update focused tests.
   - backend regression for horizontal `single_line` acceptance
   - harness regression for anti-aliased text detection
   - keep full repo verification green

## Constraints

- No layout-mode-specific text scaling
- No new arbitrary “narrow case” or “dense case” branches
- No magic thresholds presented as layout policy
- Rounding or raster tolerances are acceptable only when documented as numeric
  seam corrections, not user-facing behavior

## Progress

- 2026-04-10: Plan created from the post-instrumentation matrix summaries.
- 2026-04-10: Tightened `single_line left/right` backend fit acceptance by
  removing the old horizontal overflow allowance from those positions.
- 2026-04-10: Expanded rendered-text pixel detection to include anti-aliased
  edge pixels based on text-color and luminance, rather than only the darkest
  pixels.
- 2026-04-10: Fixed harness coordinate mapping for nested widgets so text/stamp
  diagnostics are computed in card-relative coordinates.
- 2026-04-10: Calibrated raster seam handling so small anti-alias descender loss
  does not count as clipping by itself.
- 2026-04-10: Updated backend and harness regressions to lock in the new
  horizontal `single_line` contract and anti-aliased text detection behavior.
- 2026-04-10: Final unattended matrix results:
  - `single_line v7`: `216` scenarios, `42` text clipping risks, `0`
    text/stamp overlap risks, `0` green clipped scenarios
  - `multi_line v10`: `288` scenarios, `0` text clipping risks, `0`
    text/stamp overlap risks
  - `wrapped_block v7`: `288` scenarios, `0` text clipping risks, `0`
    text/stamp overlap risks
- 2026-04-10: Preview matrix summaries now distinguish total, signable, and
  rejected text clipping/overlap counts so intentionally rejected bad layouts do
  not read like unresolved green-path regressions.
- 2026-04-10: Stamp warning and stamp edge-touch summary counts now use the same
  total/signable/rejected breakdown so text and stamp diagnostics read uniformly.
- 2026-04-10: Refined stamp diagnostics so warnings are based on border-facing
  stamp clearance only; text-facing conflicts remain the responsibility of the
  text overlap/clipping diagnostics.
- 2026-04-10: Simplified the stamp-warning threshold to a constant 1px
  near-border signal now that the harness detects anti-aliased stamp-content
  bounds directly, removing the earlier border-width-driven warning noise.
- 2026-04-10: Reran all three full preview matrices after the stamp-diagnostic
  cleanup:
  - `single_line v10`: `216` scenarios, `42` rejected text clipping risks,
    `0` signable stamp warnings, `0` signable stamp edge-touch cases
  - `multi_line v13`: `288` scenarios, `0` text clipping risks,
    `4` signable stamp warnings, `0` signable stamp edge-touch cases
  - `wrapped_block v10`: `288` scenarios, `0` text clipping risks,
    `18` signable stamp warnings, `0` signable stamp edge-touch cases
- 2026-04-10: Final verification passed:
  - `ruff check .`
  - `pytest -q`
  - result: `348 passed`
