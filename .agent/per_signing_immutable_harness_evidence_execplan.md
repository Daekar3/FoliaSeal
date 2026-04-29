# Per-Signing Immutable Harness Evidence

## Goal

Make the interactive Phase 3 harness write an immutable evidence bundle for
each successful signing run, so later GUI edits cannot blur or overwrite the
review trail.

## Problem

The current harness persists:

- current/final preview state
- latest successful output evidence

but not a frozen sign-time bundle per successful signing. If the user signs
successfully and then keeps editing until a later rejection state, the top-level
capture becomes ambiguous. The numbered PDFs still exist, but the JSON no longer
contains a one-to-one preview/output/parity record for each successful run.

## Relevant Code Path

- Interactive harness entry:
  - `src/foliaseal/presentation/qt/phase3_harness.py`
  - `run_phase3_signing_harness(...)`
- Sign-success seam:
  - `src/foliaseal/presentation/qt/signing_shell.py`
  - `submit_sign_request(...)`
  - emits `_on_status_change("sign_success")` after a successful execute
- Existing mutable top-level evidence:
  - `preview_snapshot`
  - `output_visible_appearance_snapshot`
  - `signed_output_preview_comparison`

That seam is sufficient. The harness does not need a UI redesign or a new shell
API; it can capture immutable per-run evidence from the existing sign-success
event.

## Plan

1. Add TDD around the new evidence model.
   - `Phase3HarnessCapture.to_json()` serializes `signed_runs`
   - a per-run bundle deep-copies sign-time preview/request/reservation state so
     later edits cannot mutate it

2. Add one reusable helper that builds a successful signed-output evidence
   bundle from:
   - sign-time preview state
   - `SigningRequest`
   - `SigningResult`
   - output PDF path

3. In `run_phase3_signing_harness(...)`, capture a frozen sign-time preview
   state on each `sign_success` event and append a new `signed_runs` entry.

4. Keep existing top-level fields for convenience, but treat `signed_runs` as
   the canonical review record.

5. Reuse the new helper where possible so the interactive harness and the
   signed-matrix path do not drift.

## Constraints

- No rendering or parity-logic changes in this slice
- No fit-policy changes
- No GUI workflow changes
- Keep backward compatibility where practical

## Follow-on Note

After this slice, review the `Fantasy` font choice against the originally
discussed Papyrus-style direction.

## Execution Result

Implemented with TDD.

What landed:

- `src/foliaseal/presentation/qt/phase3_harness.py`
  - `Phase3HarnessCapture` now includes `signed_runs`
  - added `_snapshot_signing_result_payload(...)`
  - added `_signed_output_preview_comparison_snapshot(...)`
  - added `_snapshot_successful_signed_output(...)`
  - added `_build_signed_run_bundle(...)`
  - interactive harness now captures an immutable per-run bundle on each
    `sign_success` event
  - the latest successful run now supplies the convenience top-level signed
    output fields when present
- `tests/unit/test_phase3_harness.py`
  - verifies `signed_runs` serialize cleanly
  - verifies a per-run bundle deep-copies sign-time state so later edits do not
    mutate it
  - verifies the top-level current preview state can diverge from a preserved
    successful run bundle

The signed-matrix path was also updated to reuse the shared signing-result and
successful-output snapshot helpers so the interactive harness and matrix runner
do not drift.

Verification:

- focused red/green tests passed
- `python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py`
  passed
- `pytest -q` passed: `453 passed`

Outcome:

- later GUI edits can no longer invalidate the evidence bundle for an earlier
  successful signing run
- the interactive harness now has a canonical per-signing review record in
  `signed_runs`
- the previous ambiguity between top-level final preview state and earlier
  successful outputs is removed for review purposes

Follow-on remains unchanged:

- review the `Fantasy` font choice against the originally discussed
  Papyrus-style direction

## Follow-up Slice: Horizontal Left-Stamp Text Ink Alignment

### Goal

Make horizontal single-line previews and signed PDF appearances keep visible
text ink as close to the border as the established top/bottom behavior, while
preserving stamp scaling and the existing no-clipping invariants.

The current Issue #47 manual run showed that preview/PDF parity is encouraging,
but left-stamp single-line captures still reserve too much right-side whitespace
before the rounded border:

- Cap 4 left-stamp preview: canonical glyph ink ended about `19 px` from the
  right border.
- Cap 5 top-stamp preview: the same text family can safely approach the border
  at about `3 px`.
- The left-stamp excess whitespace shrinks the stamp sooner than necessary
  because the layout treats invisible text side-bearing slack as visible content.

### Relevant Code Path

- Shared text style and text-box alignment:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_build_text_box_style(...)`
- Preview canonical renderer:
  - `src/foliaseal/application/signing_preview_renderer.py`
  - `_canonical_preview_layout(...)`
- Signed PDF style construction:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_build_stamp_style(...)`
- Horizontal rendered-ink reservation:
  - `src/foliaseal/application/horizontal_signature_reservation.py`
  - `measure_horizontal_single_line_rendered_reference(...)`
  - `build_horizontal_single_line_ink_reservation(...)`

The horizontal ink reservation correctly narrows the text lane from rendered
ink width plus border/stamp padding. The remaining defect is that pyHanko places
the text object by natural font advance width, while the visible glyph ink can
have substantial right side-bearing. For a left-side stamp, that preserves
invisible right-side slack and leaves the visible glyph ink far from the right
border.

### Required Approach

1. Add a focused red test that replays the Cap 4-style left-stamp geometry and
   asserts:
   - visible glyph ink remains inside the rounded-border guard
   - visible glyph ink is no farther from the right border than the established
     close-border target
   - the stamp remains visible
   - stamp and text ink do not overlap

2. First attempt the simplest text-style alignment seam used by preview and
   signed PDF generation. If pyHanko line rendering does not expose line-level
   alignment there, use the measured horizontal ink reservation instead of an
   arbitrary threshold.

3. Do not change fit policy in this slice:
   - no altered width thresholds
   - no expanded reservation lane
   - no top/bottom layout behavior changes
   - any optical text translation must be derived from measured rendered-ink
     side-bearing and must preserve visible ink inside the border guard

4. Use the same alignment helper in:
   - canonical preview rendering
   - signed PDF style construction
   - any backend measurement path that must match the rendered appearance

5. Verify with focused tests first, then run the relevant broader preview and
   backend suites.

### Acceptance Criteria

This slice is complete when:

- the Cap 4-style preview test fails before the implementation and passes after
  it
- left-stamp single-line visible text can approach the right border like
  top/bottom single-line text
- stamp scaling improves because invisible right-side text slack no longer
  consumes the stamp lane
- preview and signed PDF generation use the same text alignment decision
- existing horizontal edge-safety tests still pass

### Execution Result

Implemented with TDD.

What landed:

- Added a Cap 4-style preview regression test asserting the visible text ink is
  within `1..6 px` of the right border, the stamp remains visible, and text/stamp
  ink do not overlap.
- Traced pyHanko text rendering and confirmed `TextBoxStyle` horizontal
  alignment does not move the visible glyph ink in this multiline case because
  the natural text advance is already right-aligned; the residual gap is font
  side-bearing.
- Added `_apply_horizontal_single_line_ink_text_alignment(...)` to translate
  left-stamp single-line text placement by the measured rendered-ink right
  side-bearing. This changes final appearance only; fit reservation and lane
  sizing still come from the existing ink reservation model.
- Wired the same alignment helper into canonical preview rendering and signed
  PDF style construction.
- Updated backend tests to assert the measured side-bearing margin adjustment
  instead of the old unchanged-right-margin assumption.
- Kept the rendered-ink preservation check intact, with a documented `3 px`
  reference-height tolerance for antialias row variance between the selected box
  and roomy reference render.

Observed result:

- The Cap 4-style preview right glyph-to-border gap moved from `19 px` to
  `4 px`.
- Stamp remains visible and non-overlapping in the regression test.

Verification:

- Focused preview/backend horizontal tests passed.
- `python -m ruff check ...` passed for touched code/tests.
- `pytest -q` passed: `513 passed, 1 warning`.

## Follow-up Slice: Vertical Single-Line Alignment and Horizontal Multi-Line Fit Honesty

### Goal

Address the latest manual harness observations without broadening fit policy:

- Caps 5-7: top/bottom single-line image stamps are left-packed with good border
  spacing, but their text remains centered, producing an inconsistent preview.
- Caps 10-12: horizontal multi-line layouts look visually valid, but validation
  is red because structural text height is `44 pt` while the reserved text lane
  is `42-43 pt`.

### Relevant Code Path

- Shared reservation layout:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_layout_reservation_for_template(...)`
- Stamp image fitting:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_background_layout_for_stamp(...)`
- Backend validation and rendered fallback:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_ensure_layout_can_fit(...)`
  - `_single_line_rendered_ink_fits_reservation(...)`
- Canonical preview tests:
  - `tests/unit/test_signing_preview_renderer.py`

### Required Approach

1. Add preview regression tests for the Cap 5-7 class:
   - top and bottom single-line image-stamp layouts should keep the text block
     aligned with the left-packed stamp rather than horizontally centered
   - stamp remains visible and non-overlapping

2. Change only the single-line top/bottom image-stamp text x-alignment:
   - keep the existing left-packed stamp behavior because manual review says the
     stamp border spacing is good
   - align text to the same left edge for visual consistency
   - do not change no-stamp single-line behavior
   - do not change multi-line/wrapped top/bottom behavior

3. Add backend regression tests for Caps 10-12:
   - horizontal multi-line left/right image-stamp layouts with small structural
     height overflow should validate when canonical preview geometry shows text
     and stamp inside the border with no overlap

4. Add a narrow multi-line rendered-layout fallback:
   - only for `multi_line` + visible image stamp + `left/right`
   - only when structural width still fits and structural height overflow is
     small
   - canonical preview structural text bounds and stamp bounds must be inside
     the container
   - text and stamp bounds must not overlap

5. Preserve existing rejection behavior:
   - no zero-width/zero-height stamp bands
   - no large text overflow acceptance
   - no top/bottom multi-line relaxation

### Acceptance Criteria

- Cap 5-7 style previews no longer show left-packed stamp with centered text.
- Cap 10-12 style horizontal multi-line cases validate when canonical preview
  geometry is visibly non-overlapping and inside the border.
- Existing compact rejection tests still pass.
- Full suite passes.

### Execution Result

Implemented with TDD.

What landed:

- Added top/bottom single-line preview regression coverage that reproduces the
  Cap 5-7 mismatch and asserts text stays visually near the left-packed stamp.
- Updated single-line top/bottom image-stamp text x-alignment to `ALIGN_MIN`
  only when a real image stamp is present. Default/no-image reservation behavior
  remains centered.
- Added horizontal multi-line regression coverage for the Cap 10-12 dimensions.
- Added `_horizontal_multi_line_rendered_layout_fits_reservation(...)`, a narrow
  fallback used only after structural validation fails. It accepts only
  `multi_line` + `left/right` image-stamp cases with no structural width
  overflow, small structural height overflow, canonical text/stamp bounds inside
  the rendered container, and no text/stamp overlap.
- Existing compact rejection tests still pass.

Verification:

- Focused red/green tests passed.
- Related layout/rejection tests passed.
- `python -m ruff check ...` passed for touched code/tests.
- `pytest -q` passed: `518 passed, 1 warning`.

### Follow-up Correction

The next manual harness run showed Caps 4-9 still red even though they should
pass, while Cap 10 was an intentional failure that should remain red.

Root cause:

- The horizontal multi-line fallback was capped at `3 pt` structural height
  overflow.
- The new valid manual cases had `4-5 pt` structural height overflow but still
  rendered visibly inside the border without text/stamp overlap.
- The fallback also checked structural text bounds against the container, which
  rejected one-pixel structural overflow even when the visible rendered ink was
  inside.

Correction:

- Expanded the narrow horizontal multi-line fallback limit to `6 pt` structural
  height overflow.
- Kept the large-overflow rejection path; the intentional Cap 10-style case
  remains rejected.
- Changed the final fallback geometry check to use rendered text ink bounds
  instead of structural text bounds, preserving the rendered-output fit policy.
- Added regression cases for the Cap 4-10 dimensions.

Verification:

- Cap 4-10 regression matrix passed with Caps 4-9 green and Cap 10 red.
- Related compact rejection tests passed.
- `python -m ruff check ...` passed for touched code/tests.
- `pytest -q` passed: `525 passed, 1 warning`.

## Next Slice: Sign-Time Fit and Geometry Diagnostics for Manual Harness Runs

### Goal

Resolve disputes like the current capture-2 / capture-3 case with direct,
coordinate-consistent evidence instead of mixed preview/debug heuristics.

The immediate problem is:

- the backend fit decision is based on point-space reservation math and is
  internally consistent
- the saved manual preview-side bounds for those same captures are not
  self-consistent
- therefore the current harness artifacts cannot honestly answer whether the
  preview is lying about available horizontal room

This slice should add sign-time diagnostics that make that question answerable
from one capture.

### Current Evidence and Justification

From the recent manual harness capture:

- capture 2 and capture 3 use the same text content and same measured backend
  text width
- the backend fit decision changes because the requested rectangle width changes
  from roughly `246 pt` to `257 pt`
- but the saved preview-side width/bounds evidence is internally inconsistent
  for those same captures

Relevant code path:

- backend fit measurement:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_measure_text_box_dimensions(...)`
  - `_layout_reservation_for_template(...)`
  - `_ensure_layout_can_fit(...)`
- preview capture and artifact serialization:
  - `src/foliaseal/presentation/qt/phase3_harness.py`
  - `_capture_interactive_state(...)`
  - `_snapshot_preview(...)`
  - `_capture_preview_render(...)`
- canonical preview rendering:
  - `src/foliaseal/application/signing_preview_renderer.py`

The missing seam is a sign-time snapshot that records:

- backend point-space measurements
- reservation results
- canonical preview image size
- canonical preview line/text bounds in that same image coordinate space

without mixing in widget-relative or detector-derived coordinates that can drift.

### Required Approach

Add a new sign-time diagnostic payload for successful and rejected manual
harness states. The payload should be attached directly to the per-state preview
snapshot and, for successful runs, also preserved under `signed_runs`.

For each captured preview state, record:

1. backend point-space fit inputs
   - `measured_text_box_width_pt`
   - `measured_text_box_height_pt`
   - `text_area_width_pt`
   - `text_area_height_pt`
   - `stamp_area_width_pt`
   - `stamp_area_height_pt`
   - `fit_gate_width_limit_pt`
   - `fit_gate_height_limit_pt`
   - `fit_gate_passed`

2. canonical preview geometry
   - canonical preview image width/height in px
   - canonical text bounds in px
   - canonical line bounds in px
   - canonical stamp bounds in px when present

3. explicit coordinate-space metadata
   - identify whether each bounds object is in:
     - canonical-preview image space
     - widget/card space
     - PDF point space

Do not rely on detector-derived text unions as the primary truth for this new
payload. Use canonical preview structural geometry first, and keep detector
results only as secondary diagnostics.

### TDD Plan

1. Add red tests around a new sign-time diagnostic snapshot helper:
   - verifies the helper returns point-space fit numbers and canonical preview
     geometry together
   - verifies the coordinate spaces are explicit

2. Add a red test for the recent failure shape:
   - two preview states with identical text content but different rectangle
     widths produce different `text_area_width_pt`
   - the snapshot shows the backend threshold crossing directly

3. Wire the helper into:
   - `_capture_interactive_state(...)`
   - `signed_runs` per-run bundles

4. Keep old debug fields for compatibility, but treat the new sign-time
   diagnostic payload as the authoritative fit/geometry record for manual review.

### Acceptance Criteria

This slice is complete when:

- a manual harness capture contains enough sign-time data to explain a pass/fail
  fit decision without inference
- the point-space fit gate and canonical preview geometry can be compared from
  one JSON payload
- the capture-2 / capture-3 class of dispute can be resolved from artifacts
  without hand-waving about widget-space seams

### Constraints

- Do not change fit policy in this slice
- Do not change rendering in this slice
- Do not change acceptance thresholds in this slice
- This is instrumentation and reviewability work only

### Execution Result

Implemented in:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_harness.py`

What landed:

- `_snapshot_backend_reservation(...)` now preserves sign-time fit numbers even
  when layout validation fails:
  - `measured_text_box_width_pt`
  - `measured_text_box_height_pt`
  - `text_area_width_pt`
  - `text_area_height_pt`
  - `stamp_area_width_pt`
  - `stamp_area_height_pt`
  - `reserved_primary_extent_pt`
  - `fit_gate_width_limit_pt`
  - `fit_gate_height_limit_pt`
  - `fit_gate_passed`
  - `error`
- `_snapshot_sign_time_fit_diagnostics(...)` now combines:
  - backend fit numbers in `pdf_points`
  - canonical preview geometry in `canonical_preview_pixels`
- `_capture_interactive_state(...)` now attaches that diagnostic payload to each
  preview snapshot at capture time.

TDD notes:

- The original fit-failure test was unstable because it depended on certificate
  subject length.
- It was replaced with explicit override-backed visible text so the overflow
  case is deterministic and exercises the actual width-threshold path.

Verification:

- `python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py`
- `pytest -q`
- Result: `455 passed`

## Next Slice: Normalize Interactive Preview Diagnostics and Remove Live Right-Edge Blank Strip

### Problem Statement

The new sign-time diagnostics made the current `single_line/top + stamp` issue
explicit, but they also exposed one remaining inconsistency:

- the interactive harness writes a bordered analysis image via
  `render_canonical_signature_preview(..., include_border=True, flatten_to_white=True)`
- but `_capture_preview_render(...)` currently serializes
  `analysis_appearance_snapshot` from the borderless GUI snapshot already stored
  on `card_container._canonical_preview_snapshot`
- it only swaps the `image_path`, leaving the bordered analysis artifact paired
  with borderless geometry metadata

That is why recent captures produced impossible combinations such as:

- analysis image width around `249 px`
- serialized text bounds width around `334 px`

Those numbers are coming from two different snapshots.

There is also a live preview defect in the Qt shell:

- `SigningShellAdapter._apply_canonical_preview_render(...)` scales the preview
  pixmap with `KeepAspectRatio`
- but then fixes the render label to the full inner-body size instead of the
  scaled pixmap size
- in narrow `single_line/top + stamp` cases this can leave a visible blank strip
  on the right side of the live preview even though the canonical pixmap itself
  is not blank

### Relevant Code Path

- interactive harness capture:
  - `src/foliaseal/presentation/qt/phase3_harness.py`
  - `_capture_preview_render(...)`
  - `_snapshot_sign_time_fit_diagnostics(...)`
  - `_preview_appearance_snapshot_from_capture(...)`
- canonical preview rendering:
  - `src/foliaseal/application/signing_preview_renderer.py`
  - `render_canonical_signature_preview(...)`
- live GUI preview composition:
  - `src/foliaseal/presentation/qt/signing_shell.py`
  - `SigningShellAdapter._apply_canonical_preview_render(...)`
  - `SigningShellAdapter._load_canonical_preview_pixmap(...)`

### Required Changes

1. Fix the interactive harness analysis snapshot source
   - when `_capture_preview_render(...)` creates a bordered analysis render,
     build `analysis_appearance_snapshot` from `analysis_snapshot.appearance_snapshot`
     rather than from the borderless GUI snapshot
   - preserve analysis-specific:
     - `image_size_px`
     - `container_bounds_px`
     - `border_bounds_px`
     - `text_bounds_px`
     - `line_bounds_px`
     - `stamp_bounds_px`
   - only fall back to the GUI snapshot when the bordered analysis render is
     unavailable

2. Keep sign-time diagnostics on one coordinate system
   - after the harness fix above,
     `_snapshot_sign_time_fit_diagnostics(...)` should consume the corrected
     `analysis_appearance_snapshot` directly
   - no new detector-derived overrides should be introduced in this slice

3. Fix the live GUI blank-strip behavior
   - when a canonical preview pixmap is available, size the render label to the
     scaled pixmap dimensions rather than the full inner-body dimensions
   - preserve transparent composition and existing aspect-ratio scaling
   - do not stretch the pixmap

### TDD Plan

1. Add a harness regression proving analysis geometry comes from the bordered
   analysis snapshot, not the borderless GUI snapshot.
2. Add a shell regression proving the render label uses the scaled pixmap size
   instead of the full inner-body size.
3. Implement the two code changes above.
4. Run focused tests, then `ruff`, then the full suite.

### Acceptance Criteria

- manual capture analysis artifacts no longer contain impossible combinations of
  image size and text bounds
- `sign_time_diagnostics.canonical_preview_geometry` is consistent with the
  saved analysis image
- the live preview no longer shows a right-edge blank strip caused by label
  oversizing
- no fit-policy, rendering-policy, or threshold changes are introduced

### Execution Result

Implemented in:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_phase3_harness.py`
- `tests/unit/test_qt_signing_shell.py`

What landed:

- `_capture_preview_render(...)` now builds `analysis_appearance_snapshot` from
  the bordered analysis render when it exists, instead of reusing borderless GUI
  snapshot geometry with only the image path swapped.
- This keeps analysis-specific:
  - `image_size_px`
  - `container_bounds_px`
  - `border_bounds_px`
  - `text_bounds_px`
  - `line_bounds_px`
  - `stamp_bounds_px`
  on one coherent coordinate system.
- `SigningShellAdapter._apply_canonical_preview_render(...)` now sizes the live
  render label to the scaled pixmap dimensions when available, rather than the
  full inner-body dimensions.

Why this fixes the current issue:

- recent manual captures showed impossible combinations such as analysis images
  around `249 px` wide paired with serialized text bounds around `334 px` wide
- that mismatch came from mixing bordered analysis images with borderless GUI
  snapshot geometry
- the live right-edge blank strip came from the render label being larger than
  the scaled pixmap

Verification:

- focused harness regression: passed
- focused Qt shell regressions: passed
- `python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py`
- `pytest -q`
- Result: `456 passed`

## Next Slice: Make the GUI Preview Use the Real Bordered Canonical Appearance

### Problem Statement

The corrected diagnostics show the remaining disagreement clearly:

- backend fit for the recent `single_line/top + stamp` ladder is internally
  consistent
- canonical analysis geometry now matches that backend fit
- but the live GUI preview is still misleading because it shows a borderless
  transparent render inside a separate white card

In failing states, clipped text at the right edge is therefore perceived as a
white bar inside the signature instead of as text clipping against the actual
signature border.

### Relevant Code Path

- live preview render selection:
  - `src/foliaseal/presentation/qt/signing_shell.py`
  - `SigningShellAdapter._apply_canonical_preview_render(...)`
- preview card chrome:
  - `src/foliaseal/presentation/qt/signing_shell.py`
  - `_build_preview_controls(...)`
  - `refresh_preview()` card style updates

### Required Changes

1. Change the GUI canonical preview request to render the real bordered
   appearance:
   - `include_border=True`
   - `flatten_to_white=False`

2. When a canonical preview snapshot is active:
   - remove the extra outer card border/background chrome
   - leave only the canonical rendered rounded border as the visible signature
     border

3. Keep the existing scaled-pixmap sizing fix so the render label matches the
   actual scaled pixmap dimensions.

### TDD Plan

1. Update the shell regression that currently expects a borderless canonical
   preview request.
2. Add a regression proving the outer card chrome is suppressed when a
   canonical preview snapshot is active.
3. Implement the render and card-style changes.
4. Run focused shell tests, then `ruff`, then the full suite.

### Acceptance Criteria

- failing `single_line/top + stamp` GUI previews visibly clip against the real
  rounded border instead of appearing to have a white internal bar
- successful cases still show the same rounded border as the signed PDF
- no double-border reappears

### Execution Result

Implemented in:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`

What landed:

- the GUI preview now requests the canonical render with:
  - `include_border=True`
  - `flatten_to_white=False`
- when a canonical preview snapshot is active, the extra outer card chrome is
  suppressed:
  - `QGroupBox { border: none; background: transparent; padding: 0px; }`
- the scaled-pixmap sizing fix remains in place, so the render label follows
  the actual pixmap dimensions instead of the full body size

Why this is the right fix:

- the previous GUI path displayed a borderless transparent render inside a
  separate white card
- in failing states, clipped text therefore looked like a white internal bar
  rather than clipping against the real signature border
- switching the GUI to the real bordered canonical appearance makes the preview
  visually honest and aligns it with the signed PDF appearance model

Verification:

- focused Qt shell regressions: passed
- `python -m ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py`
- `pytest -q`
- Result: `457 passed`

## Next Slice: Separate Structural Text Boxes from Raster Glyph-Ink Bounds

### Problem Statement

Recent manual review showed that the current diagnostics still overstate
apparent preview crowding. The root cause is now clear:

- `signing_preview_renderer._structural_line_bounds_px(...)` derives line bounds
  from `_measure_text_box_dimensions(...)`
- those bounds describe structural text boxes, not raster glyph ink
- the harness was reporting those structural boxes as `text_bounds_px` in
  manual fit diagnostics

That made statements like "the border is 13 px into the text" unsound even when
visible white space remained between the border and the rendered glyph pixels.

### Relevant Code Path

- structural preview bounds:
  - `src/foliaseal/application/signing_preview_renderer.py`
  - `_structural_line_bounds_px(...)`
  - `render_canonical_signature_preview(...)`
- manual harness preview capture:
  - `src/foliaseal/presentation/qt/phase3_harness.py`
  - `_capture_preview_render(...)`
  - `_capture_headless_preview_render(...)`
  - `_snapshot_sign_time_fit_diagnostics(...)`
- raster text detection:
  - `src/foliaseal/presentation/qt/phase3_harness.py`
  - `_detect_text_content_bounds_in_preview(...)`
  - `_detect_text_line_bounds_in_preview(...)`

### Required Changes

1. Preserve structural bounds explicitly
   - `text_structural_content_bounds_px`
   - `text_structural_line_bounds_px`

2. Detect raster glyph-ink bounds from the canonical analysis image and record
   them separately:
   - `text_rendered_content_bounds_px`
   - `text_rendered_line_bounds_px`

3. Update `sign_time_diagnostics.canonical_preview_geometry` to report both:
   - structural bounds for backend-fit reasoning
   - glyph-ink bounds for visible-fit judgment

4. Keep the backend fit gate unchanged.
   - This slice changes instrumentation and review semantics only.

### TDD Plan

1. Add a harness regression proving canonical captures preserve structural
   bounds and also record raster glyph-ink bounds when detection succeeds.
2. Update sign-time diagnostics tests so visible-fit review defaults to the
   glyph-ink bounds while still preserving structural bounds.
3. Implement the capture and diagnostics changes.
4. Update docs to explain why rasterization returned here: not to drive fit
   policy, but to judge preview honesty.

### Acceptance Criteria

- manual harness diagnostics no longer present structural text boxes as if they
  were glyph-pixel bounds
- review payloads clearly distinguish:
  - backend structural fit reasoning
  - visible glyph-ink clearance in the preview
- docs state explicitly that rasterization is review instrumentation, not the
  primary fit engine

### Execution Result

Implemented in:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_harness.py`
- `README.md`
- `phase3_parallel_plan.md`
- `pdf_signing_app_feasibility.md`

What landed:

- canonical preview captures now preserve both:
  - structural text bounds from the canonical text layout
  - raster glyph-ink bounds detected from the canonical analysis image
- the harness now records:
  - `text_structural_content_bounds_px`
  - `text_structural_line_bounds_px`
  - `text_rendered_content_bounds_px`
  - `text_rendered_line_bounds_px`
- `sign_time_diagnostics.canonical_preview_geometry` now exposes both models:
  - `structural_text_bounds_px`
  - `structural_line_bounds_px`
  - `glyph_ink_text_bounds_px`
  - `glyph_ink_line_bounds_px`
- for visible-fit review, the compatibility `text_bounds_px` / `line_bounds_px`
  fields now prefer the glyph-ink bounds when available.

Documentation updates:

- `README.md`
- `phase3_parallel_plan.md`
- `pdf_signing_app_feasibility.md`

Those docs now state explicitly that rasterization returned only for review and
QA instrumentation. The backend fit engine remains structural and
calculation-driven.

Verification:

- focused harness regressions: passed
- `python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py README.md phase3_parallel_plan.md pdf_signing_app_feasibility.md .agent/per_signing_immutable_harness_evidence_execplan.md`
- `pytest -q`
- Result: `457 passed`

## Next Slice: Tighten the Live GUI Preview to the Canonical Render Bounds

### Problem Statement

The latest manual ladder changed the diagnosis again:

- backend fit numbers for the exact `Morgan Ellery | Board Secretary | FoliaSeal`
  cases are consistent with HarfBuzz advance/extents
- the remaining mismatch is primarily visual:
  - cap 3 and cap 4 look like they should fit
  - cap 5 shows much more horizontal room in the live preview than the
    canonical analysis image reports

The likely cause is that the live Qt preview still displays the canonical
render inside a larger body container than the render itself, which makes the
preview look looser than the actual canonical image the fit diagnostics are
based on.

### Relevant Code Path

- live canonical preview composition:
  - `src/foliaseal/presentation/qt/signing_shell.py`
  - `SigningShellAdapter._apply_canonical_preview_render(...)`
- preview body sizing in `refresh_preview()`
- harness capture:
  - `src/foliaseal/presentation/qt/phase3_harness.py`
  - `_capture_preview_render(...)`

### Required Changes

1. Add automated tracer-bullet coverage for the current manual ladder shape.
   - exact `single_line/top + stamp` style
   - widths representing:
     - clearly red
     - near-boundary red
     - first green
   - assert the live preview body does not retain extra width beyond the actual
     canonical render bounds when a canonical pixmap is active

2. Tighten the live preview layout.
   - when a canonical preview pixmap is present, size the active body container
     to that pixmap as well as the render label
   - do not leave the render label floating inside a larger blank body region

3. Keep the current bordered canonical render and transparency behavior.
   - this slice is about body/container sizing, not another border change

### TDD Plan

1. Add a Qt shell regression proving the active preview body container is sized
   to the scaled canonical pixmap, not the larger inner-body allowance.
2. Add one harness-side regression proving the captured live preview bounds
   align with the canonical render width for the current single-line path.
3. Implement the container-sizing change.
4. Run focused tests, then `ruff`, then the full suite.

### Acceptance Criteria

- the live GUI preview no longer shows “ocean of space” around the canonical
  signature for the same cap-3/cap-5 class
- the live preview more closely matches the canonical analysis image used by the
  fit diagnostics
- the new automated tests cover this ladder so manual harness reruns are not
  the only signal

### Execution Result

Implemented in:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`

What landed:

- when a canonical preview pixmap is active, the active preview body container
  is now sized to the scaled pixmap as well as the render label
- this removes the larger blank body region that previously made the live GUI
  preview look looser than the canonical render the fit diagnostics were based
  on

Automated guardrail added:

- a Qt shell regression now proves that when the scaled canonical pixmap is
  `91x37`, both:
  - `single_render_label.fixed_size`
  - `single_body_container.fixed_size`
  resolve to `91x37`

Verification:

- focused Qt shell regressions: passed
- `python -m ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py .agent/per_signing_immutable_harness_evidence_execplan.md`
- `pytest -q`
- Result: `457 passed`

## Next Slice: Use Analysis-Space Bounds for Raster Glyph Detection

### Problem Statement

The latest manual ladder shows the remaining diagnostics problem clearly:

- the interactive harness writes a 1x bordered analysis image
- but the raster glyph detector in `_capture_preview_render(...)` still uses
  live widget bounds from the larger on-screen preview
- those bounds are then applied directly to the smaller analysis image

That means the detector is still mixing coordinate spaces. In the current
captures, `text_widget_bounds_px.width` can be around `330`, while the analysis
image width is only around `255`. The crop then degenerates into “almost the
entire analysis image”, which can falsely report too much or too little text
width.

### Relevant Code Path

- `src/foliaseal/presentation/qt/phase3_harness.py`
  - `_capture_preview_render(...)`
  - `_detect_text_content_bounds_in_preview(...)`
  - `_detect_text_line_bounds_in_preview(...)`

### Required Changes

1. In the interactive harness path, use analysis-space bounds when the detector
   reads from the analysis image:
   - `analysis_snapshot.text_area_bounds_px`
   - `analysis_snapshot.stamp_area_bounds_px`
   instead of the live widget/card bounds.

2. Keep live widget bounds separately for GUI capture metadata and live preview
   review. Do not overwrite them.

3. Add automated regression coverage so the detector cannot silently fall back
   to mixed coordinate spaces again.

### TDD Plan

1. Add a harness regression that forces:
   - one set of live widget bounds
   - a different set of analysis-space bounds
   - and asserts the detector is called with the analysis-space bounds
2. Implement the interactive capture fix.
3. Run focused harness tests, then `ruff`, then the full suite.

### Acceptance Criteria

- raster glyph detection on the interactive harness uses the analysis image's
  own coordinate system
- manual ladder diagnostics stop conflating live widget bounds with analysis
  image bounds
- this failure mode is covered by an automated regression

### Execution Result

Implemented in:

- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_harness.py`

What landed:

- interactive raster glyph detection now uses the analysis image's own
  `text_area_bounds_px` when the detector reads from the bordered 1x analysis
  image
- live widget bounds are still preserved separately for GUI metadata, but they
  are no longer fed directly into the analysis-image detector

Automated guardrail added:

- a harness regression now forces different live-widget and analysis-space
  bounds and asserts that `_detect_text_content_bounds_in_preview(...)` is
  called with the analysis-space rectangle

Verification:

- focused harness regressions: passed
- `python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py .agent/per_signing_immutable_harness_evidence_execplan.md`
- `pytest -q`
- Result: `458 passed`

## Next Slice: Backend Single-Line Rendered-Ink Fit Fallback

### Goal

Stop using the manual harness to rediscover the same `single_line/top + image`
fit mismatch. The current artifacts are now coherent enough to show that the
remaining problem is in the backend fit gate:

- the gate still validates against the structural text-box width
- the preview now exposes materially smaller rendered glyph ink
- the current red/red/green ladder should be automated before any more manual
  runs

### Relevant Code Path

- fit issue entry point:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_visible_signature_fit_issues_for_stamp_text(...)`
- current structural rejection seam:
  - `_build_stamp_style(...)`
  - `_ensure_layout_can_fit(...)`
- canonical rendered truth source:
  - `src/foliaseal/application/signing_preview_renderer.py`
  - `render_canonical_signature_preview(...)`
- raster glyph detector:
  - currently used by the harness and split out into a shared application
    helper in this slice

### Current Evidence

From the latest manual ladder:

- width `247.294 pt`: red
- width `256.29 pt`: red
- width `261.29 pt`: green

while the rendered glyph-ink width remains effectively unchanged across those
states. The structural width remains `254 pt`, so the gate only flips once the
reservation catches up to the structural box. That is the mismatch this slice
addresses.

### Required Changes

1. Add a tracer-bullet backend ladder test with the exact current manual text:
   - `Digitally signed by`
   - `Morgan Ellery | Board Secretary | FoliaSeal | 2026-04-24 21:26`
   and the current manual widths:
   - `247.294 pt`
   - `256.29 pt`
   - `261.29 pt`
   plus one smaller fail case below the visible threshold.

2. Extract the raster text detector into a shared application helper.
   - The harness and backend must use the same image-space text candidate rules
     and border filtering.

3. Add a narrow rendered-ink fallback in `_build_stamp_style(...)`.
   - Keep `_ensure_layout_can_fit(...)` as the first-pass structural gate.
   - Only when that gate fails for the current disputed class:
     `SignatureLayoutTemplate.SINGLE_LINE` with a visible `TOP` stamp image,
     render the canonical preview and detect actual text ink inside the
     reserved text area.
   - If the rendered ink matches the roomy reference render and still fits
     inside the reserved text area, allow the style to proceed.
   - Fail closed on render/detection errors.

4. Keep the slice narrow.
   - No multi-line or wrapped-block fit-policy changes.
   - No new tolerance slack in `_ensure_layout_can_fit(...)`.
   - No preview-only exceptions.

### Why Rasterization Is Used Here

This is not a return to rasterization as the primary layout model. Structural
reservation math remains the first pass. Rasterization comes back only as the
deciding signal for *visible fit* on a single disputed class where the
structural text box is now proven too pessimistic relative to the rendered
appearance the user sees.

### TDD Plan

1. Red:
   - add the explicit backend ladder test
   - assert the smaller width still fails
   - assert the current manual ladder widths pass after the fallback

2. Green:
   - add the shared raster detector module
   - wire the single-line rendered-ink fallback into `_build_stamp_style(...)`

3. Refactor:
   - keep the detector shared at the application layer
   - keep the fallback helper local to the backend seam

4. Verify:
   - focused backend tests
   - `ruff check`
   - full `pytest -q`

### Acceptance Criteria

- the current manual cap-2 / cap-3 / cap-4 ladder is reproduced in automated
  backend tests
- those tests pass without another manual harness run
- the backend no longer rejects the current visually acceptable ladder widths
  on this single-line stamped path
- genuinely tighter widths still fail

### Execution Result

Implemented in:

- `src/foliaseal/application/text_raster_analysis.py`
- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_signing_backend.py`

What landed:

- the harness text-raster detector was extracted into a shared application
  helper so the backend and harness now analyze text ink with the same pixel
  rules
- `_build_stamp_style(...)` now keeps the structural gate as the first pass
- when that gate fails for the narrow disputed class:
  - `single_line`
  - visible image stamp
  - `stamp_position == TOP`
  the backend renders the canonical preview, detects rendered text ink inside
  the reserved text area, and compares it against a roomy reference render of
  the same text
- if the current rendered ink matches the roomy reference and still fits inside
  the current reserved text area, the style proceeds
- tighter widths below the current manual threshold still fail in the tracer
  bullet test

Automated coverage added:

- a backend ladder test now reproduces the exact current manual widths:
  - `247.294 pt`
  - `256.29 pt`
  - `261.29 pt`
  and asserts they pass for the current real-world `Morgan Ellery` top-stamp
  case
- the test also includes a smaller `244 pt` control case that still fails

Verification:

- focused backend regressions: passed
- `python -m ruff check src/foliaseal/application/text_raster_analysis.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py .agent/per_signing_immutable_harness_evidence_execplan.md`
  passed
- `pytest -q` passed: `462 passed`

## Slice: Restore Text-First Horizontal Stamp Sizing

### Triggering Observation

The latest manual harness run shows `single_line` with `LEFT`/`RIGHT` image
stamps no longer shrinking the stamp from the space left after text. The
reported cases are captures 5, 6, 7, and 9. Capture 10 has visibly separated
text and stamp content but still reports red validation.

The current artifact values confirm the problem:

- Cap 9 and Cap 10 both use a `373.25 pt x 36.86 pt` rectangle.
- The measured text box is `254 pt x 18 pt`.
- The reservation is `text_area_width_pt = 250` and
  `stamp_area_width_pt = 115`.
- Validation fails because the text box is wider than the protected text lane.
- The protected `115 pt` stamp lane comes from
  `_single_line_horizontal_minimum_stamp_width(...)`, which sizes the stamp
  from available height and aspect ratio before allocating text.

That policy is backwards for this template. Horizontal `single_line` should be
text-first: allocate the measured text lane first, then give the stamp whatever
width remains after the normal separator. The stamp should shrink to that
remaining lane rather than forcing text to lose space.

### Requirements

- Keep the existing shared reservation model. Do not add another preview-only
  fit path.
- For horizontal `single_line` with a visible stamp, remove the protected
  minimum stamp width from the reservation calculation.
- Preserve the existing text-first behavior for horizontal `single_line`
  without a stamp.
- Keep vertical `single_line` behavior unchanged.
- Keep non-`single_line` layout behavior unchanged.
- Validation should pass when the measured text box fits in the text-first lane
  and a nonzero remaining stamp lane exists.
- Very narrow rectangles should remain invalid when the measured text still
  cannot fit.

### TDD Plan

1. Red:
   - add a reservation regression for the current cap-10 geometry proving
     horizontal `single_line/right` allocates the full `254 pt` text lane before
     assigning the remaining stamp lane
   - add a validation regression proving the same geometry has no fit issue
   - add a tighter control proving a width that cannot fit the text still fails

2. Green:
   - remove `_single_line_horizontal_minimum_stamp_width(...)` from the
     left/right reservation calculation
   - delete or rewrite tests that encoded the now-invalid protected stamp
     minimum

3. Refactor:
   - remove the unused helper if nothing else calls it
   - keep the code path linear: text width, remaining width, separator, stamp
     width

4. Verify:
   - focused backend and preview renderer tests
   - `ruff check` on touched files
   - full `pytest -q`

### Acceptance Criteria

- Cap-10-equivalent geometry is validated as fit by automated tests.
- The stamp area for cap-10-equivalent geometry is derived from remaining width,
  not from height/aspect-ratio preallocation.
- The stamp image remains rendered in canonical preview when remaining width is
  nonzero.
- A tighter width below the measured text requirement remains red.

### Execution Result

Implemented in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_signing_preview_renderer.py`
- `tests/unit/test_qt_signing_shell.py`

What landed:

- removed the horizontal `single_line` minimum stamp-width preallocation
- restored the simple reservation sequence for horizontal `single_line`:
  measured text width, remaining width, separator, stamp width
- kept vertical `single_line` and non-`single_line` reservation behavior
  unchanged
- updated stale tests that expected protected stamp width or red validation for
  compact horizontal cases that now fit under text-first sizing
- added cap-10-equivalent backend and preview regressions

Replay against the latest manual capture states after the change:

- Cap 5: `text_area_width_pt = 254`, `stamp_area_width_pt = 4`, no fit issue
- Cap 6: `text_area_width_pt = 254`, `stamp_area_width_pt = 58`, no fit issue
- Cap 7: `text_area_width_pt = 254`, `stamp_area_width_pt = 111`, no fit issue
- Cap 9: `text_area_width_pt = 254`, `stamp_area_width_pt = 105`, no fit issue
- Cap 10: `text_area_width_pt = 254`, `stamp_area_width_pt = 105`, no fit issue

Verification:

- focused backend and preview tests passed: `114 passed`
- full suite passed: `477 passed, 1 warning`
- `ruff check` passed on touched files

## Slice: Improve Horizontal Single-Line Stamp Vertical Scaling

### Triggering Observation

The next manual harness run showed that horizontal `single_line` left/right
stamps were scaling in width after the text-first change, but still looked too
tall for the available vertical lane. Multi-line cases were not exercised in
that run, so this slice is intentionally limited to horizontal `single_line`.

Latest harness evidence:

- Cap 7 and Cap 8 are green `single_line/left` cases.
- Their backend lane is `stamp_area_width_pt = 117` and
  `stamp_area_height_pt = 21`.
- Before this slice, the fitted stamp content for the cap-7/cap-8 geometry was
  `81 x 19 pt`, leaving only about one point of top/bottom breathing room.
- The PDF/canonical analysis render and GUI preview were consistent enough to
  show this is a shared fit-policy issue, not a preview-only mismatch.

### Requirements

- Keep the change in the shared sizing path used by signed output and canonical
  preview.
- Do not change validation thresholds.
- Do not alter vertical `top/bottom` single-line behavior.
- Do not alter multi-line behavior until a manual run exercises those cases.
- Base the additional vertical shrink on existing border-safe spacing rather
  than a new magic width or height threshold.

### TDD Plan

1. Red:
   - add a backend layout regression for the cap-7/cap-8 geometry proving the
     horizontal stamp fit height keeps a larger internal vertical gutter
   - add a Qt preview max-size regression for the same geometry

2. Green:
   - add a shared helper that returns the horizontal single-line vertical inset
     as `max(content_inset, border_safe_inset)`
   - apply that helper to backend stamp fitting
   - apply the same helper to `_preview_stamp_max_size`

3. Verify:
   - focused backend tests
   - focused Qt preview sizing tests
   - `ruff check` on touched files
   - full suite before commit

### Execution Result

Implemented in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_qt_signing_shell.py`

What landed:

- horizontal `single_line` stamps now use a vertical inset equal to the existing
  border-safe inset when that is larger than the content inset
- backend and Qt preview sizing use the same helper
- cap-7/cap-8 geometry now fits stamp content at `71 x 17 pt` instead of
  `81 x 19 pt` inside the same `117 x 21 pt` stamp lane

Verification so far:

- focused backend regressions passed
- focused Qt preview sizing regressions passed
- focused backend/Qt/preview renderer suite passed: `175 passed`
- full suite passed: `480 passed, 1 warning`
- `ruff check` passed on touched files

## Slice: Accept Horizontal Single-Line Short-Height Ink Fit

### Triggering Observation

Cap 6 has substantial horizontal room for a left-positioned image stamp, but the
preview suppresses the stamp and validation remains red. The artifact data
shows:

- layout: `single_line/left`
- rectangle: `423.43 pt x 24.068 pt`
- measured text box: `254 pt x 18 pt`
- reserved text/stamp lane height: `16 pt`
- reserved stamp lane width: `155 pt`
- rendered GUI text ink: `13 px` high

The failure is caused by nominal text height exceeding the lane by 2 pt. That
prevents the canonical preview from showing the stamp at all, so the stamp never
gets the opportunity to shrink vertically into the available lane.

### Requirements

- Keep the horizontal stamp visible when the only nominal overflow is text
  height and the stamp still has a real rendered lane.
- Allow backend validation to use the existing rendered-ink fallback for
  horizontal image stamps, not just top/bottom image stamps.
- Do not let rendered-ink fallback pass cases where no real horizontal stamp
  lane remains.
- Keep the existing wide-overflow guard so genuinely collapsed text lanes still
  fail.

### Execution Result

Implemented in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/application/signing_preview_renderer.py`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_signing_preview_renderer.py`

What landed:

- `_single_line_rendered_ink_fits_reservation` now supports horizontal
  left/right image stamps
- the rendered-ink fallback for horizontal image stamps requires both a real
  stamp area and rendered stamp bounds, so zero-lane stamp cases still fail
- canonical preview no longer suppresses horizontal stamps solely because the
  nominal text box is taller than the lane
- cap-6-equivalent geometry is covered by backend validation and canonical
  preview tests

Verification:

- focused cap-6 regressions passed
- focused backend/preview/Qt suite passed: `177 passed`
- full suite passed: `482 passed, 1 warning`
- `ruff check` passed on touched files

## Slice: Align Horizontal Single-Line Text By Visible Ink

### Triggering Observation

Manual caps 5 and 6 improved stamp scaling, but the right-side whitespace after
the rightmost text remained visibly larger than the behavior already achieved
for `single_line/top` and `single_line/bottom`.

Latest capture evidence:

- Cap 5 is green at `296.96 pt x 22.53 pt`.
- The backend reserves `text_area_width_pt = 254` and
  `stamp_area_width_pt = 29`.
- The canonical structural text box reaches near the right border, but rendered
  glyph ink ends significantly inside that nominal box.
- Width-ladder probes showed that reducing the text reservation width just
  clips/moves the left side; it does not move the rightmost glyph ink closer to
  the border.
- Applying an optical shift equal to the text lane height moves the glyph ink to
  within a few pixels of the right border without changing validation
  thresholds.

There is also a harness artifact issue: the interactive text-debug overlay can
draw 1x analysis bounds on the zoomed preview image, exaggerating the apparent
right whitespace. The diagnostics should use the same analysis image/bounds that
produced the detected text ink.

### Requirements

- Do not reduce the text lane width as a proxy for visible glyph width.
- Do not add a hard-coded pixel or point threshold.
- For horizontal `single_line` image stamps, let the border-facing text edge
  optically bleed by the existing text lane height.
- Keep left/right symmetric:
  - stamp on left: right text margin gets the optical bleed
  - stamp on right: left text margin gets the optical bleed
- Keep top/bottom and non-single-line behavior unchanged.
- Make the harness text debug overlay use the analysis image and analysis bounds
  when those are the source of text detection.

### TDD Plan

1. Red:
   - add backend layout tests for left and right horizontal `single_line` image
     stamps proving the border-facing margin is adjusted by the text lane height
   - add a canonical preview raster test proving cap-5-equivalent rendered text
     ink lands near the right border

2. Green:
   - apply the optical bleed in `_layout_reservation_for_template`
   - update interactive harness text-debug overlay image/bounds selection

3. Verify:
   - focused backend and canonical preview tests
   - focused harness tests
   - `ruff check`
   - full suite

### Execution Result

Implemented in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/presentation/qt/phase3_harness.py`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_signing_preview_renderer.py`

What landed:

- horizontal `single_line` image-stamp text now optically bleeds toward the
  border-facing edge by the text lane height
- the bleed is disabled when border-safe inset expands the normal edge margin,
  so thick-border safety remains intact
- cap-5-equivalent canonical preview raster coverage asserts rendered text ink
  reaches within a few pixels of the right border
- the interactive harness text-debug overlay now uses the analysis image and
  analysis bounds when those produced the detected text ink

Verification:

- focused backend/preview/harness suites passed: `214 passed, 1 warning`
- full suite passed: `485 passed, 1 warning`
- `ruff check` passed on touched files

## Investigation: Horizontal Single-Line Stamp/Text Separator

### Triggering Observation

After visible-ink right-edge alignment, the right-side border spacing for
`single_line/left` is correct, but manual caps still show more whitespace than
desired between the stamp image and the first visible text glyph. The user asked
whether the gap could be reduced to roughly 20% of its current size.

The investigation showed two separate contributors:

- The explicit layout separator is the old `6 pt` left/right gap.
- The larger visible gap is mostly geometric: preserving the right-border ink
  alignment while the rendered text ink is narrower than the available interval
  necessarily leaves space on the stamp-facing side.

Therefore, reducing the whole visible gap to 20% is not possible without one of
these tradeoffs:

- degrade the right-border text alignment that was just fixed
- reduce text size or horizontally scale text
- allow stamp/text overlap

An implementation was attempted that shrank only the explicit separator to 20%
of the existing base gap. The follow-up trace showed that this did not address
the root cause because the dominant whitespace came from the negative
border-facing optical bleed, not from the separator itself.

### Decision

- Do not land the separator-only change.
- Restore the base separator for now so the layout has one simple reservation
  model.
- Address clipped text first; only revisit separator size after the preview can
  no longer validate truncated text.

## Slice: Revert Flawed Horizontal Optical Bleed And Reject Clipped Ink

### Triggering Observation

The next manual run showed that caps 4-8 regressed:

- text on the border-facing edge can run into or past the rectangle border
- caps with a visible stamp can turn green even when text is visibly clipped
- the visible gap between stamp ink and text ink remains large

The trace through the relevant code paths showed why:

- `_layout_reservation_for_template(...)` applied a negative border-facing text
  margin equal to `text_area_height` for horizontal `single_line` image-stamp
  layouts.
- That did not shrink internal whitespace independently. It shifted the whole
  nominal text widget toward the border, which violated the earlier border-safe
  text guard.
- `_single_line_rendered_ink_fits_reservation(...)` then accepted some clipped
  cases because it only checked whether the detected visible ink subset fit
  inside the text area. It did not require the detected ink to preserve the
  reference text ink width/height.
- The uncommitted separator-tightening slice depended on the same flawed
  optical-bleed premise. Reducing the explicit separator by itself cannot fix a
  text widget that is being shifted out of bounds.

### Requirements

- Restore the simple horizontal `single_line` reservation contract:
  text first, base separator second, remaining lane for the stamp.
- Preserve the normal border-facing text margin; do not use negative margins to
  push text toward the border.
- Do not let rendered-ink fallback pass if detected text ink has lost more than
  the same raster tolerances already used by harness diagnostics:
  `3 px` width loss or `1 px` height loss against the reference bounds.
- Keep vertical `single_line`, top/bottom stamp, no-stamp, and non-single-line
  behavior unchanged.
- Leave manual harness artifacts unstaged.

### TDD Plan

1. Red:
   - change the horizontal left/right reservation tests to require normal
     border-facing margins instead of negative optical-bleed margins
   - add a rendered-ink fallback test that simulates a cap-6-style clipped
     visible subset and requires rejection
   - change the canonical preview test to assert a positive border-facing text
     guard instead of near-border optical alignment

2. Green:
   - remove the negative-margin optical bleed from
     `_layout_reservation_for_template(...)`
   - remove the uncommitted horizontal separator helper and restore the base
     separator
   - add reference ink loss checks to
     `_single_line_rendered_ink_fits_reservation(...)`

3. Verify:
   - focused backend horizontal `single_line` tests
   - focused preview renderer border-guard test
   - focused backend/harness/preview suites
   - `ruff check`
   - full suite if focused verification is clean

### Execution Result

Implemented in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_signing_preview_renderer.py`

What changed:

- removed the horizontal `single_line` negative border-facing margin
- restored the base horizontal separator instead of the attempted 20% separator
- added reference ink loss rejection for horizontal `single_line` image-stamp
  rendered-ink fallback
- changed tests so the desired invariant is a positive border-facing guard and
  rejection of cap-6-style clipped visible ink

Verification:

- focused horizontal/rendered-ink backend tests passed: `21 passed`
- focused preview renderer tests passed: `2 passed`
- focused backend/preview/harness suites passed: `215 passed, 1 warning`
- full suite passed: `486 passed, 1 warning`
- `ruff check` passed on touched files

## Slice: Add Layout Safety Invariants Before Further Visual Tuning

### Triggering Observation

The reverted horizontal `single_line` optical-bleed slice looked plausible
because it attacked a real visual defect: rendered text ink had excessive
border-facing whitespace even though the structural text box was already fully
reserved. The implementation failed because it moved the whole text widget
outside the safe layout box. That violated the border guard, increased
stamp-facing whitespace, and exposed a validation fallback that could pass a
clipped visible subset.

Future preview/PDF parity work needs explicit invariant tests before any more
appearance tuning. The invariants should make it hard to accidentally trade one
edge for another, or to let validation green-light a clipped render.

### Requirements

- Add automated tests that encode non-negotiable layout invariants for
  horizontal `single_line` image-stamp layouts:
  - border-facing text margin must remain non-negative and at least the active
    border-safe inset
  - stamp-facing text margin must equal `stamp_area + separator + edge_margin`
    and must not silently grow because of border-facing alignment
  - stamp/text rectangles must not overlap
  - the rendered text fallback must reject visible ink that loses more than the
    reference raster tolerance
- Add a small helper or assertion utility in tests only if it reduces repeated
  geometry arithmetic. Do not add production abstraction solely for tests.
- Extend canonical preview raster coverage to check both text edges in the same
  test case, not just the edge being tuned.
- Keep the tolerance vocabulary aligned with the existing harness diagnostics:
  `3 px` width loss and `1 px` height loss for reference ink preservation.
- Update documentation in this ExecPlan to require a "cannot override" section
  for any future fit relaxation or optical tuning slice.
- Do not modify generated harness artifacts as part of this slice.

### TDD Plan

1. Red:
   - add backend reservation tests for `single_line/left` and
     `single_line/right` with image stamps that assert both edge margins and
     separator-derived geometry
   - add canonical preview tests that detect rendered text ink and assert:
     border-facing distance is positive, stamp-facing distance is positive, and
     text ink does not overlap stamp bounds
   - add or expand rendered-ink fallback tests so a clipped current render fails
     even when the detected subset fits inside the text area

2. Green:
   - keep production layout simple unless tests expose a real invariant gap
   - if existing production logic already satisfies the invariants, land only
     tests and documentation
   - if a failure appears, fix the smallest production path that violates the
     invariant rather than adding a second branch or special-case threshold

3. Refactor:
   - remove duplicated test arithmetic only after the tests are proving the
     right behavior
   - avoid introducing any new layout mode, threshold ladder, or alternate fit
     path unless the invariant tests prove the existing model cannot express the
     behavior

4. Verify:
   - focused backend reservation and rendered-ink fallback tests
   - focused canonical preview renderer tests
   - focused `phase3_harness` tests that cover text clipping diagnostics
   - `ruff check` on touched files
   - full `pytest` before declaring the slice complete

### Future ExecPlan Rule

Any future slice that relaxes fit validation, changes optical alignment, or
modifies reserved layout geometry must include a "Cannot Override" subsection
before implementation. It must explicitly state how the change preserves:

- non-negative border-safe margins
- stamp/text non-overlap
- full-reference text ink preservation
- preview/PDF parity instrumentation
- simple single-path layout logic without arbitrary split boundaries

### Execution Result

Implemented in:

- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_signing_preview_renderer.py`
- `tests/unit/test_phase3_harness.py`

What changed:

- added horizontal `single_line` image-stamp reservation invariant tests for
  left/right stamp positions and normal/thick borders
- added canonical preview raster tests that check both border-facing and
  stamp-facing text distances, plus stamp/text non-overlap
- added harness text-edge diagnostics coverage for horizontal border-edge
  reference ink loss
- production layout code did not need to change; the current implementation
  already satisfies these invariants after the previous regression fix

Verification:

- focused backend invariant tests passed: `7 passed`
- focused preview invariant tests passed: `3 passed`
- focused harness clipping diagnostics tests passed: `2 passed`
- focused backend/preview/harness suites passed: `222 passed, 1 warning`
- full suite passed: `493 passed, 1 warning`
- `ruff check` passed on touched files

## Slice: Add Distilled Manual Cap 4-8 Replay Fixture

### Triggering Observation

The safety invariant slice covered the class of regression, but it still did not
preserve the exact manual harness ladder that exposed the bug. Caps 4-8 should
be reproducible without another GUI pass and without committing bulky generated
artifact images.

### Requirements

- Create a small, stable fixture that captures the manual cap 4-8 geometry:
  label, width, height, and expected backend readiness.
- Keep the fixture self-contained by generating a local stamp image in tests
  instead of depending on the user's local GIF path or generated artifacts.
- Replay the fixture through backend validation so the red/green ladder remains
  stable:
  - caps 4 and 5 reject
  - caps 6, 7, and 8 accept
- Replay the same fixture through canonical preview rendering and assert the
  geometry invariants that matter for this failure mode:
  - text ink keeps a positive border-facing distance
  - text ink does not overlap stamp ink
  - when stamp ink exists, text keeps a positive stamp-facing distance
- Do not stage or depend on `artifacts/phase3_harness_capture*`.

### Execution Result

Implemented in:

- `tests/fixtures/phase3_horizontal_single_line_manual_replay.json`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_signing_preview_renderer.py`

What changed:

- added a distilled JSON replay fixture for manual caps 4-8
- added backend validation replay coverage for the captured ladder
- added canonical preview geometry replay coverage using the same cases
- kept the fixture small and independent of generated harness artifacts

Verification:

- focused replay/invariant backend tests passed: `6 passed`
- focused replay/invariant preview tests passed: `3 passed`
- focused backend/preview/harness suites passed: `224 passed, 1 warning`
- full suite passed: `495 passed, 1 warning`
- `ruff check` passed on touched Python files

## Slice: Require Visible Horizontal Stamps And Fix Ink Reference Coordinates

### Triggering Observation

The next manual run showed three separate issues:

- Cap 4 validated green even though a left image stamp was selected, the stamp
  had no visible reserved lane, and no stamp appeared.
- Caps 7 and 8 looked visually acceptable but validated red in short-height
  horizontal `single_line` cases.
- Harness diagnostics reported very large left-stamp text width loss that did
  not match the visible preview.

### Cannot Override

- A selected horizontal image stamp must have non-zero reserved width and
  height.
- Rendered-ink fallback may relax structural text-box height only when the
  current rendered ink still matches a roomy rendered reference.
- Reference text bounds passed to raster detection are absolute preview
  coordinates and must be converted into crop-local coordinates before
  filtering candidate pixels.
- The fix must not reintroduce negative text margins, stamp/text overlap, or a
  second layout branch for visual tuning.

### Requirements

- Reject horizontal `single_line` layouts with a selected stamp image when the
  reserved stamp band has zero width or height.
- Preserve the existing non-single-line zero-stamp-band rejection.
- Compare horizontal `single_line` fallback against a roomy rendered reference
  image, not structural text bounds.
- Allow the small observed `2 px` rendered-height delta between compact and
  roomy horizontal references while keeping width preservation strict.
- Fix `text_raster_analysis` so absolute reference envelopes are translated
  into crop-local coordinates.
- Add tests covering the absolute/crop coordinate conversion and the latest
  cap-4, cap-7, and cap-8 replay outcomes.

### Execution Result

Implemented in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `src/foliaseal/application/text_raster_analysis.py`
- `tests/fixtures/phase3_horizontal_single_line_manual_replay.json`
- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_phase3_harness.py`
- `tests/unit/test_signing_preview_renderer.py`
- `tests/unit/test_text_raster_analysis.py`

What changed:

- horizontal `single_line` image-stamp validation now rejects zero-size stamp
  lanes instead of allowing green validation with no visible stamp
- rendered-ink fallback now compares compact horizontal cases against a roomy
  rendered reference and accepts cap-7/cap-8-style short-height cases when ink
  is preserved
- text raster analysis now treats reference bounds as absolute preview
  coordinates and converts them to crop-local coordinates before envelope
  filtering
- the manual replay fixture now includes the latest cap-4/cap-7/cap-8 geometry

Verification:

- focused backend/rendered-ink/replay tests passed: `8 passed`
- focused preview replay tests passed: `4 passed`
- focused harness text-edge diagnostics tests passed: `5 passed`
- focused backend/preview/harness/raster suites passed: `225 passed, 1 warning`
- full suite passed: `496 passed, 1 warning`
- `ruff check` passed on touched files

### Remaining Decision Point

The fresh cap-5/cap-6 spacing complaint is now separated from validation and
instrumentation correctness. The next slice should decide whether horizontal
`single_line` should reserve text width from rendered ink rather than structural
text-box width. That change may improve stamp scaling, but it affects signed PDF
appearance and preview/PDF parity, so it should be implemented only with a
dedicated ExecPlan and parity tests.

## Slice: Rendered-Ink-Informed Horizontal Single-Line Reservation

### Triggering Observation

After fixing zero-stamp validation, rendered-ink fallback, and reference
coordinate handling, the remaining manual issue is visual efficiency:

- Cap 5 has a left stamp and green validation, but the right edge of the border
  is meaningfully farther from the rightmost glyphs than in `single_line/top`
  or `single_line/bottom`.
- Cap 6 has a right stamp and green validation, but the gap between the
  rightmost glyphs and the left edge of the stamp is larger than necessary.
- Cap 7 and Cap 8 were validation issues before the previous slice; after the
  rendered-reference fallback fix, they should validate based on preserved ink.
- The current horizontal reservation still uses structural text-box width
  (`254 pt` in the observed cases), while the rendered glyph ink is materially
  narrower. That structural slack reduces the available stamp lane and makes
  the stamp smaller than necessary.

The tempting simple fix is to reserve only the rendered ink width. That is not
safe by itself. The actual PDF signature is written through pyHanko text boxes
and layout margins, not by copying preview pixels. Font side bearings and
line-box whitespace mean the glyph ink does not start at the text-box origin.
If reservation uses raw ink width but PDF placement still aligns the structural
text box, preview and signed PDF output can diverge or clip.

### Cannot Override

- Do not reintroduce negative margins or optical bleed outside the existing safe
  box.
- Do not size the text lane from raw rendered-ink width alone.
- Do not let the preview and signed PDF independently interpret the horizontal
  text translation.
- Preserve selected-stamp visibility: horizontal image-stamp layouts must retain
  a real non-zero stamp lane.
- Preserve full-reference text ink: validation may not pass if the current
  render loses glyph ink relative to a roomy rendered reference.
- Preserve stamp/text non-overlap and positive border-facing/stamp-facing text
  distances.
- Keep a single shared reservation/translation model consumed by preview,
  backend validation, and signed PDF generation.

### Decision

Proceed with rendered-ink-informed reservation, but model the ink envelope and
translation explicitly.

Do not implement:

- `text_lane_width = rendered_ink_width`
- another hard-coded optical shift
- a layout split based on an arbitrary rectangle width threshold

Implement instead:

- measure a roomy rendered reference for horizontal `single_line` image-stamp
  layouts
- capture both ink size and ink offset within the structural text box
- reserve a tighter text lane using the ink width plus named safe padding
- translate the structural text box inside that lane so the glyph ink lands at
  the same intended offset in preview and signed PDF output

### Proposed Model

Introduce a small shared model for horizontal `single_line` ink reservation,
owned by the application layer and used by both preview and signing paths:

```python
@dataclass(frozen=True)
class HorizontalSingleLineInkReservation:
    lane_width_pt: int
    ink_width_pt: int
    ink_height_pt: int
    ink_left_offset_pt: int
    ink_right_slack_pt: int
    border_facing_padding_pt: int
    stamp_facing_padding_pt: int
```

The model should be constructed only when all of these are true:

- layout template is `single_line`
- stamp position is `left` or `right`
- a visible image stamp is selected
- a roomy rendered reference can be measured

Fallback behavior:

- If the rendered reference cannot be measured, use the current structural
  reservation path and keep validation conservative.
- Do not guess a tighter lane without a rendered reference.

### Translation Rules

The reservation model must describe both width and translation:

- `lane_width_pt = ink_width_pt + stamp_facing_padding_pt + border_facing_padding_pt`
- for a left stamp, align the text ink's border-facing edge to
  `border_facing_padding_pt` inside the text lane
- for a right stamp, mirror the same rule
- derive the structural text-box margin adjustment from the measured ink offset:
  the text box may move inside the lane, but the lane itself must stay inside
  the safe border box
- never let the translated structural box cause stamp/text ink overlap or
  border contact

The PDF writer must consume the same translation model. The signed appearance
cannot simply receive a narrower text width while leaving pyHanko alignment to
place the structural text box as before.

### Implementation Plan

1. Add reference measurement support.
   - Add a shared helper that renders or reuses a roomy canonical reference for
     horizontal `single_line` image-stamp layouts.
   - Measure rendered text ink bounds and structural text bounds from that
     reference.
   - Convert pixel measurements to point-space using the canonical preview
     scale for the signature rectangle.
   - Keep the helper deterministic and cacheable by the existing rendered-ink
     cache key inputs.

2. Add reservation model computation.
   - Compute `ink_width_pt`, `ink_left_offset_pt`, and `ink_right_slack_pt`.
   - Choose named padding from existing layout concepts:
     - initial proposal: `border_facing_padding_pt = edge_margin`
     - initial proposal: `stamp_facing_padding_pt = edge_margin`
   - Clamp `lane_width_pt` so it never exceeds the current structural
     reservation width and never drops below the measured ink plus padding.
   - If clamping would remove required padding, reject or fall back to
     structural reservation.

3. Apply reservation to `_layout_reservation_for_template`.
   - Add an optional reservation override parameter rather than adding a second
     independent layout branch.
   - Keep the existing text-first/separator/stamp-remainder sequence.
   - Replace only the horizontal `single_line` text reservation width with the
     ink-informed lane width when the model is available.

4. Apply translation to preview and PDF signing.
   - Extend the returned reservation/layout data with enough information to
     translate the structural text box inside the reserved lane.
   - Ensure `signing_preview_renderer` and `_build_stamp_style` consume the
     same translation data.
   - Do not let the GUI-only live preview invent its own placement. It should
     either use canonical rendering or the same application-layer reservation
     and translation.

5. Preserve validation correctness.
   - Keep zero horizontal stamp-lane rejection.
   - Keep rendered-reference ink preservation checks.
   - Add checks that the translated ink remains inside the border-safe box and
     does not overlap stamp ink.

### TDD Plan

1. Red: backend reservation.
   - Add cap-5/cap-6 replay cases proving the horizontal text lane becomes
     narrower than structural reservation while preserving positive
     border-facing and stamp-facing distances.
   - Add left/right symmetry tests.
   - Add a fallback test proving missing reference measurement keeps structural
     reservation.

2. Red: preview geometry.
   - Add canonical preview tests proving the stamp grows for cap-5/cap-6-style
     cases while text ink remains inside the border and away from the stamp.
   - Assert no negative margins and no stamp/text overlap.

3. Red: signed PDF parity.
   - Add or extend signed-output comparison tests so the actual PDF signature
     uses the same horizontal ink placement as the preview.
   - The test should compare text ink bounds, stamp ink bounds, and rounded
     border presence in normalized preview/PDF crops.

4. Green.
   - Implement the shared reference measurement and reservation model.
   - Wire it through backend validation, canonical preview, GUI preview if
     needed, and PDF stamp style construction.
   - Keep implementation single-path; avoid one-off cap-specific conditions.

5. Refactor.
   - Move shared math into narrowly named helpers only after the tests are
     passing.
   - Document why raw ink width alone is not used and why translation is
     required for PDF output.

6. Verify.
   - focused backend reservation tests
   - focused canonical preview tests
   - focused signed-output parity tests
   - focused harness tests for replay artifacts
   - full parity matrix if available
   - `ruff check`
   - full `pytest`

### Acceptance Criteria

- Cap-5/cap-6-style horizontal cases allocate more stamp width than structural
  reservation without losing or clipping text ink.
- Cap-4 remains red when the selected stamp has no real lane.
- Cap-7/cap-8 remain green when rendered ink is preserved.
- Preview and actual signed PDF match for text placement, stamp placement, and
  border shape.
- The implementation has no negative margins, no arbitrary width threshold, and
  no separate preview-only placement rule.

### Issue #41 Execution Result: Shared Horizontal Ink Reservation Model

Implemented with TDD in:

- `src/foliaseal/application/horizontal_signature_reservation.py`
- `src/foliaseal/application/__init__.py`
- `tests/unit/test_horizontal_signature_reservation.py`

What landed:

- added `HorizontalSingleLineInkReservation`
- added `build_horizontal_single_line_ink_reservation(...)`
- limited construction to horizontal `single_line` layouts with a visible image
  stamp
- preserved conservative fallback behavior by returning `None` when reference
  geometry is missing, outside the structural text box, overwide after named
  padding, or otherwise unsafe
- exported the model/helper from the application package for later backend,
  preview, and signed-PDF wiring

No production layout behavior is wired to the model yet. That is deliberate:
issue #41 establishes the shared contract only, so later slices can consume it
without mixing model creation with fit-policy changes.

Verification:

- `pytest -q tests/unit/test_horizontal_signature_reservation.py`
- `pytest -q tests/unit/test_horizontal_signature_reservation.py tests/unit/test_phase3_signing_backend.py`
- `python -m ruff check src/foliaseal/application/horizontal_signature_reservation.py src/foliaseal/application/__init__.py tests/unit/test_horizontal_signature_reservation.py`

### Issue #42 Execution Result: Roomy Rendered Reference Measurement

Implemented with TDD in:

- `src/foliaseal/application/horizontal_signature_reservation.py`
- `src/foliaseal/application/__init__.py`
- `tests/unit/test_horizontal_signature_reservation.py`

What landed:

- added `HorizontalSingleLineRenderedReference`
- added `measure_horizontal_single_line_rendered_reference(...)`
- the helper is limited to horizontal `single_line` layouts with a visible image
  stamp
- the helper creates a deterministic roomy reference rectangle, renders through
  the canonical preview engine, detects rendered glyph ink from that reference,
  and returns both structural and rendered-ink bounds
- the payload includes pixel bounds, point-space bounds, preview size, and the
  `px_to_pt` scale needed by later reservation/translation slices
- unavailable or contradictory measurement returns `None` so later consumers can
  fall back conservatively

No backend fit decision, preview placement, or signed-PDF placement uses this
measurement yet. That wiring belongs to the next dependent issues.

Verification:

- `pytest -q tests/unit/test_horizontal_signature_reservation.py`
- `pytest -q tests/unit/test_horizontal_signature_reservation.py tests/unit/test_signing_preview_renderer.py`
- `python -m ruff check src/foliaseal/application/horizontal_signature_reservation.py src/foliaseal/application/__init__.py tests/unit/test_horizontal_signature_reservation.py`
- `pytest -q`

### Issue #43 Guidance: Backend Validation Uses Reservation, Not Placement

Code-path review before starting issue #43 found a boundary that must remain
explicit:

- `_build_stamp_style(...)` currently computes `_SignatureLayoutReservation` and
  then returns pyHanko `background_layout` / `inner_content_layout` objects.
- Those returned layout objects are also the signed-PDF placement path.
- Therefore issue #43 must not change the returned stamp style placement or
  pyHanko margins. That belongs to issue #45 after canonical preview translation
  is addressed in issue #44.

Issue #43 should instead add a validation-only reservation path:

- compute the existing structural reservation first
- when the layout is horizontal `single_line` with a visible image stamp, attempt
  to build a `HorizontalSingleLineInkReservation` from the roomy rendered
  reference
- create an ink-informed validation reservation by replacing only the text lane
  width used by the fit gate
- keep the existing text-first / separator / stamp-remainder sequence
- require the resulting reservation to keep a non-zero stamp lane
- preserve the rendered-reference ink preservation check before accepting a
  layout that structural validation rejected
- if reference measurement or ink reservation construction fails, use the
  structural reservation and keep the current conservative behavior

The tests for issue #43 should prove:

- cap-5/cap-6-style geometry produces a validation reservation with a narrower
  text lane and wider stamp lane than the structural reservation
- left and right stamp positions mirror correctly at the reservation level
- missing/unsafe rendered reference data returns the structural reservation
- cap-4-style zero-stamp-lane geometry remains rejected
- no production preview/PDF placement contract changes are asserted in this
  slice

### Issue #43 Execution Result: Backend Validation Consumes Ink Reservation

Implemented with TDD in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

What landed:

- added `_horizontal_single_line_ink_validation_reservation(...)`
- added `_horizontal_single_line_ink_reservation_for_stamp_text(...)`
- `_build_stamp_style(...)` now computes the normal structural reservation, then
  computes an ink-informed validation reservation only for horizontal
  `single_line` image-stamp layouts when a roomy rendered reference is available
- validation uses the ink-informed reservation for the fit gate, but the
  returned pyHanko layout objects still come from the structural reservation
- missing rendered-reference data falls back to structural validation
- the existing rendered-ink preservation fallback remains in place for cases
  where validation still fails

Important boundary:

- This issue deliberately does not change canonical preview placement or signed
  PDF placement. Those remain issue #44 and issue #45. Until those land, this
  slice should be treated as backend-validation plumbing, not as a manual-harness
  ready visual parity fix.

Verification:

- `pytest -q tests/unit/test_phase3_signing_backend.py -k "ink_validation_reservation or backend_validation_uses_ink_reference or backend_validation_falls_back_without_ink_reference"`
- `pytest -q tests/unit/test_phase3_signing_backend.py`
- `python -m ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py`
- `pytest -q`

### Issue #44 Guidance: Canonical Preview Must Avoid Reference-Render Recursion

Code-path review before starting issue #44 found one additional constraint:

- `measure_horizontal_single_line_rendered_reference(...)` currently obtains its
  reference by calling `render_canonical_signature_preview(...)`.
- If canonical preview rendering starts consuming that helper unconditionally,
  the reference render can recursively request another reference render.

Issue #44 must therefore add an explicit bypass for reference renders, for
example:

- a private/internal flag on `render_canonical_signature_preview(...)` or
  `_canonical_preview_layout(...)` that disables ink-informed reservation while
  measuring a roomy reference
- or a separate structural-only layout helper used by the measurement path

The preview slice should also keep these boundaries clear:

- It may change canonical preview reservation and structural bounds.
- It may not change signed-PDF placement; that remains issue #45.
- It should not remove the existing stamp-suppression guard unless the new
  ink-informed reservation proves a real non-zero stamp lane.
- It should reuse the same application-layer reservation construction as the
  backend, including fallback to structural layout when reference measurement is
  unavailable.
- The first preview tests should compare a structural render to an
  ink-informed render and assert that the stamp lane grows while rendered text
  ink remains inside the border and does not overlap the stamp.

Additional detail found during implementation:

- The canonical preview structural Y bounds can disagree with rendered glyph
  ink Y bounds because they describe text-box structure, not raster ink.
- The shared reservation model only uses horizontal ink offsets and slack.
- Therefore reservation construction should require horizontal containment and
  rendered ink height preservation, but should not reject solely because the
  raster ink Y coordinate falls outside the structural Y box.

### Issue #44 Execution Result: Canonical Preview Uses Ink Reservation

Implemented with TDD in:

- `src/foliaseal/application/signing_preview_renderer.py`
- `src/foliaseal/application/horizontal_signature_reservation.py`
- `tests/unit/test_signing_preview_renderer.py`
- `tests/unit/test_horizontal_signature_reservation.py`

What landed:

- `render_canonical_signature_preview(...)` now has an internal
  `use_horizontal_ink_reservation` switch
- default canonical preview rendering uses the ink-informed text lane for
  horizontal `single_line` image-stamp layouts when measurement succeeds
- rendered-reference measurement explicitly disables ink reservation to avoid
  recursive reference rendering
- structural-only preview rendering remains available for regression tests and
  reference measurement
- the canonical preview stamp lane grows relative to the structural reservation
  while rendered text ink remains inside the border and does not overlap the
  stamp
- reservation construction now ignores structural Y offset disagreement while
  still requiring horizontal containment and rendered-height preservation

Important boundary:

- Signed-PDF placement is still unchanged. Issue #45 must wire equivalent
  translation into the PDF signing path before manual preview/PDF parity should
  be considered complete.

Verification:

- `pytest -q tests/unit/test_signing_preview_renderer.py -k "uses_ink_reservation"`
- `pytest -q tests/unit/test_horizontal_signature_reservation.py`
- `pytest -q tests/unit/test_horizontal_signature_reservation.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py`
- `pytest -q tests/unit/test_qt_signing_shell.py`
- `python -m ruff check src/foliaseal/application/horizontal_signature_reservation.py src/foliaseal/application/signing_preview_renderer.py tests/unit/test_horizontal_signature_reservation.py tests/unit/test_signing_preview_renderer.py`
- `pytest -q`

### Issue #45 Guidance: Signed PDF Style Must Use The Same Ink Lane As Preview

Code-path review before starting issue #45 found the remaining mismatch:

- `_build_stamp_style(...)` now computes an ink-informed reservation for
  validation, but still returns `background_layout` and `inner_content_layout`
  from the structural reservation.
- `signing_preview_renderer._canonical_preview_layout(...)` now uses the
  ink-informed lane in the returned canonical preview style.
- Therefore preview and signed PDF can still diverge even though both validation
  and preview are improved.

Issue #45 should:

- compute one optional ink-informed layout reservation in `_build_stamp_style`
  after structural measurement
- use that reservation for validation and for the returned signed-PDF
  `inner_content_layout`
- use the same text lane width when computing signed-PDF `background_layout`, so
  the stamp lane matches canonical preview
- keep the structural reservation as the conservative fallback when reference
  measurement or reservation construction fails
- avoid adding a separate signed-PDF-only translation rule; signed PDF and
  canonical preview should both interpret the lane-width reservation the same
  way

Tests should prove:

- `_build_stamp_style(...)` returns a wider stamp lane and narrower text lane for
  horizontal `single_line` image-stamp layouts when an ink reference is
  available
- missing reference measurement preserves the previous structural margins
- canonical preview and signed-PDF style margins match for the same
  cap-5/cap-6-style input

### Issue #45 Execution Result: Signed PDF Style Uses Ink Reservation

Implemented with TDD in:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

What landed:

- `_build_stamp_style(...)` now computes the optional ink-informed reservation
  once and uses it for both validation and returned signed-PDF layout
- signed-PDF `inner_content_layout` now uses the ink-informed text lane when a
  horizontal `single_line` image-stamp reference is available
- signed-PDF `background_layout` is computed with the same ink-informed text
  lane width so the stamp lane matches canonical preview
- missing reference measurement still falls back to the previous structural
  margins
- tests assert signed-PDF style margins and canonical preview margins match for
  the same cap-5/cap-6-style input

Verification:

- `pytest -q tests/unit/test_phase3_signing_backend.py -k "pdf_layout or falls_back_to_structural_horizontal_layout or matches_canonical_preview"`
- `pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py tests/unit/test_horizontal_signature_reservation.py`
- `python -m ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py`
- `pytest -q`

### Issue #46 Guidance: Parity Matrix Must Cover Horizontal Single-Line Ladder

Code-path and asset review before starting issue #46 found that the existing
`signed_preview_parity_matrix.json` covers layout families and stamp positions,
but it only has one relaxed horizontal `single_line` image-stamp case. It does
not explicitly encode the cap-4-through-cap-8 manual replay ladder that drove
the ink-reservation work.

Issue #46 should:

- extend the signed preview/PDF parity manifest with horizontal `single_line`
  image-stamp scenarios derived from
  `tests/fixtures/phase3_horizontal_single_line_manual_replay.json`
- include both left and right stamp positions
- include compact accepted cases near the minimum validated size, not only roomy
  cases
- keep these as expected-success parity cases; the intentional rejection ladder
  remains in the signed fit rejection manifest
- preserve strict signed matrix expectations:
  - every scenario signs successfully
  - zero preview/output comparison failures
  - zero annotation-rect mismatches

Tests should prove:

- the parity manifest contains the horizontal manual replay scenarios by name
- those scenarios use `single_line`, horizontal stamp positions, visible image
  stamps, and expected success
- the manifest acceptance expectation scenario count matches the scenario list
  exactly after adding the new cases

### Issue #46 Execution Result: Horizontal Single-Line Parity Matrix Cases

Implemented with TDD in:

- `artifacts/preview_sweep_assets/signed_preview_parity_matrix.json`
- `tests/unit/test_phase3_harness.py`

What landed:

- extended the signed preview/PDF parity manifest from 18 to 23 expected-success
  scenarios
- added five horizontal `single_line` image-stamp scenarios derived from the
  manual replay ladder:
  - `single_line_left_stamp_manual_replay_06_minimum_success`
  - `single_line_left_stamp_manual_replay_07_success`
  - `single_line_left_stamp_manual_replay_08_roomy_success`
  - `single_line_right_stamp_manual_replay_07_short_height_success`
  - `single_line_left_stamp_manual_replay_08_short_height_success`
- included both left and right stamp positions
- kept the matrix strict: every scenario is expected to sign successfully and
  the manifest requires zero preview/output comparison failures
- added manifest tests proving the horizontal replay ladder is present and that
  `acceptance_expectations.scenario_count` exactly matches the scenario list

Verification:

- `pytest -q tests/unit/test_phase3_harness.py -k "signed_preview_parity_manifest"`
- `pytest -q tests/unit/test_phase3_harness.py`
- `python -m json.tool artifacts/preview_sweep_assets/signed_preview_parity_matrix.json`
- `python -m ruff check tests/unit/test_phase3_harness.py`
- `pytest -q`

## Follow-up Slice: Single-Line Left Stamp-Facing Gap

### Goal

Fix the current manual-harness single-line-left appearance issue without
regressing the border-facing text fit that is now working.

The latest harness run shows:

- Cap 4: validation green, right text-to-border gap is `4 px`, but stamp-to-text
  glyph gap is `16 px`.
- Cap 5: validation green, right text-to-border gap is `4 px`, but stamp-to-text
  glyph gap is `13 px`.
- Cap 6: validation green, right text-to-border gap is `4 px`, but stamp-to-text
  glyph gap is `26 px`.
- Cap 10 is an intentional fail case and must remain red.

This is now an appearance/stamp-allocation problem, not a validation problem.
The right-side text guard is good; the left/stamp-facing gap is too large, which
makes the text consume horizontal space too early and shrinks the stamp sooner
than necessary.

### Relevant Code Path

- Horizontal single-line layout split:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_layout_reservation_for_template(...)`
- Horizontal rendered-ink reservation:
  - `src/foliaseal/application/horizontal_signature_reservation.py`
  - `build_horizontal_single_line_ink_reservation(...)`
- Single-line left optical text placement:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_apply_horizontal_single_line_ink_text_alignment(...)`
- Canonical preview uses the same helper through:
  - `src/foliaseal/application/signing_preview_renderer.py`
  - `_canonical_preview_layout(...)`

The current implementation correctly uses measured right side-bearing to keep
the rightmost glyphs close to the rounded border. However, for left-stamp
single-line layouts, that correction can leave excessive stamp-facing whitespace
between the stamp ink and the leftmost text glyphs.

### Required Approach

1. Add regression tests for Cap 4-6 style `single_line` + `left` image-stamp
   previews.
   - Assert validation remains green.
   - Assert right text-to-border gap remains close, around `4 px`.
   - Assert stamp and text do not overlap.
   - Assert stamp-to-text glyph gap is reduced to a small guard rather than
     `13-26 px`.

2. Adjust placement using measured ink data, not arbitrary box expansion.
   - Keep the existing border-facing right side-bearing correction.
   - Add a bounded stamp-facing correction so visible text ink can move closer
     to the stamp when there is excessive gap.
   - The correction must be derived from the measured rendered-ink side bearings
     and/or the existing configured separator, not a percentage of rectangle
     width.

3. Do not change validation policy in this slice.
   - Cap 4-6 already validate green.
   - Cap 10 must remain red.
   - Existing rendered-fit fallbacks should remain scoped as they are.

4. Keep preview and signed PDF parity.
   - The final text placement helper is shared by canonical preview and signed
     PDF style construction.
   - Any adjustment must happen at that shared helper, or be represented in the
     shared reservation model before both renderers consume it.

5. Preserve the simplicity constraint.
   - Do not add independent preview-only or PDF-only special cases.
   - Do not introduce new threshold ladders.
   - Do not make margins negative unless the test explicitly proves visible ink
     remains inside the border and the alternative would reintroduce structural
     side-bearing pessimism. If negative margins are used, they must represent
     measured invisible side-bearing only, not fit relaxation.

### Acceptance Criteria

- Cap 4-6 style automated preview tests pass with:
  - right text-to-border gap still close
  - stamp-to-text glyph gap materially smaller than the current `13-26 px`
  - no text/stamp overlap
  - stamp still visible
- Cap 10-style intentional rejection remains red.
- Existing horizontal single-line edge-safety tests still pass.
- Full suite passes.

### Execution Result

Implemented with TDD.

What landed:

- Added Cap 4-6 style canonical preview regression coverage for
  `single_line` + `left` image-stamp layouts.
- Kept validation/reservation math unchanged after the first implementation
  attempt showed that changing the separator in `_layout_reservation_for_template`
  altered backend validation policy.
- Changed only stamp/background placement:
  - left single-line image stamps get a slightly wider drawing lane for the
    background image
  - stamp content is aligned toward the text inside that lane
  - text placement and validation still use the existing ink-informed text lane
- This keeps preview and signed PDF on the same shared background-layout path.

Measured result:

- Cap-style stamp-to-text gaps improved to `11 px`, `10 px`, and `9 px`.
- Right text-to-border gap stayed at `4 px`.
- Stamp and text do not overlap.

Verification:

- Focused Cap 4-6 preview regression tests passed.
- Horizontal edge-safety and manual replay tests passed.
- `python -m ruff check ...` passed for touched code/tests.
- `pytest -q` passed: `528 passed, 1 warning`.

## Follow-up Slice: Rendered-Ink Stamp Allocation

### Goal

Replace the provisional left-stamp background-width tweak with a shared,
rendered-ink-based allocation rule so the stamp scales against the actual
visible text footprint rather than structural text side-bearing.

The previous slice improved stamp-to-text gaps from `13-26 px` to `9-11 px`,
but the desired rule is stricter: the stamp should consume the rectangle up to
the rendered text ink guard, not stop at a structural text-box edge. The user
correctly clarified the invariant as:

- text protected space is the rendered glyph ink required by the selected text
  settings
- the stamp image receives the remaining rectangle space
- the guard is measured between stamp ink and text glyph ink
- preview and actual PDF signing must compute the same placement from the same
  request data, not from GUI-only measured coordinates

### Relevant Code Path

- Shared ink reservation:
  - `src/foliaseal/application/horizontal_signature_reservation.py`
  - `HorizontalSingleLineInkReservation`
  - `build_horizontal_single_line_ink_reservation(...)`
- Signed PDF style construction:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_build_stamp_style(...)`
  - `_horizontal_single_line_ink_validation_reservation(...)`
  - `_apply_horizontal_single_line_ink_text_alignment(...)`
  - `_background_layout_for_stamp(...)`
- Canonical preview style construction:
  - `src/foliaseal/application/signing_preview_renderer.py`
  - `_canonical_preview_layout(...)`
- Rendered-fit fallback:
  - `src/foliaseal/application/phase3_signing_backend.py`
  - `_single_line_rendered_ink_fits_reservation(...)`

### Required Approach

1. Add a failing regression for Cap 4-6 style `single_line` + `left` layouts
   requiring the stamp-to-rendered-text gap to be `<= 5 px`, while preserving:
   - close right text-to-border gap
   - no stamp/text ink overlap
   - visible stamp bounds

2. Replace the hidden arithmetic inside `_background_layout_for_stamp(...)`.
   - That helper should receive an already-decided text width.
   - It must not contain secret left-stamp point subtraction.
   - The allocation decision belongs in a named helper used by both preview and
     backend signing.

3. Add `_horizontal_single_line_background_text_width(...)`.
   - For non-target layouts, return the existing fallback text width.
   - For `single_line` + `left` with ink reservation, reserve
     `ink_width + stamp_facing_padding - base_separator`.
   - Rationale: `_layout_reservation_for_template(...)` always inserts the base
     separator between stamp and text, while `stamp_facing_padding` is the
     desired rendered-ink guard. Subtracting the separator avoids counting the
     gap twice.

4. Use this helper in both construction paths.
   - `_build_stamp_style(...)` for signed PDF appearance.
   - `_canonical_preview_layout(...)` for preview appearance.
   - The PDF signer will recompute this from `SigningRequest`/appearance data
     and rendered text measurement; no GUI-only placement values are passed to
     signing.

5. Fix instrumentation where the new legal layout crosses structural boxes.
   - A black stamp can now occupy invisible text side-bearing space.
   - Tests and rendered-fit fallback must measure text ink from a text-only
     render of the same canonical layout.
   - Full-render text detection is no longer valid for stamp-to-text gap checks
     when stamp and text are the same color.

6. Preserve fit safety.
   - Keep validation/reservation thresholds unchanged.
   - Retain reference-render ink preservation.
   - Permit only the existing kind of raster seam: a `1 px` rendered-height
     difference in the rendered-ink fallback after reference preservation proves
     no visible ink is lost.

### Acceptance Criteria

- Cap 4-6 style tests show rendered stamp-to-text gaps no larger than `5 px`.
- Right text-to-border gaps remain close.
- Manual replay tests measure text ink from text-only canonical renders and do
  not misclassify stamp pixels as text.
- The backend manual replay validation ladder remains unchanged.
- Preview and PDF style construction share the same background text-width
  helper.
- Focused horizontal tests, ruff, and full pytest pass.

### Execution Result

Implemented with TDD.

What landed:

- Added/updated the Cap-style preview regression to require `<= 5 px`
  stamp-to-text rendered-ink gap.
- Added `_horizontal_single_line_background_text_width(...)` and wired it into
  both `_build_stamp_style(...)` and `_canonical_preview_layout(...)`.
- Removed hidden point subtraction from `_background_layout_for_stamp(...)`.
- Updated preview geometry tests to use text-only canonical renders for
  rendered text ink when comparing stamp-to-text spacing.
- Updated `_single_line_rendered_ink_fits_reservation(...)` to use text-only
  canonical renders for selected and reference text ink so stamp pixels cannot
  contaminate the text measurement.
- Preserved the manual replay validation ladder, with a documented `1 px`
  raster-height seam allowance after reference ink preservation.

Verification:

- Focused Cap-style preview regression passed.
- Horizontal edge-safety/manual replay/backend validation tests passed.
- `python -m ruff check ...` passed for touched code/tests.
- `pytest -q` passed: `528 passed, 1 warning`.

## Follow-up Slice: Rendered-Ink Layout Matrix Review

### Goal

Review and normalize the visible-signature layout matrix so every combination
of layout template and stamp position has an explicit answer to this question:

Does stamp allocation and validation use rendered glyph ink, or does it still
use structural text-box dimensions?

The latest manual harness run shows `single_line` + `right` still has more
stamp-facing whitespace than the newly improved `single_line` + `left` path.
That is expected from the current code: the rendered-ink background allocation
helper only applies to `LEFT`.

### Current Matrix From Code Review

`single_line` + `left`

- Current state: most complete rendered-ink path.
- Uses `measure_horizontal_single_line_rendered_reference(...)`.
- Uses `HorizontalSingleLineInkReservation`.
- Uses `_horizontal_single_line_ink_validation_reservation(...)`.
- Uses `_apply_horizontal_single_line_ink_text_alignment(...)` to move visible
  glyph ink toward the border by measured right side-bearing.
- Uses `_horizontal_single_line_background_text_width(...)` to size the stamp
  lane from rendered text ink plus explicit stamp-facing guard.
- Uses text-only canonical renders for tests/fallback where stamp and text ink
  can legally occupy overlapping structural boxes.
- Manual observation: improved substantially; now the reference implementation
  for the rendered-ink approach.

`single_line` + `right`

- Current state: partial rendered-ink path.
- Uses `measure_horizontal_single_line_rendered_reference(...)`.
- Uses `HorizontalSingleLineInkReservation`.
- Uses `_horizontal_single_line_ink_validation_reservation(...)`.
- Does not use a mirrored text side-bearing alignment.
- Does not use `_horizontal_single_line_background_text_width(...)` because that
  helper returns the fallback width unless `stamp_position == LEFT`.
- Latest Cap 5 geometry showed text-to-stamp gap around `6 px`, while the target
  behavior is the same explicit rendered-ink guard used by left.
- Required next implementation target.

`single_line` + `top`

- Current state: structural allocation plus rendered-ink fit fallback.
- Vertical stamp/text allocation is determined by `_layout_reservation_for_template(...)`
  and vertical single-line helpers:
  - `_single_line_vertical_outer_margin(...)`
  - `_single_line_vertical_stamp_border_gap(...)`
  - `_single_line_no_stamp_vertical_optical_shift(...)`
- `_single_line_rendered_ink_fits_reservation(...)` can accept cases where
  rendered ink fits even when nominal structural metrics are pessimistic.
- It does not currently allocate stamp height from rendered text ink in the same
  explicit way as `single_line` + `left` allocates stamp width.
- Manual result from the latest run looked acceptable, but the matrix needs an
  automated probe proving the stamp-facing and border-facing rendered-ink guards
  are intentional.

`single_line` + `bottom`

- Current state: same category as `single_line` + `top`.
- Structural vertical allocation with rendered-ink fit fallback.
- Needs the same matrix probe and may not need implementation if rendered-ink
  guards already match the established visual target.

`multi_line` + `left`

- Current state: structural allocation with horizontal rendered-layout fallback.
- `_horizontal_multi_line_rendered_layout_fits_reservation(...)` exists, but it
  is a fit-honesty fallback rather than stamp allocation from rendered ink.
- Latest manual Cap 7 showed `5 px` stamp-to-text gap and `4 px` border gap,
  which is visually consistent.
- Needs automated matrix coverage so future changes do not regress this.

`multi_line` + `right`

- Current state: structural allocation with horizontal rendered-layout fallback.
- Latest manual Cap 6 showed `6 px` text-to-stamp gap and `4 px` border gap.
- Needs review against the target guard; likely the same mirror issue as
  `single_line` + `right`, but less severe because multi-line text width is
  narrower and structural layout happens to be close.

`multi_line` + `top`

- Current state: structural allocation.
- Existing tests preserve top inset and separate stamp/text bounds.
- No rendered-ink allocation comparable to `single_line` + `left`.
- Needs matrix instrumentation before deciding whether an implementation change
  is warranted.

`multi_line` + `bottom`

- Current state: structural allocation.
- Existing backend tests cover compact bottom width rounding and zero-height
  stamp rejection.
- No rendered-ink allocation comparable to `single_line` + `left`.
- Needs matrix instrumentation before deciding whether an implementation change
  is warranted.

`wrapped_block` + `left`

- Current state: structural allocation.
- Latest manual Caps 8-9 showed `5 px` stamp-to-text gap and `4 px` border gap,
  which is visually consistent.
- No rendered-ink allocation comparable to `single_line` + `left`; this may be
  acceptable because wrapped text is intentionally block-shaped and uses the
  structural block width.

`wrapped_block` + `right`

- Current state: structural allocation.
- Existing tests preserve right inset.
- Needs matrix probe, especially because the right-side mirror issue can hide in
  any layout where text ink is narrower than the structural text block.

`wrapped_block` + `top`

- Current state: structural allocation.
- Existing tests preserve top inset.
- Needs matrix probe only unless artifacts show visible mismatch.

`wrapped_block` + `bottom`

- Current state: structural allocation.
- Existing tests preserve bottom inset.
- Needs matrix probe only unless artifacts show visible mismatch.

### Required Approach

1. Add a matrix test/probe that renders canonical previews for:
   - `single_line`, `multi_line`, `wrapped_block`
   - `top`, `bottom`, `left`, `right`
   - with an image stamp and the same representative text/font settings used in
     manual harness captures.

2. The probe must report, per case:
   - rendered text ink bounds from text-only canonical render
   - stamp ink bounds from stamp-only canonical render
   - border-facing rendered-ink gap
   - stamp-facing rendered-ink gap
   - validation result from backend fit path
   - whether preview/PDF style construction share the same margins

3. Add assertions only where the intended behavior is already clear:
   - no stamp/text rendered-ink overlap
   - stamp is visible when validation is green and an image stamp is selected
   - border-facing rendered text ink remains inside the border guard
   - `single_line` + `left` remains at the established tight guard
   - `single_line` + `right` is expected to fail the new mirrored tight-guard
     assertion before implementation

4. Implement the first normalization target: `single_line` + `right`.
   - Mirror `_apply_horizontal_single_line_ink_text_alignment(...)` using
     measured left side-bearing, not a new arbitrary threshold.
   - Generalize `_horizontal_single_line_background_text_width(...)` so it
     handles both `LEFT` and `RIGHT` from rendered ink plus stamp-facing guard.
   - Preserve `_layout_reservation_for_template(...)` fit policy.
   - Preserve text-only measurement for cases where stamp ink can legally enter
     invisible text side-bearing space.

5. After `single_line` + `right` passes, use the matrix output to decide whether
   multi-line or wrapped-block should change.
   - Do not assume every layout should receive the single-line treatment.
   - Multi-line and wrapped-block may intentionally reserve structural block
     space if the rendered-ink approach would make text columns appear unstable
     as content changes.
   - Any change outside horizontal single-line must be justified by a failing
     rendered-ink gap assertion and preview/PDF parity need.

6. Update harness documentation so manual testers know which cases still rely
   on structural block behavior and which are rendered-ink allocated.

### Acceptance Criteria

- The ExecPlan contains an explicit matrix status for all twelve combinations.
- Automated matrix probe covers all twelve combinations.
- `single_line` + `right` uses the same rendered-ink allocation principle as
  `single_line` + `left`.
- Preview and signed PDF style construction still share all placement decisions.
- No validation policy is relaxed.
- Full test suite passes.

### Notes For Implementation

- Avoid adding another one-off branch.
- Prefer renaming `_horizontal_single_line_background_text_width(...)` only if
  the helper becomes conceptually broader; otherwise keep it focused and mirror
  its internal position logic.
- If right-side text alignment requires negative left margins, the amount must
  be derived from measured `ink_left_offset_pt` and must be guarded by rendered
  ink preservation tests.
- Treat full-render text detection as invalid for same-color stamp/text gap
  checks; use text-only and stamp-only canonical layers for matrix assertions.

### Execution Result

Implemented with TDD.

What landed:

- Added a 12-case canonical preview matrix covering:
  - `single_line`, `multi_line`, `wrapped_block`
  - `top`, `bottom`, `left`, `right`
- The matrix records the rendered-ink contract by asserting:
  - backend validation is green for representative valid rectangles
  - preview and signed PDF style construction produce matching margins
  - text-only rendered ink and stamp-only rendered ink do not overlap
  - rendered text ink remains inside the border-facing guard
  - horizontal single-line left/right stamp-facing gaps are tight
- Confirmed the expected red case before implementation:
  - `single_line` + `right` had a `14 px` rendered text-to-stamp gap
- Mirrored the horizontal single-line rendered-ink implementation:
  - `_apply_horizontal_single_line_ink_text_alignment(...)` now handles
    `RIGHT` using measured `ink_left_offset_pt`
  - `_horizontal_single_line_background_text_width(...)` now handles both
    `LEFT` and `RIGHT`
  - validation/reservation policy remains unchanged

Measured matrix after implementation:

- `single_line` + `top`: stamp-facing gap `8 px`, border-facing gap `1 px`
- `single_line` + `bottom`: stamp-facing gap `3 px`, border-facing gap `6 px`
- `single_line` + `left`: stamp-facing gap `4 px`, border-facing gap `4 px`
- `single_line` + `right`: stamp-facing gap `4 px`, border-facing gap `4 px`
- `multi_line` + `top`: stamp-facing gap `9 px`, border-facing gap `3 px`
- `multi_line` + `bottom`: stamp-facing gap `6 px`, border-facing gap `6 px`
- `multi_line` + `left`: stamp-facing gap `5 px`, border-facing gap `8 px`
- `multi_line` + `right`: stamp-facing gap `10 px`, border-facing gap `4 px`
- `wrapped_block` + `top`: stamp-facing gap `9 px`, border-facing gap `3 px`
- `wrapped_block` + `bottom`: stamp-facing gap `5 px`, border-facing gap `6 px`
- `wrapped_block` + `left`: stamp-facing gap `6 px`, border-facing gap `10 px`
- `wrapped_block` + `right`: stamp-facing gap `12 px`, border-facing gap `4 px`

Decision from the matrix:

- Horizontal `single_line` left/right now use the same rendered-ink allocation
  principle.
- `single_line` top/bottom continue to use structural vertical allocation plus
  rendered-ink fit fallback; current measured gaps are acceptable and do not
  justify a vertical allocation change in this slice.
- `multi_line` and `wrapped_block` remain structural block layouts. Their
  larger gaps are visible in the matrix, especially right-side stamp positions,
  but changing them to rendered-ink allocation would make block-width behavior
  content-dependent. That should be a separate design decision, not a hidden
  follow-on to the single-line fix.

Verification:

- Matrix probe passed: `12 passed`
- Focused horizontal/manual replay/backend parity tests passed: `8 passed`
- `python -m ruff check ...` passed for touched code/tests.
- `pytest -q` passed: `540 passed, 1 warning`.
