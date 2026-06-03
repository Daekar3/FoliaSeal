# Consolidate Matrix Evidence And CLI Dispatch Behind The Phase 3 Evidence Service

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the preview matrix, signed-acceptance matrix, signed-acceptance evidence command, and capture-validation command will all call through one explicit Phase 3 evidence service. The public commands and artifact outputs stay stable, but `src/foliaseal/__main__.py` becomes a dispatcher instead of a second orchestration layer.

This is the slice that finishes the hybrid `3+4` direction: explicit caller-facing verbs with internally injected adapters for Qt boot, matrix execution, and artifact writing.

## Child ExecPlan Dependencies

- [ ] `docs/ExecPlans/phase3_reporting_boundary_execplan.md` must be complete first.
- [ ] `docs/ExecPlans/phase3_harness_session_runner_execplan.md` must be complete first.

## Progress

- [ ] Begin after the prior child plans land.

## Surprises & Discoveries

- Observation: fill this section as the slice proceeds.
  Evidence: add concise test output or code references.

## Decision Log

- Decision: no decisions recorded yet.
  Rationale: this plan has not been implemented yet.
  Date/Author: 2026-06-03 / Codex

## Outcomes & Retrospective

This slice has not started yet.

## Context and Orientation

`src/foliaseal/presentation/qt/phase3_harness.py` currently exports the preview-matrix and signed-acceptance matrix runners directly. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` adds another orchestration layer on top of that for one-command evidence generation. `src/foliaseal/__main__.py` then dispatches directly into both families. The result is that callers still know too much about which helper to call and how its output should be summarized.

The prior child plans establish smaller reporting and session-runner boundaries. This final child plan should wrap those boundaries and the matrix flows in one explicit service with caller-facing verbs such as capture harness, run preview matrix, run signed acceptance evidence, and validate capture.

## Plan of Work

Create an explicit service module that owns Phase 3 evidence orchestration. Give it a caller-friendly surface with explicit methods rather than a generic mode flag. Internally, inject or wrap the concrete Qt boot path, matrix execution path, artifact writer, asset generator, and evidence contract evaluator.

Migrate `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` so it becomes a client of the new service rather than a peer orchestrator. Then migrate `src/foliaseal/__main__.py` so the relevant CLI commands build request objects, call the service, and print concise summaries. Preserve command names, exit behavior, and documented output paths.

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

This slice is accepted when the Phase 3 CLI commands still behave the same for users, but the implementation path is routed through one explicit service boundary with direct tests that no longer need broad orchestration patching.

## Idempotence and Recovery

If migration needs a temporary compatibility wrapper, keep it additive and remove it before closing the plan. Do not leave two long-term orchestrators in parallel.

## Artifacts and Notes

Allowed changes:

- architecture change in the Phase 3 evidence path,
- narrowly related test updates,
- architecture/doc status updates.

Forbidden changes:

- unrelated GUI shell changes,
- acceptance-schema changes that are not required by the new service boundary.

## Interfaces and Dependencies

The end state should expose explicit caller-facing request/result types and service methods, with internally injected adapters for Qt bootstrapping, matrix execution, artifact writing, and asset generation. The dependency strategy is the full hybrid:

- external surface shaped like Design 3, with explicit verbs,
- internal dependency handling shaped like Design 4, with adapter seams around concrete Qt and filesystem behavior.

Revision note: created on 2026-06-03 as child plan 3 of the Phase 3 evidence-service program.
