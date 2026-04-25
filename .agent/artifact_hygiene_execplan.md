# Keep Generated Artifacts Out of Day-to-Day Git Status

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agent/PLANS.md`.

## Purpose / Big Picture

The project now has strong visual evidence tooling for signature preview and signed-PDF parity, but the generated evidence has overwhelmed source control. After this change, contributors can keep durable fixtures and small curated evidence in git while running preview matrices and manual harness captures locally without thousands of PNG, PDF, and JSON outputs clogging VSCode or `git status`.

The user-visible proof is simple: after the slice is implemented, `git status --short --ignored artifacts` should no longer list generated run directories as ordinary tracked or untracked changes. Durable inputs such as fixture PDFs, stamp images, scenario manifests, and acceptance summary documents should remain available in the repository.

## Progress

- [x] (2026-04-25 02:25Z) Read `.agent/PLANS.md`, `.gitignore`, `README.md`, and the tracked artifact inventory.
- [x] (2026-04-25 02:25Z) Measured the problem: `git ls-files artifacts | wc -l` reported `142076`, and `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts | wc -l` reported `141226`.
- [x] (2026-04-25 02:25Z) Classified durable artifact inputs separately from generated run outputs.
- [x] (2026-04-25 02:26Z) Updated `.gitignore` so future generated harness and matrix outputs are ignored by default.
- [x] (2026-04-25 02:26Z) Updated `README.md` with the artifact retention policy and operator guidance.
- [x] (2026-04-25 02:27Z) Removed generated run outputs from git tracking with `git rm --cached`, leaving the files on disk for local inspection.
- [x] (2026-04-25 02:27Z) Validated that durable fixture assets remain tracked and generated outputs have zero tracked paths.

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

- Decision: Ignore and untrack generated run directories such as `artifacts/preview_sweep_runs/`, `artifacts/signed_*_matrix_run*/`, and `artifacts/phase3_harness_capture_artifacts/`.
  Rationale: These directories are outputs from harness and matrix execution. They are valuable for local diagnosis but too large and too volatile for normal source control.
  Date/Author: 2026-04-25 / Codex.

- Decision: Leave curated top-level Markdown/JSON evidence tracked for now.
  Rationale: Files such as `artifacts/phase3_fr3b_acceptance_results.md`, `artifacts/phase3_handoff_2026-04-03.md`, and `artifacts/team_assessment_2026-04-03.md` are small status/evidence documents. Removing them is a separate policy decision and should not be mixed with this generated-output cleanup.
  Date/Author: 2026-04-25 / Codex.

## Outcomes & Retrospective

Implemented the first artifact hygiene slice. Generated matrix and harness run directories are now ignored by default, the README explains the durable-input versus generated-output split, and the large generated output directories have been removed from git tracking with `git rm --cached` while remaining on disk locally. Durable fixture and manifest directories remain tracked.

The main remaining work is optional follow-up cleanup: decide whether top-level acceptance summary JSON/Markdown files should remain tracked as curated evidence or move to a separate release-evidence convention.

## Context and Orientation

The `artifacts/` directory contains two very different kinds of files. Durable inputs are files the project needs in order to reproduce tests, such as fixture PDFs, stamp images, PKCS#12 test identities, and scenario manifests. Generated outputs are files produced by running the harness or matrix tools, such as per-scenario PNG captures, signed PDFs, comparison images, debug overlays, and versioned run directories.

The important durable input locations are `artifacts/preview_sweep_assets/`, which contains preview matrix manifests and reusable stamp/PDF/certificate fixtures, and `artifacts/generated_acceptance_assets/`, which contains the clean signed-acceptance fixture PDF and signing identity.

The large generated output locations are `artifacts/preview_sweep_runs/`, `artifacts/phase3_harness_capture_artifacts/`, `artifacts/signed_acceptance_matrix_run*`, `artifacts/signed_preview_parity_matrix_run*`, and `artifacts/signed_fit_rejection_matrix_run*`. These outputs can be regenerated by running the documented harness and matrix commands.

The source control ignore rules live in `.gitignore`. The operator-facing documentation lives in `README.md`. This ExecPlan lives at `.agent/artifact_hygiene_execplan.md`.

## Plan of Work

First, update `.gitignore` to ignore generated artifact directories. The rules must be specific enough that durable fixture directories remain trackable. In particular, do not ignore all of `artifacts/`; ignore only known generated-output directories and local review scratch directories.

Second, update `README.md` with an "Artifact hygiene" section. This section must explain what belongs in git, what should stay local or in CI artifact storage, and why `.gitignore` does not hide files that were already tracked before the policy existed.

Third, remove generated output directories from git tracking with `git rm -r --cached`. The `--cached` option is essential: it removes paths from the git index without deleting the files from the working tree. This lets local evidence remain available for inspection while preventing future commits from carrying the generated files.

Fourth, validate the result. `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts` should return no paths. `git ls-files artifacts/preview_sweep_assets artifacts/generated_acceptance_assets` should still show durable inputs. `git status --short --ignored artifacts` should show generated output directories as ignored rather than normal untracked changes.

## Concrete Steps

Run all commands from the repository root:

    cd /home/daekar/SignPDF/Scratch

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

The first command should print nothing. The second command should print fixture and manifest paths. The third command should show generated directories with ignored markers (`!!`) rather than ordinary untracked markers (`??`).

## Validation and Acceptance

This slice is accepted when generated matrix and harness output directories are no longer tracked by git, durable fixture inputs remain tracked, and README explains the policy clearly enough for a contributor to decide where a new artifact belongs.

The expected observable behavior is:

- `git ls-files artifacts/preview_sweep_runs artifacts/phase3_harness_capture_artifacts 'artifacts/signed_acceptance_matrix_run*' 'artifacts/signed_preview_parity_matrix_run*' 'artifacts/signed_fit_rejection_matrix_run*' | wc -l` prints `0`.
- `git ls-files artifacts/preview_sweep_assets artifacts/generated_acceptance_assets` still prints the reusable fixtures and manifests.
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

The retained durable fixture directories are `artifacts/preview_sweep_assets/` and `artifacts/generated_acceptance_assets/`.

## Interfaces and Dependencies

This slice does not introduce runtime interfaces or third-party dependencies. It depends only on git ignore semantics:

`.gitignore` hides untracked files from ordinary status output, but it does not affect files already tracked by git. To stop tracking a generated file while leaving it on disk, use `git rm --cached`.

Revision note: created on 2026-04-25 to make generated preview and signed-output evidence manageable in source control after parity instrumentation created thousands of useful but disposable visual artifacts.

Revision note: updated on 2026-04-25 after implementation to record the ignore-rule changes, README policy, `git rm --cached` cleanup, and validation result that generated run directories now have zero tracked paths.
