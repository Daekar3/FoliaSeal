# Backend Horizontal Fit Follow-Up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

The latest manual harness run showed that `single_line` horizontal visible signatures (`Left` and
`Right`) now produce readable text, but the stamp image is still smaller than necessary and leaves
obvious unused horizontal space beside the text. After this follow-up, the backend should keep the
current text-first contract while using the remaining horizontal stamp area more effectively, so the
signed PDF looks balanced instead of conservative and underfilled.

## Progress

- [x] (2026-04-01 00:20Z) Created this ExecPlan for the backend horizontal-fit follow-up.
- [x] (2026-04-01 00:23Z) Inspected the current horizontal reservation and image-fit helpers in
  `src/foliaseal/application/phase3_signing_backend.py`.
- [x] (2026-04-01 00:26Z) Adjusted the horizontal `single_line` reservation logic to better
  reflect the wrapped/measured text footprint instead of starving the stamp.
- [x] (2026-04-01 00:27Z) Added focused regression tests in
  `tests/unit/test_phase3_signing_backend.py`.
- [ ] Run focused pytest and ruff verification.

## Surprises & Discoveries

- Observation: horizontal `single_line` output already has acceptable text clarity.
  Evidence: the user reported that `single_line/left` and `single_line/right` text size, position,
  and clarity looked good in the actual PDF.

- Observation: the remaining defect is stamp underuse, not text overflow.
  Evidence: the user reported obvious unused horizontal space beside the text while the stamp stayed
  smaller than necessary.

- Observation: the compact horizontal example still does not honestly fit at `6pt`.
  Evidence: `_visible_signature_fit_issues()` continued to report the expected layout error for the
  `259.28 x 22.12 pt` rectangle at `6.0`, `5.5`, and `5.0` points, but accepted the same geometry
  at `4.5pt`.

## Decision Log

- Decision: keep this follow-up scoped to backend reservation and fit logic only.
  Rationale: the preview and harness issues are already assigned elsewhere; this pass should only
  improve actual signed-PDF horizontal stamp sizing.
  Date/Author: 2026-04-01 / Codex

- Decision: reserve horizontal `single_line` text width using the same bounded-overflow tolerance
  already used when wrapped body text is chosen.
  Rationale: the text builder already allows modest width overflow when a horizontal stamp is
  present, but the later reservation step still treated the full measured width as untouchable. The
  mismatch starved the stamp area unnecessarily.
  Date/Author: 2026-04-01 / Codex

## Outcomes & Retrospective

This follow-up improved the horizontal stamp/text split without widening scope into shell or
harness code. The backend now reserves less width for horizontal `single_line` text by reusing the
existing bounded-overflow contract, which gives the stamp area more space while keeping the
text-first rule intact. The remaining limitation is explicit: this compact horizontal example is
still a `4.5pt` case, not a `6pt` case, so any future change to accept larger text there would be a
separate fit-policy decision rather than a stamp-sizing correction.

## Context and Orientation

The relevant backend lives in `src/foliaseal/application/phase3_signing_backend.py`. The two key
helpers are `_layout_reservation_for_template()`, which splits the signature rectangle into text and
stamp regions, and `_background_layout_for_stamp()`, which applies image-fit margins inside the
reserved stamp region. For horizontal positions, the code currently reserves text width based on a
measured text box and gives the remainder to the stamp. That is likely too conservative once the
final wrapped body footprint is considered.

The regression tests live in `tests/unit/test_phase3_signing_backend.py`.

## Plan of Work

Inspect the horizontal `single_line` path in `_layout_reservation_for_template()` and the fit logic
in `_background_layout_for_stamp()`. Determine whether the reservation is using a text width that is
larger than the final rendered width, or whether the image-fit step is failing to grow the stamp to
consume the reserved area. Then change only the horizontal `single_line` branch so it uses the text
footprint more effectively without changing the recently improved vertical `Top` and `Bottom`
behavior.

Add tests that encode the user-visible complaint: for a realistic horizontal rectangle, the stamp
area should be larger than before and should not leave an obvious amount of unused space while text
still fits honestly. Keep the tests scoped to backend helpers and signed-output facts where
possible.

## Concrete Steps

From `/home/daekar/SignPDF/Scratch`:

1. Inspect the current helpers:

       rg -n "_layout_reservation_for_template|_background_layout_for_stamp|single_line|LEFT|RIGHT" \
         src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

2. Implement the backend fit change in `src/foliaseal/application/phase3_signing_backend.py`.
3. Add or update focused tests in `tests/unit/test_phase3_signing_backend.py`.
4. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py
       ./.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

## Validation and Acceptance

Acceptance is reached when horizontal `single_line` layouts in the backend use the reserved stamp
area more effectively, the focused backend tests pass, and the change does not regress the improved
vertical behavior.

## Idempotence and Recovery

These edits are code-and-test only and safe to repeat. If a tentative change worsens vertical
output, revert that local edit and keep this plan updated rather than broadening scope.

## Artifacts and Notes

- Latest user evidence:
  - `single_line/top` and `single_line/bottom` actual PDF output now looks good
  - `single_line/left` and `single_line/right` still leave obvious unused horizontal space while
    the stamp remains too small

## Interfaces and Dependencies

Keep the implementation inside `src/foliaseal/application/phase3_signing_backend.py` and
`tests/unit/test_phase3_signing_backend.py`. Do not introduce new runtime dependencies.

Update note: created on 2026-04-01 after the latest harness run showed that the remaining backend
issue has narrowed to horizontal `single_line` stamp sizing.
