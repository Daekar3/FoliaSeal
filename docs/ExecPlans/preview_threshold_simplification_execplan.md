# Preview Threshold Simplification ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The visible-signature preview should scale smoothly as the user changes the rectangle size, border weight, font size, stamp position, and layout template. Today the preview still contains several hardcoded cutoffs such as `<= 24`, `<= 28`, and `<= 40` that change spacing and wrapping behavior abruptly. After this change, the preview should use one coherent, geometry-driven layout policy so the same content simply gets tighter or looser as space changes, instead of switching into hidden compact modes. The visible proof is that the preview code no longer contains those threshold branches, the existing preview tests still pass, and the preview continues to render all supported layouts with deterministic sizing.

## Progress

- [x] (2026-04-05 14:25Z) Re-read `Agents.md`, `.agents/skills/write-execplan/PLANS.md`, and the current preview/back-end layout helpers before planning.
- [x] (2026-04-05 14:31Z) Audited threshold-driven preview logic and confirmed the main simplification targets are `src/foliaseal/presentation/qt/signing_shell.py::_preview_detail_text`, `::_single_line_vertical_separator_cap`, `::_preview_stamp_max_size`, and the vertical band fitting path in `::_update_preview_controls`.
- [x] (2026-04-05 14:42Z) Removed the preview-only threshold branches in `src/foliaseal/presentation/qt/signing_shell.py` by deleting the local `single_line` compact wrap logic, deleting `_single_line_vertical_separator_cap()`, and replacing threshold-based preview padding and stamp gutters with continuous geometry-driven helpers.
- [x] (2026-04-05 14:44Z) Updated the focused preview test that still asserted the deleted `6px` vertical compact padding special case.
- [x] (2026-04-05 14:47Z) Re-ran the focused verification commands and confirmed `123 passed` plus clean `ruff` results.

## Surprises & Discoveries

- Observation: the preview duplicates back-end wrapping heuristics instead of consuming one shared reservation model.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py::_preview_detail_text` reproduces vertical `<= 24` and horizontal stamp-width reservation branches locally instead of relying on `_layout_reservation_for_template()`.

- Observation: the preview adds threshold-driven spacing even after the reservation split has already been computed.
  Evidence: `src/foliaseal/presentation/qt/signing_shell.py::_single_line_vertical_separator_cap` applies `<= 24` and `<= 28` cutoffs on top of the reservation-driven text/stamp band heights.

- Observation: the remaining arbitrary thresholds in the preview are concentrated in `single_line`; the other templates do not appear to have the same mode-switching complexity in the Qt layer.
  Evidence: the threshold inventory in `src/foliaseal/presentation/qt/signing_shell.py` is localized to the `single_line` sizing and wrapping helpers rather than the wrapped-block or stacked-block preview branches.

- Observation: the simplest safe way to remove the preview’s local threshold branches was to reuse the backend’s shared `single_line` wrap-limit helper instead of inventing a second “clean” preview policy in the same slice.
  Evidence: replacing the branchy code in `_preview_detail_text()` with a call to `_single_line_text_wrap_limits()` preserved the current wrapping semantics while eliminating the duplicated preview cutoffs.

- Observation: after this slice, the preview file no longer contains the explicit `24`, `26`, `28`, `34`, or `40` cutoff branches or the word `compact`.
  Evidence: `rg -n "<=\\s*(24|26|28|34|40)|compact|threshold" src/foliaseal/presentation/qt/signing_shell.py` returns no matches.

## Decision Log

- Decision: keep this change slice focused on the preview layer, even though the backend still contains threshold-heavy helpers.
  Rationale: the user explicitly asked for an ExecPlan and implementation effort for the preview code, and mixing a broader backend reservation rewrite into the same slice would make the review and regression surface much harder to control.
  Date/Author: 2026-04-05 / Codex

- Decision: remove preview-specific threshold branches even when the backend still has similar heuristics.
  Rationale: duplicating those heuristics in the preview is the larger immediate maintenance hazard because it creates two separate behavior policies. The preview can still consume the backend reservation split while avoiding additional mode switches of its own.
  Date/Author: 2026-04-05 / Codex

- Decision: use continuous calculations derived from available inner width, inner height, title-row height, and measured text size hints instead of explicit compact-mode cutoffs.
  Rationale: that follows the user’s direction that layout should respond to actual geometry and content needs rather than arbitrary thresholds.
  Date/Author: 2026-04-05 / Codex

- Decision: keep the backend threshold helpers out of scope for this slice, but let the preview call the shared `_single_line_text_wrap_limits()` helper instead of reimplementing its own branchy version.
  Rationale: this removes duplicated preview complexity immediately while keeping the change slice narrow enough to verify safely. The remaining backend threshold debt should be addressed in a separate reservation-model simplification effort.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The preview simplification landed as intended. The preview code in `src/foliaseal/presentation/qt/signing_shell.py` no longer carries the explicit compact-size cutoffs that had accumulated in the `single_line` path. The preview now relies on a shared wrap-limit helper for `single_line`, uses continuous local padding and stamp-gutter calculations, and no longer applies a second separator-cap mode switch after the reservation split is known.

The result is narrower than a full layout-architecture rewrite, but it meaningfully improves the shape of the preview layer: there is less duplicated policy, less threshold drift, and less code that can diverge from the backend by accident. The remaining threshold-heavy logic is now more clearly isolated in the backend reservation layer, which makes the next simplification wave easier to scope.

## Context and Orientation

The interactive visible-signature preview lives in `src/foliaseal/presentation/qt/signing_shell.py`. The main refresh method is `SignaturePropertiesPanel._update_preview_controls()`. That method takes a `SigningDraftPreview`, computes the card size, measures visible text, sizes the stamp image, and updates the Qt widgets that represent the preview. The preview uses two major widget arrangements: a vertical arrangement for `single_line` when the stamp position is `top` or `bottom`, and a horizontal arrangement for positions such as `left` and `right`.

The preview currently depends on several helpers imported from `src/foliaseal/application/phase3_signing_backend.py`. Those helpers compute text measurements, border-safe margins, and the broad stamp/text reservation split. That shared reservation model is useful and should remain. The problematic complexity comes from the extra preview-only branches layered on top, especially the threshold-driven wrapping logic in `_preview_detail_text()` and the separator-capping logic in `_single_line_vertical_separator_cap()`.

For this plan, “threshold branch” means a branch whose behavior changes because a rectangle crosses an arbitrary size cutoff such as `24pt`, `28pt`, or `40pt`, rather than because a different layout template or stamp position is selected. A “continuous geometry-driven calculation” means a formula that uses actual available width, available height, title-row height, and measured content size to choose the result without flipping into a different mode.

The main files in scope are:

- `src/foliaseal/presentation/qt/signing_shell.py` for the preview logic itself.
- `tests/unit/test_qt_signing_shell.py` for preview behavior and widget-geometry regressions.
- Optionally `tests/unit/test_phase3_harness.py` if any helper behavior exposed through harness capture changes as a direct consequence of the preview refactor.

The primary change class for this slice is behavior change in the preview layer. Test updates are allowed because they are direct evidence for the changed behavior. Documentation changes are intentionally limited to this ExecPlan unless verification reveals a user-facing workflow change that must be documented elsewhere.

## Plan of Work

First, simplify text wrapping in `src/foliaseal/presentation/qt/signing_shell.py::_preview_detail_text()`. Instead of reproducing the backend’s compact vertical and horizontal stamp reservation thresholds, compute a single preview text budget from the actual preview geometry: start from the signature rectangle, subtract the border-safe edge margin, subtract any dedicated title row that is already rendered separately, and for horizontal stamp positions subtract the stamp width that the shared reservation model actually reserves. Then call `_wrap_visible_signature_fragments()` with those continuous width and height budgets. If the wrapped text still does not fit, fall back deterministically to the simple joined string instead of branching on compact mode.

Second, simplify the vertical `single_line` band fitting in `src/foliaseal/presentation/qt/signing_shell.py`. Remove `_single_line_vertical_separator_cap()` entirely. After `_preview_vertical_band_geometry()` returns the reservation-driven split, fit the text and stamp bands against the live Qt size hints by reclaiming or redistributing the separator height continuously. The separator should be whatever space remains after honoring the actual fitted text height and the reserved stamp band, not a threshold-capped value.

Third, simplify stamp sizing in `src/foliaseal/presentation/qt/signing_shell.py::_preview_stamp_max_size()`. Keep the idea of fitting the pixmap into the reserved stamp area, but replace threshold-driven stamp-content insets with a continuous gutter derived from the visible border and the preview scale. That keeps the preview stamp away from borders without switching behavior at arbitrary rectangle heights.

Fourth, audit the non-`single_line` preview branches while touching the refresh path. The expectation from the current inventory is that the other layout templates already avoid this threshold complexity, so the implementation should leave them alone except where shared helper cleanup naturally simplifies them as well.

Finally, expand the tests in `tests/unit/test_qt_signing_shell.py` so they prove the preview no longer relies on the deleted helper branches. The tests should cover at least one vertical `single_line` case, one horizontal `single_line` case, and one non-`single_line` case to show that the simplified helper behavior remains stable outside the main target.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Read and edit the preview logic:

    sed -n '420,980p' src/foliaseal/presentation/qt/signing_shell.py
    sed -n '1810,2145p' src/foliaseal/presentation/qt/signing_shell.py

Update or add preview tests:

    rg -n "preview_detail_text|single_body_container|multi_body_container|stamp_label" tests/unit/test_qt_signing_shell.py

Run focused verification:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py

Expected test transcript after the implementation:

    1..N
    ...
    120+ passed

Expected `ruff` transcript after the implementation:

    All checks passed!

## Validation and Acceptance

The change is acceptable only if all of the following are true:

- `src/foliaseal/presentation/qt/signing_shell.py` no longer contains the preview-only threshold branches targeted by this plan, especially the `<= 24` and `<= 28` cutoffs in the vertical `single_line` path.
- The preview still renders vertical and horizontal `single_line` arrangements using the shared reservation split, but the extra preview behavior now scales continuously with geometry instead of switching modes.
- The focused preview test suite passes, showing that the vertical title row, stamp placement, and horizontal content layout still work after the simplification.
- No unrelated workflow behavior changes are mixed into this slice.

## Idempotence and Recovery

These edits are safe to repeat because they only change deterministic helper logic and tests in the working tree. If a simplification attempt causes preview regressions, revert only the local helper being changed, rerun the focused preview tests, and record the failed approach in `Surprises & Discoveries` and `Decision Log` before trying a narrower change. Do not mix backend reservation rewrites into this slice as a recovery strategy.

## Artifacts and Notes

The most important artifact for this plan is the updated source itself. The concrete proof comes from the absence of the threshold branches in `src/foliaseal/presentation/qt/signing_shell.py` and from the focused preview tests passing.

Observed verification transcript:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    123 passed in 2.77s

    $ .venv/bin/ruff check src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_qt_signing_shell.py
    All checks passed!

## Interfaces and Dependencies

No new runtime dependencies are allowed. Use the existing helpers already imported by `src/foliaseal/presentation/qt/signing_shell.py`, especially `_layout_reservation_for_template`, `_measure_text_box_dimensions`, `_build_text_box_style`, and `_wrap_visible_signature_fragments`, when they help keep the preview aligned with the backend reservation model. Any new helper added in the preview module must be private to `signing_shell.py` unless there is a second concrete use in the current codebase.

Revision note: created on 2026-04-05 after a focused preview audit showed that the Qt preview still contained multiple threshold-driven `single_line` branches, even after earlier harness and matrix work improved visible behavior. The purpose of this plan is to remove those preview-only mode switches and replace them with continuous geometry-driven calculations.

Revision note: updated on 2026-04-05 after implementation. The preview now uses continuous padding and stamp-gutter helpers, no longer contains the targeted threshold branches, and the focused verification suite passes.
