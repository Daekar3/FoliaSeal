# Text Line-Height Contract ExecPlan

## Goal

Resolve the remaining stress-matrix green-path clipping clusters in:

- `single_line` vertical stacked cases
- `wrapped_block` sparse/medium vertical cases

without reintroducing magic thresholds or layout-mode-specific font-size
semantics.

## Current State

After the first stress remediation slice:

- `multi_line` stress green path is clean
- `single_line` stress still has `108` signable text-clipping risks
- `wrapped_block` stress still has `48` signable text-clipping risks

The surviving cases are no longer caused by:

- split title/body preview geometry
- missing preview artifact capture
- border strokes being mistaken for rendered text

Those seams were fixed already.

## Problem Statement

The remaining green-path cases share a deeper contract problem:

- backend fit validation measures text using pyHanko `TextBox` geometry
- preview renders text using Qt label layout
- in compact stacked layouts, Qt's effective rendered line boxes are taller than
  the pyHanko measurement model currently assumes

This mismatch shows up as:

- backend says the text fits
- preview image shows visibly clipped bottom lines
- detector correctly flags clipping in the rendered preview PNG

Representative examples:

- `single_top_short_border_0_5_stamp_wide_text_10_0_label_sparse`
- `wrapped_block_top_wide_border_0_5_stamp_wide_text_8_5_label_sparse_named`

## Discovery Already Executed

I tested two candidate fixes during this slice and intentionally did not keep
either one:

1. Explicit backend line leading
   - made backend text height much closer to the rendered preview
   - but also broke compact `single_line` cases that had already been accepted
     manually

2. Preview-side rich-text line-height compression
   - did not materially change the stress matrix outcomes
   - would have added complexity without restoring semantic trust

Those experiments were useful because they narrowed the problem:

- the remaining seam is real
- it is not safely fixable by adding ad hoc leading on one side only
- the next durable fix has to make preview and final/PDF text layout share a
  more faithful rendering contract

## Next Remediation Direction

The next slice should move away from QLabel-driven multi-line text rendering as
the preview truth source for stacked layouts.

Preferred direction:

1. First correct the shared text-height calculation if the backend line-box
   model is demonstrably undercounting stacked descenders.
2. Then, if needed, introduce a PDF-faithful preview text render path for
   stacked layouts.
3. Use the same composed stamp text and backend-owned style inputs.
4. Render the text preview with a line-box model that matches the final stamp
   rendering contract more closely than Qt QLabel does today.

This can be done one of two ways:

- render text preview from the same pyHanko/PDF text engine semantics used by
  final stamp generation, then rasterize for the preview card
- or introduce one shared explicit text line-box model used by both backend
  measurement and preview rendering

The first option is preferred if it is tractable, because it reduces semantic
drift instead of creating another abstract approximation layer. A small fixed
descender-height correction in the backend measurement model is also acceptable
if it is justified by repeatable stacked-text evidence and is applied as a
calculation correction rather than a pass/fail tolerance.

## Execution Steps

1. Build a narrow prototype for one representative `single_line` stress case
   and one representative `wrapped_block` stress case.
2. Compare:
   - backend text-box metrics
   - Qt preview render bounds
   - PDF-faithful prototype render bounds
3. Choose the rendering contract that best matches the final signed output.
4. Replace the current stacked-layout preview text rendering path with that
   shared contract.
5. Rerun:
   - focused shell/harness/backend tests
   - full suite
   - stress matrices

## Acceptance

Success target:

- `single_line` stress signable text-clipping risks reduced from `108` to `0`
- `wrapped_block` stress signable text-clipping risks reduced from `48` to `0`
- no regressions in:
  - `multi_line`
  - accepted compact `single_line` manual cases
  - baseline matrices

## Notes

This execplan intentionally does not bless either of the rejected experiments as
the solution. It defines the next slice as a rendering-contract problem, not a
"find the right fudge factor" problem.

Policy note for this and future slices:

- We do the hard work of getting the calculations right.
- We do not fix fit bugs by slapping percentage-based tolerances onto the
  backend until the numbers happen to look acceptable.
- The only acceptable allowance is a tiny documented numeric seam correction
  when mixed integer rounding would otherwise create false negatives.
- We also do not pretend user-provided assets have a different aspect ratio
  than they actually do in order to make the layout look easier to solve.
