# Consolidate Matrix Evidence And CLI Dispatch Behind The Phase 3 Evidence Service

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This slice is complete. The preview matrix, signed-acceptance matrix, signed-acceptance evidence command, and capture-validation command all call through one explicit Phase 3 evidence service. The public commands and artifact outputs stayed stable, and `src/foliaseal/__main__.py` now behaves as a dispatcher instead of a second orchestration layer.

This is the slice that finishes the hybrid `3+4` direction: explicit caller-facing verbs with internally injected adapters for Qt boot, matrix execution, and artifact writing.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_reporting_boundary_execplan.md` is complete.
- [x] `docs/ExecPlans/phase3_harness_session_runner_execplan.md` is complete.

## Progress

- [x] The explicit Phase 3 evidence service and thin CLI dispatch path are in place.
- [x] The signed-acceptance evidence wrapper now delegates through the service boundary instead of acting as a peer orchestrator.
- [x] `src/foliaseal/__main__.py` now builds request objects and dispatches through the service for harness, matrix, evidence, and validation commands.

## Surprises & Discoveries

- Observation: the service boundary is small, but it is still the right place to own the caller-facing request/result types.
  Evidence: `src/foliaseal/application/phase3_evidence_service.py` now owns the request dataclasses, result dataclasses, matrix-summary validation, and the evidence-summary writer path.

- Observation: the CLI and wrapper layers are now intentionally thin.
  Evidence: `src/foliaseal/__main__.py` routes every Phase 3 workflow through `build_default_phase3_evidence_service()`, and `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` just filters known chatter and supplies default request wiring.

## Decision Log

- Decision: keep the command names and output paths stable while moving orchestration behind the service.
  Rationale: the user-visible evidence workflow was already documented and tested; only the ownership of orchestration needed to move.
  Date/Author: 2026-06-03 / Codex

## Outcomes & Retrospective

This slice is complete. The CLI-facing evidence flows now have a single application-layer service boundary, the wrapper module is thin, and the documented command outputs remain unchanged.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` still exports the preview-matrix and signed-acceptance matrix runners directly, but the CLI-facing orchestration now routes through `src/foliaseal/application/phase3_evidence_service.py`. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` is now a thin wrapper/client around that service, and `src/foliaseal/__main__.py` dispatches through the service for the Phase 3 harness, matrix, evidence, and validation commands.

The prior child plans established smaller reporting and session-runner boundaries. This final child plan wrapped those boundaries and the matrix flows in one explicit service with caller-facing verbs such as capture harness, run preview matrix, run signed acceptance evidence, and validate capture.

## Plan of Work

Complete the explicit service module that owns Phase 3 evidence orchestration. Give it a caller-friendly surface with explicit methods rather than a generic mode flag. Internally, inject or wrap the concrete Qt boot path, matrix execution path, artifact writer, asset generator, and evidence contract evaluator.

`src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` now acts as a client of the service rather than a peer orchestrator. `src/foliaseal/__main__.py` now builds request objects, calls the service, and prints concise summaries. Command names, exit behavior, and documented output paths were preserved.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Expected edit surfaces:

    src/foliaseal/presentation/qt/phase3_harness.py
    src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py
    src/foliaseal/__main__.py
    tests/unit/test_phase3_harness.py
    tests/unit/test_main_cli.py
    tests/unit/test_qa_signed_acceptance_evidence.py
    docs/ExecPlans/phase3_evidence_service_and_cli_execplan.md
    docs/ExecPlans/phase3_evidence_service_program_execplan.md

## Validation and Acceptance

This slice is accepted. The Phase 3 CLI commands still behave the same for users, but the implementation path now routes through one explicit service boundary with direct tests that no longer need broad orchestration patching.

## Idempotence and Recovery

The compatibility wrapper was kept thin and should not be expanded. Do not reintroduce a second long-term orchestrator in parallel.

## Artifacts and Notes

Allowed changes:

- architecture change in the Phase 3 evidence path,
- narrowly related test updates,
- architecture/doc status updates.

Forbidden changes:

- unrelated GUI shell changes,
- acceptance-schema changes that are not required by the new service boundary.

## Interfaces and Dependencies

The end state exposes explicit caller-facing request/result types and service methods, with internally injected adapters for Qt bootstrapping, matrix execution, artifact writing, and asset generation. The dependency strategy is the full hybrid:

- external surface shaped like Design 3, with explicit verbs,
- internal dependency handling shaped like Design 4, with adapter seams around concrete Qt and filesystem behavior.

Revision note: created on 2026-06-03 as child plan 3 of the Phase 3 evidence-service program; completed on 2026-06-03 after the service boundary and CLI dispatch landed.
