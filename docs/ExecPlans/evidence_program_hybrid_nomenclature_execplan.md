# Deepen the evidence program and remove obsolete internal Phase 3 naming

This ExecPlan is a living document and must be maintained according to `.agents/skills/write-execplan/PLANS.md`. It is deliberately a complete one-slice DevLoop: design translation, implementation, compatibility/cruft deletion, validation, architecture review, documentation reconciliation, and commit all belong to this slice. Milestones organize the work but are not stopping points.

## Purpose / Big Picture

FoliaSeal’s evidence workflow already has explicit application verbs, but its caller-facing types and composition still carry obsolete “Phase 3” names. The presentation layer also has a redundant lazy matrix holder and three near-identical operation wrappers. After this slice, callers use a neutral application-owned `EvidenceProgram` boundary, lazy runner construction lives in one composition module, and obsolete matrix-operation compatibility layers are gone. Users still run the same CLI commands and receive the same capture JSON, matrix summaries, artifact paths, rejection rows, and markdown evidence.

The slice intentionally strips `phase3` nomenclature from internal orchestration, request, port, and composition names. Names that are part of persisted JSON, schema versions, artifact paths, or public CLI commands remain unchanged because renaming them would be a user-visible compatibility break; the plan records those as external contracts rather than silently introducing aliases.

## Child ExecPlan Dependencies

The bounded compliance follow-up is tracked in
`docs/ExecPlans/evidence_program_hybrid_compliance_followup_execplan.md`.
It was created after review found contract and validation issues outside the
initial rename pass, and it is complete before this parent closes.

## Progress

- [x] (2026-08-02) Fresh explorer reviewed clean `main` at `1884bab63`, confirmed the canonical orchestrator/service callers, identified the redundant matrix holder and operation wrappers, and inventoried stable CLI/persisted contracts.
- [x] (2026-08-02) Selected the hybrid: neutral application `EvidenceProgram` with explicit capture, preview, signed-acceptance, evidence, and validation verbs; separate lazy interactive capability; no generic tagged dispatcher.
- [x] (2026-08-02) Created this one-slice ExecPlan before implementation.
- [x] (2026-08-02) Renamed the application service/orchestrator/ports and request/session types to `EvidenceService`, `EvidenceProgram`, neutral request names, and neutral module paths; preserved serialized `Phase3*` result DTOs, schema/version strings, CLI commands, and artifact paths.
- [x] (2026-08-02) Folded lazy matrix construction into `evidence_runner_factories.py`, deleted `phase3_matrix_operations.py`, and migrated holder tests to neutral factory boundary tests.
- [x] (2026-08-02) Removed service aliases and duplicate forwarding seams; migrated production callers and tests without changing CLI or persisted contracts.
- [x] (2026-08-02) Focused validation passes 137 tests with one pre-existing Pillow warning; full suite passes 1042 tests with the same warning; Ruff, compileall, and diff checks are clean.
- [x] (2026-08-02) Preview smoke executed 4 scenarios and signed acceptance smoke executed 3 offscreen scenarios; summary files were produced in a temporary directory and removed, with no FoliaSeal/Python process left running.
- [x] First compliance pass identified the historical summary-path regression, construction-time heavy imports, stale current documentation, a residual internal Phase3 protocol name, and the missing aggregate scenario-error gate; the child follow-up was created.
- [x] Child follow-up restored the persisted artifact path, deferred heavy imports, neutralized the residual protocol, added the aggregate error-counter regression test, and reconciled current docs.
- [x] Two independent post-fix architecture reviews passed the implementation, lifecycle, contract, and documentation checks.
- [x] Documentation worker reconciled README and `docs/ARCHITECTURE.md` using architecture-steward guidance. Commit remains owned by the parent workflow.

## Surprises & Discoveries

- Observation: The current matrix holder has only one production consumer and the three operation wrappers are near-identical.
  Evidence: The fresh explorer found `signed_acceptance_evidence.py` is the only production wiring site; focused service/orchestrator/matrix tests pass 21 tests before this change.
- Observation: The interactive and signed matrix paths have different lifecycle requirements.
  Evidence: Preview is headless; signed acceptance owns an offscreen Qt lifecycle and must close it in `finally`; interactive capture loads QApplication only when requested.
- Observation: CLI names and capture/matrix output fields are observable contracts.
  Evidence: `tests/unit/test_main_cli.py` asserts command headings, counters, artifact directories, summary paths, and validation behavior; capture JSON uses the `phase3_evidence_v1` contract.
- Observation: A broad nomenclature replacement can silently alter an external artifact path or validation gate.
  Evidence: Compliance review caught the restored `artifacts/phase3_signed_acceptance_evidence_summary.md` path and the missing `error_scenario_count` aggregate rejection before closure; both now have regression coverage.

## Decision Log

- Decision: Use an application-owned `EvidenceProgram` with explicit methods rather than a `run(mode=...)` dispatcher.
  Rationale: The prior tagged dispatcher was intentionally removed; explicit verbs keep operation-specific required inputs visible and prevent a new generic registry.
  Date/Author: 2026-08-02 / Codex.
- Decision: Keep persisted `Phase3*` result DTOs, schema/version strings, artifact paths, and CLI command names in this slice.
  Rationale: They are externally observable contracts; internal nomenclature can be removed without silently invalidating existing evidence or automation.
  Date/Author: 2026-08-02 / Codex.
- Decision: Move lazy operation ownership into the neutral composition/program module and delete `phase3_matrix_operations.py` rather than adding another façade.
  Rationale: The holder only forwards two callables and duplicates the factory layer; deleting it reduces surface area and preserves lazy headless imports.
  Date/Author: 2026-08-02 / Codex.
- Decision: Do not rename the large harness module or every persisted DTO in this slice.
  Rationale: Several private harness builders are directly monkeypatched by tests and internally coupled; broad renaming would obscure behavior changes and weaken the one-slice acceptance boundary. The application/composition seam is the safe first nomenclature tranche.
  Date/Author: 2026-08-02 / Codex.

## Outcomes & Retrospective

The neutral `EvidenceProgram` now exposes explicit verbs without a tagged dispatcher; lazy interactive,
preview, and signed runner/operation construction is centralized in
`evidence_runner_factories.py`; and `phase3_matrix_operations.py`/`EvidenceMatrixOperations` are
deleted. The child compliance plan fixed the historical default signed-evidence markdown path,
deferred heavy imports during program construction, neutralized the internal protocol, and made
`error_scenario_count` fail aggregate validation. The CLI commands, persisted `Phase3*` DTOs, JSON
fields, summary paths, and artifact paths remain unchanged. Focused/full validation, two post-fix
compliance passes, and documentation reconciliation are complete. The implementation and plan closure
were committed as `6c2f9fb4a` (`Refine evidence program boundaries and nomenclature`).

## Context and Orientation

The application layer currently exposes `EvidenceService` from `src/foliaseal/application/evidence_service.py` and the thin `EvidenceProgram` from `src/foliaseal/application/evidence_program.py`. The service owns request dataclasses, injected capture/matrix runners, asset generation, capture validation, signed-evidence aggregation, and markdown publication. The orchestrator delegates explicit verbs and provides a PDF-bound session.

The presentation composition module `src/foliaseal/presentation/qt/evidence_runner_factories.py` lazily imports the concrete Qt/Pillow/pyHanko graph from `phase3_harness.py` and builds interactive, preview, and signed matrix runners. The former `phase3_matrix_operations.py` holder has been deleted; `signed_acceptance_evidence.py` now injects the neutral lazy operation callables directly. `evidence_interactive_capture.py` owns the lazy interactive runner while retaining the serialized `Phase3HarnessCapture` result name.

The CLI in `src/foliaseal/__main__.py` calls the explicit orchestrator verbs. `src/foliaseal/application/phase3_evidence_core.py` and the concrete capture/matrix result models define serialized evidence behavior. The test suite includes import-isolation tests proving that constructing the default service does not eagerly import Qt, Pillow, or pyHanko.

## Plan of Work

First rename the application-facing service/orchestrator concepts and their request/port types to neutral names. Move `EvidenceService` to a neutral `EvidenceService` module/name, move `EvidenceProgram` to an application-owned `EvidenceProgram`, and rename only internal request/port/session types whose names are not serialized. Keep result DTOs and JSON/schema identifiers unchanged. Update `__main__.py`, default composition, tests, README, architecture documentation, and imports together; do not add deprecated aliases.

Next fold `_LazyMatrixOperation`, `EvidenceMatrixOperations`, and the two matrix factory wrappers into `evidence_runner_factories.py` or the neutral program composition module. The resulting factories must still construct concrete runners only on first invocation, forward every request field unchanged, and avoid importing `phase3_harness.py` during headless application import. Delete `phase3_matrix_operations.py` and its dedicated compatibility tests after migrating their behavior assertions to factory/program boundary tests.

Keep interactive capture as an explicit capability. Its builder may continue to load the Qt graph lazily, but its internal builder names should use neutral evidence terminology where they are not persisted. Do not remove private harness helpers that are still directly consumed by other helpers or tests; instead, record them as the next extraction target. Remove only aliases, re-exports, and duplicate forwarding seams proven unused by repository-wide search.

Finally migrate tests from private composition seams to the neutral program boundary. Add tests that construct the default program without importing heavy GUI/signing modules, verify preview and signed request forwarding, verify interactive construction is deferred, assert lifecycle cleanup on success/failure, and preserve stable summary/capture contracts. Update documentation to describe neutral ownership, retained external contracts, and the next safe extraction boundary.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the starting point and capture the baseline:

       git status --short
       git log -1 --oneline
       .venv/bin/python -m pytest -q tests/unit/test_evidence_runner_factories.py tests/unit/test_evidence_program.py tests/unit/test_evidence_service.py

   Expect a clean tree and the explorer-confirmed focused baseline of 21 passing tests.

2. Rename neutral application modules/types and migrate imports with `rg`-verified completeness. Preserve `Phase3*` names only for result models, persisted contracts, schema/version identifiers, and CLI/artifact strings. Run the focused tests after each dependency-order group.

3. Move lazy matrix operation construction into the neutral factory/program module. Preserve the callable signatures consuming the existing matrix request shape, then delete `src/foliaseal/presentation/qt/phase3_matrix_operations.py`. Replace holder-specific tests with boundary tests for lazy construction, import isolation, request forwarding, and exception/result propagation. (Completed; see Progress.)

4. Remove stale compatibility aliases and re-exports. Verify with:

       rg -n "EvidenceService|EvidenceProgram|EvidenceServicePort|phase3_matrix_operations|EvidenceMatrixOperations|build_evidence_matrix_operations" src tests README.md docs --glob '!docs/ExecPlans/*'

   Any remaining match must be either an intentional persisted/CLI contract or a historical documentation entry explicitly labeled as such.

5. Run focused tests, import-isolation subprocess checks, Ruff, compileall, and the full suite:

       .venv/bin/python -m pytest -q tests/unit/test_evidence_runner_factories.py tests/unit/test_evidence_program.py tests/unit/test_evidence_service.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py
       .venv/bin/ruff check src tests
       .venv/bin/python -m compileall -q src tests
       .venv/bin/python -m pytest -q

   Update this plan with actual counts and any pre-existing warnings.

6. Run preview and signed acceptance smoke commands using a new temporary artifacts directory, verify authoritative summary paths and expected scenario/counter rows, then remove the temporary directory and confirm no FoliaSeal processes, dialogs, core files, or temporary artifacts remain. Use `QT_QPA_PLATFORM=offscreen` for the signed command.

7. Run `git diff --check`, inspect the complete diff for accidental contract changes, and ask the documentation worker to reconcile README and `docs/ARCHITECTURE.md` using the architecture-steward skill. Then ask the git worker to use write-git-commit for the implementation and plan closure.

## Validation and Acceptance

The slice is accepted only when the default application evidence program can be imported and constructed without importing PySide6, Pillow, or pyHanko; preview and signed matrix requests forward all existing fields and produce the same summary counters/paths; interactive capture constructs Qt only when explicitly requested; and signed lifecycle cleanup runs on both success and failure.

The existing CLI commands and options must continue to print their current headings/counters, write the same JSON/markdown keys and artifact paths, preserve intentional fit-rejection rows, and return the same success/failure exit behavior. The full test suite must pass, with only previously known warnings allowed. Focused boundary tests must cover lazy construction and removal of the old matrix holder. `git diff --check`, Ruff, compileall, and the cleanup audit must be clean.

## Idempotence and Recovery

Use `git mv` for module renames and update imports before deleting files. Repeat searches and tests after each rename group. If a test exposes an external import or persisted contract, retain that contract name in its owning module and record the exception rather than adding a compatibility alias. Use fresh temporary artifact directories for smoke runs. Never use destructive repository resets; recover a failed rename by restoring only the affected file from the current diff.

## Artifacts and Notes

Baseline focused slice: 21 tests passed. Final focused selected suite: 137 passed with one pre-existing Pillow deprecation warning; the post-fix focused compliance subset passed 61 tests. Full suite: 1044 passed with the same warning. Ruff, compileall, and `git diff --check` are clean. Default-program construction loaded none of `PySide6`, `PIL`, `pyhanko`, or `cryptography`. Preview smoke produced 4 scenarios and signed acceptance smoke produced 3 scenarios with matching temporary summary paths; the temporary directory was removed and a separate exact process audit found no running `foliaseal`, `python`, or `python3` process. Two independent post-fix compliance reviews passed. The documentation worker reconciled README and `docs/ARCHITECTURE.md`. Commit: `6c2f9fb4a`.

## Interfaces and Dependencies

At completion, the application boundary is neutral and explicit:

    class EvidenceProgram:
        def capture(self, request: EvidenceCaptureRequest) -> CaptureResultPort: ...
        def preview_matrix(self, request: EvidenceMatrixRequest) -> MatrixResult: ...
        def signed_acceptance_matrix(self, request: EvidenceMatrixRequest) -> MatrixResult: ...
        def signed_acceptance_evidence(self, request: SignedAcceptanceEvidenceRequest) -> SignedAcceptanceEvidenceResult: ...
        def validate(self, request: EvidenceValidationRequest) -> EvidenceContractEvaluation: ...

The concrete runner types, Qt bindings, Pillow/Poppler rendering, pyHanko/certification/TSA services, filesystem artifact sink, and markdown writer remain injected or lazily constructed adapters. No generic mode registry or tagged dispatcher is introduced. Stable persisted result DTOs and evidence schema identifiers remain available at the serialization boundary even though internal orchestration and request/port names become neutral.

## Revision Notes

2026-08-02: Created after a fresh explorer and three independent interface designs. The recommended hybrid combines an explicit application-owned program with internal ports/adapters, removes the redundant matrix holder and compatibility wrappers, and begins stripping internal `phase3` nomenclature while preserving observable CLI and evidence contracts.
2026-08-02: Updated after implementation and smoke validation. The application boundary and composition modules now use neutral names; the large harness and persisted evidence vocabulary remain intentionally unchanged for this bounded slice. Focused/full counts and smoke cleanup evidence were recorded before compliance review.
2026-08-02: Added the compliance follow-up after two initial reviews found an artifact-path regression, eager construction imports, stale docs, a residual internal protocol name, and an aggregate error-counter gate hole. All findings were fixed, two post-fix reviews passed, and README/architecture documentation was reconciled; commit closure remains.
