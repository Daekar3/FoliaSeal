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
- [ ] Identify or introduce and version a machine-readable comparison contract, then define a representative release corpus with explicit expected outcomes.
- [ ] Run canonical-preview and signed-output acceptance evidence for every corpus scenario.
- [ ] Classify every result as supported, rejected-before-signing, or a reproducible defect.
- [ ] Update README/architecture/legacy-plan status with bounded claims and commit the evidence refresh.

## Surprises & Discoveries

- Observation: a clean compact matrix does not prove the earlier large stress corpus was fixed.
  Evidence: `text_line_height_stress_evidence_refresh_execplan.md` explicitly records the different corpus sizes and forbids comparing their counts as remediation.

## Decision Log

- Decision: rebaseline before implementing any old March corrective bullet.
  Rationale: the present renderer, font assets, profile semantics, and viewer implementation have changed enough that old symptoms are not a reliable current defect specification.
  Date/Author: 2026-07-20 / Codex
- Decision: support a small bounded set of high-confidence layouts rather than treating every theoretical style combination as V1.
  Rationale: `docs/SPEC.md` explicitly prefers high-confidence appearance/layout combinations over maximum expressiveness.
  Date/Author: 2026-07-20 / Codex

## Outcomes & Retrospective

At creation, current evidence proves a compact corpus only. At completion, record the corpus version, supported scenario count, rejected scenario count, image-comparison threshold, and any defect follow-up ExecPlan.

## Context and Orientation

The canonical preview is the in-app representation shown before signing. The signed-output renderer produces a bitmap of the actual PDF after signing. Fidelity means the expected text, image, border, and placement appear consistently in both. Phase 3 is the repository’s automated preview/signed-output harness. The current manifests live under `artifacts/preview_sweep_assets/`, but those local assets are not reliable release inputs by themselves.

## Plan of Work

First identify the existing machine-readable signed-preview comparison fields and counters in `phase3_evidence_service.py`; if no stable contract exists, introduce a versioned contract that names the metric, tolerance, and critical-zero counters. Create a tracked corpus definition or deterministic generator under `tests/fixtures/` or `scripts/`, not an unversioned binary artifact. Its first version must enumerate exact supported layouts and positions: `single_line` with `top`, `bottom`, `left`, and `right`; `multi_line` with `top` and `bottom`; and `wrapped_block` with `top` and `bottom`. It must contain named empty, compact certificate-derived, long-field, custom-text, image-stamp, page-aspect, and zoom cases, each with `expected_outcome` (`signable` or intentional `rejected`) and expected diagnostic fields. Newly proposed variants require a follow-up plan rather than silently enlarging release scope. Use `phase3-signing-preview-matrix` and `phase3-signing-acceptance-matrix` with the same release manifest. All signable cases must have zero clipping, overlap, and edge-touch risks, `acceptance_expectations_passed=true`, and every `CRITICAL_ZERO_COUNTERS` value zero. Intentional validation rejections are acceptable only when their manifest expectation matches; output-comparison failures are defects, not acceptable rejections.

## Concrete Steps

From `/home/daekar/FoliaSeal`:

    .venv/bin/python scripts/generate_signed_acceptance_assets.py
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-release-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-release-signed
    .venv/bin/python -m foliaseal phase3-signing-acceptance-evidence --artifacts-root . --summary-markdown-path /tmp/foliaseal-fixed-evidence.md
    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py

Expected summaries: every scenario is accounted for; expected intentional rejections match their manifests; all signable scenarios have zero risks; the signed summary reports `acceptance_expectations_passed=true`; and all critical counters are zero.

## Validation and Acceptance

Inspect representative preview/output image pairs and the JSON summaries. A supported release scenario must show readable content and a visibly matching signed output; a risky scenario must be rejected before signing with plain-language remediation. Update the README only with the exact corpus version and result scope.

## Idempotence and Recovery

Write each run to a new `/tmp/foliaseal-release-fidelity-<timestamp>` directory. Preserve failed summaries and image pairs. Do not overwrite historical stress summaries or claim that a different corpus fixed them.

## Artifacts and Notes

Record manifest digest, scenario list, command lines, summary JSON paths, and representative image pair paths. Generated PNG/PDF files remain artifacts unless the repository’s fixture policy explicitly permits them.

## Interfaces and Dependencies

Use the existing Phase 3 CLI and `VisibleSignatureLayoutEngine`, `VisibleSignatureSemanticsService`, `signature_preview_lifecycle.py`, `phase3_signed_output_render_snapshotter.py`, and `phase3_image_comparison_helper.py`. Do not reintroduce direct backend-private layout calls into the harness.

Revision note: 2026-07-20 / Codex
Created as the evidence-refresh child of `v1_release_compliance_parent_execplan.md`; it replaces no historical plan and deliberately requires a current rebaseline before any fidelity behavior change.
