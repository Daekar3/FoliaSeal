# Instrumentation Fidelity RCA ExecPlan

## Objective

Explain why recent manual harness captures still surfaced obvious preview/validation failures, then correct the harness instrumentation so those failures are recorded and promoted clearly in saved evidence.

## Root causes

1. Font fidelity was not instrumented.
   - The harness recorded geometry, clipping, and stamp overlap, but it did not record whether the selected font family actually resolved to a different rendered family.
   - The preview font mapper only distinguished monospace, serif, and a sans fallback, so `Cursive` and `Fantasy` collapsed silently.

2. State changes were evaluated in isolation.
   - Manual captures stored each state independently.
   - There was no transition analysis for cases like “font size changed but the preview barely changed.”

3. Render diagnostics were not promoted strongly enough.
   - A state could be `can_submit = true` while `render_capture` already contained a user-visible clipping/overlap signal.
   - The evidence contract validated artifact presence, but not signable-vs-visible mismatch.

4. The text detector still trusted noisy pixels too much.
   - Rounded border strokes and other dark pixels near the text widget could inflate rendered text bounds.
   - Small but visible bottom-edge loss was also masked by a symmetric tolerance that was too generous for vertical clipping.

## Corrective actions

1. Add font diagnostics to every captured render.
   - requested family and size
   - effective resolved font family and point size
   - requested vs effective generic font category
   - explicit flag for generic families that do not yet have a direct preview mapping

2. Add transition diagnostics across captured states.
   - compare adjacent states when text, layout, and rectangle are unchanged
   - flag negligible visual response to font-size changes
   - flag negligible visual response to font-family changes when the effective category does not change

3. Promote signable render failures into the evidence contract.
   - a signable state with rendered text clipping, text/stamp overlap, or a stamp touching the band edge is now an evidence error

4. Tighten rendered-text detection with the reference render.
   - constrain candidate pixels to an expanded envelope around the reference text bounds when available
   - use a stricter vertical loss tolerance than horizontal loss tolerance so bottom-edge clipping is not waved through

## Validation

- focused harness/evidence suite
- full repo suite

## Result

The harness now records font-fidelity diagnostics, transition diagnostics, and signable render mismatches, and it uses the reference render to suppress false text bounds contamination from unrelated dark pixels.
