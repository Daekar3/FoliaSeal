# Backend fit correction for compact visible-signature rectangles

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md` and the repo `Agents.md`.

## Purpose / Big Picture

The current signing backend can produce a valid signed PDF, but ordinary compact rectangles still
behave too harshly for `single_line` visible signatures. A normal form-line rectangle around
260 pt wide by 20-22 pt high can still be rejected at 6 pt, and when it does sign the `Top` and
`Bottom` image row is still aligned and sized in ways that do not match the intended layout. After
this change, the backend should keep honoring the user-selected text size, allow realistic compact
rectangles when the text can still be rendered honestly, and keep the stamp image inside the true
remaining stamp row with sensible alignment.

The user-visible proof is a focused harness rerun plus backend tests that show compact
`single_line` `Top` and `Bottom` rectangles sign successfully and produce a plausibly sized stamp
image instead of a grossly oversized or rejected layout.

## Progress

- [x] (2026-04-01 09:43Z) Read the current backend fit and reservation code in `src/foliaseal/application/phase3_signing_backend.py` and the focused tests in `tests/unit/test_phase3_signing_backend.py`.
- [x] (2026-04-01 09:45Z) Identified two backend causes worth correcting in this slice: `single_line` body wrapping still measures against nearly the full rectangle width instead of the position-specific text area, and vertical stamp rows still center the background image inside the row.
- [x] (2026-04-01 09:56Z) Adjusted `single_line` text wrapping and fit heuristics so compact vertical rectangles can prefer fewer body lines with a bounded horizontal overflow tolerance instead of failing immediately at 6 pt.
- [x] (2026-04-01 09:56Z) Tightened `Top` and `Bottom` stamp-row alignment so the final PDF uses left-aligned image placement for vertical `single_line` rows instead of centering the stamp in the row.
- [x] (2026-04-01 09:58Z) Added focused regression tests covering compact vertical body wrapping, 6 pt fit acceptance for `Top` and `Bottom`, and the updated alignment expectations.
- [x] (2026-04-01 09:59Z) Ran focused pytest and ruff checks successfully.

## Surprises & Discoveries

- Observation: the current backend wrap path still uses `signature_rect.width_pt - 8` even for
  `single_line` layouts that reserve width for a stamp image.
  Evidence: `_build_stamp_text()` currently calls `_wrap_visible_signature_fragments()` with
  `max_text_width_pt=max(1, int(round(signature_rect.width_pt)) - 8)` regardless of
  `stamp_position`.

- Observation: the current vertical reservation path makes the stamp image behave like a centered
  background row rather than a row aligned with the text block.
  Evidence: `_layout_reservation_for_template()` gives `Top` and `Bottom`
  `background_alignment = AxisAlignment.ALIGN_MID`, which matches the user’s observation that the
  final `Top` and `Bottom` stamp is centered in the row.

- Observation: the compact 6 pt failure came from width validation after body wrapping, not only
  from the stamp row height.
  Evidence: the realistic `263.04 x 20.48 pt` case measured as `315 x 12 pt` for the two-line
  prefix/body candidate and was then rejected because `_ensure_layout_can_fit()` enforced the
  exact text-area width even when the vertical row would otherwise be honest and readable.

## Decision Log

- Decision: keep this worker strictly on backend geometry and fit behavior, not shell preview or
  harness capture behavior.
  Rationale: the user explicitly scoped this worker to `phase3_signing_backend.py` and
  `test_phase3_signing_backend.py`, and parallel shell/harness workers are already active.
  Date/Author: 2026-04-01 / Codex worker

- Decision: preserve the text-first contract and relax only the backend fit math around the stamp
  row and the wrapped body width.
  Rationale: the user already clarified that text size is the priority and the stamp may shrink
  aggressively; that means we should make the text-area math more accurate rather than trimming
  fields or shrinking text.
  Date/Author: 2026-04-01 / Codex worker

- Decision: allow a bounded horizontal overflow tolerance for compact vertical `single_line`
  rectangles before rejecting the layout.
  Rationale: the real-world 6 pt case only failed because the body wrapped into too many lines and
  then tripped exact-width validation. A modest tolerance keeps the text size honest while letting
  realistic rectangles survive instead of forcing a drop to 4.5 pt.
  Date/Author: 2026-04-01 / Codex worker

- Decision: limit the new left alignment to vertical `single_line` rows only.
  Rationale: `wrapped_block` and other non-`single_line` layouts already had stable expectations in
  tests and did not share the user-visible centering complaint.
  Date/Author: 2026-04-01 / Codex worker

## Outcomes & Retrospective

This worker slice now leaves the backend in a materially better state for the next harness rerun.
Compact vertical `single_line` bodies can stay on fewer lines when a small amount of width
overflow keeps the overall text block honest at 6 pt, and the `Top` / `Bottom` image row no longer
defaults to a centered horizontal placement. The focused backend suite passes with the new compact
rectangle tests, so the remaining questions are now best answered in the integrated harness run
with the preview and output-analysis workers’ changes alongside these backend corrections.

## Context and Orientation

The work in this plan touches only:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`

The backend receives a `SigningBackendAppearance` and `SignatureRect`, then builds a pyHanko
`TextStampStyle`. In this repository, the “stamp image” is the optional signature image placed as
the stamp background. The “body” is the pipe-separated visible-signature text below or beside the
prefix line. The `single_line` template still permits wrapped body lines when the rectangle is too
compact to keep everything on one line, but the backend should only wrap because of the true text
area and should not reject a normal rectangle just because the reservation math is too conservative.

The two key backend helpers are `_build_stamp_text()`, which decides how the body is wrapped, and
`_layout_reservation_for_template()`, which decides the text area and stamp area geometry for the
pyHanko layout rules. `_background_layout_for_stamp()` then turns that reservation into the actual
image placement rule.

## Plan of Work

First, update `_build_stamp_text()` so the `single_line` wrap decision uses the text area that
matches the requested `stamp_position`, not the near-full rectangle width. For horizontal positions
this should prevent the backend from over-promising a one-line body. For vertical positions it
should let the backend make a more honest body-width decision based on the real row geometry.

Second, adjust `_layout_reservation_for_template()` and `_background_layout_for_stamp()` for
vertical `single_line` signatures. The vertical compact path should keep enough row height for the
stamp without making the image centered in the row by default. The image should preserve aspect
ratio, shrink aggressively when necessary, and align sensibly within the reserved row instead of
looking like a generic centered banner.

Third, add focused tests. At minimum there should be:

- a compact 6 pt rectangle case that is accepted for `single_line` `Top`
- a corresponding `Bottom` case
- assertions that the output PDF contains a non-trivial but bounded background scale
- assertions that the layout reservation for `Top` and `Bottom` now aligns the background row as
  intended instead of centering it

## Concrete Steps

Work from `/home/daekar/SignPDF/Scratch`.

1. Update `src/foliaseal/application/phase3_signing_backend.py`.
2. Extend `tests/unit/test_phase3_signing_backend.py` with focused compact-rectangle coverage.
3. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py
       ./.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

4. Record the results and any caveats in this plan before reporting completion.

## Validation and Acceptance

Acceptance is reached when the focused backend tests pass and demonstrate all of the following:

- an ordinary compact `single_line` rectangle at 6 pt can sign successfully for `Top` and `Bottom`
  when the text is still honestly renderable
- the final PDF’s background scale for the compact vertical cases is non-trivial and not grossly
  oversized
- the vertical stamp row uses sensible alignment rather than a generic centered placement

The manual proof will come from the parent wave’s harness rerun, but this worker must leave the
backend in a state where that rerun has a realistic chance of succeeding.

## Idempotence and Recovery

These edits are code and tests only, so they are safe to repeat. If a proposed fit change makes the
compact tests worse, revert only that local backend logic and update this plan’s `Progress` and
`Surprises & Discoveries` sections before trying another approach.

## Artifacts and Notes

The user’s latest harness notes that matter for this worker are:

- `single_line / Top` and `Bottom` still require font size reduction down to 4.5 pt before the
  backend allows signing
- once signing succeeds, the vertical stamp image is better scaled but still centered in its row
- `single_line / Left` is closer to correct, which suggests the remaining issue is specific to the
  vertical row geometry

Verification run after the implementation:

    ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py
    27 passed in 1.68s

    ./.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

## Interfaces and Dependencies

Use the existing backend helpers and pyHanko layout classes already imported in
`src/foliaseal/application/phase3_signing_backend.py`. Do not add a new dependency. Keep all new
logic local to the backend module unless a tiny test helper is truly necessary.

Update note: created on 2026-04-01 for the backend-fit track of the current corrective wave after
the latest harness run showed improved but still overly strict compact-rectangle behavior and a
still-centered vertical stamp image in the final PDF.
