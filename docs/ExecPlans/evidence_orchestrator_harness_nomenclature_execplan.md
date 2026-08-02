# Converge evidence orchestration and strip obsolete Phase 3 internals

This ExecPlan is a living document and must be maintained according to `.agents/skills/write-execplan/PLANS.md`. It is intentionally a complete one-slice DevLoop: implementation, compatibility cleanup, validation, compliance review, documentation reconciliation, and commit all belong to this slice. Milestones organize the work but are not stopping points.

The earlier `docs/ExecPlans/evidence_gateways_nomenclature_cleanup_execplan.md` and related gateway/composition plans are historical and superseded by this plan. They describe the pre-cleanup gateway layer and must not be used as the current acceptance target.

## Purpose / Big Picture

FoliaSeal already has an application-owned evidence boundary in `phase3_evidence_orchestrator.py`, but presentation code still adds a second layer of three near-identical lazy gateways and a separate matrix-operation wrapper. The large `phase3_harness.py` also remains the private composition root that those wrappers reach into. This makes the code harder to navigate and leaves obsolete `Phase3`/compatibility terminology in internal APIs even though the product no longer has a meaningful “Phase 3” concept.

After this slice, application callers use the existing explicit orchestrator/session verbs, presentation wiring is supplied by one neutral runner-factory module, and the duplicate `evidence_gateways.py` layer is gone. The unused tagged `Phase3EvidenceOrchestrator.run()` dispatcher and its request/result compatibility types are removed after verifying there are no live callers. Private forwarding aliases and unused interactive lazy wrappers are deleted or renamed. Existing CLI commands, persisted JSON fields, artifact paths, intentional rejection semantics, and the typed evidence-service contracts remain observable and unchanged. The result is demonstrated by the existing CLI help/smoke commands and the full test suite.

## Child ExecPlan Dependencies

No child ExecPlan is required. The slice is bounded to orchestration/composition cleanup and the first internal nomenclature migration. If compliance review finds a behavior change outside these contracts, create a child plan before broadening scope; do not add a compatibility shim silently.

## Progress

- [x] (2026-08-02) Fresh explorer-light reviewed clean HEAD `32b6516a4`; confirmed 43 focused orchestrator/service/matrix/CLI tests pass and mapped all production consumers of the duplicate gateway/dispatcher layers.
- [x] (2026-08-02) Selected the hybrid: retain explicit `Phase3EvidenceOrchestrator`/`Phase3EvidenceSession` as the application boundary, delete duplicate presentation gateways, move composition into neutral runner factories, and remove stale internal dispatcher/aliases.
- [x] (2026-08-02) Added `evidence_runner_factories.py`, moved the three lazy composition entrypoints behind neutral factories, and migrated interactive/matrix service wiring.
- [x] (2026-08-02) Deleted `evidence_gateways.py`, removed the tagged orchestrator dispatcher/types, renamed the matrix operation boundary, and removed the harness private-builder compatibility seams while preserving stable request/result/CLI contracts.
- [x] (2026-08-02) Migrated orchestrator/harness/matrix tests to explicit boundary behavior, added concrete preview/signed factory forwarding coverage, and the focused suite passes 140 tests with Ruff clean.
- [x] (2026-08-02) Two independent compliance reviews completed; stale `.run()` typing was migrated, concrete matrix factory forwarding tests were added, and the full suite passes 1044 tests with one pre-existing Pillow warning.
- [x] (2026-08-02) Architecture-steward documentation reconciliation updated README and `docs/ARCHITECTURE.md`; current-section stale gateway/dispatcher references are removed, with only historical changelog vocabulary retained.
- [x] (2026-08-02) CLI/matrix smoke validation passed: preview executed 4 scenarios and signed acceptance executed 3 offscreen scenarios, both persisted matching authoritative summary paths; temporary artifacts/processes were cleaned up.
- [x] (2026-08-02) Final cleanup audit passed (`git diff --check`, Ruff, compileall, no live stale symbols, no leftover FoliaSeal process/core/temp artifacts).
- [x] (2026-08-02) Implementation committed on `main` as `4cfe53a0f` (`Remove duplicate evidence gateways and tagged dispatcher`); a final plan-only closure commit remains to record this hash.
- [x] (2026-08-02) Complete final commit and living-plan evidence through write-git-commit; leave the working tree clean.
- [x] (2026-08-02) Final plan closure recorded in follow-up commit after implementation commit `4cfe53a0f`.

## Surprises & Discoveries

- Observation: The CLI never constructs `Phase3OperationRequest` or calls `Phase3EvidenceOrchestrator.run()`; it calls explicit verbs directly.
  Evidence: `src/foliaseal/__main__.py` handlers call capture, preview, signed acceptance, evidence, and validate methods; the fresh baseline found only orchestrator tests and documentation using the tagged dispatcher.
- Observation: `evidence_gateways.py` has one production consumer, `phase3_signed_acceptance_evidence.py`; `phase3_matrix_operations.py` is the existing dependency-light lazy matrix wrapper and can remain as the only matrix laziness seam.
  Evidence: Repository-wide import search on clean HEAD found no other production imports.
- Observation: `phase3_interactive_capture.py` owns the canonical capture DTO/runner, while `phase3_harness.py` only imports aliases and builders for composition.
  Evidence: The fresh explorer found no production caller of `build_interactive_phase3_capture_runner()` and no second live capture dataclass definition.
- Observation: Broadly renaming every persisted `Phase3*` DTO, CLI command, manifest identifier, or artifact directory in this slice would break external evidence consumers.
  Evidence: README, architecture contracts, parser tests, and matrix summaries assert those strings and paths; the migration therefore targets internal names first and records the remaining external vocabulary explicitly.

## Decision Log

- Decision: Keep `Phase3EvidenceOrchestrator` explicit methods and `Phase3EvidenceSession` as the application boundary, while deleting only the unused tagged `run()` dispatcher and its request/result wrapper types.
  Rationale: Explicit methods are the live caller contract; the dispatcher adds a second mode registry and has no production callers. Removing it strips cruft without changing CLI behavior.
  Date/Author: 2026-08-02 / Codex.
- Decision: Create `src/foliaseal/presentation/qt/evidence_runner_factories.py` for lazy interactive/preview/signed runner construction and delete `evidence_gateways.py`.
  Rationale: One neutral factory seam removes three duplicate gateway classes while keeping heavy Qt/PDF construction lazy. Concrete helper movement is limited to composition in this slice; behavior-bearing render/snapshot clusters remain in their already-tested modules until a follow-up extraction has a complete boundary.
  Date/Author: 2026-08-02 / Codex.
- Decision: Retain `phase3_matrix_operations.py` temporarily as the single lazy preview/signed callable holder, but rename its public dataclass and factory to neutral `EvidenceMatrixOperations`/`build_evidence_matrix_operations` and migrate all in-repository callers/tests.
  Rationale: It is a real dependency-light seam, unlike the deleted duplicate gateway layer. The neutral names start nomenclature cleanup without changing request/result or CLI contracts.
  Date/Author: 2026-08-02 / Codex.
- Decision: Remove private aliases and compatibility methods only when repository-wide search proves they are not external contracts; preserve persisted `Phase3` strings and application DTO field names for this slice.
  Rationale: The user requested cruft removal, but evidence files and CLI automation are compatibility surfaces. Internal aliases should disappear rather than be re-exported under another name.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The implementation removed the duplicate gateway layer and tagged dispatcher, moved lazy composition behind neutral runner factories, renamed the matrix holder and interactive factory, and preserved CLI/JSON/artifact contracts. Full validation is green at 1044 tests with one pre-existing Pillow deprecation warning; preview/signed smoke paths are green; two independent compliance reviews and architecture-steward documentation reconciliation are complete. The implementation commit is `4cfe53a0f`; this plan records the completed handoff.

## Context and Orientation

`src/foliaseal/application/phase3_evidence_service.py` owns injected runner callables and typed normalization. `src/foliaseal/application/phase3_evidence_orchestrator.py` is the application-facing boundary with explicit capture, preview, signed-acceptance, evidence, validation, and document-bound session methods. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` builds the default service. `phase3_harness.py` contains the concrete Qt/PDF composition helpers and many behavior-bearing diagnostics. `phase3_interactive_capture.py` owns the stable interactive capture result/runner contract. `phase3_matrix_operations.py` lazily holds the two matrix callables. `evidence_gateways.py` currently duplicates that laziness with three gateway classes and private imports into `phase3_harness.py`.

This plan uses “runner factory” to mean a lazy function that constructs one concrete evidence runner only when its first request arrives. It uses “compatibility cruft” to mean an internal alias, facade, tagged dispatcher, or serializer retained solely for callers that have already migrated within this repository. It does not include persisted JSON keys, CLI command names, artifact directory names, or manifest identifiers, which remain external contracts in this slice.

## Plan of Work

First add `src/foliaseal/presentation/qt/evidence_runner_factories.py`. Move the three composition entrypoints currently defined near the top of `phase3_harness.py` into neutral lazy factory functions. Keep their request adapters explicit: interactive capture forwards `Phase3HarnessCaptureRequest`, and each matrix factory forwards all five `Phase3MatrixRequest` fields to the existing runner. Keep heavy imports inside factory call paths. Where a moved composition function still needs a behavior-bearing helper from `phase3_harness.py`, inject or import that helper only inside the factory and mark it as a later extraction target; do not create a new facade or generic operation registry.

Update `phase3_interactive_capture.py` so its lazy builder uses `evidence_runner_factories.py` rather than importing a private builder from `phase3_harness.py`. Update `phase3_signed_acceptance_evidence.py` to use the neutral interactive factory and `build_evidence_matrix_operations` with explicit preview/signed factories. Delete `evidence_gateways.py` after all imports migrate. Rename the matrix holder symbols in `phase3_matrix_operations.py` to neutral names and remove the old names rather than adding aliases; update tests and docs in the same change.

In `phase3_evidence_orchestrator.py`, remove `Phase3OperationKind`, `Phase3OperationPayload`, `Phase3OperationResult`, `Phase3OperationRequest`, `run()`, and `_require_payload()` after repository-wide caller verification. Retain explicit methods, `Phase3ValidationRequest`, `Phase3EvidenceSession`, service ports, typed result DTOs, and all CLI-facing behavior. Rename only internal helper symbols whose names are not persisted; do not rename request/result classes in this slice unless tests prove they are not an external application contract.

Remove obsolete aliases in `phase3_harness.py` that exist only to re-export the canonical interactive capture types or forward to extracted modules. Keep behavior-bearing helpers until their existing dedicated tests have a replacement boundary. Move any duplicate checklist/serialization helper that is demonstrably unused into the existing reporting or capture module, delete its old alias, and record the exact deletion in the plan.

Migrate tests from factory call-count and private-builder mechanics to behavior at `Phase3EvidenceOrchestrator`, `Phase3EvidenceSession`, `Phase3EvidenceService`, `EvidenceMatrixOperations`, and the concrete runner boundaries. Add tests for lazy neutral factories, complete request forwarding, import isolation, explicit-method orchestration, and preservation of summary paths/JSON keys. Delete tests whose only purpose was to enforce the removed dispatcher/gateway aliases. Search all README/docs/architecture references and update them to neutral names, explicitly documenting which remaining `Phase3` strings are persisted compatibility contracts.

Run compliance review, documentation reconciliation, full validation, and commit without stopping after a green focused suite.

## Concrete Steps

Run commands from `/home/daekar/FoliaSeal`.

1. Confirm clean baseline and inspect all live imports before editing:

       git status --short
       rg -n "evidence_gateways|phase3_matrix_operations|Phase3Operation(Request|Kind|Payload|Result)|\.run\(" src tests README.md docs

   Record the baseline; do not reset unrelated changes.
2. Implement the neutral factory/matrix rename, orchestrator dispatcher deletion, alias cleanup, and test/doc migration with `apply_patch`. Delete obsolete files only after live imports are gone.
3. Run the focused boundary suite:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_matrix_operations.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_lifecycle.py tests/unit/test_main_cli.py tests/unit/test_phase3_harness.py

   Expect all migrated behavior tests to pass. Record the actual count in `Artifacts and Notes`.
4. Verify neutral import isolation and stale-name cleanup:

       .venv/bin/python - <<'PY'
       import json, subprocess, sys
       script = """
       import json, sys
       import foliaseal.presentation.qt.evidence_runner_factories
       import foliaseal.presentation.qt.phase3_signed_acceptance_evidence
       heavy = ("PySide6", "PIL", "pyhanko")
       print(json.dumps(sorted(name for name in sys.modules if any(name == p or name.startswith(p + ".") for p in heavy))))
       """
       completed = subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True)
       assert json.loads(completed.stdout) == []
       print("neutral evidence imports remain headless-safe")
       PY
       rg -n "evidence_gateways|Phase3OperationRequest|Phase3OperationKind|_build_preview_matrix_operation|_build_signed_acceptance_matrix_operation" src tests README.md docs/ARCHITECTURE.md

   The Python check must print the success line. The search may show only intentionally historical plan text; it must show no live import or deleted compatibility symbol.
5. Run CLI help and real smoke checks with temporary artifact roots. Preview should produce the same summary counters and `summary_json_path`; signed acceptance should preserve `timestamping_mode`, intentional rejection rows, and cleanup. Use `QT_QPA_PLATFORM=offscreen` when no display is available. Remove temporary directories and verify no FoliaSeal/Qt process or core file remains.
6. Run repository-wide validation:

       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src
       .venv/bin/python -m pytest -q
       git diff --check

   Record test counts and any pre-existing warnings; do not call the slice complete until failures are resolved or a concrete external blocker is documented.
7. After first implementation, spawn two explorer-light compliance reviewers. They must inspect `docs/ARCHITECTURE.md`, `docs/SPEC.md`, README, current ExecPlans, and the live diff. Resolve every actionable discrepancy in this plan; create and execute a child plan only if a fix cannot remain within this slice.
8. Spawn a worker-light using architecture-steward to reconcile README, `docs/ARCHITECTURE.md`, and relevant ExecPlan status. Then spawn a worker-light using write-git-commit to review/stage/commit all intended changes. Update this plan with both commit hashes and final evidence; leave `git status --short` empty.

## Validation and Acceptance

The application still exposes explicit capture, preview, signed-acceptance, evidence, and validation behavior through `Phase3EvidenceOrchestrator` and `Phase3EvidenceSession`; no CLI command or persisted evidence schema changes. Importing the neutral factories and default evidence service remains free of PySide6, Pillow, and pyHanko imports. Preview and signed matrix runs construct their concrete runners lazily, forward every request field, close their lifecycles, publish authoritative summary paths, and preserve existing result rows/counters. No live code imports the deleted gateway module or removed tagged dispatcher symbols. The residual harness may still contain behavior-bearing helpers, but its removed aliases are not reintroduced and every moved responsibility has one documented owner.

## Idempotence and Recovery

Run migrations in dependency order: add neutral factories, migrate imports/tests, then delete old modules/types. Re-running tests and smoke commands is safe when artifacts use a new temporary directory. If an intermediate edit fails, restore only the affected file from the current diff; never use destructive repository resets. If a GUI smoke run aborts because of display configuration, retry with `QT_QPA_PLATFORM=offscreen`, then clean all temporary artifacts/processes before continuing.

## Artifacts and Notes

Record baseline focused count, migrated focused count, full-suite count, lint/compile results, smoke artifact paths, compliance findings and fixes, documentation worker result, cleanup audit, and final commit hashes here during execution. Implementation commit: `4cfe53a0f`; focused rerun: 99 passed with one pre-existing Pillow deprecation warning; `git diff --check`: clean before plan closure; final tree verified clean after closure commit.

## Interfaces and Dependencies

At completion, `evidence_runner_factories.py` exposes neutral lazy factories for the three existing request/result lifecycles without a tagged dispatcher. `phase3_matrix_operations.py` exposes `EvidenceMatrixOperations` and `build_evidence_matrix_operations` as the sole dependency-light matrix lazy holder. `Phase3EvidenceOrchestrator` exposes explicit methods (`capture`, `preview_matrix`, `signed_acceptance_matrix`, `signed_acceptance_evidence`, `validate`) and `for_pdf`; it no longer exposes the unused generic `run()` registry. Qt/Pillow/pyHanko remain presentation-edge dependencies, while application tests use service, lifecycle, workspace, and artifact fakes.

## Revision Notes

2026-08-02: Initial one-slice plan created after fresh explorer review. The plan deliberately removes duplicate gateways and the unused tagged dispatcher, moves composition behind neutral factories, preserves persisted external contracts, and begins stripping internal `phase3` nomenclature without leaving compatibility aliases.
