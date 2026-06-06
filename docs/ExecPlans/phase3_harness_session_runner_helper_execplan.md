# Extract Phase 3 harness session runner helper

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, `foliaseal phase3-signing-harness` should still behave the same for a user, but `src/foliaseal/presentation/qt/phase3_harness.py` will stop owning the full interactive Qt session callback cluster inline. The user-visible proof stays the same: the harness still launches, records captured states and signed runs, and writes the same Phase 3 evidence artifacts, but contributors will be able to test the session-runner seam at a dedicated boundary instead of patching more module-private harness helpers.

## Child ExecPlan Dependencies

- [x] `docs/ExecPlans/phase3_harness_capture_assembler_execplan.md` is complete, so signed-run bundle assembly and final payload shaping already live outside `phase3_harness.py`.

## Progress

- [x] (2026-06-05 22:02Z) Re-read `src/foliaseal/presentation/qt/phase3_harness.py`, `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py`, `src/foliaseal/presentation/qt/phase3_harness_reporting.py`, `src/foliaseal/application/phase3_evidence_service.py`, and the focused harness tests to choose the next narrow seam.
- [x] (2026-06-05 22:14Z) Extracted `Phase3HarnessSessionRunner`, `Phase3HarnessSessionResult`, and `_QtHarnessBindings` into `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`, and reduced `phase3_harness.py::_run_phase3_harness_session()` to a thin delegating wrapper.
- [x] (2026-06-05 22:21Z) Added `tests/unit/test_phase3_harness_session_runner.py`, removed the old raw-session proof from `tests/unit/test_phase3_harness.py`, and reran the focused harness/session validation plus Ruff and `git diff --check`.
- [x] (2026-06-05 22:29Z) Reconciled `docs/ARCHITECTURE.md`, closed this ExecPlan, and confirmed the slice stays documentation-complete without `docs/SPEC.md` changes.

## Surprises & Discoveries

- Observation: The capture assembler removed payload shaping from `phase3_harness.py`, but the interactive Qt callback cluster still owns sign-request capture, signed-run freezing, toolbar wiring, state capture, and final-state capture in one function.
  Evidence: `_run_phase3_harness_session()` still spans the shell callback cluster, toolbar wiring, and final-state assembly in `src/foliaseal/presentation/qt/phase3_harness.py`.

- Observation: The extraction did not require changing the top-level harness orchestration test because `_run_phase3_harness_session()` could stay as a thin compatibility wrapper over the new helper.
  Evidence: `tests/unit/test_phase3_harness.py::test_run_phase3_signing_harness_orchestrates_session_and_reporting` still patches `_run_phase3_harness_session()` and passed unchanged after the extraction.

- Observation: The new runner boundary can be tested with pure fake Qt bindings and a fake shell, so the focused proof no longer needs to live in the 4k-line harness test file.
  Evidence: `.venv/bin/python -m pytest tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_harness_session or run_phase3_signing_harness_orchestrates_session_and_reporting'` reported `2 passed, 91 deselected`.

## Decision Log

- Decision: Target the interactive session runner before the matrix paths.
  Rationale: This is the narrowest remaining slice on the same `3+4` Phase 3 hybrid because the harness already has separate reporting and capture-assembly boundaries, while the session callback cluster is still a single broad runtime seam.
  Date/Author: 2026-06-05 / Codex

- Decision: Keep the public harness entry points and CLI-facing service verbs unchanged in this slice.
  Rationale: The goal is to deepen the internal runtime seam without widening into matrix orchestration or service redesign.
  Date/Author: 2026-06-05 / Codex

- Decision: Keep `_run_phase3_harness_session()` in `phase3_harness.py` as a thin delegating wrapper instead of deleting it.
  Rationale: That preserves the stable harness orchestration seam for the existing top-level test and callers while still moving the real runtime ownership into the new helper module.
  Date/Author: 2026-06-05 / Codex

## Outcomes & Retrospective

This slice is complete. The interactive Qt callback cluster now lives in `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`, while `src/foliaseal/presentation/qt/phase3_harness.py` remains the top-level harness entrypoint, capture-assembler builder, and reporting orchestrator. The result matches the purpose of the slice: users still run the same Phase 3 harness command and get the same reporting behavior, but contributors now have a dedicated session-runner boundary and a focused test file for it.

The main remaining Phase 3 seam is no longer the interactive callback cluster. The next good slices are deeper runtime boundaries around preview-matrix or signed-acceptance matrix execution, or a more explicit application-facing gateway once enough of the internal Qt/runtime helpers have been narrowed.

## Context and Orientation

The interactive Phase 3 harness lives in `src/foliaseal/presentation/qt/phase3_harness.py`. That file currently does three different jobs for the interactive path. First, it creates the Qt application window and signing shell. Second, it wires shell callbacks that record sign requests, errors, interaction counts, captured states, and signed runs. Third, it hands the raw session state to `Phase3HarnessCaptureAssembler` and then to `phase3_harness_reporting.py`.

This repository already has two narrower boundaries for the same workflow. `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` turns raw session state into JSON-ready payloads, and `src/foliaseal/presentation/qt/phase3_harness_reporting.py` finalizes those payloads into `Phase3HarnessCapture` plus checklist and JSON output. The remaining broad seam is the interactive Qt session runner itself.

In this plan, a “session runner” means the code that owns the Qt window lifecycle and the callback cluster around the signing shell for one interactive harness run. It should return `Phase3HarnessSessionResult`, which is the raw session state consumed later by the capture assembler. This slice must leave matrix execution, report finalization, and evidence-service callers untouched.

## Plan of Work

Create a new helper module at `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`. That module should own the raw session result data type, the Qt bindings data type used by the interactive harness, and a dedicated helper object or function that runs one interactive harness session. Keep the shell and capture-specific behaviors injectable through constructor or function parameters so tests can fake them without patching deep module-private harness helpers.

Update `src/foliaseal/presentation/qt/phase3_harness.py` so it imports and reuses the new session-runner helper instead of keeping the full `_run_phase3_harness_session()` implementation inline. Preserve compatibility for existing callers and focused tests by keeping the public harness entry point and any needed test-visible names stable. The harness file should still own the top-level `run_phase3_signing_harness()` orchestration and the helper builders that wire the real shell and capture callables into the new session-runner boundary.

Add a new focused test module, `tests/unit/test_phase3_harness_session_runner.py`, that exercises the extracted runner boundary directly with fake Qt bindings and a fake shell. Remove or simplify the old raw-session proof in `tests/unit/test_phase3_harness.py` so the broad harness test file stops owning that boundary coverage. Keep the orchestration test in `tests/unit/test_phase3_harness.py`, but let it patch the narrowed seam instead of the old inline runtime cluster.

Finally, update `docs/ARCHITECTURE.md` so the Phase 3 harness section names the new session-runner helper explicitly and explains that `phase3_harness.py` now delegates the interactive callback cluster to it. Keep `docs/SPEC.md` unchanged unless the implementation proves a documented behavior mismatch.

## Concrete Steps

Work from `/home/daekar/FoliaSeal`.

1. Create `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` and move the interactive session-runner ownership there.
2. Update `src/foliaseal/presentation/qt/phase3_harness.py` to build and delegate to the new runner.
3. Add `tests/unit/test_phase3_harness_session_runner.py` and trim the old raw session proof from `tests/unit/test_phase3_harness.py`.
4. Run:

    `.venv/bin/python -m pytest tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_harness_session or run_phase3_signing_harness_orchestrates_session_and_reporting'`

5. Run:

    `.venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_session_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py`

6. Run:

    `git diff --check`

7. Reconcile `docs/ARCHITECTURE.md` and close this ExecPlan.

## Validation and Acceptance

Acceptance is behavioral. `run_phase3_signing_harness()` must still produce the same reporting flow and payload assembly path, while the raw interactive runtime boundary becomes directly testable at the new helper module.

The slice is complete when:

- `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` owns the interactive Qt session callback cluster and returns `Phase3HarnessSessionResult`;
- `src/foliaseal/presentation/qt/phase3_harness.py` delegates that work instead of keeping the full runtime logic inline;
- the new focused runner test passes without broad monkeypatching of unrelated harness helpers;
- the existing harness orchestration test still proves `run_phase3_signing_harness()` wires session, capture assembly, and report finalization together;
- `ruff check` and `git diff --check` pass cleanly.

## Idempotence and Recovery

This slice is additive and safe to retry. If the new helper module import path or delegation shape is wrong, restore the harness delegation first, rerun the focused tests, and then retry the extraction. Do not mix matrix-runner or reporting changes into this slice.

## Artifacts and Notes

Focused validation transcript after implementation:

    $ .venv/bin/python -m pytest tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_harness.py -k 'run_phase3_harness_session or run_phase3_signing_harness_orchestrates_session_and_reporting'
    ======================= 2 passed, 91 deselected in 0.44s =======================

    $ .venv/bin/ruff check src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_session_runner.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

The extracted helper module must end with stable names for:

- `Phase3HarnessSessionResult`, the raw session-state dataclass consumed by `Phase3HarnessCaptureAssembler`;
- `_QtHarnessBindings`, the Qt binding dataclass used by the interactive harness path;
- a dedicated runner boundary that accepts:
  - Qt bindings,
  - `source_path`,
  - `artifacts_dir`,
  - `ViewerWorkflow`,
  - `SigningDraftWorkflow`,
  - preset catalog store,
  - sign executor,
  - `Phase3HarnessCaptureAssembler`,
  - injected callables for shell construction, draft-request snapshotting, current-state capture, output-path selection, and compatibility-surface lookup.

`src/foliaseal/presentation/qt/phase3_harness.py` should remain the place that wires the real repository callables into that helper. `src/foliaseal/presentation/qt/phase3_harness_capture_assembler.py` and `src/foliaseal/presentation/qt/phase3_harness_reporting.py` are dependencies, not implementation targets, for this slice.

Revision note: Created on 2026-06-05 by Codex after the capture-assembler slice exposed the remaining interactive Qt session callback cluster as the narrowest next deepening seam. Updated on 2026-06-05 after implementation to record the extracted `phase3_harness_session_runner.py` boundary, focused validation, and final documentation reconciliation.
