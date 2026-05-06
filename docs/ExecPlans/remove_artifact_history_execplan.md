# Remove committed artifact history from the repository

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

## Purpose / Big Picture

The repository currently contains thousands of generated artifact files in Git history, which makes the clone and pack size much larger than it should be. After this change, the repository history will no longer include the committed artifact directories and temporary binary outputs, so future clones and fetches will be smaller and easier to work with.

## Child ExecPlan Dependencies

- [ ] None. This task is self-contained and does not depend on a separate child plan.

## Progress

- [x] (2026-05-05 00:00Z) Inspected the current repository history and confirmed that `artifacts/` and `tmp_inspect/` contain the large generated files.
- [x] (2026-05-05 00:00Z) Rewrote history to remove the committed artifact and temporary output paths.
- [x] (2026-05-05 00:00Z) Verified that the rewritten history no longer contains those paths and that the pack size dropped materially.
- [x] (2026-05-05 00:00Z) Updated the working tree docs to record the rewrite approach and recovery notes.
- [x] (2026-05-05 00:00Z) Recorded the result and recovery notes.

## Surprises & Discoveries

- Observation: the pack is dominated by generated preview run summaries under `artifacts/preview_sweep_runs/`, with individual blobs around 18 MB each.
  Evidence: `git rev-list --objects --all | git cat-file --batch-check` showed many `summary.json` blobs in the multi-megabyte range.
- Observation: `git filter-repo` is not installed in this environment, so the rewrite had to use `git filter-branch` instead.
  Evidence: `git filter-repo --help` failed, and the fallback rewrite completed successfully with `git filter-branch`.
- Observation: pruning the rewritten history reduced the repository pack from about 600.63 MiB to 5.31 MiB.
  Evidence: `git count-objects -vH` before and after the rewrite.

## Decision Log

- Decision: remove the entire committed `artifacts/` tree and `tmp_inspect/` tree from history rather than trying to keep a hand-curated subset.
  Rationale: the tracked files are overwhelmingly generated evidence and temporary outputs, and the simplest safe way to shrink history is to strip the complete generated-output directories.
  Date/Author: 2026-05-05 / Codex
- Decision: use `git filter-branch` as the rewrite mechanism because `git filter-repo` was unavailable in the environment.
  Rationale: the repo still needed a working history rewrite, and the built-in Git command was the available fallback.
  Date/Author: 2026-05-05 / Codex

## Outcomes & Retrospective

The repository history now excludes every reachable `artifacts/` and `tmp_inspect/` path, and the pack size dropped from roughly 600 MiB to 5.31 MiB. The rewrite path was less ideal than `git filter-repo`, but the fallback was sufficient once the backup refs were pruned and garbage collection ran.

## Context and Orientation

The repository root is `/home/daekar/FoliaSeal`. The large files currently live under `artifacts/`, especially `artifacts/preview_sweep_runs/`, `artifacts/preview_sweep_assets/`, `artifacts/generated_acceptance_assets/`, and a small `tmp_inspect/` directory. The source code, tests, and documentation remain in `src/`, `tests/`, and `docs/`.

In this plan, “history rewrite” means changing the Git commits themselves so the unwanted paths no longer exist in any commit reachable from the rewritten branch tip. This is different from deleting files in the current checkout, because the goal is to remove them from old commits too.

## Plan of Work

First, create a safety reference to the current branch tip so the pre-rewrite state can be recovered locally if needed. Then use `git filter-repo` from the repository root to delete `artifacts/` and `tmp_inspect/` from all reachable history. After the rewrite, inspect the new history and object database to confirm the large artifact paths are gone and the pack size has dropped. Finally, update this plan with the observed results and note that the remote branch will need a force push if the rewritten history is published.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create a recovery branch pointing at the current tip.

   Expected result:

       git branch backup/pre-artifact-rewrite

2. Rewrite history to remove the generated directories.

   Command:

       git filter-repo --force --path artifacts --path tmp_inspect --invert-paths

3. Verify the rewritten history.

   Commands:

       git log --oneline --decorate -n 5
       git rev-list --objects --all | rg '^(artifacts/|tmp_inspect/)'
       git count-objects -vH

   Expected result:

       no output from the path search
       a materially smaller `size-pack` than before the rewrite

## Validation and Acceptance

Acceptance is met when the rewritten repository no longer contains any `artifacts/` or `tmp_inspect/` paths in any reachable commit, and the pack size is substantially smaller than the pre-rewrite 600 MiB pack. The current checkout should still build and test normally for the remaining source files.

## Idempotence and Recovery

The rewrite itself is not idempotent, so the safety branch is important. If the rewrite must be repeated, start again from `backup/pre-artifact-rewrite`. If the result is unsatisfactory, reset the working branch to that backup branch locally and rerun the filter with the same path list.

## Artifacts and Notes

Before the rewrite, the history inspection showed very large blobs like:

    18449472 artifacts/preview_sweep_runs/single_line_full_matrix_stress_headless_v1/summary.json
    17359927 artifacts/preview_sweep_runs/single_line_full_matrix_stress/summary.json

## Interfaces and Dependencies

No code interfaces change. The only required tool is `git filter-repo`, which is already available in this environment.
