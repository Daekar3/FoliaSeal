# Backend Fit Rejection Trace ExecPlan

Date: 2026-04-01
Owner: Codex

## Goal

Trace exactly why the backend rejects some visible-signature layouts that look renderable in the preview and, in some nearby cases, produce acceptable final output once forced through.

## Scope

- `src/foliaseal/application/phase3_signing_backend.py`
- relevant unit tests in `tests/unit/test_phase3_signing_backend.py`
- optional diagnostic notes in `docs/ExecPlans/`

## Steps

1. Trace the rejection path.
- Follow `_visible_signature_fit_issues()`
- then `_build_stamp_style()`
- then `_build_stamp_text()`
- then `_wrap_visible_signature_fragments()`
- then `_layout_reservation_for_template()`
- then `_ensure_layout_can_fit()`

2. Reproduce a realistic refusal.
- Use a representative compact `single_line / top` or `bottom` case.
- Record:
  - requested rectangle
  - measured text box width/height
  - reserved text area width/height
  - exact failure condition

3. Decide whether the wrong actor is:
- text wrapping
- text box measurement
- reservation split
- final fit gate

4. Implement the smallest safe correction.
- Keep text-size honesty.
- Do not silently drop fields.
- Avoid widening scope into image-format fixes or preview work.

5. Add regression coverage.

## Success criteria

- We can explain the refusal in concrete measured terms.
- The backend accepts realistic compact rectangles it can honestly render.
- Tests pin the corrected behavior.
