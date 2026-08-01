# Replace the Phase 3 evidence gateway with a typed command pipeline

This ExecPlan is a living document. It must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`. The goal is one complete implementation slice: typed application commands and results, a Qt-free evidence core, explicit effect ports, direct CLI/service wiring, removal of obsolete compatibility facades, documentation reconciliation, validation, and commit.

## Purpose / Big Picture

After this change, Phase 3 evidence capture, preview matrices, signed-acceptance matrices, aggregate signed evidence, and capture validation will cross one explicit application boundary with typed inputs and outputs. The Qt harness will remain responsible for Qt/PDF/image effects, while application code will own result normalization, evidence decisions, and stable artifact contracts. Users will observe the same CLI commands, artifact paths, JSON fields, checklist files, and matrix lifecycles, but callers and tests will no longer depend on a generic `object` gateway, raw callback bundles, or legacy `run_*` aliases.

The slice deliberately removes cruft instead of adding another compatibility layer. The obsolete `phase3_evidence_gateway.py` facade, `Phase3Harness.run_*` aliases, one-method matrix wrapper ports, private evidence-builder bridges, and tests that exist only to preserve those names are deleted or migrated. Existing public CLI command names and serialized evidence keys remain unchanged because they are documented behavior.

## Child ExecPlan Dependencies

- [x] Fresh explorer-light review of the current checkout and architecture completed before planning.
- [x] No child ExecPlans are required; this slice is intentionally self-contained so it can be completed and validated in one development loop.

## Progress

- [x] (2026-08-01 10:24 -04:00) Reviewed the current clean checkout at `15891e476`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, the existing Phase 3 service/orchestrator/gateway, CLI wiring, Qt evidence adapter, tests, and outstanding Phase 3 plan notes.
- [x] (2026-08-01 10:24 -04:00) Confirmed the design: typed command/query results plus a pure evidence core and explicit effect protocols; preview/headless and signed/Qt lifecycles remain separate.
- [x] (2026-08-01) Added the pure evidence core and explicit service effect ports.
- [x] (2026-08-01) Replaced generic orchestrator dispatch with typed command/query handlers and moved the reusable document-bound session out of the gateway.
- [x] (2026-08-01) Routed CLI and signed-evidence composition directly through the orchestrator/session and removed the gateway and harness compatibility aliases.
- [x] (2026-08-01) Migrated tests from private compatibility seams to boundary tests and removed tests whose only purpose was preserving deleted names.
- [x] (2026-08-01) Implementation validation was completed by the development loop; documentation checks and diff review are recorded below.
- [x] (2026-08-01) Reconciled README, `docs/ARCHITECTURE.md`, and superseded ExecPlans with the final typed hybrid.
- [x] (2026-08-01) Added a blocked-import purity test, lazy application exports, and a concrete capture-result protocol so the application boundary is genuinely dependency-light and typed.
- [x] (2026-08-01) Removed duplicate service normalization/reporting helpers and routed tests and adapters to the single pure-core implementation.
- [x] (2026-08-01) Validation evidence: focused Phase 3/CLI/harness tests `134 passed, 1 warning`; full suite `1032 passed, 1 warning`; Ruff and `git diff --check` passed.

## Surprises & Discoveries

- Observation: The application already has tagged operation requests and a separate validation request, but `Phase3EvidenceOrchestrator.run()` returns `object` and the service still exposes raw `Callable` dependencies.
  Evidence: `src/foliaseal/application/phase3_evidence_orchestrator.py` and `phase3_evidence_service.py` currently define the tagged request but dispatch through broad methods and callback aliases.
- Observation: `Phase3Harness` is already a Qt adapter with canonical `capture()`, `preview_matrix()`, and `signed_acceptance_matrix()` verbs; the remaining `run_*` methods are compatibility wrappers.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` lines 220-248 and callers in `phase3_signed_acceptance_evidence.py`.
- Observation: The architecture explicitly says V1 prefers replacement over compatibility layers and lists gateway/service aliases as debt.
  Evidence: `docs/SPEC.md` replacement guidance and `docs/ARCHITECTURE.md` debt entries around lines 1074-1076.
- Observation: Workspace command objects and separate Phase 3 lifecycles are already stable enough to leave in the presentation adapter for this slice.
  Evidence: `phase3_harness_workspace.py` owns immutable scenario commands and the architecture warns against merging preview/headless with signed/Qt lifecycles speculatively.
- Observation: Importing a submodule under `foliaseal.application` originally executed eager package exports and loaded signing/render dependencies even for pure evidence code.
  Evidence: The new subprocess guard initially observed `PIL` and `pyhanko`; lazy exports in `application/__init__.py` reduced the heavy-module set to empty.
- Observation: Keeping the old service helper copies after introducing the core would allow evidence decisions to drift.
  Evidence: The compliance review found duplicate `_normalize_matrix_result`, matrix-row, markdown, and capture-loader implementations; they were deleted and the service now calls only `phase3_evidence_core.py`.

## Decision Log

- Decision: Use a hybrid of command/query handlers and a pure evidence core rather than moving the entire Qt harness into application code.
  Rationale: This removes generic and legacy seams while preserving the three different runtime lifecycles and keeping PySide6, PyHanko, Pillow, filesystem, and TSA effects outside the pure core.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep the documented CLI command names, arguments, artifact locations, summary JSON keys, checklist output, and matrix counters stable.
  Rationale: These are observable contracts used by users, acceptance scripts, and downstream evidence review; the refactor is structural, not a schema redesign.
  Date/Author: 2026-08-01 / Codex.
- Decision: Delete compatibility wrappers after migrating callers and tests in the same slice.
  Rationale: The user explicitly requires legacy compatibility pieces and cruft to be stripped out, and `docs/SPEC.md` prefers replacement over indefinite compatibility layers.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep `Phase3HarnessCapture` as the stable serialized capture payload for this slice, but move normalization/validation/report decisions into typed application helpers rather than widening the Qt harness.
  Rationale: Splitting the 43-field payload into new artifacts would create schema churn unrelated to the boundary cleanup; typed results can wrap it without changing emitted evidence.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

This section is completed at the end of the implementation. It must state which compatibility pieces were removed, which observable contracts were preserved, the exact validation evidence, and any remaining architecture debt that needs a future ExecPlan.

The completed slice removes `phase3_evidence_gateway.py`, `Phase3Harness.run_*` aliases, and the
service's raw matrix `run_*` methods. `phase3_evidence_core.py` now owns typed result truth and
evidence decisions, `phase3_evidence_ports.py` owns effect protocols, and the orchestrator/session
is the canonical reusable application boundary. CLI names, arguments, printed labels, summary JSON
fields and paths, checklist output, matrix counters, intentional rejection handling, and separate
preview/headless versus signed/Qt lifecycle ownership remain unchanged. Focused and full validation
were completed during implementation; the final documentation pass also confirms no live source or
test import references to the deleted gateway or aliases. Remaining debt is the intentional split
between application orchestration and runner-specific Qt/headless effects; a future slice should
only consolidate those contexts behind a proven shared contract.

## Context and Orientation

The repository is a local Python/Qt desktop application. Phase 3 evidence commands are parsed in `src/foliaseal/__main__.py`. `src/foliaseal/presentation/qt/phase3_harness.py` owns concrete Qt-backed capture and matrix adapters, including PDF inspection and image evidence. `src/foliaseal/application/phase3_evidence_service.py` coordinates those adapters through explicit effect protocols and delegates evidence decisions to `phase3_evidence_core.py`. `phase3_evidence_orchestrator.py` is the canonical typed command/query boundary and owns the document-bound session. `phase3_evidence_gateway.py` and the harness/service `run_*` aliases have been removed. `phase3_signed_acceptance_evidence.py` builds the concrete service and supplies the Qt adapter verbs directly.

The pure evidence core means code that accepts immutable Python values and makes evidence decisions without importing Qt, PyHanko, Pillow, filesystem stores, or subprocesses. An effect port is a small `Protocol` describing one replaceable side effect, such as running a matrix, generating fixture assets, loading a capture JSON file, or writing markdown. A command is an effectful request; a query is read-only validation. These terms are used only to make ownership and testing explicit.

## Plan of Work

First create `src/foliaseal/application/phase3_evidence_core.py`. Move or re-express the pure pieces currently embedded in `phase3_evidence_service.py`: matrix-summary normalization, critical-counter error calculation, signed-acceptance summary validation, signed-acceptance matrix row construction, and aggregate evidence markdown rendering inputs. Define typed immutable result/read models for matrix outcomes and validation outcomes, preserving all existing counters and paths. The module must import only standard-library typing/dataclass/path helpers and existing Qt-free evidence-contract types. Add unit tests that feed representative preview, signed-acceptance, intentional-rejection, and malformed summaries and assert the existing pass/fail decisions and serialized fields.

Next create `src/foliaseal/application/phase3_evidence_ports.py` with protocols for capture execution, preview matrix execution, signed-acceptance matrix execution, signed-acceptance asset generation, capture loading, text writing, and runtime-noise context. Replace the service’s `Callable` type aliases with these protocols. The concrete `Phase3Harness` and the signed-evidence Qt adapter will satisfy the protocols structurally; no runtime registration or dependency framework is needed.

Then revise `phase3_evidence_orchestrator.py` into the canonical application boundary. Define explicit command dataclasses (capture, preview matrix, signed matrix, aggregate signed evidence) and a separate capture-validation query, plus a typed result union or overloads so the dispatcher never returns `object` in annotations. Move the reusable document-bound `Phase3EvidenceSession` into this module and have it call typed orchestrator methods directly. Keep request constructors concise and preserve the existing request field names.

Update `phase3_evidence_service.py` to use the new protocols and pure core. Its typed matrix methods should call the injected runner and then the pure normalizer; aggregate signed evidence should call the pure summary/row/markdown helpers and retain the existing runtime-noise context and asset behavior. Remove `for_pdf()`’s import of the gateway and have it return the new orchestrator-owned session. Remove raw `run_preview_matrix()` and `run_signed_acceptance_matrix()` compatibility methods once all production callers and tests use typed methods or direct injected runners.

Update `src/foliaseal/__main__.py` to build an orchestrator directly over the default service and dispatch commands through its typed methods. Preserve every command name, argument, printed label, exit behavior, and artifact path. Update `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` to construct the service with `Phase3Harness.capture`, `preview_matrix`, and `signed_acceptance_matrix` rather than `run_*` aliases.

Delete `src/foliaseal/application/phase3_evidence_gateway.py` after callers migrate. Remove `Phase3Harness.run_preview_matrix`, `run_signed_acceptance_matrix`, and `run_signing_harness` from `phase3_harness.py`, along with one-method compatibility port classes and any private delegating builders that are no longer referenced by production code. Do not broaden this slice into a complete 4,351-line harness extraction: leave concrete Qt/PDF/image helpers in their existing adapter modules, but remove only obsolete bridges proven unused by search and tests.

Migrate tests accordingly. Replace gateway tests with orchestrator/session tests. Move pure normalization and validation assertions into the new core tests. Change harness tests to exercise canonical verbs and delete tests whose sole assertion is that a `run_*` alias or gateway import exists. Keep focused adapter tests for real lifecycle ordering, artifact paths, and stable payload keys. Add an import/grep guard test or validation command proving that deleted gateway and harness aliases are absent from production imports.

Finally reconcile `README.md`, `docs/ARCHITECTURE.md`, and the relevant Phase 3 ExecPlans. Describe the orchestrator/session and pure evidence core as canonical, describe the Qt harness as an adapter, remove gateway and `run_*` entries from module maps and entrypoint lists, and record the compatibility cleanup. Mark any superseded gateway-specific ExecPlan stale or completed according to repository conventions rather than leaving it as an active plan.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Confirm the starting state before edits:

       git status --short --branch
       rg -n "Phase3EvidenceGateway|gateway_for_service|run_preview_matrix|run_signed_acceptance_matrix|run_signing_harness" src tests

   The work must start from a clean `main` checkout at or beyond `15891e476`. If unrelated edits are present, preserve them and keep this slice scoped to the named files.

2. Implement the pure core, effect protocols, typed orchestrator/session, and service/CLI/Qt adapter migration described above. Use `apply_patch` for edits. After each logical migration, run the smallest relevant unit test file before deleting the old seam.

3. Remove the gateway module and compatibility aliases only after `rg` shows no production references. Update tests in the same change so no test preserves deleted cruft.

4. Run focused validation:

       .venv/bin/python -m pytest -q \
         tests/unit/test_phase3_evidence_core.py \
         tests/unit/test_phase3_evidence_orchestrator.py \
         tests/unit/test_phase3_evidence_service.py \
         tests/unit/test_main_cli.py \
         tests/unit/test_qa_signed_acceptance_evidence.py \
         tests/unit/test_phase3_harness_reporting.py

   Expect all selected tests to pass and no import errors for the deleted gateway.

5. Run the affected harness and signing evidence tests, then the complete suite:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m pytest -q

   The full suite must pass with no new warnings treated as errors.

6. Run static and repository checks:

       .venv/bin/ruff check src tests
       git diff --check
       rg -n "phase3_evidence_gateway|Phase3EvidenceGateway|gateway_for_service|def run_preview_matrix|def run_signed_acceptance_matrix|def run_signing_harness" src tests

   The final search may return only historical documentation references if those are explicitly marked completed; it must return no live production or test compatibility seam.

7. Exercise the observable CLI contract with the existing Phase 3 fixtures/manifests and run the repository’s preview and signed acceptance evidence commands used by the prior slice. Confirm stable summary paths, counters, intentional rejection handling, and checklist output. If the commands launch Qt or create files, use the existing offscreen/headless harness runners and clean up all generated processes and windows afterward.

8. Review the final diff for scope, update this plan’s Progress, Surprises & Discoveries, Decision Log, and Outcomes & Retrospective sections, then create one focused commit using the write-git-commit skill.

## Validation and Acceptance

The slice is accepted only when all of the following are true:

- The CLI commands `phase3-signing-harness`, `phase3-signing-preview-matrix`, `phase3-signing-acceptance-matrix`, `phase3-signing-acceptance-evidence`, and `phase3-signing-harness-validate` still parse and execute with their existing arguments and printed headings.
- Preview and signed matrix results retain their existing scenario counts, successful signing counts, critical zero-tolerance counters, intentional rejection behavior, authoritative `summary_json_path`, and artifact directories.
- Existing evidence payload fields such as `backend_reservation_snapshot`, `signed_runs`, `captured_states`, `captured_state_transition_diagnostics`, `evidence_contract_version`, `acceptance_tier`, and `gate_verdict` remain present and semantically unchanged.
- The application core can be imported and unit-tested without importing PySide6, PyHanko, Pillow, or Qt render backends.
- The orchestrator’s typed methods and session return concrete result types rather than `object` or an unbounded raw dictionary.
- No production or test code imports `phase3_evidence_gateway.py` or calls the deleted `Phase3Harness.run_*` aliases.
- Focused tests, affected harness tests, the full test suite, Ruff, and `git diff --check` pass.
- A final process/window audit shows no FoliaSeal or Phase 3 Python processes and no leftover GUI windows.

## Idempotence and Recovery

All code and documentation edits are additive or reversible until the final deletion step. Before deleting a compatibility file or alias, use `rg` to prove its callers have migrated and run the focused tests. If a deletion reveals an undocumented caller, restore only the smallest typed import or adapter needed, record the discovery in this plan, and do not reintroduce a generic gateway. Generated evidence artifacts belong under the existing artifacts directories and may be removed or regenerated by the repository’s normal harness commands; do not delete user documents or configuration catalogs. If tests fail after a partial migration, keep the new typed path and repair the caller/test rather than adding a new compatibility wrapper.

## Artifacts and Notes

The important proof artifacts are the new core/port unit tests, focused CLI and service test output, full-suite output, preview/signed matrix summaries, checklist markdown, and the final diff. Record concise command results here as implementation proceeds, for example:

       1032 passed, 1 warning
       preview matrix: 8 scenarios, 0 errors
       signed acceptance matrix: 8 scenarios, 6 successful signings, 2 matched intentional rejections

Implementation evidence: the focused boundary/CLI/harness run completed with `134 passed, 1 warning`; the full suite completed with `1032 passed, 1 warning`. The offscreen release-fidelity preview matrix completed 8/8 scenarios with zero errors. The signed release-fidelity matrix completed 8 scenarios with 6 successful signings, 2 matched intentional rejections, zero critical counters, and `acceptance_expectations_passed=true`. The generated `/tmp/foliaseal-hybrid-*` directories were removed after inspection, and no FoliaSeal/Phase 3 Python process remained; no display was available for `wmctrl`, so the process audit was supplemented by the offscreen runner's clean exit.

Do not paste full JSON or large diffs into this plan; record paths and the fields/counters verified.

## Interfaces and Dependencies

In `src/foliaseal/application/phase3_evidence_ports.py`, define structurally typed protocols with these shapes:

    class CaptureRunnerPort(Protocol):
        def __call__(self, request: Phase3HarnessCaptureRequest) -> CaptureResultPort: ...

    class CaptureResultPort(Protocol):
        def to_json(self) -> str: ...

    class MatrixRunnerPort(Protocol):
        def __call__(self, request: Phase3MatrixRequest) -> Mapping[str, Any]: ...

    class AssetGeneratorPort(Protocol):
        def __call__(self, *, root: Path) -> object: ...

    class CaptureLoaderPort(Protocol):
        def __call__(self, path: Path) -> Mapping[str, Any]: ...

    class TextWriterPort(Protocol):
        def __call__(self, path: Path, text: str) -> None: ...

In `phase3_evidence_core.py`, define pure functions or a small immutable service for matrix normalization, signed-summary validation, capture validation delegation, matrix-row construction, and evidence markdown model construction. These functions must not import Qt or concrete infrastructure.

In `phase3_evidence_orchestrator.py`, expose typed methods equivalent to:

    def capture(self, request: Phase3HarnessCaptureRequest) -> Phase3HarnessCapture: ...
    def preview_matrix(self, request: Phase3MatrixRequest) -> Phase3MatrixResult: ...
    def signed_acceptance_matrix(self, request: Phase3MatrixRequest) -> Phase3MatrixResult: ...
    def signed_acceptance_evidence(self, request: Phase3SignedAcceptanceEvidenceRequest) -> Phase3SignedAcceptanceEvidenceResult: ...
    def validate(self, request: Phase3ValidationRequest) -> EvidenceContractEvaluation: ...

The concrete Qt harness remains the implementation of the capture and matrix runner ports. Existing PyHanko, Pillow, PySide6, TSA, filesystem, and logging dependencies remain in their current adapter modules and are injected into the application service; they must not leak into the pure evidence core or be imported at runtime by the effect-port declarations. The lazy `foliaseal.application` exports preserve existing convenience imports while allowing direct imports of the core and orchestrator without loading those heavy dependencies.

## Change-Slice Boundary

This is one structural behavior-preserving slice. Allowed changes are application boundary code, Phase 3 Qt adapter wiring needed to satisfy the new ports, directly affected tests, README/architecture/ExecPlan status, and generated evidence outputs used for validation. Do not mix unrelated visible-signature geometry, signing-workspace, certificate-schema, packaging, or GUI redesign work into this commit. The only intentional behavior change is removal of undocumented legacy compatibility entrypoints; documented CLI and evidence behavior must remain stable.

Plan revision note: created 2026-08-01 after fresh explorer review; explicitly expanded the slice to delete obsolete compatibility wrappers and private bridges in the same implementation so the hybrid boundary is complete rather than another transitional facade.
