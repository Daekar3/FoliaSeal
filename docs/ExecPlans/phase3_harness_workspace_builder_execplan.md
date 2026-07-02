# Extract the shared Phase 3 live-workspace builder

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness still behaves the same, but the live Qt harness workspace is built through one shared helper instead of duplicated near-identical builder wiring. Users do not see a workflow change; the gain is architectural: the accepted hybrid starts with a common builder seam before the larger snapshot-payload conversion.

You can verify the change by running the focused Phase 3 harness and workspace tests. They should still pass, and the new builder-focused tests should prove that both the signing-harness and preview-matrix live paths share the same workspace construction logic.

## Child ExecPlan Dependencies

- [x] (2026-07-02 01:06Z) The testing-adapter-only seam landed in `docs/ExecPlans/signing_workspace_testing_adapter_only_execplan.md`.
- [x] (2026-07-02 01:06Z) No child ExecPlans are required for this bounded first slice of the accepted hybrid.

## Progress

- [x] (2026-07-02 01:06Z) Re-read the accepted hybrid direction and confirmed the smallest safe first slice is a shared live-workspace builder, not the snapshot payload conversion.
- [x] (2026-07-02 01:07Z) Used an `explorer-light` subagent to confirm snapshot conversion would fan out broadly, while the builder duplication is isolated to `phase3_harness.py`.
- [x] (2026-07-02 01:16Z) Extracted the shared live Phase 3 harness workspace builder in `src/foliaseal/presentation/qt/phase3_harness.py` and routed the existing live wrappers through it without changing the dict-shaped capture API.
- [x] (2026-07-02 01:20Z) Added focused tests in `tests/unit/test_phase3_harness.py` that prove the wrappers route through the shared builder wiring.
- [x] (2026-07-02 01:23Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py` passed with `103 passed in 1.37s`; `.venv/bin/python -m ruff check ...` passed; `git diff --check` passed.
- [x] (2026-07-02 01:26Z) Completed the compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; the slice is compliant and required no second iteration.

## Surprises & Discoveries

- Observation: `Phase3HarnessWorkspacePort` is already the correct boundary for the live/headless split; the immediate duplication is in builder wiring, not in the adapter interface itself.
  Evidence: `_build_qt_phase3_harness_workspace(...)` and `_build_preview_matrix_qt_workspace(...)` both construct `QtPhase3HarnessWorkspaceAdapter` with the same hook wiring and differ mainly in `profile_store`.

- Observation: the builder extraction did not require a first-pass architecture-doc edit because runtime behavior and public caller-facing boundaries stayed the same.
  Evidence: focused validation passed after touching only `phase3_harness.py`, `test_phase3_harness.py`, and this ExecPlan.

- Observation: one separate direct `QtPhase3HarnessWorkspaceAdapter` construction still exists in `_apply_preview_matrix_scenario()`, but it does not conflict with this slice’s shared-builder goal.
  Evidence: the compliance review flagged `src/foliaseal/presentation/qt/phase3_harness.py#L1801` as a follow-on seam rather than a blocker.

## Decision Log

- Decision: defer the `Phase3HarnessWorkspaceSnapshot` conversion to a follow-on slice.
  Rationale: changing `capture_state(...)` now would force broad mechanical churn through the session runner, signed-acceptance executor, and capture payload assembly. The shared builder is the low-risk first step of the accepted hybrid.
  Date/Author: 2026-07-02 / Codex

## Outcomes & Retrospective

This slice leaves the live harness builder on one shared construction path while preserving the current dict-shaped capture API. The accepted hybrid now has a low-risk first landing point that reduces duplication without forcing downstream payload churn. The next likely seam is removing the remaining direct adapter construction in `_apply_preview_matrix_scenario()` or, after that, tackling the snapshot payload conversion with a smaller caller set.

## Context and Orientation

The main Phase 3 harness facade lives in `src/foliaseal/presentation/qt/phase3_harness.py`. It still owns the caller-facing harness entrypoints and several small builder helpers. Right now, `_build_qt_phase3_harness_workspace(shell)` and `_build_preview_matrix_qt_workspace(shell, profile_store)` both instantiate `QtPhase3HarnessWorkspaceAdapter` with the same render/snapshot/diagnostic hook wiring. That duplication is the smallest safe first step toward the accepted hybrid.

The actual workspace seam lives one layer below in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. That module already depends only on `testing_adapter` for the live path and on `SigningDraftWorkflow` for the headless path. This slice intentionally does not change that port or the dict returned by `capture_state(...)`.

The focused tests for the harness facade live in `tests/unit/test_phase3_harness.py`. They already exercise the public entrypoints heavily, but they do not directly pin the duplicated builder wiring. This slice should add narrowly targeted tests that prove the two live builder wrappers go through the same shared construction path.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness.py`. Introduce one shared helper for building the live `QtPhase3HarnessWorkspaceAdapter`, parameterized by `shell` and `profile_store`, while keeping the existing public/private wrapper names so the current call graph stays stable. Update `_build_qt_phase3_harness_workspace(...)` and `_build_preview_matrix_qt_workspace(...)` to delegate to the shared helper. Do not change `_build_preview_matrix_headless_workspace(...)` in this slice beyond keeping it aligned stylistically if needed.

Second, edit `tests/unit/test_phase3_harness.py`. Add focused tests that monkeypatch `QtPhase3HarnessWorkspaceAdapter` and assert the shared helper wiring is used for both the signing-harness wrapper and the preview-matrix wrapper, including the shared render/snapshot/diagnostic hooks and the differing `profile_store` inputs.

Finally, run focused validation. If the compliance review finds only wording drift, fix it in this slice. If it reveals that the builder extraction changes the effective live/headless contract, stop and document that before widening the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the shared builder helper, focused tests, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py
       apply_patch ... on tests/unit/test_phase3_harness.py
       apply_patch ... on docs/ExecPlans/phase3_harness_workspace_builder_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
       git diff --check

   Observed result:

       103 passed in 1.37s
       All checks passed!

## Validation and Acceptance

This slice is accepted when all of the following are true:

- the live Qt workspace construction path is routed through one shared helper;
- `_build_qt_phase3_harness_workspace(...)` and `_build_preview_matrix_qt_workspace(...)` remain valid callers but no longer duplicate the hook wiring inline;
- focused tests prove the shared builder wiring;
- Phase 3 harness and workspace focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The live harness should behave exactly as before, but the construction path should now be shared and directly testable.

## Idempotence and Recovery

This is a behavior-preserving refactor. It is safe to retry. If a test fails after the extraction, restore behavior by fixing the shared helper or wrapper delegation; do not reintroduce duplicated inline builder wiring in multiple call sites.

## Artifacts and Notes

The key evidence for this slice will be:

- one shared live-builder helper in `src/foliaseal/presentation/qt/phase3_harness.py`;
- focused tests in `tests/unit/test_phase3_harness.py` proving the two live wrappers use that helper;
- focused validation output showing no regression in Phase 3 workspace behavior.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interface remains:

    class Phase3HarnessWorkspacePort(Protocol):
        def refresh_viewer(self) -> None: ...
        def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...
        def capture_state(self, command: Phase3HarnessCaptureCommand) -> dict[str, Any]: ...

At the end of this slice, the live Qt construction helpers should all delegate through one shared helper that returns `Phase3HarnessWorkspacePort`, while the dict-shaped capture payload remains unchanged for compatibility with existing callers.
