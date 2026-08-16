# Move live-shell signature-rect priming behind the compatibility surface

> **Archived completed plan (2026-08-16).** Retained for provenance; current
> work belongs to the durable acceptance/evidence owners. Do not execute as an
> active implementation queue.

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, Phase 3 signed-acceptance and preview-matrix scenario application will still place the same signature rectangle, jump the viewer to the target page, refresh the viewer, synchronize placement and overlay state, refresh the sign button, and then pump Qt events before capture or signing continues. The visible harness behavior does not change.

The architectural win is that `src/foliaseal/presentation/qt/phase3_harness_workspace.py` will stop owning the live-shell signature-rectangle priming choreography inline. Instead, `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` will own one helper for that sequence, and the harness workspace adapter will call that helper instead of manipulating viewer/page/sync anatomy directly. The proof is focused unit coverage and unchanged harness behavior.

## Child ExecPlan Dependencies

- [x] (2026-06-22 22:44Z) `docs/ExecPlans/phase3_harness_workspace_scenario_boundary_execplan.md` is complete; the workspace boundary already owns scenario application.
- [x] (2026-06-22 22:44Z) `docs/ExecPlans/phase3_harness_workspace_capture_boundary_execplan.md` is complete; the same boundary already owns current-request, last-signing-result, and raw capture reads.
- [x] (2026-06-22 22:44Z) `docs/ExecPlans/phase3_harness_workspace_refresh_boundary_execplan.md` is complete; viewer priming refresh already lives behind the workspace boundary.
- [x] (2026-06-22 22:44Z) No child ExecPlans are required for this narrow choreography-move slice.

## Progress

- [x] (2026-06-22 22:44Z) Re-read `phase3_harness_workspace.py`, `signing_workspace_compatibility_surface.py`, the focused harness workspace tests, and the relevant architecture notes.
- [x] (2026-06-22 22:44Z) Completed the required `explorer-light` dev-loop audit and fixed the next slice at the signature-rect priming choreography only.
- [x] (2026-06-22 22:47Z) Added `apply_signature_rect_placement(...)` to `SigningWorkspaceCompatibilitySurface` and wired the real composition graph to provide the placement-sync, overlay-sync, and sign-button-refresh collaborators it needs.
- [x] (2026-06-22 22:47Z) Replaced the inline Qt adapter choreography in `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` with that compatibility-surface helper and kept the headless adapter unchanged and Qt-free.
- [x] (2026-06-22 22:47Z) Ran focused validation with `.venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check`; all passed.
- [x] (2026-06-22 22:47Z) Ran the adjacent regression checks recommended by the explorer: `.venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py`; both passed.
- [x] (2026-06-22 22:47Z) Reconciled `docs/ARCHITECTURE.md` and this ExecPlan to the narrower ownership split so the compatibility surface now explicitly owns the live-shell signature-rect priming choreography.
- [x] (2026-06-22 22:47Z) Ran the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; no corrective follow-on was required.
- [x] (2026-08-16) Historical publication marker closed; implementation commit `5cfdd4de9` is recorded above and this plan is archival.

## Surprises & Discoveries

- Observation: the harness workspace boundary already delegates scenario-wide refresh to the compatibility surface, but not the signature-rect priming choreography that leads into it.
  Evidence: `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` in `src/foliaseal/presentation/qt/phase3_harness_workspace.py` still performs `set_signature_rect`, page jump, viewer refresh, placement sync, overlay sync, and sign-button refresh inline before calling `refresh_viewer()`.

- Observation: the compatibility surface already owns closely related shell-side rectangle behavior.
  Evidence: `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` already owns `set_signature_rect(...)`, which updates the draft rectangle and triggers the workspace interaction refresh plan for normal shell callers.

- Observation: moving the choreography behind the compatibility surface required explicit collaborator injection from the composition root rather than a simple method move.
  Evidence: the real compatibility surface did not already own placement-context sync or sign-button-state refresh helpers. The implemented slice injected those callables from `signing_workspace_composition.py` so the moved helper preserved the original behavior instead of silently dropping it.

## Decision Log

- Decision: keep this slice limited to moving the live-shell signature-rect priming sequence behind the compatibility surface.
  Rationale: the explorer audit found that this is the next smallest live-shell anatomy block still exposed in the harness workspace adapter. Pulling in broader protocol extraction or session-runner changes would widen the slice unnecessarily.
  Date/Author: 2026-06-22 / Codex

- Decision: preserve the exact current choreography order.
  Rationale: the current tests already encode the intended behavior order indirectly through page jump, viewer refresh, placement sync, overlay sync, and sign-button refresh assertions. Changing that sequence here would turn a seam cleanup into a behavior change.
  Date/Author: 2026-06-22 / Codex

## Outcomes & Retrospective

Implementation, focused validation, architecture reconciliation, and compliance review are complete. `phase3_harness_workspace.py` no longer owns the live-shell signature-rect priming choreography inline; instead it delegates that deeper viewer/page/sync/sign-button sequence to `signing_workspace_compatibility_surface.py`, which already owns the related shell-local helpers.

The slice stayed narrow. It did not change the harness port shape, the headless adapter, the session runner, or the signed-acceptance runner. The remaining work is only the final commit.

## Context and Orientation

The Phase 3 harness is the Qt-side evidence runner for preview and signed-output scenarios. The narrow harness boundary lives in `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. That module already owns applying scenarios, refreshing the viewer, reading the current request and last signing result, and capturing raw preview state through a common interface that works for both live Qt shells and headless workflows.

One remaining block of live-shell anatomy is still embedded there. When a scenario includes a signature rectangle, `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` does more than just set the rectangle. It reaches through the compatibility surface to mutate the properties panel, jump the viewer to the target page, refresh the viewer widget with navigation enabled, synchronize placement context, synchronize the signature overlay, and refresh the sign button before doing the normal boundary refresh and Qt event pump.

The compatibility surface in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` is intentionally broad. It already owns deep shell/test helpers such as `set_signature_rect(...)`, page accessors, and other live widget interactions. That makes it the right owner for one more deep shell-side helper: “apply this live signature rectangle and do the usual follow-up choreography.” The harness workspace adapter should ask for that one behavior rather than performing the sequence inline.

The main test coverage is already in `tests/unit/test_qt_phase3_harness_workspace.py`. The existing `test_qt_phase3_harness_workspace_adapter_applies_scenario_and_syncs_viewer()` test is the key guardrail. It already proves the current order-sensitive side effects. This slice should keep that test green, and if needed, add one smaller focused test closer to the compatibility surface behavior as exercised through the harness adapter.

## Plan of Work

First, edit `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py`. Add one explicit helper method for live-shell signature-rect priming, with a stable name such as `apply_signature_rect_placement(...)`. It should accept a `SignatureRect`, call `properties_panel.set_signature_rect(signature_rect)` using the current behavior, then perform the same current follow-up sequence: jump the viewer workflow to the rectangle page when available, refresh the viewer widget with `navigation=True` when supported, call `sync_placement_context_from_viewer()` when present, call `sync_signature_overlay()` when present, and call `refresh_sign_button_state()` when present.

Second, edit `src/foliaseal/presentation/qt/phase3_harness_workspace.py`. In `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)`, replace the inline signature-rect priming block with one call to the new compatibility-surface helper. Leave the final `refresh_viewer()` call and the `QApplication.processEvents()` pump where they are so the slice does not change event timing. Do not change the headless adapter at all.

Third, update `tests/unit/test_qt_phase3_harness_workspace.py` only as needed. The existing scenario-application test should keep proving that the live adapter still jumps to the target page, refreshes the viewer widget, synchronizes placement and overlay state, refreshes the sign button, and refreshes the viewer boundary once. If a more direct fake helper assertion is useful, keep it small and centered on the moved choreography, not on unrelated harness behavior.

Finally, run focused validation. After the code is stable, update `docs/ARCHITECTURE.md` and this ExecPlan so the architecture notes no longer imply that `phase3_harness_workspace.py` itself owns the full live-shell priming choreography inline. Then run the required architectural compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this plan. If the review finds a mismatch, fix only that mismatch inside this slice and record it here before creating one narrow commit.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Add the compatibility-surface helper and migrate the live-shell harness adapter to use it.

       apply_patch ... on src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py
       apply_patch ... on src/foliaseal/presentation/qt/phase3_harness_workspace.py

2. Adjust focused harness workspace tests if needed.

       apply_patch ... on tests/unit/test_qt_phase3_harness_workspace.py

3. Run focused validation.

       .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
       .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
       git diff --check

4. If the helper signature or boundary surface changes unexpectedly, run the adjacent regression checks.

       .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py

5. Reconcile `docs/ARCHITECTURE.md` and this plan, rerun any affected checks, then complete the compliance review and create the commit.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- live-shell scenario application with a signature rectangle still sets the rectangle, jumps to the target page, refreshes the viewer widget, synchronizes placement and overlay state, refreshes sign-button state, then refreshes the viewer boundary and pumps Qt events;
- `QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` no longer performs that signature-rect choreography inline;
- `SigningWorkspaceCompatibilitySurface` owns one helper for the live-shell signature-rect priming sequence;
- the headless harness adapter remains unchanged and Qt-free;
- no session-runner, signed-acceptance runner, or broader compatibility-surface cleanup is mixed into this slice.

Run:

    .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py

Then run:

    .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
    git diff --check

If the helper shape affects adjacent boundaries, also run:

    .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py

Acceptance is behavioral. The harness should still behave the same, but one more live-shell anatomy block must move behind the compatibility surface.

## Idempotence and Recovery

This is a behavior-preserving extraction inside local Qt presentation code. It is safe to retry. If the new helper causes failures, keep the helper in `signing_workspace_compatibility_surface.py` and move only the missing shell-local call into it rather than pushing the choreography back into `phase3_harness_workspace.py`.

If a test fails because `properties_panel.set_signature_rect(...)` needs a different notification mode here, inspect the current behavior first and preserve the existing no-loop semantics before changing anything else. Do not recover by widening the slice into a general signature-rect API redesign.

## Artifacts and Notes

The most important final evidence for this slice will be:

- a new helper in `src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py` that owns live-shell signature-rect priming choreography;
- a smaller `src/foliaseal/presentation/qt/phase3_harness_workspace.py` that delegates that choreography instead of inlining it;
- focused harness workspace tests that remain green without changing the observed side effects;
- focused validation output proving the slice stayed local.

Validation evidence after implementation:

    $ .venv/bin/python -m pytest -q tests/unit/test_qt_phase3_harness_workspace.py
    8 passed in 0.32s

    $ .venv/bin/python -m ruff check src/foliaseal/presentation/qt/signing_workspace_compatibility_surface.py src/foliaseal/presentation/qt/phase3_harness_workspace.py tests/unit/test_qt_phase3_harness_workspace.py
    All checks passed!

    $ git diff --check
    <no output>

    $ .venv/bin/python -m pytest -q tests/unit/test_phase3_harness_session_runner.py tests/unit/test_phase3_signed_acceptance_matrix_runner.py
    4 passed in 0.32s

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the important new compatibility-surface helper should stay close to:

    class SigningWorkspaceCompatibilitySurface:
        def apply_signature_rect_placement(self, signature_rect: SignatureRect) -> None: ...

That helper should own:

    properties_panel.set_signature_rect(signature_rect)
    viewer_workflow.jump_to_page(signature_rect.page_index)
    viewer_widget.refresh(navigation=True)
    sync_placement_context_from_viewer()
    sync_signature_overlay()
    refresh_sign_button_state()

`QtPhase3HarnessWorkspaceAdapter.apply_scenario(...)` should call that helper when `command.signature_rect is not None`, then continue with `refresh_viewer()` and the existing event pump. This slice must not change the public `Phase3HarnessWorkspacePort` shape and must not add any new harness verbs.

Revision note: Created on 2026-06-22 by Codex as the next `dev-loop` tracer bullet on the same hybrid harness seam. The slice intentionally moves only the remaining live-shell signature-rect priming choreography behind the compatibility surface.
