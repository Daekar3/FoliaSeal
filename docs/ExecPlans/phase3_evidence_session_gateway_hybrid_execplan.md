# Add a reusable Phase 3 evidence session gateway

This ExecPlan is a living document and must be maintained according to `.agents/skills/write-execplan/PLANS.md`. It defines one complete implementation slice: add a Qt-free `Phase3EvidenceGateway` with two top-level entry points (`run` and `validate`) and four explicit `run` operation kinds, plus a reusable per-document `Phase3EvidenceSession`, while preserving every existing `Phase3EvidenceService`, `Phase3Harness`, runner, result schema, artifact path, and CLI compatibility contract.

## Purpose / Big Picture

Phase 3 QA callers currently rebuild the same PDF path, certificate path, passphrase, manifest path, and artifact-directory request objects for every operation. After this slice, a caller can bind those document-level inputs once and run explicit operations through a small session:

    service = build_default_phase3_evidence_service()
    session = Phase3EvidenceGateway(service).for_pdf(
        "input.pdf",
        certificate_path="demo-cert.p12",
        passphrase="demo-passphrase",
        artifacts_dir="artifacts/phase3",
    )
    preview = session.preview("preview-manifest.json")
    signed = session.signed_acceptance("signed-manifest.json")

The session delegates to the existing service and runners, so the observable result remains the same typed `Phase3MatrixResult` or `Phase3HarnessCapture`, with the same summary JSON/checklist paths and cleanup behavior. Existing CLI subcommands and old service/facade verbs continue to work unchanged.

## Child ExecPlan Dependencies

There are no child ExecPlans. The existing `Phase3EvidenceService`, Phase 3 runners, lifecycle ports, artifact ports, and compatibility wrappers are the required prerequisites and are already present.

## Progress

- [x] (2026-07-31) Re-explored the current checkout with an `explorer-light` agent and confirmed `Phase3EvidenceService` is the existing application boundary.
- [x] (2026-07-31) Chosen design: per-document session convenience API backed by a two-operation gateway, with legacy wrappers preserved.
- [x] (2026-07-31) Wrote this one-slice ExecPlan after verifying current DTOs, default paths, runners, and CLI dispatch.
- [x] (2026-07-31) Added the gateway/session module and typed request dispatch.
- [x] (2026-07-31) Added `Phase3EvidenceService.for_pdf()` convenience construction without changing existing methods.
- [x] (2026-07-31) Added boundary tests for dispatch, default resolution, credential propagation, and compatibility results; gateway/service tests pass 11 tests.
- [x] (2026-07-31) Corrected the malformed lifecycle cleanup indentation discovered during compatibility imports; the Phase 3 compatibility set now passes 122 tests.
- [x] (2026-07-31) Ruff passed for the new gateway/service/test files; the complete Phase 3 compatibility run (including gateway tests) passes 133 tests with one existing Pillow warning.
- [x] (2026-07-31) Ran the complete suite; 1,009 tests passed in 45.09 seconds with one existing Pillow deprecation warning.
- [x] (2026-07-31) Compliance review found missing architecture/README documentation, a weak `Any` service return annotation, and gateway terminology drift; all were corrected. `docs/SPEC.md` has no Phase 3 API requirement.
- [x] (2026-07-31) Updated `docs/ARCHITECTURE.md` and `README.md` with the gateway/session contracts, defaults, usage, and compatibility rules.
- [x] (2026-07-31) Committed the complete slice as `42c60a8b9` (`Add reusable Phase 3 evidence gateway session`); the final plan-status amendment is ready to fold into that commit.

## Surprises & Discoveries

- Observation: `Phase3EvidenceService` already owns the typed matrix normalization and signed-evidence aggregate; the new gateway should wrap it instead of moving runner logic.
  Evidence: `src/foliaseal/application/phase3_evidence_service.py` exposes raw runner methods plus `preview_matrix_result()` and `signed_acceptance_matrix_result()`.
- Observation: The Phase 3 CLI has no harness API mandated by `docs/SPEC.md`; the stable contracts are the architecture documentation, tests, summary JSON fields, and CLI output.
  Evidence: the explorer found no Phase 3/harness API requirements in `docs/SPEC.md`.
- Observation: Signed acceptance runner cleanup is already guarded by its own lifecycle `finally` block; the session must not duplicate or bypass that lifecycle.
  Evidence: `phase3_signed_acceptance_matrix_runner.py` closes its lifecycle after scenario execution and summary publication.
- Observation: The first Phase 3 compatibility import exposed a malformed indentation in the previously committed lifecycle helper's cleanup exception handler.
  Evidence: importing `presentation/qt` failed with `SyntaxError: expected 'except' or `finally' block` at `signing_workspace_lifecycle.py`; indenting the handler restored imports and the compatibility suite passed 122 tests.

## Decision Log

- Decision: Place the new gateway/session in `src/foliaseal/application/phase3_evidence_gateway.py` and depend on a narrow service protocol rather than Qt or runner classes.
  Rationale: The session is a caller-facing application convenience boundary; Qt, PyHanko, Pillow, Poppler, TSA, and artifact implementations must remain behind the existing service composition root.
  Date/Author: 2026-07-31 / Codex.
- Decision: Expose two top-level gateway entry points, `run(request)` and `validate(request)`, with four tagged `run` kinds and explicit `preview()`, `signed_acceptance()`, `capture()`, and `validate()` methods on the per-document session.
  Rationale: The gateway keeps operation dispatch centralized while the session makes the common QA path discoverable and avoids a mode-string API.
  Date/Author: 2026-07-31 / Codex.
- Decision: Keep `Phase3EvidenceService`, `Phase3Harness`, raw dictionary methods, typed result methods, and all CLI commands intact; add only a `for_pdf()` convenience method to the service.
  Rationale: Existing callers and tests depend on those names and exact result/summary contracts. The new session is additive and can be adopted incrementally.
  Date/Author: 2026-07-31 / Codex.
- Decision: Use `artifacts/phase3` as the session’s default artifact directory for matrix/capture operations when the caller does not provide one, while preserving explicit request values and all legacy request defaults.
  Rationale: A reusable session must resolve a stable common default, but old service/CLI behavior must not be changed.
  Date/Author: 2026-07-31 / Codex.
- Decision: Do not refactor matrix runners, event streams, open-ended evidence DTOs, or CLI flags in this slice.
  Rationale: Those are future deepening opportunities; changing them would widen this slice beyond a safe gateway/session vertical path.
  Date/Author: 2026-07-31 / Codex.

## Outcomes & Retrospective

Implementation and compliance review are complete. Focused gateway/service tests pass (11 tests),
the Phase 3 compatibility set passes (133 tests), Ruff and `git diff --check` are clean, and the
complete suite passes (1,009 tests, one pre-existing Pillow deprecation warning). The session returns
the same typed matrix results and artifact paths as equivalent legacy service calls; per-call artifact
overrides and the `artifacts/phase3` default are covered by boundary tests. Documentation is updated
in `docs/ARCHITECTURE.md` and `README.md`. Commit `42c60a8b9` contains the implementation, the
necessary lifecycle syntax correction, tests, documentation, and this plan. Future work may deepen
runner ports or CLI migration, but remains outside this slice.

## Context and Orientation

`src/foliaseal/application/phase3_evidence_service.py` defines the existing application boundary. Its request DTOs are `Phase3HarnessCaptureRequest`, `Phase3MatrixRequest`, `Phase3SignedAcceptanceEvidenceRequest`, and `Phase3HarnessValidationRequest`. Its result DTOs include `Phase3MatrixResult` and `Phase3SignedAcceptanceEvidenceResult`; the interactive `Phase3HarnessCapture` schema is defined in `src/foliaseal/presentation/qt/phase3_harness.py` and is returned without changing its fields.

`Phase3EvidenceService` delegates capture to `Phase3Harness`, preview and signed matrices to their runners, signed-evidence aggregation to its asset generator and matrix runner, and validation to its capture loader/evaluator. Matrix runners own Qt lifecycle, scenario execution, artifact writing, summary counters, and `finally` cleanup. The new gateway must call these existing service methods and must not import Qt, PyHanko, Pillow, or runner-private helpers.

`src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` builds the production `Phase3EvidenceService`; `src/foliaseal/__main__.py` builds that service for CLI dispatch. Existing CLI commands require explicit paths for preview/signed matrices and print typed result fields. Their arguments, output labels, and exit/error behavior are compatibility contracts.

## Plan of Work

Create `src/foliaseal/application/phase3_evidence_gateway.py`. Define `Phase3OperationKind` with `CAPTURE`, `PREVIEW_MATRIX`, `SIGNED_ACCEPTANCE_MATRIX`, and `SIGNED_ACCEPTANCE_EVIDENCE`. Define `Phase3OperationRequest` containing a kind and one existing service request payload, with classmethods for each valid operation. Define `Phase3ValidationRequest` containing `summary_json_path`. Define a `Phase3EvidenceServicePort` protocol covering the service methods needed by the gateway. `Phase3EvidenceGateway.run()` dispatches the tagged request to the matching service method and raises a clear `TypeError` when the tag/payload pairing is invalid. `validate()` delegates to `validate_harness_capture()`.

In the same module, define `Phase3EvidenceSession` as an immutable document-bound facade with `pdf_path`, `certificate_path`, `passphrase`, `artifacts_dir`, and a gateway. Its `preview(manifest_path, artifacts_dir=None)` and `signed_acceptance(manifest_path, artifacts_dir=None)` methods build `Phase3MatrixRequest` objects and return typed matrix results through `gateway.run()`. Its `capture(summary_json_path=None, checklist_results_path=..., checklist_template_path=..., artifacts_dir=None)` method builds `Phase3HarnessCaptureRequest` and delegates it. Its `validate(summary_json_path)` method delegates to the gateway validation operation. Add `Phase3EvidenceGateway.for_pdf(...)` to construct this session, defaulting `artifacts_dir` to `artifacts/phase3`.

Add `Phase3EvidenceService.for_pdf(...)` as a convenience method that imports or constructs `Phase3EvidenceGateway(self)` and returns the session. This keeps the existing service as the production composition root while giving callers a discoverable migration path. Do not alter the behavior or signatures of existing service methods.

Add `tests/unit/test_phase3_evidence_gateway.py`. Use a fake service implementing the protocol and assert that each operation routes to the matching legacy method, invalid tag/payload pairings fail clearly, and validation passes the requested summary path. Test a session with one PDF/certificate/passphrase: preview and signed acceptance each receive the correct manifest and default/override artifact directory; capture receives the correct checklist/summary paths; validation delegates correctly; and all returned objects are passed through unchanged. Add a service convenience test showing `Phase3EvidenceService.for_pdf()` returns a usable session without changing legacy method behavior.

Update `docs/ARCHITECTURE.md` to document the application gateway/session component, its contracts, default artifact behavior, and the rule that legacy service/facade/CLI wrappers remain stable adapters. Update `README.md` only if its Phase 3 examples would otherwise omit or contradict the new session usage; do not rewrite existing CLI instructions.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

1. Write the new boundary test and run it before implementation:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_evidence_gateway.py

   Expected initial result: collection fails because the new module does not exist. This is the deliberate red step.

2. Implement the gateway/session and service convenience method. Run the tracer tests:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_evidence_gateway.py tests/unit/test_phase3_evidence_service.py

   Expected result: all gateway and existing service tests pass, with exact request forwarding and unchanged typed summaries.

3. Run the Phase 3 compatibility boundary set:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_preview_matrix_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_signed_acceptance_scenario_executor.py tests/unit/test_main_cli.py

4. Run static and repository checks:

    .venv/bin/python -m ruff check src/foliaseal/application/phase3_evidence_gateway.py src/foliaseal/application/phase3_evidence_service.py tests/unit/test_phase3_evidence_gateway.py
    git diff --check
    git status --short

5. Run the complete suite:

    .venv/bin/python -m pytest -q

   Expected result: all existing tests plus the new gateway tests pass. Any pre-existing Pillow warning must remain the only warning unless the plan records a new cause.

6. After compliance review and documentation updates, stage only the gateway module, service edit, gateway tests, architecture/README documentation if changed, and this ExecPlan for one coherent commit.

## Validation and Acceptance

The slice is accepted when a caller can bind one PDF, certificate, passphrase, and artifact directory through `Phase3EvidenceGateway.for_pdf()` and invoke `preview()`, `signed_acceptance()`, `capture()`, and `validate()` without manually rebuilding request DTOs. Each call must delegate to the existing service and return the same result object shape and artifact path values as the equivalent legacy call. Explicit per-call artifact directories must override the session default.

All existing `Phase3EvidenceService` methods, `Phase3Harness` methods, raw matrix mappings, typed matrix results, signed-evidence aggregate results, CLI flags, printed labels, and lifecycle cleanup behavior must remain unchanged. The new boundary tests must pass, the Phase 3 compatibility set must pass, the full suite must pass, and `ruff`/`git diff --check` must be clean.

## Idempotence and Recovery

The gateway is additive and has no persistent migration. Re-running tests uses fakes and temporary paths. If an operation-routing test fails, inspect the tagged request/payload pairing before changing legacy service behavior. If a full-suite regression appears, revert only the new gateway call sites or service convenience method; do not alter runner summary fields or generated artifacts. Do not use destructive Git commands.

## Artifacts and Notes

Preserve the focused test transcript, full-suite count, ruff result, and final commit hash in this plan. No generated Phase 3 artifacts belong in the commit. The gateway’s default `artifacts/phase3` directory is a path convention only; tests should use temporary overrides.

## Interfaces and Dependencies

The new module must expose these stable interfaces:

    class Phase3EvidenceGateway:
        def run(self, request: Phase3OperationRequest) -> object: ...
        def validate(self, request: Phase3ValidationRequest) -> EvidenceContractEvaluation: ...
        def for_pdf(
            self,
            pdf_path: str,
            *,
            certificate_path: str,
            passphrase: str,
            artifacts_dir: str = "artifacts/phase3",
        ) -> Phase3EvidenceSession: ...

    @dataclass(frozen=True)
    class Phase3EvidenceSession:
        def preview(self, manifest_path: str, *, artifacts_dir: str | None = None) -> Phase3MatrixResult: ...
        def signed_acceptance(self, manifest_path: str, *, artifacts_dir: str | None = None) -> Phase3MatrixResult: ...
        def capture(...): ...
        def validate(self, summary_json_path: str) -> EvidenceContractEvaluation: ...

The gateway may import only standard-library typing/dataclasses/enums and existing application DTOs/results. The injected service port is local-substitutable in tests; production uses `Phase3EvidenceService`. Qt, PyHanko, Pillow, Poppler, TSA, and filesystem artifact implementations remain behind the existing service and runner adapters. `Phase3HarnessCapture` may remain an opaque return type at the application boundary because its stable schema is owned by the presentation harness module.

## Change-slice Boundaries

The primary change class is behavior: a reusable Phase 3 evidence caller boundary. The same commit includes architecture documentation because it records a new public application contract. Do not mix event-stream redesign, generic extension registries, runner lifecycle rewrites, manifest schema changes, CLI flag changes, visible-signature layout work, GUI changes, or generated artifacts into this slice.

Plan revision note (2026-07-31): created after the live explorer confirmed that the existing service/runner/lifecycle boundaries are stable; scoped the implementation to an additive session/gateway wrapper rather than moving runner orchestration or changing evidence schemas.
