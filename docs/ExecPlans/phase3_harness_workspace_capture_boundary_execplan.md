# Extend the Phase 3 harness workspace boundary for request, result, and capture reads

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness will still capture the same preview, validation, signing-request, and backend-reservation evidence for interactive runs, and preview-matrix execution will still produce the same scenario result payloads. The visible harness outputs do not change.

The architectural win is that the harness will stop reading request/result/capture state through `compat_surface` and `properties_panel._workflow` at its main call sites. Instead, the same `phase3_harness_workspace.py` boundary introduced in the previous slice will grow a few narrow read/capture verbs so the harness can ask the workspace for its current request, last signing result, and raw capture payload without knowing shell anatomy.

## Child ExecPlan Dependencies

- [x] (2026-06-11 11:18Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the preview-scenario mutation boundary already exists and is the prerequisite for this follow-on slice.
- [x] (2026-06-11 11:18Z) No child ExecPlan is required for this second tracer bullet on the same hybrid seam.

## Progress

- [x] (2026-06-11 11:18Z) Re-read the current workspace boundary, the harness session runner, the interactive capture helper, and the tests that still prove request/capture reach-through directly.
- [x] (2026-06-11 11:21Z) Ran the required `explorer-light` dev-loop pass and fixed the next slice boundary: add `current_request()`, `last_signing_result()`, and `capture_state(...)` to the workspace boundary; do not absorb runner lifecycle or reporting.
- [x] (2026-06-11 11:25Z) Wrote this ExecPlan and fixed the implementation target at the smallest read/capture extension on the existing harness workspace boundary.
- [x] (2026-06-11 11:54Z) Extended `phase3_harness_workspace.py` with `Phase3HarnessCaptureCommand`, `current_request()`, `last_signing_result()`, and `capture_state(...)`, then migrated the preview-matrix and session-runner call sites to that boundary.
- [x] (2026-06-11 11:58Z) Added focused boundary tests for the new verbs in `test_qt_phase3_harness_workspace.py`, updated the session-runner tests to use the workspace boundary, and removed the old direct request/capture helper tests from `test_phase3_harness.py`.
- [x] (2026-06-11 12:01Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-11 12:05Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the deeper workspace-boundary ownership split.
- [x] (2026-06-11 12:07Z) Reviewed the slice against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; no corrective follow-on was required because the slice remained behavior-preserving and left lifecycle/reporting ownership unchanged.
- [ ] Create the git commit for the finished slice.

## Surprises & Discoveries

- Observation: after the scenario-mutation slice, the harness still performed direct shell-introspection at the next-most-frequent call sites.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` still refreshes preview text and snapshots requests via `compat.properties_panel` and `_snapshot_current_draft_request(...)`, and `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` still reads `properties_panel._workflow` and `last_signing_result` through the compatibility surface.

- Observation: the interactive session runner is still a distinct concern even after those leaks are removed.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` owns window construction, toolbar controls, callback wiring, and `app.exec()`, none of which should move in this slice.

- Observation: the adapter constructors needed optional capture helper injections to keep the scenario-only tests simple.
  Evidence: the first focused test run failed because the previous `apply_scenario()` tests did not care about capture helpers; adding default no-op callables preserved the narrow call shape without widening the boundary.

## Decision Log

- Decision: keep the second slice limited to read/capture verbs on the existing workspace boundary.
  Rationale: this is the smallest next step that materially reduces harness reach-through after `apply_scenario(...)` landed. Pulling in session lifecycle or reporting would broaden the tracer bullet unnecessarily.
  Date/Author: 2026-06-11 / Codex

- Decision: add three narrow verbs to `Phase3HarnessWorkspacePort`: `current_request()`, `last_signing_result()`, and `capture_state(...)`.
  Rationale: those are the smallest stable behaviors the harness still needs. They let the harness stop knowing about `properties_panel._workflow` and `compat_surface.last_signing_result` without creating a generic harness framework.
  Date/Author: 2026-06-11 / Codex

- Decision: keep `Phase3HarnessSessionRunner` responsible for Qt window lifecycle, toolbar wiring, callback ownership, and `app.exec()`.
  Rationale: `docs/ARCHITECTURE.md` already marks the previous slice as only the first tracer bullet. The runner remains the right owner for session lifecycle until a later slice deliberately targets that concern.
  Date/Author: 2026-06-11 / Codex

## Outcomes & Retrospective

Implementation, focused validation, documentation reconciliation, and compliance review are complete. The slice deepened `src/foliaseal/presentation/qt/phase3_harness_workspace.py` so it now owns request/result/capture reads in addition to scenario mutation, updated `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` to use that boundary, and moved the detailed request/capture tests beside the new owner.

The resulting design still keeps `phase3_harness_session_runner.py` as the Qt lifecycle boundary and does not mix in reporting, signed-run assembly, or broad compatibility-surface cleanup. No follow-on corrective slice was required after the compliance pass.

## Context and Orientation

The current harness boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. It already owns one narrow concept: applying a preview-matrix scenario to either a live Qt signing shell or a headless `SigningDraftWorkflow`. That module removed duplicated scenario mutation from `src/foliaseal/presentation/qt/phase3_harness.py`, but the harness still reaches through shell internals for the next layer of behavior: reading the current draft request, reading the last signing result, and capturing raw preview/validation/backend-reservation state.

Today, the main leaks are easy to point to. In `src/foliaseal/presentation/qt/phase3_harness.py`, the live preview-matrix path still does `compat.properties_panel.refresh_preview()`, `preview_text()`, `validation_text()`, and `_snapshot_current_draft_request(compat.properties_panel._workflow)` before assembling the scenario result. In `src/foliaseal/presentation/qt/phase3_harness_session_runner.py`, the runner still snapshots the current request from `self.compat_surface(shell).properties_panel._workflow`, reads `last_signing_result` off the compatibility surface, and owns an inline `capture_current_state(...)` helper that threads those reads into `capture_interactive_state(...)`.

This slice deepens the same workspace boundary instead of creating a new one. In plain language, the harness should ask the workspace, “what request would you sign right now?”, “what was the last signing result?”, and “capture your current preview/validation/request/backend state,” rather than understanding where those facts live inside the shell. The workspace adapters may still use the compatibility surface privately, but the harness should not.

The relevant tests live in `tests/unit/test_phase3_harness.py` and `tests/unit/test_qt_phase3_harness_workspace.py`. The next tests to move are the ones that directly prove `_capture_interactive_state(...)` and `_snapshot_current_draft_request(...)`, because those behaviors are the next seam being extracted.

## Plan of Work

First, extend `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Add a small capture command dataclass that carries the artifact-path and capture-kind inputs currently threaded into `_capture_interactive_state(...)`. Extend `Phase3HarnessWorkspacePort` with `current_request()`, `last_signing_result()`, and `capture_state(...)`. The Qt adapter should own the current live-shell reads: preview refresh, optional `QApplication.processEvents()`, preview text, validation text, render capture, backend-reservation evidence, sign-time diagnostics, and payload assembly. The headless adapter should own the equivalent request read and either a compatible capture payload or a deliberate narrow no-op/unsupported path if that is simpler and still sufficient for the current callers. The boundary should remain small; it must not grow submit-sign or session-lifecycle responsibilities in this slice.

Second, edit `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` to use those new verbs. The live preview-matrix execution path should stop calling `compat.properties_panel` directly for preview/request reads. The session runner should replace direct `properties_panel._workflow` request snapshots and direct `last_signing_result` reads with workspace-boundary calls. Keep window creation, toolbar callbacks, and `app.exec()` in the runner exactly where they are.

Third, add focused tests for the new boundary behaviors in `tests/unit/test_qt_phase3_harness_workspace.py`. Those tests must prove that the Qt adapter returns the current request from the live workflow, preserves `last_signing_result`, and captures preview/validation/backend-reservation data through the new boundary. Move or shrink the old direct helper tests in `tests/unit/test_phase3_harness.py` so higher-level harness tests remain there while the detailed request/capture behavior lives with the new boundary owner.

Fourth, run focused validation. After the code is stable, update `docs/ARCHITECTURE.md` and this ExecPlan so the repo describes the deeper workspace boundary accurately. Then run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. If the review finds a mismatch, fix only the mismatch inside this slice, rerun validation, and then create one narrow commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Extend the harness workspace boundary and migrate request/capture reach-through.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_session_runner.py

2. Add focused boundary tests and shrink the old helper/request tests.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_phase3_harness.py

3. Run focused validation for the new module, session runner, and affected harness tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_session_runner.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun the focused validation commands if any code or tests changed during reconciliation.

5. Run the architectural compliance review, address any findings inside this slice only, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the live preview-matrix path still captures preview snapshot, preview text, validation text, signing-request snapshot, and backend-reservation evidence for the same scenarios as before;
- the interactive session runner no longer reads `properties_panel._workflow` or `last_signing_result` directly through `compat_surface`;
- the workspace boundary, not the old inline helper path, proves current-request, last-signing-result, and raw capture-state behavior in focused tests;
- `Phase3HarnessSessionRunner` still owns Qt window lifecycle, toolbar wiring, callback ownership, and `app.exec()` after the refactor;
- no reporting/finalization refactor, no capture-assembler refactor, and no broad compatibility-surface cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py src/foliaseal/presentation/qt/phase3_harness_session_runner.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py tests/unit/test_phase3_harness_session_runner.py
    git diff --check

Acceptance is behavioral. The interactive and preview-matrix capture payloads must remain unchanged for the same inputs in this slice.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt harness code. It is safe to retry. If the new boundary causes failures, keep the new module in place and move only the missing read/capture behavior into the adapter; do not push request/capture logic back into `phase3_harness.py` or `phase3_harness_session_runner.py`.

If a test fails because the Qt adapter still needs one more shell-local read or refresh, add that behavior inside the adapter rather than widening the public port further. If a compliance review suggests absorbing runner lifecycle or report finalization too, record that as a follow-up and keep this slice centered on request/result/capture reads only.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a deeper `src/foliaseal/presentation/qt/phase3_harness_workspace.py` module that owns request/result/capture reads in addition to scenario mutation;
- a smaller `src/foliaseal/presentation/qt/phase3_harness.py` and `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` that no longer read shell anatomy directly for those behaviors;
- focused unit tests for the new boundary verbs;
- focused validation output showing the new boundary tests, harness tests, and session-runner tests still pass.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the public boundary should stay close to:

    @dataclass(frozen=True)
    class Phase3HarnessCaptureCommand:
        artifacts_dir: str | None
        artifact_basename: str | None
        capture_index: int
        capture_kind: str
        request: SigningRequest | None

    class Phase3HarnessWorkspacePort(Protocol):
        def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...
        def capture_state(self, command: Phase3HarnessCaptureCommand) -> dict[str, Any]: ...

The Qt adapter may take injected helper callables for preview capture, request snapshotting, preview snapshot shaping, backend-reservation evidence, and sign-time diagnostics so the boundary can stay in `phase3_harness_workspace.py` without creating circular imports back into `phase3_harness.py`. The headless adapter may implement only the subset currently needed by the harness entrypoints, but the port should remain coherent and explicit.

This slice must not add submit-sign methods or session-lifecycle methods to the boundary. Those remain future work.

Revision note: Created on 2026-06-11 by Codex for the second `dev-loop` implementation slice on the selected Phase 3 harness workspace-boundary hybrid.
Revision note: Updated on 2026-06-11 after implementation and focused validation to record the deeper workspace boundary, moved tests, and validation results.
