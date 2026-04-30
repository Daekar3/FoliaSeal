# Backend Stamp Position and Visible Signature Layout Fixes

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

The user can now choose `Stamp Position` in the signing UI, but the final PDF still does not match
the intended visible-signature semantics for ordinary rectangles. After this change, a user should
be able to choose `Top`, `Bottom`, `Left`, or `Right` and see the final PDF place the stamp image
and visible text in the expected order, with the stamp sized sensibly for the rectangle and with
the label prefix staying where the preview says it belongs.

This work matters because it closes the most important preview/backend mismatch remaining in the
visible signature flow. The user should be able to verify the result by running the Phase 3 harness
against a normal document and observing that `single_line` signatures produce distinct `Top` and
`Bottom` outputs, that the stamp does not overwhelm the rectangle, and that the prefix is not
silently flattened into inline pipe-separated text when the preview says it should be separate.

## Progress

- [x] (2026-03-31 01:05Z) Created this ExecPlan and scoped the backend/layout fix wave.
- [ ] Inspect the current backend `single_line` implementation and the visible-text formatting path.
- [ ] Update the backend so `Top` and `Bottom` produce distinct final-PDF layouts and the stamp is
  constrained sensibly in ordinary rectangles.
- [ ] Add regression tests for `Top` / `Bottom`, oversized-stamp behavior, and the prefix/layout
  formatting mismatch.
- [ ] Run focused verification and decide whether the next harness pass is justified.

## Surprises & Discoveries

- Observation: the harness run exposed a semantic mismatch that is larger than a single rendering
  bug.
  Evidence: the final PDF showed a `single_line` `Top` / `Bottom` output that looked essentially the
  same, even though the preview was attempting to distinguish the order.

- Observation: the prefix behavior is not just a visual concern; the preview and backend disagree on
  whether the prefix occupies its own line or collapses into inline text.
  Evidence: the user observed the signed PDF showing the prefix inline and pipe-separated instead of
  on its own line as the preview suggested.

## Decision Log

- Decision: keep this wave focused on the backend/layout path rather than reopening broader shell
  work.
  Rationale: the user requested backend ownership and the harness regression points directly to the
  final PDF appearance path.
  Date/Author: 2026-03-31 / Codex

- Decision: treat the prefix formatting mismatch as part of the backend layout contract rather than a
  cosmetic preview issue.
  Rationale: the final PDF must match the preview and the user-visible contract, so the backend
  must honor the same shape of visible text.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

Pending. The target outcome is a backend that makes `Top` / `Bottom` materially distinct in the
final PDF, keeps stamp sizing reasonable, and produces a visible prefix/text arrangement that
matches the preview semantics for ordinary rectangles.

## Context and Orientation

Relevant files for this work are:

- `src/foliaseal/application/phase3_signing_backend.py`
- `tests/unit/test_phase3_signing_backend.py`
- tightly related support tests if the existing backend tests need shared helpers or fixtures

The backend builds the visible PDF appearance from a `SignatureAppearance` and a `SignatureRect`.
The `Stamp Position` control now feeds into that appearance. The harness run showed three problems
that this plan addresses:

- `single_line` `Top` and `Bottom` final PDFs look too similar
- the stamp image can still dominate the visible signature box
- the prefix/text formatting in the final PDF does not always mirror the preview contract

## Plan of Work

First, inspect the current backend functions that build the visible stamp text and stamp style.
Pay particular attention to the functions that compute the single-line visible text string, the
layout reservation, and the image stamp sizing logic. Determine where the preview/backend contract
is being collapsed into a single inline line even when the preview says otherwise.

Then update `src/foliaseal/application/phase3_signing_backend.py` so:

- `Top` and `Bottom` produce distinct `single_line` visible layouts in the final PDF
- the prefix text is preserved according to the contract instead of being flattened into a
  misleading inline form
- the stamp image is constrained more sensibly for ordinary rectangles so the visible appearance
  does not overwhelm the box

Finally, extend `tests/unit/test_phase3_signing_backend.py` with regression coverage that would have
caught:

- `Top` and `Bottom` looking the same in the final PDF
- a stamp image scaling too large in an ordinary rectangle
- the prefix/text formatting path producing the wrong visible arrangement

## Concrete Steps

From `/home/daekar/SignPDF/Scratch`:

1. Inspect `src/foliaseal/application/phase3_signing_backend.py` and the existing backend tests.
2. Edit the backend layout helpers and visible text assembly logic.
3. Add regression tests in `tests/unit/test_phase3_signing_backend.py`.
4. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py
       ./.venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

## Validation and Acceptance

Acceptance is reached when the backend tests prove all of the following:

- `single_line` `Top` and `Bottom` no longer collapse into the same visible output path.
- The stamp image is sized appropriately for an ordinary signature rectangle.
- The prefix/text formatting path matches the contract exercised by the preview and final PDF.
- Focused backend tests pass and lint is clean.

The user-facing proof comes from the next harness run, but this ExecPlan is only accepted when the
backend tests clearly cover the semantic gaps that the harness exposed.

## Idempotence and Recovery

These edits should be additive and safe. If a new test proves too brittle, adjust the helper
construction to reflect the actual contract rather than weakening the contract itself.

## Artifacts and Notes

- The harness run that triggered this plan reported:
  - `single_line` `Top` / `Bottom` looked too similar in the PDF
  - the stamp image was oversized in the actual PDF
  - the prefix line appeared inline and pipe-separated in the final PDF
- This plan intentionally keeps the backend and test work together so the next harness run has a
  better chance of being meaningful.

## Interfaces and Dependencies

The key interfaces are:

- `SignatureAppearance` and `SignatureStampPosition` in `src/foliaseal/domain/models.py`
- `_build_stamp_text`, `_layout_reservation_for_template`, `_build_stamp_style`, and related
  helpers in `src/foliaseal/application/phase3_signing_backend.py`
- backend regression tests in `tests/unit/test_phase3_signing_backend.py`

No new external dependencies are expected.

