## Rendered Text Bounds Parity

### Goal

Use the current signed preview-parity matrix results to eliminate the remaining geometry-only mismatch between preview and signed output.

The previous slice removed two false channels:

- border-layer mismatch
- text-fragment mismatch

What remains is one clean defect class:

- rendered text bounds differ after normalization

This slice should fix that without changing fit policy, acceptance thresholds, or the semantic text model.

### Entry Evidence

Source:

- `artifacts/signed_preview_parity_matrix_run_v2/summary.json`

Current state:

- `14` scenarios total
- `11` successful signings
- `3` scenarios fail before signing for valid fit reasons
- `0` cryptographic validation failures
- `0` annotation-rect mismatches
- `11` preview/output comparison failures

Layered comparison outcome for the `11` successful signings:

- `0` border mismatches
- `0` text-fragment mismatches
- `0` stamp mismatches
- `11` text-bounds mismatches after normalization

This means the parity system is now isolating a geometric rendering mismatch instead of semantic or metadata drift.

### Scope

This slice is limited to the text-bounds channel in signed-output parity.

Allowed work:

1. Improve how preview text bounds are represented for parity.
2. Improve how signed-output text bounds are detected or reconstructed for parity.
3. Add structured line-level text geometry where that helps explain or fix the mismatch.
4. Tighten normalization so preview and signed output are compared in equivalent coordinates.

Out of scope:

- fit or layout acceptance rules
- box/border/stamp policy
- timestamping, trust, certification, or signing semantics
- new matrix coverage beyond what is needed to validate this slice

### Likely Root Cause Candidates

The current evidence suggests the remaining mismatch is probably one or more of:

1. Preview text bounds are currently a single block bbox, while signed-output text detection is raster-derived and may be picking up different line extents.
2. The preview and signed output may differ in line-box versus glyph-ink bounds.
3. Multi-line/title cases may need line-level comparison instead of one unioned text rectangle.
4. The signed-output analysis path may still be using a detector where a structural reconstruction would be more accurate.

The slice should prove which of these is actually true before broadening.

### Plan

#### 1. Inspect representative failing cases

Use `artifacts/signed_preview_parity_matrix_run_v2/summary.json` and open representative results for:

- `single_line/top`
- `multi_line/left`
- `wrapped_block/right`

For each:

- compare preview text bounds
- compare signed-output text bounds
- inspect whether the mismatch is size, origin, line aggregation, or detector failure

The objective is to classify the defect, not guess.

#### 2. Add tracer-bullet tests before changing logic

Add focused tests that fail on the current behavior for:

- a `single_line` no-stamp case
- one `multi_line` case
- one `wrapped_block` case

The tests should assert parity at the structured text-geometry level, not only boolean pass/fail.

If line-level data is necessary, add tests for line bounds explicitly.

#### 3. Upgrade the appearance snapshot if needed

If the review proves that one text bbox is too coarse, extend the appearance snapshot with the minimum additional geometry needed.

Preferred order:

1. line-level text bounds
2. normalized text block anchor/baseline metadata
3. only then any raster fallback refinement

Do not add redundant metadata without a concrete use.

#### 4. Make signed-output text geometry structurally comparable

If the signed-output side is still detector-driven in a way the preview side is not, upgrade it so both sides use comparable semantics.

That may mean:

- reconstructing line bounds from the visible appearance snapshot when possible
- comparing line unions instead of raw detector output
- or falling back to raster only when structural geometry is unavailable

The goal is not “make the detector happier.” The goal is “compare equivalent geometry.”

#### 5. Rerun the parity matrix

After the focused tests are green:

- run `pytest -q`
- rerun the signed preview-parity matrix

Acceptance for this slice:

- the three pre-sign fit failures may remain
- the `11` successful signings should no longer fail solely on text-bounds mismatch
- if any parity failures remain, the summary should identify a narrower residual cluster than “all successful signings”

### Acceptance Criteria

This slice is complete when:

- focused tracer-bullet tests for text-geometry parity pass
- full `pytest -q` passes
- the signed preview-parity matrix reruns successfully
- border/text-fragment channels remain green
- text-bounds mismatch is either eliminated or reduced to a clearly classified residual subset

### Notes

This slice should stay instrumentation-led. The repository now has enough structural parity data to debug this cleanly. The right next move is to make text geometry comparable, not to widen tolerances.

### Execution Result

This slice produced one useful narrowing, but did not eliminate the remaining parity failures.

What landed:

- signed-output text detection now receives the normalized preview text bounds as its reference envelope
- the Qt render backend now explicitly enables annotation rendering flags

What the reruns showed:

- tests remained green (`444 passed`)
- the signed preview-parity matrix still reports `11` preview/output comparison failures for the `11` successful signings
- the three pre-sign fit failures remain legitimate and unchanged
- the signed page renders are still completely white in the parity run, and the normalized signed crops are blank

Conclusion:

The remaining blocker is not text-bounds normalization anymore. The blocker is that the signed-output raster path is not actually rendering the visible signature appearance. The next slice should move parity analysis off page-level Qt rendering and onto direct appearance-stream rendering.
