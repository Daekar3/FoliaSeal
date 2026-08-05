# Neutralize the Evidence Harness Composition Boundary

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is one complete implementation
slice: source cleanup, tests, architecture/spec review, documentation
reconciliation, nomenclature audit, validation, and commit closure all belong
to this plan. Milestones are progress markers, not stopping points.

## Purpose / Big Picture

FoliaSeal's evidence workflow already has explicit application services and
lazy runner factories, but the concrete Qt composition module still exposes
private helpers named as if the product were in a temporary “Phase 3”. Those
names make current ownership harder to understand and preserve compatibility
branches that no live caller needs. After this slice, the private composition
surface will use neutral evidence terminology, the signed-scenario executor
will have one typed execution path, and the duplicate/dead compatibility code
will be gone. Existing user-facing commands, DTO names, serialized JSON keys,
artifact paths, and acceptance behavior remain unchanged.

The observable proof is unchanged evidence execution: the focused harness and
matrix tests pass, the release preview/signed matrices retain their established
counts and summaries, and import/lifecycle/artifact audits remain clean.

## Child ExecPlan Dependencies

- [x] The prior hybrid extraction is present: `EvidenceService` owns the
  application caller boundary, `evidence_runner_factories.py` owns lazy runner
  construction, and dedicated matrix/capture modules own their outer loops.
- [x] A fresh explorer-light review inspected the live helpers, tests,
  architecture/spec contracts, and active ExecPlans before this plan was
  written.
- [ ] No child ExecPlan is expected. If compliance review finds a discrepancy
  that cannot be corrected inside this bounded rename/cleanup, create a child
  plan before unrelated edits.

## Progress

- [x] (2026-08-04) Reviewed the live repository and acknowledged explorer
  findings before authoring this plan.
- [x] (2026-08-04) Wrote this self-contained one-slice ExecPlan.
- [x] (2026-08-04) Added red-phase coverage for normalized private composition
  names and the single signed-executor path; the initial run exposed one test
  fake still implementing only the removed `run(...)` compatibility method.
- [x] (2026-08-04) Migrated that fake to the typed `run_result(...)` contract;
  focused harness/factory/snapshot tests now pass.
- [x] (2026-08-04) Renamed the private composition/snapshotter builders,
  deleted the unused harness checklist helper, and updated repository-local
  callers/tests; intentional external `Phase3*` contracts remain unchanged.
- [x] (2026-08-04) Removed the signed executor `run_result` fallback and
  audited the duplicate analysis-engine assignment. The live file had only
  one assignment per builder, so no additional deletion was required.
- [x] (2026-08-04) Focused/affected suites and the full suite pass; release
  preview and signed matrix evidence also retain the expected bounded-corpus
  results.
- [x] (2026-08-04) Compliance review found one stale architecture entry for
  the signed executor; updated it to the typed `run_result()` entry point.
- [x] (2026-08-04) Completed compliance review and documentation
  reconciliation; source/test changes are ready for the focused commit.

## Surprises & Discoveries

- Observation: the accepted hybrid service boundary is already implemented;
  moving the behavior-heavy Qt/Pillow render cluster in this slice would be a
  speculative second extraction.
  Evidence: the explorer found lazy typed runner factories, dedicated matrix
  runners, `InteractiveCaptureEngine`, and architecture documentation that
  records `phase3_harness.py` as the concrete composition root.

- Observation: `docs/SPEC.md` contains no direct requirement for internal
  “Phase 3” names; its release-bar requirements are user-facing behavior.
  Evidence: the explorer reviewed the specification and found CLI/evidence
  stability enforced by architecture notes and tests instead.

## Decision Log

- Decision: limit this slice to private composition terminology and confirmed
  dead compatibility code; do not rename public `Phase3*` DTOs, CLI commands,
  JSON fields, artifact names, or historical filenames.
  Rationale: those are active or historical contracts with repository and
  automation consumers, while the private aliases have no supported caller.
  Date/Author: 2026-08-04 / Codex.

- Decision: keep `phase3_harness.py` as the concrete Qt composition root for
  this slice rather than moving the render/geometry cluster again.
  Rationale: the current hybrid already isolates the common caller and outer
  runners; a second large relocation would combine independent lifecycle and
  dependency risks.
  Date/Author: 2026-08-04 / Codex.

- Decision: normalize signed acceptance execution to the typed
  `run_result(...)` contract and remove the `run(...)` fallback.
  Rationale: the repository's concrete executor and tests use the typed path;
  the fallback is an obsolete compatibility probe, not a product contract.
  Date/Author: 2026-08-04 / Codex.

## Outcomes & Retrospective

The private Qt composition helpers now use neutral evidence terminology, and
the signed scenario executor has one typed `run_result()` path. The unused
checklist helper, signed `run(...)` fallback, and duplicate analysis-engine
assignment were removed or confirmed absent. Public `Phase3*` DTOs, CLI
commands, JSON keys, summary/artifact paths, matrix semantics, and lifecycle
cleanup remain unchanged by design. `phase3_harness.py` remains the concrete
Qt composition root; broader render extraction is deferred until a second
reusable consumer justifies it.

Validation completed with 135 focused evidence/service/runner/CLI tests and
1,031 full-suite tests. The release preview matrix covered 8/8 scenarios; the
signed matrix covered 8 scenarios with 6 successful signings, 2 matched
intentional fit rejections, and `acceptance_expectations_passed=true`.
Temporary preview/signed output directories were removed and no FoliaSeal
process remained. README and `docs/ARCHITECTURE.md` were reconciled to the
current ownership while retaining historical references where module or
public names are compatibility records.

## Context and Orientation

The main composition module is
`src/foliaseal/presentation/qt/phase3_harness.py`. It builds the interactive
session, Qt/headless workspace adapters, preview/signed snapshotters, and
behavior-bearing render diagnostics. The application caller is
`src/foliaseal/application/evidence_service.py`; lazy construction is in
`src/foliaseal/presentation/qt/evidence_runner_factories.py`; outer preview and
signed matrix loops are in their dedicated runner modules.

“Private composition helper” means a leading-underscore function used only by
repository-local wiring or tests. “Stable evidence contract” means a name or
shape consumed by the CLI, application service, serialized capture/summary,
artifact tooling, or a documented external workflow. Only the former may be
renamed or deleted here.

The target private names are the harness-local builder and diagnostic helpers
whose only purpose is composition: live workspace builders, signed-output and
appearance snapshotter builders, sign-time diagnostics builder, the auto-check
derivation helper, and the matrix scenario/error/summary helpers. Existing
public `Phase3HarnessCapture`, `Phase3HarnessScenarioCommand`, matrix runner
classes, CLI verbs, and serialized fields remain unchanged.

## Plan of Work

First, add focused tests in `tests/unit/test_phase3_harness.py` and
`tests/unit/test_evidence_runner_factories.py` that assert the neutral helper
names are used by the composition wiring, the typed signed executor path is
called, and the old fallback is not needed. Keep the tests outcome-oriented;
do not add new tests that depend on private aliases merely to preserve them.

Second, rename the selected private helpers in
`src/foliaseal/presentation/qt/phase3_harness.py` to neutral evidence names,
updating every repository-local call and test reference. Use names such as
`_build_live_evidence_workspace`, `_build_qt_evidence_workspace`,
`_build_signed_output_snapshotter`, `_build_appearance_snapshotter`,
`_build_sign_time_diagnostics_snapshotter`, `_derive_auto_checked_items`,
`_execute_signed_acceptance_scenario`, and neutral matrix summary helpers.
Do not rename imported modules or stable types solely because their historical
filename contains `phase3`.

Third, update `evidence_runner_factories.py` to refer only to the neutral
private composition helpers. Remove the `getattr(executor, "run_result")`
probe in the signed scenario adapter and call the normalized typed method
directly. Delete the duplicate `analysis_engine` assignment in the signed
output render snapshotter builder. Confirm with `rg` that no source/test file
still references the removed private aliases.

Fourth, update current architecture ownership text and README wording so the
live composition boundary is described as evidence/harness infrastructure,
while historical changelog and retired ExecPlan references remain historical.
Add this plan's completion evidence and explicitly record that public Phase 3
compatibility names remain at the edge by design.

Finally, run the complete focused/full validation and the release matrix
commands, clean only the named temporary output directories, verify no
FoliaSeal process remains, perform the required architecture/spec compliance
review, and commit the coherent source/test/documentation change.

## Concrete Steps

Run every command from `/home/daekar/FoliaSeal`.

1. Confirm the baseline and inventory the private names:

       git status --short --branch
       rg -n "_build_.*phase3|_derive_phase3|_execute_.*phase3|run_result|getattr\(executor|analysis_engine =" src tests

2. Add the red boundary tests, then run the focused harness/factory tests:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_evidence_runner_factories.py

3. Apply the renames and compatibility cleanup. Verify removed aliases and
   formatting:

       rg -n "_build_live_phase3|_build_qt_phase3|_build_phase3_|_derive_phase3|run_result|getattr\(executor" src tests
       .venv/bin/python -m ruff check src tests
       git diff --check

   The first search should return no live private alias or fallback references;
   historical documentation matches are allowed and must be clearly marked as
   history.

4. Run the affected evidence boundary tests:

       .venv/bin/python -m pytest -q \
         tests/unit/test_phase3_harness.py \
         tests/unit/test_evidence_runner_factories.py \
         tests/unit/test_phase3_preview_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_scenario_executor.py \
         tests/unit/test_phase3_harness_reporting.py \
         tests/unit/test_phase3_harness_capture_assembler.py \
         tests/unit/test_main_cli.py

5. Run the full suite and release evidence commands. Expect the established
   release behavior: eight preview scenarios with zero errors; eight signed
   scenarios with six successful signings, two matched intentional rejections,
   zero unexpected errors, and passing acceptance expectations.

       .venv/bin/python -m pytest -q
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-evidence-neutral-preview
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-evidence-neutral-signed

6. Clean only the two temporary directories and audit processes:

       rm -rf /tmp/foliaseal-evidence-neutral-preview /tmp/foliaseal-evidence-neutral-signed
       ps -eo pid,args | awk '/python.*foliaseal|python.*phase3/ && !/awk/ {print}'

   The process command must print nothing. Do not remove tracked artifacts or
   broad workspace paths.

7. Review `docs/ARCHITECTURE.md`, `docs/SPEC.md`, README, and this plan against
   the implementation. If a concrete mismatch remains, fix it within this
   slice and rerun the affected tests before committing.

## Validation and Acceptance

The slice is accepted when all of the following are true:

- private harness composition helpers use neutral evidence terminology;
- removed aliases, the signed `run(...)` fallback, and duplicate assignment are
  absent from live source and tests;
- public `Phase3*` evidence DTOs, CLI commands, JSON keys, artifact paths,
  matrix semantics, and lifecycle cleanup are unchanged;
- focused tests, the full pytest suite, Ruff, and `git diff --check` pass;
- preview and signed release matrices retain their established counts;
- documentation describes the current neutral ownership without rewriting
  historical records; and
- the worktree is clean after one focused commit with no FoliaSeal process or
  temporary matrix output left behind.

## Idempotence and Recovery

The changes are source renames and deletion of confirmed dead branches, so they
are safe to retry. If a test still imports an old private helper, migrate that
test to the neutral helper or an observable boundary; do not restore a dead
alias. If a matrix command fails after creating output, remove only the two
named temporary directories and rerun. If a compatibility concern appears,
restore only the documented external name at the evidence edge and record the
decision here; do not broaden the rename into public DTOs or CLI commands.

## Artifacts and Notes

Record final evidence here during execution:

       baseline commit: 640bee3fc2e47d77d6262d0c72dacf3d324652ff
       focused tests: 135 passed
       full suite: 1,031 passed
       preview matrix: 8/8 scenarios passed
       signed matrix: 8 scenarios; 6 successful signings; 2 matched intentional fit rejections; acceptance_expectations_passed=true
       removed private aliases/fallbacks: neutral private composition names; unused checklist helper; signed run(...) fallback; duplicate analysis_engine assignment absent
       documentation/compliance review: README.md, docs/ARCHITECTURE.md, and this ExecPlan reconciled; historical Phase3 module/DTO/CLI references retained where contractual
       implementation commit: pending focused commit

## Interfaces and Dependencies

No new public interface is introduced. The existing explicit application
contracts remain authoritative:

- `EvidenceService.preview_matrix(EvidenceMatrixRequest)` and
  `EvidenceService.signed_acceptance_matrix(EvidenceMatrixRequest)` return the
  existing raw summary mappings.
- `Phase3HarnessCapture` and its JSON serializer retain their fields and
  versioned evidence shape.
- `Phase3PreviewMatrixRunner` and
  `Phase3SignedAcceptanceMatrixRunner` retain their request arguments,
  per-scenario error rows, summary counters, and artifact writes.

The renamed helpers remain presentation-only and may depend on Qt/Pillow/PDF
adapters already owned by `phase3_harness.py`; they must not be imported by
application modules at import time. `evidence_runner_factories.py` continues
to lazy-load those collaborators so importing the application remains free of
optional GUI/render dependencies.

## Change-Slice Boundary

This is one primary architecture/refactor change with associated tests and
documentation/status updates. Allowed changes are private helper renames,
dead compatibility removal, focused test migration, current architecture/README
updates, this plan, and temporary matrix outputs. Forbidden changes include
renaming public Phase 3 DTOs or CLI commands, changing serialized schemas,
altering signing/layout semantics, broad render-module extraction, certificate
behavior, or unrelated GUI styling.

Revision note: created 2026-08-04 after the required explorer review. The plan
intentionally strips obsolete internal nomenclature while preserving external
evidence compatibility contracts.
