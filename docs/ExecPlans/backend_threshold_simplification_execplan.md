# Backend Threshold Simplification ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It follows the preview-only simplification work recorded in `docs/ExecPlans/preview_threshold_simplification_execplan.md`.

## Purpose / Big Picture

The visible-signature backend should decide whether content fits, how much space text and stamps receive, and how stamp images are inset using one coherent geometry-driven model. Today the backend still contains several hardcoded size cutoffs and one-off “compact” branches in the `single_line` path. After this change, the backend should preserve the same user-visible output requirements while removing those arbitrary mode switches, so the layout scales continuously with rectangle size and border weight. The visible proof is that the backend no longer contains the targeted threshold branches, the preview still builds against the shared backend helpers, and the targeted backend and preview test suites continue to pass.

## Progress

- [x] (2026-04-05 15:02Z) Re-read the current backend reservation and wrap helpers in `src/foliaseal/application/phase3_signing_backend.py`, the preview simplification ExecPlan, and the tests that still assert compact-only helper behavior.
- [x] (2026-04-05 15:11Z) Replaced the backend `single_line` threshold branches with continuous helpers for vertical spacing, vertical outer margin, stamp gutter, and orientation-based width overflow tolerance.
- [x] (2026-04-05 15:16Z) Removed the compact-only body-wrap fallback in `_build_stamp_text()` and rewrote the directly coupled backend tests to assert stable behavior instead of the deleted threshold shape.
- [x] (2026-04-05 15:18Z) Ran the targeted backend/preview suite and confirmed `123 passed` plus clean `ruff` results.
- [x] (2026-04-05 15:19Z) Ran the broader automated suite and confirmed `312 passed`; no additional stale-assumption tests required changes outside the focused backend test file.

## Surprises & Discoveries

- Observation: the backend still has the highest concentration of threshold-driven logic, especially in `_base_layout_spacing()`, `_single_line_vertical_outer_margin()`, `_single_line_stamp_content_inset()`, `_ensure_layout_can_fit()`, `_should_prefer_compact_single_line_body()`, and `_single_line_text_wrap_limits()`.
  Evidence: `src/foliaseal/application/phase3_signing_backend.py` currently contains the explicit `<= 24`, `<= 26`, `<= 34`, and `<= 40` branches that the preview used to duplicate.

- Observation: several existing backend tests assert the threshold helpers directly rather than asserting a user-visible output requirement.
  Evidence: `tests/unit/test_phase3_signing_backend.py::test_single_line_stamp_content_inset_targets_compact_cases` and several tests whose names still encode “compact” are tied to the deleted implementation shape instead of the observable behavior.

- Observation: the first simplification pass caused a genuine regression in vertical `single_line` fit acceptance before the broader contract changes were complete.
  Evidence: the targeted suite initially failed `test_build_stamp_text_accepts_compact_vertical_single_line_with_modest_width_overflow` and the two six-point vertical fit-acceptance tests until the vertical width overflow tolerance was restored as a continuous orientation policy instead of being removed entirely.

- Observation: after the focused backend test updates, the rest of the automated suite did not depend on the deleted threshold behavior.
  Evidence: `.venv/bin/python -m pytest -q` completed with `312 passed in 2.87s`.

## Decision Log

- Decision: keep this backend simplification slice focused on removing threshold-driven layout branches, not on the larger signer-label/title-band architectural mismatch.
  Rationale: the threshold cleanup is already substantial and independently valuable. Mixing the title-band redesign into the same slice would make it hard to separate geometry-policy simplification from a user-visible layout restructuring.
  Date/Author: 2026-04-05 / Codex

- Decision: preserve the existing user-visible `single_line` output contracts where possible, even if some tests that mention “compact” must be rewritten.
  Rationale: the user explicitly called out that the assumptions being changed are implementation details, not output requirements. Test updates should follow that principle.
  Date/Author: 2026-04-05 / Codex

- Decision: keep a bounded width-overflow tolerance for `single_line`, but make it depend only on layout orientation rather than rectangle-height thresholds.
  Rationale: removing the compact-only vertical tolerance entirely caused real regressions in realistic vertical fit acceptance. An orientation-based allowance keeps the model simple and continuous while preserving the output contract.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The backend simplification landed successfully. `src/foliaseal/application/phase3_signing_backend.py` no longer contains the targeted `<= 24`, `<= 26`, `<= 34`, and `<= 40` compact-mode branches in the `single_line` reservation and wrap path. The backend now uses continuous vertical spacing, a uniform stamp-content gutter, and an orientation-based width overflow policy instead of threshold-triggered alternate modes.

The only meaningful regression encountered during the work was that removing the vertical width-overflow allowance entirely made realistic vertical `single_line` cases fail again. Restoring that allowance as a simple orientation-based policy fixed the regression without reintroducing the deleted height thresholds.

The broader test suite result is especially important: `312 passed` means the threshold removal was indeed mostly an implementation-detail change. The only tests that needed updates were the focused backend tests that were directly asserting the old helper outputs or compact-specific wording.

## Context and Orientation

The signing backend for Phase 3 lives in `src/foliaseal/application/phase3_signing_backend.py`. The critical functions for this change are:

- `_layout_reservation_for_template()`, which splits the selected signature rectangle into a text area and a stamp area.
- `_background_layout_for_stamp()`, which fits the image stamp into the reserved stamp area.
- `_build_stamp_text()`, which chooses how the visible fields are wrapped into one or more text lines.
- `_ensure_layout_can_fit()`, which decides whether the chosen wrapped text honestly fits inside the reservation.

The preview in `src/foliaseal/presentation/qt/signing_shell.py` now depends on the backend for its `single_line` wrap limits. That means backend simplification is now the next important source of complexity reduction, because the preview no longer carries its own independent cutoff logic.

For this plan, a “threshold branch” means a backend branch that changes policy because a rectangle crosses a hardcoded size cutoff such as `24pt`, `26pt`, `34pt`, or `40pt`. A “continuous geometry-driven helper” means a helper that derives its result from the actual rectangle width, height, border width, or measured content size without switching into a separate compact mode.

The files in scope are:

- `src/foliaseal/application/phase3_signing_backend.py` for the backend reservation, fitting, and wrap helpers.
- `tests/unit/test_phase3_signing_backend.py` for backend regression coverage.
- `tests/unit/test_qt_signing_shell.py` only if a changed backend helper changes a preview-facing expectation.

The primary change class for this slice is behavior change in the backend reservation and wrap policy. Evidence refresh is allowed only through test updates that prove the intended behavior remains intact.

## Plan of Work

First, replace the threshold-driven `single_line` spacing helpers in `src/foliaseal/application/phase3_signing_backend.py` with continuous helpers. `_base_layout_spacing()` should no longer branch on `<= 40` for vertical layouts. `_single_line_vertical_outer_margin()` should stop adding a compact-only bonus, and `_single_line_stamp_content_inset()` should stop switching between `0` and `1` based on hardcoded size cutoffs. These helpers should instead derive edge margins, separator gaps, and stamp gutters from actual box geometry and visible border thickness.

Second, simplify the `single_line` wrap and fit path. `_ensure_layout_can_fit()` should stop enabling a special width-overflow tolerance only for `top`/`bottom` rectangles at `<= 24pt`. `_build_stamp_text()` should stop calling `_should_prefer_compact_single_line_body()`, and that helper should be removed. `_single_line_text_wrap_limits()` should become the single place where `single_line` wrap policy is derived from geometry. Horizontal stamp reservations may still differ from vertical ones because left/right layouts are semantically different, but that difference must be encoded as a continuous reservation rule, not a compact-mode exception.

Third, update or remove tests that assert deleted implementation details. The tests should continue to verify border-aware insets, stamp alignment, realistic fit acceptance, and honest rejection of overfull rectangles, but they should not require a specific threshold helper to return `1` only at one hardcoded box size if that is no longer part of the design.

Finally, run the targeted suite that covers the backend, the preview, the harness capture path, and the signing preview renderer. Then inspect the broader automated suite for failures. If that broader run reveals tests that encoded the old threshold implementation shape rather than real behavior, update this ExecPlan with the discovery and fix the suite accordingly.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Read and edit the backend helpers:

    sed -n '300,980p' src/foliaseal/application/phase3_signing_backend.py

Inspect and update the backend tests:

    rg -n "compact|_single_line_stamp_content_inset|_single_line_text_wrap_limits|visible_signature_fit_issues" tests/unit/test_phase3_signing_backend.py

Run targeted verification after the backend refactor:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py

Run the broader automated suite to detect stale assumption tests:

    .venv/bin/python -m pytest -q

Expected targeted verification transcript after the implementation:

    120+ passed

Expected broader verification transcript after the implementation:

    all project tests passed

or, if a stale-assumption test exists:

    one or more failures that clearly point to tests asserting deleted threshold details

## Validation and Acceptance

The change is acceptable only if all of the following are true:

- `src/foliaseal/application/phase3_signing_backend.py` no longer contains the targeted hardcoded threshold branches for `single_line` layout sizing and wrapping.
- The backend still accepts realistic `single_line` rectangles that fit and still rejects overfull rectangles honestly.
- The preview-facing suite still passes, proving that the preview can consume the simplified backend helpers without reintroducing divergence.
- The broader automated suite is run. If it fails because of tests coupled to deleted implementation details, those tests are corrected and the plan is updated to record the discovery.

## Idempotence and Recovery

These edits are safe to repeat because they only change deterministic helper logic and tests. If a simplification step causes a real fit regression, revert only the specific helper being changed, rerun the targeted backend suite, and record the failed approach in `Surprises & Discoveries` and `Decision Log` before trying a narrower geometry-driven helper. Do not recover by reintroducing the old threshold branches under new names.

## Artifacts and Notes

The most important artifacts are the simplified backend helper code and the verification transcripts. The broader `pytest -q` run is especially important in this slice because it checks whether the rest of the test suite accidentally encoded the old threshold implementation details.

Observed verification transcript:

    $ .venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py
    123 passed in 2.70s

    $ .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

    $ .venv/bin/python -m pytest -q
    312 passed in 2.87s

## Interfaces and Dependencies

No new runtime dependencies are allowed. Reuse the existing backend measurement helpers such as `_measure_text_box_dimensions()`, `_layout_reservation_for_template()`, and `_wrap_visible_signature_fragments()`. Any new helper added in `src/foliaseal/application/phase3_signing_backend.py` must remain private unless there is an immediate second use in the current repository.

Revision note: created on 2026-04-05 after the preview threshold simplification completed and the next concentration of arbitrary `single_line` cutoffs was confirmed to be in the backend reservation and wrap helpers.

Revision note: updated on 2026-04-05 after implementation. The targeted backend threshold branches were removed, the focused backend tests were rewritten to assert stable behavior instead of threshold helper internals, and both the targeted suite and the full automated suite passed.
