# Fix Shared Stamp Sizing for `single_line` Preview and Signing

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

After this change, `single_line` signatures should size image stamps from one shared geometry model that behaves sensibly in both the live preview and the real PDF signing path. A user drawing the same small rectangle they have been using for manual checks should no longer see a stamp that is much smaller than the reserved band suggests, and `left` / `right` cases should no longer silently collapse the stamp band to zero width while still showing text.

The observable result is a more honest and more efficient image fit. In `single_line/top` and `single_line/bottom`, the stamp should use most of the stamp band instead of being shrunk by an oversized internal gutter. In `single_line/left` and `single_line/right`, the stamp should either receive real reserved width or the backend should fail honestly because the rectangle cannot satisfy both text and image demands.

## Progress

- [x] (2026-04-05 16:29Z) Traced the relevant backend and preview code paths that determine stamp area reservation, stamp inset, and preview pixmap sizing.
- [x] (2026-04-05 16:31Z) Confirmed the two current root causes with real-code inspection and targeted probes: vertical stamp gutters are disproportionately large relative to the reserved band, and horizontal reservation can still starve the stamp band to `0pt` width.
- [x] (2026-04-05 16:34Z) Wrote aspect-aware stamp-demand helpers into the backend reservation path and threaded them through preview sizing.
- [x] (2026-04-05 16:37Z) Removed the stale preview `140x80` pixmap cap and switched preview stamp gutter sizing to the shared backend helper.
- [x] (2026-04-05 16:40Z) Added focused regression coverage for reserved-band-aware inset behavior, non-zero horizontal stamp reservation, and uncapped preview stamp sizing.
- [x] (2026-04-05 16:44Z) Ran focused validation (`129 passed`) and the full suite (`318 passed`), then recorded the resulting evidence here.

## Surprises & Discoveries

- Observation: The vertical `single_line` stamp band is not primarily being limited by the preview card width. It is being limited by the reserved stamp height, and the current content inset consumes a large fraction of that already-small height.
  Evidence: For a real `single_line/top` rectangle around `260.61pt x 23.04pt`, `_layout_reservation_for_template()` reserves a stamp area of `257pt x 8pt`. `_single_line_stamp_content_inset()` currently returns `2pt` for this geometry, cutting the effective fit height from `8pt` to `4pt`.

- Observation: The preview path magnifies the same problem because `_preview_stamp_content_gutter_pt()` is converted into pixels after preview scaling, so a seemingly small point gutter becomes a large pixel gutter inside a short vertical band.
  Evidence: In the user-reported `single_line/top` capture, the stamp band height is `16px`, while the preview gutter computes to roughly `5px` per side after scaling, leaving only about `6px` of usable stamp height.

- Observation: `single_line/left` and `single_line/right` can still allocate `0pt` of stamp width when text width consumes the full horizontal budget.
  Evidence: A targeted probe using the user’s real `~260pt x 23pt` rectangle produced `stamp_area_width_pt = 0` and `stamp_area_height_pt = 15` for both `left` and `right` with a visible image stamp.

- Observation: The vertical reservation itself did not need a wholesale rebalance to make the stamp more useful; shrinking the inset relative to the reserved band was enough to recover a large fraction of the lost usable height.
  Evidence: With the same real `single_line/top` rectangle, the reserved stamp band remains `8pt` tall, but the effective internal inset drops from `2pt` per side to `1pt` per side, increasing the usable fit height from `4pt` to `6pt`.

- Observation: Horizontal stamp visibility improves once the reservation can preserve image-driven minimum width, even before any preview-only rendering adjustments.
  Evidence: After the backend reservation update, the same real `single_line/right` probe moved from `stamp_area_width_pt = 0` to `stamp_area_width_pt = 56` while keeping `text_area_height_pt = 15`.

- Observation: A real Qt probe against the user’s GIF showed that the stamp can legitimately scale to the full band height, so the remaining “too small” feeling was still coming from a conservative vertical inset, not from Qt failing to scale the image.
  Evidence: `QPixmap.scaled(..., Qt.KeepAspectRatio, ...)` on the real GIF produced `113x27` for a `691x27` band, which confirmed the band itself was large enough to support a visibly larger stamp.

## Decision Log

- Decision: Fix stamp sizing through one shared reservation and fit model instead of adding another preview-only exception.
  Rationale: The repository already moved toward one authoritative backend-owned layout model. Adding another preview-only stamp-sizing rule would recreate the preview/output drift that earlier simplification work removed.
  Date/Author: 2026-04-05 / Codex

- Decision: Treat horizontal `0pt` stamp reservation as a structural bug, not as an acceptable “tiny stamp” outcome.
  Rationale: A visible image stamp that receives zero reserved width cannot ever be rendered correctly. The system must either reserve real width or fail honestly.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The implemented slice fixed the shared causes of undersized or invisible `single_line` image stamps without reintroducing preview-only behavior. The backend now reserves stamp space with awareness of the reserved band and, for horizontal layouts, awareness of the stamp image aspect ratio. The preview now uses those same reservation and inset results directly and no longer applies the stale `140x80` cap.

The result is narrower and cleaner than a larger layout rewrite. Vertical `top` / `bottom` stamps now keep more of their already-limited band height for actual image content. Horizontal `left` / `right` stamps no longer disappear because the reservation model gave them `0pt` width.

The remaining gap is manual confirmation with the user’s real harness profile. The automated evidence shows the shared model is behaving more honestly and the repository remains stable, but the final acceptance question is whether the real stamp now looks appropriately sized in the live GUI.

## Context and Orientation

The live signing shell is built in `src/foliaseal/presentation/qt/signing_shell.py`. The backend logic that predicts whether a visible signature will fit and that generates the actual PDF stamp style lives in `src/foliaseal/application/phase3_signing_backend.py`.

The key term in this plan is “reservation.” A reservation is the split of a signature rectangle into text space and stamp-image space. In this repository, `_layout_reservation_for_template()` in `src/foliaseal/application/phase3_signing_backend.py` is the function that computes that split. The preview reads from that same function to size the preview label and the preview stamp.

The current stamp-sizing bug comes from two places inside that shared model:

1. `_single_line_stamp_content_inset()` in `src/foliaseal/application/phase3_signing_backend.py` returns a fixed inset that is too large relative to the tiny stamp bands used by short `single_line/top` and `single_line/bottom` rectangles.
2. `_effective_horizontal_text_reservation_width()` and the horizontal branch of `_layout_reservation_for_template()` can leave no width for the stamp at all in `single_line/left` and `single_line/right`.

The preview mirrors these decisions in `src/foliaseal/presentation/qt/signing_shell.py` through `_preview_stamp_content_gutter_pt()`, `_preview_stamp_max_size()`, and `_preview_vertical_band_geometry()`. There is also an old preview-only hard cap in `_preview_stamp_max_size()` (`140x80`) that can keep a stamp smaller than the reserved band even after the band has been fixed.

The tests that currently protect this behavior are concentrated in:

- `tests/unit/test_phase3_signing_backend.py`
- `tests/unit/test_qt_signing_shell.py`

## Plan of Work

The first edit is in `src/foliaseal/application/phase3_signing_backend.py`. Introduce a helper that computes stamp fit demand from actual geometry rather than from a generic shortest-edge threshold. The helper should accept the stamp position, the reserved band size, and optionally the source image aspect ratio when one is available. It should return an internal inset that never consumes a disproportionate share of the reserved band and, for horizontal layouts, a minimum stamp width requirement derived from the available height and image aspect ratio.

Then update `_layout_reservation_for_template()` so the horizontal `single_line` path never silently collapses the stamp band to zero when an image stamp is present. The reservation should preserve a minimum stamp width if the image exists. If the rectangle truly cannot support both the text and that minimum stamp demand, the backend fit check should fail honestly instead of pretending the stamp band can be zero.

Next, update `_background_layout_for_stamp()` so it uses the new shared inset helper rather than the current coarse `_single_line_stamp_content_inset()` value. The goal is to let vertical stamps use more of their reserved band while still preserving a small safety gutter.

In `src/foliaseal/presentation/qt/signing_shell.py`, replace `_preview_stamp_content_gutter_pt()` with a thin adapter over the backend-owned helper so the preview inset matches the real output inset. Update `_preview_stamp_max_size()` to stop imposing the stale `140x80` hard cap. The preview should size the pixmap from the reserved band and available preview scale, not from an unrelated ceiling that predates the current reservation model.

After the code changes, extend `tests/unit/test_phase3_signing_backend.py` with explicit coverage for:

- vertical `single_line` reservations where the effective stamp fit height remains meaningfully larger than half the reserved band height,
- horizontal `single_line` reservations with a visible image stamp where the stamp band width is non-zero for the real-world rectangle family that currently starves the stamp.

Extend `tests/unit/test_qt_signing_shell.py` with explicit preview-side checks that:

- vertical stamp pixmap sizing uses most of the reserved band for `top` / `bottom`,
- horizontal preview stamps receive a real pixmap size when the reservation is signable,
- `_preview_stamp_max_size()` is not artificially clamped to `140x80`.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Inspect the current code paths before editing:

    sed -n '380,760p' src/foliaseal/application/phase3_signing_backend.py
    sed -n '480,760p' src/foliaseal/presentation/qt/signing_shell.py

Implement the backend reservation and inset updates in:

    src/foliaseal/application/phase3_signing_backend.py

Implement the preview sizing updates in:

    src/foliaseal/presentation/qt/signing_shell.py

Update the tests in:

    tests/unit/test_phase3_signing_backend.py
    tests/unit/test_qt_signing_shell.py

Run focused validation first:

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py
    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py

Then run the full suite:

    .venv/bin/pytest -q

Expected success shape:

    ruff reports no issues
    pytest reports all tests passing

Observed completion transcript:

    .venv/bin/ruff check src/foliaseal/application/phase3_signing_backend.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py .agent/single_line_stamp_sizing_execplan.md
    All checks passed!

    .venv/bin/pytest -q tests/unit/test_phase3_signing_backend.py tests/unit/test_qt_signing_shell.py tests/unit/test_phase3_harness.py tests/unit/test_signing_preview_renderer.py
    129 passed in 2.60s

    .venv/bin/pytest -q
    318 passed in 2.62s

## Validation and Acceptance

Acceptance is both behavioral and structural.

Behaviorally, the backend must no longer reserve a uselessly small vertical fit region for `single_line/top` and `single_line/bottom`, and the horizontal reservation must not produce a `0pt` stamp band for signable image-stamp cases. The preview must size the stamp from those same shared reservations without wrapping or preview-only growth hacks.

Structurally, there must be only one place that decides how much of a reserved stamp band is lost to internal gutter. The preview may convert that result into pixels, but it must not invent a second policy.

The focused tests must prove:

- vertical `single_line` image fit preserves more usable band height than the current implementation,
- horizontal `single_line` image fit reserves real width for the stamp,
- preview stamp max-size logic no longer applies the old hard cap.

The full suite must remain green so this fix does not destabilize unrelated signing behavior.

## Idempotence and Recovery

The edits in this plan are safe to rerun. The validation commands are idempotent. If a test fails mid-implementation, keep the plan updated, inspect the failure, and adjust the shared reservation model instead of adding preview-only exceptions. No destructive migration or data rewrite is involved.

## Artifacts and Notes

Key evidence gathered before implementation:

    For `single_line/top` with a `~260pt x 23pt` real rectangle and a visible image stamp:
      text area: 257pt x 10pt
      stamp area: 257pt x 8pt
      current backend inset: 2pt per side
      effective backend fit height after inset: 4pt

    For `single_line/left` and `single_line/right` with the same rectangle:
      text area: 253pt x 15pt
      stamp area: 0pt x 15pt

These values explain both user-visible symptoms: vertical stamps look much smaller than the band suggests, and horizontal stamps disappear entirely.

Key evidence gathered after implementation:

    For `single_line/top` with the same rectangle and a wide signature aspect ratio:
      text area: 257pt x 10pt
      stamp area: 257pt x 8pt
      effective inset: 1pt per side
      usable stamp fit height: 6pt

    For `single_line/right` with the same rectangle and a wide signature aspect ratio:
      text area: 197pt x 15pt
      stamp area: 56pt x 15pt

These values show that the backend no longer starves horizontal image stamps to zero width and that the vertical band now keeps materially more usable height for the image.

## Interfaces and Dependencies

Do not add new runtime dependencies.

The implementation should continue to center on these existing interfaces:

- `foliaseal.application.phase3_signing_backend._layout_reservation_for_template`
- `foliaseal.application.phase3_signing_backend._background_layout_for_stamp`
- `foliaseal.presentation.qt.signing_shell._preview_stamp_max_size`
- `foliaseal.presentation.qt.signing_shell._preview_vertical_band_geometry`

If a new helper is introduced, keep it backend-owned and narrowly named, for example:

    def _single_line_stamp_fit_metrics(
        *,
        stamp_position: SignatureStampPosition,
        reserved_width_pt: int,
        reserved_height_pt: int,
        box_width_pt: int,
        box_height_pt: int,
        stamp_aspect_ratio: float | None = None,
    ) -> _SingleLineStampFitMetrics:

The preview may call a thin adapter over that helper, but it must not create a second semantic model.

Revision note (2026-04-05): Created this ExecPlan after tracing the current stamp-sizing bug to oversized internal gutters in short vertical bands and zero-width horizontal stamp reservation.
Revision note (2026-04-05): Updated this ExecPlan after implementation to record the final helper design, test results, and before/after reservation evidence.
Revision note (2026-04-05): Updated this ExecPlan after a manual-harness follow-up to record the final vertical inset tuning informed by a real Qt GIF scaling probe.
