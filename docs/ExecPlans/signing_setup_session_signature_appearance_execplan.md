# Move Programmatic Signature Appearance Updates Behind SigningSetupSession

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [`.agents/skills/write-execplan/PLANS.md`](/home/daekar/FoliaSeal/.agents/skills/write-execplan/PLANS.md).

## Purpose / Big Picture

The signing-setup hybrid is nearly complete, but `SignaturePropertiesPanel.set_signature_appearance()` still mutates `SigningDraftWorkflow` directly and then manually clears the selected preset via `DefaultSignaturePropertiesCoordinator`. This slice moves that residual setup orchestration behind `SigningSetupSession` so the panel remains a thinner Qt adapter and the setup session owns one more piece of preset-dirtying policy.

The user-visible behavior should stay the same. Programmatic appearance changes should still update the draft, still clear an active saved preset selection, still reload the panel state, and still refresh the preview. The change is architectural: the panel should no longer sequence the workflow mutation plus preset-clear itself.

## Child ExecPlan Dependencies

- [x] (2026-05-29 21:47Z) No child ExecPlans are required for this bounded slice.

## Progress

- [x] (2026-05-29 21:47Z) Reviewed `SignaturePropertiesPanel.set_signature_appearance()` and confirmed it is the clearest remaining setup-hybrid residue in the panel.
- [x] (2026-05-29 21:47Z) Wrote this ExecPlan and fixed the slice boundary at: programmatic appearance mutation only. Placement-rectangle mutation remains outside this slice.
- [x] (2026-05-30 02:35Z) Added an explicit `set_signature_appearance(...)` verb to `SigningSetupSession`.
- [x] (2026-05-30 02:35Z) Migrated `SignaturePropertiesPanel.set_signature_appearance()` to delegate to the session.
- [x] (2026-05-30 02:35Z) Added direct setup-session coverage for appearance mutation clearing the selected preset.
- [x] (2026-05-30 02:35Z) Added a focused shell test proving the panel now uses the session entrypoint.
- [x] (2026-05-30 02:35Z) Ran focused validation with `pytest`, `ruff check`, and `git diff --check`.
- [x] (2026-05-30 02:35Z) Ran the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`, then addressed the remaining architecture-doc gap.
- [x] (2026-05-30 02:35Z) Updated documentation, including this ExecPlan, to final state.
- [x] (2026-05-30 02:35Z) Committed the slice as one narrow architecture change.

## Surprises & Discoveries

- Observation: the remaining direct setup mutation in the panel is not form-driven; it is the programmatic appearance setter used by the shell surface and tests.
  Evidence: `SignaturePropertiesPanel.set_signature_appearance()` still calls `self._workflow.set_signature_appearance(...)` and then `self._coordinator.reconcile(ClearSelectedSignaturePreset(...))` directly.

- Observation: removing the panel-owned path also removed the last direct shell use of `ClearSelectedSignaturePreset`.
  Evidence: after the migration, `ruff` flagged the shell import of `ClearSelectedSignaturePreset` as unused, and removing it left the focused suite green.

## Decision Log

- Decision: keep placement-rectangle mutation out of this slice.
  Rationale: rectangle changes belong partly to viewer/placement coordination, while programmatic appearance changes are still squarely inside the signing-setup hybrid.
  Date/Author: 2026-05-29 / Codex

## Outcomes & Retrospective

Implemented result:

- `set_signature_appearance()` no longer sequences workflow mutation plus preset clearing in the panel
- the setup session owns another piece of preset-dirtying policy
- direct setup-session tests cover the programmatic appearance-update path
- `SPEC.md` and `SCHEMAS.md` behavior remains intact
- focused validation evidence:
  - `pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py -q` -> `114 passed`
  - `ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signing_setup_session.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_qt_signing_shell.py` -> passed
  - `git diff --check` -> passed

## Context and Orientation

The visible-signature form path already uses `SigningSetupSession.apply_visible_setup(...)`, and preset/certificate selection plus preset mutation already go through the session too. The remaining gap is the programmatic setter that bypasses the form and still clears a saved preset the old way.

The current method is small, but it is exactly the kind of shallow orchestration the hybrid is intended to eliminate:

- mutate `SigningDraftWorkflow.signature_appearance`
- clear selected preset
- reload panel state
- emit change notifications

The session should own the first two steps so the panel remains only the adapter that renders returned state and refreshes preview.

## Plan of Work

First, extend `SigningSetupSession` with `set_signature_appearance(...)`. It should mutate the coordinator workflow, clear the selected preset through the existing coordinator-backed path, and return `SignaturePropertiesViewState`.

Second, migrate `SignaturePropertiesPanel.set_signature_appearance()` to call the session and render the returned state instead of talking to the workflow and coordinator directly.

Third, add direct session tests plus one focused shell test proving the panel now delegates to the session entrypoint.

Finally, run focused validation, review compliance, update docs, and commit the slice.

## Concrete Steps

All commands run from `/home/daekar/FoliaSeal`.

1. Edit the session boundary, the signing shell, and focused tests.

       apply_patch ... on src/foliaseal/application/signing_setup_session.py
       apply_patch ... on src/foliaseal/presentation/qt/signing_shell.py
       apply_patch ... on tests/unit/test_signing_setup_session.py
       apply_patch ... on tests/unit/test_qt_signing_shell.py

2. Run focused validation.

       pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
       ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
       git diff --check

3. Run the required compliance review against `docs/ARCHITECTURE.md`, `docs/SPEC.md`, and `docs/SCHEMAS.md`. If the review finds a mismatch, update this ExecPlan, implement the fix, and repeat validation before committing.

4. Update documentation and commit the slice.

## Validation and Acceptance

This slice is accepted when all of the following are true:

- programmatic appearance updates go through `SigningSetupSession`
- the panel no longer directly mutates workflow appearance plus clears preset selection for that path
- direct setup-session tests cover the appearance-update path
- focused shell tests still pass
- `docs/ARCHITECTURE.md` describes the updated setup-session boundary accurately

Run:

    pytest tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py

Then run:

    ruff check src/foliaseal/application/signing_setup_session.py src/foliaseal/application/__init__.py src/foliaseal/presentation/qt/signing_shell.py tests/unit/test_signature_properties_coordinator.py tests/unit/test_signing_setup_session.py tests/unit/test_qt_signing_shell.py
    git diff --check

Acceptance is behavior-preserving. There is no intended product-surface change in this slice.

## Idempotence and Recovery

This is a behavior-preserving refactor in local application/Qt presentation code. It is safe to retry. If the slice proves broader than expected, keep the new session verb even if the panel temporarily still handles one of the render/reload steps itself. Do not pull preview rendering into the session as a shortcut.

## Artifacts and Notes

The most important evidence for this slice will be:

- the focused `pytest` result covering session, shell, and affected coordinator tests
- a clean `ruff check`
- a clean `git diff --check`
- the updated `docs/ARCHITECTURE.md` description of programmatic appearance mutation inside the setup session boundary

These transcripts should be recorded back into this ExecPlan as work completes.

## Interfaces and Dependencies

This slice uses the `Local-substitutable` dependency category.

At the end of this slice, the setup seam should look approximately like:

    class SigningSetupSession(Protocol):
        def load(...) -> SignaturePropertiesViewState: ...
        def apply_visible_setup(...) -> SignaturePropertiesViewState: ...
        def set_signature_appearance(...) -> SignaturePropertiesViewState: ...
        def select_signature_preset(...) -> SignaturePropertiesViewState | None: ...
        def clear_selected_signature_preset(...) -> SignaturePropertiesViewState: ...
        def select_certificate_configuration(...) -> SignaturePropertiesViewState | None: ...
        def refresh_catalogs(...) -> SignaturePropertiesViewState: ...
        def save_preset(...) -> SignaturePropertiesViewState: ...
        def delete_preset(...) -> SignaturePropertiesViewState: ...

Revision note: Created on 2026-05-29 by Codex for the next signing-setup session hybrid slice.
