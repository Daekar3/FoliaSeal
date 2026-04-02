# Backend Fit Rejection Trace Notes

Date: 2026-04-02
Focus: why the backend can still reject compact vertical `single_line` signatures even when the preview appears acceptable

## Findings

### 1. There was a real mismatch between early wrapping and final fit

For compact vertical `single_line` layouts:

- `_ensure_layout_can_fit()` already allowed `1.25x` width overflow when:
  - `layout_template == SINGLE_LINE`
  - `stamp_position in {TOP, BOTTOM}`
  - `container_height_pt <= 24`
- but `_build_stamp_text()` still called `_wrap_visible_signature_fragments()` with `width_overflow_tolerance = 1.0`

That meant some layouts were rejected early during body-text wrapping even though the later fit gate would have allowed them.

This mismatch is now fixed by reusing the same vertical compact overflow tolerance in `_build_stamp_text()`.

### 2. The remaining refusal in the traced `10pt` case is a height failure, not a width failure

Representative traced case:

- rectangle: `260 x 22 pt`
- layout: `single_line / top`
- image stamp present
- visible fields:
  - common name
  - email
  - title
  - company
- prefix: `Inkslapped by`
- font size: `10 pt`

After the early-width fix:

- `_build_stamp_text()` succeeds
- resulting stamp text:

```text
Inkslapped by
Adam Smith | test@example.com | Board Secretary | FoliaSeal
```

- measured text box: `295 x 20 pt`
- reserved text area from `_layout_reservation_for_template()`: `256 x 18 pt`
- compact vertical width tolerance in the final fit gate: `256 * 1.25 = 320 pt`

So:

- width is acceptable: `295 <= 320`
- height is not acceptable: `20 > 18`

The rejection in this case is therefore caused by the final height check in `_ensure_layout_can_fit()`, not by the earlier wrapping step.

### 3. What this means

There are now two separate questions:

1. Was the early width rejection wrong?
- Yes.
- Fixed.

2. Is the remaining height rejection wrong?
- Not obviously.
- The backend currently says that a prefix plus one body line at `10 pt` does not honestly fit inside a `22 pt` rectangle once margins are applied.

That may still be too conservative, but it is a different problem from the earlier mismatch.

## Likely next backend questions

If we continue this track, the next thing to audit is compact vertical height budgeting:

- current compact vertical margins/gap come from `_compact_vertical_spacing()`
- current reservation may leave too little usable text height for borderline cases
- but relaxing height too far could collapse the stamp area to zero or make output dishonest

So the next safe decision point is:

- do we want to allow modest height overflow in compact vertical text?
- or do we want to reduce compact vertical margins/gap further?
- or do we accept that the preview is currently more optimistic than the backend for these borderline `10 pt` cases?
