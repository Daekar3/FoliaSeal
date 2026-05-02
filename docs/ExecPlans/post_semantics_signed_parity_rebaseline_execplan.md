# Post-Semantics Signed Parity Rebaseline

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

Issue #50 moved visible-signature field text, stamp text, and PDF metadata into `VisibleSignatureSemanticsService`. Before doing more manual GUI review or broader architectural extraction, rerun the signed-output acceptance baselines to prove the user-facing promise still holds: the visible signature reviewed in preview is the visible signature written into the signed PDF. This plan should produce fresh automated evidence for success-only preview-vs-signed-output parity and intentional fit rejection behavior after the semantics migration.

## Progress

- [x] (2026-05-02T03:14Z) Created this ExecPlan after reviewing the existing signed parity and Issue #50 cleanup plans.
- [x] (2026-05-02T03:21Z) Confirmed the working tree contained only the planning/doc slice before running evidence commands.
- [x] (2026-05-02T03:26Z) Ran the success-only signed preview parity matrix after the semantics migration.
- [x] (2026-05-02T03:27Z) Ran the signed fit-rejection matrix after the semantics migration.
- [x] (2026-05-02T03:31Z) Inspected the new summary JSON files and classified stale manifest specimens rather than production regressions.
- [x] (2026-05-02T03:39Z) Updated the signed parity and rejection manifests, this ExecPlan, and the follow-on manual harness plan with the rebaseline result.
- [x] (2026-05-02T03:43Z) Commit the rebaseline manifest and documentation changes.

## Surprises & Discoveries

- Observation: `docs/ExecPlans/direct_annotation_appearance_rendering_execplan.md` already says the next useful step is a manual harness sanity pass.
  Evidence: its final follow-on section starts with "The next useful step is a short manual harness sanity pass against the current GUI path."

- Observation: that manual-pass recommendation predates the Issue #50 semantics migration.
  Evidence: Issue #50 commits `3e0686e24`, `2ed5a99f7`, `928c4fcd3`, `9eaf1af86`, and `e9b739e4d` changed the preview and backend text/metadata path after the signed parity baseline recorded in the direct annotation plan.

- Observation: headless CI or terminal evidence runs need Qt's offscreen platform for this matrix command.
  Evidence: running without `QT_QPA_PLATFORM=offscreen` failed with `qt.qpa.xcb: could not connect to display :0`; reruns with the offscreen platform completed.

- Observation: five expected-success horizontal single-line replay specimens were stale after the semantics cleanup.
  Evidence: `single_line_left_stamp_manual_replay_06_minimum_success`, `single_line_left_stamp_manual_replay_07_success`, `single_line_left_stamp_manual_replay_08_roomy_success`, `single_line_right_stamp_manual_replay_07_short_height_success`, and `single_line_left_stamp_manual_replay_08_short_height_success` failed both preview and backend validation as out-of-bounds or non-fitting rectangles, while `preview_output_comparison_failure_count` stayed `0`.

- Observation: one expected-rejection specimen was stale in the other direction.
  Evidence: `single_line_left_stamp_sparse_large` signed successfully with its old `320 x 52 pt` rectangle. Tightening it to `160 x 32 pt` restored the intentional rejection contract.

- Observation: pyHanko self-signed TSA validation traces and `FFTM NOT subset` warnings are noisy but not acceptance failures for this evidence run.
  Evidence: both final summaries had `acceptance_expectations_passed = true`, zero cryptographic validation failures, and zero preview-output comparison failures.

## Decision Log

- Decision: insert an automated rebaseline before the manual GUI sanity pass.
  Rationale: Issue #50 touched semantic stamp text and metadata consumed by both preview and backend signing. Even though focused tests passed, the signed-output acceptance matrices are the cheapest end-to-end proof that preview and written PDF still match.
  Date/Author: 2026-05-02 / Codex

- Decision: keep this rebaseline separate from the manual harness sanity pass.
  Rationale: automated parity evidence and human GUI artifact review are different change classes. If the automated baseline regresses, the manual pass should wait until the regression is classified or fixed.
  Date/Author: 2026-05-02 / Codex

- Decision: do not start Issue #49 layout extraction in this plan.
  Rationale: Issue #49 is architectural layout-policy extraction. This plan is build-process evidence refresh after semantic changes. Mixing extraction with evidence refresh would make parity failures harder to interpret.
  Date/Author: 2026-05-02 / Codex

- Decision: update manifests instead of production code for the post-semantics red runs.
  Rationale: every failing success scenario was invalid under both preview and backend validation, and the only rejection mismatch was still a coherent successful signing. No preview-vs-signed-output comparison failures appeared, so this was stale specimen data rather than a rendering or semantics regression.
  Date/Author: 2026-05-02 / Codex

- Decision: keep generated post-semantics run directories ignored.
  Rationale: the durable evidence is the checked-in manifest contract and this plan's recorded summary counts. The generated images, PDFs, and per-scenario JSON bundles are large rebuildable artifacts.
  Date/Author: 2026-05-02 / Codex

## Outcomes & Retrospective

The post-semantics signed-output rebaseline is green after correcting stale manifest specimens.

Final success-only parity evidence:

    artifacts/signed_preview_parity_post_semantics_run2/summary.json
    scenario_count = 18
    successful_signing_run_count = 18
    preview_output_comparison_failure_count = 0
    expected_outcome_mismatch_count = 0
    acceptance_expectations_passed = true

Final intentional rejection evidence:

    artifacts/signed_fit_rejection_post_semantics_run3/summary.json
    scenario_count = 3
    successful_signing_run_count = 0
    expected_intentional_rejection_count = 3
    matched_expected_intentional_rejection_count = 3
    expected_outcome_mismatch_count = 0
    acceptance_expectations_passed = true

The follow-on manual harness sanity pass can proceed after the full preview-matrix rebaseline plan is also green or has classified any failures.

## Context and Orientation

FoliaSeal signs PDFs and can draw a visible signature rectangle on the signed page. A preview is the visual signature card shown before signing; signed-output parity means the rendered signature annotation in the final PDF matches that preview closely enough to trust the preview. A fit rejection is an intentional validation failure where the selected visible signature rectangle is too small for the requested text and stamp.

The relevant code paths are:

- `src/foliaseal/application/visible_signature_semantics.py`, which now owns visible fields, stamp text, metadata reason/location/contact info, and semantic fit aggregation.
- `src/foliaseal/application/signing_draft_workflow.py`, which builds `SigningDraftPreview` and now populates `SigningDraftPreview.stamp_text` from the semantics service.
- `src/foliaseal/application/signing_preview_renderer.py`, which renders canonical preview snapshots using the resolved preview stamp text.
- `src/foliaseal/application/phase3_signing_backend.py`, which signs through pyHanko and now resolves final-signing semantics once for stamp text, fit validation, and PDF metadata.
- `src/foliaseal/presentation/qt/phase3_harness.py`, which runs the signed acceptance matrix and writes per-scenario artifacts plus `summary.json`.

The checked-in scenario manifests are:

- `artifacts/preview_sweep_assets/signed_preview_parity_matrix.json` for success-only preview-vs-signed-output appearance parity.
- `artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json` for intentional fit-rejection behavior.

The checked-in acceptance inputs are:

- `artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf`
- `artifacts/generated_acceptance_assets/signed_acceptance_identity.p12`

The PKCS#12 passphrase used by the repository acceptance assets is `secret`.

## Plan of Work

Start by verifying that the working tree is clean enough to run evidence without mixing unrelated changes. Then run the success-only signed parity matrix into a fresh ignored artifact directory whose name makes the post-semantics context clear. Inspect its `summary.json`; the expected healthy result is that all scenarios sign successfully, `preview_output_comparison_failure_count` is zero, `expected_outcome_mismatch_count` is zero, and `acceptance_expectations_passed` is true.

Next run the signed fit-rejection matrix into a separate fresh ignored artifact directory. Inspect its `summary.json`; the expected healthy result is that the configured rejection scenarios fail signing for the expected validation reason and do not produce signed-output parity failures.

If either matrix fails, do not jump into layout extraction. First classify the failure as one of: semantic text/metadata drift introduced by Issue #50, layout/rendering regression, bad scenario specimen, or artifact-analysis defect. Record the classification in this plan and only then decide whether to fix code or adjust the matrix.

If both matrices pass, update this plan with the artifact directories and mark the manual harness sanity pass ExecPlan as unblocked. Do not check in generated run directories unless the repository already tracks the specific summary file you intend to update; most matrix run outputs belong under ignored `artifacts/` directories.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Check the current status:

    git status --short

Run the success-only signed preview parity matrix:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix \
      --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf \
      --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/signed_preview_parity_matrix.json \
      --artifacts-dir artifacts/signed_preview_parity_post_semantics_run2

The command should print:

    Phase 3 signed acceptance matrix
    - scenarios executed: 18
    - successful signings: 18
    - artifacts directory: artifacts/signed_preview_parity_post_semantics_run2
    - summary json: artifacts/signed_preview_parity_post_semantics_run2/summary.json

Inspect the summary:

    .venv/bin/python -m json.tool artifacts/signed_preview_parity_post_semantics_run2/summary.json | rg "scenario_count|successful_signing_run_count|preview_output_comparison_failure_count|expected_outcome_mismatch_count|acceptance_expectations_passed"

Run the signed fit-rejection matrix:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix \
      --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf \
      --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 \
      --passphrase "secret" \
      --scenario-manifest-path artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json \
      --artifacts-dir artifacts/signed_fit_rejection_post_semantics_run3

Inspect that summary:

    .venv/bin/python -m json.tool artifacts/signed_fit_rejection_post_semantics_run3/summary.json | rg "scenario_count|successful_signing_run_count|expected_outcome_mismatch_count|acceptance_expectations_passed"

Run focused tests if a code change is needed:

    .venv/bin/ruff check src/foliaseal/application/signing_preview_renderer.py src/foliaseal/application/phase3_signing_backend.py src/foliaseal/application/visible_signature_semantics.py tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py
    .venv/bin/pytest -q tests/unit/test_visible_signature_semantics.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py

## Validation and Acceptance

This plan is accepted when the success-only signed preview parity matrix passes after Issue #50, the signed fit-rejection matrix passes after Issue #50, and this document records the exact artifact directories and summary counts. If both matrices pass, the next plan is `docs/ExecPlans/manual_harness_sanity_pass_execplan.md`. If either matrix fails, acceptance requires a concrete classification and a follow-up fix plan before manual GUI review begins.

## Idempotence and Recovery

The matrix commands are safe to rerun. If an artifacts directory already exists, choose a new directory name with a suffix such as `_run2`; do not delete old evidence unless the user explicitly asks. Generated matrix run directories under `artifacts/` are usually ignored by git, but always check `git status --short` before committing.

If a run fails halfway, inspect the partial `summary.json` and per-scenario directories before rerunning. A partially written run directory can still contain useful evidence. Use a new artifacts directory for the retry so the two attempts are not mixed.

## Artifacts and Notes

Current pre-plan baseline from `docs/ExecPlans/direct_annotation_appearance_rendering_execplan.md`:

    artifacts/signed_preview_parity_matrix_run_v17/summary.json
    scenario_count = 18
    successful_signing_run_count = 18
    preview_output_comparison_failure_count = 0
    expected_outcome_mismatch_count = 0
    acceptance_expectations_passed = true

The signed rejection baseline was previously recorded as green at:

    artifacts/signed_fit_rejection_matrix_run_v1/summary.json

## Interfaces and Dependencies

Use the existing CLI command implemented in `src/foliaseal/__main__.py` and `src/foliaseal/presentation/qt/phase3_harness.py`: `python -m foliaseal phase3-signing-acceptance-matrix`. Do not add a new runner. Use the manifests in `artifacts/preview_sweep_assets/` and the acceptance assets in `artifacts/generated_acceptance_assets/`.

This plan depends on the semantics ownership documented by Issue #50 and `docs/ARCHITECTURE.md`: semantic text belongs to `visible_signature_semantics.py`, layout geometry belongs to `visible_signature_layout.py`, preview rendering belongs to `signing_preview_renderer.py`, and PDF signing belongs to `phase3_signing_backend.py`.

Revision note: Created 2026-05-02 by Codex to insert a post-Issue-50 automated parity rebaseline before manual GUI harness review.
