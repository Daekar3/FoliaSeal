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
