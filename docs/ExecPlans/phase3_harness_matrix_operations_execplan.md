# Replace the redundant Phase 3 presentation composition with typed matrix operations

This ExecPlan is a living document and must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. It defines one complete implementation slice after commits `06697aec0` and `c682a72bf`.

## Purpose / Big Picture

FoliaSeal already has a canonical application boundary for Phase 3 evidence in `Phase3EvidenceService` and `Phase3EvidenceOrchestrator`. The remaining presentation layer still carries a redundant three-verb composition (`Phase3Composition` plus `Phase3Harness`) and two specialized lazy wrappers inside the 3,899-line `phase3_harness.py`. That shape makes a headless matrix caller depend conceptually on an interactive capture composition and forces tests to patch private builder names.

After this slice, the application service will receive two explicit typed matrix operations from a focused `phase3_matrix_operations.py` module: preview and signed acceptance. Interactive capture will be installed separately and lazily through an explicit capture factory. The old composition/facade classes, specialized lazy wrappers, and obsolete forwarding-only compatibility seams will be removed once their callers and tests migrate. The CLI commands, application request DTOs, raw matrix summaries, capture JSON, checklist/report files, artifact paths, lifecycle cleanup, and intentional rejection semantics will remain unchanged.

The user-visible proof is unchanged commands with a cleaner execution path: preview-only service construction does not create the interactive Qt capture runner, while the signed matrix and interactive capture still produce the same summary artifacts and evidence fields.

## Child ExecPlan Dependencies

- [x] The application-level `Phase3EvidenceService`/`Phase3EvidenceOrchestrator` boundary and request DTOs are present and remain the caller contract.
- [x] The headless-first composition and pure signed-PDF snapshotter slices are complete at commits `0a86d5eaf`, `06697aec0`, and `c682a72bf`.
- [x] A fresh explorer-light review inspected live callers, stable contracts, safe relocation targets, and extraction risks before this plan was written.
- [x] No child ExecPlan is required initially; this is one presentation-composition migration with source, tests, documentation, compliance review, cleanup, and commit work in one slice. A child plan may be created only if the required compliance review finds a concrete discrepancy.

## Progress

- [x] (2026-08-01) Selected the recommended hybrid: typed preview/signed matrix operations plus an explicit lazy interactive capture factory, while retaining the application service as the canonical boundary.
- [x] (2026-08-01) Completed the required fresh explorer review. Confirmed that production wiring enters through `phase3_signed_acceptance_evidence.py`; `Phase3Composition` and `Phase3Harness` are otherwise internal/test seams.
- [x] (2026-08-01) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-08-01) Created `phase3_matrix_operations.py` with typed operation holders and lazy factories; preserved exact `Phase3MatrixRequest` forwarding and raw summary mappings.
- [x] (2026-08-01) Updated default evidence-service wiring to inject matrix operations directly and construct interactive capture only through an explicit lazy factory.
- [x] (2026-08-01) Removed `Phase3Composition`, `Phase3Harness`, `_Phase3LazyMatrixOperation`, `_Phase3LazyCaptureOperation`, and their obsolete protocols from the production module.
- [x] (2026-08-01) Replaced composition-forwarding tests with operation routing, lazy-construction, import-isolation, capture-installation, and raw-summary boundary tests; the corrected focused set passes (`107 passed`, one pre-existing Pillow warning).
- [x] (2026-08-01) `ruff check src tests` and `git diff --check` pass after adding lazy Qt-package exports so focused submodule imports remain dependency-light.
- [x] (2026-08-01) Affected evidence, matrix, reporting, service, orchestrator, QA-evidence, and CLI tests pass (`144 passed`, one pre-existing Pillow warning).
- [x] (2026-08-01) Full suite passes (`1038 passed`, one pre-existing Pillow warning); Ruff and diff checks pass. Preview matrix reports 8/8 successful with zero errors; signed matrix reports 8 scenarios, 6 successful signings, 2 matched intentional rejections, zero unexpected errors, and passing acceptance expectations. Temporary artifacts and processes were cleaned up; stale production/test symbols are absent.
- [x] (2026-08-01) Initial compliance review passed stable contracts; high-risk review found eager optional-dependency imports and an unused lifecycle comment, so child plan `phase3_harness_matrix_operations_import_isolation_followup_execplan.md` was created and implemented.
- [x] (2026-08-01) Completed the required second compliance/high-risk review after the child follow-up; no remaining discrepancies were found in import isolation, lifecycle cleanup, raw summary parity, or artifact handling.
- [x] (2026-08-01) Reconciled README, `docs/ARCHITECTURE.md`, and the active child ExecPlan through an architecture-steward documentation review; historical changelog entries remain explicitly historical.
- [ ] Create the focused main-branch commit with write-git-commit and verify a clean checkout.

## Surprises & Discoveries

- Observation: The application layer already owns tagged operation dispatch, so a second generic tagged dispatcher at the Qt boundary would duplicate an existing contract.
  Evidence: `src/foliaseal/application/phase3_evidence_orchestrator.py` dispatches typed `Phase3OperationRequest` values, while `Phase3EvidenceService` expects independent capture and matrix ports.
- Observation: `Phase3Composition` and `Phase3Harness` have no production callers beyond default service wiring; direct references are concentrated in `tests/unit/test_phase3_harness.py`, README, and architecture/history documents.
  Evidence: fresh explorer search on the clean `main` tree found the only production construction in `phase3_signed_acceptance_evidence.py`.
- Observation: Moving the entire remaining preview/render helper tail in the same slice would cross dynamic Qt, PIL, temporary-artifact, and snapshot seams.
  Resolution: move the composition/lazy operation boundary now; leave the pure preview-diagnostics cluster and tightly coupled widget/render payload code for a later focused slice rather than creating speculative adapters here.
- Observation: Existing composition tests assert lazy construction and exact request forwarding through private builder seams.
  Resolution: migrate those tests to the new typed operation factory and explicit capture factory, then delete the private compatibility seams instead of preserving aliases for test imports.
- Observation: There is no `tests/unit/test_phase3_signed_acceptance_evidence.py` file.
  Resolution: use the existing `tests/unit/test_qa_signed_acceptance_evidence.py` and signed matrix/lifecycle tests for default evidence wiring and matrix behavior.

## Decision Log

- Decision: Introduce `Phase3MatrixOperations` with explicit `preview` and `signed_acceptance` callables rather than a new generic `run(kind, payload)` registry.
  Rationale: The application orchestrator is already the canonical tagged dispatcher; the presentation boundary should match the two typed callables the service actually injects and avoid a second service locator.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep interactive capture separate from matrix composition and construct it only when `capture_harness` is invoked.
  Rationale: Interactive capture owns Qt bindings, viewer/signing workflows, session lifecycle, reporting, and checklist output; keeping it out of the matrix object preserves headless construction and makes the dependency direction explicit.
  Date/Author: 2026-08-01 / Codex.
- Decision: Remove `Phase3Composition` and `Phase3Harness` rather than retain compatibility aliases.
  Rationale: They are internal forwarding layers with no production callers, and the user explicitly requested removal of legacy compatibility pieces and cruft. The stable contracts are the application service/orchestrator, request DTOs, raw summaries, capture payload, CLI behavior, and artifacts.
  Date/Author: 2026-08-01 / Codex.
- Decision: Relocate only composition-owned code in this slice and defer broad Qt/PIL/render-helper extraction.
  Rationale: The fresh review found a safe pure preview-diagnostics seam, but combining it with the composition migration would enlarge the change surface. The deferred cluster remains a ranked follow-up, not a reason to keep the redundant composition facade.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

The primary migration and import-isolation follow-up are implemented and validated. `Phase3MatrixOperations` owns lazy preview/signed operation wiring; interactive capture is separately lazy; redundant composition/facade/lazy/protocol symbols are removed; and Qt package exports are lazy. The signed matrix retains one shell/lifecycle for its scenario sweep and closes it in the existing cleanup path. The second compliance/high-risk review and architecture-steward documentation reconciliation completed on 2026-08-01. Pure preview-diagnostics and broad widget/render extraction remain deferred; only the focused main-branch commit remains before closure.

## Context and Orientation

The application-facing flow begins in `src/foliaseal/application/phase3_evidence_service.py`. Its `Phase3EvidenceService` accepts independent capture, preview-matrix, and signed-acceptance runner callables, normalizes matrix mappings into typed result models, and leaves CLI dispatch to `phase3_evidence_orchestrator.py` and `src/foliaseal/__main__.py`.

The Qt composition root is `src/foliaseal/presentation/qt/phase3_harness.py`. It now supplies concrete runner factories, the interactive runner, matrix builders, and many preview/render/PDF helpers; the removed `Phase3Composition`, `Phase3Harness`, and specialized lazy wrappers are no longer current symbols. `src/foliaseal/presentation/qt/phase3_matrix_operations.py` owns the dependency-light lazy matrix boundary. `src/foliaseal/presentation/qt/phase3_preview_matrix_runner.py` owns one headless preview sweep; `phase3_signed_acceptance_matrix_runner.py` owns one Qt-backed signed sweep; `phase3_harness_session_runner.py`, `phase3_harness_workspace.py`, `phase3_harness_capture_assembler.py`, and `phase3_harness_reporting.py` own narrower session, workspace, payload, and report boundaries.

`src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` builds `Phase3MatrixOperations`, injects its two matrix methods, and provides a separate lazy capture runner factory. Concrete harness and signed-asset imports occur only when a selected operation requires them. Existing `Phase3MatrixRequest`, `Phase3HarnessCaptureRequest`, `Phase3HarnessCapture`, raw matrix summary dictionaries, and artifact/report contracts remain unchanged.

## Plan of Work

First create `src/foliaseal/presentation/qt/phase3_matrix_operations.py`. Define a frozen `Phase3MatrixOperations` dataclass whose `preview` and `signed_acceptance` fields accept `Phase3MatrixRequest` and return the existing raw summary mapping. Provide `build_headless_phase3_matrix_operations(preview_factory, signed_acceptance_factory)` that stores lazy factories and constructs only the selected runner on first invocation. The module must import only standard-library typing/dataclass utilities and application request types; it must not import PySide6, PIL, pyHanko, render backends, profile stores, or `phase3_harness.py`.

Then update `phase3_signed_acceptance_evidence.py` to build the matrix operation object and inject `operations.preview` and `operations.signed_acceptance` into `Phase3EvidenceService`. Add an explicit `build_interactive_phase3_capture_runner()` entrypoint at the Qt adapter edge that lazily builds `Phase3InteractiveHarnessRunner`; use it only for `harness_runner`. Preserve runtime-noise suppression and the existing `matrix_runner` override used by tests.

Migrate `phase3_harness.py` so its old composition section no longer defines the two protocols, lazy wrapper classes, `Phase3Composition`, or `Phase3Harness`. Keep the existing concrete runner builders and interactive runner wiring only where they are still required by the new factories. Remove forwarding-only helpers proven unused by search and tests; do not remove concrete helpers that are live dependencies of matrix runners, workspace adapters, capture assembly, or render snapshotters. If moving a builder into `phase3_matrix_operations.py` would create a circular import, keep the builder in the Qt composition root and pass it as a factory; the new module must remain dependency-light.

Retarget `tests/unit/test_phase3_harness.py` and related tests. Replace tests that construct `Phase3Composition`/`Phase3Harness` with tests for lazy matrix operation construction, exact request forwarding, selected-operation isolation, explicit capture-factory installation, and stable raw summary results. Preserve tests for runner-level lifecycle closure, error-row shaping, artifact paths, capture JSON, and CLI/application normalization. Add an import-isolation assertion that importing `phase3_matrix_operations` does not load Qt/PIL/pyHanko modules.

Finally update `README.md`, `docs/ARCHITECTURE.md`, and active Phase 3 ExecPlans. State that the application service/orchestrator is the caller boundary, matrix operations are explicit and lazy, interactive capture is separately installed, and `phase3_harness.py` is no longer a three-verb compatibility facade. Record that broad preview/widget/render extraction and the pure preview-diagnostics cluster remain a separate future slice. Do not rewrite historical ExecPlans merely to erase their historical descriptions; update current ownership statements and any active plan that claims the removed classes are present.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the clean baseline and inventory callers:

       git status --short --branch
       rg -n "Phase3Composition|Phase3Harness\\b|_Phase3Lazy|Phase3HarnessInteractivePort|Phase3HarnessMatrixPort" src tests README.md docs/ARCHITECTURE.md

   The baseline is expected to be clean on `main` at or after `c682a72bf`.

2. Add the operation module and migrate default service wiring. Run the focused composition/service tests:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_phase3_signed_acceptance_evidence.py

   The new operation-boundary tests must prove that constructing headless operations invokes neither Qt nor the interactive factory, and that each selected operation forwards the exact `Phase3MatrixRequest` fields.

3. Remove obsolete composition/facade symbols and migrate tests. Verify that no production source imports the deleted classes or lazy wrappers:

       rg -n "Phase3Composition|Phase3Harness\\b|_Phase3Lazy|Phase3HarnessInteractivePort|Phase3HarnessMatrixPort" src tests
       .venv/bin/ruff check src tests
       git diff --check

4. Run the affected evidence and CLI tests:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_capture_assembler.py tests/unit/test_phase3_harness_reporting.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_phase3_signed_acceptance_evidence.py tests/unit/test_main_cli.py

5. Run the complete suite and release-fidelity matrices. Preserve the tracked fixture and certificate files:

       .venv/bin/python -m pytest -q
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-hybrid-preview
       QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-phase3-hybrid-signed

   Expect the established behavior: eight preview scenarios with zero errors; eight signed scenarios with six successful signings, two matched intentional rejections, zero unexpected errors, and passing acceptance expectations.

6. Remove only the two temporary matrix directories and prove environment cleanup:

       rm -rf /tmp/foliaseal-phase3-hybrid-preview /tmp/foliaseal-phase3-hybrid-signed
       ps -eo pid,args | awk '/python.*foliaseal|python.*phase3/ && !/awk/ {print}'

   The process check must print nothing. Do not delete tracked artifacts or broad workspace paths.

7. After the first implementation pass, spawn one explorer-light compliance reviewer for `docs/ARCHITECTURE.md`, `docs/SPEC.md`, README, and stable evidence contracts. Spawn a second high-risk explorer-light review for Qt laziness, lifecycle cleanup, raw summary parity, import isolation, and artifact cleanup. If either review finds a discrepancy, create a child ExecPlan, implement it, and repeat both reviews before documentation and commit.

8. Spawn a worker-light documentation reviewer using `architecture-steward` to reconcile the current architecture and active plans. Then spawn a worker-light using `write-git-commit` to stage only intended files and create the focused main-branch commit. Verify `git status --short --branch` is clean.

## Validation and Acceptance

The slice is accepted when `Phase3MatrixOperations` supplies preview and signed matrix callables without importing or constructing the interactive Qt graph, and the interactive capture runner is created only when explicitly requested. `Phase3EvidenceService` and `Phase3EvidenceOrchestrator` retain their current request/result contracts. No production source or test imports the removed `Phase3Composition`, `Phase3Harness`, specialized lazy wrappers, or obsolete forwarding-only protocols.

The complete pytest suite, focused evidence tests, Ruff, and `git diff --check` must pass. The preview matrix must report eight scenarios and zero errors. The signed matrix must report eight scenarios, six successful signings, two matched intentional rejections, zero unexpected errors, and passing acceptance expectations. CLI labels, summary JSON keys, artifact paths, capture JSON fields, checklist output, and lifecycle cleanup must remain behaviorally identical. No FoliaSeal or Phase 3 process may remain after validation.

## Idempotence and Recovery

The operation module is additive until callers migrate. If a migration test fails, compare the raw request and summary mapping with the pre-migration test and correct only the factory/wiring adapter; do not restore deleted compatibility aliases. If a full matrix run fails halfway, remove only the two named temporary directories and rerun. If documentation review finds stale current ownership text, update the architecture/active plan and rerun `git diff --check`; do not rewrite historical records unless they falsely describe current behavior.

## Artifacts and Notes

Record evidence here as implementation proceeds:

       baseline commit: c682a72bf
       operation-boundary tests: 4 tests included in the 107 focused passing tests
       affected tests: 144 passed, 1 pre-existing Pillow warning
       full suite: 1038 passed, 1 pre-existing Pillow deprecation warning
       preview matrix: 8 scenarios, 0 errors
       signed matrix: 8 scenarios, 6 successful signings, 2 intentional rejections, expectations passed
       compatibility cleanup: removed composition/facade/lazy symbols and stale test seams; stable contracts retained
       process cleanup: no matching FoliaSeal/Phase 3 process
       implementation commit: <hash>

## Interfaces and Dependencies

In `src/foliaseal/presentation/qt/phase3_matrix_operations.py`, define:

    @dataclass(frozen=True)
    class Phase3MatrixOperations:
        preview: Callable[[Phase3MatrixRequest], Mapping[str, Any]]
        signed_acceptance: Callable[[Phase3MatrixRequest], Mapping[str, Any]]

    def build_headless_phase3_matrix_operations(
        *,
        preview_factory: Callable[[], Callable[[Phase3MatrixRequest], Mapping[str, Any]]],
        signed_acceptance_factory: Callable[
            [], Callable[[Phase3MatrixRequest], Mapping[str, Any]]
        ],
    ) -> Phase3MatrixOperations: ...

The factory must use one generic internal lazy callable or equivalent implementation so each runner is constructed once, on first selected invocation. The module may import `Phase3MatrixRequest` from `foliaseal.application.phase3_evidence_service`, but it must not import Qt, PIL, pyHanko, rendering, filesystem adapters, or `phase3_harness.py`.

The explicit interactive factory may remain in `phase3_harness.py` or move to a dedicated `phase3_interactive_capture.py` if the move is mechanical and does not create a circular import. Its returned callable must accept `Phase3HarnessCaptureRequest` and return `Phase3HarnessCapture`. It owns Qt binding/session/reporting dependencies; it must not be constructed by `build_headless_phase3_matrix_operations`.

The stable external contracts are `Phase3EvidenceService.capture_harness`, `preview_matrix_result`, `signed_acceptance_matrix_result`, `Phase3HarnessCaptureRequest`, `Phase3MatrixRequest`, `Phase3HarnessCapture.to_json()`, raw matrix summary dictionaries, CLI command names, and artifact/report files. These contracts are not to be replaced with untyped mappings or a second public dispatcher.

## Change-Slice Boundary

This is one primary architecture/refactor change with affected tests and documentation/status updates. Allowed changes are the new matrix-operations module, default service wiring, explicit capture-factory wiring, removal of redundant composition/lazy/forwarding symbols, migration of direct tests, current architecture/README/active-plan updates, and temporary matrix artifacts. Forbidden changes include changing application DTOs, CLI commands or labels, evidence JSON schemas, matrix manifests, signing semantics, Qt workspace behavior, broad preview-widget/render extraction, recursive PDF parsing, certificate behavior, or unrelated GUI styling.

Plan revision note: created 2026-08-01 after the required fresh explorer review. The plan deliberately narrows the recommended hybrid to the safe operation-composition seam; pure preview diagnostics and tightly coupled Qt/PIL/render payload extraction remain future slices rather than hidden work in this implementation.
