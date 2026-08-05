# Deepen the Evidence Harness Runtime Boundary

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is one complete DevLoop slice:
implementation, compatibility cleanup, internal `phase3` nomenclature
cleanup, tests, specification review, documentation reconciliation, validation,
and commit closure are all part of this plan.

## Purpose / Big Picture

The evidence workflow already exposes explicit application verbs, but the Qt
harness still leaks a large callback bundle through
`evidence_runner_factories.py` and private helpers in
`phase3_harness.py`. The preview and signed matrix runners also duplicate
summary/error projection policy. After this slice, callers will receive one
typed, lazy evidence runtime whose explicit operations hide capability wiring;
matrix diagnostics and summary projection will live behind a neutral module;
and confirmed dead compatibility paths will be removed. A developer can prove
the result by running the same CLI matrix commands and observing unchanged
summary keys, artifact paths, scenario counts, and lifecycle cleanup.

This slice intentionally preserves public historical contracts: the
`phase3-signing-*` CLI commands, `Phase3*` DTOs, JSON keys, artifact names, and
module paths remain stable at the edge. Internal capability and operation names
use neutral evidence terminology, and no compatibility alias is retained
unless a live source consumer is demonstrated.

## Child ExecPlan Dependencies

- [x] The application `EvidenceService`/`EvidenceProgram` explicit verbs and
  lazy factory architecture already exist.
- [x] A fresh DevLoop explorer reviewed the current composition, stable
  contracts, test seams, and remaining compatibility wrapper before this plan.
- [ ] No child plan is expected. A child is permitted only if compliance review
  finds a concrete defect that cannot be fixed within this runtime/projection
  slice.

## Progress

- [x] (2026-08-05) Completed the required explorer review and acknowledged its
  findings before authoring this plan.
- [x] (2026-08-05) Wrote this one-slice ExecPlan.
- [x] (2026-08-05) Added and migrated boundary tests for typed runtime
  construction, lazy heavy imports, matrix request forwarding, projection
  counter parity, and removal of the signed mapping wrapper.
- [x] (2026-08-05) Implemented the neutral runtime/projection modules and
  migrated default service/factory wiring while preserving explicit application
  verbs and artifact/lifecycle contracts.
- [x] (2026-08-05) Removed matrix projection helpers from the concrete harness
  and deleted `Phase3SignedAcceptanceScenarioExecutor.run()` after migrating
  its test-only callers to `run_result()`.
- [x] (2026-08-05) Ran focused/full validation and reconciled the release preview/signed matrix evidence.
- [x] (2026-08-05) Completed architecture/spec compliance review and documentation updates.
- [x] (2026-08-05) Created implementation commit `9a626f1ea` and plan-closure
  commit `956ae34b8`; verified a clean main worktree.

## Surprises & Discoveries

- Observation: the previous nomenclature slice removed private builder aliases
  but intentionally left the behavior-heavy harness composition root intact.
  Evidence: `phase3_harness.py` remains the concrete builder for Qt, workspace,
  snapshotter, and render-analysis callbacks.

- Observation: a generic `run(kind, payload)` registry is forbidden by the
  current architecture because `EvidenceProgram` already owns explicit verbs.
  Evidence: `docs/ARCHITECTURE.md` records the removal of the prior tagged
  dispatcher. This slice therefore uses typed explicit operations and
  operation-local capabilities, not a service locator.

- Observation: the subsequent compliance review found one unused `_LazyOperation`
  helper and stale documentation pointing at already-cleaned temporary release
  paths. Both were removed/reconciled in the closure pass; the public edge
  contracts remain unchanged.

## Decision Log

- Decision: add an internal `EvidenceHarnessRuntime` with explicit
  `capture`, `preview_matrix`, and `signed_acceptance_matrix` operations while
  leaving `EvidenceService` as the application boundary.
  Rationale: this deepens the presentation composition seam without
  resurrecting the removed public harness facade.
  Date/Author: 2026-08-05 / Codex.

- Decision: introduce typed operation-local capability bundles for runtime,
  projection, and artifact collaborators, but keep the existing Qt/Pillow/PDF
  adapters at the presentation edge.
  Rationale: the capability bundle hides callback wiring and is fakeable in
  tests without allowing optional GUI dependencies into application imports.
  Date/Author: 2026-08-05 / Codex.

- Decision: move matrix error/diagnostic/acceptance projection into a neutral
  module and delete the private harness copies after migration.
  Rationale: both matrix runners need the same policy, and these functions are
  pure enough to test through one stable boundary.
  Date/Author: 2026-08-05 / Codex.

- Decision: remove `Phase3SignedAcceptanceScenarioExecutor.run()` after
  migrating its two test-only callers to `run_result()`.
  Rationale: production composition already uses the typed result path and the
  mapping wrapper is confirmed compatibility cruft, not a documented CLI/DTO
  contract.
  Date/Author: 2026-08-05 / Codex.

## Outcomes & Retrospective

Implementation and compliance review completed 2026-08-05. The typed runtime and
pure projection modules are in place; public phase3 CLI/DTO/JSON/artifact edge
contracts remain stable while internal phase3 nomenclature, duplicate forwarding
wrappers, and deleted private projection helpers are stripped. Focused evidence
boundary validation passed 143 tests (one existing Pillow deprecation warning);
the full suite passed 1,037 tests (same warning). Release preview evidence covers
8 scenarios with 0 errors. Release signed evidence covers 8 scenarios with 6
successful signings, 2 matched intentional validation rejections, and 0 scenario
errors. Architecture and README now document runtime/projection ownership and
the intentional public-edge compatibility policy. Render-policy work remains
unchanged and deferred outside this slice.
The initial compliance review identified stale ownership references, a
protocol/documentation mismatch, and an uncovered setup-failure cleanup path;
the high-risk follow-up added cleanup regression coverage and the subsequent
compliance re-review found no remaining discrepancies.

## Context and Orientation

`src/foliaseal/application/evidence_service.py` and
`evidence_program.py` are the application-facing boundaries. They call lazy
operations built in `src/foliaseal/presentation/qt/evidence_runner_factories.py`.
Those factories currently construct matrix runners and an interactive capture
engine by passing many private functions from
`src/foliaseal/presentation/qt/phase3_harness.py`.

The new runtime module will own only composition and operation capability
bundles. `evidence_harness_projection.py` will own pure matrix result/error/
diagnostic/expectation projection. The existing matrix runners retain Qt
lifecycle, scenario iteration, artifact writes, and signed cleanup. The
existing `PreviewAnalysisEngine`, snapshotters, workspace adapters, and
`EvidenceArtifactPort` remain the concrete adapters used by the capability
bundle.

## Plan of Work

Create `src/foliaseal/presentation/qt/evidence_harness_projection.py` with
neutral typed functions or a small projector object for preview error rows,
preview diagnostic counters, signed diagnostic counters, signed expectation
evaluation, and JSON-safe summary projection. The output mappings must remain
byte/key compatible with the current matrix summaries.

Create `src/foliaseal/presentation/qt/evidence_harness_runtime.py` with typed
operation protocols and an immutable `EvidenceHarnessRuntime` containing the
three explicit operations. Its builder must lazily construct the existing
interactive/preview/signed runners and must not import Qt, Pillow, pyHanko, or
filesystem adapters at module import time.

Update `evidence_runner_factories.py` to construct the runtime and remove the
`callable()`/`hasattr(runner, "run")` compatibility branch. Factories should
return typed operations whose request object is forwarded without reconstructing
keyword dictionaries in multiple places.

Update both matrix runners to consume the neutral projector and preserve their
existing summary path authority, second serialization behavior, lifecycle
`finally` close, error rows, and intentional rejection counters. Remove the
duplicated private projection helpers from `phase3_harness.py` only after all
source and test references migrate.

Migrate tests from private summary/helper imports to the runtime/projector
boundary. Remove the two test-only calls to
`Phase3SignedAcceptanceScenarioExecutor.run()` and delete that mapping wrapper
if `rg` proves no supported consumer remains. Rename internal capability and
operation names to neutral evidence terminology; preserve public historical
`Phase3*` types, filenames, CLI commands, and serialized fields.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the clean baseline and inventory current callers:

       git status --short --branch
       rg -n "callable\(runner\)|hasattr\(runner|\.run\(\)|_preview_matrix_(error|diagnostic)|_signed_matrix_diagnostic|_evaluate_signed_matrix" src tests

2. Add red runtime/projector boundary tests and run them before implementation.
The expected red failure is an import or missing-interface error, not a changed
matrix behavior.

3. Implement the neutral modules and migrate factory/runner wiring. Run the
focused evidence boundary suite:

       .venv/bin/python -m pytest -q \
         tests/unit/test_evidence_runner_factories.py \
         tests/unit/test_phase3_preview_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_matrix_runner.py \
         tests/unit/test_phase3_signed_acceptance_scenario_executor.py \
         tests/unit/test_phase3_harness.py \
         tests/unit/test_phase3_harness_reporting.py \
         tests/unit/test_phase3_harness_capture_assembler.py \
         tests/unit/test_main_cli.py

4. Verify import isolation, stale-symbol removal, formatting, and diff hygiene:

       .venv/bin/python -c "import sys; import foliaseal.application; assert not any(name.startswith(('PySide6','PIL','pyhanko')) for name in sys.modules)"
       rg -n "callable\(runner\)|hasattr\(runner|Phase3Harness\.run|_Phase3Lazy|_preview_matrix_(error|diagnostic)|_signed_matrix_diagnostic|_evaluate_signed_matrix" src tests
       .venv/bin/ruff check src tests
       git diff --check

5. Run the complete suite and the release-fidelity matrices. Expect 8 preview
   scenarios with zero errors, and 8 signed scenarios with 6 successful
   signings, 2 matched intentional rejections, and passing expectations.

       .venv/bin/python -m pytest -q
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-runtime-preview
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-runtime-signed

6. Remove only the two temporary directories and audit processes:

       rm -rf /tmp/foliaseal-runtime-preview /tmp/foliaseal-runtime-signed
       ps -eo pid,args | awk '/python.*foliaseal|python.*phase3/ && !/awk/ {print}'

7. After implementation, have an explorer-light reviewer inspect
`docs/ARCHITECTURE.md`, `docs/SPEC.md`, README, and active evidence plans.
Fix any concrete mismatch within this slice and rerun affected tests. Have a
second high-risk reviewer check lazy imports, summary-path authority, signed
lifecycle cleanup, and artifact removal.

## Validation and Acceptance

Acceptance requires typed runtime operations with lazy construction; no
application import of Qt/Pillow/pyHanko; neutral projector boundary tests;
absence of removed compatibility branches/private projection helpers; stable
CLI/DTO/JSON/artifact behavior; full pytest/Ruff/diff-check success; the
expected 8-scenario preview and signed matrix results; no leftover processes or
temporary artifacts; reconciled architecture/README/ExecPlan documentation;
and a clean main worktree after commit.

## Idempotence and Recovery

The migration is additive until callers are switched. If a boundary test
fails, compare the new mapping with the existing golden result and fix the
projector or adapter, not the stable contract. If a matrix run fails, remove
only the named temporary directories and rerun. Do not restore a removed
compatibility branch unless a live consumer is demonstrated and documented.

## Artifacts and Notes

Record final evidence here:

       baseline commit: parent worktree baseline (see git log)
       focused tests: 143 passed, 1 warning
       full suite: 1,037 passed, 1 warning
       preview matrix: 8 scenarios, 0 errors
       signed matrix: 8 scenarios, 6 successful signings, 2 matched intentional rejections, 0 scenario errors
       removed compatibility/nomenclature: internal phase3 aliases, duplicate forwarding wrappers, private matrix projection helpers, and signed mapping wrapper
       compliance/doc review: complete; ARCHITECTURE.md and README.md reconciled 2026-08-05
       implementation commit: 9a626f1ea (Refactor evidence harness runtime and projections)
       plan-closure commit: 956ae34b8 (Close evidence harness runtime execution plan)

## Interfaces and Dependencies

The runtime is presentation-owned and application-free:

    class CaptureOperation(Protocol):
        def __call__(self, request: EvidenceCaptureRequest) -> Phase3HarnessCapture: ...

    class MatrixOperation(Protocol):
        def __call__(self, request: EvidenceMatrixRequest) -> Mapping[str, Any]: ...

    @dataclass(frozen=True)
    class EvidenceHarnessRuntime:
        capture_operation: CaptureOperation
        preview_matrix_operation: MatrixOperation
        signed_acceptance_matrix_operation: MatrixOperation

The projector is pure/in-process and accepts ordinary mappings and typed result
objects, returning stable JSON-compatible mappings. Qt/Pillow/pyHanko and
filesystem behavior remains behind injected presentation adapters and fakes.
No generic operation registry or tagged `run(kind, payload)` API is introduced.

## Change-Slice Boundary

This is one architecture/refactor change with associated tests and
documentation/status updates. Allowed changes are the runtime/capability and
projection modules, matrix/factory migration, confirmed dead compatibility and
internal nomenclature removal, focused tests, README/architecture/ExecPlan
updates, and temporary matrix outputs. Forbidden changes include changing
public CLI names, `Phase3*` DTOs, JSON/artifact schemas, signing/layout policy,
certificate behavior, or unrelated GUI styling.

Revision note: created 2026-08-05 after the required DevLoop explorer review.
