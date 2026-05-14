# Automated Signed Parity Evidence Pass

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice answers a practical question before asking the user to drive the interactive harness: how much signed-output parity evidence can FoliaSeal refresh automatically in the current workspace? After this pass, a contributor can see which source-controlled automated checks pass without user interaction, which artifact-backed matrix commands remain blocked by missing local QA fixtures, and which exact command should be run once those fixtures are restored.

This is an evidence refresh and documentation/status update. It must not change visible-signature layout behavior, signing behavior, Qt UI behavior, or persisted schemas. Generated run artifacts under `artifacts/` are allowed only if the required local fixture inputs exist; otherwise no generated artifacts should be produced.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/agent_backend_stamp_position_execplan.md` is closed for backend-test acceptance and explicitly defers user-facing harness or signed-output proof to a later pass.
- [x] The current repository contains automated tests for CLI dispatch, preview/request parity, backend signing/layout, Phase 3 harness evidence contracts, and signed-output comparison helpers.
- [ ] Local artifact fixtures are present for artifact-backed matrix commands: `artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf`, `artifacts/generated_acceptance_assets/signed_acceptance_identity.p12`, `artifacts/preview_sweep_assets/signed_preview_parity_matrix.json`, `artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json`, and `artifacts/preview_sweep_assets/signed_acceptance_matrix.json`.

## Progress

- [x] (2026-05-14T01:25Z) Started the dev-loop automated parity evidence pass after confirming the user wants automated validation before manual harness involvement.
- [x] (2026-05-14T01:27Z) Spawned an explorer to identify unblocked automated checks and artifact-backed blockers.
- [x] (2026-05-14T01:30Z) Confirmed this workspace has no files under `artifacts/`, so signed-output matrix commands cannot run yet.
- [x] (2026-05-14T01:34Z) Created this ExecPlan to record the evidence pass and keep it separate from behavior changes.
- [x] (2026-05-14T01:40Z) Ran the source-controlled automated parity and harness test set successfully.
- [x] (2026-05-14T01:41Z) Checked the required signed-acceptance fixture paths and confirmed they are absent.
- [x] (2026-05-14T01:42Z) Ran the signed acceptance matrix command far enough to capture the missing-fixture failure.
- [x] (2026-05-14T01:43Z) Updated this ExecPlan with validation transcripts and blocker status.

## Surprises & Discoveries

- Observation: the current workspace has no local artifact files.
  Evidence: `find artifacts -maxdepth 4 -type f` returned no output. The signed acceptance matrix documented in README requires inputs under both `artifacts/generated_acceptance_assets/` and `artifacts/preview_sweep_assets/`.

- Observation: the useful unblocked evidence is test-based, not matrix-run based.
  Evidence: the repository has source-controlled unit/integration-style tests for preview/request parity, signed-output comparison snapshots, evidence-contract enforcement, CLI dispatch, backend signing/layout, and optional artifact manifests. The real matrix commands still read ignored local QA fixture files.

## Decision Log

- Decision: run source-controlled automated tests first and record matrix commands as blocked if fixture files are absent.
  Rationale: the user asked whether manual harness involvement was needed. The safest answer is to exhaust automated checks that do not need user interaction, while being explicit that source-controlled tests are not a substitute for artifact-backed signed-output matrices.
  Date/Author: 2026-05-14 / Codex

- Decision: do not regenerate or synthesize acceptance fixtures in this slice.
  Rationale: signed-output acceptance is evidence-sensitive. Using ad hoc regenerated PDFs, certificates, or manifests would produce a different corpus from the documented baseline and could make parity counts misleading. Fixture regeneration should be a separate, explicit ExecPlan if needed.
  Date/Author: 2026-05-14 / Codex

## Outcomes & Retrospective

This evidence pass is complete. The automated source-controlled evidence pass completed successfully: CLI parser and dispatch tests, preview/request parity tests, backend signing/layout tests, Phase 3 harness/evidence tests, and artifact-gated certification tests reported `255 passed, 23 skipped, 1 warning`.

The artifact-backed signed acceptance matrix did not run because the required local QA fixture `artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf` is absent. No signed PDFs, renders, crops, comparison images, or matrix summaries were produced by this pass.

## Context and Orientation

FoliaSeal’s signed-output parity promise means that a visible signature shown in preview should match the visible signature written into the signed PDF closely enough for a user to trust the preview. The automated evidence stack has two layers.

The first layer is source-controlled tests. These tests synthesize their own temporary PDFs, certificates, captures, and snapshots where practical. They cover CLI parsing and dispatch in `tests/unit/test_cli_parser.py` and `tests/unit/test_main_cli.py`, preview/request and appearance-layer parity in `tests/unit/test_signing_preview_renderer.py`, backend signing and visible-signature layout in `tests/unit/test_phase3_signing_backend.py`, and Phase 3 harness evidence contracts plus signed-output comparison helpers in `tests/unit/test_phase3_harness.py`. `tests/unit/test_certification_hardening.py` contains artifact-gated checks that skip cleanly when the ignored acceptance assets are absent.

The second layer is artifact-backed matrix execution through `python -m foliaseal phase3-signing-acceptance-matrix`. That command is implemented by `src/foliaseal/__main__.py` and `src/foliaseal/presentation/qt/phase3_harness.py::run_phase3_signed_acceptance_matrix()`. It signs each manifest scenario, writes signed PDFs, signed page renders, signed annotation crops, preview-vs-signed-output comparison images, cryptographic verification details, and a `summary.json`. This layer is closer to user-facing proof, but it requires ignored local QA fixtures under `artifacts/`.

## Plan of Work

First, run the unblocked automated evidence set with `QT_QPA_PLATFORM=offscreen` so Qt-backed rendering code can run headlessly. Record the exact pass/skip count in this plan. If a source-controlled test fails, stop and fix the failure in a separate behavior-fix plan rather than mixing fixes into this evidence pass.

Second, attempt the representative signed acceptance matrix command documented in README only far enough to verify the artifact blocker. If it fails because the source PDF or certificate path is missing, record that as the expected blocked outcome. Do not create substitute fixtures in this slice.

Third, update this ExecPlan with the validation transcript, then commit the plan. If generated matrix artifacts are not produced, state that clearly. If the fixtures unexpectedly exist and the matrix runs, inspect the `summary.json` and record `acceptance_expectations_passed`, `preview_output_comparison_failure_count`, `expected_outcome_mismatch_count`, and cryptographic validation failure counts.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Run the unblocked automated evidence set:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q \
      tests/unit/test_cli_parser.py \
      tests/unit/test_main_cli.py \
      tests/unit/test_signing_preview_renderer.py \
      tests/unit/test_phase3_signing_backend.py \
      tests/unit/test_phase3_harness.py \
      tests/unit/test_certification_hardening.py

Check whether the matrix fixtures exist:

    test -f artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf
    test -f artifacts/generated_acceptance_assets/signed_acceptance_identity.p12
    test -f artifacts/preview_sweep_assets/signed_acceptance_matrix.json

If those files exist, run:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix \
      --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf \
      --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 \
      --passphrase secret \
      --scenario-manifest-path artifacts/preview_sweep_assets/signed_acceptance_matrix.json \
      --artifacts-dir artifacts/signed_acceptance_matrix_run_automated_parity

If the fixture checks fail, record the missing path and do not run the matrix with substitutes.

## Validation and Acceptance

This evidence pass is accepted when the source-controlled automated test set has been run and recorded, and the artifact-backed matrix status is either recorded as passed with summary counts or blocked with exact missing fixture paths. Passing tests mean the code-level and harness-helper parity contracts are still intact. They do not, by themselves, prove fresh user-facing signed-output parity across the ignored local matrix corpus.

## Idempotence and Recovery

The test command is safe to rerun. The artifact-backed matrix command writes only under `artifacts/`, which is ignored by git. If a matrix run partially writes output and fails, rerun into a fresh suffixed directory rather than committing generated PDFs or PNGs.

Do not commit generated signed PDFs, rendered pages, crops, comparison images, or full matrix summaries from `artifacts/` in this slice. Commit only this concise evidence/status plan unless a separate review explicitly promotes a small curated summary.

## Artifacts and Notes

Automated parity and harness test set:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_cli_parser.py tests/unit/test_main_cli.py tests/unit/test_signing_preview_renderer.py tests/unit/test_phase3_signing_backend.py tests/unit/test_phase3_harness.py tests/unit/test_certification_hardening.py
    255 passed, 23 skipped, 1 warning in 186.90s (0:03:06)

Fixture checks:

    test -f artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf
    <exit code 1>

    test -f artifacts/generated_acceptance_assets/signed_acceptance_identity.p12
    <exit code 1>

    test -f artifacts/preview_sweep_assets/signed_acceptance_matrix.json
    <exit code 1>

Signed acceptance matrix attempt:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path artifacts/preview_sweep_assets/signed_acceptance_matrix.json --artifacts-dir artifacts/signed_acceptance_matrix_run_automated_parity
    FileNotFoundError: PDF does not exist: artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf

No generated artifacts were produced by the failed matrix attempt.

## Interfaces and Dependencies

Use the existing CLI commands and tests only. The relevant command entry points are `src/foliaseal/__main__.py` for argument parsing and dispatch, and `src/foliaseal/presentation/qt/phase3_harness.py::run_phase3_signed_acceptance_matrix()` for signed-output matrix execution. The conventional fixture paths are defined in `src/foliaseal/application/qa_signed_acceptance_assets.py`.

Revision note: Created 2026-05-14 by Codex to run the automated parity evidence pass before asking the user to perform manual harness review.

Revision note: Updated 2026-05-14 by Codex after running the source-controlled automated evidence set and confirming the signed acceptance matrix remains blocked by missing local fixture assets.
