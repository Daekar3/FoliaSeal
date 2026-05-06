# ExecPlan: Rendered Text Instrumentation And Preview UX Verification

## Objective

Upgrade the Phase 3 harness and unattended preview matrix so they can detect
rendered-text clipping and text/stamp overlap from the actual preview image,
not just from widget geometry and backend reservation math.

The goal is to make obviously bad user-visible states machine-detectable:

- text clipped by the border
- text clipped by the text widget bounds
- text visually running into the stamp-facing edge
- text/stamp overlap

This instrumentation must apply uniformly across layout modes. It must not
introduce layout-specific thresholds or special narrow-case policies.

## Problem Statement

The current harness is strong on stamp-image diagnostics, but weak on rendered
text diagnostics. It mostly reasons from widget boxes and reservation bands.
That leaves a blind spot:

- the backend can say a case is signable
- the preview can still look obviously clipped or overlapped
- the harness has insufficient rendered-text evidence to catch the mismatch

This is not acceptable for a system that aims to verify actual user experience.

## Desired Outcome

The harness and matrix should produce objective rendered-text evidence:

- detected text-content bounds inside the preview image
- distances from rendered text to the text-widget edges
- distances from rendered text to the card border
- text/stamp intersection diagnostics
- explicit booleans/counters for clipping risk and overlap risk
- debug overlays that make the evidence easy to inspect when needed

## Implementation Plan

1. Add image-based text-content extraction helpers.
   - Analyze the saved preview PNG inside the active detail-label bounds.
   - Detect non-background pixels and compute rendered text-content bounds.
   - Keep the detection generic so it works across layouts and sizes.

2. Add text diagnostics.
   - Compute text-content edge distances within the text widget.
   - Compute text-content distances to the card border.
   - Compute text/stamp-band and text/stamp-content intersection diagnostics.
   - Expose concise booleans for likely clipping/overlap.

3. Add a text debug overlay artifact.
   - Draw the text widget bounds.
   - Draw the detected rendered text bounds.
   - Draw the stamp band/content bounds when present.

4. Thread the new data into render_capture.
   - Include the new text-content bounds and diagnostics in harness JSON.
   - Keep the old geometry snapshots for context.

5. Extend unattended matrix summaries.
   - Count scenarios with rendered-text clipping risk.
   - Count scenarios with text/stamp overlap risk.

6. Add focused tests.
   - image-based text-content detection
   - text edge/overlap diagnostics
   - debug overlay generation
   - summary counting

## Constraints

- No arbitrary layout thresholds or “narrow case” branches.
- Instrumentation must observe the actual rendered preview, not reinterpret
  the layout with another geometry model.
- Preview-user-experience verification should become more comprehensive, not
  more permissive.

## Progress

- 2026-04-09: Plan created and execution started.
- 2026-04-09: Implemented rendered-text content extraction from preview PNG crops.
- 2026-04-09: Added text edge/overlap diagnostics and text debug overlay artifacts.
- 2026-04-09: Threaded text diagnostics into `render_capture` and matrix summary counts.
- 2026-04-09: Added focused unit coverage for text detection, overlap diagnostics,
  debug overlay generation, and summary aggregation.
- 2026-04-09: Verification passed:
  - `ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py docs/ExecPlans/text_render_instrumentation_execplan.md`
  - `pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py`
  - `pytest -q`
- 2026-04-09: Unattended `multi_line` matrix rerun completed with the new diagnostics
  written into summary output at
  `artifacts/preview_sweep_runs/multi_line_full_matrix_text_instrumented/summary.json`.
