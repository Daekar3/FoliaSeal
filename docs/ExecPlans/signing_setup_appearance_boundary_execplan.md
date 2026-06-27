# Move Signature-Appearance Mutation Behind The Signing Setup Boundary

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with `.agents/skills/write-execplan/PLANS.md`.

## Purpose / Big Picture

After this slice, the Qt properties panel will still call `SigningSetupSession.set_signature_appearance(...)`, but the session will stop mutating `SigningDraftWorkflow` directly. Instead, an explicit application-layer coordinator entrypoint or command will own appearance-only updates and the related preset-clearing/state-reload behavior. The visible behavior must stay the same: programmatic appearance changes still clear the selected preset, re-render the current setup state, recompute readiness text, and notify the shell when a real change applied.

The user-visible proof is behavior preservation with a deeper module boundary. Focused coordinator and setup-session tests should prove that appearance-only updates now flow through the same application boundary as the other setup verbs instead of bypassing it.

## Child ExecPlan Dependencies

- [x] (2026-06-27 00:00Z) No child ExecPlans are required for this bounded application-boundary slice.

## Progress

- [x] (2026-06-27 00:00Z) Re-read the current hybrid seam in `src/foliaseal/application/signing_setup_session.py`, `src/foliaseal/application/signature_properties_coordinator.py`, `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py`, `docs/ARCHITECTURE.md`, and the focused setup/coordinator tests.
- [x] (2026-06-27 00:00Z) Used the required `explorer-light` dev-loop audit to select the next slice: move appearance-only mutation behind the coordinator boundary and keep the Qt panel API unchanged.
- [x] (2026-06-27 00:00Z) Wrote this ExecPlan before implementation.
- [x] (2026-06-27 17:23Z) Added focused red-phase tests proving the leak: the coordinator now needs an appearance-only boundary entrypoint, and the session must delegate instead of touching `coordinator.workflow` directly.
- [x] (2026-06-27 17:23Z) Implemented `DefaultSignaturePropertiesCoordinator.set_signature_appearance()` plus the `SetSignatureAppearance` command path, and rewired `SigningSetupSession.set_signature_appearance()` to delegate through that boundary.
- [x] (2026-06-27 17:23Z) Ran focused validation: `.venv/bin/python -m pytest -q tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py`, `.venv/bin/python -m ruff check ...`, and `git diff --check` all passed.
- [x] (2026-06-27 17:26Z) Completed the required `explorer-light` compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan; the reviewer found only stale architecture/plan wording plus two missing direct tests on the new path.
- [x] (2026-06-27 17:26Z) Added direct command-path and control-issue coverage for `SetSignatureAppearance`, reconciled `docs/ARCHITECTURE.md`, and re-ran focused validation plus a shell smoke subset: `.venv/bin/python -m pytest -q tests/unit/test_qt_signing_shell.py -k 'set_signature_appearance_uses_setup_session_entrypoint or apply_changes_maps_form_value_error_to_validation_issue'`.
- [ ] Prepare the slice for the required documentation and commit steps in the larger dev-loop.

## Surprises & Discoveries

- Observation: before this slice, the hybrid was almost complete for the common setup path, but `SigningSetupSession.set_signature_appearance()` still bypassed the coordinator and mutated `workflow` directly.
  Evidence: the previous `src/foliaseal/application/signing_setup_session.py` implementation called `self.coordinator.workflow.set_signature_appearance(...)` before delegating only the preset-clearing half back through the coordinator.

- Observation: a pure behavior test was not enough to guard this seam because the old direct-mutation path and the desired delegated path both produced the same visible result.
  Evidence: the pre-existing session test already proved preset clearing plus appearance replacement, yet the boundary leak remained until a fake coordinator made direct `workflow` access fail loudly.

## Decision Log

- Decision: keep this slice narrowly focused on the appearance-only mutation path and do not widen into visible-setup form validation, prompt interactions, or save/delete confirmations.
  Rationale: those are separate seams. The immediate architectural debt is the last direct workflow mutation escaping the session boundary.
  Date/Author: 2026-06-27 / Codex

- Decision: preserve the panel-facing API and shell behavior.
  Rationale: the point of the slice is to deepen the application module, not to make the Qt caller learn a new interface.
  Date/Author: 2026-06-27 / Codex

## Outcomes & Retrospective

The implementation, focused validation, and compliance review are complete. The code now exposes an explicit coordinator-owned appearance-only path, and the setup session no longer mutates `workflow` directly for `set_signature_appearance(...)`. The compliance review initially found only documentation drift and missing direct proof on the new command path; those gaps were closed in the same slice with updated architecture wording, stronger coordinator coverage, and a shell smoke subset.

## Context and Orientation

The relevant application boundary is split between `src/foliaseal/application/signature_properties_coordinator.py` and `src/foliaseal/application/signing_setup_session.py`.

`DefaultSignaturePropertiesCoordinator` already owns most of the signing-setup workflow mutation and state projection. It can load current selector names, apply visible-signature setup drafts, apply named certificate configurations, apply named signature presets, refresh catalogs, save or delete presets, and clear the selected preset while returning `SignaturePropertiesViewState`.

`SigningSetupSession` is the higher-level application wrapper used by the Qt panel. It adds manual certificate-password retry, session-local password caching, and explicit `SigningSetupSelectionOutcome` values for selection verbs. The panel in `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` is intentionally thin: it normalizes placeholder combo-box values, owns overwrite/delete confirmation dialogs, renders returned state, and notifies the shell when the applied result says a real change happened.

Before this slice, the remaining boundary leak was `SigningSetupSession.set_signature_appearance(...)`. That method wrote directly to `self.coordinator.workflow`, then asked the coordinator only to clear the preset selection and reload view state. This plan closes that last common-path escape hatch so the setup verbs now flow through explicit application-layer entrypoints consistently.

The focused safety net lives in `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_signing_setup_session.py`. `docs/ARCHITECTURE.md` already describes the panel delegating common setup flow to the setup session and should be updated if the coordinator gains a first-class appearance-only command or method.

This slice must not widen into:

- `src/foliaseal/presentation/qt/visible_signature_setup_form.py`
- `src/foliaseal/presentation/qt/signing_workspace_properties_panel.py` behavior changes
- prompt/confirm dialog ownership changes
- signing action, review workspace, or app-frame lifecycle seams

## Plan of Work

First, add a first-class appearance-only operation to `src/foliaseal/application/signature_properties_coordinator.py`. The operation may be a new command dataclass handled by `reconcile(...)`, or a dedicated wrapper method that delegates to such a command, but it must leave the coordinator as the sole owner of workflow mutation plus returned `SignaturePropertiesViewState` for this path. The operation must preserve current behavior: set the workflow signature appearance, clear the selected preset state through the existing coordinator rules, and return freshly loaded state with the optional `control_issue` folded into readiness and validation text.

Second, update `src/foliaseal/application/signing_setup_session.py` so `set_signature_appearance(...)` delegates entirely to the coordinator boundary instead of mutating `self.coordinator.workflow` directly. Do not widen the session interface or change how the panel calls it.

Third, update focused tests in `tests/unit/test_signature_properties_coordinator.py` and `tests/unit/test_signing_setup_session.py`. The coordinator suite should prove that appearance-only application mutates the workflow, clears the selected preset, and returns recomputed state through the application boundary. The session suite should prove that `set_signature_appearance(...)` still delivers the expected state after delegating through the coordinator. Keep the tests behavioral and boundary-oriented rather than asserting implementation details such as exact internal helper names.

Fourth, reconcile `docs/ARCHITECTURE.md` so it accurately states that appearance-only updates are now delegated through the coordinator boundary rather than partially handled by direct workflow mutation in the session. Then run the required focused validation and the post-implementation compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and this ExecPlan.

## Concrete Steps

Work from the repository root:

    cd /home/daekar/FoliaSeal

Edit these files:

    src/foliaseal/application/signature_properties_coordinator.py
    src/foliaseal/application/signing_setup_session.py
    tests/unit/test_signature_properties_coordinator.py
    tests/unit/test_signing_setup_session.py
    docs/ARCHITECTURE.md
    docs/ExecPlans/signing_setup_appearance_boundary_execplan.md

Suggested implementation order:

1. Update the focused tests first.
2. Add the new coordinator command or wrapper entrypoint.
3. Route `SigningSetupSession.set_signature_appearance(...)` through that boundary.
4. Re-run the focused tests and only then update documentation.

Run focused validation as the slice progresses:

    .venv/bin/python -m pytest -q tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    .venv/bin/python -m ruff check src/foliaseal/application/signature_properties_coordinator.py src/foliaseal/application/signing_setup_session.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py
    git diff --check

After the first implementation pass, run the required compliance review against at least:

    docs/ARCHITECTURE.md
    docs/SPEC.md
    docs/ExecPlans/signing_setup_appearance_boundary_execplan.md

## Validation and Acceptance

This slice is accepted when all of the following are true:

- `SigningSetupSession.set_signature_appearance(...)` no longer mutates `SigningDraftWorkflow` directly.
- an explicit coordinator boundary now owns appearance-only signature-appearance mutation and preset clearing.
- applying a programmatic signature appearance still clears any selected preset and returns refreshed `SignaturePropertiesViewState`.
- the Qt panel-facing setup-session API stays unchanged.
- focused coordinator and setup-session tests pass.
- `docs/ARCHITECTURE.md` describes the updated boundary accurately.

Observable proof is a focused test run where the new or updated boundary tests pass and the architecture document matches the final code path.

## Idempotence and Recovery

This is a behavior-preserving refactor and is safe to retry. If the first pass leaves both direct workflow mutation and coordinator-owned mutation active, remove the direct session-side mutation before considering the slice complete; do not keep two sources of truth for appearance updates. If the coordinator needs a new command dataclass, prefer the additive command first and only remove obsolete special-casing after the tests are green.

If the change unexpectedly requires panel behavior changes, stop and split that broader redesign into a later slice instead of widening this one.

## Artifacts and Notes

Capture and keep concise:

- the focused test run proving appearance-only updates still behave correctly
- any architecture wording changed to reflect the new coordinator-owned path

## Interfaces and Dependencies

This slice uses the `In-process` dependency category.

At the end of the slice, the coordinator boundary should expose one explicit appearance-only path in addition to its current setup verbs. One acceptable final shape is:

    @dataclass(frozen=True)
    class SetSignatureAppearance:
        signature_appearance: SignatureAppearance | None

    class SignaturePropertiesCoordinator(Protocol):
        def set_signature_appearance(
            self,
            signature_appearance: SignatureAppearance | None,
            *,
            control_issue: SigningDraftValidationIssue | None = None,
        ) -> SignaturePropertiesViewState: ...

Or, if the implementation stays command-only, `reconcile(...)` must accept the new command and `SigningSetupSession.set_signature_appearance(...)` must use it. The contract is what matters: appearance-only changes go through the coordinator boundary, clear the selected preset, and return refreshed state without direct session-side workflow mutation.

Revision note: Created on 2026-06-27 by Codex after the required dev-loop explorer selected the next hybrid slice: move appearance-only mutation fully behind the application boundary.

Revision note: Updated on 2026-06-27 by Codex after the red-green implementation pass to record the new `SetSignatureAppearance` coordinator path, the focused validation results, and the stronger session-boundary test that now fails on direct workflow mutation.
