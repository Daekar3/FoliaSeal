# Keep Generated Artifacts Out of Day-to-Day Git Status

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

The project now has strong visual evidence tooling for signature preview and signed-PDF parity, but the generated evidence has overwhelmed source control. After the original slice, contributors could keep durable fixtures and small curated evidence in git while running preview matrices and manual harness captures locally without thousands of PNG, PDF, and JSON outputs clogging VSCode or `git status`. As of the 2026-05-06 revision, the stronger current policy is that the whole `artifacts/` tree is an ignored local QA workspace; clone-stable durable fixtures should move to `tests/fixtures/` or another explicitly tracked small fixture location only when needed.

The user-visible proof is simple: after the slice is implemented, `git status --short --ignored artifacts` should no longer list generated run directories as ordinary tracked or untracked changes. In the current repository state, `git ls-files artifacts` should produce no tracked artifact inputs, and tests that use local artifact fixtures should skip when those ignored files are absent.

## Progress

- [x] (2026-04-25 02:25Z) Read `.agents/skills/write-execplan/PLANS.md`, `.gitignore`, `README.md`, and the tracked artifact inventory.
- [x] (2026-04-25 02:25Z) Measured the problem: `git ls-files artifacts | wc -l` reported `142076`, and `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts | wc -l` reported `141226`.
- [x] (2026-04-25 02:25Z) Classified durable artifact inputs separately from generated run outputs.
- [x] (2026-04-25 02:26Z) Updated `.gitignore` so future generated harness and matrix outputs are ignored by default.
- [x] (2026-04-25 02:26Z) Updated `README.md` with the artifact retention policy and operator guidance.
- [x] (2026-04-25 02:27Z) Removed generated run outputs from git tracking with `git rm --cached`, leaving the files on disk for local inspection.
- [x] (2026-04-25 02:27Z) Validated that durable fixture assets remain tracked and generated outputs have zero tracked paths.
- [x] (2026-05-06 10:34Z) Revised this plan to reflect the current post-history-rewrite state: `artifacts/` is ignored as a whole and no artifact fixture paths are tracked.

## Surprises & Discoveries

- Observation: The repository has more than 142,000 tracked paths under `artifacts/`.
  Evidence: `git ls-files artifacts | wc -l` returned `142076`.

- Observation: Almost all tracked artifact paths are generated preview sweep run outputs, not durable inputs.
  Evidence: `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts | wc -l` returned `141226`, and `du -sh artifacts/preview_sweep_runs` reported about `1.8G`.

- Observation: `.gitignore` currently ignores Python/build outputs but does not ignore generated harness or matrix run directories.
  Evidence: the current `.gitignore` only contained Python cache, virtualenv, build, and dist entries before this slice.

## Decision Log

- Decision: Keep `artifacts/preview_sweep_assets/` and `artifacts/generated_acceptance_assets/` tracked.
  Rationale: These are durable test inputs. They include fixture PDFs, test certificates, stamp images, and scenario manifests needed to reproduce automated preview and signed-output checks.
  Date/Author: 2026-04-25 / Codex.

- Decision: Supersede the earlier tracked-fixture decision and treat `artifacts/preview_sweep_assets/` and `artifacts/generated_acceptance_assets/` as ignored local QA inputs.
  Rationale: After the artifact history cleanup, fresh clones must not re-download the large artifact workspace. `git ls-files artifacts` now reports no tracked artifact paths, and artifact-backed tests must skip cleanly when local fixtures are absent.
  Date/Author: 2026-05-06 / Codex.

- Decision: Ignore and untrack generated run directories such as `artifacts/preview_sweep_runs/`, `artifacts/signed_*_matrix_run*/`, and `artifacts/phase3_harness_capture_artifacts/`.
  Rationale: These directories are outputs from harness and matrix execution. They are valuable for local diagnosis but too large and too volatile for normal source control.
  Date/Author: 2026-04-25 / Codex.

- Decision: Leave curated top-level Markdown/JSON evidence tracked for now.
  Rationale: Files such as `artifacts/phase3_fr3b_acceptance_results.md`, `artifacts/phase3_handoff_2026-04-03.md`, and `artifacts/team_assessment_2026-04-03.md` are small status/evidence documents. Removing them is a separate policy decision and should not be mixed with this generated-output cleanup.
  Date/Author: 2026-04-25 / Codex.

## Outcomes & Retrospective

Implemented the first artifact hygiene slice. Generated matrix and harness run directories are now ignored by default, the README explains the durable-input versus generated-output split, and the large generated output directories have been removed from git tracking with `git rm --cached` while remaining on disk locally. The original outcome kept durable fixture and manifest directories tracked.

Revision outcome on 2026-05-06: the current repository state supersedes that original durable-fixture outcome. The whole `artifacts/` tree is ignored, no artifact paths are tracked, and local artifact fixtures are optional QA inputs rather than unit-test requirements in a fresh clone.

The main remaining work is optional follow-up cleanup: decide whether any small artifact fixture should be promoted into `tests/fixtures/` for clone-stable automated coverage, or whether the current skip-when-absent local QA boundary remains sufficient.

## Context and Orientation

The `artifacts/` directory contains two very different kinds of files. Durable inputs are files the project needs in order to reproduce tests, such as fixture PDFs, stamp images, PKCS#12 test identities, and scenario manifests. Generated outputs are files produced by running the harness or matrix tools, such as per-scenario PNG captures, signed PDFs, comparison images, debug overlays, and versioned run directories.

The important local QA input locations are `artifacts/preview_sweep_assets/`, which contains preview matrix manifests and reusable stamp/PDF/certificate fixtures when present locally, and `artifacts/generated_acceptance_assets/`, which contains the clean signed-acceptance fixture PDF and signing identity when present locally. These paths are ignored and are not guaranteed to exist in a fresh clone.

The large generated output locations are `artifacts/preview_sweep_runs/`, `artifacts/phase3_harness_capture_artifacts/`, `artifacts/signed_acceptance_matrix_run*`, `artifacts/signed_preview_parity_matrix_run*`, and `artifacts/signed_fit_rejection_matrix_run*`. These outputs can be regenerated by running the documented harness and matrix commands.

The source control ignore rules live in `.gitignore`. The operator-facing documentation lives in `README.md`. This ExecPlan lives at `docs/ExecPlans/artifact_hygiene_execplan.md`.

## Plan of Work

First, update `.gitignore` to ignore generated artifact directories. The rules must be specific enough that durable fixture directories remain trackable. In particular, do not ignore all of `artifacts/`; ignore only known generated-output directories and local review scratch directories.

Second, update `README.md` with an "Artifact hygiene" section. This section must explain what belongs in git, what should stay local or in CI artifact storage, and why `.gitignore` does not hide files that were already tracked before the policy existed.

Third, remove generated output directories from git tracking with `git rm -r --cached`. The `--cached` option is essential: it removes paths from the git index without deleting the files from the working tree. This lets local evidence remain available for inspection while preventing future commits from carrying the generated files.

Fourth, validate the result. `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts` should return no paths. In the current 2026-05-06 state, `git ls-files artifacts/preview_sweep_assets artifacts/generated_acceptance_assets` should also return no paths because those directories are ignored local QA inputs. `git status --short --ignored artifacts` should show artifact files with ignored markers rather than ordinary untracked changes.

## Concrete Steps

Run all commands from the repository root:

    cd /home/daekar/FoliaSeal

Before editing, inspect the current scope:

    git ls-files artifacts | wc -l
    git ls-files artifacts | cut -d/ -f1-2 | sort | uniq -c | sort -nr
    du -sh artifacts/* 2>/dev/null | sort -h

After editing `.gitignore` and `README.md`, untrack generated outputs while preserving local files:

    git rm -r --cached artifacts/preview_sweep_runs
    git rm -r --cached artifacts/phase3_harness_capture_artifacts
    git rm -r --cached artifacts/signed_acceptance_matrix_run*
    git rm -r --cached artifacts/signed_preview_parity_matrix_run*
    git rm -r --cached artifacts/signed_fit_rejection_matrix_run*

If a glob matches only ignored untracked paths or no tracked paths, git may print an error for that command. That is acceptable only after verifying that the intended tracked paths are gone.

Validate the durable/generated split:

    git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts
    git ls-files artifacts/preview_sweep_assets artifacts/generated_acceptance_assets
    git status --short --ignored artifacts | sed -n '1,160p'

The first command should print nothing. In the current repository state, the second command should also print nothing because durable artifacts are no longer tracked under `artifacts/`. The third command should show local artifact files with ignored markers (`!!`) rather than ordinary untracked markers (`??`).

## Validation and Acceptance

This slice was originally accepted when generated matrix and harness output directories were no longer tracked by git, durable fixture inputs remained tracked, and README explained the policy clearly enough for a contributor to decide where a new artifact belongs. The current superseding acceptance is stricter: no `artifacts/` paths are tracked, artifact-backed tests skip when local ignored fixtures are absent, and README explains that durable clone-stable fixtures should live outside `artifacts/`.

The expected observable behavior is:

- `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts 'artifacts/signed_acceptance_matrix_run*' 'artifacts/signed_preview_parity_matrix_run*' 'artifacts/signed_fit_rejection_matrix_run*' | wc -l` prints `0`.
- `git ls-files artifacts/preview_sweep_assets artifacts/generated_acceptance_assets` prints no paths in the current policy.
- `git status --short --ignored artifacts` reports generated run directories as ignored (`!!`) rather than as thousands of ordinary changed files.

No application behavior changes are intended. The change class is repository hygiene plus documentation/status update. Generated artifacts are allowed to change only in git tracking state; fixture contents must not be modified.

## Idempotence and Recovery

The ignore-rule edits are idempotent: reapplying them should not change behavior beyond keeping generated outputs hidden. The untracking commands are also safe to repeat. If a generated directory is already untracked, `git rm --cached` may report no matching tracked path; verify with `git ls-files`.

The commands use `--cached`, so they do not delete local artifacts from disk. If a future contributor needs to restore a generated artifact to tracking for a deliberate release-evidence commit, they can use `git add -f <path>` and explain that exception in the commit message.

## Artifacts and Notes

Initial inventory evidence:

    git ls-files artifacts | wc -l
    142076

    git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts | wc -l
    141226

    du -sh artifacts/preview_sweep_runs
    1.8G artifacts/preview_sweep_runs

The former durable fixture directories were `artifacts/preview_sweep_assets/` and `artifacts/generated_acceptance_assets/`. As of 2026-05-06, those directories are local ignored QA workspaces rather than tracked durable fixture directories.

## Interfaces and Dependencies

This slice does not introduce runtime interfaces or third-party dependencies. It depends only on git ignore semantics:

`.gitignore` hides untracked files from ordinary status output, but it does not affect files already tracked by git. To stop tracking a generated file while leaving it on disk, use `git rm --cached`.

Revision note: created on 2026-04-25 to make generated preview and signed-output evidence manageable in source control after parity instrumentation created thousands of useful but disposable visual artifacts.

Revision note: updated on 2026-04-25 after implementation to record the ignore-rule changes, README policy, `git rm --cached` cleanup, and validation result that generated run directories now have zero tracked paths.

Revision note: updated on 2026-05-06 after artifact history cleanup to record that `artifacts/` is now ignored wholesale, no artifact fixture paths are tracked, and artifact-dependent tests must treat those files as optional local QA inputs.
