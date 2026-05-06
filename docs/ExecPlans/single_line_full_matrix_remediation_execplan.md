# Single-Line Full-Matrix Remediation

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this change, the `single_line` preview and output path should behave predictably across the full set of practical stamp positions, border weights, text sizes, stamp shapes, and compact-versus-roomy rectangle families exercised by the repository-local matrix. A contributor should be able to run one unattended matrix command, inspect the summary JSON and the overlay PNGs, and see no compact `single_line` cases where meaningful stamp content is pushed into warning-distance territory merely because the current reservation or preview-fit logic starved the stamp band unnecessarily.

The user-visible proof is straightforward. Run the full single-line matrix under `artifacts/preview_sweep_assets/single_line_full_matrix.json`. When the remediation is complete, the summary JSON should no longer report content-warning clusters for the currently failing scenario families, and the corresponding preview/debug PNGs should show the stamp content with comfortable clearance instead of one- or two-pixel margins.

## Progress

- [x] (2026-04-05 03:02Z) Generated and ran a broader `single_line` matrix with 216 scenarios covering all four positions, three border weights, three stamp assets, three text sizes, and compact/roomier rectangle families per orientation.
- [x] (2026-04-05 03:08Z) Clustered the content-aware warnings from `artifacts/preview_sweep_runs/single_line_full_matrix/summary.json` and identified the recurring failure families.
- [x] (2026-04-05 03:16Z) Traced the relevant backend reservation and preview-fit code paths in `src/foliaseal/application/phase3_signing_backend.py` and `src/foliaseal/presentation/qt/signing_shell.py`.
- [x] (2026-04-05 03:34Z) Implemented the traced remediation slice for compact vertical and tight horizontal `single_line`.
- [x] (2026-04-05 03:39Z) Re-ran the full matrix, compared the before/after warning clusters, and refreshed this plan with the outcome.

## Surprises & Discoveries

- Observation: all 216 full-matrix scenarios remain semantically `Ready to sign.` before and after the remediation, so the preview-quality diagnostics are intentionally stricter than the draft validator.
  Evidence: the baseline and rerun both complete all 216 scenarios successfully, while only the content-aware preview metrics distinguish the cramped baseline from the remediated result.

- Observation: the original failures were clustered, not random, and the successful fix followed those clusters closely.
  Evidence: the baseline warning scenarios concentrated in:
  - vertical compact `top/bottom short` with `stamp_tall` in every border/text permutation
  - vertical compact `top/bottom short` with `stamp_script` in every border/text permutation
  - vertical compact `top/bottom short` with `stamp_wide` when either text size reaches `10.0pt` or border width reaches `3.5pt`
  - horizontal `left/right tight` with `stamp_tall` in every border/text permutation
  - one `top/bottom medium` outlier with `stamp_tall` at `3.5pt` and `10.0pt`
  After centering compact stamp content inside the reserved band and adding a shared compact-content inset, those clusters disappeared entirely in the rerun.

- Observation: the new `stamp_pixmap_touches_band_edge` flag is effectively always true and therefore not useful as a remediation target by itself.
  Evidence: the full matrix reports `pixmap_touch_count 216`, which happens because the preview intentionally aligns the pixmap flush to one band edge in several layout modes; the content-aware bounds are the meaningful signal.

- Observation: the compact vertical failures were not caused by total clipping of the painted content; they were caused by the stamp band becoming too shallow to provide comfortable content clearance and by the rendered image being pinned too aggressively inside that band.
  Evidence: before remediation, representative scenarios such as `single_top_short_border_3_5_stamp_tall_text_8_5` sat at `stamp_content_min_edge_distance_px = 1`. After remediation, that same scenario reports `stamp_content_min_edge_distance_px = 3`, with content edges `{'bottom': 4, 'left': 237, 'right': 238, 'top': 3}`.

- Observation: the tight horizontal tall-stamp failures were width-driven rather than height-driven, but the decisive fix was still the same shared compact-content inset plus correct centering semantics.
  Evidence: `single_left_tight_border_3_5_stamp_tall_text_8_5` and `single_right_tight_border_1_0_stamp_tall_text_10_0` now both report balanced content clearance of `4` pixels on every side in the rerun.

- Observation: the original vertical compact output path had a hidden alignment asymmetry that the content-aware matrix made easy to trace.
  Evidence: `_background_layout_for_stamp()` in `src/foliaseal/application/phase3_signing_backend.py` had a `single_line top/bottom` special case that left-aligned the fitted image inside the reserved stamp band. Removing that special case and always centering the remaining horizontal slack was necessary to eliminate the vertical warning families.

- Observation: the real PySide alignment lookup is more brittle than the fake test Qt namespace suggested.
  Evidence: the live preview initially resolved vertical stamp alignment as `1` rather than centered when `Qt.AlignCenter` was not exposed through a simple direct attribute path. Adding an `AlignmentFlag` fallback in both the preview and harness code was necessary to make the live GUI follow the intended centering semantics.

## Decision Log

- Decision: treat the 216-scenario full matrix as the primary acceptance corpus for this remediation slice.
  Rationale: the earlier curated sweep was useful for spot checks, but the new full matrix exposes the real cluster structure of the remaining failures and prevents single-case tuning.
  Date/Author: 2026-04-05 / Codex

- Decision: the next code-change slice must start with trace-driven diagnosis of both backend reservation and preview fitting before changing any constants.
  Rationale: the current failures arise from interactions among reservation, text wrapping, preview scaling, and widget fitting. Tweaking one padding constant in isolation is unlikely to fix all clusters cleanly.
  Date/Author: 2026-04-05 / Codex

- Decision: use the content-aware warning metrics, not the pixmap-edge metric, as the main regression gate for this slice.
  Rationale: the pixmap-edge metric is currently dominated by intentional alignment behavior and would produce false failures for healthy scenarios.
  Date/Author: 2026-04-05 / Codex

## Outcomes & Retrospective

The remediation landed cleanly and the full-matrix rerun reduced the content-warning baseline from `66/216` scenarios to `0/216`.

The most important contributing causes were:

- backend-side compact stamp placement for `single_line top/bottom` was still left-aligning the image inside the reserved band in `_background_layout_for_stamp()`
- preview-side alignment lookup for the real Qt namespace was not reliably resolving `AlignCenter`
- compact stamps in both vertical and tight horizontal layouts had no shared internal safety gutter, so tall and script assets could use the entire reserved band and end up at one- or two-pixel clearance even when the reservation itself was technically valid

The implemented fix set was intentionally narrow and trace-driven:

- add `_single_line_stamp_content_inset()` in `src/foliaseal/application/phase3_signing_backend.py` and apply it to compact single-line stamp fitting
- remove the special-case left alignment for vertical compact stamps in `_background_layout_for_stamp()` and center the fitted image inside the reserved band
- mirror the same compact-content inset in `src/foliaseal/presentation/qt/signing_shell.py` when converting reserved stamp regions into preview pixmap target sizes
- resolve Qt alignment flags robustly in the live preview path so the real GUI uses the intended centered alignment semantics
- center horizontal `left/right` preview stamps within their already-reserved side band instead of pinning the pixmap to the outer edge

Representative before/after improvements:

- `single_top_short_border_3_5_stamp_tall_text_8_5`: from `stamp_content_min_edge_distance_px = 1` to `3`
- `single_bottom_short_border_3_5_stamp_script_text_8_5`: now `stamp_content_min_edge_distance_px = 4`
- `single_left_tight_border_3_5_stamp_tall_text_8_5`: now `stamp_content_min_edge_distance_px = 4`
- `single_right_tight_border_1_0_stamp_tall_text_10_0`: now `stamp_content_min_edge_distance_px = 4`

No warning clusters remain in the current 216-scenario corpus, so there are no intentionally accepted exceptions in this slice. The main residual risk is future regression if new stamp-position heuristics bypass the shared compact-content inset or reintroduce preview/backend alignment drift.

## Context and Orientation

The matrix harness and the content-aware diagnostics live in `src/foliaseal/presentation/qt/phase3_harness.py`. That file is not the right place to fix the remaining layout issues; it only provides the evidence that tells us where the behavior is still too tight.

The actual reservation logic for visible signatures lives in `src/foliaseal/application/phase3_signing_backend.py`. The most important functions for this plan are:

- `_layout_reservation_for_template()`, which divides the requested signature rectangle into text and stamp regions
- `_single_line_vertical_outer_margin()`, which determines the symmetric outer inset for compact `top/bottom` single-line layouts
- `_effective_horizontal_text_reservation_width()`, which determines how much width is reserved for text in `left/right` single-line layouts
- `_base_layout_spacing()`, which supplies edge margins and the separator gap used by the reservation logic

The preview path that mirrors those decisions lives in `src/foliaseal/presentation/qt/signing_shell.py`. The critical functions there are:

- `_preview_text_width_limit()`, which translates the backend text reservation into preview pixels for `left/right`
- `_preview_stamp_max_size()`, which turns the backend stamp reservation into a preview pixmap target size for `left/right`
- `_preview_vertical_band_geometry()`, which translates the backend text/stamp heights into preview pixel bands for `top/bottom`
- `_fit_vertical_preview_band_geometry()`, which modifies those bands to satisfy live Qt size hints
- `_update_preview_controls()`, which applies all of the above to the actual Qt labels and layouts

The current full-matrix manifest is `artifacts/preview_sweep_assets/single_line_full_matrix.json`, and the latest run artifacts live in `artifacts/preview_sweep_runs/single_line_full_matrix/`.

## Current Findings

The refreshed full matrix still contains 216 scenarios, and every one of them remains semantically valid according to the draft workflow. After remediation, none of those scenarios carry a content-proximity warning according to the content-aware diagnostics.

The pre-remediation warning clusters split into two main groups:

- compact vertical `top/bottom` cases where tall or script-like stamps ended up with only one or two pixels of meaningful content clearance because the compact stamp band had no internal gutter and the rendered image was not centered correctly
- tight horizontal `left/right` cases where tall stamps sat only two pixels from the side edge because the preview pinned the pixmap to the outer edge of the side band rather than centering the fitted image within that band

The traced remediation resolved both groups without changing the manifest, warning threshold, or harness logic. The current representative scenarios now show:

- `single_top_short_border_3_5_stamp_tall_text_8_5`: `stamp_content_min_edge_distance_px = 3`
- `single_bottom_short_border_3_5_stamp_script_text_8_5`: `stamp_content_min_edge_distance_px = 4`
- `single_left_tight_border_3_5_stamp_tall_text_8_5`: balanced content edges of `4` on all sides
- `single_right_tight_border_1_0_stamp_tall_text_10_0`: balanced content edges of `4` on all sides

The debug overlays in `artifacts/preview_sweep_runs/single_line_full_matrix/` confirm that the projected non-transparent content bounds now sit cleanly inside the reserved stamp band for those former hotspots.

## Plan of Work

Start with tracing, not editing. Instrument or temporarily log the exact reservation values for a few representative warning scenarios and a few clean comparison scenarios. For vertical, use `single_top_short_border_3_5_stamp_tall_text_8_5`, `single_bottom_short_border_3_5_stamp_script_text_8_5`, and a clean medium-box comparison. For horizontal, use `single_left_tight_border_3_5_stamp_tall_text_8_5`, `single_right_tight_border_1_0_stamp_tall_text_10_0`, and a clean mid-box comparison. Record the backend text/stamp area dimensions, the preview pixel bands, the Qt size hints, and the final rendered content distances.

Once the trace is in hand, address vertical compact `top/bottom` first. The likely root cause chain is:

- `_layout_reservation_for_template()` reserves full `text_box_height` first
- `remaining_height` becomes the entire stamp budget
- `_preview_vertical_band_geometry()` copies that split into preview pixels
- `_fit_vertical_preview_band_geometry()` allows text to grow further to satisfy Qt hints
- the stamp band is left with only a thin strip, especially for tall or script-like images

The remediation must decide whether to change the backend reservation, the preview fit adjustment, or both. The plan should prefer a shared semantic fix over a preview-only cosmetic patch, but only after verifying whether output parity would benefit from the same change.

Then address horizontal tight `left/right` with tall stamps. The likely root cause chain is:

- `_effective_horizontal_text_reservation_width()` still reserves width primarily from the text box
- `_layout_reservation_for_template()` gives the stamp the remaining width and the full height
- `_preview_stamp_max_size()` fits the tall image into that narrow stamp region
- the projected content box ends up with only two pixels of side clearance

Trace whether the hard preview cap in `_preview_stamp_max_size()` contributes materially, or whether the real issue is the upstream backend width reservation. Do not guess. If the cap is irrelevant for the warning cases, leave it alone and document that result.

Keep the change slice narrow. This plan should change reservation and preview-fit logic only where the traces show a real causal path to the warning clusters. Do not mix in output-analysis work, GIF normalization, or timestamping.

## Milestones

### Milestone 1: Trace Representative Failures End to End

At the end of this milestone, a novice should be able to pick one warning scenario and one clean comparison scenario and see the exact values that flow through the backend reservation, preview geometry translation, preview fit adjustment, and final content-aware warning computation. The proof is a short trace note checked into `docs/ExecPlans/` or captured in this ExecPlan’s `Surprises & Discoveries` section with file/function names and concrete numbers.

### Milestone 2: Fix Compact Vertical `Top/Bottom`

At the end of this milestone, the vertical warning clusters should be materially reduced. Specifically, the compact `top/bottom short` cases with tall and script stamps should no longer sit at one- or two-pixel content clearance by default. The proof is a rerun of the full matrix showing a reduced warning count for the `top/bottom short` families plus representative preview/debug PNGs that look meaningfully less cramped.

### Milestone 3: Fix Tight Horizontal `Left/Right`

At the end of this milestone, the `left/right tight` tall-stamp warnings should be eliminated or reduced to explicitly justified exceptions. The proof is the full matrix rerun plus a trace showing whether the successful fix came from backend width reservation, preview max-size behavior, or both.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Regenerate the full matrix if needed:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix.json \
      --artifacts-dir artifacts/preview_sweep_runs/single_line_full_matrix

Run the focused verification while iterating:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_signing_shell.py \
      tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

When tracing representative scenarios, capture or print the values coming from:

    src/foliaseal/application/phase3_signing_backend.py::_layout_reservation_for_template
    src/foliaseal/presentation/qt/signing_shell.py::_preview_vertical_band_geometry
    src/foliaseal/presentation/qt/signing_shell.py::_fit_vertical_preview_band_geometry
    src/foliaseal/presentation/qt/signing_shell.py::_preview_text_width_limit
    src/foliaseal/presentation/qt/signing_shell.py::_preview_stamp_max_size

## Validation and Acceptance

This remediation is accepted when all of the following are true:

- The full 216-scenario matrix still completes successfully.
- The current warning baseline of 66 scenarios is reduced to `0`, including the formerly failing families:
  - `top/bottom short` with `stamp_tall`
  - `top/bottom short` with `stamp_script`
  - `left/right tight` with `stamp_tall`
- Representative debug PNGs for the formerly failing clusters show visibly improved stamp-content clearance.
- Focused unit tests pass, and new regression tests pin the corrected reservation/preview behavior.

## Idempotence and Recovery

The matrix generation and focused tests are safe to rerun. This plan should use repository-local assets only, so no manual cleanup is needed beyond overwriting the `artifacts/preview_sweep_runs/single_line_full_matrix/` directory contents with a fresh run. If a trace experiment becomes noisy, remove or gate the temporary logging before concluding the slice.

## Artifacts and Notes

Current baseline artifacts and counts to compare against:

- manifest: `artifacts/preview_sweep_assets/single_line_full_matrix.json`
- summary: `artifacts/preview_sweep_runs/single_line_full_matrix/summary.json`
- baseline scenario count: `216`
- baseline warning count: `66`
- baseline content-edge touches: `0`

Current remediated outcome:

- rerun scenario count: `216`
- rerun warning count: `0`
- rerun content-edge touches: `0`

Representative current warning scenarios:

- `single_top_short_border_3_5_stamp_tall_text_8_5`
- `single_bottom_short_border_3_5_stamp_script_text_8_5`
- `single_left_tight_border_3_5_stamp_tall_text_8_5`
- `single_right_tight_border_1_0_stamp_tall_text_10_0`

Representative current clean comparisons:

- `single_top_medium_border_1_0_stamp_wide_text_8_5`
- `single_bottom_medium_border_1_0_stamp_wide_text_8_5`
- `single_left_mid_border_1_0_stamp_tall_text_8_5`
- `single_right_mid_border_1_0_stamp_tall_text_8_5`

## Interfaces and Dependencies

Do not add new dependencies. Use the existing content-aware diagnostics in `src/foliaseal/presentation/qt/phase3_harness.py` as the acceptance signal. Keep behavior changes concentrated in:

- `src/foliaseal/application/phase3_signing_backend.py` for shared reservation semantics
- `src/foliaseal/presentation/qt/signing_shell.py` for preview-side fit logic that must mirror those semantics

If a new temporary trace helper is needed, keep it local to the touched module or a short-lived `docs/ExecPlans/` note. Do not expand the public CLI surface for this slice.

Revision note: created on 2026-04-05 after running the 216-scenario full `single_line` matrix and clustering the remaining content-aware warnings by position, rectangle family, stamp asset, border weight, and text size.
