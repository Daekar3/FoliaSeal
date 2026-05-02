# Manual Harness Sanity Pass For Signed Preview Parity

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `docs/PLANS.md`.

## Purpose / Big Picture

After the automated signed-output parity baselines are green, perform a short human review of the live Qt signing harness. The goal is to verify what an actual user sees: the preview card should look rational before signing, the successful signed PDF should visually match that preview, and an intentional rejection case should clearly explain why no signed output was written. This is a build-process confidence slice, not a broad architectural refactor.

## Progress

- [x] (2026-05-02T03:14Z) Created this ExecPlan as the follow-on to the post-semantics signed parity rebaseline.
- [x] (2026-05-02T03:39Z) Waited for `docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md` to complete with green parity and rejection matrices.
- [x] (2026-05-02T04:15Z) Waited for `docs/ExecPlans/post_semantics_preview_matrix_rebaseline_execplan.md` to complete with classified full preview matrices.
- [x] (2026-05-02T04:31Z) Reviewed the current manual cap set, including preview validation and visual signed-PDF parity.
- [x] (2026-05-02T04:31Z) Classified cap 9 as a validation defect: the preview severely cut off characters at the border but did not show red validation.
- [x] (2026-05-02T04:31Z) Recorded that the other previews behaved as expected and the actual signed PDFs looked visually acceptable, within the precision available for manual review.
- [x] (2026-05-02T04:18Z) Created `docs/ExecPlans/cap9_single_line_validation_honesty_execplan.md` as the follow-up build/layout fix plan for the cap 9 validation miss.

## Surprises & Discoveries

- Observation: the older direct annotation plan already identified manual harness sanity as the next useful step.
  Evidence: `docs/ExecPlans/direct_annotation_appearance_rendering_execplan.md` says the automated parity/rejection baselines are strong enough to support a focused human visual check.

- Observation: this manual pass should not start until the post-semantics automated rebaseline is green.
  Evidence: Issue #50 changed the semantic text and metadata path after the older parity baseline. Manual review is useful only after automated parity proves there is no broad regression.

- Observation: this manual pass should also wait for the broad preview matrix rebaseline.
  Evidence: the full preview manifests cover `3384` scenarios across baseline and stress cases and can reveal preview-only drift that the smaller signed parity suite does not exercise.

- Observation: the signed-output prerequisite is now green after refreshing stale manifest specimens.
  Evidence: `docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md` records `artifacts/signed_preview_parity_post_semantics_run2/summary.json` with `18` successful signings and `artifacts/signed_fit_rejection_post_semantics_run3/summary.json` with `3` matched intentional rejections.

- Observation: the full preview-matrix prerequisite is now classified, not perfectly green.
  Evidence: `docs/ExecPlans/post_semantics_preview_matrix_rebaseline_execplan.md` records all `3384` preview scenarios completing with zero error scenarios, while single-line matrices retain classified signable clipping/overlap diagnostics for follow-up build/layout work.

- Observation: cap 9 is a manual validation-honesty miss.
  Evidence: user manual review on 2026-05-02 reported that cap 9 should have red validation because characters were severely cut off by the border.

- Observation: the remaining manual previews and signed PDFs were visually acceptable.
  Evidence: user manual review on 2026-05-02 reported that all other previews behaved as expected and that the actual signed PDFs looked pretty good, with the caveat that the review was visual rather than a precise output-parity measurement.

## Decision Log

- Decision: keep manual harness sanity in its own ExecPlan.
  Rationale: the work is evidence review and possibly GUI-path diagnosis, not automated matrix rebaseline and not architectural extraction. A separate plan keeps the stopping condition clear.
  Date/Author: 2026-05-02 / Codex

- Decision: run only a small tracer-bullet set.
  Rationale: automated matrices already cover broad parity and rejection behavior. Manual review is expensive and subjective, so it should focus on representative cases that exercise the live Qt harness path.
  Date/Author: 2026-05-02 / Codex

- Decision: do not use this plan for Issue #49 layout extraction.
  Rationale: if manual review finds a concrete layout defect, that defect should become a targeted fix. Layout-policy extraction should wait until current build evidence is stable.
  Date/Author: 2026-05-02 / Codex

- Decision: treat cap 9 as a real validation defect, not as an acceptable manual-review limitation.
  Rationale: if preview text is visibly cut off by the border, the user needs red validation before signing. This is directly aligned with the single-line clipping/overlap diagnostics classified by the preview-matrix rebaseline.
  Date/Author: 2026-05-02 / Codex

## Outcomes & Retrospective

The manual pass found one concrete follow-up: cap 9 should fail validation because the preview visibly cuts characters off at the border. Other reviewed previews behaved as expected, and the signed PDFs looked visually aligned with the previews within the available manual-review precision.

This plan is not fully closed until the cap 9 validation miss is represented in the next build/layout fix plan. The next slice should tighten validation/fit detection for the single-line border-clipping case before declaring preview behavior fully resolved.

Follow-up is now represented by `docs/ExecPlans/cap9_single_line_validation_honesty_execplan.md`. That child plan owns the regression test and code change for rejecting cap 9-like single-line border clipping.

The child plan completed on 2026-05-02. The cap 9-like condition is now represented by `test_single_line_rendered_ink_fallback_rejects_border_flush_text`, and backend validation rejects horizontal single-line rendered text that is flush with the visible border.

## Context and Orientation

The live Qt signing harness is the path closest to user behavior. It wires together `SigningDraftWorkflow`, the Qt signing shell, preview rendering, request construction, backend signing, and artifact capture. It lives primarily in `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/signing_shell.py`.

A tracer-bullet case means one representative scenario chosen to prove a path end to end. In this plan, use three successful visible-signature cases and one intentional rejection case:

- single-line no-stamp baseline with sparse content and a comfortable rectangle;
- multi-line image-stamp case with a comfortably signable two-region layout;
- wrapped-block medium-content case from the green parity matrix;
- one known rejection case from `artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json`.

The successful cases should come from `artifacts/preview_sweep_assets/signed_preview_parity_matrix.json` after `docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md` has confirmed that matrix is still green.

## Plan of Work

First read the latest post-semantics signed-output rebaseline results and the full preview-matrix rebaseline results. If either automated signed matrix is red, or if the preview matrix battery has unclassified regressions, stop and do not run this manual pass. Manual review should not be used to explain broad automated failures.

Next choose exact scenario names from the current manifests. Prefer cases that are already comfortably signable and are not near fit thresholds. The goal is to inspect the GUI composition and final output, not to re-litigate fit boundaries.

Run the Phase 3 signing harness or, if manual interaction is needed, launch the interactive harness with an artifacts directory and use the selected settings. Capture each successful case with preview images, analysis preview images, signed output render/crop, comparison images, and harness JSON. Capture the rejection case with preview validation issues and no signed PDF.

Review artifacts manually. For successful cases, inspect whether the live preview card is visually centered and sane, whether the analysis preview matches the intended layout, whether the normalized signed crop matches the preview, and whether structured snapshots agree on text fragments, stamp presence, borders, and bounds. For the rejection case, inspect whether the failure message is clear and no signed output was written.

If a discrepancy is found, do not make speculative changes. Save the artifact bundle and classify the discrepancy. Only then create or update a fix ExecPlan.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/SignPDF/Scratch

Confirm the automated prerequisite:

    rg -n "acceptance_expectations_passed|preview_output_comparison_failure_count|successful_signing_run_count" docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md
    rg -n "scenario_count|single-line|multi-line|wrapped-block|stress|accepted|rejected|warning|failure" docs/ExecPlans/post_semantics_preview_matrix_rebaseline_execplan.md

Inspect the manifests to choose scenario names:

    .venv/bin/python -m json.tool artifacts/preview_sweep_assets/signed_preview_parity_matrix.json | rg "\"name\""
    .venv/bin/python -m json.tool artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json | rg "\"name\""

Use the existing harness commands and code paths; do not introduce a new manual runner unless the existing harness cannot capture one of the selected cases. The relevant entry points are:

    .venv/bin/python -m foliaseal phase3-signing-harness --help
    .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --help

Use an artifacts directory whose name identifies this pass, for example:

    artifacts/manual_harness_sanity_post_semantics

After capture, inspect:

    preview_image_path
    analysis_preview_image_path
    normalized_signature_crop_path
    signed_output_preview_comparison
    preview issues
    request snapshot
    backend reservation snapshot

The exact inspection method may be local image viewing or, for automated metadata, `python -m json.tool` and `rg` over the harness JSON. Do not commit generated artifact directories unless the repository already tracks the specific evidence file being updated.

## Validation and Acceptance

This plan is accepted when the signed-output rebaseline and full preview-matrix rebaseline have completed or have classified any failures, all three successful GUI cases look visually rational in the live harness, their signed PDFs match the preview closely enough that no new class of appearance defect is found, and the rejection case clearly reports validation failure without writing signed output. Acceptance must be documented with artifact paths and a short judgment for each case.

If any discrepancy is found, this plan is still useful but not complete until the discrepancy is classified as one of:

- GUI composition defect;
- artifact-analysis defect;
- real rendering defect;
- bad manual specimen.

## Idempotence and Recovery

Manual captures are safe to repeat. Use a new artifacts directory for each attempt so evidence is not overwritten. If the interactive harness cannot run because Qt bindings or display support are unavailable, record the blocker here and fall back only to already automated matrix artifacts; do not claim the manual pass is complete.

If a selected case turns out to be near a fit boundary, replace it with another green parity case and record the replacement reason. Do not change layout policy in this plan.

## Artifacts and Notes

This plan is intentionally gated by `docs/ExecPlans/post_semantics_signed_parity_rebaseline_execplan.md` and `docs/ExecPlans/post_semantics_preview_matrix_rebaseline_execplan.md`. The previous signed baseline recorded in `docs/ExecPlans/direct_annotation_appearance_rendering_execplan.md` was:

    artifacts/signed_preview_parity_matrix_run_v17/summary.json
    scenario_count = 18
    successful_signing_run_count = 18
    preview_output_comparison_failure_count = 0
    expected_outcome_mismatch_count = 0
    acceptance_expectations_passed = true

That evidence is useful context but should not substitute for the post-Issue-50 rebaseline.

## Interfaces and Dependencies

Use the existing Qt harness and signed acceptance harness in `src/foliaseal/presentation/qt/phase3_harness.py`; do not create another evidence format. The harness depends on the current architecture: `visible_signature_semantics.py` owns text/metadata semantics, `visible_signature_layout.py` owns geometry planning, `signing_preview_renderer.py` owns canonical preview rendering, `signing_shell.py` owns live Qt composition, and `phase3_signing_backend.py` owns pyHanko signing.

Revision note: Created 2026-05-02 by Codex to capture the manual GUI sanity pass as a separate, gated follow-on to automated post-semantics signed parity rebaseline.

Revision note: Updated 2026-05-02 by Codex to link the cap 9 validation-honesty child plan after the user reported severe border clipping in cap 9.

Revision note: Updated 2026-05-02 by Codex after the child plan completed the regression and validation fix for cap 9-like border clipping.
