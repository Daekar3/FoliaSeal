# Extract Phase 3 harness scenario application behind a narrow workspace boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, running a Phase 3 preview-matrix scenario will still behave the same: the live-shell path will apply appearance overrides, timestamp requirements, and signature-rectangle changes to the signing workspace, and the headless path will apply the same scenario to `SigningDraftWorkflow` before preview capture. The visible harness outputs do not change.

The architectural win is that scenario mutation will stop being implemented twice in `src/foliaseal/presentation/qt/phase3_harness.py`. A new narrow workspace boundary will own “apply one preview scenario” for both the interactive shell and the headless workflow path. This cuts the worst reach-through into `compat_surface` and `properties_panel._workflow` without mixing in the separate concerns of Qt window lifecycle, toolbar wiring, or capture assembly.

## Child ExecPlan Dependencies

- [x] (2026-06-07 20:34Z) The app-frame workspace-open and certificate-dialog boundary slices are complete; no prerequisite app-frame work remains for this harness slice.
- [x] (2026-06-07 20:34Z) No child ExecPlan is required for this first tracer bullet on the Phase 3 harness seam.

## Progress

- [x] (2026-06-07 20:34Z) Re-read the selected hybrid design, the live Phase 3 harness scenario helpers, the relevant harness tests, and the architecture notes for the compatibility surface.
- [x] (2026-06-07 20:37Z) Ran the required `explorer-light` dev-loop pass and fixed the first slice boundary: extract only duplicated scenario application behind a small workspace port; do not pull in interactive session control or capture orchestration.
- [x] (2026-06-07 20:42Z) Wrote this ExecPlan and fixed the implementation target at one `apply_scenario(...)` boundary with interactive and headless adapters.
- [x] (2026-06-07 20:56Z) Added `src/foliaseal/presentation/qt/phase3_harness_workspace.py` with `Phase3HarnessScenarioCommand`, `Phase3HarnessWorkspacePort`, `QtPhase3HarnessWorkspaceAdapter`, and `HeadlessPhase3HarnessWorkspaceAdapter`, then migrated the duplicated preview-matrix scenario helpers to it.
- [x] (2026-06-07 20:59Z) Added `tests/unit/test_qt_phase3_harness_workspace.py` for live/headless adapter coverage and removed the old direct live-helper test from `tests/unit/test_phase3_harness.py` while keeping the remaining pure helper coverage.
- [x] (2026-06-07 21:02Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-07 21:11Z) Reconciled `docs/ARCHITECTURE.md` to the implemented ownership split so the repo now names `phase3_harness_workspace.py` as the preview-scenario owner and keeps `phase3_harness_session_runner.py` as the intentional interactive lifecycle boundary.
- [x] (2026-06-07 21:15Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan through a fresh `explorer-light` pass; no findings were reported.
- [ ] Create the git commit for the finished slice.

## Surprises & Discoveries

- Observation: the preview-matrix scenario concept is still duplicated in two places even after substantial harness extraction elsewhere.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness.py` still has `_apply_preview_matrix_scenario_to_workflow(...)` for headless mutation and `_apply_preview_matrix_scenario(...)` for live-shell mutation.

- Observation: the interactive scenario helper still depends on the broad compatibility surface for operations that are conceptually one “apply scenario” action.
  Evidence: the live helper reaches through `compat.properties_panel._workflow`, `compat.viewer_workflow`, `compat.viewer_widget`, and optional sync helpers before calling `compat.refresh_viewer()`.

- Observation: the interactive session runner is adjacent but not the same concern.
  Evidence: `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` owns window lifecycle, callback wiring, toolbar controls, capture timing, and final-state assembly rather than scenario mutation.

- Observation: the existing pure appearance-override tests still belong to the scenario boundary even though they stay in `test_phase3_harness.py` for now.
  Evidence: moving `_apply_appearance_overrides(...)` into the new module immediately surfaced a behavior mismatch for `visible_fields`, and the preserved tests caught it before the slice was declared complete.

## Decision Log

- Decision: keep the first slice limited to scenario mutation and do not absorb interactive session control.
  Rationale: scenario duplication is the smallest cut that materially deepens the seam. Pulling in session runner behavior now would mix two refactors and broaden the tracer bullet unnecessarily.
  Date/Author: 2026-06-07 / Codex

- Decision: use one narrow `Phase3HarnessWorkspacePort.apply_scenario(...)` boundary with two local adapters, one for the Qt shell path and one for the headless workflow path.
  Rationale: this is the strongest part of the selected `4 + 1` hybrid. It removes the duplicated logic and shell-anatomy reach-through while keeping the new vocabulary intentionally small.
  Date/Author: 2026-06-07 / Codex

- Decision: do not widen `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` to support this slice.
  Rationale: widening the broad compatibility surface would defeat the purpose. The new harness adapter may consume the existing compatibility surface privately, but the harness itself should learn less shell anatomy, not more.
  Date/Author: 2026-06-07 / Codex

- Decision: keep `_apply_preview_matrix_scenario(...)` in `phase3_harness.py` only as a thin compatibility wrapper for the signed-acceptance executor.
  Rationale: that preserves the existing executor call shape while removing the duplicated mutation logic from the file. The important architectural change is that the wrapper no longer owns the behavior.
  Date/Author: 2026-06-07 / Codex

## Outcomes & Retrospective

Implementation, documentation reconciliation, focused validation, and architectural compliance review are complete. The slice added `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, moved preview-matrix scenario mutation into interactive and headless adapters, removed the duplicated headless helper from `phase3_harness.py`, and reduced the remaining live helper to a thin adapter-backed wrapper used by the signed-acceptance executor.

The slice stayed narrow all the way through review. It did not absorb interactive session lifecycle, capture-state assembly, manifest parsing, or broader compatibility-surface cleanup. Only the final commit remains.

## Context and Orientation

The Phase 3 harness is the repo’s interactive signing-evidence runner. In this repository, “Phase 3” means running controlled signing scenarios, capturing preview and signed-output evidence, and assembling acceptance artifacts. The main orchestration lives in `src/foliaseal/presentation/qt/phase3_harness.py`. A smaller helper in `src/foliaseal/presentation/qt/phase3_harness_session_runner.py` owns the Qt window and callback cluster for one interactive harness run.

Today, one product concept is still split into two separate helper implementations: “apply one preview scenario.” The headless path uses `_apply_preview_matrix_scenario_to_workflow(...)` to mutate a `SigningDraftWorkflow` directly. The live-shell path uses `_apply_preview_matrix_scenario(...)` to reach through `_shell_compat_surface(shell)`, mutate `properties_panel._workflow`, set the signature rectangle through the panel, jump the viewer to the new page, refresh the viewer widget, run placement/overlay sync helpers when available, refresh the sign button, and then call `compat.refresh_viewer()`.

That duplication matters because the live helper still exposes too much shell anatomy to the harness. In plain language, the harness knows about panel internals, workflow placement rules, and viewer/overlay sync details that should be hidden inside a deeper module. The current architecture document already describes `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` as a broad harness/testing surface that remains technical debt. This slice narrows one dependency on that debt without attempting to remove the whole compatibility surface at once.

The relevant test coverage lives in `tests/unit/test_phase3_harness.py`. Today there is a direct helper test, `test_apply_preview_matrix_scenario_syncs_viewer_to_signature_rect_page()`, that proves exactly the behavior the new live adapter should own. This slice should move that behavior proof to a focused new boundary test module and leave `test_phase3_harness.py` with higher-level preview-matrix execution coverage.

## Plan of Work

First, add a new module under `src/foliaseal/presentation/qt/` for the harness workspace boundary. Define one small scenario command dataclass and one small port with a single public verb, `apply_scenario(...)`. Inside that module, define two local adapters: one wrapping the Qt signing shell path and one wrapping the headless `SigningDraftWorkflow` path. The interactive adapter may privately use the existing compatibility surface, but the public boundary must hide that detail. The interactive adapter should own the current sequence of appearance update, timestamp mutation, signature-rectangle placement, viewer page jump, viewer refresh, optional placement/overlay sync, sign-button refresh, and final compatibility-surface refresh. The headless adapter should own the corresponding workflow-only mutation sequence.

Second, edit `src/foliaseal/presentation/qt/phase3_harness.py` so the duplicated helpers are replaced by calls into the new boundary. `_execute_preview_matrix_scenario(...)` should open or receive the interactive adapter and call `apply_scenario(...)` before collecting preview and request snapshots. `_execute_headless_preview_matrix_scenario(...)` should do the same through the headless adapter. Remove the old duplicated helper implementations after the new boundary is wired.

Third, add focused tests for the new boundary in a new unit test module. The live-adapter tests must prove appearance override application, timestamp flag mutation, signature-rectangle page sync, and viewer refresh choreography. The headless-adapter tests must prove that the same scenario fields are applied to `SigningDraftWorkflow` without needing the Qt shell path. Then shrink `tests/unit/test_phase3_harness.py` so the old inline helper test is either deleted or replaced with a higher-level execution test that no longer proves adapter internals.

Fourth, run focused validation. After the code is stable, update `docs/ARCHITECTURE.md` and this ExecPlan so the repo describes the new harness boundary accurately. Then run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. If the review finds a mismatch, fix only the mismatch inside this slice, rerun validation, and then create one narrow commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the harness workspace boundary module and migrate the duplicated scenario helpers.

       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness.py

2. Add focused boundary tests and shrink the old helper coverage.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on tests/unit/test_phase3_harness.py

3. Run focused validation for the new module and affected harness tests.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
       git diff --check

4. Reconcile `docs/ARCHITECTURE.md` and this ExecPlan to the implemented boundary, then rerun the focused validation commands if any code or tests changed during reconciliation.

5. Run the architectural compliance review, address any findings inside this slice only, and create the git commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- live-shell preview-matrix execution still applies profile-based appearance, appearance overrides, timestamp requirements, and signature-rectangle changes before preview capture;
- the live-shell path still syncs the viewer to the signature rectangle page and refreshes placement-related UI after scenario application;
- the headless preview-matrix path still applies the same scenario fields to `SigningDraftWorkflow` before preview capture;
- `src/foliaseal/presentation/qt/phase3_harness.py` no longer contains two separate scenario-mutation implementations;
- the new boundary, not the old inline helper, proves the page-sync and workflow-mutation behavior in focused tests;
- no interactive session runner, capture assembly, manifest parsing, or broader compatibility-surface cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
    git diff --check

Acceptance is behavioral. The preview-matrix outputs must remain unchanged for the same scenarios in this slice.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt harness code. It is safe to retry. If the new boundary causes failures, keep the new module in place and move only the missing collaborator or tiny compatibility call into the adapter; do not re-inline the scenario logic back into `phase3_harness.py`.

If a test fails because the interactive adapter still needs one more shell-local refresh or sync call, add that behavior inside the adapter rather than widening the public port. If a compliance review suggests unifying capture or interactive session control too, record that as a follow-up and keep this slice centered on scenario mutation only.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a new `src/foliaseal/presentation/qt/phase3_harness_workspace.py` module that owns scenario application for both live and headless paths;
- a smaller `src/foliaseal/presentation/qt/phase3_harness.py` that no longer contains duplicated scenario-mutation helpers;
- a new focused unit test module for the harness workspace boundary;
- focused validation output showing the new boundary tests and the affected harness tests still pass.

Current validation transcript:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
    88 passed, 1 warning in 1.31s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/phase3_harness_workspace.py src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_qt_phase3_harness_workspace.py tests/unit/test_phase3_harness.py
    All checks passed!

    $ git diff --check
    <no output>

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the new public boundary should stay close to:

    @dataclass(frozen=True)
    class Phase3HarnessScenarioCommand:
        profile_name: str | None
        appearance_overrides: dict[str, Any] | None
        timestamp_required: bool | None
        signature_rect: SignatureRect | None

    class Phase3HarnessWorkspacePort(Protocol):
        def apply_scenario(self, command: Phase3HarnessScenarioCommand) -> None: ...

Internally, the module may define:

    class QtPhase3HarnessWorkspaceAdapter:
        ...

    class HeadlessPhase3HarnessWorkspaceAdapter:
        ...

The interactive adapter may depend on the existing compatibility surface privately. The harness entrypoints in `phase3_harness.py` must depend only on the new narrow port or on thin constructors that produce it. This slice must not introduce capture-state methods, sign-submit methods, or session-lifecycle methods to the port yet.

Revision note: Created on 2026-06-07 by Codex for the first `dev-loop` implementation slice of the selected Phase 3 harness workspace-boundary hybrid.

Revision note: Updated on 2026-06-07 after implementation and focused validation to record the extracted scenario boundary, the retained thin signed-acceptance wrapper, and the validation results.

Revision note: Updated on 2026-06-07 after architecture reconciliation and compliance review to record the completed documentation work, the clean review outcome, and the remaining follow-up limit to commit creation only.
