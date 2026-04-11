# Stress Matrix Green-Path Remediation ExecPlan

## Goal

Eliminate the remaining green-path clipping mismatches exposed by the new
real-world stress matrices without introducing threshold-triggered layout modes
or layout-specific text-size semantics.

## Problem Statement

The stress matrices surfaced signable scenarios where the preview still looks
clipped even though backend validation is green:

1. `single_line` vertical stress cases with signer label present
2. `multi_line` horizontal medium-density stress cases
3. `wrapped_block` sparse/medium named stress cases

The common seam is that preview rendering is still structurally different from
the backend contract:

- backend fit validation measures a single composed `stamp_text` box
- preview still splits the signer label/title into a separate widget
- preview geometry is therefore subtracting title/widget overhead that the
  backend reservation never modeled
- preview also allows QLabel/container behavior to consume a little extra
  content-box space after backend reservation is translated into Qt geometry

This is a structural mismatch, not a data-only issue and not a case for more
magic tolerances.

## Root Cause

### Shared root cause

Preview text is still rendered as multiple widgets whose geometry is not the
same thing the backend measures. The backend measures one text box containing:

- signer label prefix line when present
- body lines composed according to layout template

The preview instead:

- renders `title_label` separately
- subtracts `title_label` height from the available body height
- measures reservation using `detail_text` rather than the full composed text
- then relies on widget size hints and container geometry for the final text
  content box

That drift is what the stress corpus exposed.

## Remediation Strategy

### 1. Make preview text use the same composed text unit as the backend

Introduce a preview-side helper that mirrors backend text composition:

- full preview stamp text = signer label prefix + composed detail text
- use that full text for preview reservation measurement
- use that full text for the actual rendered preview label

Preview must stop treating the signer label/title as a separate geometry path.

### 2. Remove preview-only title/body geometry splitting

For the actual preview card:

- keep the `title_label` widget for compatibility if needed, but hide it in the
  rendered card
- do not subtract title height or title gap from the body region
- render the full composed stamp text inside the reservation-derived text box

This makes preview geometry continuous across the full range of rectangle sizes.

### 3. Keep typography semantics unchanged

- selected point size remains the selected point size
- do not add new narrow-case compactness logic
- do not add new overflow tolerances to validation in this slice
- fix preview honesty by unifying the geometry model, not by changing the
  meaning of text size

### 4. Keep wrapping semantics backend-owned

Preview should not add widget-driven wrapping behavior that the backend did not
measure. The composed preview text already contains the backend-owned line
breaks, so the rendered preview text widgets should not invent more wrapping.

## Implementation Steps

1. Add a preview helper that returns the full composed preview text.
2. Update preview reservation measurement to use the full composed text.
3. Update preview rendering to place the full composed text into the active text
   label for both vertical and horizontal layouts.
4. Stop subtracting title widget height from the preview body geometry.
5. Disable widget-driven wrapping for the rendered preview text path so preview
   line breaks stay backend-owned.
6. Update preview text extraction helpers/tests to reflect the unified text box.
7. Add focused regressions for:
   - `single_line` vertical stress geometry using full composed text
   - `multi_line` horizontal preview content box matching reservation geometry
   - wrapped-block named sparse stress cases preserving full preview text

## Verification

Targeted verification:

- `ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py`
- `pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py`

Full verification:

- `ruff check .`
- `pytest -q`

Stress acceptance:

- rerun `single_line_full_matrix_stress`
- rerun `multi_line_full_matrix_stress`
- rerun `wrapped_block_full_matrix_stress`

Success target:

- `signable_text_clipping_risk_scenario_count == 0` for all three stress matrix
  summaries

## Notes

This slice is intentionally about unifying preview geometry with backend text
semantics. It does not change layout policy, validator thresholds, or text-size
meaning.

## Execution Notes

Implemented:

- preview now composes and renders one unified `stamp_text` payload instead of
  subtracting a separate title widget from the geometry budget
- preview reservation measurement now uses the same composed text unit the
  backend validates
- rendered preview text no longer relies on widget-driven wrapping that the
  backend never measured
- `preview_text()` now reports the active vertical text widget for
  `wrapped_block` and `multi_line`, so captured manual evidence no longer drops
  those cases on the floor
- text-content detection in the harness now filters out border-like black
  strokes before computing rendered text bounds, which removed a class of
  border-as-text false positives

Verified:

- `ruff check` on the touched files: passed
- focused shell/harness/backend suites: passed
- full suite: `364 passed`

Stress matrix outcome after the implemented remediation:

- `single_line_full_matrix_stress_v3`
  - signable text clipping risks: `108`
  - rejected text clipping risks: `672`
- `multi_line_full_matrix_stress_v3`
  - signable text clipping risks: `0`
  - rejected text clipping risks: `264`
- `wrapped_block_full_matrix_stress_v3`
  - signable text clipping risks: `48`
  - rejected text clipping risks: `606`

Interpretation:

- the unified preview text-box fix fully cleared the stress green path for
  `multi_line`
- it materially improved the earlier structural mismatch and fixed missing
  vertical evidence capture
- the remaining `single_line` and `wrapped_block` green-path stress clusters are
  now much more clearly isolated as a line-height contract problem between
  backend measurement and rendered preview, not a title/body geometry mismatch
- an attempted explicit backend line-leading fix was intentionally not kept,
  because it also broke compact `single_line` cases that had already been
  accepted manually
