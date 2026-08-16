# Move live-shell current-request extraction behind a narrow workspace boundary

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Phase 3 harness will still be able to read the current live signing request, shape preview and backend evidence from it, and continue preview-matrix and signed-acceptance flows without any user-visible behavior change.

The architectural win is one more removed reach-through. `src/foliaseal/presentation/qt/phase3_harness_workspace.py` should stop reconstructing the live request from `compat.properties_panel._workflow`. Instead, it should ask the live shell boundary for `current_request()` through one narrow compatibility verb. The proof is focused unit coverage, unchanged capture payloads, and updated architecture notes where the old constraint is now stale.

## Child ExecPlan Dependencies

- [x] (2026-06-23 22:34Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the workspace boundary already owns scenario mutation.
- [x] (2026-06-23 22:34Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the same boundary already owns request/result/capture reads.
- [x] (2026-06-23 22:34Z) `docs/ExecPlans/phase3_harness_signature_rect_priming_execplan.md` is complete; signature-rect priming already moved behind the compatibility surface.
- [x] (2026-06-23 22:34Z) `docs/ExecPlans/phase3_harness_timestamp_boundary_execplan.md` is complete; scenario application no longer reaches through `_workflow` for appearance or timestamp state.
- [x] (2026-06-23 22:34Z) No child ExecPlans are required for this narrow current-request slice.

## Progress

- [x] (2026-06-23 22:34Z) Re-read `phase3_harness_workspace.py`, `signing_workspace_compatibility_surface.py`, `signing_shell.py`, the focused harness request tests, and the relevant architecture notes.
- [x] (2026-06-23 22:34Z) Completed the required `explorer-light` dev-loop audit and fixed the next slice at the remaining `_workflow` access inside `QtPhase3HarnessWorkspaceAdapter.current_request()`.
- [x] (2026-06-23 22:35Z) Added a focused failing test that removes `_workflow` from the live fake and requires request reads to come from a public `current_request()` seam.
- [x] (2026-06-23 22:35Z) Implemented `current_request()` on the compatibility-shell edge and updated the live adapter to call it.
- [x] (2026-06-23 22:36Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-23 22:36Z) Ran adjacent regression checks with `.venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py`; both passed.
- [x] (2026-06-23 22:36Z) Updated `docs/ARCHITECTURE.md` and the stale notes in `docs/ExecPlans/phase3_harness_timestamp_boundary_execplan.md` so they no longer describe `current_request()` as a private-workflow leak.
- [x] (2026-06-23 22:37Z) Completed the required `explorer-light` architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and the affected ExecPlans; the reviewer found the slice compliant and no corrective follow-on was required.
- [x] (2026-08-16) Historical publication marker closed; implementation commit `0ab01f604` is recorded above and this plan is archival.

## Surprises & Discoveries

- Observation: the remaining leak is smaller than the earlier scenario slices because the protocol already exposes `current_request()`.
  Evidence: `Phase3HarnessWorkspacePort` already defines `current_request()`, so only the live-shell implementation still needs to stop using `properties_panel._workflow`.

- Observation: this read is reconstructed state, not a simple field getter.
  Evidence: `snapshot_current_draft_request(...)` returns `None` until both `current_signature_rect` and `current_signature_appearance` exist and copies the exact workflow request fields into a new `SigningRequest`.

- Observation: reusing the harness helper directly from the compatibility surface would have added a reverse dependency from the shell layer back into the harness boundary.
  Evidence: the implemented slice keeps the shell layer self-contained by reconstructing the same request shape locally inside `signing_workspace_compatibility_surface.py` instead of importing `snapshot_current_draft_request(...)` from `phase3_harness_workspace.py`.

## Decision Log

- Decision: keep this slice limited to the `current_request()` live-shell implementation.
  Rationale: that is the only remaining production workflow reach-through in `phase3_harness_workspace.py`, so mixing it with preview-control or capture-helper cleanup would widen the review without improving the seam ranking.
  Date/Author: 2026-06-23 / Codex

- Decision: add a narrow `current_request()` verb on `SigningWorkspaceCompatibilitySurface` and proxy it through `signing_shell.py`.
  Rationale: the current hybrid direction is to add targeted harness-facing verbs instead of reopening a broad workflow-export contract. A proxy also preserves the fallback shell shape used by older fakes when `_compat_surface(...)` resolves to the shell itself.
  Date/Author: 2026-06-23 / Codex

- Decision: keep the compatibility-surface implementation self-contained instead of importing the harness request-snapshot helper.
  Rationale: importing `snapshot_current_draft_request(...)` from the harness module would invert the intended dependency direction between the production shell layer and the harness boundary. A small local helper preserves behavior without introducing that reverse edge.
  Date/Author: 2026-06-23 / Codex

## Outcomes & Retrospective

Implementation, documentation reconciliation, and compliance review are complete. `QtPhase3HarnessWorkspaceAdapter.current_request()` no longer touches `properties_panel._workflow`; it now delegates through `_compat_surface(self._shell).current_request()`, with the live compatibility surface and shell proxy owning the narrow request-shaped verb.

The slice stayed narrow. It did not change `Phase3HarnessWorkspacePort`, the headless adapter, session-runner ownership, or the surrounding capture/preview flows. The only remaining work is the final commit.

## Context and Orientation

The Phase 3 harness uses `src/foliaseal/presentation/qt/phase3_harness_workspace.py` as the shared workspace boundary for both live Qt shells and headless workflows. That module already owns scenario mutation, viewer refresh, request/result reads, and raw capture-state assembly used by preview matrices, signed-acceptance runs, and the interactive session runner.

The headless adapter is already clean: it returns `snapshot_current_draft_request(self._workflow)`. The live adapter is the remaining problem. `QtPhase3HarnessWorkspaceAdapter.current_request()` still resolves `_compat_surface(self._shell).properties_panel._workflow` and then passes that private workflow object to `snapshot_current_draft_request(...)`. This keeps one private shell-anatomy dependency in the harness boundary even after the recent timestamp and signature-rect cleanup.

The compatibility surface in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` already owns other narrow harness/testing helpers such as `signature_appearance()`, `set_timestamp_required(...)`, `set_signature_rect(...)`, and `apply_signature_rect_placement(...)`. It is the right owner for one more request-shaped verb. The real request reconstruction should stay in `snapshot_current_draft_request(...)` so both headless and live paths continue to share the same field mapping and `None` behavior.

The key files for this slice are `src/foliaseal/presentation/qt/phase3_harness_workspace.py`, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`, `src/foliaseal/presentation/qt/signing_shell.py`, `tests/unit/test_qt_phase3_harness_workspace.py`, `docs/ARCHITECTURE.md`, and this ExecPlan. The timestamp-boundary ExecPlan from the previous slice also contains now-stale notes that should be corrected if this slice lands as planned.

## Plan of Work

First, tighten the focused live-adapter test in `tests/unit/test_qt_phase3_harness_workspace.py`. The fake compatibility object should expose `current_request()` and stop carrying `_workflow` on its fake panel. The test should fail if the adapter still reconstructs the request from `properties_panel._workflow`.

Second, edit `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` to add `current_request(self) -> SigningRequest | None`, implemented with the same request-shaping rules currently used by `snapshot_current_draft_request(...)` but kept local to the shell layer so the production shell code does not depend back on the harness module. Then edit `src/foliaseal/presentation/qt/signing_shell.py` to proxy that verb so direct-shell fallback callers also satisfy `_compat_surface(...)`.

Third, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. Replace the live adapter’s direct `_workflow` read in `current_request()` with `return _compat_surface(self._shell).current_request()`. Leave the headless adapter and `snapshot_current_draft_request(...)` unchanged so the field mapping stays shared.

Finally, run focused validation, update `docs/ARCHITECTURE.md` to remove the stale claim that the workspace boundary still relies on `properties_panel._workflow`, update any stale note in `docs/ExecPlans/phase3_harness_timestamp_boundary_execplan.md`, and perform the required compliance review before creating the commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the focused failing test, then implement the narrow current-request boundary.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py

2. Re-run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
       git diff --check

3. Run adjacent regression checks if the new boundary affects harness callers.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py

4. Reconcile `docs/ARCHITECTURE.md` and stale ExecPlan notes, perform the compliance review, and create the commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `QtPhase3HarnessWorkspaceAdapter.current_request()` no longer reads `compat.properties_panel._workflow`;
- the live adapter still returns the same `SigningRequest` snapshot shape and the same `None` behavior as `snapshot_current_draft_request(...)`;
- `SigningWorkspaceCompatibilitySurface` owns a narrow `current_request()` verb, and `signing_shell.py` proxies it for direct-shell fallback callers;
- the headless adapter remains unchanged; and
- the stale architecture/ExecPlan notes about the remaining `current_request()` leak are corrected.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/signing_shell.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
    git diff --check

If the seam change touches adjacent harness paths, also run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_signed_acceptance_matrix_runner.py tests/unit/test_phase3_harness_session_runner.py

Acceptance is behavioral. The harness should behave the same, but the last production `_workflow` read in `phase3_harness_workspace.py` must disappear.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt presentation code. It is safe to retry. If the new compatibility verb causes failures, keep the verb and move only the missing fallback behavior into it rather than restoring `_workflow` access in `QtPhase3HarnessWorkspaceAdapter.current_request()`.

Do not recover by widening the slice into a generic workflow-export API. The point is to keep the harness boundary talking in request-shaped verbs, not shell-internal state objects.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a smaller `QtPhase3HarnessWorkspaceAdapter.current_request()` in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`;
- a narrow `current_request()` verb on `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` and its shell proxy;
- focused harness tests that fail before the seam change and pass after it; and
- documentation updates that remove the now-stale “current_request still leaks workflow” note.

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
    4 passed in 0.34s

    $ explorer-light compliance review
    Compliant; no docs or code correction required for this slice.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the important live-shell seam should include:

    class SigningWorkspaceCompatibilitySurface:
        def current_request(self) -> SigningRequest | None: ...

and the shell proxy:

    class SigningWorkspaceWidget:
        def current_request(self) -> SigningRequest | None: ...

`QtPhase3HarnessWorkspaceAdapter.current_request()` should delegate to that verb. The live compatibility helper must preserve the same field-copying and `None` behavior as `snapshot_current_draft_request(...)`, even though the shell layer keeps that logic locally to avoid depending back on the harness module. This slice must not change `Phase3HarnessWorkspacePort`, must not broaden the compatibility surface into generic workflow export, and must not absorb unrelated preview or capture cleanup.

Revision note: Created on 2026-06-23 by Codex as the next `dev-loop` tracer bullet on the same hybrid harness seam. This slice intentionally removes only the remaining production `_workflow` access inside live-shell current-request extraction.
