# Preview Geometry Fidelity ExecPlan

Date: 2026-04-02
Owner: Codex

## Goal

Tighten the preview box geometry so the on-screen preview rectangle matches the selected PDF rectangle's aspect ratio more faithfully at the fixed available pane width.

## Scope

- `src/foliaseal/presentation/qt/signing_shell.py`
- `tests/unit/test_qt_signing_shell.py`
- optional diagnostic notes in `.agent/`

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
