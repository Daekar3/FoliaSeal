# Post-Semantics Preview Matrix Rebaseline

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

Issue #50 centralized visible-signature field text, stamp text, and metadata in `VisibleSignatureSemanticsService`. That was the right architecture move, but it means the broad preview-only matrix artifacts are probably stale. This plan refreshes the large preview matrix battery across single-line, multi-line, and wrapped-block signature layouts so the preview side of the build process has current evidence before manual GUI review or further layout architecture work.

## Progress

- [x] (2026-05-02T03:20Z) Created this ExecPlan after confirming the signed rebaseline plan does not include the full preview-matrix battery.
- [ ] Confirm the working tree is clean or contains only planning changes.
- [ ] Run the baseline full preview matrices for single-line, multi-line, and wrapped-block layouts.
- [ ] Run the stress preview matrices for single-line, multi-line, and wrapped-block layouts.
- [ ] Inspect all six summary JSON files and record scenario counts plus any warning/failure counts that changed meaningfully.
- [ ] Classify any regression before changing preview, layout, or semantics code.
- [ ] Update this ExecPlan with artifact directories and final results.

## Surprises & Discoveries

- Observation: the existing post-semantics signed parity rebaseline plan covers signed-output acceptance only, not the large preview-only sweep.
  Evidence: `docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md` runs `signed_preview_parity_matrix.json` and `signed_fit_rejection_matrix.json`, but not the full preview manifests.

- Observation: the checked-in preview battery is large enough to justify its own plan.
  Evidence: current manifest counts are `216` single-line baseline scenarios, `1296` single-line stress scenarios, `288` multi-line baseline scenarios, `432` multi-line stress scenarios, `288` wrapped-block baseline scenarios, and `864` wrapped-block stress scenarios, for `3384` preview scenarios before per-scenario debug artifacts.

## Decision Log

- Decision: keep the preview-matrix rebaseline separate from the signed-output rebaseline.
  Rationale: preview sweeps produce many thousands of PNG/JSON artifacts and test preview fit/diagnostic breadth, while signed acceptance proves final PDF parity and cryptographic output. Combining them would make failures and artifact handling harder to interpret.
  Date/Author: 2026-05-02 / Codex

- Decision: run this before the manual GUI sanity pass.
  Rationale: manual review is most useful after automated preview breadth and signed-output parity are both current. If the broad preview battery is red, manual review should wait until that is classified.
  Date/Author: 2026-05-02 / Codex

- Decision: do not commit generated matrix run directories by default.
  Rationale: these runs create thousands of artifacts. The repository normally treats matrix run directories as local evidence; commit only curated manifests or summary/status docs when they are intentionally tracked.
  Date/Author: 2026-05-02 / Codex

## Outcomes & Retrospective

No implementation outcome yet. At completion, record each artifact directory, expected and actual scenario counts, whether the matrix command completed, and any changed diagnostic counts worth following up.

## Context and Orientation

FoliaSeal has two automated evidence families for visible signatures. Signed-output acceptance signs PDFs and compares final signed annotations to previews. Preview matrices are broader but preview-only: they render many combinations of layout template, stamp image, border, rectangle shape, and visible fields, then record preview images and diagnostics. The "many thousands of artifacts" are produced by these preview matrices because each scenario can write a preview PNG, stamp debug PNG, JSON metadata, and summary entries.

The preview matrix runner is the CLI command `phase3-signing-preview-matrix`, implemented through `src/foliaseal/__main__.py` and `src/foliaseal/presentation/qt/phase3_harness.py`.

Use these checked-in preview manifests:

- `artifacts/preview_sweep_assets/single_line_full_matrix.json`
- `artifacts/preview_sweep_assets/single_line_full_matrix_stress.json`
- `artifacts/preview_sweep_assets/multi_line_full_matrix.json`
- `artifacts/preview_sweep_assets/multi_line_full_matrix_stress.json`
- `artifacts/preview_sweep_assets/wrapped_block_full_matrix.json`
- `artifacts/preview_sweep_assets/wrapped_block_full_matrix_stress.json`

Use the preview fixture inputs:

- `artifacts/preview_sweep_assets/sweep_fixture.pdf`
- `artifacts/preview_sweep_assets/test_identity.p12`

The PKCS#12 passphrase for the preview sweep identity is `secret`.

## Plan of Work

Run each preview matrix into a fresh post-semantics artifact directory. Use separate directories so a failure in one layout family does not corrupt another family’s evidence. After each run, inspect `summary.json`. At minimum record `scenario_count` and whether the command completed. Also look for diagnostic counts related to clipping, overlap, stamp warnings, edge touch, fit rejection, and signable warning scenarios. The exact key names can evolve, so inspect the summary rather than assuming a fixed schema.

If a matrix fails, classify the failure before changing code. A preview matrix failure after Issue #50 may be a semantics regression, a layout regression, a changed diagnostic threshold, a bad stress specimen, or an artifact-generation problem. Do not start Issue #49 layout extraction from this plan; use this plan to produce evidence and classification.

If all six matrices complete and their summary counts are acceptable, update this plan and unblock the manual harness sanity pass.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Check status:

    git status --short

Run the single-line baseline matrix:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix.json \
      --artifacts-dir artifacts/preview_matrix_post_semantics_single_line

Run the single-line stress matrix:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/single_line_full_matrix_stress.json \
      --artifacts-dir artifacts/preview_matrix_post_semantics_single_line_stress

Run the multi-line baseline matrix:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/multi_line_full_matrix.json \
      --artifacts-dir artifacts/preview_matrix_post_semantics_multi_line

Run the multi-line stress matrix:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/multi_line_full_matrix_stress.json \
      --artifacts-dir artifacts/preview_matrix_post_semantics_multi_line_stress

Run the wrapped-block baseline matrix:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/wrapped_block_full_matrix.json \
      --artifacts-dir artifacts/preview_matrix_post_semantics_wrapped_block

Run the wrapped-block stress matrix:

    .venv/bin/python -m foliaseal phase3-signing-preview-matrix \
      --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf \
      --certificate-path artifacts/preview_sweep_assets/test_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/wrapped_block_full_matrix_stress.json \
      --artifacts-dir artifacts/preview_matrix_post_semantics_wrapped_block_stress

For each completed run, inspect the summary:

    .venv/bin/python -m json.tool artifacts/preview_matrix_post_semantics_single_line/summary.json | rg "scenario_count|warning|failure|clipping|overlap|edge|touch|accepted|rejected|signable"

Repeat the summary inspection for the other five artifact directories.

## Validation and Acceptance

This plan is accepted when all six preview matrix commands complete, their `summary.json` files report the expected scenario counts, and any changed warning/failure diagnostics are either accepted as expected after Issue #50 or classified with a follow-up. The expected scenario counts are:

- single-line baseline: `216`
- single-line stress: `1296`
- multi-line baseline: `288`
- multi-line stress: `432`
- wrapped-block baseline: `288`
- wrapped-block stress: `864`

The manual harness sanity pass should not begin until this plan and `docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md` are both green or any failures are explicitly classified.

## Idempotence and Recovery

These commands are safe to rerun, but they can generate thousands of files. If an artifact directory already exists, use a new suffix such as `_run2` rather than overwriting it. If disk space becomes a problem, stop and ask before deleting artifact directories.

If one matrix fails, keep the partial artifact directory and proceed only if the failure is clearly isolated and does not invalidate the remaining runs. Record the failure and retry in a fresh directory after any fix.

## Artifacts and Notes

The current manifest counts were checked on 2026-05-02 with:

    for f in artifacts/preview_sweep_assets/*.json; do ...; done

Relevant counts:

    single_line_full_matrix.json 216
    single_line_full_matrix_stress.json 1296
    multi_line_full_matrix.json 288
    multi_line_full_matrix_stress.json 432
    wrapped_block_full_matrix.json 288
    wrapped_block_full_matrix_stress.json 864

These six matrices total `3384` preview scenarios. Because each scenario can produce multiple artifacts, this is the "full battery" that can create many thousands of files.

## Interfaces and Dependencies

Use the existing `phase3-signing-preview-matrix` CLI. Do not add a new runner. Use `artifacts/preview_sweep_assets/sweep_fixture.pdf` and `artifacts/preview_sweep_assets/test_identity.p12`; do not use signed acceptance assets for preview-only matrices. The preview matrices exercise `SigningDraftWorkflow`, `visible_signature_semantics.py`, `signing_preview_renderer.py`, Qt preview sizing paths, layout planning, and harness diagnostics without writing signed PDFs.

Revision note: Created 2026-05-02 by Codex to cover the full preview artifact battery that is separate from signed-output acceptance.
