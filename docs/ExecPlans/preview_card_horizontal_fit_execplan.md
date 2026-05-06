# Preview Card Scaling and Horizontal Stamp Fit Follow-up

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The last harness rerun showed that the signed PDF is now much better for `single_line` `Top` and
`Bottom`, but two issues remain: the shell preview card still behaves like a tiny clipped viewport,
and the backend still makes the stamp too small for `single_line` `Left` and `Right`. After this
follow-up, the preview should use the available panel width while preserving aspect ratio, and the
horizontal stamp positions should use the reserved area more effectively so the stamp does not look
needlessly shrunken beside readable text.

## Progress

- [x] (2026-04-01 00:25Z) Created this ExecPlan from the latest harness findings.
- [x] (2026-04-01 00:31Z) Fixed shell preview card/body sizing so the card width follows the available preview width, while the body region keeps the signature-rectangle aspect ratio.
- [x] (2026-04-01 00:33Z) Fixed backend horizontal `single_line` wrapping so `Left` and `Right` reserve stamp space before wrapping the text body and allow bounded width overflow.
- [x] (2026-04-01 00:34Z) Added focused regression tests covering the revised shell sizing contract and the more aggressive horizontal wrapping behavior.
- [x] (2026-04-01 00:35Z) Ran the focused pytest and ruff slices successfully.

## Surprises & Discoveries

- Observation: the preview can show only the border even when validation says the layout is signable.
  Evidence: the shell currently fixes `card_container` to the body size, even though the card also
  contains the title row and padding.

- Observation: horizontal `Left`/`Right` output still leaves unused space beside the text.
  Evidence: `_build_stamp_text()` wraps against the full rectangle width before the left/right
  reservation logic subtracts stamp space.

- Observation: the shell preview bug was not just “too small”; the card was literally fixed to the
  body height, leaving no guaranteed room for the title/detail stack.
  Evidence: `_update_preview_controls()` previously applied `setFixedSize(body_width, body_height)`
  to `card_container`, even though that widget also contains the title row and outer padding.

## Decision Log

- Decision: keep this follow-up local and focused instead of reopening the larger wave.
  Rationale: the remaining bugs are concentrated in `signing_shell.py` and
  `phase3_signing_backend.py`, and the harness/output analysis slice is already providing the
  evidence we need.
  Date/Author: 2026-04-01 / Codex

- Decision: use the actual preview-container width when available, but only fix the outer card
  width and the inner body size separately.
  Rationale: the user wants the preview to use available panel width without widening the panel,
  and separating outer-card width from inner-body height preserves visibility of the title/detail
  stack.
  Date/Author: 2026-04-01 / Codex

- Decision: keep horizontal `Left`/`Right` wrapping conservative but allow bounded overflow after
  reserving stamp width.
  Rationale: constraining the body width before wrapping gives the stamp more room, but a strict
  hard limit created a new rejection path for realistic content. A bounded overflow tolerance keeps
  the improvement without making horizontal layouts brittle.
  Date/Author: 2026-04-01 / Codex

## Outcomes & Retrospective

This follow-up landed two concrete improvements. The shell preview now uses the available preview
width instead of a tiny static viewport, and the outer card is no longer clipped to the inner body
height. That should make the preview human-usable again without widening the panel. On the backend,
horizontal `single_line` now wraps after reserving stamp space, which should let `Left` and `Right`
use the stamp area more effectively while keeping text readable.

The remaining proof is the next harness rerun. That rerun needs to confirm the shell stays stable
and that the horizontal stamp is no longer obviously undersized.

## Context and Orientation

The shell preview lives in `src/foliaseal/presentation/qt/signing_shell.py`. The current preview
size helpers compute a body size, but `_update_preview_controls()` applies that size to the entire
card container, which clips the title/detail stack into an almost empty-looking box. The backend
layout lives in `src/foliaseal/application/phase3_signing_backend.py`; for horizontal
`single_line`, it currently wraps the body text using the full rectangle width, then reserves stamp
space afterward, which leaves the stamp smaller than necessary.

## Plan of Work

First, change the shell preview sizing so the body region keeps the signature-rectangle aspect
ratio, but the outer card only fixes its width. Use the available preview-container width when
computing the body size instead of a tiny static viewport when possible. Then add or adjust tests so
they prove the preview card remains stable, uses more width, and keeps the text visible.

Second, change the backend `single_line` text wrapping for `Left` and `Right` so it wraps against a
constrained text width that already accounts for reserved stamp space. Then cover that behavior with
focused backend tests that show the horizontal path keeps readable text while leaving more room for
the stamp.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

1. Edit `src/foliaseal/presentation/qt/signing_shell.py` and `tests/unit/test_qt_signing_shell.py`.
2. Edit `src/foliaseal/application/phase3_signing_backend.py` and `tests/unit/test_phase3_signing_backend.py`.
3. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/application/phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_signing_backend.py

## Validation and Acceptance

Acceptance means the shell preview uses the available panel width without widening the panel, the
preview text remains visible inside the card when the layout is signable, and `single_line`
`Left`/`Right` leaves less obvious unused space beside the text in the next harness rerun.

## Idempotence and Recovery

These changes are code-and-test only. If a test assumption turns out to be stale, update the test
to match the intended preview/backend contract rather than weakening the code change.

## Artifacts and Notes

Latest manual evidence:

    - `single_line/top` and `single_line/bottom` now look good in the final PDF.
    - the preview card still uses only about one-third to one-half of the available width.
    - `single_line/left` and `single_line/right` still produce a stamp that is smaller than necessary.

## Interfaces and Dependencies

No new dependencies are required. Keep the shell changes inside `signing_shell.py` and the backend
changes inside `phase3_signing_backend.py`, with focused unit coverage in their existing test
modules.
