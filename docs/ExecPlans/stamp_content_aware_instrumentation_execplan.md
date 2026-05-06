# Stamp Content-Aware Preview Instrumentation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, a contributor will be able to determine whether a visible stamp image is merely small, genuinely clipped, or visually too close to the border without relying on a human description of what “looks wrong.” The harness and preview-matrix artifacts will show the reserved stamp band, the actual rendered pixmap bounds, and the non-transparent content bounds of the source image. The JSON artifacts will also include explicit machine checks for “pixmap touches band edge” and “meaningful stamp strokes are within a warning distance of the border.”

The user-visible proof is simple. Run the preview matrix, open one of the generated debug PNGs, and inspect the overlay. The artifact should show the border, the reserved stamp band, the rendered stamp pixmap box, and the alpha-aware content box inside the stamp image. Then open the summary JSON and confirm that the same scenario records concrete clipping and proximity flags rather than forcing a reviewer to infer them from raw geometry alone.

## Progress

- [x] (2026-04-05 02:05Z) Created this ExecPlan and refreshed `.agents/skills/write-execplan/PLANS.md`, `README.md`, and the existing harness docs to keep the scope aligned with the current preview-matrix workflow.
- [x] (2026-04-05 02:18Z) Extended preview capture so stamped scenarios now write a stamp-focused debug crop with overlay rectangles for the reserved stamp band, rendered pixmap, and projected content bounds.
- [x] (2026-04-05 02:24Z) Added alpha-aware source-image analysis and persisted the source/content bounds, rendered content bounds, and stamp-edge diagnostics into `render_capture`.
- [x] (2026-04-05 02:31Z) Added explicit clipping and proximity flags to the summary JSON and verified them against the compact `single_bottom` script-stamp scenario.
- [x] (2026-04-05 02:35Z) Added focused regression tests, reran the preview matrix, and refreshed the operator docs with the new artifact/diagnostic outputs.

## Surprises & Discoveries

- Observation: the current preview-matrix instrumentation can prove that a pixmap is small or that a stamp band is crowded, but it cannot prove whether meaningful painted strokes are being obscured.
  Evidence: `artifacts/preview_sweep_runs/single_line_matrix/summary.json` records widget bounds and border distances, but it does not record where the non-transparent content of `stamp_wide.png`, `stamp_tall.png`, or `stamp_script.png` actually sits within the rendered pixmap.

- Observation: transparent images make geometry-only judgments misleading.
  Evidence: a stamp can fit perfectly inside its label bounds while still looking “cut off” if the visible strokes sit low in the transparent canvas or if the border overlaps the painted portion instead of the transparent padding.

- Observation: the current preview capture already had enough geometry to project content-aware diagnostics without touching the signing shell.
  Evidence: `phase3_harness.py` already recorded the active stamp label bounds, pixmap size, and full preview PNG path, which was enough to compute band-relative pixmap bounds and draw a stamp-focused overlay entirely inside the harness layer.

## Decision Log

- Decision: implement content-aware instrumentation in the harness layer rather than the signing shell.
  Rationale: the shell should stay focused on rendering and interaction, while the harness and matrix already own artifact generation and JSON evidence capture.
  Date/Author: 2026-04-04 / Codex

- Decision: treat source-image alpha bounds as diagnostic metadata, not as a layout input.
  Rationale: the immediate goal is accurate detection and review, not a silent behavioral change in stamp fitting. The preview and backend should not start trimming or re-centering user images as part of this slice.
  Date/Author: 2026-04-04 / Codex

- Decision: keep the change slice primarily in the “behavior change” class for instrumentation logic, with evidence refresh and documentation updates only as direct support.
  Rationale: the main value is new observable behavior in the harness artifacts. Refactors unrelated to preview capture, signing output, or stamp diagnostics must not be mixed into this slice.
  Date/Author: 2026-04-04 / Codex

## Outcomes & Retrospective

The new instrumentation closes the most important blind spot in the preview sweep. The matrix can now distinguish between the full reserved stamp band, the rendered pixmap box, and the projected non-transparent content bounds of the source image. That means an agent no longer has to guess whether a tiny stamp is merely small, touching the edge, or carrying painted content dangerously close to the border.

This implementation stayed additive and contained to the harness layer. No visible-signature layout behavior changed, and the signing shell did not need another round of rendering logic changes. The remaining gap is final-output parity: these diagnostics currently describe the Qt preview only. If later work shows that preview and signed-PDF appearance diverge in a way that matters, the same content-aware overlay approach should be extended to rendered output crops as a separate slice.

## Context and Orientation

The interactive Phase 3 harness and the batch preview matrix both live in `src/foliaseal/presentation/qt/phase3_harness.py`. That file already knows how to capture a preview PNG of the Qt preview card, record widget bounds, and serialize a `render_capture` object into the preview snapshot inside `summary.json`. The current preview widget itself lives in `src/foliaseal/presentation/qt/signing_shell.py`, but this plan intentionally avoids moving instrumentation logic into that file unless a very small helper is required for access to an already-rendered widget.

In this repository, a “stamp band” means the region of the preview card reserved for the stamp image according to the current visible-signature layout model. A “pixmap” means the rendered Qt image that is actually placed into the preview label. An “alpha-aware content box” means the smallest rectangle inside the source image that contains non-transparent pixels. For a transparent PNG, this box approximates the actual signature strokes rather than the full transparent canvas. A “debug overlay crop” means a PNG artifact derived from the preview capture that draws colored rectangles around the stamp band, the rendered pixmap bounds, and the alpha-aware content box so a human or agent can see exactly what is happening.

The current harness already captures `preview_image_path`, widget bounds, and border-distance metrics. What is missing is content-aware evidence. The existing JSON can tell us the stamp label height is `19` or `38` pixels, but it cannot tell us whether the visible strokes inside that label are pressed into the lower border or have been cropped away. This plan closes that gap by adding three upgrades:

First, write a stamp-region debug crop with overlay rectangles. Second, analyze the source image’s non-transparent content bounds and include them in the capture. Third, compute explicit flags that detect likely clipping or dangerously small border distance for the meaningful stamp content.

## Plan of Work

Start in `src/foliaseal/presentation/qt/phase3_harness.py`. Extend the preview capture path so that, whenever a preview PNG is written, the harness can also derive a smaller stamp-focused debug artifact. The debug crop should be based on the already-rendered preview card, not a separate renderer. It should isolate the active stamp label region with a little surrounding padding so the border and immediate neighborhood remain visible. Draw overlay rectangles on top of that crop for the stamp band bounds, the rendered pixmap bounds, and the alpha-aware content bounds projected into preview coordinates. Keep the colors fixed and documented so a reviewer can learn them once and reuse the interpretation across sweeps.

Add a small image-analysis helper in the same module, or a nearby helper module if the code grows beyond a few functions. That helper should load the source stamp image using an already-available image library in the repo. Use `Pillow`, which is already available for local asset generation, to inspect RGBA alpha values. Compute the minimal non-transparent bounding box in source-image coordinates. When the stamp source has no alpha channel, treat the full image bounds as the content bounds. When the image is fully transparent or unreadable, return an explicit error state rather than guessing.

Once the source-image content box is known, map it into preview coordinates. The rendered pixmap is already scaled to fit inside the stamp band. Use the rendered pixmap width and height from the active Qt label plus the source-image width and height to scale the content box proportionally. Record both source-image and preview-space content bounds in the `render_capture` payload. Then compute explicit checks. At minimum, include:

- whether the rendered pixmap touches any edge of the reserved stamp band
- whether the projected non-transparent content touches any edge of the reserved stamp band
- the minimum distance in pixels from non-transparent content to each band edge
- whether that minimum distance is below a warning threshold, such as `2` pixels or `max(2, ceil(border_width / 2))`

These checks should produce stable booleans and numeric distances in the JSON rather than prose judgments.

After the core capture is working, extend the matrix summary format so the new fields are present in each scenario record. The summary should remain backwards-compatible where practical: existing fields such as `preview_image_path`, widget bounds, and border-distance metrics should stay intact. New fields should be additive and clearly named, for example `stamp_debug_image_path`, `stamp_source_content_bounds_px`, `stamp_rendered_content_bounds_px`, `stamp_pixmap_touches_band_edge`, `stamp_content_touches_band_edge`, and `stamp_content_min_edge_distance_px`.

Keep this slice narrow. Do not change visible-signature layout behavior, backend reservation logic, or image-stamp fitting rules as part of this plan unless a tiny plumbing change is required to expose existing data. The goal is diagnosis and confidence, not another round of silent layout changes.

## Milestones

### Milestone 1: Overlay Artifact Capture

At the end of this milestone, every matrix scenario that renders a stamp image should also write a stamp-focused overlay PNG. A novice should be able to run the matrix, open one overlay image, and see three distinct boxes: the reserved band, the rendered pixmap, and the content box placeholder even if the alpha-aware logic is not complete yet. The acceptance proof is visual and mechanical: the summary JSON names the overlay path, and the file exists beside the regular preview PNG.

Implement this in `src/foliaseal/presentation/qt/phase3_harness.py` by extending `_capture_preview_render()` and its helpers. Add a helper that extracts the stamp region from the preview PNG and draws the overlay rectangles. In the first pass, it is acceptable for the “content box” overlay to match the full pixmap bounds until Milestone 2 lands, as long as the naming and rendering pipeline are stable.

### Milestone 2: Alpha-Aware Stamp Content Bounds

At the end of this milestone, the harness should know where the meaningful non-transparent pixels live inside the source image and should project that box into preview coordinates. The acceptance proof is that the JSON for a transparent script-like stamp records a content box that is smaller than the full image bounds, while a solid opaque test stamp records content bounds equal to the full source image.

Implement the image analysis with `Pillow` and keep the behavior explicit for edge cases. If the image cannot be loaded or has no non-transparent pixels, record a structured error in the capture instead of falling back silently. Add unit tests that cover transparent, opaque, and fully transparent fixtures.

### Milestone 3: Explicit Clipping and Proximity Checks

At the end of this milestone, the matrix summary should mechanically flag scenarios where either the full pixmap or the meaningful content is touching the stamp-band edge or is within a warning distance of it. The acceptance proof is that the JSON contains stable booleans and distances, and at least one existing problematic compact scenario now shows a warning even if it still passes the broader `Ready to sign.` semantic validation.

Implement the checks in the harness summary layer, not inside the UI. Add tests that prove the thresholds behave as intended and that a “safe” scenario remains unflagged while a hand-constructed edge-touching scenario is flagged.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run the focused harness and preview tests while building the feature:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py tests/unit/test_signing_preview_renderer.py

Run the local preview sweep after each milestone:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/single_line_matrix.json \
      --artifacts-dir artifacts/preview_sweep_runs/single_line_matrix

Expected command behavior at the end of the plan:

    Phase 3 preview matrix
    - scenarios executed: 16
    - artifacts directory: artifacts/preview_sweep_runs/single_line_matrix
    - summary json: artifacts/preview_sweep_runs/single_line_matrix/summary.json

The new artifact directory should now contain, for scenarios with image stamps, both the existing preview PNG and an additional stamp-focused debug PNG. The summary JSON should name both files and include the new content-aware metrics.

## Validation and Acceptance

The work is accepted when all of the following are true:

- A matrix run writes a stamp overlay PNG for stamped scenarios without breaking the existing preview PNG capture.
- The overlay visibly distinguishes the reserved stamp band, the rendered pixmap bounds, and the projected non-transparent content bounds.
- `summary.json` includes additive, machine-readable stamp-content diagnostics for each stamped scenario.
- At least one previously ambiguous compact scenario can now be classified mechanically as “tiny but intact,” “touching the band edge,” or “content within warning distance of the border.”
- The focused unit tests pass, and the matrix still runs unattended with the repository-local assets.

Validation should include opening a few known scenarios from `artifacts/preview_sweep_runs/single_line_matrix/`, especially compact `single_bottom` and tight horizontal `single_left/right` cases, and confirming that the overlay and JSON agree with what a human sees.

## Idempotence and Recovery

This work is additive. Re-running the matrix with the same artifact directory should overwrite the overlay and summary files deterministically for the same scenario names. If a stamp image fails to load or analyze, the run should continue and record a scenario-local error in JSON rather than aborting the entire sweep. Recovery should consist of fixing the image-analysis bug or asset problem and rerunning the same command.

Do not mutate the source stamp files during analysis. The alpha-aware content box is diagnostic metadata only.

## Artifacts and Notes

The final artifact set for a stamped scenario should include:

- the existing preview PNG for the full preview card
- a stamp-focused overlay PNG
- JSON fields that describe the source-image content box, rendered pixmap box, projected content box, and clipping/proximity flags

An expected summary shape for one scenario should resemble this, with the exact key names kept stable once chosen:

    {
      "name": "single_bottom_wide_short_border_3_5_stamp_script",
      "preview_snapshot": {
        "render_capture": {
          "preview_image_path": "artifacts/.../single_bottom_wide_short_border_3_5_stamp_script.png",
          "stamp_debug_image_path": "artifacts/.../single_bottom_wide_short_border_3_5_stamp_script_stamp_debug.png",
          "stamp_pixmap_size_px": {"width": 59, "height": 19},
          "stamp_source_content_bounds_px": {"left": 4, "top": 3, "width": 112, "height": 34},
          "stamp_rendered_content_bounds_px": {"left": 12, "top": 4, "width": 47, "height": 14},
          "stamp_pixmap_touches_band_edge": false,
          "stamp_content_touches_band_edge": true,
          "stamp_content_min_edge_distance_px": 0
        }
      }
    }

This example is illustrative. The actual numbers will depend on the rendered scenario.

## Interfaces and Dependencies

Use `src/foliaseal/presentation/qt/phase3_harness.py` as the primary edit surface. If the image-analysis code becomes too large for that file, extract a narrow helper under `src/foliaseal/presentation/qt/` or another already-appropriate package, but keep the public surface small and explicit.

Use `Pillow` for alpha-aware image inspection. Do not add a new runtime dependency for this slice. The code must handle PNG, GIF, and other stamp formats already exercised by the repo-local fixtures, but it only needs to analyze the source image; it does not need to normalize or rewrite the image file.

Add or extend tests in `tests/unit/test_phase3_harness.py`. If a helper is extracted, add focused unit tests beside it. Keep `tests/unit/test_qt_signing_shell.py` limited to preview rendering concerns rather than new harness-only analysis logic.

Revision note: created on 2026-04-04 to define the next instrumentation slice after geometry capture, focused on content-aware stamp diagnostics and explicit clipping detection.

Revision note (2026-04-05, completion): the harness now writes stamp-focused overlay crops, records alpha-aware source/content bounds plus projected rendered content bounds, and emits explicit stamp-edge proximity/clipping diagnostics into preview-matrix summaries without changing the signing shell layout behavior.
