# Add a snapshot-returning Phase 3 workspace boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness workspace boundary can return one structured snapshot object containing the current request, last signing result, preview snapshot, text, and backend reservation evidence. Users do not see a workflow change yet; this is the first bounded step of the accepted snapshot-based hybrid.

The architectural win is that callers can begin moving away from separately probing `current_request()`, `last_signing_result()`, and dict-shaped capture payloads. You can verify the change by running the focused workspace tests and seeing that both live-shell and headless adapters expose the new snapshot path while the old dict/probe methods continue to work.

## Child ExecPlan Dependencies

- [x] (2026-07-02 02:05Z) The live builder consolidation landed through `docs/ExecPlans/phase3_harness_workspace_builder_execplan.md`.
- [x] (2026-07-02 02:05Z) No child ExecPlans are required for this bounded first snapshot slice.

## Progress

- [x] (2026-07-02 02:05Z) Re-read the accepted hybrid direction and confirmed the smallest safe snapshot slice is additive: add the snapshot type and method inside `phase3_harness_workspace.py` while leaving the dict/probe methods in place.
- [x] (2026-07-02 02:06Z) Used an `explorer-light` subagent to confirm the initial snapshot slice should not touch `phase3_harness_session_runner.py`, `phase3_signed_acceptance_scenario_executor.py`, or `phase3_harness.py`.
- [x] (2026-07-02 02:15Z) Added `Phase3HarnessWorkspaceSnapshot` and a snapshot-returning boundary method in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`.
- [x] (2026-07-02 02:15Z) Kept `capture_state(...)`, `current_request()`, and `last_signing_result()` as compatibility methods while routing `capture_state(...)` through the new snapshot path.
- [x] (2026-07-02 02:18Z) Extended focused workspace tests and reconciled `docs/ARCHITECTURE.md` for the now-public snapshot seam.
- [x] (2026-07-02 02:19Z) Ran focused validation, completed the compliance review, and recorded the outcome.

## Surprises & Discoveries

- Observation: the real fan-out of the snapshot conversion starts only when callers stop using `current_request()` and `last_signing_result()` separately.
  Evidence: `phase3_harness_session_runner.py` and `phase3_signed_acceptance_scenario_executor.py` still read those probe methods directly today, so changing callers now would widen the slice substantially.
- Observation: the first patch landed almost completely before the tool response truncated, but the architecture table and ExecPlan progress sections were left stale.
  Evidence: `git status --short` showed all expected files modified, the new snapshot type/tests already existed in-tree, and only the architecture summary row plus unchecked plan items still described the pre-snapshot seam.

## Decision Log

- Decision: introduce the snapshot path additively before migrating any caller to it.
  Rationale: this exposes the deeper boundary without forcing broad churn through the session runner, signed-acceptance executor, and capture assembly in the same commit.
  Date/Author: 2026-07-02 / Codex

## Outcomes & Retrospective

This slice should make the snapshot seam real without breaking existing harness callers. Success means the workspace boundary can already return one structured snapshot object, and the old dict/probe methods remain as compatibility shims for later migration.

Completed on 2026-07-02. The workspace boundary now returns `Phase3HarnessWorkspaceSnapshot` from both adapters, `capture_state(...)` adapts that object back to the legacy dict payload, and focused tests/lint/whitespace validation all passed. The only compliance drift found during review was stale architecture wording that still described the seam as raw dict capture reads; that wording was corrected in this slice.

## Context and Orientation

The Phase 3 workspace boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Right now its protocol exposes `apply_scenario(...)`, `refresh_viewer()`, `current_request()`, `last_signing_result()`, and `capture_state(...) -> dict[str, Any]`. The accepted hybrid direction is to move toward a smaller behavioral boundary where callers primarily apply a scenario and then read one structured snapshot.

The immediate downstream callers still expect the older shape. `phase3_harness_session_runner.py` reads `workspace.last_signing_result()` and `workspace.capture_state(...)`. `phase3_signed_acceptance_scenario_executor.py` reads `workspace.current_request()` and `workspace.capture_state(...)`. Because those consumers are not part of this first slice, the snapshot path must be additive.

The focused boundary tests already live in `tests/unit/test_qt_phase3_harness_workspace.py`. They are the right place to define the initial snapshot schema and prove parity between the new snapshot-returning path and the older compatibility path.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Add a `Phase3HarnessWorkspaceSnapshot` dataclass that carries the current request, last signing result, capture metadata, preview snapshot, preview text, validation text, request snapshot, backend reservation snapshot, backend reservation error, and any capture label already produced for live captures. Add a `capture_snapshot(...) -> Phase3HarnessWorkspaceSnapshot` method to `Phase3HarnessWorkspacePort` and to both adapters. Leave `capture_state(...)` in place, but implement it by converting the snapshot to the legacy dict shape. Leave `current_request()` and `last_signing_result()` in place as compatibility reads.

Second, edit `tests/unit/test_qt_phase3_harness_workspace.py`. Add focused assertions for the new snapshot-returning method on both the live-shell and headless adapters. Keep the existing dict-path assertions so the compatibility shape stays covered.

Third, update `docs/ARCHITECTURE.md`. The Phase 3 workspace boundary entry should mention the new snapshot type and snapshot-returning method alongside the still-present compatibility methods, so the public seam description matches the code.

Finally, run focused validation. If the compliance review finds only stale wording, fix it in this slice. Do not migrate the session runner or signed-acceptance executor here.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Update the workspace boundary, focused tests, architecture notes, and this living plan.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on docs/ARCHITECTURE.md
       apply_patch ... on docs/ExecPlans/phase3_harness_workspace_snapshot_execplan.md

2. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
       git diff --check

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `Phase3HarnessWorkspaceSnapshot` exists as a public workspace-boundary type;
- both the live-shell and headless adapters implement a snapshot-returning method;
- `capture_state(...)` still returns the old dict shape by adapting the snapshot;
- `current_request()` and `last_signing_result()` remain usable for downstream compatibility;
- focused tests, lint, and whitespace checks pass.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
    git diff --check

Acceptance is behavioral. The new snapshot path should expose the same observable capture data as the dict path, but no downstream caller migration should be required yet.

## Idempotence and Recovery

This is an additive refactor. It is safe to retry. If a test fails, fix the snapshot-to-dict adaptation rather than removing the snapshot method or widening the slice to downstream callers.

## Artifacts and Notes

The key evidence for this slice will be:

- `src/foliaseal/presentation/qt/phase3_harness_workspace.py` defining `Phase3HarnessWorkspaceSnapshot` and returning it from both adapters;
- focused tests in `tests/unit/test_qt_phase3_harness_workspace.py` proving live/headless snapshot parity;
- architecture text naming the new public snapshot seam.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

The important interface at the end of the slice should be:

    @dataclass(frozen=True)
    class Phase3HarnessWorkspaceSnapshot:
        current_request: SigningRequest | None
        last_signing_result: SigningResult | None
        capture_index: int
        capture_kind: str
        capture_label: str | None
        preview_snapshot: dict[str, Any]
        preview_text: str
        validation_text: str
        sign_request_snapshot: dict[str, Any] | None
        backend_reservation_snapshot: dict[str, Any] | None
        backend_reservation_error: str | None

    class Phase3HarnessWorkspacePort(Protocol):
        def refresh_viewer(self) -> None: ...
        def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...
        def current_request(self) -> SigningRequest | None: ...
        def last_signing_result(self) -> SigningResult | None: ...
        def capture_snapshot(
            self, command: Phase3HarnessCaptureCommand
        ) -> Phase3HarnessWorkspaceSnapshot: ...
        def capture_state(self, command: Phase3HarnessCaptureCommand) -> dict[str, Any]: ...
