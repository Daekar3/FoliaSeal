# Shell Preview Scaling and Fixed-Width Contract

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`,
`Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`, the repository
`Agents.md`, and the parent wave plan `docs/ExecPlans/visible_signature_output_analysis_execplan.md`.

## Purpose / Big Picture

The visible-signature preview currently tells the truth too literally in the wrong coordinate
system. It uses raw PDF point dimensions as widget pixels, then fixes the inner body containers to
that same tiny size. The result is a preview card that becomes unusably small after the user draws a
normal form-line rectangle, hides almost all text, and can still nudge the settings panel into a
horizontal-scroll state. After this change, the preview should use a scaled fixed card that fills
the available preview area more usefully, preserves the selected rectangle's aspect ratio, keeps the
settings panel width stable, and shows overflow or clipping inside the card instead of making the UI
pretend the content fits.

This matters because the preview is the user's primary feedback loop before signing. If the preview
is too small to read or changes the surrounding panel geometry, it stops being a reliable signal
about whether the chosen font size and visible fields make sense.

## Progress

- [x] (2026-04-01 00:12Z) Reviewed `.agents/skills/write-execplan/PLANS.md`, `Agents.md`, the parent wave plan, and the
  current preview-sizing code before making changes.
- [x] (2026-04-01 00:15Z) Identified two concrete root causes in
  `src/foliaseal/presentation/qt/signing_shell.py`: raw PDF-point dimensions are being used as
  widget pixels, and the inner body containers are being fixed to the full card height.
- [x] (2026-04-01 00:23Z) Implemented a scaled fixed-card preview size that fits inside a stable
  preview viewport while preserving the selected rectangle's aspect ratio.
- [x] (2026-04-01 00:24Z) Stopped fixing the inner body containers to the full card height and
  instead kept them width-limited so overflow can happen inside the card.
- [x] (2026-04-01 00:25Z) Fixed `_set_container_widgets()` so vertical preview containers are
  repopulated correctly after refresh.
- [x] (2026-04-01 00:27Z) Updated focused Qt-shell tests to assert the new scaled preview contract
  and fixed-width panel behavior.
- [x] (2026-04-01 00:28Z) Ran focused pytest and ruff verification for the shell-preview slice.

## Surprises & Discoveries

- Observation: the preview width bug is entangled with the preview readability bug.
  Evidence: `_preview_body_size()` returns the raw signature rectangle width and height in points,
  while `_update_preview_controls()` also assigns that height to `single_body_container` and
  `multi_body_container`, leaving no space for the title line inside the same card.

- Observation: the preview stamp sizing is already using backend reservation logic, but then applies
  an arbitrary `0.5` scale factor that is unrelated to the actual display card size.
  Evidence: `_preview_stamp_max_size()` computes a reservation from backend-style geometry and then
  applies `preview_scale = 0.5` instead of the real display scale derived from the card.

- Observation: vertical preview refreshes were silently clearing their own content containers.
  Evidence: `_set_container_widgets()` had an unreachable `layout.addWidget(widget)` for non-tuple
  items, so the vertical `single_body_container` was emptied after `_clear_layout()` and never
  repopulated.

## Decision Log

- Decision: scale the preview card into a fixed preview viewport instead of mapping PDF points
  directly to widget pixels.
  Rationale: the preview must preserve aspect ratio, but it also needs to be readable by a human
  inside the properties panel. A scaled viewport satisfies both constraints without widening the UI.
  Date/Author: 2026-04-01 / Codex

- Decision: keep the outer preview card fixed-size, but stop fixing the inner body containers to the
  full card height.
  Rationale: the title, stamp, and detail text all need to compete for space inside the card. If
  the inner body is forced to the full card height, the title line effectively has no room and the
  content disappears.
  Date/Author: 2026-04-01 / Codex

- Decision: fix the container repopulation helper as part of this slice instead of treating it as a
  separate cleanup.
  Rationale: the helper bug directly affects the preview contract and was responsible for part of
  the “blank preview” behavior the user reported, especially on vertical layouts.
  Date/Author: 2026-04-01 / Codex

- Decision: keep the preview honest through clipping or overflow inside the card, not by panel
  growth or by silently shrinking unrelated geometry.
  Rationale: the user explicitly asked for the preview to stay the same size and let oversize text
  signal the problem directly.
  Date/Author: 2026-04-01 / Codex

## Outcomes & Retrospective

The preview now scales the selected rectangle into a fixed viewport instead of treating raw PDF
points as widget pixels. The outer preview container and the card remain width-limited, while the
inner body containers are no longer fixed to the card's full height. That keeps the panel stable and
lets the title and detail text remain visible inside the card instead of disappearing.

The focused Qt-shell suite passed after the change, and ruff stayed clean. The main remaining caveat
is that this slice only improves the preview geometry and refresh behavior; it does not by itself
relax backend fit rules or change final-PDF stamp placement.

## Context and Orientation

The code for this slice lives in `src/foliaseal/presentation/qt/signing_shell.py`. The preview card
is built by `SignaturePropertiesPanel._build_preview_controls()` and refreshed by
`SignaturePropertiesPanel._update_preview_controls()`. The sizing helpers are `_preview_body_size()`
and `_preview_stamp_max_size()`.

The tests for this slice live in `tests/unit/test_qt_signing_shell.py`. They use fake Qt widgets and
layouts that expose fields like `fixed_width`, `fixed_size`, `visible`, and `layout.items` so the
preview geometry can be asserted without a full Qt runtime.

In this plan, “fixed-width panel” means the outer preview container may change to reflect a new
selected rectangle, but it must not widen itself in response to oversized preview text. “Scaled
fixed card” means the preview uses the selected rectangle's aspect ratio while fitting inside a
stable preview viewport rather than using raw PDF point dimensions as pixels.

## Plan of Work

Update the preview sizing helper in `src/foliaseal/presentation/qt/signing_shell.py` so it returns a
scaled display size and the corresponding scale factor for the selected rectangle. Use a fixed
preview viewport large enough to remain readable inside the properties panel. The default no-rect
preview should continue to use a reasonable fallback size.

Then update `_preview_stamp_max_size()` so it uses the real display scale instead of the hard-coded
`0.5` multiplier. That keeps the preview stamp size aligned with the preview card size rather than
an arbitrary thumbnail rule.

Next, revise `_update_preview_controls()` so only the preview card itself is fixed-size. The inner
body containers should be width-limited but not fixed to the full card height, which allows the
title line and body content to occupy the card naturally and clip honestly if they overflow. The
horizontal `Left` and `Right` preview should still use the current `Stamp Position` semantics and
keep the text vertically centered beside the stamp.

Finally, update the focused tests in `tests/unit/test_qt_signing_shell.py` so they assert the new
scaled preview contract. The tests should prove that the panel no longer widens, the card is scaled
to a useful size, and oversize content still produces visible preview text instead of disappearing.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

1. Patch the preview sizing helpers in `src/foliaseal/presentation/qt/signing_shell.py`.
2. Patch `_update_preview_controls()` so the card is fixed-size but the inner body containers are
   width-limited instead of fixed-height.
3. Update `tests/unit/test_qt_signing_shell.py` for the new preview geometry contract.
4. Run:

       ./.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py
       ./.venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

## Validation and Acceptance

The change is acceptable when the focused Qt-shell tests pass and the preview contract is
demonstrably better for the next harness run. Specifically:

- the preview container no longer grows because of oversize text
- the preview card uses a scaled size that is larger and more readable than the raw PDF-point
  rectangle
- the selected rectangle's aspect ratio is preserved
- the title and detail text remain visible instead of disappearing because an inner body container
  consumed the full card height
- the `single_line` `Left` preview continues to use the current stamp-position semantics

## Idempotence and Recovery

These edits are safe to repeat. If a test expectation turns out to be too coupled to the old raw
point-size behavior, update the test to assert the new preview contract instead of weakening the
implementation back toward the buggy behavior.

## Artifacts and Notes

Current relevant observations from the latest harness run:

    - the preview card stays too small after drawing a normal rectangle
    - no visible text appears in the preview at 6.0 pt for ordinary `single_line` cases
    - the settings pane reintroduces a horizontal slider once the font reaches 5.0 pt
    - signing is blocked with `visible_signature_layout_unavailable` before the preview gives useful
      readable feedback

## Interfaces and Dependencies

This slice only changes `src/foliaseal/presentation/qt/signing_shell.py` and
`tests/unit/test_qt_signing_shell.py`. No new dependencies are needed. The implementation must keep
working with the existing fake Qt bindings in the tests.

Update note: revised on 2026-04-01 after the shell-preview fix landed. The revision records the
scaled fixed-card implementation, the `_set_container_widgets()` repopulation bug that was fixed in
the same slice, and the successful focused test/lint verification.
