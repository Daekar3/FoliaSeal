# Deepen Phase 3 evidence orchestration behind one application boundary

This ExecPlan is a living document. Maintain it in accordance with `.agents/skills/write-execplan/PLANS.md`. The entire change is one compatibility-preserving architecture slice: make an application-owned Phase 3 evidence orchestrator canonical for tagged evidence dispatch and validation, route the CLI through it, and preserve the existing Qt adapters, matrix runners, artifact files, result DTOs, and command-line contracts.

## Purpose / Big Picture

Phase 3 evidence currently has a small gateway, but the gateway's real behavior is still embedded in a presentation-layer facade and several runner-specific trees. After this slice, all caller-facing Phase 3 operations will cross one application-owned `run()`/`validate()` boundary. Preview matrices, signed-acceptance matrices, interactive capture, aggregate signed evidence, and capture validation will still use their existing execution adapters, but callers will no longer need to know which runner or Qt composition root owns each operation.

The user-visible behavior is intentionally unchanged. Running `foliaseal phase3-signing-preview-matrix`, `foliaseal phase3-signing-acceptance-matrix`, `foliaseal phase3-signing-acceptance-evidence`, `foliaseal phase3-signing-harness`, or `foliaseal phase3-signing-harness-validate` must produce the same labels, exit behavior, artifact paths, summary fields, acceptance counters, checklist output, and cleanup behavior as before. The architectural result is observable through boundary tests that dispatch every operation through the new application module and through the unchanged release-fidelity matrices.

## Child ExecPlan Dependencies

- [x] The visible-signature text measurement boundary is complete on `main` (`909fddd8c` and its plan metadata commits).
- [x] Fresh explorer-light reconnaissance inspected the current gateway, service, Qt facade, preview/signed runners, lifecycle/artifact ports, CLI dispatch, and tests.
- [x] The recommended hybrid is selected: one application orchestrator, existing runner-specific execution adapters, and compatibility gateway/service facades.
- [x] No child plan is required; preview/headless and signed/Qt execution contexts are deliberately retained as separate adapter strategies in this slice.

## Progress

- [x] (2026-08-01) Re-checked clean `main` and confirmed the existing `Phase3EvidenceGateway` is additive but not yet the canonical orchestration owner.
- [x] (2026-08-01) Completed fresh reconnaissance of service/gateway DTOs, `Phase3Harness`, preview and signed runners, lifecycle cleanup, artifact summary differences, CLI dispatch, and tests.
- [x] (2026-08-01) Chose the bounded hybrid: move tagged dispatch and validation into an application module, keep runner-specific Qt/headless execution intact, and route CLI calls through the application boundary.
- [x] (2026-08-01) Wrote this self-contained one-slice ExecPlan before implementation.
- [x] (2026-08-01) Added `Phase3EvidenceOrchestrator` and moved tagged request/validation ownership into the application module.
- [x] (2026-08-01) Converted `Phase3EvidenceGateway` into a compatibility facade over the orchestrator without breaking imports or `for_pdf()` sessions.
- [x] (2026-08-01) Routed Phase 3 CLI dispatch through the orchestrator while preserving typed service methods and output contracts.
- [x] (2026-08-01) Added boundary tests for all operation kinds, payload validation, validation dispatch, compatibility gateway/session behavior, and CLI behavior; the focused service/runner/CLI slice passes (58 tests).
- [x] (2026-08-01) Completed the first focused validation pass (59 tests after the gateway-routing spy and compatibility fixes; Ruff clean).
- [x] (2026-08-01) Completed architecture/SPEC review; restored legacy gateway DTO exports, corrected the orchestrator factory to accept the service protocol, and added a CLI gateway-routing assertion.
- [x] (2026-08-01) Ran the full suite (1,032 passed, one existing Pillow deprecation warning), preview and signed release-fidelity matrices, `git diff --check`, and the process/window cleanup audit.
- [x] (2026-08-01) Updated README, architecture documentation, and this plan to describe the application-owned orchestrator, compatibility gateway/session, CLI routing, retained execution adapters, lifecycle/artifact contracts, and residual debt.
- [ ] Commit the completed slice (parent agent owns commit/handoff).

## Surprises & Discoveries

- Observation: the existing gateway already has the desired two-entry shape, but its dispatch logic and request types live in `phase3_evidence_gateway.py` while the service owns normalization and aggregate evidence behavior.
  Evidence: `Phase3EvidenceGateway.run()` dispatches four operation kinds at `src/foliaseal/application/phase3_evidence_gateway.py:108-135`; `Phase3EvidenceService` owns typed matrix normalization and aggregate signed evidence at `src/foliaseal/application/phase3_evidence_service.py:164-303`.
- Observation: preview and signed matrix execution contexts cannot be safely merged in one pass.
  Evidence: preview is headless and uses `HeadlessPhase3HarnessWorkspaceAdapter`, while signed acceptance creates Qt bindings, a shell, a lifecycle, and a signing executor; signed cleanup is guarded by `finally` in `phase3_signed_acceptance_matrix_runner.py`.
  Resolution: unify request dispatch and validation only; retain separate execution adapters and their existing lifecycle ownership.
- Observation: artifact summary behavior differs between preview and signed matrices.
  Evidence: preview writes `summary.json` directly and the service normalizer supplies a fallback path; signed uses `Phase3MatrixArtifactPort` and writes twice to establish authoritative `summary_json_path`.
  Resolution: do not alter runner artifact logic or summary schemas in this slice.
- Observation: `Phase3HarnessSessionRunner` has a different interactive lifecycle than the signed matrix runner.
  Evidence: interactive capture owns `app.exec()` and session/report choreography in `phase3_harness.py`, while signed matrix explicitly closes its lifecycle in `finally`.
  Resolution: the orchestrator must delegate interactive capture unchanged; lifecycle cleanup improvements beyond the existing runner contracts are deferred unless a boundary test exposes a regression.
- Observation: the first broad focused-test command named a nonexistent `test_phase3_matrix_artifacts.py` file.
  Resolution: the repository has no standalone matrix-artifact test module; the valid focused command uses the existing evidence, runner, lifecycle, scenario, gateway, service, parser, and CLI test modules listed in `Concrete Steps`.
- Observation: existing CLI tests return lightweight `SimpleNamespace` result doubles rather than `Phase3MatrixResult` instances.
  Resolution: the CLI keeps attribute-based output formatting and does not add a runtime result-type assertion, preserving the previous test and extension contract.
- Observation: the compatibility review found that several DTOs had been exposed as imported module attributes from `phase3_evidence_gateway.py` even though they were not defined there.
  Resolution: the gateway now explicitly re-exports those legacy names in `__all__` while the orchestrator owns their definitions.
- Observation: the orchestrator's first factory annotation narrowed the protocol boundary to the concrete service.
  Resolution: `orchestrator_for_service()` now accepts `Phase3EvidenceServicePort`, preserving dependency inversion and test fakes.

## Decision Log

- Decision: Create `src/foliaseal/application/phase3_evidence_orchestrator.py` rather than expanding the Qt harness facade.
  Rationale: the durable boundary belongs beside the existing application evidence service; importing Qt/PyHanko/Pillow into the new module would recreate the coupling this slice is intended to hide.
  Date/Author: 2026-08-01 / Codex.
- Decision: Move `Phase3OperationKind`, `Phase3OperationRequest`, `Phase3ValidationRequest`, and `Phase3EvidenceServicePort` into the application orchestrator module and re-export them from the gateway.
  Rationale: request ownership must move with dispatch, while old imports remain valid for callers and tests.
  Date/Author: 2026-08-01 / Codex.
- Decision: Keep `Phase3EvidenceGateway` and `Phase3EvidenceSession` as compatibility facades.
  Rationale: existing application callers use `gateway_for_service()`, `for_pdf()`, and convenience methods; removing them would mix architectural consolidation with API migration.
  Date/Author: 2026-08-01 / Codex.
- Decision: Route CLI operations through `Phase3EvidenceGateway`/`Phase3EvidenceOrchestrator`, but leave `Phase3EvidenceService` typed methods intact.
  Rationale: the service remains the composition/normalization adapter for existing runners, while the CLI proves that new callers use the canonical application boundary without changing raw result contracts.
  Date/Author: 2026-08-01 / Codex.
- Decision: Do not force preview and signed runners into one lifecycle or scenario engine in this slice.
  Rationale: their current dependencies and artifact semantics differ materially; a forced merger would increase risk without improving the caller boundary.
  Date/Author: 2026-08-01 / Codex.

## Outcomes & Retrospective

Implementation and validation are complete for the application-boundary slice. The focused
service/runner/CLI slice passed 59 tests; the full suite passed 1,032 tests with one existing
Pillow deprecation warning. The preview release matrix ran 8 scenarios with 0 error rows. The
signed release matrix ran 8 scenarios with 6 successful signings, 2 matched intentional
rejections, 0 expected-outcome mismatches, 0 cryptographic failures, 0 preview-comparison
failures, 0 annotation-rectangle mismatches, and acceptance expectations passed. Ruff and
`git diff --check` passed. The final cleanup audit found no FoliaSeal/Phase 3 Python processes
and no GUI windows. Architecture/SPEC review initially found stale ownership docs, a concrete
factory annotation, missing gateway DTO re-exports, and absent CLI routing coverage; all were
fixed and revalidated. Documentation now records canonical orchestrator ownership, gateway and
session compatibility, CLI routing, lifecycle/artifact contracts, and residual runner-specific
complexity plus compatibility aliases. No Qt/PyHanko/Pillow types are directly imported by the
orchestrator module.

## Context and Orientation

`src/foliaseal/application/phase3_evidence_service.py` defines the existing Phase 3 request/result data: `Phase3HarnessCaptureRequest`, `Phase3MatrixRequest`, `Phase3MatrixResult`, `Phase3SignedAcceptanceEvidenceRequest`, and related typed result values. It owns runner injection, matrix result normalization, aggregate signed-acceptance evidence, and capture-contract validation.

`src/foliaseal/application/phase3_evidence_gateway.py` currently defines the tagged `Phase3OperationRequest`, `Phase3OperationKind`, `Phase3ValidationRequest`, `Phase3EvidenceGateway`, and document-bound `Phase3EvidenceSession`. Its public methods are already the intended caller shape, but dispatch is implemented inside the gateway rather than in a standalone application module.

`src/foliaseal/presentation/qt/phase3_harness.py` is the concrete composition root. `Phase3Harness` exposes interactive, preview-matrix, and signed-acceptance ports. Its interactive runner owns Qt binding loading, viewer/signing workflow construction, session execution, capture assembly, report finalization, checklist writing, and artifact compatibility. The preview runner is headless; the signed runner creates a Qt lifecycle and must close it in `finally`.

`src/foliaseal/presentation/qt/phase3_matrix_artifacts.py` provides filesystem and memory artifact ports. The signed matrix uses the artifact port to establish an authoritative summary path; the preview matrix writes its own summary and relies on service normalization for the fallback path. These details are externally visible and must not be changed.

`src/foliaseal/__main__.py` parses stable Phase 3 commands and currently calls `Phase3EvidenceService` methods directly. The CLI prints stable labels and summary paths; it must continue doing so after routing through the gateway/orchestrator.

## Plan of Work

Create `src/foliaseal/application/phase3_evidence_orchestrator.py`. Move the tagged request vocabulary and service protocol into this module, importing only application DTOs and the evidence-contract result type. Define `Phase3EvidenceOrchestrator` with two methods: `run(request: Phase3OperationRequest) -> object` and `validate(request: Phase3ValidationRequest) -> EvidenceContractEvaluation`. Dispatch all four existing operation kinds, validate payload types before calling the service port, and preserve the existing error messages and return objects. The module must not import Qt, PyHanko, Pillow, TSA, filesystem artifact implementations, or presentation modules.

Update `src/foliaseal/application/phase3_evidence_gateway.py` to import and re-export the moved request/protocol names. Keep `Phase3EvidenceGateway(service=...)` constructor compatibility, but delegate `run()` and `validate()` to a `Phase3EvidenceOrchestrator` constructed from the same service. Keep `Phase3EvidenceSession`, `gateway_for_service()`, convenience methods, type checks, and default artifact/checklist paths unchanged.

Update `src/foliaseal/__main__.py` with a small `_build_phase3_evidence_gateway()` composition helper. Route Phase 3 capture, preview matrix, signed matrix, aggregate evidence, and validation branches through `Phase3OperationRequest` or `Phase3ValidationRequest`. Keep existing typed result checks, printed labels, return codes, exceptions, and request builders. Do not change parser arguments or command names.

Add `tests/unit/test_phase3_evidence_orchestrator.py` using a fake `Phase3EvidenceServicePort`. Prove all four operation kinds dispatch to the correct service method, wrong payload types fail before service calls, validation delegates to `validate_harness_capture`, and service return objects pass through unchanged. Add compatibility coverage proving `Phase3EvidenceGateway` and `Phase3EvidenceSession` still behave identically. Extend CLI tests only where needed to prove commands route through the gateway and preserve output labels/paths; retain existing service normalization tests.

Do not move scenario execution, snapshotters, report rendering, artifact writing, Qt lifecycle code, manifest schemas, or signed/preview summary fields. Those are separate adapters and remain behind the service/harness composition in this slice.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Baseline:

    git status --short --branch
    .venv/bin/pytest -q tests/unit/test_phase3_evidence_gateway.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_cli_parser.py tests/unit/test_main_cli.py

After implementation:

    .venv/bin/ruff check src/foliaseal/application/phase3_evidence_orchestrator.py src/foliaseal/application/phase3_evidence_gateway.py src/foliaseal/__main__.py tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_phase3_evidence_gateway.py tests/unit/test_main_cli.py
    .venv/bin/pytest -q tests/unit/test_phase3_evidence_orchestrator.py tests/unit/test_phase3_evidence_gateway.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_cli_parser.py tests/unit/test_main_cli.py

Final validation:

    .venv/bin/pytest -q
    git diff --check

Run the existing release-fidelity commands with artifacts under `/tmp`:

    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-preview-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-orchestrator-preview
    QT_QPA_PLATFORM=offscreen .venv/bin/python -m foliaseal phase3-signing-acceptance-matrix --pdf-path artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf --certificate-path artifacts/generated_acceptance_assets/signed_acceptance_identity.p12 --passphrase secret --scenario-manifest-path tests/fixtures/phase3/release_fidelity_manifest.json --artifacts-dir /tmp/foliaseal-orchestrator-signed

Expect eight preview scenarios with zero error rows, and eight signed scenarios with six successful signings, two matched intentional rejections, zero expected-outcome mismatches, cryptographic failures, preview-comparison failures, and annotation-rectangle mismatches.

Finish with:

    git status --short
    ps -eo pid=,comm=,args= | awk '$2 ~ /python/ && $0 ~ /foliaseal|phase3/ {print}'
    wmctrl -l 2>/dev/null || true

## Validation and Acceptance

The slice is accepted when the application-owned orchestrator dispatches every existing Phase 3 operation and validation request, `Phase3EvidenceGateway` and `Phase3EvidenceSession` remain compatible, and the CLI routes through that boundary without changing command names, printed output, exit behavior, result summaries, or artifact paths. The orchestrator module must remain free of Qt, PyHanko, Pillow, TSA, and presentation imports.

All new orchestrator tests and existing gateway/service/runner/CLI tests must pass. The full suite must remain green. The preview and signed release-fidelity matrices must preserve their expected scenario counts and zero-tolerance counters. The final process/window audit must show no FoliaSeal/Phase 3 Python processes and no leftover GUI windows. No generated PDFs, images, logs, or `/tmp` artifacts may be committed.

## Idempotence and Recovery

The change is additive and safe to rerun. Keep all matrix output under `/tmp`. If moving request names creates import cycles, keep service DTO imports one-way: the orchestrator may import service DTOs, the gateway may import and re-export orchestrator types, and the service may retain only a `TYPE_CHECKING` reference to the session. If CLI tests fail because they patch the service builder, update the tests to patch the new gateway composition helper while retaining a compatibility test for the service builder. Do not change runner artifact logic to make tests easier; preserve the preview fallback path and signed authoritative summary path. Never use destructive Git commands.

## Artifacts and Notes

Tracked artifacts are the new application orchestrator, gateway/CLI routing changes, focused boundary tests, README/architecture updates, and this ExecPlan. Generated matrix artifacts remain in `/tmp`. At completion, record the exact test counts, matrix counters, compliance findings, cleanup audit, and commit hashes here.

## Interfaces and Dependencies

In `src/foliaseal/application/phase3_evidence_orchestrator.py`, define:

    class Phase3EvidenceServicePort(Protocol):
        def capture_harness(self, request: Phase3HarnessCaptureRequest) -> object: ...
        def preview_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult: ...
        def signed_acceptance_matrix_result(self, request: Phase3MatrixRequest) -> Phase3MatrixResult: ...
        def run_signed_acceptance_evidence(self, request: Phase3SignedAcceptanceEvidenceRequest) -> Phase3SignedAcceptanceEvidenceResult: ...
        def validate_harness_capture(self, request: Phase3HarnessValidationRequest) -> EvidenceContractEvaluation: ...

    class Phase3EvidenceOrchestrator:
        def run(self, request: Phase3OperationRequest) -> object: ...
        def validate(self, request: Phase3ValidationRequest) -> EvidenceContractEvaluation: ...

The orchestrator owns only dispatch, payload validation, and the application boundary. Concrete runner behavior remains injected through `Phase3EvidenceServicePort`. `Phase3EvidenceGateway` re-exports the request vocabulary and remains the compatibility/session facade.

## Revision Note

2026-08-01 / Codex: Created after fresh explorer-light reconnaissance selected the minimal application orchestrator plus common matrix caller hybrid. The slice intentionally preserves separate preview/headless, signed/Qt, and interactive capture adapters rather than merging incompatible lifecycles.
