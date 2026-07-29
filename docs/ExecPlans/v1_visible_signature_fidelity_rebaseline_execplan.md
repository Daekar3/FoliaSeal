# Rebaseline release-grade visible-signature fidelity evidence

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this evidence-refresh slice, FoliaSeal has a maintained, representative fidelity corpus showing which visible-signature layouts are safe to present as WYSIWYG (what you see is what you get). A release reviewer can distinguish current supported combinations from old, non-comparable stress findings instead of treating either as a blanket product claim.

## Child ExecPlan Dependencies

- [x] Current compact nine-scenario stress manifests ran clean on 2026-07-19.
- [x] This child has no further child ExecPlans.

## Progress

- [x] (2026-07-20) Identified that the March output-analysis plan has unresolved historical bullets while the July compact corpus is clean but explicitly non-comparable.
- [x] (2026-07-28) Explorer review confirmed the Phase 3 counters exist but manifests are loose/unversioned and the tracked `tests/fixtures/phase3/release_fidelity_manifest.json` is missing.
- [x] (2026-07-29) Added `phase3_fidelity_v1`, manifest version 1, zero-tolerance comparison fields, and the tracked eight-scenario corpus at `tests/fixtures/phase3/release_fidelity_manifest.json`.
- [x] (2026-07-29) Ran canonical preview evidence (`/tmp/foliaseal-release-preview-final`) and signed-output evidence (`/tmp/foliaseal-release-signed-final`) for all eight scenarios.
- [x] (2026-07-29) Classified six scenarios as supported and two as intentional pre-signing fit rejections; no reproducible defect remains in the release corpus.
- [x] (2026-07-29) Initial compliance review found stale README/architecture scope text and an incomplete validator requirement; those were corrected by documenting the bounded claim and requiring every scenario to declare `expected_outcome` plus diagnostics.
- [x] (2026-07-29) Documentation review reconciled README, architecture, SPEC, and legacy stress/output-analysis plans; the bounded claim and historical non-comparability are explicit.

## Surprises & Discoveries

- Observation: a clean compact matrix does not prove the earlier large stress corpus was fixed.
  Evidence: `text_line_height_stress_evidence_refresh_execplan.md` explicitly records the different corpus sizes and forbids comparing their counts as remediation.
- Observation: existing generated acceptance manifests are artifact-rooted and cannot serve as release inputs without a tracked contract.
  Evidence: current local manifests are under `artifacts/preview_sweep_assets/`; the planned `tests/fixtures/phase3/release_fidelity_manifest.json` does not exist.
- Observation: the first release-corpus run without signature rectangles produced no signable requests; adding one explicit safe page rectangle per scenario enabled the intended six signings and two fit rejections.
  Evidence: preview summary initially reported `signature_rect_missing`; the final rerun at `/tmp/foliaseal-release-signed-final/summary.json` reports `acceptance_expectations_passed=true`.
- Observation: the two intentionally rejected layouts fail with the same user-actionable fit message, while every signable layout has zero critical failures.
  Evidence: `single_line_left_long_fields` and `wrapped_block_bottom_custom_text` report “does not fit inside the selected rectangle”; signed counters are all zero in `/tmp/foliaseal-release-signed-final/summary.json`.
- Observation: compliance review found the release claim was not yet visible in README/architecture and the validator accepted a scenario missing `expected_outcome`.
  Evidence: independent review of the first pass; both issues are now corrected and covered by `tests/unit/test_phase3_fidelity_contract.py`.
- Observation: tightening the validator initially exposed a test fixture that omitted `expected_outcome`; the test was corrected and the contract suite now passes six tests.
  Evidence: first post-review run had two fixture failures; rerun reports `6 passed`.
- Observation: enabling the generated QA assets surfaced four certification-policy test failures because their broad field-name appearance no longer fit the regenerated identity subject inside the fixed test rectangle.
  Evidence: the certification matrix returned `PDF_SIGNING_FAILED` with the visible-fit diagnostic before policy assertions ran; the test now uses a compact appearance, keeping this policy test independent from layout stress, and the focused file passes `10 passed`.

## Decision Log

- Decision: rebaseline before implementing any old March corrective bullet.
  Rationale: the present renderer, font assets, profile semantics, and viewer implementation have changed enough that old symptoms are not a reliable current defect specification.
  Date/Author: 2026-07-20 / Codex
- Decision: support a small bounded set of high-confidence layouts rather than treating every theoretical style combination as V1.
  Rationale: `docs/SPEC.md` explicitly prefers high-confidence appearance/layout combinations over maximum expressiveness.
  Date/Author: 2026-07-20 / Codex
- Decision: version the release manifest with `manifest_version: 1` and a `phase3_fidelity_v1` comparison contract while preserving the existing `success`/`validation_rejection` outcome vocabulary.
  Rationale: the existing matrix runners already enforce critical zero counters; a versioned wrapper makes tolerances, expected diagnostics, and corpus scope reviewable without changing their stable seams.
  Date/Author: 2026-07-28 / Codex

## Outcomes & Retrospective

The release corpus is `tests/fixtures/phase3/release_fidelity_manifest.json` (SHA-256 `4dd4545c94398411268589666caf06ee7cdceb3a79f03aeac6591008b5e1085e`), manifest version 1, using comparison contract `phase3_fidelity_v1` with zero preview/output tolerance. It contains eight scenarios: six supported signings and two intentional pre-signing fit rejections. The signed summary at `/tmp/foliaseal-release-signed-final/summary.json` reports `acceptance_expectations_passed=true`, six successful signings, two matched intentional rejections, and zero expected-outcome, cryptographic, preview/output, or annotation-rectangle failures. No defect follow-up ExecPlan is required for this bounded release claim.

## Context and Orientation

The canonical preview is the in-app representation shown before signing. The signed-output renderer produces a bitmap of the actual PDF after signing. Fidelity means the expected text, image, border, and placement appear consistently in both. Phase 3 is the repository’s automated preview/signed-output harness. The current manifests live under `artifacts/preview_sweep_assets/`, but those local assets are not reliable release inputs by themselves.

## Plan of Work

First identify the existing machine-readable signed-preview comparison fields and counters in `phase3_evidence_service.py`; if no stable contract exists, introduce a versioned contract that names the metric, tolerance, and critical-zero counters. Create a tracked corpus definition or deterministic generator under `tests/fixtures/` or `scripts/`, not an unversioned binary artifact. Its first version must enumerate exact supported layouts and positions: `single_line` with `top`, `bottom`, `left`, and `right`; `multi_line` with `top` and `bottom`; and `wrapped_block` with `top` and `bottom`. It must contain named empty, compact certificate-derived, long-field, custom-text, image-stamp, page-aspect, and zoom cases, each with `expected_outcome` (`success` or intentional `validation_rejection`) and expected diagnostic fields. Newly proposed variants require a follow-up plan rather than silently enlarging release scope. Use `phase3-signing-preview-matrix` and `phase3-signing-acceptance-matrix` with the same release manifest. All successful cases must have zero clipping, overlap, and edge-touch risks, `acceptance_expectations_passed=true`, and every `CRITICAL_ZERO_COUNTERS` value zero. Intentional validation rejections are acceptable only when their manifest expectation matches; output-comparison failures are defects, not acceptable rejections.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    .venv/bin/python scripts/generate_signed_acceptance_assets.py
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-release-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-release-signed
    .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence --artifacts-root . --summary-markdown-path /tmp/foliaseal-fixed-evidence.md
    .venv/bin/python -m pytest -q tests/unit/test_phase3_fidelity_contract.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/python -m pytest -q

Expected summaries: every scenario is accounted for; six supported signings and two intentional fit rejections match their manifest outcomes; all signable scenarios have zero risks; the signed summary reports `acceptance_expectations_passed=true`; all critical counters are zero; and the full repository suite is green.

## Validation and Acceptance

Inspect representative preview/output image pairs and the JSON summaries. A supported release scenario must show readable content and a visibly matching signed output; a risky scenario must be rejected before signing with plain-language remediation. Update the README only with the exact corpus version and result scope.

## Idempotence and Recovery

Write each run to a new `/tmp/foliaseal-release-fidelity-<timestamp>` directory. Preserve failed summaries and image pairs. Do not overwrite historical stress summaries or claim that a different corpus fixed them.

## Artifacts and Notes

Record manifest digest, scenario list, command lines, summary JSON paths, and representative image pair paths. The release manifest is tracked; generated PNG/PDF files remain in `/tmp` unless the repository’s fixture policy explicitly permits them. Current evidence is `/tmp/foliaseal-release-preview-final/summary.json`, `/tmp/foliaseal-release-signed-final/summary.json`, and representative comparison `/tmp/foliaseal-release-signed-final/single_line_bottom_compact_certificate_signed_output_compare.png`.

## Interfaces and Dependencies

Use the existing Phase 3 CLI and `VisibleSignatureLayoutEngine`, `VisibleSignatureSemanticsService`, `signature_preview_lifecycle.py`, `phase3_signed_output_render_snapshotter.py`, and `phase3_image_comparison_helper.py`. Do not reintroduce direct backend-private layout calls into the harness.

Revision note: 2026-07-29 / Codex
Added the versioned release-fidelity contract, tracked eight-scenario corpus, matrix evidence, and bounded supported/rejected classification; no historical stress plan was rewritten. Final post-review evidence is under `/tmp/foliaseal-release-preview-final` and `/tmp/foliaseal-release-signed-final`.

Revision note: 2026-07-29 / Codex
Documentation reconciliation completed. README and architecture now name the manifest contract and scope; legacy stress/output-analysis records remain historical and are not presented as remediated by this corpus.

Revision note: 2026-07-29 / Codex
Full-suite validation initially exposed four certification-policy failures caused by generated-identity subject width, not certification behavior. The policy test fixture now uses a compact appearance and the full suite passes `979 passed` with one pre-existing Pillow deprecation warning.
