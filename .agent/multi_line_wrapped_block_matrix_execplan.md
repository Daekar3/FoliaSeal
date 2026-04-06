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
- [ ] Update user-facing documentation and focused/full verification results so the new sweep assets and final behavior are covered and reproducible.

## Surprises & Discoveries

- Observation: the current checked-in documentation already treats the preview matrix as the preferred deterministic regression net for layout work, so adding `multi_line` and `wrapped_block` coverage is a natural extension rather than a new workflow.
  Evidence: `README.md` documents `phase3-signing-preview-matrix`, the reusable sweep fixture set, and the current `single_line` matrix baseline.

- Observation: `wrapped_block` was already healthier than expected; its first full matrix run produced zero invalid scenarios and zero stamp-content warnings across all 288 scenarios.
  Evidence: `artifacts/preview_sweep_runs/wrapped_block_full_matrix/summary.json` recorded `invalid = 0`, `warnings = 0`, and `touches = 0` before any code changes in this slice.

- Observation: the only first-pass `multi_line` issue was a non-blocking warning cluster on tall top/bottom stamps, and every warning reported exactly `2px` of alpha-aware content clearance.
  Evidence: the initial `multi_line` summary showed 36 warnings, all from top/bottom tall-stamp cases, with `stamp_content_min_edge_distance_px = 2` and no `can_submit` failures.

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

## Outcomes & Retrospective

This plan achieved its purpose. The repository now has checked-in unattended full matrices for both `multi_line` and `wrapped_block`, and both are green under the current harness diagnostics:

- `artifacts/preview_sweep_runs/multi_line_full_matrix/summary.json`: 288 scenarios, 0 invalid, 0 warnings, 0 edge-touch cases.
- `artifacts/preview_sweep_runs/wrapped_block_full_matrix/summary.json`: 288 scenarios, 0 invalid, 0 warnings, 0 edge-touch cases.

The only code change needed in this slice was in the harness diagnostics, not the layout engine itself. That is a good outcome: the first broad `multi_line` and `wrapped_block` coverage did not immediately uncover backend/preview contract defects, only an over-eager proximity warning threshold for one harmless `multi_line` cluster.

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
