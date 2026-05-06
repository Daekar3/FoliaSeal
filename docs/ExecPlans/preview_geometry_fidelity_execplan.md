# Preview Geometry Fidelity ExecPlan

Date: 2026-04-02
Owner: Codex

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Goal

Tighten the preview box geometry so the on-screen preview rectangle matches the selected PDF rectangle's aspect ratio more faithfully at the fixed available pane width.

After this change, the preview should no longer look deceptively roomy just because the card has been stretched far beyond physical PDF scale. The same selected point size should mean the same thing across layout modes, and narrow-box failures should become visually obvious in the preview instead of only appearing in the validation status.

## Progress

- [x] (2026-04-02) Created the original geometry-fidelity plan.
- [x] (2026-04-09 21:52Z) Reopened the plan after the latest manual harness run showed that `multi_line top` previews still looked signable while backend validation correctly rejected them.
- [x] (2026-04-09 21:58Z) Identified the remaining root cause: the preview card is still stretched to pane width, so the card can be magnified far beyond physical PDF scale while text remains at real point size.
- [x] (2026-04-09 22:06Z) Updated `_preview_body_size()` to cap preview magnification at physical PDF-to-screen scale, added focused Qt regressions for that cap, and verified the targeted and full test suites.

## Surprises & Discoveries

- Observation: after restoring layout-invariant text sizing, the remaining false `multi_line top` failures were not caused by text scaling anymore; they were caused by the preview card itself being enlarged too aggressively.
  Evidence: in the latest harness capture, a `~96pt` wide `multi_line top` rectangle rendered into a `206px` wide card, which made `8.5pt` text look comfortably placed even though backend reservation only allowed `88pt` of text width.

- Observation: capping preview geometry to physical scale addresses the honesty problem uniformly across all layouts without introducing a new behavior mode for narrow rectangles.
  Evidence: the card-width calculation is global in `_preview_body_size()`, so the fix applies to `single_line`, `multi_line`, and `wrapped_block` alike.

## Decision Log

- Decision: fix preview honesty by limiting preview-card magnification to physical PDF-to-screen scale instead of changing text behavior again.
  Rationale: once text-size semantics were made layout-invariant, the remaining drift came from card geometry, not typography. A global scale cap applies continuously across the entire range of rectangle sizes and avoids reintroducing layout-specific preview rules.
  Date/Author: 2026-04-09 / Codex

## Outcomes & Retrospective

The reopened geometry slice succeeded. Preview card size no longer outruns text scale as aggressively, so validation failures in narrow boxes should now be reflected more honestly on screen. The change is intentionally global: there is no new threshold-specific preview mode.

## Scope

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`
- optional diagnostic notes in `docs/ExecPlans/`

## Steps

1. Trace preview geometry.
- follow `_preview_available_width()`
- `_preview_body_size()`
- `_preview_display_scale()`
- `_update_preview_controls()`
- identify where aspect ratio is being distorted

2. Decide whether the mismatch comes from:
- width budgeting
- hard max-height clamping
- card/container padding assumptions
- integer rounding / body-vs-card overhead

3. Implement the smallest safe geometry correction.
- preserve stable pane width
- preserve fixed-width preview behavior
- improve rectangle fidelity without reopening scrollbar regressions

4. Add focused regression tests.

5. Verify locally and document any remaining non-geometry parity gaps.

## Success criteria

- preview box aspect ratio is materially closer to the selected rectangle
- pane remains stable
- tests pin the intended geometry behavior
