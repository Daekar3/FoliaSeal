# Cap 9 Single-Line Validation Honesty

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

The manual Qt harness review found one user-visible defect: cap 9 showed single-line signature text with characters severely cut off by the border, but the UI did not show red validation. After this change, the same class of visible clipping must be treated as a signing blocker before the user signs. A user should see a red validation message instead of a signable preview whenever rendered text ink touches or crosses the visible border in a compact single-line image-stamp layout.

## Progress

- [x] (2026-05-02T04:18Z) Created this child ExecPlan from the manual cap 9 observation in `docs/ExecPlans/manual_harness_sanity_pass_execplan.md`.
- [x] (2026-05-02T04:18Z) Confirmed no tracked cap 9 harness JSON is available; only the older `captured_states[9]` evidence note and the user's manual observation are present.
- [x] (2026-05-02T04:20Z) Added `test_single_line_rendered_ink_fallback_rejects_border_flush_text` for rendered single-line text ink touching the border without triggering the existing reference-width-loss rejection.
- [x] (2026-05-02T04:20Z) Confirmed the new regression failed before the production change: `_single_line_rendered_ink_fits_reservation` returned `True` for border-flush text.
- [x] (2026-05-02T04:20Z) Tightened validation so horizontal single-line image-stamp rendered text must remain inside the border-safe inset.
- [x] (2026-05-02T04:20Z) Ran focused signing backend tests, the full signing backend unit file, Ruff for touched Python files, and `git diff --check`.
- [x] (2026-05-02T04:20Z) Updated this plan and the parent manual harness plan with the outcome.

## Surprises & Discoveries

- Observation: the repository has a manual replay fixture for caps 4 through 8 but not cap 9.
  Evidence: `tests/fixtures/phase3_horizontal_single_line_manual_replay.json` contains `manual_04_single_line_left` through `manual_08_single_line_left` plus later latest cap 4, 7, and 8 cases.

- Observation: the cap 9 class of defect has appeared before in harness evidence validation.
  Evidence: `artifacts/phase3_fr3b_acceptance_results.md` records `captured_states[9] is signable even though render diagnostics report a user-visible fit failure`.

- Observation: the current backend fallback checks rendered text bounds against the text lane dimensions and checks reference ink preservation, but it does not explicitly reject rendered ink that is flush against the outer preview border.
  Evidence: `_single_line_rendered_ink_fits_reservation` in `src/foliaseal/application/phase3_signing_backend.py` compares `text_bounds["width"]` and `text_bounds["height"]` to `snapshot.text_area_bounds_px`, while the manual defect is visual border clipping.

- Observation: the focused regression reproduced the missing guard before the fix.
  Evidence: `.venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text` failed with `AssertionError: assert not True`.

## Decision Log

- Decision: create a child ExecPlan instead of expanding the manual harness plan.
  Rationale: the parent plan is the manual review record. This plan is an executable fix slice with tests and code changes.
  Date/Author: 2026-05-02 / Codex

- Decision: fix validation honesty in the backend/application validation path before adding any Issue #49 style layout extraction.
  Rationale: the user needs the UI to block a visibly clipped preview now. Architectural extraction can happen after the behavior is stable and covered by focused tests.
  Date/Author: 2026-05-02 / Codex

- Decision: use an equivalent deterministic rendered-ink unit test rather than relying on an unavailable cap 9 artifact.
  Rationale: no saved cap 9 capture is tracked. A unit test can reproduce the important behavior exactly: rendered text ink is signable by size and reference preservation but is border-flush and must be rejected.
  Date/Author: 2026-05-02 / Codex

## Outcomes & Retrospective

This plan is in progress. It is complete when compact single-line rendered text that is visibly clipped or border-flush is non-signable, the regression is covered by a focused test, and the existing manual caps 4 through 8 behavior still passes.

The plan is complete for the intended slice. `_single_line_rendered_ink_fits_reservation` now rejects horizontal single-line image-stamp text ink that is not inside the border-safe inset. The new regression covers cap 9-like border clipping, while the existing manual caps 4 through 8 replay still passes with its expected validation ladder.

## Context and Orientation

Visible signature validation is assembled in `src/foliaseal/application/phase3_signing_backend.py` and exposed to the Qt shell through `SigningDraftWorkflow`. A compact single-line image-stamp layout is the layout where `SignatureLayoutTemplate.SINGLE_LINE` is paired with an image stamp on the left or right side. These cases use rendered-ink measurements because the nominal text box can be wider than the visible glyph ink.

The key function for this slice is `_single_line_rendered_ink_fits_reservation` in `src/foliaseal/application/phase3_signing_backend.py`. It renders a canonical preview, measures the visible text pixels, and decides whether a layout fit issue can be forgiven because the actual rendered ink still fits. If this function returns true for border-clipped text, `_build_stamp_style` can allow a preview that should be blocked.

The regression tests belong in `tests/unit/test_phase3_signing_backend.py`, near the existing rendered-ink fallback tests. The existing fixture `tests/fixtures/phase3_horizontal_single_line_manual_replay.json` should continue to pass; it guards against breaking caps 4 through 8 while fixing cap 9.

## Plan of Work

First, add a unit test that monkeypatches the canonical preview renderer and text-bound detector so `_single_line_rendered_ink_fits_reservation` sees a compact single-line left-stamp preview whose rendered text dimensions fit, whose roomy reference loses no meaningful width, but whose text ink begins at the outer image edge. Before the fix, this shape is accepted. After the fix, it must be rejected.

Second, update `_single_line_rendered_ink_fits_reservation` to require a border-safe inset for horizontal single-line image-stamp text ink. The function should keep the existing reference-preservation check and dimension check, but it must also reject rendered text bounds that are not fully inside the preview image by at least the same border-aware safety inset used elsewhere for visible signature layout.

Third, run focused tests covering the new regression, the existing rendered-ink fallback cache behavior, and the manual caps 4 through 8 replay. If the focused tests pass, run lint for touched files and `git diff --check`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Add the regression test:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text

The first run should fail before the production change because border-flush rendered text is still accepted.

Implement the production change in:

    src/foliaseal/application/phase3_signing_backend.py

Then run:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_caches_identical_checks tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_reference_text_loss tests/unit/test_phase3_signing_backend.py::test_manual_caps_4_to_8_replay_backend_validation_ladder
    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py
    git diff --check

## Validation and Acceptance

Acceptance requires the new regression test to pass, the existing rendered-ink fallback tests to pass, and the manual caps 4 through 8 replay to keep its expected pass/fail ladder. The user-visible acceptance is that a cap 9-like preview whose text is cut off by the border now yields a validation error instead of remaining signable.

## Idempotence and Recovery

The code and test edits are safe to re-run. The tests write temporary images under pytest-managed temporary directories. If a focused test fails after the fix, inspect only the changed rendered-ink guard and do not regenerate broad preview matrix artifacts in this slice.

## Artifacts and Notes

The motivating manual evidence is the parent plan entry:

    user manual review on 2026-05-02 reported that cap 9 should have red validation because characters were severely cut off by the border.

The older related harness evidence is:

    artifacts/phase3_fr3b_acceptance_results.md: captured_states[9] is signable even though render diagnostics report a user-visible fit failure.

Focused verification completed on 2026-05-02:

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_border_flush_text tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_caches_identical_checks tests/unit/test_phase3_signing_backend.py::test_single_line_rendered_ink_fallback_rejects_reference_text_loss tests/unit/test_phase3_signing_backend.py::test_manual_caps_4_to_8_replay_backend_validation_ladder
    4 passed in 3.89s

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py
    100 passed in 10.93s

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

    git diff --check
    no output

## Interfaces and Dependencies

This slice should use the existing functions and types in `src/foliaseal/application/phase3_signing_backend.py`; do not introduce a new rendering dependency. The only expected production interface change is stricter return behavior from `_single_line_rendered_ink_fits_reservation` for border-flush rendered ink.

Revision note: Created 2026-05-02 by Codex to convert the manual cap 9 observation into a narrow executable validation-honesty fix.

Revision note: Updated 2026-05-02 by Codex after implementing and validating the border-safe rendered-ink guard.
