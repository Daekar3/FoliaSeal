# Deepen The Phase 3 Evidence Service

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

This program is complete. The Phase 3 automatic evidence path is easier to run, easier to test, and much easier to extend without editing one 6,000-line Qt harness file. The user-visible behavior did not change: `foliaseal phase3-signing-harness`, `foliaseal phase3-signing-preview-matrix`, `foliaseal phase3-signing-acceptance-matrix`, and the signed-acceptance evidence workflow still produce the same kinds of JSON and Markdown artifacts, but the orchestration boundary is now explicit and testable.

The practical outcome is that future automatic acceptance work no longer requires broad monkeypatch-heavy edits in `src/foliaseal/presentation/qt/phase3_harness.py` and `tests/unit/test_phase3_harness.py`. A later contributor can test the evidence service at a smaller boundary while leaving Qt adapters and artifact-writing adapters thinner.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_reporting_boundary_execplan.md` landed first. It created the first pure reporting boundary and proved that capture finalization can move out of the Qt runner without changing schemas.
- [x] `docs/ExecPlans/phase3_harness_session_runner_execplan.md` depended on the reporting boundary and is now complete. It separated interactive Qt session execution from capture assembly.
- [x] `docs/ExecPlans/phase3_evidence_service_and_cli_execplan.md` depended on the prior two plans and is now complete. It consolidated the matrix and signed-acceptance evidence flows behind the explicit service and reduced `src/foliaseal/__main__.py` to a dispatcher.

## Progress

- [x] (2026-06-03 03:01Z) Investigated the Phase 3 harness seam and confirmed that the long-term value is automatic acceptance evidence, not disposable GUI code.
- [x] (2026-06-03 03:01Z) Chose the hybrid `3+4` direction for the full correction: explicit caller-facing verbs over an internally port-shaped evidence service.
- [x] (2026-06-03 03:01Z) Split the full correction into three child ExecPlans so the refactor can land in narrow, reviewable slices.
- [x] Complete the reporting-boundary child plan.
- [x] Complete the interactive harness session-runner child plan.
- [x] Complete the matrix/evidence service and CLI child plan.

## Surprises & Discoveries

- Observation: the deepest current problem is not the Qt harness window itself, but the fact that execution, capture finalization, contract evaluation, artifact writing, and reporting still live in one function family.
  Evidence: `run_phase3_signing_harness()` in `src/foliaseal/presentation/qt/phase3_harness.py` still assembles payloads, evaluates the evidence contract, constructs `Phase3HarnessCapture`, writes JSON, writes the checklist Markdown, and prints summaries in one path.

- Observation: the harness is part of the supported automated evidence path, not just developer scratch tooling.
  Evidence: `src/foliaseal/__main__.py` exposes dedicated Phase 3 commands, `README.md` documents them, `src/foliaseal/application/phase3_evidence_service.py` now owns the CLI-facing evidence verbs, and `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` is a thin wrapper/client around that service.

## Decision Log

- Decision: stage the full correction across multiple ExecPlans instead of attempting a single large rewrite.
  Rationale: the current seam mixes interactive Qt behavior, schema-sensitive evidence payloads, and CLI/documented outputs. A one-shot refactor would create unnecessary review risk and blur behavior-change versus architecture-change slices.
  Date/Author: 2026-06-03 / Codex

- Decision: make the first slice pure reporting extraction rather than Qt runner extraction.
  Rationale: contract evaluation, checklist rendering, and artifact writing are already mostly pure and already have focused tests, so that seam can move first without touching JSON shape or matrix summaries.
  Date/Author: 2026-06-03 / Codex

- Decision: finish the final child plan by making the application layer the explicit service boundary and leaving `phase3_signed_acceptance_evidence.py` as a thin wrapper/client.
  Rationale: the CLI-facing workflows needed one stable orchestration seam, but the existing command names, artifact paths, and summary shape were already good contracts.
  Date/Author: 2026-06-03 / Codex

## Outcomes & Retrospective

This program plan is complete. The reporting-boundary child plan, the interactive harness session-runner child plan, and the matrix/evidence service and CLI child plan all landed, leaving a smaller and testable Phase 3 evidence stack with the same documented command surface.

## Context and Orientation

The current Phase 3 evidence path is spread across four key files. `src/foliaseal/presentation/qt/phase3_harness.py` contains the interactive signing harness, the session-runner boundary, the capture-payload assembler, the preview matrix runner, the signed-acceptance matrix runner, and many helper functions for snapshotting rendered output, serializing summary payloads, and writing artifacts. `src/foliaseal/application/phase3_evidence_service.py` owns the CLI-facing service boundary and the signed-acceptance evidence summary assembly. `src/foliaseal/presentation/qt/phase3_signed_acceptance_evidence.py` is the thin wrapper/client that provides noise filtering and default service wiring. `src/foliaseal/application/qa_evidence_contract.py` validates saved capture payloads and determines whether they are engineering-only, gate-candidate, or release-gating evidence. `src/foliaseal/__main__.py` exposes the relevant commands and dispatches through the service boundary.

The architectural problem that motivated this program has been resolved. The caller-facing workflows now go through one explicit service instead of reaching into a large presentation module whose public functions co-own Qt bootstrapping, capture finalization, contract evaluation, artifact writing, matrix loops, and summary formatting.

The achieved end state for this program is a deep module with explicit caller-facing verbs such as “capture harness,” “run preview matrix,” “run signed acceptance evidence,” and “validate capture,” while Qt bootstrapping, filesystem writing, and matrix execution sit behind smaller internal adapter seams.

## Plan of Work

The first child plan extracted the reporting boundary. It left Qt execution in place, but moved contract evaluation, capture construction, checklist generation, and artifact writing behind one explicit helper path.

The second child plan landed. The Qt session now returns raw session state and signed-run state while a separate capture assembler converts that state into one stable `Phase3HarnessCapture`.

The third child plan lifted the matrix and signed-acceptance evidence flow behind the explicit service boundary. `src/foliaseal/__main__.py` is now the thin dispatcher that builds request objects and prints concise summaries.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Read and update these plans as the program proceeds:

    docs/ExecPlans/phase3_reporting_boundary_execplan.md
    docs/ExecPlans/phase3_harness_session_runner_execplan.md
    docs/ExecPlans/phase3_evidence_service_and_cli_execplan.md

For each child plan, run its validation commands and update this parent plan so the dependency checkboxes always reflect the actual state.

## Validation and Acceptance

This parent plan is accepted when the child plans exist, remain synchronized with the actual state of the work, and together describe a full path from the current fused harness to the proposed hybrid `3+4` evidence service. The completed program is accepted only when the child plans land and the documented Phase 3 commands still produce working evidence outputs with passing tests.

## Idempotence and Recovery

This parent plan is safe to revise repeatedly. If child plans change shape, update the dependency section and the context/orientation prose immediately so a later contributor can still navigate the program from this document alone.

## Artifacts and Notes

The first and second child plans do not change JSON schema shape, matrix summary counters, or CLI command names. Those constraints exist to keep the program incremental and are repeated in the child plans where they matter.

## Interfaces and Dependencies

The full program targeted a hybrid interface and now has the expected shape. The external surface looks like a small service with explicit verbs for harness capture, matrix execution, signed-acceptance evidence generation, and capture validation. Internally, the implementation uses port-shaped boundaries for Qt bootstrapping, matrix execution, and artifact writing. The dependency categories are:

- `In-process` for evidence shaping, contract evaluation, and summary formatting.
- `Local-substitutable` for filesystem writes, Qt test doubles, and fixture-driven matrix runners.
- `Ports & adapters` for the longer-term internal seams where concrete Qt/filesystem behavior should be injected behind service-owned orchestration.

Revision note: created on 2026-06-03 to track the full multi-loop correction of the Phase 3 evidence architecture after the hybrid `3+4` design was selected.
