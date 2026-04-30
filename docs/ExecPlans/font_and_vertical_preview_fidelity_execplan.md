# Font And Vertical Preview Fidelity ExecPlan

## Objective

Correct two user-visible preview bugs:

1. The font-family selector must produce meaningfully different preview typography for the advertised families.
2. Vertical stacked previews must stop clipping text at the bottom when the backend still considers the case signable.

## Root causes

### Font-family preview bug

- `_preview_font_stack()` matched `"serif"` before `"sans serif"`, so the literal `Sans Serif` selection was rendered with the serif stack.
- `Cursive` and `Fantasy` both fell through to the generic sans fallback, so the control offered choices the preview did not honor.

### Vertical preview clipping bug

- `_fit_vertical_preview_band_geometry()` already received `detail_hint_height_px`, but discarded it.
- The preview therefore hard-clamped text to the backend-reserved text height even when separator/stamp space could be borrowed without changing the overall card size.
- Result: green backend verdicts with visibly clipped bottom text in preview.

## Corrective action

1. Make preview font mapping explicit and category-correct:
   - `Sans Serif` -> sans stack
   - `Serif` -> serif stack
   - `Monospace` -> mono stack
   - `Cursive` -> cursive/script stack
   - `Fantasy` -> fantasy/display stack

2. Use `detail_hint_height_px` in vertical band fitting:
   - preserve the total card height
   - borrow space from separator first, then from stamp height down to a small visible minimum
   - do not introduce a narrow-case rule; apply this continuously across vertical stacked layouts

3. Add focused tests that lock in:
   - distinct preview font stacks for the advertised families
   - `Sans Serif` no longer collapsing into serif
   - vertical band fitting expands text when the rendered hint exceeds the reserved text height

## Verification

- focused Qt shell tests
- full suite

## Non-goals

- no change to the backend PDF font-support contract in this slice
- no threshold-triggered layout modes
