# Reconcile Artifact-Dependent Test Fixtures

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows `.agents/skills/write-execplan/PLANS.md`. It is a child-quality plan for the next development-loop slice after schema model alignment slice 1.

## Purpose / Big Picture

The repository recently removed generated artifact history so a fresh clone is no longer hundreds of megabytes. The remaining test suite still contains assertions that directly read files under `artifacts/`, even though `.gitignore` now ignores the entire `artifacts/` tree and `git ls-files` shows no artifact fixtures are tracked. After this change, a developer can run the unit suite in a fresh clone without ignored local artifact files, while developers who do have the local artifact workspace still get meaningful validation that those manifests are internally coherent and aligned with the currently retained local scenario names.

This work matters because the schema model alignment work needs a trustworthy green baseline. Artifact-workspace drift should not mask real schema regressions.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/schema_model_alignment_slice1_profiles_execplan.md` is complete and committed, leaving the suite with only artifact-manifest failures in `tests/unit/test_phase3_harness.py`.
- [x] The repository-level artifact hygiene decision is in force: generated artifacts are not committed by default, and `artifacts/` remains ignored.

## Progress

- [x] (2026-05-06 10:34Z) Confirmed `.gitignore` ignores `artifacts/` and `git ls-files artifacts tests/fixtures | rg 'preview_sweep_assets|generated_acceptance'` returns no durable artifact inputs.
- [x] (2026-05-06 10:34Z) Inspected the four failing `tests/unit/test_phase3_harness.py` assertions and the local ignored manifests they read.
- [x] (2026-05-06 10:36Z) Updated artifact-dependent tests so they skip cleanly when ignored local fixtures are absent and validate current local manifest content when fixtures are present.
- [x] (2026-05-06 10:38Z) Updated stale README, architecture, and artifact hygiene documentation that still described artifact fixtures as checked in.
- [x] (2026-05-06 10:39Z) Ran focused tests, the full unit suite, and lint successfully.
- [ ] Commit the completed slice.

## Surprises & Discoveries

- Observation: The existing tests read ignored files under `artifacts/preview_sweep_assets/` and `artifacts/generated_acceptance_assets/`.
  Evidence: `git ls-files artifacts tests/fixtures | rg 'preview_sweep_assets|generated_acceptance|signed_acceptance|full_matrix_stress|full_matrix'` produced no output, while `rg -n "preview_sweep_assets|generated_acceptance_assets" tests src -g'*.py'` found direct test references.

- Observation: The local ignored signed acceptance manifest is a compact 9-scenario matrix, but one test expects older scenario names such as `single_line_top_no_stamp_sparse_large`.
  Evidence: `artifacts/preview_sweep_assets/signed_acceptance_matrix.json` currently contains scenario names such as `single_line_top_label_success`, `multi_line_bottom_medium_success`, and `wrapped_block_right_plain_reject`.

- Observation: Full-suite validation is green after making artifact fixtures optional and reconciling local manifest expectations.
  Evidence: `.venv/bin/pytest -q` reported `564 passed, 1 warning in 33.68s`; `.venv/bin/ruff check .` reported `All checks passed!`.

## Decision Log

- Decision: Do not force-add artifact files or reintroduce tracked artifact fixtures in this slice.
  Rationale: The user explicitly wants fresh laptop clones to avoid the previous large artifact download. The current `.gitignore` ignores `artifacts/`, and this slice is about restoring suite trust without reopening artifact history growth.
  Date/Author: 2026-05-06 / Codex

- Decision: Treat artifact-workspace validation as optional local QA, not mandatory unit-test input for every clone.
  Rationale: Unit tests should be reliable in the tracked repository. If local ignored fixture files exist, tests can still validate them; if they are absent, tests should report skips rather than failures.
  Date/Author: 2026-05-06 / Codex

- Decision: Keep the existing production constants in `src/foliaseal/application/qa_signed_acceptance_assets.py` unchanged.
  Rationale: Those constants remain the conventional local QA paths used by harness commands. The issue was not runtime path ownership; it was unit tests treating ignored local files as mandatory repository inputs.
  Date/Author: 2026-05-06 / Codex

## Outcomes & Retrospective

Completed the reconciliation slice. `tests/unit/test_phase3_harness.py` now gates artifact-backed manifest tests with a clear skip helper and validates the compact local stress and signed-acceptance manifests that exist in this workspace. `tests/unit/test_certification_hardening.py` now skips as a module when the ignored acceptance PDF or PKCS#12 identity is absent. README, architecture, and the older artifact hygiene ExecPlan now describe the current artifact boundary: `artifacts/` is ignored local QA workspace, and clone-stable fixtures should be promoted to `tests/fixtures/` only when explicitly needed.

The result restores a reliable validation baseline for the next schema model alignment slice: full pytest is green in this workspace, and a fresh clone without ignored artifacts should skip artifact-dependent local QA tests instead of failing with missing files.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. The Python package lives under `src/foliaseal/`, and unit tests live under `tests/unit/`. The harness tests in `tests/unit/test_phase3_harness.py` validate both pure helper behavior and optional local QA matrices. A "manifest" is a JSON file that lists signing or preview scenarios. A "fixture" is a reusable input file such as a PDF, PKCS#12 certificate, image stamp, or manifest. The path `artifacts/` is now a local workspace for generated and reusable QA materials, not a tracked source directory.

The constants in `src/foliaseal/application/qa_signed_acceptance_assets.py` still point to the conventional local artifact paths. That is acceptable for local QA commands, but tests that read those paths must not require them to exist in a fresh clone unless the files are tracked.

The failing tests observed after schema slice 1 were:

- `test_stress_preview_manifests_reference_stress_fixture_profile`
- `test_single_line_stress_manifest_includes_required_dense_field_sets`
- `test_signed_acceptance_manifest_includes_required_positive_and_negative_families`
- `test_stress_preview_manifests_preserve_expected_family_variants`

The certification hardening tests in `tests/unit/test_certification_hardening.py` also read `artifacts/generated_acceptance_assets/` and should receive the same optional-fixture treatment, even if they currently pass in this workspace because local ignored files exist.

## Plan of Work

First, add small helper functions in the relevant test modules to skip artifact-dependent tests when required local files are absent. The helper should use `pytest.skip` with a clear message that explains these files are ignored local QA fixtures.

Second, update stale manifest expectations in `tests/unit/test_phase3_harness.py` to match the compact local manifests that currently exist. For the stress manifests, validate the top-level `fixture_profile` and accept that scenario-level `appearance_overrides` may omit `fixture_profile` because the top-level manifest profile is the canonical default for the whole file. For signed acceptance, assert the current compact positive and negative scenario families and expected outcomes.

Third, update documentation that directly contradicts the current artifact hygiene state. `docs/ExecPlans/artifact_hygiene_execplan.md` currently says `artifacts/preview_sweep_assets/` and `artifacts/generated_acceptance_assets/` are tracked. Revise that completed plan with a dated revision note explaining that the current repository state now treats those directories as ignored local QA inputs. Do not rewrite historical evidence more than necessary.

Fourth, run focused tests for the changed files, then run the full unit suite and lint. If a full-suite failure remains and is unrelated to artifact fixture presence, document it before deciding whether this slice should address it.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect state:

    git status --short
    git ls-files artifacts tests/fixtures | rg 'preview_sweep_assets|generated_acceptance|signed_acceptance|full_matrix_stress|full_matrix'
    rg -n 'preview_sweep_assets|generated_acceptance_assets' tests src -g'*.py'

Validate the changed slice:

    .venv/bin/pytest -q tests/unit/test_phase3_harness.py::test_stress_preview_manifests_exist_and_parse tests/unit/test_phase3_harness.py::test_stress_preview_manifests_reference_stress_fixture_profile tests/unit/test_phase3_harness.py::test_single_line_stress_manifest_includes_required_dense_field_sets tests/unit/test_phase3_harness.py::test_signed_acceptance_manifest_includes_required_positive_and_negative_families tests/unit/test_phase3_harness.py::test_stress_preview_manifests_preserve_expected_family_variants tests/unit/test_certification_hardening.py

    Output observed on 2026-05-06:

        15 passed in 1.40s

Validate the repository:

    .venv/bin/ruff check .
    .venv/bin/pytest -q

    Output observed on 2026-05-06:

        All checks passed!
        564 passed, 1 warning in 33.68s

## Validation and Acceptance

Acceptance is met when `ruff check .` passes and the full unit suite no longer fails because ignored artifact fixtures are absent or because local artifact manifest names are stale relative to the tests. In a workspace with the ignored local artifacts present, the artifact tests should pass by validating the compact manifest contents. In a fresh clone without ignored local artifacts, the artifact-dependent tests should skip with clear messages instead of failing with `FileNotFoundError`.

## Idempotence and Recovery

The test changes are safe to run repeatedly. No generated artifact files should be staged or committed. If a local artifact file is missing during validation, the test should skip; if a local artifact file exists but is malformed, the test should fail because that indicates local QA evidence drift.

If the implementation accidentally modifies files under `artifacts/`, do not stage them. Use `git status --short --ignored artifacts` to inspect the workspace and leave ignored generated files alone.

## Artifacts and Notes

Key evidence before changes:

    .gitignore contains:
        artifacts/

    git ls-files artifacts tests/fixtures | rg 'preview_sweep_assets|generated_acceptance|signed_acceptance|full_matrix_stress|full_matrix'
        produced no output

    Local signed acceptance scenario names include:
        single_line_top_label_success
        single_line_bottom_label_success
        single_line_left_label_reject
        multi_line_top_medium_success
        multi_line_bottom_medium_success
        multi_line_right_medium_reject
        wrapped_block_left_plain_success
        wrapped_block_right_plain_reject
        wrapped_block_top_plain_success

## Interfaces and Dependencies

Use only `pytest`, `pathlib.Path`, and existing test helpers in this slice. Do not change runtime production interfaces unless validation proves the optional fixture behavior belongs in production code. The expected repository interfaces after this slice are the existing constants in `src/foliaseal/application/qa_signed_acceptance_assets.py` and optional test helper functions in the test modules.

Revision note: updated on 2026-05-06 after implementation to record the optional artifact fixture test behavior, documentation corrections, and successful validation results.
