# Shell Preview Sizing Fixes for Visible Signature Output

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md` and the parent wave plan
`/.agent/visible_signature_output_analysis_execplan.md`.

## Purpose / Big Picture

The signing shell currently stretches its properties panel and preview card when the visible
signature text becomes too long. That makes the preview misleading: the panel looks like the text
fits because the UI grows to make room, but the final PDF does not. After this fix, the preview
panel should stay the same size, show the selected signature rectangle’s aspect ratio honestly, and
let text overflow or clip inside the preview card when the chosen font size or field set is too
large. A user should be able to see, immediately, that the current settings do not fit instead of
having the UI quietly expand to hide the problem.

This matters because the preview is part of the contract between the user and the final PDF. If the
preview grows to fit content, it stops being a trustworthy signal about what will actually be
signed.

## Progress

- [x] (2026-03-31 23:58Z) Created this ExecPlan for the shell preview sizing worker.
- [x] (2026-03-31 01:10Z) Inspected the current preview card and properties-panel sizing path in
  `src/foliaseal/presentation/qt/signing_shell.py` and identified the outer preview container as
  part of the width-growth problem.
- [x] (2026-03-31 01:18Z) Added explicit width limits to the preview container, preview card, and
  preview text widgets so oversized content clips instead of widening the panel.
- [x] (2026-03-31 01:20Z) Added regression tests in `tests/unit/test_qt_signing_shell.py` proving
  the preview container and preview card keep fixed geometry.
- [x] (2026-03-31 01:21Z) Ran focused shell tests and lint successfully.

## Surprises & Discoveries

- Observation: the preview can pass fake-Qt tests while still widening the real panel in PySide.
  Evidence: earlier shell fixes caught layout-order bugs in tests, but the user still observed the
  actual properties panel widening when the drawn rectangle and text were large.

- Observation: fixing only the inner preview card was not enough to stop width growth.
  Evidence: the outer preview container still needed an explicit width limit, or the panel could
  expand through its size hint even when the card itself was fixed-size.

## Decision Log

- Decision: keep the preview sizing behavior fixed rather than letting it grow to accommodate text.
  Rationale: a faithful preview must show the user when their requested font size or field set does
  not fit; panel growth hides that information.
  Date/Author: 2026-03-31 / Codex

- Decision: width-limit both the outer preview container and the inner preview card/text widgets.
  Rationale: the fake-Qt tests and the user’s report both showed that the outer container can still
  drive panel growth even if the inner card is fixed-size, so the width contract must be enforced at
  both layers.
  Date/Author: 2026-03-31 / Codex

## Outcomes & Retrospective

The shell preview now keeps the preview container and preview card width-limited even when the
draft text is oversized. That means the panel no longer widens to make long content look like it
fits; instead, the preview remains honest and lets content clip or overflow inside the fixed
geometry. The focused Qt shell tests and the harness-facing shell tests both pass, so the worker
slice achieved its intended visible behavior.

The main lesson from this pass is that the outer preview container mattered as much as the inner
card. Fixing only the card was not enough, because the container’s own width hint could still push
the properties panel wider. The final fix had to constrain both layers.

## Context and Orientation

The relevant code lives in:

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`

The `SignaturePropertiesPanel` inside `signing_shell.py` builds both the editable form controls and
the preview card. The problem described by the user happens when the preview content becomes large
enough that the surrounding panel starts to widen. That should not happen. The preview should be a
fixed-size representation of the selected signature rectangle, not a responsive text layout that
pushes the whole UI wider.

When I say “honest overflow,” I mean the preview should keep its fixed size and allow text or stamp
content to run out of room visibly or clip within the preview card. It should not resize the
properties panel to avoid the overflow. That behavior tells the user the settings need to be made
smaller.

## Plan of Work

Inspect the preview card construction in `src/foliaseal/presentation/qt/signing_shell.py`, with
special attention to any widget or layout calls that can change size hints after the preview text or
stamp image updates. The key targets are the `PreviewControls` widgets, `_build_preview_controls()`,
and `_update_preview_controls()`.

Then make the preview explicitly use a fixed geometry derived from the selected signature
rectangle’s aspect ratio. If a Qt size policy or fixed-size setter is needed, apply it to the
preview container and the content widgets so the panel does not widen itself when text becomes too
long. Prefer honest clipping/overflow over dynamic growth.

Finally, add tests in `tests/unit/test_qt_signing_shell.py` that prove the properties panel remains
stable when the visible text is oversized. The tests should fail before the fix and pass after it by
checking that the preview container keeps a fixed size or fixed-size policy and that content updates
do not change the panel’s width-hint behavior in the fake Qt layer.

## Concrete Steps

From `/home/daekar/SignPDF/Scratch`:

1. Inspect `src/foliaseal/presentation/qt/signing_shell.py` for any preview container size or size
   policy manipulation that can cause the panel to widen.
2. Edit the preview container setup so it keeps a fixed size or fixed-size policy tied to the
   selected rectangle.
3. Add tests in `tests/unit/test_qt_signing_shell.py` for the fixed-size preview behavior and for
   the case where text is too large.
4. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

## Validation and Acceptance

Acceptance is reached when all of these are true:

- the properties panel no longer widens when preview text is too large
- the preview card stays fixed to the selected rectangle’s aspect ratio
- oversized text is shown honestly through overflow or clipping rather than resizing the panel
- focused shell tests pass and lint is clean

The user-visible proof is a harness run where the control panel stays the same width after drawing
the rectangle, even if the text is too large to fit neatly.

## Idempotence and Recovery

These edits should be additive and safe to repeat. If a fixed-size rule proves too strict for a fake
Qt test, adjust the test doubles to reflect the intended contract instead of weakening the contract
itself.

## Artifacts and Notes

- User observations to address:
  - the panel widens after drawing the rectangle
  - shrinking the text size can hide the problem, which means the preview is not acting like a fixed
    visible-signature card
- The goal is not to eliminate all clipping; the goal is to make the clipping visible and honest.

## Interfaces and Dependencies

No new dependencies are expected. The main interfaces are:

- `SignaturePropertiesPanel` in `src/foliaseal/presentation/qt/signing_shell.py`
- the preview container widgets in `PreviewControls`
- the fake Qt bindings and layout doubles in `tests/unit/test_qt_signing_shell.py`

Any future edits in this wave should keep the preview container’s geometry stable and should not
rely on stretching the properties panel to make content fit.

Update note: revised on 2026-03-31 after the shell preview width-lock fix landed and the
regression tests were expanded to prove the outer preview container and inner preview card stay
fixed instead of growing with oversized content.
