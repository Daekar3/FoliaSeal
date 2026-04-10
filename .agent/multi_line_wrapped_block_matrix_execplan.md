# Multi-Line and Wrapped-Block Preview Matrix ExecPlan

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan must be maintained in accordance with [`.agent/PLANS.md`](/home/daekar/SignPDF/Scratch/.agent/PLANS.md).

## Purpose / Big Picture

After this change, the repository will have the same kind of unattended preview-sweep coverage for `multi_line` and `wrapped_block` that it now has for `single_line`. A contributor will be able to run one deterministic matrix for each layout family, inspect PNG and JSON evidence for every stamp position, border width, text size, field-density mix, and representative rectangle family, and then fix only the clustered failures instead of guessing from one-off manual runs.

The user-visible outcome is straightforward. Running the preview matrix commands for `multi_line` and `wrapped_block` should create artifact directories under `artifacts/preview_sweep_runs/` with one preview PNG per scenario, stamp-debug overlays where applicable, and `summary.json` files that identify signability errors, stamp proximity warnings, and scenario metadata. Those summaries become the baseline for the next manual acceptance pass instead of ad hoc exploration.

## Progress

- [x] (2026-04-05 22:42Z) Re-read `.agent/PLANS.md`, the current preview-matrix workflow in `README.md`, and the existing `single_line` sweep assets to reuse the same manifest format and evidence model.
- [x] (2026-04-05 22:49Z) Created this ExecPlan with scope limited to unattended coverage and any tightly related remediation needed to make `multi_line` and `wrapped_block` preview sweeps useful.
- [x] (2026-04-05 22:55Z) Generated checked-in full-matrix manifests for `multi_line` and `wrapped_block` under `artifacts/preview_sweep_assets/`, with 288 deterministic scenarios per layout family.
- [x] (2026-04-05 23:03Z) Ran unattended preview matrices for both layout families and captured their summaries under `artifacts/preview_sweep_runs/`.
- [x] (2026-04-05 23:11Z) Analyzed the baseline summaries, identified one non-blocking `multi_line` warning cluster from the content-proximity threshold, made the threshold layout-aware in `phase3_harness.py`, and reran both matrices to a clean state.
- [x] (2026-04-05 23:18Z) Updated user-facing documentation and verification results so the new sweep assets and final behavior are covered and reproducible.
- [x] (2026-04-05 23:34Z) Reviewed the latest interactive manual-harness capture and corrected one mistaken interpretation: `multi_line` `left/right` are not failing from width strictness, but from genuine text-height overflow in very short horizontal rectangles.
- [x] (2026-04-05 23:41Z) Narrowed non-`single_line` stamp-edge diagnostics so they evaluate only the border-facing edge of the reserved stamp band, which removed a misleading `multi_line top` warning from the manual-harness capture without changing signability.
- [x] (2026-04-05 23:58Z) Investigated the next manual harness report and found a real preview/backend mismatch: `multi_line` preview was not sizing text and stamp widgets to the same reservation bands used by backend fit validation.
- [x] (2026-04-06 00:05Z) Updated `signing_shell.py` so `multi_line` vertical and horizontal preview widgets use reservation-derived band sizes, then added focused Qt regressions for the vertical and horizontal cases.
- [x] (2026-04-06 18:29Z) Reviewed a newer six-state manual harness run and identified two narrower follow-ups: one real backend false negative from `1pt` of width rounding in `multi_line bottom`, and one real backend false positive where a `multi_line` image stamp could be approved even when its reserved stamp band collapsed to zero height.
- [x] (2026-04-06 18:36Z) Added a `1pt` non-`single_line` width tolerance in `_ensure_layout_can_fit(...)`, rejected zero-size image-stamp bands for non-`single_line` layouts, added focused backend regressions, reran the `multi_line` matrix, and kept it green.
- [x] (2026-04-06 19:04Z) Reviewed the latest nine-state manual harness run and found the remaining “looks okay but validation fails” cluster was concentrated in narrow `multi_line` top/bottom boxes where the preview was still drawing text at nominal screen points while the backend was validating PDF-space geometry. Updated `signing_shell.py` so non-`single_line` preview text scales with the preview card’s PDF-space scale, then added a focused Qt regression for that honesty rule.
- [x] (2026-04-09 21:38Z) Revisited a newer six-state manual harness run and traced the remaining false `multi_line top` failures to backend font-size rounding: the preview was rendering the selected `8.5pt`, but backend fit checks were still measuring the same text as `9pt`. Updated backend text measurement to preserve half-point font sizes using rational values and added regressions for the real-world narrow-box case.
- [x] (2026-04-09 09:42Z) Revisited the non-`single_line` preview text scaling after manual comparison against `single_line` and removed it. The preview now treats the selected point size as layout-invariant again, and the focused Qt test now locks that invariant across `single_line`, `multi_line`, and `wrapped_block`.

## Surprises & Discoveries

- Observation: the current checked-in documentation already treats the preview matrix as the preferred deterministic regression net for layout work, so adding `multi_line` and `wrapped_block` coverage is a natural extension rather than a new workflow.
  Evidence: `README.md` documents `phase3-signing-preview-matrix`, the reusable sweep fixture set, and the current `single_line` matrix baseline.

- Observation: `wrapped_block` was already healthier than expected; its first full matrix run produced zero invalid scenarios and zero stamp-content warnings across all 288 scenarios.
  Evidence: `artifacts/preview_sweep_runs/wrapped_block_full_matrix/summary.json` recorded `invalid = 0`, `warnings = 0`, and `touches = 0` before any code changes in this slice.

- Observation: the only first-pass `multi_line` issue was a non-blocking warning cluster on tall top/bottom stamps, and every warning reported exactly `2px` of alpha-aware content clearance.
  Evidence: the initial `multi_line` summary showed 36 warnings, all from top/bottom tall-stamp cases, with `stamp_content_min_edge_distance_px = 2` and no `can_submit` failures.

- Observation: the later manual-harness `multi_line left/right` failures were initially misread as width-gate pessimism, but the captured states show the opposite: width fits exactly while text height exceeds the reserved band by 1.8x to 3.8x.
  Evidence: reconstructing the saved states from `artifacts/phase3_harness_capture.json` against `_layout_reservation_for_template(...)` produced cases such as `text_box 62x25` with `text_area 62x14` and `text_box 112x54` with `text_area 112x14`.

- Observation: the remaining `multi_line top` stamp-edge warning in the manual-harness capture was a diagnostic artifact, not a real border-crowding defect.
  Evidence: the saved top state had `stamp_content_edge_distances_px = {top: 6, left: 1, right: 5, bottom: 0}`. The `0px` distance was on the text-facing band edge, not the border-facing edge, and the scenario was signable with no visible complaint from the user.

- Observation: later manual harness captures exposed a separate preview honesty bug for `multi_line`: the preview was still giving text and stamp labels more live widget space than the backend reservation actually allowed.
  Evidence: a saved `multi_line top` state was marked signable while the preview showed the bottom text row cut off by the border, and a saved `multi_line left` state looked visually roomy while the backend correctly rejected it. The common cause was that the Qt preview body used soft width hints but not reservation-derived fixed heights for non-`single_line` bands.

- Observation: the later six-state manual run refined that picture further. Most “looks like it should fit” failures were still traceable to old preview dishonesty, but two cases exposed real backend edge conditions:
  1. one `multi_line bottom` case failed even though the measured text width only exceeded the reserved width by `1pt`;
  2. one narrower `multi_line bottom` case was allowed even though the reserved image-stamp band height was `0pt`.
  Evidence: reconstructing the saved states from `artifacts/phase3_harness_capture.json` produced `text_box 76x27 / text_area 75x27 / stamp_area 75x37` for the false-negative case and `text_box 76x27 / text_area 76x27 / stamp_area 76x0` for the false-positive case.

- Observation: the latest nine-state manual run showed one more preview/backend seam in narrow `multi_line` top/bottom rectangles. The backend was still validating against actual PDF-space geometry, but the preview was drawing text at nominal screen-point size, which made these narrow vertical cases look roomier on screen than the real PDF layout contract allowed.
  Evidence: states 4, 5, 7, 8, and 9 all failed with `visible_signature_layout_unavailable` even though they looked acceptable in the live preview. The common shape was `multi_line top/bottom` at roughly `80–98pt` width with `8.5pt` Serif italic text. The preview card geometry was already scaled from PDF points into preview pixels, but the preview text size was not scaled to match.

- Observation: after restoring layout-invariant preview text sizing, the remaining narrow `multi_line top` false failures were explained by a different seam: backend measurement was rounding `8.5pt` up to `9pt`, while the Qt preview rendered the actual selected `8.5pt`.
  Evidence: the same five-line `multi_line top` text measured `112x45` at `9pt` but `106x42` at exact `8.5pt`, which is enough to flip the `~117pt` and `~114pt` width captures from failure to success while leaving the narrower `~98pt` case blocked.

## Decision Log

- Decision: keep this slice focused on unattended matrix coverage plus only the minimum remediation needed to make the new matrices trustworthy.
  Rationale: the user asked to proceed to `multi_line` and `wrapped_block` testing next, not to launch a broad architecture rewrite. The right first move is to get deterministic evidence for those layouts, then let any failures drive narrow fixes.
  Date/Author: 2026-04-05 / Codex

- Decision: reuse the existing sweep fixture assets (`sweep_fixture.pdf`, `test_identity.p12`, and the three transparent stamp images) rather than creating a second asset family.
  Rationale: those assets already support wide, tall, and script-like stamp shapes, which is enough to expose layout pathologies without multiplying variables.
  Date/Author: 2026-04-05 / Codex

- Decision: generate one checked-in “full matrix” manifest per layout family instead of one giant mixed manifest.
  Rationale: keeping `multi_line` and `wrapped_block` separate makes the summaries easier to interpret, keeps reruns narrow, and matches the user’s stated desire to test permutations family by family.
  Date/Author: 2026-04-05 / Codex

- Decision: treat the initial `multi_line` tall-stamp warning cluster as instrumentation noise rather than a layout defect and lower the content-proximity threshold to `1px` for `multi_line` and `wrapped_block`.
  Rationale: the clustered scenarios were signable, not touching the band edge, and all reported the same centered `2px` content clearance. Preserving the stricter `2px` warning threshold for `single_line` while using a `1px` threshold for the more spacious non-`single_line` layouts keeps the alert useful without flagging benign centered fits.
  Date/Author: 2026-04-05 / Codex

- Decision: do not loosen the backend fit gate for horizontal `multi_line` based on the latest manual harness run.
  Rationale: the saved `left/right` states are genuinely over-height for their reserved text bands, so allowing them to sign would create preview/output dishonesty rather than simplification. The correct action is to preserve the backend rejection and make the harness evidence clearer.
  Date/Author: 2026-04-05 / Codex

- Decision: for `multi_line` and `wrapped_block`, evaluate stamp-edge warnings against the border-facing edge only.
  Rationale: those layouts intentionally reserve separate text and stamp bands, so touching the text-facing band edge is not the same problem as crowding the outer border. The manual `multi_line top` state demonstrated that the old rule was producing false-positive warnings.
  Date/Author: 2026-04-05 / Codex

- Decision: keep backend fit validation unchanged for `multi_line`, and instead make the Qt preview honor the backend reservation bands more strictly.
  Rationale: the newest manual harness report showed green-but-clipped `multi_line top/bottom` previews and blocked-but-roomy `multi_line left` previews. That is a preview contract bug, not proof that the backend is too strict.
  Date/Author: 2026-04-06 / Codex

- Decision: allow a `1pt` width tolerance for non-`single_line` layouts, but keep height checks strict and reject zero-size image-stamp bands for those layouts.
  Rationale: the manual capture showed one legitimate width-rounding false negative for `multi_line bottom`, while the zero-height stamp-band case is objectively nonconforming and must fail. This keeps the backend honest without reopening the earlier false-permissive `left/right` cases, which were height failures rather than width failures. The `1pt` allowance is explicitly a rounding-seam correction, not a new layout threshold or compactness mode. It exists because text measurement and reservation math currently meet at integer boundaries. The zero-size stamp-band guard is likewise semantic rather than arbitrary: it applies only to templates that reserve separate text and image bands (`multi_line` and `wrapped_block`), and does not apply to `single_line`, whose compact composition model intentionally allows much tighter image placement.
  Date/Author: 2026-04-06 / Codex

- Decision: fix the remaining narrow `multi_line` top/bottom false-negative cluster by making the preview text scale with the preview card’s PDF-space geometry instead of loosening backend validation further.
  Rationale: those states were not another backend threshold bug; they were a preview honesty problem. The card itself was already scaled from PDF points into preview pixels, but the text stayed at nominal screen-point size, which made narrow vertical `multi_line` cases look more permissive than the actual PDF layout contract. Scaling non-`single_line` preview text by the same PDF-to-preview factor keeps the preview aligned with the backend without inventing another validation tolerance.
  Date/Author: 2026-04-06 / Codex

- Decision: reverse the layout-specific preview text scaling and keep typography semantics invariant across layouts.
  Rationale: using different text-size rules for `single_line` versus `multi_line`/`wrapped_block` is more counter-intuitive than the narrow-cluster honesty problem it was trying to solve. The user expectation is that `8.5pt` means the same thing regardless of layout mode; layout selection should only change arrangement and available space. Preview honesty must come from reservation geometry and clipping, not from silently changing text-size semantics by layout.
  Date/Author: 2026-04-09 / Codex

- Decision: preserve the user's selected half-point font sizes in backend measurement instead of rounding them up to the nearest integer point.
  Rationale: once preview typography semantics were made layout-invariant again, the remaining false `multi_line top` failures were no longer a preview problem. They came from backend measurement inflating `8.5pt` to `9pt`. Using rational half-point sizes removes that seam directly and is simpler than adding more validation tolerance.
  Date/Author: 2026-04-09 / Codex

## Outcomes & Retrospective

This plan achieved its purpose. The repository now has checked-in unattended full matrices for both `multi_line` and `wrapped_block`, and both are green under the current harness diagnostics:

- `artifacts/preview_sweep_runs/multi_line_full_matrix/summary.json`: 288 scenarios, 0 invalid, 0 warnings, 0 edge-touch cases.
- `artifacts/preview_sweep_runs/wrapped_block_full_matrix/summary.json`: 288 scenarios, 0 invalid, 0 warnings, 0 edge-touch cases.

The only code change needed in this slice was in the harness diagnostics, not the layout engine itself. That is a good outcome: the first broad `multi_line` and `wrapped_block` coverage did not immediately uncover backend/preview contract defects, only an over-eager proximity warning threshold for one harmless `multi_line` cluster.

After the later manual harness review, that conclusion still holds. The follow-up trace showed one more harness-diagnostic mismatch, but it did not justify loosening backend fit validation. The corrected understanding is:

- `multi_line top/bottom` are healthy under the current layout contract; the harness needed to ignore text-facing stamp-band edges for non-`single_line` warnings.
- `multi_line left/right` remain blocked in very short rectangles for a real reason: the stacked text lines do not fit vertically inside the reserved text band, even when width fits cleanly.

The additional preview correction in `signing_shell.py` tightened that contract further. The live Qt preview now sizes non-`single_line` text and stamp widgets from the same reservation bands that drive backend validation, which should remove the class of “green but visibly clipped” and “blocked but visually roomy” contradictions from the manual harness.

The latest backend follow-up kept that direction intact. After adding the narrow `1pt` width tolerance and the zero-size stamp-band rejection, the unattended `multi_line` matrix remained clean:

- `artifacts/preview_sweep_runs/multi_line_full_matrix/summary.json`: 288 scenarios, 0 invalid, 0 warnings, 0 edge-touch cases.

## Context and Orientation

The batch preview sweep entry point is `src/foliaseal/presentation/qt/phase3_harness.py`. That file owns both the interactive harness and the unattended `phase3-signing-preview-matrix` runner. The matrix runner reads a JSON manifest with a top-level `scenarios` array. Each scenario names a `signature_rect` and an `appearance_overrides` object. The overrides already support the controls we need for this slice: `layout_template`, `stamp_position`, `image_stamp_path`, `signer_label_prefix`, `box_style`, `text_style`, and `visible_fields`.

The checked-in sweep fixture assets live under `artifacts/preview_sweep_assets/`. Right now that directory contains `single_line_full_matrix.json`, `single_line_matrix.json`, `sweep_fixture.pdf`, `test_identity.p12`, and the three stamp images `stamp_wide.png`, `stamp_tall.png`, and `stamp_script.png`. The generated sweep outputs live under `artifacts/preview_sweep_runs/`.

The layout behavior itself spans two core files. `src/foliaseal/application/phase3_signing_backend.py` computes the backend reservation split, fit validation, and stamp placement semantics that ultimately determine whether real signing should fail. `src/foliaseal/presentation/qt/signing_shell.py` mirrors those semantics in the live Qt preview. The purpose of the unattended matrix is to catch mismatches or ugly edge cases across both layers without requiring the user to click through hundreds of permutations manually.

This change slice allows three classes of change:

- behavior change, only if the new matrices reveal real clustered layout failures;
- evidence refresh in `artifacts/preview_sweep_runs/`;
- documentation/status updates tied directly to the new matrix workflow.

This slice must not mix in unrelated signing, certificate, TSA, or PDF-output changes.

## Plan of Work

First, create two new full manifests under `artifacts/preview_sweep_assets/`: one for `multi_line` and one for `wrapped_block`. Each manifest will be generated deterministically from a small set of dimensions instead of hand-editing hundreds of scenarios. The generator can be a one-off repository-local command as long as the resulting JSON files are checked in and stable.

The `multi_line` matrix should exercise all four stamp positions, three border widths (`0.5`, `1.0`, `3.5`), three font sizes (`7.5`, `8.5`, `10.0`), signer label shown and hidden, three stamp assets, and at least three field-density sets that cover sparse, medium, and dense content. It should also vary rectangle families meaningfully: one wide-medium family, one tall-balanced family, and one tighter horizontal family that stresses left/right reservations.

The `wrapped_block` matrix should use the same border, font, signer-label, stamp-asset, and stamp-position variations, but its field sets should be longer on purpose. `wrapped_block` exists to wrap, so the scenarios need enough content to exercise line grouping, including at least one long set with field names enabled and one more compact set without field names.

Second, run the unattended preview matrix separately for each manifest. Write outputs under:

    artifacts/preview_sweep_runs/multi_line_full_matrix/
    artifacts/preview_sweep_runs/wrapped_block_full_matrix/

Then inspect each `summary.json` programmatically. Record total scenarios, invalid scenarios, warning counts, and any recurring clusters by layout position, rectangle family, or stamp asset. If both matrices are already clean, the implementation part of this plan is mostly evidence capture plus documentation refresh. If there are clustered failures, trace the corresponding code path in `phase3_signing_backend.py` and `signing_shell.py`, fix the smallest shared logic defect that explains the cluster, and rerun the affected matrix until the summary stabilizes.

Third, document the new coverage in `README.md` and `phase3_parallel_plan.md`. The README should name the new checked-in manifests and explain that `single_line`, `multi_line`, and `wrapped_block` now each have dedicated unattended sweep coverage. The parallel plan should record the current matrix status as historical baseline for whoever performs the next manual harness pass.

Finally, add or adjust focused tests only where the new matrices expose a real code-path defect or where new helper behavior becomes part of the stable contract. Tests must prove actual user-facing layout behavior, not old threshold implementation details.

## Concrete Steps

All commands below run from the repository root: `/home/daekar/SignPDF/Scratch`.

1. Generate the two manifest files in a deterministic way. The command may be a repository-local Python one-off. It must overwrite:

    artifacts/preview_sweep_assets/multi_line_full_matrix.json
    artifacts/preview_sweep_assets/wrapped_block_full_matrix.json

2. Run the `multi_line` matrix:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/multi_line_full_matrix.json \
      --artifacts-dir artifacts/preview_sweep_runs/multi_line_full_matrix

3. Run the `wrapped_block` matrix:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase preview-passphrase \
      --scenario-manifest-path artifacts/preview_sweep_assets/wrapped_block_full_matrix.json \
      --artifacts-dir artifacts/preview_sweep_runs/wrapped_block_full_matrix

4. Summarize the results from each `summary.json` with a short script or shell command that counts:

    - total scenarios,
    - scenarios with `preview_snapshot.can_submit == false`,
    - scenarios with `stamp_content_within_warning_distance == true`,
    - scenarios with `stamp_content_touches_band_edge == true`,
    - recurring failure groups by `stamp_position`.

5. If clustered failures appear, fix the responsible code path, rerun the affected matrix, and then run:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

Expected success shape:

    All checks passed!
    ...
    329 passed in <roughly a few seconds>

The exact pass count may rise if new focused tests are added during this slice.

## Validation and Acceptance

This plan is successful when:

- both new manifest files exist and are checked in;
- both unattended matrix commands complete and write `summary.json`;
- the result summaries are understandable enough to guide a later manual pass;
- any newly discovered clustered failure is either fixed or explicitly documented in this ExecPlan and the main status docs;
- the repository test suite still passes after the work.

The most important human validation is not “every scenario is pretty.” It is “we can now inspect `multi_line` and `wrapped_block` systematically, the same way we can inspect `single_line`, and we have objective evidence for where they still need work.”

## Idempotence and Recovery

The manifest-generation step is safe to rerun; it should overwrite the same JSON files deterministically. The matrix commands are also safe to rerun; they overwrite the artifact directories with fresh PNG and JSON evidence. If a remediation attempt makes results worse, rerun the same matrix after reverting or adjusting the suspect code path and compare the new `summary.json` to the previous one. No external state beyond the repository-local artifacts is modified.

## Artifacts and Notes

The key artifacts produced by this plan are:

- `artifacts/preview_sweep_assets/multi_line_full_matrix.json`
- `artifacts/preview_sweep_assets/wrapped_block_full_matrix.json`
- `artifacts/preview_sweep_runs/multi_line_full_matrix/summary.json`
- `artifacts/preview_sweep_runs/wrapped_block_full_matrix/summary.json`

The expected evidence shape inside each run directory is the same as the existing `single_line` matrix:

- one preview PNG per scenario,
- one stamp-debug PNG per stamped scenario,
- one `summary.json` that records preview snapshots, backend reservation snapshots, and render-capture diagnostics.

## Interfaces and Dependencies

This plan depends on the existing matrix runner in `src/foliaseal/presentation/qt/phase3_harness.py`. It already knows how to interpret the manifest schema and write the preview/debug artifacts; this plan should not create a second runner.

The backend layout contract remains in `src/foliaseal/application/phase3_signing_backend.py`, especially `_layout_reservation_for_template`, `_background_layout_for_stamp`, and `_visible_signature_fit_issues_for_stamp_text`. The preview mirroring path remains in `src/foliaseal/presentation/qt/signing_shell.py`, especially `_preview_text_width_limit`, `_preview_stamp_max_size`, `_preview_vertical_band_geometry`, and `_update_preview_controls`.

Revision note (2026-04-05): created this plan to move the unattended preview-sweep workflow beyond `single_line` and into `multi_line` and `wrapped_block`, using the same fixture set, evidence model, and remediation discipline.
Revision note (2026-04-05): updated after implementation to record the generated manifest counts, the first-pass `multi_line` warning cluster, the layout-aware harness-threshold adjustment, and the final clean matrix results.
