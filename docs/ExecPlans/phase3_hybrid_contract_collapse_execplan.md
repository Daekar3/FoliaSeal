# Collapse The Phase 3 Hybrid To One Application Contract

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this collapse, the Phase 3 evidence stack has one caller-facing contract in the application layer instead of three overlapping ones in the application layer, Qt harness module, and signed-acceptance wrapper. A contributor invokes harness capture, preview matrices, signed-acceptance matrices, signed-acceptance evidence generation, and capture validation through `src/foliaseal/application/phase3_evidence_service.py` request objects and service verbs, while the Qt harness module acts as an internal adapter that only owns Qt-backed execution details.

The user-visible behavior must stay the same. The commands `foliaseal phase3-signing-harness`, `foliaseal phase3-signing-preview-matrix`, `foliaseal phase3-signing-acceptance-matrix`, `foliaseal phase3-signing-acceptance-evidence`, and `foliaseal phase3-signing-harness-validate` must keep their current arguments, printouts, artifact paths, and summary shapes. The proof is that focused unit suites keep passing, the architecture document no longer describes duplicate public contracts, and the remaining public seams are small enough that the next `$improve-codebase-architecture` pass can rank a new seam instead of rediscovering this unfinished one.

## Child ExecPlan Dependencies

- [x] (2026-07-04 00:00Z) `docs/ExecPlans/phase3_evidence_service_program_execplan.md` is complete and establishes the application service boundary plus the earlier hybrid `3+4` direction.
- [x] (2026-07-04 00:00Z) `docs/ExecPlans/phase3_harness_facade_signed_acceptance_execplan.md` is complete and records the interim `Phase3Harness` facade tracer bullet that the collapse later superseded.
- [x] (2026-07-04 00:00Z) `docs/ExecPlans/phase3_harness_facade_interactive_execplan.md` is complete and records the interim interactive caller surface that the collapse later superseded.
- [x] (2026-07-04 00:00Z) No child ExecPlans are planned for this pass. This document covers the entire consolidation so the seam is ready for a fresh architecture ranking.

## Progress

- [x] (2026-07-04 00:00Z) Re-read `.agents/skills/dev-loop/SKILL.md`, `.agents/skills/improve-codebase-architecture/SKILL.md`, `.agents/skills/write-execplan/SKILL.md`, and `.agents/skills/write-execplan/PLANS.md`.
- [x] (2026-07-04 00:00Z) Completed the required `explorer-light` dev-loop audit for the accepted hybrid seam and confirmed the remaining problem is duplicate public contracts, not a known functional bug.
- [x] (2026-07-04 00:00Z) Re-read the current Phase 3 service, CLI, wrapper, facade, package export, and the most relevant historical ExecPlans.
- [x] (2026-07-04 00:00Z) Wrote this full-pass ExecPlan before implementation.
- [x] (2026-07-04 00:00Z) `phase3_signed_acceptance_evidence.py` no longer defines a second public orchestration surface and now provides only default service-building helpers plus runtime-noise suppression internals.
- [x] (2026-07-04 00:00Z) `Phase3Harness` consumes the application-layer request dataclasses instead of maintaining `Phase3HarnessRequest` as a second public request type.
- [x] (2026-07-04 00:00Z) Legacy free-function shims in `phase3_harness.py` and package exports are retired or demoted to internal compatibility helpers.
- [x] (2026-07-04 00:00Z) CLI dispatch routes through small service-builder/request-builder helpers so `src/foliaseal/__main__.py` no longer duplicates the Phase 3 command-to-request contract inline.
- [x] (2026-07-04 00:00Z) Focused tests assert the new contract ownership and no longer exist solely to protect transitional shims.
- [x] (2026-07-04 00:00Z) `docs/ARCHITECTURE.md` and the stale ExecPlan notes were reconciled with the final ownership split.
- [x] (2026-07-04 00:00Z) Focused validation passed: `.venv/bin/python -m pytest -q tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py tests/unit/test_qa_signed_acceptance_evidence.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`.
- [x] (2026-07-04 00:00Z) Completed the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan. Reviewer findings exposed one real CLI wiring bug (signed-acceptance evidence passphrase forwarding), one remaining Qt export/helper leak, and one stale architecture type-table row; all were fixed in the same pass and the focused validation suite stayed green.
- [x] (2026-07-04 00:00Z) Created the required git commit after the compliance review was complete: `2366544b8d6a84d34351120bee2c10f795a88cb5` (`Collapse Phase 3 hybrid contract`).

## Surprises & Discoveries

- Observation: the current seam now has the right long-term application boundary and the intermediate facade has been collapsed.
  Evidence: `src/foliaseal/application/phase3_evidence_service.py` owns request/result types and service verbs, while `src/foliaseal/presentation/qt/phase3_harness.py` is now an adapter/composition root that consumes application-layer request dataclasses and no longer publishes `Phase3HarnessRequest` or stable free-function wrappers.

- Observation: `docs/SPEC.md` constrains this pass mostly by what it forbids, not by naming the harness modules directly.
  Evidence: `docs/SPEC.md` says preview fidelity is trust-critical, live-document editing is the primary workflow, and V1 may simplify or remove lower-level secondary controls if the main flow stays clearer. This supports collapsing duplicate QA/tooling seams as long as command behavior stays intact.

- Observation: the only real behavioral regression risk surfaced in review was outside the harness adapter itself.
  Evidence: the first compliance reviewer caught that `_build_phase3_signed_acceptance_evidence_request()` in `src/foliaseal/__main__.py` had stopped forwarding the fixed generated-asset passphrase; the follow-up fix restored that wiring and added a focused CLI assertion.

## Decision Log

- Decision: finish the hybrid by converging on the application-layer service contract instead of promoting the Qt facade to a broader public API.
  Rationale: the user-selected hybrid was `Russell + Leibniz`: explicit service verbs at the application boundary, with Qt/session/workspace/reporting details hidden behind internal adapter seams. Keeping both `Phase3EvidenceService` and `Phase3Harness` as public contracts would preserve the exact duplication this refactor was designed to remove.
  Date/Author: 2026-07-04 / Codex

- Decision: keep CLI command names, parser arguments, printed summaries, and artifact file shapes stable in this pass.
  Rationale: those are documented and tested contracts. This is an architectural simplification slice, not a user-visible CLI redesign.
  Date/Author: 2026-07-04 / Codex

- Decision: treat free-function harness wrappers and package re-exports as legacy compatibility surfaces that should be removed or made explicitly internal once callers are migrated.
  Rationale: they duplicated the same workflows already owned by the service and forced test coverage to protect transitional indirection instead of the real boundary.
  Date/Author: 2026-07-04 / Codex

## Outcomes & Retrospective

Implementation, compliance review, and the final commit have landed. The outcome is a single caller-facing Phase 3 contract in `src/foliaseal/application/phase3_evidence_service.py`, a thinner Qt-backed adapter layer in `src/foliaseal/presentation/qt/phase3_harness.py`, smaller CLI dispatch helpers, updated focused tests, and reconciled documentation with no known stale references to the intermediate facade/shim state.

## Context and Orientation

The current Phase 3 evidence stack spans five files that matter for this pass. `src/foliaseal/application/phase3_evidence_service.py` is the public boundary. It defines request dataclasses for harness capture, matrix runs, signed-acceptance evidence generation, and capture validation, plus `Phase3EvidenceService` methods that execute those operations. `src/foliaseal/presentation/qt/phase3_harness.py` is the Qt-backed adapter module and composition root. It consumes the application-layer request dataclasses and delegates to extracted runners rather than defining its own public request type or caller-facing contract. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` is an internal helper module that provides default runtime-noise suppression and default service wiring for the signed-acceptance evidence flow. `src/foliaseal/__main__.py` is the CLI dispatcher and now builds service-owned requests through small helpers instead of duplicating that mapping inline. `src/foliaseal/presentation/qt/__init__.py` no longer advertises the retired free-function seam as a stable public contract.

The earlier hybrid refactor was intentionally incremental. `docs/ExecPlans/phase3_evidence_service_program_execplan.md` established the service boundary and `docs/ExecPlans/phase3_harness_facade_*` plans introduced interim facades so all harness modes used one Qt-side object. That was useful as a tracer bullet, but it left duplicate public contracts in place until the hybrid collapse removed them. The goal now is not to add another tracer bullet. The goal is to keep the documentation aligned with the final ownership so the next architecture pass can rank a different seam.

In this repository, “public contract” means a type or function that callers outside the module are expected to import or construct directly. The correct public contract is the application-layer request dataclasses and `Phase3EvidenceService` verbs. The Qt harness module owns the real execution work for interactive capture and matrix runs, but it does so as an adapter implementation detail. “Legacy shim” means a compatibility wrapper kept only to bridge older callers. Those wrappers are now treated as internal helpers rather than first-class public API in docs and tests.

The allowed change class for this pass was primarily `behavior change` only in the narrow sense of contract ownership and call routing. Artifact content, evidence schema shape, and CLI output wording remained stable except where a test or doc explicitly proved the current wording was describing a transitional shim. Evidence refreshes were not part of this slice. Documentation updates were limited to reconciliations of ownership, public entrypoints, and stale transitional notes.

## Plan of Work

Start by collapsing the signed-acceptance wrapper. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` now only provides runtime-noise suppression helpers and default service-building helpers, because those are useful adapter responsibilities. If the module still needs one tiny helper for CLI/service construction, keep it narrowly scoped and make its ownership obvious in the module docstring and exports.

Then collapse the duplicate request contract in `src/foliaseal/presentation/qt/phase3_harness.py`. `Phase3Harness` consumes the existing application-layer request dataclasses from `src/foliaseal/application/phase3_evidence_service.py` rather than publishing its own public request dataclass. Preserve the existing deeper helper boundaries already extracted from this file: the session runner, workspace adapters, capture assembler, reporting boundary, preview matrix runner, and signed-acceptance runner. Do not reopen those seams in this pass.

Next, keep the remaining harness entrypoints only where module-local composition needs concrete callables to pass into `Phase3EvidenceService`. Prefer builder helpers or adapter methods over public free-function workflow entrypoints. Any free function that survives for local composition is now treated as an internal helper rather than a public seam, and the desired end state is that callers use the service, not the free functions.

After the service and harness modules are converged, reduce duplication in `src/foliaseal/__main__.py`. The parser definitions stay as they are, because the CLI contract must remain stable. The execution branch should avoid inlining Phase 3 request construction in multiple places if a small helper can centralize that mapping cleanly. The important outcome is not a clever abstraction; it is that the CLI dispatch reads as “parse args, build the service once, build a service-owned request, call the service verb, print the stable summary.” If a helper makes validation clearer, define it in `__main__.py`; do not move parser-only logic into the service.

Once code ownership is simplified, update tests. `tests/unit/test_phase3_harness.py` should keep protecting the real Qt-backed adapter boundary, but it should stop enshrining transitional public shims as if they are the long-term API. `tests/unit/test_phase3_evidence_service.py` should remain the main caller-facing boundary proof. `tests/unit/test_main_cli.py` should continue proving the CLI contract and should be updated if helper extraction changes how requests are built. `tests/unit/test_qa_signed_acceptance_evidence.py` should be reconciled depending on whether signed-acceptance evidence remains callable through a thin wrapper helper or only through the service. Prefer deleting or rewriting tests that exist only to prove shim delegation when the shim itself is removed.

Finally, reconcile documentation. `docs/ARCHITECTURE.md` must stop describing the facade/shim split as the target end state and instead explain that the application service owns the caller-facing contract while the Qt harness module is an adapter/composition root. Review the older Phase 3 ExecPlans named in this document for stale “current state” wording and update only the notes that would mislead the next contributor about the present architecture. `docs/SPEC.md` should not need edits unless a requirement conflict appears during compliance review.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Re-read the current code before editing and locate the exact transitional surfaces.

       rg -n "Phase3HarnessRequest|run_phase3_signing_harness|run_phase3_preview_matrix|run_phase3_signed_acceptance_matrix|run_signed_acceptance_evidence|build_default_phase3_evidence_service" src/foliaseal

2. Edit the Phase 3 modules in this order so the public contract converges top-down:

       src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py
       src/foliaseal/presentation/qt/phase3_harness.py
       src/foliaseal/presentation/qt/__init__.py
       src/foliaseal/__main__.py

3. Update focused tests as soon as the code shape changes:

       tests/unit/test_phase3_evidence_service.py
       tests/unit/test_phase3_harness.py
       tests/unit/test_main_cli.py
       tests/unit/test_qa_signed_acceptance_evidence.py

4. Run focused validation before touching docs:

       .venv/bin/python -m pytest -q tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py tests/unit/test_qa_signed_acceptance_evidence.py
       .venv/bin/python -m ruff check src/foliaseal/application/phase3_evidence_service.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py src/foliaseal/presentation/qt/__init__.py src/foliaseal/__main__.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py tests/unit/test_qa_signed_acceptance_evidence.py
       git diff --check

5. Reconcile docs and rerun the compliance review:

       docs/ARCHITECTURE.md
       docs/ExecPlans/phase3_evidence_service_program_execplan.md
       docs/ExecPlans/phase3_harness_facade_interactive_execplan.md
       docs/ExecPlans/phase3_harness_facade_signed_acceptance_execplan.md
       docs/ExecPlans/phase3_hybrid_contract_collapse_execplan.md

6. Perform the required post-implementation compliance review against:

       docs/ARCHITECTURE.md
       docs/SPEC.md
       docs/ExecPlans/phase3_hybrid_contract_collapse_execplan.md

7. When the pass is complete, create the required git commit with a message that makes the contract collapse explicit.

## Validation and Acceptance

This pass is accepted when all of the following are true:

- `src/foliaseal/application/phase3_evidence_service.py` is the only caller-facing Phase 3 contract described by the architecture docs and protected as the primary public boundary by tests.
- `src/foliaseal/presentation/qt/phase3_harness.py` no longer publishes `Phase3HarnessRequest` as a second public request type.
- any surviving module-level harness callables exist only as internal adapter helpers and are no longer package-exported or treated as stable public seams.
- `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` no longer acts as a second end-user orchestration API beyond default service construction and runtime-noise suppression.
- `src/foliaseal/__main__.py` still accepts the same CLI arguments and prints the same operational summaries while routing cleanly through the service contract.
- focused tests for the service, harness adapter, CLI dispatch, and signed-acceptance evidence all pass.
- `docs/ARCHITECTURE.md` and the relevant historical ExecPlans describe the final ownership accurately enough that the next `$improve-codebase-architecture` pass can move to a new seam.

Behavioral proof is:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py tests/unit/test_qa_signed_acceptance_evidence.py

and:

    .venv/bin/python -m ruff check src/foliaseal/application/phase3_evidence_service.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py src/foliaseal/presentation/qt/__init__.py src/foliaseal/__main__.py tests/unit/test_phase3_evidence_service.py tests/unit/test_phase3_harness.py tests/unit/test_main_cli.py tests/unit/test_qa_signed_acceptance_evidence.py
    git diff --check

The compliance review must explicitly confirm that `docs/SPEC.md` remains satisfied because the main live-document workflow and preview-trust requirements are unchanged, while the QA/tooling seams are simplified.

## Idempotence and Recovery

This pass is safe to retry because it is mostly contract consolidation and routing cleanup inside one repository. If a first implementation attempt breaks callers, restore behavior by reintroducing a narrow internal adapter helper rather than re-promoting a deleted public shim. Do not recover by creating a third request dataclass or a second service wrapper. The whole point of this pass is to delete duplication, not move it.

If one sub-step exposes a deeper bug in Qt session execution, matrix iteration, or evidence rendering, stop widening this plan and fix the bug behind the existing adapter/service boundary. Do not let a bug fix turn this consolidation pass back into a broad harness redesign.

## Artifacts and Notes

Keep the most important evidence concise:

- the focused `pytest` transcript covering the four main suites,
- the `ruff` and `git diff --check` outputs,
- a short before/after note in `docs/ARCHITECTURE.md` showing that duplicate public contracts were removed,
- and the final `git status --short` before commit so the scope stays narrow.

The initial explorer audit for this pass found no obvious functional defect. The change is justified by architectural duplication and stale transitional surfaces, not by a failing user-visible scenario.

## Interfaces and Dependencies

This pass uses the `Local-substitutable` dependency category for the overall seam and preserves the earlier `ports & adapters` intent inside the implementation. At the end of the pass, the caller-facing types should remain in `src/foliaseal/application/phase3_evidence_service.py`, including:

    @dataclass(frozen=True)
    class Phase3HarnessCaptureRequest: ...

    @dataclass(frozen=True)
    class Phase3MatrixRequest: ...

    @dataclass(frozen=True)
    class Phase3SignedAcceptanceEvidenceRequest: ...

    @dataclass(frozen=True)
    class Phase3HarnessValidationRequest: ...

    class Phase3EvidenceService:
        def capture_harness(self, request: Phase3HarnessCaptureRequest) -> Any: ...
        def run_preview_matrix(self, request: Phase3MatrixRequest) -> dict[str, Any]: ...
        def run_signed_acceptance_matrix(self, request: Phase3MatrixRequest) -> dict[str, Any]: ...
        def validate_harness_capture(
            self,
            request: Phase3HarnessValidationRequest,
        ) -> EvidenceContractEvaluation: ...
        def run_signed_acceptance_evidence(
            self,
            request: Phase3SignedAcceptanceEvidenceRequest,
        ) -> Phase3SignedAcceptanceEvidenceResult: ...

`src/foliaseal/presentation/qt/phase3_harness.py` may still define a concrete adapter object if that keeps builder wiring clean, but that object must consume the service-owned request dataclasses rather than defining a second public request type. If module-level adapter helpers survive, they must be clearly internal and must not be re-exported from `src/foliaseal/presentation/qt/__init__.py`.

Revision note: Created on 2026-07-04 by Codex as the full-pass dev-loop ExecPlan for the accepted hybrid recommendation. This plan intentionally completes the contract convergence in one slice so the next architecture pass can explore a different seam instead of reopening the same Phase 3 hybrid transition.
