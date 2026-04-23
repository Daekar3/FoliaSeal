# Goal

Correct the visual vertical placement of no-image `single_line` visible signatures without broadening the change into other layout families.

# Why This Slice Exists

- Manual harness evidence shows a no-stamp `single_line/top` case where the content sits visibly low in the signature box even though there is no reserved stamp band.
- The current reservation math is not the problem:
  - no-image `single_line` uses `stamp_area_width_pt = 0`
  - no-image `single_line` uses `stamp_area_height_pt = 0`
  - the full interior is reserved for text
- The defect is that the text area is vertically centered by the nominal text-box metrics, but the rendered glyph ink is bottom-weighted within that text box.

# Constraints

- Keep the change narrow:
  - only no-image `single_line`
  - do not change `multi_line` or `wrapped_block`
  - do not touch detector thresholds
- Keep preview and final rendering on the same policy path.
- Do not reintroduce tolerance-based acceptance logic.

# Work Plan

## 1. Add a regression for canonical no-image `single_line` placement

Add a canonical preview renderer test using a real no-stamp `single_line` case and assert:

- `stamp_area_bounds_px is None`
- `stamp_bounds_px is None`
- the rendered text stays within the reserved text area vertically
- top and bottom slack are close enough to count as visually centered

This test should reflect the actual current problem rather than a synthetic geometry-only assertion.

## 2. Adjust the no-image `single_line` vertical placement rule

Change the no-image `single_line` reservation path so the text content uses a top-biased vertical alignment inside its reserved text area instead of `ALIGN_MID`.

Rationale:

- for this path, the full box is already reserved for text
- the rendered glyph ink is bottom-heavy relative to the nominal text-box metrics
- using `ALIGN_MAX` for the text area gives a visually centered result without introducing new margins, per-font offsets, or detector slack

This is simpler than adding asymmetric margin hacks or template-specific preview-only corrections.

## 3. Update backend tests to match the corrected policy

Replace the outdated assertion that no-image vertical `single_line` content is centered with `ALIGN_MID`.

The new backend tests should make the policy explicit:

- no-image `single_line` text uses `ALIGN_MAX`
- image-bearing `single_line` paths keep their current band-alignment behavior

## 4. Verify against the current manual harness case

Run focused tests and render the current no-stamp `single_line` case through the canonical preview path to confirm:

- no stamp band is present
- the text no longer sits visibly low in the box
- the text stays within the reserved text area

# Verification

- `ruff check` on touched files
- focused tests for backend and canonical preview renderer
- `pytest -q`

# Acceptance Criteria

- No-image `single_line` still reserves zero stamp area
- No-image `single_line` text is visually centered by canonical render, not nominal box centering
- No preview-only special case is introduced
- `multi_line` and `wrapped_block` behavior is unchanged in this slice

# Execution Notes

Implemented in this slice:

- changed the no-image `single_line` reservation path to use:
  - an asymmetric outer margin shift bounded by the existing outer inset
  - `AxisAlignment.ALIGN_MAX` for the text area, so the rendered glyph block is placed more honestly
- added backend coverage that locks in the no-image `single_line` optical-alignment policy
- added a canonical preview regression based on the real `8.5pt` manual harness case that exposed the defect

Verification:

- `python -m ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py`
- `pytest -q`

Observed outcome:

- focused backend/preview suites remained green
- full suite remained green: `435 passed`
- the canonical render for the real no-stamp `single_line` case now moves the text block upward instead of leaving it flush to the bottom edge
