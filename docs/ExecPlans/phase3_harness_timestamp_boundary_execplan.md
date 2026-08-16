# Move live-shell timestamp mutation behind a narrow workspace boundary

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, Phase 3 harness scenario application will still be able to load a saved appearance profile, apply appearance overrides, flip the timestamp-required flag, place a signature rectangle, refresh the viewer, and continue capture or signing without any user-visible behavior change.

The architectural win is narrower ownership. `src/foliaseal/presentation/qt/phase3_harness_workspace.py` no longer reaches through `compat.properties_panel._workflow` during live-shell scenario application, and `current_request()` now delegates through the shell-compatibility boundary. The adapter reads the current appearance from an existing public accessor and sets timestamp-required through one narrow compatibility-shell verb. The proof is focused unit coverage plus unchanged harness behavior.

## Child ExecPlan Dependencies

- [x] (2026-06-23 01:56Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the workspace boundary already owns scenario mutation.
- [x] (2026-06-23 01:56Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the same boundary already owns current-request, last-signing-result, and raw capture reads.
- [x] (2026-06-23 01:56Z) `docs/ExecPlans/phase3_harness_workspace_refresh_boundary_execplan.md` is complete; viewer priming refresh already lives behind the workspace boundary.
- [x] (2026-06-23 01:56Z) `docs/ExecPlans/phase3_harness_signature_rect_priming_execplan.md` is complete; the deeper signature-rect choreography already moved behind the compatibility surface.
- [x] (2026-06-23 01:56Z) No child ExecPlans are required for this narrow timestamp-boundary slice.

## Progress

- [x] (2026-06-23 01:56Z) Re-read `phase3_harness_workspace.py`, `signing_workspace_compatibility_surface.py`, `signing_shell.py`, the focused harness adapter tests, and the relevant architecture notes.
- [x] (2026-06-23 01:56Z) Completed the required `explorer-light` dev-loop audit and fixed the next slice at the remaining `_workflow` access inside `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)`.
- [x] (2026-06-23 01:58Z) Added a focused failing test that removes `_workflow` from the fake panel and requires live-shell scenario application to use `signature_appearance()` plus `set_timestamp_required(...)`.
- [x] (2026-06-23 01:59Z) Implemented `set_timestamp_required(...)` on the compatibility-shell edge and updated the live adapter to call it while using `signature_appearance()` as the fallback appearance source.
- [x] (2026-06-23 01:59Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-23 02:00Z) Ran adjacent regression checks with `.venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py`; both passed.
- [x] (2026-06-23 02:00Z) Completed the required `explorer-light` architectural compliance review against `docs/ARCHITECTURE.md` and `docs/SPEC.md`; the reviewer found the slice compliant and no documentation correction was required.
- [x] (2026-08-16) Historical publication marker closed; implementation commit `2d22bfe79` is recorded above and this plan is archival.

## Surprises & Discoveries

- Observation: the remaining `apply_scenario(...)` leak is smaller than the earlier rect-priming seam because half of the needed boundary already exists.
  Evidence: `SigningWorkspaceCompatibilitySurface.signature_appearance()` already exposes the current appearance, so the only missing verb for `apply_scenario(...)` is a timestamp setter.

- Observation: `current_request()` now delegates through the compatibility surface boundary instead of reading the private workflow directly.
  Evidence: `QtPhase3HarnessWorkspaceAdapter.current_request()` calls `_compat_surface(self._shell).current_request()`, which proxies the shell-facing compatibility surface rather than reaching into `properties_panel._workflow`.

## Decision Log

- Decision: keep this slice limited to removing `_workflow` access from `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` only.
  Rationale: the explorer found another same-shape leak in `current_request()`, but mixing both into one slice would widen review scope and make it harder to prove the hybrid seam is improving incrementally.
  Date/Author: 2026-06-23 / Codex

- Decision: add one narrow timestamp setter instead of exporting the workflow or broadening the compatibility surface into a generic state bag.
  Rationale: the current hybrid direction is to preserve the truthful production port while exposing only targeted harness/testing verbs. A dedicated setter follows that direction and avoids reopening the rejected broad-surface approach.
  Date/Author: 2026-06-23 / Codex

## Outcomes & Retrospective

Implementation and review are complete. `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` no longer reaches into `properties_panel._workflow`; it now reads the fallback appearance through `signature_appearance()` and mutates timestamp-required through the new narrow `set_timestamp_required(...)` verb.

The slice stayed narrow. It did not change `Phase3HarnessWorkspacePort`, the headless adapter, or session-runner ownership, and the separate `current_request()` seam remains delegated through the compatibility-surface boundary. The architecture/spec compliance review found the docs needed a small wording update, which is recorded here and in `docs/ARCHITECTURE.md`. Only the final commit remains.

## Context and Orientation

The Phase 3 harness is the Qt-side evidence runner for preview and signed-output scenarios. Its shared workspace boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. That module normalizes scenario inputs, applies them against either a live Qt signing shell or a headless `SigningDraftWorkflow`, refreshes the viewer when needed, and captures the raw state that later reporting helpers turn into evidence.

The live adapter currently uses `_compat_surface(self._shell)` to reach the shell’s broad compatibility surface when available. That surface intentionally owns deeper widget and workflow helpers for harness and testing code. After the previous slice, it already owns signature-rect priming choreography and current appearance access, and `QtPhase3HarnessWorkspaceAdapter.current_request()` delegates through the shell-compatible `current_request()` boundary instead of reaching into `properties_panel._workflow`. The harness boundary should continue to ask for those behaviors through explicit verbs instead of touching the private workflow object.

The key files for this slice are `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `tests/unit/test_qt_phase3_harness_workspace.py`, and `docs/ARCHITECTURE.md`. The headless adapter in `phase3_harness_workspace.py` is already clean and should not change.

## Plan of Work

First, tighten the focused unit test in `tests/unit/test_qt_phase3_harness_workspace.py`. The fake compatibility object should expose `signature_appearance()` and `set_timestamp_required(...)` as the public seam. The test should fail if the adapter still depends on `properties_panel._workflow` for the appearance fallback or timestamp mutation.

Second, edit `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` to add `set_timestamp_required(self, required: bool) -> None`, implemented as a narrow workflow write plus `properties_panel.load_from_workflow()` if that is needed to keep the UI state aligned. Then edit `src/foliaseal/presentation/qt/signing_shell.py` to proxy the same verb so fallback shells can still satisfy `_compat_surface(...)` callers without exposing the workflow itself.

Third, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. In `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)`, replace the private workflow fallback read with `compat.signature_appearance()` and replace the direct `timestamp_required` write with `compat.set_timestamp_required(...)`. Leave `apply_signature_rect_placement(...)`, `refresh_viewer()`, and the Qt event pump exactly where they are.

Finally, run focused validation and perform the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan before creating the commit. If the review finds the architecture docs already accurate, record that result here instead of forcing a no-op documentation edit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the focused failing test and then implement the narrow timestamp boundary.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py

2. Re-run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
       git diff --check

3. Run adjacent regression checks if the seam change affects harness callers.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py

4. Update this plan with the actual results, perform the compliance review, and create the commit. Only edit `docs/ARCHITECTURE.md` if the review finds a real mismatch.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` no longer reads or writes `compat.properties_panel._workflow`;
- live-shell scenario application still applies appearance overrides, timestamp-required changes, signature-rect placement, viewer refresh, and Qt event pumping exactly as before;
- `SigningWorkspaceCompatibilitySurface` owns a narrow `set_timestamp_required(...)` verb, and `signing_shell.py` proxies it for callers that reach the shell edge directly;
- the headless adapter remains unchanged; and
- the separate `current_request()` private-workflow read is intentionally left for a later slice and not widened here.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
    git diff --check

If the compatibility edge change touches adjacent harness paths, also run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py

Acceptance is behavioral. The harness should behave the same, but one more live-shell workflow reach-through must disappear from scenario application.

## Idempotence and Recovery

This slice is a behavior-preserving extraction inside local Qt presentation code. It is safe to retry. If the new timestamp setter causes failures, keep the setter on the compatibility-shell edge and move only the missing UI resync step into that helper rather than restoring direct `_workflow` access in the harness adapter.

Do not recover by widening the slice into a general workflow-export API. The point of the slice is to preserve narrow verbs and make the harness boundary less coupled to shell anatomy.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a smaller `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`;
- a narrow `set_timestamp_required(...)` verb on `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` and its shell proxy;
- focused harness tests that fail before the seam change and pass after it; and
- validation output showing the slice stayed local.

Validation evidence:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
    ........                                                                 [100%]
    8 passed in 0.32s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
    All checks passed!

    $ git diff --check
    <no output>

    $ .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py
    ....                                                                     [100%]
    4 passed in 0.32s

    $ explorer-light compliance review
    Compliant; no `docs/ARCHITECTURE.md` or `docs/SPEC.md` correction required for this slice.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the important live-shell seam should include:

    class SigningWorkspaceCompatibilitySurface:
        def signature_appearance(self) -> SignatureAppearance | None: ...
        def set_timestamp_required(self, required: bool) -> None: ...

and the shell proxy:

    class SigningWorkspaceWidget:
        def set_timestamp_required(self, required: bool) -> None: ...

`QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` should use `compat.signature_appearance()` as the fallback appearance source and `compat.set_timestamp_required(...)` for timestamp mutation. This slice must not change `Phase3HarnessWorkspacePort`, must not broaden the compatibility surface into generic workflow export, and must not absorb the `current_request()` seam.

Revision note: Created on 2026-06-23 by Codex as the next `dev-loop` tracer bullet on the same hybrid harness seam. Updated on 2026-06-23 after implementation and compliance review to record the finished timestamp-boundary slice and the decision not to force a no-op architecture-doc edit.
