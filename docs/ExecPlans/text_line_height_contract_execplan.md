# Text Line-Height Contract ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the preview analysis code and the backend fit-validation code will use one explicit line-height contract for stacked visible-signature text. A user will not see a new control, but the product gets closer to the V1 requirement that the on-page preview is a trustworthy promise of the final visible signature. The observable proof is a focused regression test that compares preview structural line bounds against the same pyHanko-backed text measurement used by signing fit validation, plus the existing backend and preview suites staying green.

This slice is intentionally narrow. It does not attempt to eliminate every historical stress-matrix clipping cluster in one pass. It first turns the current implicit text-height behavior into a shared application-layer helper so future matrix work changes one contract rather than independently tuning backend and preview calculations.

## Child ExecPlan Dependencies

- [x] The direct annotation appearance rendering and signing-preview snapshot work has already introduced `SignatureAppearanceSnapshot.line_bounds_px`.
- [x] `VisibleSignatureLayoutEngine` already exposes `PyHankoTextMeasurer`, which delegates to the backend `_measure_text_box_dimensions()` function.
- [x] The current backend `_measure_text_box_dimensions()` already reserves at least nominal font size per line plus one point for multi-line descender room.
- [x] The dev-loop explorer identified this plan as the next high-leverage V1 slice because it targets preview/output WYSIWYG trust.

## Progress

- [x] (2026-05-13T11:37Z) Selected this existing plan as the next high-leverage dev-loop slice after reviewing `docs/SPEC.md`, README release-gap notes, recent ExecPlans, and the explorer recommendation.
- [x] (2026-05-13T11:41Z) Rewrote this ExecPlan into PLANS.md-compliant, self-contained form and narrowed the first implementation pass to an explicit shared stacked line-box contract.
- [x] (2026-05-13T11:45Z) Added a focused regression test proving structural line bounds preserve the full stacked text height contract and use full-text measurement first.
- [x] (2026-05-13T11:45Z) Implemented `structural_line_bounds()` in `visible_signature_layout.py`, updated canonical preview line bounds to call it, and updated Phase 3 harness fallback snapshot reconstruction for the new helper signature.
- [x] (2026-05-13T11:51Z) Ran focused Ruff and backend/preview tests successfully.
- [x] (2026-05-13T11:53Z) Ran broader shell/harness tests successfully.
- [x] (2026-05-13T11:53Z) Ran full Ruff successfully.
- [x] (2026-05-13T11:58Z) Ran the full unit suite successfully.
- [x] (2026-05-13T12:33Z) Committed the completed slice as `Share structural line bounds contract`.
- [x] (2026-05-13T12:39Z) Addressed compliance review findings by making `structural_line_bounds()` expand to the full measured stacked text height and adding a production-path canonical preview regression test.
- [x] (2026-05-13T12:45Z) Reran targeted Ruff, focused backend/preview tests, broader shell/harness tests, and full Ruff after the compliance fix.
- [x] (2026-05-13T12:51Z) Ran the full unit suite after the compliance fix.
- [x] (2026-05-13T12:51Z) Amended the slice commit with the compliance fixes.

## Surprises & Discoveries

- Observation: The current backend already contains a small multi-line height correction.
  Evidence: `src/foliaseal/application/phase3_signing_backend.py` `_measure_text_box_dimensions()` returns `max(measured_height, ceil(line_count * font_size) + 1)` when there is more than one line.

- Observation: The preview renderer already asks `PyHankoTextMeasurer` for each line fragment, but it does not expose a named contract for distributing the full measured text-box height across structural line bounds.
  Evidence: `src/foliaseal/application/signing_preview_renderer.py` `_structural_line_bounds_px()` measures each fragment and scales them into `text_bounds_px`; the rule is local to the preview renderer.

- Observation: Phase 3 harness fallback snapshot reconstruction also calls `_structural_line_bounds_px()`.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` reconstructs preview and signed-output line bounds when captured raster line bounds are unavailable, so it needed to pass joined full text to the updated helper wrapper.

- Observation: The first implementation measured the full text but still distributed only the allocated `text_bounds.height`.
  Evidence: compliance review found that `structural_line_bounds()` called `measurer.measure(text, text_style)` but used `divmod(text_bounds.height, len(visible_fragments))`. The helper now expands structural height to `max(text_bounds.height, round(full_metrics.height_pt))`.

- Observation: The first regression test covered the helper directly but not the canonical preview production path.
  Evidence: compliance review found the test called `structural_line_bounds()` with a fake measurer. A new test now calls `render_canonical_signature_preview()` and compares emitted line bounds with `PyHankoTextMeasurer` full-text height.

## Decision Log

- Decision: Make the first pass an explicit shared line-box contract rather than another backend fit threshold change.
  Rationale: Prior experiments recorded in the old plan showed that backend-only line leading can regress accepted compact `single_line` cases. A shared helper makes the contract visible and testable before larger stress-matrix remediation.
  Date/Author: 2026-05-13 / Codex

- Decision: Keep this slice as behavior-change plus plan documentation only; do not refresh large generated stress artifacts in the same commit.
  Rationale: The code change is small and should be reviewed separately from expensive matrix evidence refresh. Matrix reruns belong in a follow-up evidence slice if focused validation shows the contract is stable.
  Date/Author: 2026-05-13 / Codex

## Outcomes & Retrospective

This slice is complete. The shared helper and focused regression tests are implemented, and a compliance review fix tightened the helper and production-path coverage. Targeted Ruff, focused backend/preview tests, broader shell/harness tests, full Ruff, and the full unit suite all pass after the fix. The remaining stress-matrix evidence refresh is intentionally deferred to a follow-up slice.

## Context and Orientation

FoliaSeal renders visible PDF signatures. A visible signature has a text part, such as the signer name and signing time, and may also have a stamp image. In compact vertical layouts, several lines of text are stacked in a small rectangle. The product spec requires WYSIWYG trust: the preview should look like the final signed output.

The backend signing and fit-validation path is in `src/foliaseal/application/phase3_signing_backend.py`. The key function for this slice is `_measure_text_box_dimensions(stamp_text, text_box_style)`, which uses pyHanko's `TextBox` engine and currently applies the minimum stacked line height correction.

The application-layer layout boundary is `src/foliaseal/application/visible_signature_layout.py`. It already has `TextMetrics` and `PyHankoTextMeasurer`. `PyHankoTextMeasurer.measure(text, text_style)` delegates to `_measure_text_box_dimensions()`, so callers can use backend-faithful text dimensions without importing backend-private style objects directly.

The canonical preview renderer is `src/foliaseal/application/signing_preview_renderer.py`. `render_canonical_signature_preview()` writes a tiny PDF stamp, rasterizes it, and returns `CanonicalSignaturePreviewSnapshot`. It also creates a `SignatureAppearanceSnapshot` with `line_bounds_px`, which are structural rectangles used by preview/output comparison. Today `_structural_line_bounds_px()` owns the line-bound distribution locally.

The first goal is not to add a new rendering engine. The first goal is to move the line-bound distribution into a shared helper that takes the complete text, its fragments, the text style, and the allocated text bounds, then returns per-line bounds whose union preserves the same full-text measured height that backend fit validation uses.

## Plan of Work

First, add tests. In `tests/unit/test_signing_preview_renderer.py`, extend the existing canonical preview line-bounds coverage with a case whose stamp text has at least three lines. The test should call `render_canonical_signature_preview()`, get `snapshot.appearance_snapshot.line_bounds_px`, and assert that the union height of those line bounds is at least the height produced by `PyHankoTextMeasurer().measure(full_stamp_text, text_style)` scaled to the preview image. This test protects against reconstructing line bounds solely from per-fragment approximations when the full text-box contract changes.

Second, add a small helper to `src/foliaseal/application/visible_signature_layout.py`, for example:

    def structural_line_bounds(
        *,
        text: str,
        text_fragments: tuple[str, ...],
        text_style: SignatureTextStyle,
        text_bounds: RectBounds,
        text_measurer: TextMeasurer | None = None,
    ) -> tuple[RectBounds, ...]:
        ...

The helper should measure the complete text with `PyHankoTextMeasurer` by default, measure each fragment for relative widths, distribute the full measured height across visible fragments, and return `RectBounds` values. It should be deterministic, avoid Qt imports, and return an empty tuple if there are no visible fragments or the bounds are unusable.

Third, replace the body of `_structural_line_bounds_px()` in `src/foliaseal/application/signing_preview_renderer.py` with a call to the new helper. Convert dictionaries to and from `RectBounds` at the boundary so existing public snapshot shapes remain unchanged.

Fourth, run focused validation. At minimum run:

    .venv/bin/python -m ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    .venv/bin/python -m pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py

If those pass, run the broader shell/harness coverage because preview snapshots feed harness evidence:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py

Do not run or update large stress-matrix artifacts in this first slice unless the focused tests reveal a direct need. Record that as a follow-up if needed.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Check the current references:

    rg -n "_measure_text_box_dimensions|PyHankoTextMeasurer|_structural_line_bounds_px|line_bounds_px" src/foliaseal/application tests/unit

Edit only:

    docs/ExecPlans/text_line_height_contract_execplan.md
    src/foliaseal/application/visible_signature_layout.py
    src/foliaseal/application/signing_preview_renderer.py
    src/foliaseal/presentation/qt/phase3_harness.py
    tests/unit/test_signing_preview_renderer.py

Run the validation commands listed in `Plan of Work`. Expected focused result is that Ruff exits with `All checks passed!` and pytest reports all selected tests passing.

## Validation and Acceptance

This slice is accepted when preview structural line bounds are produced by the shared helper in `visible_signature_layout.py`, the new preview test proves the bounds preserve backend-faithful full-text stacked height, existing backend text-height tests still pass, and the focused preview/backend suites pass.

The helper must not change public snapshot JSON shape: line bounds remain tuples of dictionaries with `x`, `y`, `width`, and `height` integer keys after leaving `signing_preview_renderer.py`.

Large stress-matrix risk remains after this slice. Acceptance for this first pass is not "all historical stress clusters are green"; acceptance is that the line-height contract is now centralized and protected so the next evidence refresh has one calculation to inspect.

## Idempotence and Recovery

The change is safe to repeat. If tests fail, revert only the helper call in `_structural_line_bounds_px()` and keep the plan update; then record the failed transcript in `Surprises & Discoveries`. Do not change backend fit policy, stamp image sizing, border logic, or generated matrix artifacts in this slice.

If the new helper needs a different name after implementation, update the `Interfaces and Dependencies` section before committing so a future contributor can restart from this document.

## Artifacts and Notes

No generated artifacts were expected or produced. The important evidence is focused test output, full validation output, and the `Share structural line bounds contract` commit.

Initial focused validation started before edits:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    150 passed in 167.97s (0:02:47)

Post-edit focused lint:

    .venv/bin/python -m ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

Post-edit focused tests:

    .venv/bin/python -m pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    151 passed in 178.53s (0:02:58)

Whitespace validation:

    git diff --check
    <no output>

Broader shell/harness tests:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
    147 passed, 13 skipped, 1 warning in 31.61s

Full lint:

    .venv/bin/python -m ruff check .
    All checks passed!

Full unit suite:

    .venv/bin/python -m pytest -q
    654 passed, 23 skipped, 1 warning in 213.65s (0:03:33)

Post-compliance-fix targeted lint:

    .venv/bin/python -m ruff check src/foliaseal/application/visible_signature_layout.py src/foliaseal/application/signing_preview_renderer.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    All checks passed!

Post-compliance-fix focused tests:

    .venv/bin/python -m pytest -q tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py
    152 passed in 169.30s (0:02:49)

Post-compliance-fix broader shell/harness tests:

    .venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py
    147 passed, 13 skipped, 1 warning in 31.17s

Post-compliance-fix full lint:

    .venv/bin/python -m ruff check .
    All checks passed!

Post-compliance-fix full unit suite:

    .venv/bin/python -m pytest -q
    655 passed, 23 skipped, 1 warning in 210.72s (0:03:30)

## Interfaces and Dependencies

`src/foliaseal/application/visible_signature_layout.py` should expose one helper for structural line bounds. It should use existing local dataclasses where possible:

    RectBounds
    TextMetrics
    TextMeasurer
    PyHankoTextMeasurer

The helper should return `tuple[RectBounds, ...]` so callers get typed values inside the application layer. `src/foliaseal/application/signing_preview_renderer.py` should convert those values to dictionaries with `RectBounds.as_dict()` because snapshot payloads and tests already expect dictionaries.

Revision note: Rewritten 2026-05-13 by Codex to make the previously sketched text-line-height plan self-contained and narrow the first dev-loop slice to a shared structural line-box helper.

Revision note: Updated 2026-05-13 by Codex after implementing the shared structural line-bound helper and discovering the Phase 3 harness fallback reconstruction call sites.

Revision note: Updated 2026-05-13 by Codex after committing the completed slice and correcting this plan's completion state during compliance review.
